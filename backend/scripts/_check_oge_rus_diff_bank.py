"""Проверка новых вариантов 10×3 перед импортом."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.universal.variant_builder import OGE_RUS_CONTEXT_DIFFICULTY

IMP = _ROOT / "backend" / "universal" / "packs" / "oge_rus" / "imports"
BANNED = (
    "хлорид натрия",
    "наилю",
    "наили",
    "универсального рецепта",
    "яковлев",
    "паустовск",
    "железников",
    "лиханов",
)


def main() -> int:
    errors: list[str] = []
    by_diff: dict[str, list[str]] = {"easy": [], "medium": [], "hard": []}
    for cid, diff in sorted(OGE_RUS_CONTEXT_DIFFICULTY.items()):
        path = IMP / f"{cid}.json"
        if not path.is_file():
            errors.append(f"нет файла {path.name}")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(raw, ensure_ascii=False).lower()
        for bad in BANNED:
            if bad in blob:
                errors.append(f"{cid}: запрещено «{bad}»")
        listen = (raw.get("listening_text") or {}).get("audio_script") or ""
        words = len(re.findall(r"[А-Яа-яЁёA-Za-z]+", str(listen)))
        if words < 160:
            errors.append(f"{cid}: изложение {words} слов")
        reading = (raw.get("reading_text") or {}).get("content") or ""
        n = len(re.findall(r"\(\d+\)", str(reading)))
        if n < 32:
            errors.append(f"{cid}: рассказ {n} предл.")
        nums = {
            int(t["task_number"])
            for t in (raw.get("tasks") or [])
            if isinstance(t, dict) and t.get("task_number")
        }
        if not set(range(2, 14)) <= nums:
            errors.append(f"{cid}: слоты {sorted(nums)}")
        by_diff.setdefault(diff, []).append(cid)
    for diff, ids in by_diff.items():
        print(f"{diff}: {len(ids)} {ids}")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(" -", e)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
