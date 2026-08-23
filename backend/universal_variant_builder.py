"""CLI / тонкая обёртка над backend.universal.variant_builder.

Примеры:
  python -m backend.universal_variant_builder --subject math --exam OGE
  set UNIVERSAL_VARY=0 && python -m backend.universal_variant_builder --subject math --exam OGE
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.universal.variant_builder import UniversalGenerateError, generate_variant


async def _run(subject: str, exam: str) -> int:
    def _print_progress(msg: str) -> None:
        print(msg, flush=True)

    try:
        variant = await generate_variant(subject, exam, progress=_print_progress)
    except UniversalGenerateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(variant, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    # Windows cp1251 ломается на символах вроде − / √ в шаблонах
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Universal PostgreSQL variant builder")
    parser.add_argument("--subject", required=True, help="subject_code, напр. math")
    parser.add_argument("--exam", required=True, help="exam_code, напр. OGE | EGE")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.subject, args.exam)))


if __name__ == "__main__":
    main()
