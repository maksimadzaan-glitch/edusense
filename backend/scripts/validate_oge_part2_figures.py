"""Валидация чертежей части 2 ОГЭ math (pack SVG + figure_data ссылки).

Запуск из корня проекта:
  python -m backend.scripts.validate_oge_part2_figures

Проверки:
  - файл по main_figure_url существует
  - нет <script
  - есть viewBox и класс geo-fig / fipi-fig
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services.figures import (
    is_safe_pack_svg,
    load_pack_figure_svg,
    normalize_pack_figure_url,
    resolve_pack_figure_path,
)
from backend.universal.packs.loader import pack_dir

PACK_ID = "oge_math"
SPEC_PATH = _ROOT / "backend" / "universal" / "specs" / "math_oge.json"
SAMPLES_PATH = (
    pack_dir(PACK_ID) / "tasks" / "part2" / "figures_part2_samples.json"
)


def _collect_figure_data_refs() -> list[tuple[str, dict]]:
    refs: list[tuple[str, dict]] = []

    if SPEC_PATH.is_file():
        data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        for i, p in enumerate(data.get("prototypes") or []):
            fd = p.get("figure_data")
            if isinstance(fd, dict) and fd.get("main_figure_url"):
                title = p.get("prototype_title") or f"proto[{i}]"
                refs.append((f"math_oge.json::{title}", fd))

    if SAMPLES_PATH.is_file():
        data = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
        for i, s in enumerate(data.get("samples") or []):
            fd = s.get("figure_data")
            if isinstance(fd, dict) and fd.get("main_figure_url"):
                code = s.get("subtype_code") or f"sample[{i}]"
                refs.append((f"figures_part2_samples.json::{code}", fd))

    sample_task = pack_dir(PACK_ID) / "tasks" / "part2" / "task_23_sample.json"
    if sample_task.is_file():
        data = json.loads(sample_task.read_text(encoding="utf-8"))
        fd = data.get("figure_data")
        if isinstance(fd, dict) and fd.get("main_figure_url"):
            refs.append(("task_23_sample.json", fd))

    return refs


def _validate_known_files() -> list[str]:
    errors: list[str] = []
    fig_dir = pack_dir(PACK_ID) / "assets" / "figures" / "part2"
    expected = [
        "q23_sample_main.svg",
        "q24_sample_main.svg",
        "q25_sample_main.svg",
    ]
    for name in expected:
        path = fig_dir / name
        if not path.is_file():
            errors.append(f"missing file: {path}")
            continue
        raw = path.read_text(encoding="utf-8")
        if not is_safe_pack_svg(raw):
            errors.append(f"unsafe/invalid SVG: {path.name}")
    return errors


def main() -> int:
    errors = _validate_known_files()
    refs = _collect_figure_data_refs()
    if not refs:
        errors.append("no figure_data.main_figure_url references found")

    seen: set[str] = set()
    for label, fd in refs:
        url = str(fd.get("main_figure_url") or "").strip()
        rel = normalize_pack_figure_url(url)
        path = resolve_pack_figure_path(url, pack_id=PACK_ID)
        key = f"{label} -> {rel}"
        if key in seen:
            continue
        seen.add(key)
        if path is None:
            errors.append(f"{label}: file not found for {url!r}")
            continue
        svg = load_pack_figure_svg(url, pack_id=PACK_ID)
        if not svg:
            errors.append(f"{label}: SVG failed safety check ({path.name})")

    print(f"checked {len(seen)} figure_data refs + sample files")
    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: part2 figure assets valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
