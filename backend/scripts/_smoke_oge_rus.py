"""Smoke: generate russian/OGE several times (vary=False). КИМ 1–13."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["UNIVERSAL_VARY"] = "0"
os.environ["BANK_VARY"] = "0"

from backend.universal.variant_builder import generate_variant  # noqa: E402
from backend.universal.adapt import universal_variant_to_questions  # noqa: E402


async def main() -> int:
    seen: set[str] = set()
    n = 5
    for i in range(n):
        v = await generate_variant("russian", "OGE", vary=False)
        tasks = v["tasks"]
        assert len(tasks) == 13, len(tasks)
        nums = [t["task_number"] for t in tasks]
        assert nums == list(range(1, 14)), nums
        locked = {
            t.get("context_id")
            for t in tasks
            if int(t["task_number"]) in {1, 2, 3, 10, 11, 12, 13}
        }
        assert len(locked) == 1, locked
        cid = next(iter(locked))
        assert cid
        free = {
            t.get("context_id")
            for t in tasks
            if int(t["task_number"]) in {4, 5, 6, 7, 8, 9}
        }
        assert not (free - {cid, "oge_rus_pool_49"}), free
        # неполные legacy и чужие авторы не должны попадать в generate
        assert not str(cid).endswith(("_01", "_02", "_03", "_04", "_05")), cid
        assert str(cid) not in {
            "oge_rus_var_a",
            "oge_rus_var_kim",
            "oge_rus_var_friendship",
            "oge_rus_var_books",
            "oge_rus_var_courage",
        }, cid
        seen.add(str(cid))
        empty = [t["task_number"] for t in tasks if not (t.get("text") or "").strip()]
        assert not empty, (cid, empty)
        assert tasks[0]["part"] == 2 and tasks[12]["part"] == 2
        assert all(tasks[j]["part"] == 1 for j in range(1, 12))
        assert tasks[0].get("max_score") == 7
        assert tasks[12].get("max_score") == 7
        assert all(tasks[j].get("max_score") == 1 for j in range(1, 12))
        p1 = tasks[0].get("payload") or {}
        assert p1.get("oge_rus") and p1.get("listening_text"), p1.keys()
        assert (p1.get("rubric") or {}).get("kind") == "izlozhenie", p1.get("rubric")
        assert len(p1.get("listening_text") or "") > 80, cid
        p2 = tasks[1].get("payload") or {}
        assert p2.get("grammar_text") and len(p2.get("grammar_text") or "") > 40, cid
        p3 = tasks[2].get("payload") or {}
        assert p3.get("grammar_text") and p3.get("grammar_text") == p2.get("grammar_text"), cid
        p4 = tasks[3].get("payload") or {}
        assert p4.get("matching"), p4.keys()
        p10 = tasks[9].get("payload") or {}
        assert p10.get("reading_text") and len(p10.get("reading_text") or "") > 80, cid
        p13 = tasks[12].get("payload") or {}
        assert p13.get("essay_options") and len(p13["essay_options"]) == 3
        assert (p13.get("rubric") or {}).get("kind") == "sochinenie", p13.get("rubric")
        qs = universal_variant_to_questions(v)
        assert [q["num"] for q in qs] == list(range(1, 14)), [q["num"] for q in qs]
        assert qs[0]["part"] == 2 and qs[0]["type"].startswith("Тип")
        assert (qs[1].get("payload") or {}).get("grammar_text")
        assert (qs[2].get("payload") or {}).get("grammar_text")
        gtxt = (qs[1].get("payload") or {}).get("grammar_text") or ""
        assert "Соль" in gtxt or "(1)" in gtxt or len(gtxt) > 40
        print(f"ok #{i + 1} ctx={cid} payloads=ok kim_order=ok grammar2+3=ok")
    print("unique_contexts", sorted(seen), "count", len(seen), f"of {n} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
