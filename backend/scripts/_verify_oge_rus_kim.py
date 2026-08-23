from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
LOG = ROOT / "backend" / "scripts" / "_oge_rus_verify_out.txt"


def log(msg: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def main() -> int:
    if LOG.exists():
        LOG.unlink()
    try:
        from backend.scripts.oge_rus_convert import convert_variant

        path = ROOT / "backend/universal/packs/oge_rus/imports/oge_rus_var_kim.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        block, rows = convert_variant(raw)
        log(f"CONVERT_OK {block['context_id']} n={len(rows)} nums={sorted(r['task_number'] for r in rows)}")
        p1 = rows[0].get("figure_params") or {}
        p2 = rows[1].get("figure_params") or {}
        p4 = rows[3].get("figure_params") or {}
        p10 = rows[9].get("figure_params") or {}
        p13 = rows[12].get("figure_params") or {}
        log(f"listening={bool(p1.get('listening_text'))} grammar={bool(p2.get('grammar_text'))} matching={bool(p4.get('matching'))}")
        log(f"reading={bool(p10.get('reading_text'))} essay={len(p13.get('essay_options') or [])}")
        assert "Соль (хлорид натрия) организует" not in (rows[1].get("template_text") or "")
        assert "(1) Прежде чем увидеть Наилю" not in (rows[9].get("template_text") or "")
        # полный аудиоскрипт не дампим в условие (только зачин, как в КИМ)
        assert "окончательный выбор всегда остаётся" not in (rows[0].get("template_text") or "")
        assert "Текст для изложения (аудиоскрипт)" not in (rows[0].get("template_text") or "")
        log("TEXT_SEPARATION_OK")
    except Exception:
        log("CONVERT_FAIL")
        log(traceback.format_exc())
        return 1

    try:
        from backend.scripts.import_oge_rus_variants import run

        summary = run(json_path=path, skip_seed=False)
        log("IMPORT_OK " + json.dumps(summary, ensure_ascii=False)[:800])
    except SystemExit as e:
        log(f"IMPORT_EXIT {e}")
        try:
            summary = run(json_path=path, skip_seed=True)
            log("IMPORT_FILES_ONLY " + json.dumps(summary, ensure_ascii=False)[:500])
        except Exception:
            log(traceback.format_exc())
            return 2
    except Exception:
        log("IMPORT_FAIL")
        log(traceback.format_exc())
        try:
            from backend.scripts.import_oge_rus_variants import run as run2

            summary = run2(json_path=path, skip_seed=True)
            log("IMPORT_FILES_ONLY " + json.dumps(summary, ensure_ascii=False)[:500])
        except Exception:
            log(traceback.format_exc())
        return 2

    try:
        import asyncio
        import os

        os.environ["UNIVERSAL_VARY"] = "0"
        os.environ["BANK_VARY"] = "0"
        from backend.universal.variant_builder import generate_variant
        from backend.universal.adapt import universal_variant_to_questions

        async def once():
            v = await generate_variant("russian", "OGE", vary=False)
            assert len(v["tasks"]) == 13
            qs = universal_variant_to_questions(v)
            assert [q["num"] for q in qs] == list(range(1, 14))
            assert qs[0]["part"] == 2
            log(f"SMOKE_OK ctx={v['tasks'][0].get('context_id')} kim_nums={[q['num'] for q in qs]}")

        asyncio.run(once())
    except Exception:
        log("SMOKE_FAIL")
        log(traceback.format_exc())
        return 3

    log("ALL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
