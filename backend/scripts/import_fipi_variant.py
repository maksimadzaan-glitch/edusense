"""Импорт эталонного варианта ФИПИ/КИМ → Postgres (без LLM / polish).

Запуск из корня проекта:
  python -m backend.scripts.import_fipi_variant path/to/etalon.json
  python -m backend.scripts.import_fipi_variant path/to/etalon.json --golden
  python -m backend.scripts.import_fipi_variant path/to/etalon.json --skip-seed
  python -m backend.scripts.import_fipi_variant --build-fixtures

Правила (см. TZ_FIPI_ETALON.md):
  - LLM / polish_fipi_text / polish_answer_key / vary — запрещены
  - слоты 1..N строго по kim_spec (math 25, rus 13)
  - correct_answer только из keys-файла
  - provenance + content_hash на context_block
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.universal.etalon import (  # noqa: E402
    compute_content_hash,
    expected_slot_count,
    load_kim_spec,
    normalize_image_urls,
    pack_id_for_subject,
    resolve_pack_asset_url,
)
from backend.universal.packs.loader import pack_dir  # noqa: E402

# Явный запрет импортировать polish в этом модуле (golden / lint-friendly).
_FORBIDDEN = ("polish_fipi_text", "polish_answer_key")


def _opt_text(value: object | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _json_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    s = str(value).strip()
    return s or None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: ожидался JSON-объект")
    return data


def _resolve_keys_path(etalon_path: Path, data: dict[str, Any]) -> Path:
    keys_file = data.get("keys_file")
    if keys_file:
        p = Path(str(keys_file))
        if not p.is_absolute():
            cand = etalon_path.parent / p
            if cand.is_file():
                return cand
            # относительно fixtures/etalon или корня пака
            for base in (etalon_path.parent, etalon_path.parent.parent):
                cand = base / p
                if cand.is_file():
                    return cand
        if p.is_file():
            return p
        raise SystemExit(f"keys_file не найден: {keys_file}")
    # inline keys
    if isinstance(data.get("keys"), dict):
        return etalon_path  # sentinel: keys inline
    raise SystemExit("Нужен keys_file или секция keys")


def _load_answers(etalon_path: Path, data: dict[str, Any]) -> dict[str, str]:
    if isinstance(data.get("keys"), dict) and isinstance(data["keys"].get("answers"), dict):
        raw = data["keys"]["answers"]
    elif isinstance(data.get("answers"), dict):
        raw = data["answers"]
    else:
        keys_path = _resolve_keys_path(etalon_path, data)
        if keys_path == etalon_path and isinstance(data.get("keys"), dict):
            raw = data["keys"].get("answers") or {}
        else:
            keys = _load_json(keys_path)
            raw = keys.get("answers") if isinstance(keys.get("answers"), dict) else keys
    out: dict[str, str] = {}
    for k, v in (raw or {}).items():
        out[str(k)] = "" if v is None else str(v)
    return out


def validate_slots(data: dict[str, Any], *, subject_code: str, kim_spec_id: str) -> int:
    n_expected = expected_slot_count(kim_spec_id, subject_code)
    try:
        spec = load_kim_spec(kim_spec_id)
        if int(spec.get("slot_count") or 0) and int(spec["slot_count"]) != n_expected:
            n_expected = int(spec["slot_count"])
    except FileNotFoundError:
        pass

    tasks = list(data.get("tasks") or [])
    if not tasks:
        raise SystemExit("В эталоне нет tasks")
    nums = sorted(int(t["task_number"]) for t in tasks if t.get("task_number") is not None)
    expected = list(range(1, n_expected + 1))
    if nums != expected:
        raise SystemExit(
            f"Слоты должны быть ровно 1..{n_expected}, получено {nums[:8]}… "
            f"(len={len(nums)})"
        )
    return n_expected


def _apply_keys(tasks: list[dict[str, Any]], answers: dict[str, str]) -> None:
    for t in tasks:
        num = str(int(t["task_number"]))
        if num not in answers:
            # part2 без ключа-слова — пустая строка допустима
            t["correct_answer"] = str(t.get("correct_answer") or "")
            continue
        t["correct_answer"] = answers[num]


def _process_assets(
    *,
    pack_id: str,
    root: Path,
    tasks: list[dict[str, Any]],
    copy_assets: bool,
) -> list[dict[str, Any]]:
    """Проверить/скопировать локальные медиа; проставить checksum; нормализовать URL."""
    manifest: list[dict[str, Any]] = []
    for t in tasks:
        payload = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        payload = dict(payload)
        media = list(payload.get("media") or []) if isinstance(payload.get("media"), list) else []
        image_urls = list(payload.get("image_urls") or []) if isinstance(payload.get("image_urls"), list) else []

        # media[].path → image_urls
        for m in media:
            if not isinstance(m, dict):
                continue
            path_rel = str(m.get("path") or "").strip()
            if not path_rel:
                continue
            if path_rel not in image_urls:
                image_urls.append(path_rel)

        new_media = []
        for m in media:
            if not isinstance(m, dict):
                continue
            m = dict(m)
            path_rel = str(m.get("path") or "").strip().replace("\\", "/")
            if not path_rel:
                new_media.append(m)
                continue
            src = Path(path_rel)
            if not src.is_absolute():
                # относительно корня пака или cwd
                cand = root / path_rel
                if not cand.is_file() and (root.parent / path_rel).is_file():
                    cand = root.parent / path_rel
                src_abs = cand
            else:
                src_abs = src

            dest_rel = path_rel
            if not dest_rel.startswith("assets/"):
                dest_rel = f"assets/etalon/{Path(path_rel).name}"

            dest = root / dest_rel
            if src_abs.is_file():
                if copy_assets or not dest.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if src_abs.resolve() != dest.resolve():
                        shutil.copy2(src_abs, dest)
                digest = _sha256_file(dest if dest.is_file() else src_abs)
                m["path"] = dest_rel
                m["sha256"] = digest
                manifest.append({"path": dest_rel, "sha256": digest, "task_number": t.get("task_number")})
            elif (root / path_rel).is_file():
                digest = _sha256_file(root / path_rel)
                m.setdefault("sha256", digest)
                manifest.append(
                    {"path": path_rel, "sha256": digest, "task_number": t.get("task_number")}
                )
            else:
                # относительный путь уже в паке, но файла нет — предупреждение
                print(f"WARNING: asset не найден: {path_rel} (task {t.get('task_number')})")
            new_media.append(m)

        # Нормализованные URL для UI
        payload["media"] = new_media
        payload["image_urls"] = normalize_image_urls(pack_id, image_urls)
        # сохранить и относительные пути для provenance
        payload["image_paths"] = [
            u.replace(f"/packs/{pack_id}/", "") if str(u).startswith(f"/packs/{pack_id}/") else u
            for u in image_urls
        ]
        t["payload"] = payload
    return manifest


def _prototype_title(*, variant_code: str, num: int, topic: str, subject_code: str) -> str:
    topic = (topic or "").strip() or "Задание"
    label = topic if " " in topic or topic[0].isupper() else topic.replace("_", " ")
    return f"{label} · etalon · {variant_code} #{num}"


def _prompt_for(num: int, topic: str) -> str:
    return (
        f"Эталонный слот №{num}"
        + (f" ({topic})" if topic else "")
        + ". Не перефразировать. Текст и ключ — как в источнике."
    )


def build_rows(data: dict[str, Any], *, pack_id: str, provenance: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    subject_code = str(data["subject_code"]).strip().lower()
    exam_code = str(data["exam_code"]).strip().upper()
    variant_code = str(data["variant_code"]).strip()
    ctx_src = data.get("context") if isinstance(data.get("context"), dict) else {}
    context_id = str(ctx_src.get("context_id") or f"etalon_{variant_code}").strip()

    ctx_params: dict[str, Any] = {
        "etalon": True,
        "variant_code": variant_code,
        "kim_spec_id": data.get("kim_spec_id"),
        "provenance": provenance,
        "published": False,
        "status": "draft",
    }
    for k in ("listening_text", "grammar_text", "reading_text"):
        if ctx_src.get(k) is not None:
            ctx_params[k] = ctx_src[k]

    block = {
        "context_id": context_id,
        "title": str(ctx_src.get("title") or f"Эталон · {variant_code}").strip(),
        "description_text": _opt_text(ctx_src.get("description_text")),
        "figure_kind": None,
        "figure_params": ctx_params,
        "subject_code": subject_code,
        "exam_code": exam_code,
        "etalon": True,
    }

    rows: list[dict[str, Any]] = []
    for t in data["tasks"]:
        num = int(t["task_number"])
        part = int(t.get("part") or (2 if (subject_code in ("russian", "rus") and num in (1, 13)) else 1))
        topic = str(t.get("topic") or f"slot_{num}")
        payload = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        payload = dict(payload)
        payload["etalon"] = True
        payload["provenance"] = {
            "variant_code": variant_code,
            "kim_spec_id": data.get("kim_spec_id"),
            "content_hash": provenance.get("content_hash"),
            "source": provenance.get("source"),
            "year": provenance.get("year"),
        }
        if subject_code in ("russian", "rus", "ru"):
            payload.setdefault("oge_rus", True)
            payload.setdefault("kim_type", num)
            payload.setdefault("ui", payload.get("ui") or "oge_rus")

        fig_params: dict[str, Any]
        if subject_code in ("russian", "rus", "ru"):
            fig_params = payload
        else:
            fig_params = {
                "etalon": True,
                "payload": payload,
                "image_urls": payload.get("image_urls") or [],
                "media": payload.get("media") or [],
                "provenance": payload["provenance"],
            }

        rows.append(
            {
                "task_number": num,
                "part": part,
                "prototype_title": _prototype_title(
                    variant_code=variant_code, num=num, topic=topic, subject_code=subject_code
                ),
                "prompt_instruction": _prompt_for(num, topic),
                "template_text": str(t.get("statement") or "").strip()
                or (
                    "Выполните только ОДНО из заданий: 13.1, 13.2 или 13.3."
                    if int(t.get("task_number") or 0) == 13
                    and isinstance(payload.get("essay_options"), list)
                    else ""
                ),
                "template_answer": str(t.get("correct_answer") or ""),
                "template_solution": _opt_text(t.get("template_solution") or t.get("solution_hint")),
                "figure_kind": _opt_text(t.get("figure_kind")),
                "figure_params": fig_params,
                "figure_data": t.get("figure_data"),
                "figure_svg": _opt_text(t.get("figure_svg")),
                "context_id": context_id,
                "answer_type": _opt_text(t.get("type") or t.get("answer_type")),
                "max_score": int(t["max_score"]) if t.get("max_score") is not None else (2 if part == 2 else 1),
                "acceptable_answers": t.get("acceptable_answers"),
                "subject_code": subject_code,
                "exam_code": exam_code,
            }
        )
    return block, rows


def seed_pg(block: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    from sqlalchemy import select

    from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
    from backend.db.pg_models import ContextBlock, ExamType, Subject, TaskPrototype

    if not is_postgres_configured():
        raise SystemExit("POSTGRES_URL не задан — seed невозможен (используйте --skip-seed)")

    init_pg_tables()
    SessionLocal = session_factory()
    db = SessionLocal()
    subject_code = str(block["subject_code"])
    exam_code = str(block["exam_code"])
    context_id = str(block["context_id"])
    try:
        names = {"math": "Математика", "russian": "Русский язык"}
        subj = db.scalar(select(Subject).where(Subject.code == subject_code))
        if subj is None:
            db.add(Subject(code=subject_code, name=names.get(subject_code, subject_code)))
        exam = db.scalar(select(ExamType).where(ExamType.code == exam_code))
        if exam is None:
            db.add(ExamType(code=exam_code, name=exam_code))
        db.flush()

        # удалить старые прототипы этого эталонного context_id
        old = db.scalars(
            select(TaskPrototype).where(
                TaskPrototype.subject_code == subject_code,
                TaskPrototype.exam_code == exam_code,
                TaskPrototype.context_id == context_id,
            )
        ).all()
        for row in old:
            db.delete(row)
        db.flush()

        exists = db.scalar(
            select(ContextBlock).where(
                ContextBlock.context_id == context_id,
                ContextBlock.subject_code == subject_code,
                ContextBlock.exam_code == exam_code,
            )
        )
        fig_params = _json_or_none(block.get("figure_params"))
        if exists:
            exists.title = str(block["title"])
            exists.description_text = _opt_text(block.get("description_text"))
            exists.figure_kind = _opt_text(block.get("figure_kind"))
            exists.figure_params = fig_params
            ctx_action = "updated"
        else:
            db.add(
                ContextBlock(
                    context_id=context_id,
                    title=str(block["title"]),
                    description_text=_opt_text(block.get("description_text")),
                    figure_kind=_opt_text(block.get("figure_kind")),
                    figure_params=fig_params,
                    subject_code=subject_code,
                    exam_code=exam_code,
                )
            )
            ctx_action = "inserted"

        for p in rows:
            db.add(
                TaskPrototype(
                    subject_code=subject_code,
                    exam_code=exam_code,
                    task_number=int(p["task_number"]),
                    prototype_title=str(p["prototype_title"]),
                    part=int(p["part"]),
                    prompt_instruction=str(p["prompt_instruction"]),
                    template_text=_opt_text(p.get("template_text")),
                    template_answer=str(p.get("template_answer") or ""),
                    template_solution=_opt_text(p.get("template_solution")),
                    figure_kind=_opt_text(p.get("figure_kind")),
                    figure_params=_json_or_none(p.get("figure_params")),
                    figure_data=_json_or_none(p.get("figure_data")),
                    figure_svg=_opt_text(p.get("figure_svg")),
                    context_id=context_id,
                    answer_type=_opt_text(p.get("answer_type")),
                    max_score=int(p["max_score"]) if p.get("max_score") is not None else None,
                    acceptable_answers=_json_or_none(p.get("acceptable_answers")),
                )
            )
        db.commit()
        return {
            "context": ctx_action,
            "context_id": context_id,
            "prototypes": len(rows),
            "stale_deleted": len(old),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def write_context_file(root: Path, block: dict[str, Any], rows: list[dict[str, Any]]) -> Path:
    cdir = root / "context_blocks"
    cdir.mkdir(parents=True, exist_ok=True)
    cid = str(block["context_id"])
    out = {
        "context_id": cid,
        "title": block["title"],
        "description_text": block.get("description_text"),
        "figure_kind": block.get("figure_kind"),
        "figure_params": block.get("figure_params"),
        "etalon": True,
        "tasks": [
            {
                "task_number": r["task_number"],
                "part": r["part"],
                "prototype_title": r["prototype_title"],
                "prompt_instruction": r["prompt_instruction"],
                "template_text": r["template_text"],
                "correct_answer": r["template_answer"],
                "template_answer": r["template_answer"],
                "template_solution": r.get("template_solution"),
                "figure_kind": r.get("figure_kind"),
                "figure_params": r.get("figure_params"),
                "figure_svg": r.get("figure_svg"),
                "max_score": r.get("max_score"),
                "answer_type": r.get("answer_type"),
                "acceptable_answers": r.get("acceptable_answers"),
            }
            for r in rows
        ],
    }
    path = cdir / f"{cid}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def golden_check(data: dict[str, Any], *, expected_hash: str, slot_count: int) -> dict[str, Any]:
    """Лёгкая проверка: hash совпал, слоты 1..N."""
    recomputed = compute_content_hash(data)
    nums = sorted(int(t["task_number"]) for t in data.get("tasks") or [])
    ok_slots = nums == list(range(1, slot_count + 1))
    ok_hash = recomputed == expected_hash
    return {
        "ok": ok_hash and ok_slots,
        "content_hash": recomputed,
        "expected_hash": expected_hash,
        "hash_match": ok_hash,
        "slot_count": len(nums),
        "expected_slots": slot_count,
        "slots_ok": ok_slots,
    }


def import_etalon(
    etalon_path: Path,
    *,
    skip_seed: bool = False,
    copy_assets: bool = True,
    golden: bool = False,
) -> dict[str, Any]:
    path = Path(etalon_path).resolve()
    if not path.is_file():
        raise SystemExit(f"Файл не найден: {path}")

    data = _load_json(path)
    if not data.get("etalon", True):
        raise SystemExit("JSON должен иметь etalon=true")

    subject_code = str(data.get("subject_code") or "").strip().lower()
    exam_code = str(data.get("exam_code") or "").strip().upper()
    kim_spec_id = str(data.get("kim_spec_id") or "").strip()
    variant_code = str(data.get("variant_code") or "").strip()
    if subject_code not in ("math", "russian"):
        raise SystemExit("Скоуп импортёра: subject_code math | russian")
    if exam_code != "OGE":
        raise SystemExit("Скоуп импортёра: exam_code OGE")
    if not kim_spec_id or not variant_code:
        raise SystemExit("Нужны kim_spec_id и variant_code")

    slot_count = validate_slots(data, subject_code=subject_code, kim_spec_id=kim_spec_id)
    answers = _load_answers(path, data)
    tasks = list(data["tasks"])
    _apply_keys(tasks, answers)
    data["tasks"] = tasks

    pack_id = pack_id_for_subject(subject_code)
    root = pack_dir(pack_id)
    root.mkdir(parents=True, exist_ok=True)

    manifest = _process_assets(pack_id=pack_id, root=root, tasks=tasks, copy_assets=copy_assets)
    data["tasks"] = tasks

    content_hash = compute_content_hash(data)
    now = datetime.now(timezone.utc).isoformat()
    prov_src = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
    provenance = {
        "source": prov_src.get("source") or "manual_teacher",
        "year": prov_src.get("year") or 2026,
        "variant_code": variant_code,
        "kim_spec_id": kim_spec_id,
        "content_hash": content_hash,
        "imported_at": now,
        "assets": manifest,
    }
    data["provenance"] = {**prov_src, **provenance, "imported_at": now, "content_hash": content_hash}

    block, rows = build_rows(data, pack_id=pack_id, provenance=provenance)
    ctx_path = write_context_file(root, block, rows)

    # сохранить каноническую копию импорта
    imports_dir = root / "imports" / "etalon"
    imports_dir.mkdir(parents=True, exist_ok=True)
    dest = imports_dir / f"{variant_code}.etalon.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary: dict[str, Any] = {
        "etalon_path": str(path),
        "import_copy": str(dest),
        "context_file": str(ctx_path),
        "context_id": block["context_id"],
        "variant_code": variant_code,
        "kim_spec_id": kim_spec_id,
        "subject_code": subject_code,
        "exam_code": exam_code,
        "slot_count": slot_count,
        "content_hash": content_hash,
        "provenance": provenance,
        "assets": len(manifest),
        "seed": None,
        "golden": None,
    }

    if golden:
        summary["golden"] = golden_check(data, expected_hash=content_hash, slot_count=slot_count)
        if not summary["golden"]["ok"]:
            raise SystemExit(f"Golden check FAILED: {summary['golden']}")

    if skip_seed:
        print("import_fipi_variant (files only):", json.dumps(summary, ensure_ascii=False, indent=2))
        return summary

    summary["seed"] = seed_pg(block, rows)
    print("import_fipi_variant:", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Импорт эталонного варианта (без LLM)")
    parser.add_argument("json_path", nargs="?", help="Путь к etalon JSON")
    parser.add_argument("--skip-seed", action="store_true", help="Только файлы, без Postgres")
    parser.add_argument("--no-copy-assets", action="store_true", help="Не копировать медиа в pack assets")
    parser.add_argument("--golden", action="store_true", help="Проверить content_hash / слоты после импорта")
    parser.add_argument("--build-fixtures", action="store_true", help="Собрать demo-фикстуры")
    args = parser.parse_args(argv)

    # sanity: этот модуль не должен тянуть polish
    mod = sys.modules[__name__]
    for name in _FORBIDDEN:
        if name in getattr(mod, "__dict__", {}):
            raise SystemExit(f"Запрещённый символ в импортёре: {name}")

    if args.build_fixtures:
        from backend.scripts._build_etalon_fixtures import main as build_main

        build_main()
        return 0

    if not args.json_path:
        parser.error("Укажите json_path или --build-fixtures")

    import_etalon(
        Path(args.json_path),
        skip_seed=bool(args.skip_seed),
        copy_assets=not bool(args.no_copy_assets),
        golden=bool(args.golden),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
