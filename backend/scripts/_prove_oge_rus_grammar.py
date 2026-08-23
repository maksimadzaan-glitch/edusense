"""Локальная проверка: grammar_text в payload 2+3 + HTML пассажа."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def format_passage_like_js(raw: str) -> str:
    """Упрощённый аналог formatPassageHtml для smoke без браузера."""
    t = raw.replace("\r\n", "\n")
    t = re.sub(r'([.!?…»"])\s+(?=\(\d+\))', r"\1\n", t)
    t = re.sub(r'([.!?…»"])(?=\(\d+\))', r"\1\n", t)
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    parts = []
    for line in lines:
        marked = re.sub(r"\((\d+)\)", r'<span class="oge-sent-num">(\1)</span>', line)
        parts.append(f'<span class="oge-sent-line">{marked}</span>')
    return '<p class="oge-passage-p">' + "".join(parts) + "</p>"


def main() -> int:
    # 1) convert kim → figure_params
    from backend.scripts.oge_rus_convert import convert_variant

    path = _ROOT / "backend/universal/packs/oge_rus/imports/oge_rus_var_kim.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    block, rows = convert_variant(raw)
    by_num = {int(r["task_number"]): r for r in rows}
    p2 = by_num[2].get("figure_params") or {}
    p3 = by_num[3].get("figure_params") or {}
    assert p2.get("grammar_text"), "task2 missing grammar_text after convert"
    assert p3.get("grammar_text"), "task3 missing grammar_text after convert"
    assert p2["grammar_text"] == p3["grammar_text"]
    assert "Соль (хлорид натрия)" in p2["grammar_text"]
    html = format_passage_like_js(p2["grammar_text"])
    assert "oge-sent-num" in html
    assert "(1)" in html
    assert "oge-sent-line" in html
    print("CONVERT+HTML_OK", len(p2["grammar_text"]), "chars, lines~", html.count("oge-sent-line"))

    # 2) optional live generate
    try:
        import asyncio
        import os

        os.environ["UNIVERSAL_VARY"] = "0"
        from backend.universal.variant_builder import generate_variant
        from backend.universal.adapt import universal_variant_to_questions

        async def once():
            v = await generate_variant("russian", "OGE", vary=False)
            qs = universal_variant_to_questions(v)
            g2 = (qs[1].get("payload") or {}).get("grammar_text") or ""
            g3 = (qs[2].get("payload") or {}).get("grammar_text") or ""
            assert g2 and g3 and g2 == g3
            print("GENERATE_OK", v["tasks"][0].get("context_id"), "grammar_len", len(g2))

        asyncio.run(once())
    except Exception as exc:
        print("GENERATE_SKIP", type(exc).__name__, exc)

    print("ALL_LOCAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
