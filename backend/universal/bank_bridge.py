"""Мост: bank_data → universal JSON-прототипы с template_*."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

VARY_HINT = "Измени числа и формулировку условия, сохрани тип задания и корректный ответ."


def _default_solution(text: str, answer: str) -> str:
    return (
        "Решение.\n"
        f"1) Условие: {text}\n"
        "2) Выполним необходимые преобразования и вычисления.\n"
        f"3) Ответ: {answer}."
    )


def prototypes_from_bank_tasks(
    tasks: list[dict[str, Any]],
    *,
    part1_last: int,
    max_per_slot: int = 4,
) -> list[dict[str, Any]]:
    """Сгруппировать банк по slot → несколько прототипов с готовыми шаблонами."""
    by_slot: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for t in tasks:
        try:
            slot = int(t.get("slot"))
        except (TypeError, ValueError):
            continue
        text = str(t.get("text") or "").strip()
        answer = str(t.get("answer") or "").strip()
        if not text or not answer:
            continue
        by_slot[slot].append(t)

    out: list[dict[str, Any]] = []
    for slot in sorted(by_slot.keys()):
        items = by_slot[slot][:max_per_slot]
        for idx, t in enumerate(items, start=1):
            part = int(t.get("part") or (1 if slot <= part1_last else 2))
            topic = str(t.get("topic") or "Задание").strip() or "Задание"
            title = f"{topic} · ex{idx}"
            text = str(t["text"]).strip()
            answer = str(t["answer"]).strip()
            proto: dict[str, Any] = {
                "task_number": slot,
                "part": part,
                "prototype_title": title,
                "prompt_instruction": VARY_HINT,
                "template_text": text,
                "template_answer": answer,
            }
            if part == 2:
                proto["template_solution"] = _default_solution(text, answer)
            out.append(proto)
    return out
