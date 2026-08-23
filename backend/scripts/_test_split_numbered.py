"""Mirror of OgeRusUI.splitNumberedOptions — unit-check on the exact user string."""
from __future__ import annotations

import html
import re
import sys


def split_numbered_options(text: str) -> dict:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return {"stem": "", "options": []}

    line_re = re.compile(r"^(\d+)\)\s*(.+)$", re.M)
    line_opts = []
    first_idx = -1
    for m in line_re.finditer(raw):
        if first_idx < 0:
            first_idx = m.start()
        line_opts.append({"id": m.group(1), "text": m.group(2).strip()})
    if len(line_opts) >= 2:
        return {"stem": raw[:first_idx].strip(), "options": line_opts}

    marks = []
    for m in re.finditer(r"(\d+)\)(?=\s|$)", raw):
        pos = m.start()
        k = pos - 1
        while k >= 0 and raw[k] in " \t":
            k -= 1
        prev = raw[k] if k >= 0 else ""
        if prev and re.match(r"[A-Za-zА-Яа-яЁё0-9]", prev):
            continue
        after = m.end()
        text_start = after + 1 if after < len(raw) and raw[after].isspace() else after
        marks.append({"id": m.group(1), "pos": pos, "textStart": text_start})

    if len(marks) < 2 or marks[0]["id"] != "1":
        return {"stem": raw, "options": []}

    kept = []
    for i, mk in enumerate(marks):
        if int(mk["id"]) != i + 1:
            break
        kept.append(mk)
    if len(kept) < 2:
        return {"stem": raw, "options": []}
    marks = kept

    options = []
    for i, mk in enumerate(marks):
        end = marks[i + 1]["pos"] if i + 1 < len(marks) else len(raw)
        options.append({"id": mk["id"], "text": raw[mk["textStart"] : end].strip()})
    return {"stem": raw[: marks[0]["pos"]].strip(), "options": options}


def format_prose_html(text: str) -> str:
    parsed = split_numbered_options(text)
    parts = []
    if parsed["stem"]:
        stem = html.escape(parsed["stem"]).replace("\n", "<br>")
        parts.append(f'<div class="oge-prose-stem">{stem}</div>')
    if parsed["options"]:
        rows = []
        for o in parsed["options"]:
            rows.append(
                '<div class="oge-prose-opt" role="listitem">'
                f'<span class="oge-prose-opt-id">{html.escape(o["id"])})</span> '
                f'<span class="oge-prose-opt-text">{html.escape(o["text"])}</span>'
                "</div>"
            )
        parts.append(
            '<div class="oge-prose-options" role="list">' + "".join(rows) + "</div>"
        )
    return "".join(parts)


FLAT = (
    "Укажите варианты ответов, в которых верно определена грамматическая основа "
    "в одном из предложений или в одной из частей сложного предложения текста. "
    "Запишите номера ответов. "
    "1) соль поддерживает (предложение 1) "
    "2) может привести (предложение 2) "
    "3) соль содержится (предложение 3) "
    "4) организм получает (предложение 4) "
    "5) он поглощает (предложение 5)"
)


def main() -> int:
    print("=== BEFORE (FLAT) ===")
    print(FLAT)
    r = split_numbered_options(FLAT)
    print("=== AFTER ===")
    print("stem:", r["stem"])
    print("n_options:", len(r["options"]))
    for o in r["options"]:
        print(f"  {o['id']}) {o['text']}")
    html_out = format_prose_html(FLAT)
    print("=== HTML ===")
    print(html_out)
    assert len(r["options"]) == 5, r
    assert r["options"][0]["id"] == "1"
    assert all(re.search(r"\(предложение \d+\)", o["text"]) for o in r["options"])
    assert html_out.count("oge-prose-opt") >= 5
    # multiline path
    multi = FLAT.replace(") ", ")\n").replace("ответов. 1)", "ответов.\n1)")
    r2 = split_numbered_options(
        "Укажите варианты ответов, в которых верно определена грамматическая основа "
        "в одном из предложений или в одной из частей сложного предложения текста. "
        "Запишите номера ответов.\n"
        "1) соль поддерживает (предложение 1)\n"
        "2) может привести (предложение 2)\n"
        "3) соль содержится (предложение 3)\n"
        "4) организм получает (предложение 4)\n"
        "5) он поглощает (предложение 5)"
    )
    assert len(r2["options"]) == 5, r2
    print("OK split_numbered_options")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
