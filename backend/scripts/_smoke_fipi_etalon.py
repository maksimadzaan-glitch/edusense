"""Smoke: import etalon fixtures + generate mode=etalon."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


async def main() -> int:
    from backend.scripts.import_fipi_variant import import_etalon
    from backend.scripts._build_etalon_fixtures import main as build_fixtures
    from backend.universal.adapt import universal_variant_to_questions
    from backend.universal.variant_builder import generate_variant

    build_fixtures()

    rus = (
        _ROOT
        / "backend/universal/packs/oge_rus/fixtures/etalon/oge_rus_var_kim.etalon.json"
    )
    math = (
        _ROOT
        / "backend/universal/packs/oge_math/fixtures/etalon/oge_math_demo_01.etalon.json"
    )

    r_sum = import_etalon(rus, golden=True)
    m_sum = import_etalon(math, golden=True)
    print("IMPORT RUS ok", r_sum["content_hash"], r_sum["slot_count"])
    print("IMPORT MATH ok", m_sum["content_hash"], m_sum["slot_count"])

    for sc, label in (("russian", "RUS"), ("math", "MATH")):
        v = await generate_variant(sc, "OGE", vary=True, mode="etalon")
        assert v.get("etalon") is True, v.keys()
        assert v.get("provenance"), "no provenance"
        tasks = v.get("tasks") or []
        assert len(tasks) == (13 if sc == "russian" else 25), len(tasks)
        # vary must not mutate: first statement equals import for slot 1
        t1 = next(t for t in tasks if int(t["task_number"]) == 1)
        assert t1.get("etalon") or (t1.get("payload") or {}).get("etalon")
        if sc == "math":
            urls = (t1.get("payload") or {}).get("image_urls") or []
            assert urls, "math q1 must keep image_urls"
            assert all("/packs/" in u or u.startswith("assets/") for u in urls), urls
        qs = universal_variant_to_questions(v)
        assert len(qs) == len(tasks)
        # polish must not wipe passage numbers for rus
        if sc == "russian":
            g = next(
                (
                    q
                    for q in qs
                    if (q.get("payload") or {}).get("grammar_text")
                ),
                None,
            )
            assert g and "(1)" in str((g.get("payload") or {}).get("grammar_text")), g
        print(
            f"GENERATE {label} ok etalon={v.get('etalon')} "
            f"slots={len(tasks)} prov={v.get('provenance', {}).get('variant_code')} "
            f"hash={v.get('provenance', {}).get('content_hash', '')[:20]}"
        )

    print(json.dumps({"ok": True, "rus_hash": r_sum["content_hash"], "math_hash": m_sum["content_hash"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
