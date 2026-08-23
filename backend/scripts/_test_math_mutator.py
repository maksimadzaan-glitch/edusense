"""Проверка мутатора на эталонных условиях ОГЭ математики.

  py -3 -m backend.scripts._test_math_mutator
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.services.math_mutator import personalize_questions

PACK = (
    Path(__file__).resolve().parents[1]
    / "universal"
    / "packs"
    / "oge_math"
    / "imports"
    / "oge_math_finish_v1.json"
)


def _questions_from_pack() -> list[dict]:
    data = json.loads(PACK.read_text(encoding="utf-8"))
    out = []
    for t in data.get("tasks") or []:
        num = int(t.get("task_number") or 0)
        out.append(
            {
                "num": num,
                "part": 2 if num >= 20 else 1,
                "text": t.get("statement") or "",
                "answer": str(t.get("correct_answer") or ""),
                "acceptable_answers": list(t.get("acceptable_answers") or []),
                "payload": {},
            }
        )
    return out


def main() -> int:
    base = _questions_from_pack()
    a, n_a = personalize_questions(
        base, assignment_id=41, student_name="Иванов Иван", subject="Математика"
    )
    b, n_b = personalize_questions(
        base, assignment_id=41, student_name="Петрова Анна", subject="Математика"
    )
    a2, n_a2 = personalize_questions(
        base, assignment_id=41, student_name="Иванов Иван", subject="Математика"
    )
    off, n_off = personalize_questions(
        base,
        assignment_id=41,
        student_name="Иванов Иван",
        subject="Математика",
        enabled=False,
    )

    errors: list[str] = []
    if n_off != 0:
        errors.append(f"enabled=False must be 0, got {n_off}")
    if n_a < 6:
        errors.append(f"expected >=6 mutated for Ivan, got {n_a}")
    if n_b < 6:
        errors.append(f"expected >=6 mutated for Anna, got {n_b}")
    if n_a != n_a2:
        errors.append(f"unstable count {n_a} vs {n_a2}")

    by_a = {q["num"]: q for q in a}
    by_a2 = {q["num"]: q for q in a2}
    by_b = {q["num"]: q for q in b}
    by_off = {q["num"]: q for q in off}

    for num in by_a:
        if by_a[num]["text"] != by_a2[num]["text"] or by_a[num]["answer"] != by_a2[num]["answer"]:
            errors.append(f"#{num} not stable for same student")
        if by_a[num]["text"] != by_off[num]["text"] and by_a[num]["answer"] == by_off[num]["answer"]:
            # mutated text should usually change the key; warn only if both same
            pass

    # two students should differ on at least one numeric slot
    differ = 0
    for num in (6, 8, 9, 10, 12, 14, 15, 16, 17, 1, 7, 13, 19):
        if num not in by_a:
            continue
        if by_a[num]["answer"] != by_b[num]["answer"] or by_a[num]["text"] != by_b[num]["text"]:
            differ += 1
    if differ < 3:
        errors.append(f"two students too similar (differ={differ})")

    # part 2 must stay
    for num in (20, 21, 22, 23, 24, 25):
        if num in by_a and by_a[num]["text"] != by_off[num]["text"]:
            errors.append(f"part2 #{num} was mutated")

    # square equation: answer is sqrt of the constant
    import re

    m = re.search(r"x\^2\s*-\s*(\d+)\s*=\s*0", by_a[9]["text"])
    if not m:
        errors.append("slot 9 pattern lost")
    else:
        n = int(m.group(1))
        root = int(n**0.5)
        if str(root) != str(by_a[9]["answer"]):
            errors.append(f"slot 9 answer {by_a[9]['answer']} != sqrt({n})")

    kinds = [
        (q.get("payload") or {}).get("unique_kind")
        for q in a
        if (q.get("payload") or {}).get("unique")
    ]
    print("mutated", n_a, "kinds", sorted({k for k in kinds if k}))
    print("ivan9", by_a[9]["answer"], "anna9", by_b[9]["answer"])
    print("ivan10", by_a[10]["answer"], "anna10", by_b[10]["answer"])
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
