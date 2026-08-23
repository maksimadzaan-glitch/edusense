"""Типы сюжетного блока ОГЭ математика 1–5 (Parent-Child).

На фронте то же самое в JSDoc ``frontend/js/math_oge_ui.js``.
Стек — vanilla JS + FastAPI, не React/Next.
"""

from __future__ import annotations

from typing import Any, TypedDict


class TaskContext(TypedDict, total=False):
    title: str
    story_text: str
    asset_id: str
    base_vars: dict[str, Any]
    figure_kind: str | None
    figure_svg: str | None
    figure_url: str | None


class TaskSubtask(TypedDict, total=False):
    task_num: int
    question: str
    type: str
    answer: str


class TaskGroup(TypedDict, total=False):
    group_id: str
    context: TaskContext
    subtasks: list[TaskSubtask]


class TaskTemplate(TypedDict, total=False):
    template_text: str
    mutator_logic: dict[str, Any]
    explanation_template: str
    group_mutator_logic: dict[str, Any]
