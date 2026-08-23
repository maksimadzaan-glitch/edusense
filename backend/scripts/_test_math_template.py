"""Проверка generate_math_task (шаблоны мутатора ОГЭ математики).

  py -3 -m backend.scripts._test_math_template
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from backend.services.math_mutator import generate_math_task, apply_mutator_logic_to_question

SPEC = (
    Path(__file__).resolve().parents[1]
    / "universal"
    / "specs"
    / "math_oge_mutator.json"
)


def _load_prototypes() -> list[dict]:
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    return list(data.get("prototypes") or [])


def _as_template(proto: dict) -> dict:
    fp = proto.get("figure_params") if isinstance(proto.get("figure_params"), dict) else {}
    return {
        "template": proto.get("template_text"),
        "mutator_logic": fp.get("mutator_logic"),
        "explanation_template": fp.get("explanation_template") or proto.get("template_solution"),
    }


def main() -> int:
    errors: list[str] = []
    rng = random.Random(20260816)

    tz = {
        "template": "Найдите больший корень уравнения: x² + {b}x + {c} = 0",
        "mutator_logic": {
            "variables": {
                "x1": "random_int(-10, 10)",
                "x2": "random_int(-10, 10, exclude=[x1])",
            },
            "computed": {
                "b": "-(x1 + x2)",
                "c": "x1 * x2",
                "answer": "max(x1, x2)",
            },
        },
        "explanation_template": "Корни: {x1} и {x2}. Больший = {answer}.",
    }
    one = generate_math_task(tz, rng)
    vals = one["values"]
    if int(vals["b"]) != -(int(vals["x1"]) + int(vals["x2"])):
        errors.append(f"TZ b mismatch {vals}")
    if int(vals["c"]) != int(vals["x1"]) * int(vals["x2"]):
        errors.append(f"TZ c mismatch {vals}")
    if str(one["answer"]) != str(max(int(vals["x1"]), int(vals["x2"]))):
        errors.append(f"TZ answer mismatch {one['answer']} {vals}")
    if "{b}" in one["text"] or "{c}" in one["text"]:
        errors.append(f"TZ placeholders left: {one['text']}")

    protos = _load_prototypes()
    if len(protos) < 14:
        errors.append(f"expected at least 14 mutator prototypes, got {len(protos)}")

    for proto in protos:
        num = int(proto.get("task_number") or 0)
        fp = proto.get("figure_params") if isinstance(proto.get("figure_params"), dict) else {}
        if not isinstance(fp.get("mutator_logic"), dict):
            continue
        seen = set()
        for i in range(8):
            got = generate_math_task(_as_template(proto), random.Random(1000 + num * 17 + i))
            if not str(got.get("answer") or "").strip():
                errors.append(f"#{num} empty answer")
                break
            if "{" in str(got.get("text") or ""):
                errors.append(f"#{num} leftover placeholder: {got['text']}")
                break
            seen.add(str(got["answer"]) + "|" + got["text"])
            q = {
                "num": num,
                "part": 1,
                "text": proto.get("template_text"),
                "answer": proto.get("template_answer"),
                "payload": {
                    "mutator_logic": fp["mutator_logic"],
                    "mutator_template": proto["template_text"],
                    "explanation_template": fp.get("explanation_template"),
                    "subtype_code": fp.get("subtype_code"),
                },
                "figure_params": {"subtype_code": fp.get("subtype_code")},
            }
            if not apply_mutator_logic_to_question(q, random.Random(50 + i)):
                errors.append(f"#{num} apply_mutator_logic_to_question failed")
                break
            if "{" in str(q.get("text") or ""):
                errors.append(f"#{num} apply left placeholder: {q['text']}")
                break
        if len(seen) < 2:
            errors.append(f"#{num} not enough variety ({len(seen)})")

    from backend.services.math_mutator import fill_math_templates

    kit_q = [
        {
            "num": 1,
            "part": 1,
            "text": "сюжет",
            "payload": {"context_id": "dacha_sosnovoe"},
        },
        {
            "num": 10,
            "part": 1,
            "text": "старый текст",
            "answer": "0.1",
            "payload": {},
        },
        {
            "num": 14,
            "part": 1,
            "text": "старый текст",
            "answer": "1",
            "payload": {},
        },
        {
            "num": 16,
            "part": 1,
            "text": "старый текст",
            "answer": "1",
            "payload": {},
        },
        {
            "num": 17,
            "part": 1,
            "text": "старый текст",
            "answer": "1",
            "payload": {},
        },
    ]
    fill_math_templates(kit_q, random.Random(11))
    if "России" not in str(kit_q[1].get("text") or ""):
        errors.append(f"kit stamp q10 expected queue, got {kit_q[1].get('text')!r}")
    if "бактери" not in str(kit_q[2].get("text") or ""):
        errors.append(f"kit stamp q14 expected geom, got {kit_q[2].get('text')!r}")
    if "вписан" not in str(kit_q[3].get("text") or "").lower():
        errors.append(f"kit stamp q16 expected cyclic quad, got {kit_q[3].get('text')!r}")
    if "треугольника" not in str(kit_q[4].get("text") or ""):
        errors.append(f"kit stamp q17 expected triangle area, got {kit_q[4].get('text')!r}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("ok", len(protos), "mutator templates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
