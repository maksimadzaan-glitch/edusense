"""Пополнить банк ОГЭ русский оригинальными вариантами (LLM → импорт → аудио).

  py -3 -m backend.scripts.autogen_oge_rus
  py -3 -m backend.scripts.autogen_oge_rus --count 2 --tema память
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Autogen original OGE Russian variants")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--tema", default="")
    args = ap.parse_args()

    from backend.services.oge_rus_autogen import autogen_many

    result = asyncio.run(autogen_many(args.count, tema=args.tema or None))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
