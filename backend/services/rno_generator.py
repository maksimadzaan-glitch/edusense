"""Работа над ошибками: номера с баллом < max → новый вариант того же подтипа."""

from __future__ import annotations

import copy
import hashlib
import random
import time
from typing import Any, Callable, Optional

from backend.services.analytics_labels import subject_is_math, subject_is_russian
from backend.services.figures import attach_figure
from backend.services.grade_calculator import item_failed, item_num
from backend.services.math_mutator import (
    apply_mutator_logic_to_question,
    mutate_task_group,
    _mutate_one,
)


PickAlternate = Callable[[dict[str, Any], int], Optional[dict[str, Any]]]

# Русский: изложение / чтение / сочинение общие на класс — в РНО не подменяем.
RUS_LOCKED_SLOTS = frozenset({1, 10, 11, 12, 13})
# Математика ч.2: тот же сюжет, без новых чисел.
MATH_PART2_SLOTS = frozenset({20, 21, 22, 23, 24, 25})


def _as_num(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _question_num(q: dict[str, Any]) -> int:
    return _as_num(q.get("num") or q.get("task_number"))


def _has_plot_context(q: dict[str, Any]) -> bool:
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    if pl.get("math_context") or pl.get("context_id") or pl.get("asset_id") or pl.get("shared_story"):
        return True
    fp = q.get("figure_params") if isinstance(q.get("figure_params"), dict) else {}
    return bool(fp.get("theme") or fp.get("asset_id") or fp.get("base_vars"))


def item_missed_for_rno(item: Optional[dict[str, Any]]) -> bool:
    """В РНО: пустой, неверный или недобранный балл. Pending (ждёт проверки) — нет."""
    if not isinstance(item, dict):
        return False
    if not item_num(item):
        return False
    status = str(item.get("status") or "").lower()
    if status == "correct":
        return item_failed(item)
    if status in ("empty", "wrong"):
        return True
    if "pending" in status:
        return False
    return item_failed(item)


def _heat_get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def rno_title(source_title: Optional[str]) -> str:
    base = str(source_title or "").strip() or "Исходный тест"
    if base.lower().startswith("работа над ошибками"):
        return base[:200]
    title = f"Работа над ошибками: {base}"
    return title[:200]


def rno_seed(*parts: Any) -> int:
    raw = "|".join(str(p) for p in parts if p is not None).encode("utf-8")
    digest = hashlib.sha256(raw + str(time.time_ns()).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def exam_ui_for_rno(subject: Optional[str], questions: Optional[list[dict[str, Any]]] = None) -> Optional[str]:
    if subject_is_russian(subject):
        return "oge_rus_kim"
    for q in questions or []:
        if not isinstance(q, dict):
            continue
        pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        ui = pl.get("exam_ui") or q.get("exam_ui")
        if ui:
            return str(ui)
    return None


def collect_failed_task_ids(
    *,
    items: Optional[list[dict[str, Any]]] = None,
    heatmap: Optional[list[Any]] = None,
) -> list[int]:
    """Номера, которые ученик решил неверно или не написал (empty/wrong / heatmap misses)."""
    nums: set[int] = set()
    for it in items or []:
        if not isinstance(it, dict):
            continue
        if not item_missed_for_rno(it):
            continue
        n = item_num(it)
        if n:
            nums.add(n)

    for h in heatmap or []:
        n = _as_num(_heat_get(h, "num"))
        if not n:
            continue
        misses = int(_heat_get(h, "wrong_count", 0) or 0) + int(_heat_get(h, "empty_count", 0) or 0)
        if misses > 0:
            nums.add(n)

    if not nums:
        return []
    return sorted(nums)


def expand_plot_group(failed_nums: list[int], source_questions: list[dict[str, Any]]) -> list[int]:
    """1–5 на ОГЭ — один сюжет: если упал любой, берём всю пятёрку с исходным чертежом."""
    have = {_question_num(q) for q in source_questions or [] if isinstance(q, dict)}
    nums = [n for n in failed_nums if n]
    if any(n in {1, 2, 3, 4, 5} for n in nums):
        for n in (1, 2, 3, 4, 5):
            if n in have and n not in nums:
                nums.append(n)
    return sorted(set(nums))


def stamp_rno_meta(q: dict[str, Any], *, source_num: int, mutated: bool) -> dict[str, Any]:
    pl = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
    pl["source_num"] = source_num
    pl["remediation"] = True
    pl["rno"] = True
    pl["rno_mutated"] = bool(mutated)
    q["payload"] = pl
    q["num"] = source_num
    return q


def _shuffle_options(q: dict[str, Any]) -> bool:
    changed = False
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else None
    rng = random.Random()
    if pl:
        for key in ("options", "choices", "variants", "right", "left"):
            arr = pl.get(key)
            if isinstance(arr, list) and len(arr) > 1:
                shuffled = list(arr)
                rng.shuffle(shuffled)
                if shuffled != arr:
                    pl[key] = shuffled
                    changed = True
        q["payload"] = pl
    opts = q.get("options")
    if isinstance(opts, list) and len(opts) > 1:
        shuffled = list(opts)
        rng.shuffle(shuffled)
        if shuffled != opts:
            q["options"] = shuffled
            changed = True
    return changed


def mutate_question_unique(
    q: dict[str, Any],
    *,
    seed: int,
    math_mode: bool,
) -> bool:
    """Перегенерировать значения того же подтипа. True, если текст или ключ изменились."""
    original_text = str(q.get("text") or "")
    original_answer = str(q.get("answer") or "")
    for attempt in range(8):
        rng = random.Random(int(seed) + attempt * 7919 + _as_num(q.get("num")) * 10007)
        changed = False
        if math_mode:
            try:
                changed = bool(apply_mutator_logic_to_question(q, rng))
            except Exception:
                changed = False
            if not changed:
                pl = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
                pl.pop("mutator_values", None)
                q["payload"] = pl
                try:
                    changed = bool(_mutate_one(q, rng, math_mode=True))
                except Exception:
                    changed = False
        else:
            try:
                changed = bool(_mutate_one(q, rng, math_mode=False))
            except Exception:
                changed = False
            if not changed:
                changed = _shuffle_options(q)
        new_text = str(q.get("text") or "")
        new_answer = str(q.get("answer") or "")
        if changed and (new_text != original_text or new_answer != original_answer):
            if not _has_plot_context(q):
                attach_figure(q)
            return True
    if not math_mode:
        _shuffle_options(q)
    if not _has_plot_context(q):
        attach_figure(q)
    return str(q.get("text") or "") != original_text or str(q.get("answer") or "") != original_answer


def apply_rno_mutations(
    questions: list[dict[str, Any]],
    *,
    subject: Optional[str],
    seed: int,
) -> int:
    math_mode = subject_is_math(subject)
    mutated = 0
    group_changed = 0
    if math_mode:
        try:
            group_changed = int(mutate_task_group(questions, random.Random(int(seed)), enabled=True) or 0)
        except Exception:
            group_changed = 0
        if group_changed:
            mutated += group_changed
    group_nums = {1, 2, 3, 4, 5}
    for q in questions:
        if not isinstance(q, dict):
            continue
        num = _as_num(q.get("num"))
        if math_mode and num in MATH_PART2_SLOTS:
            stamp_rno_meta(q, source_num=num, mutated=False)
            continue
        if math_mode and group_changed and num in group_nums:
            stamp_rno_meta(q, source_num=num, mutated=True)
            if not _has_plot_context(q):
                attach_figure(q)
            continue
        q_seed = int(seed) ^ (num * 10007)
        ok = mutate_question_unique(q, seed=q_seed, math_mode=math_mode)
        if ok:
            mutated += 1
        stamp_rno_meta(q, source_num=num, mutated=ok or (math_mode and group_changed and num in group_nums))
        if not (math_mode and num in group_nums and _has_plot_context(q)):
            attach_figure(q)
    return mutated


def generate_rno(
    source_questions: list[dict[str, Any]],
    failed_nums: list[int],
    *,
    subject: Optional[str] = None,
    source_title: str = "",
    seed: Optional[int] = None,
    pick_alternate: Optional[PickAlternate] = None,
) -> dict[str, Any]:
    """Собрать новый КИМ из failedTaskIds: тот же подтип, новые значения мутатора."""
    by_num: dict[int, dict[str, Any]] = {}
    for q in source_questions or []:
        if not isinstance(q, dict):
            continue
        n = _question_num(q)
        if n:
            by_num[n] = q

    pick = sorted({n for n in (failed_nums or []) if n})
    used_alt = False
    assembled: list[dict[str, Any]] = []
    for num in pick:
        src = by_num.get(num)
        if not src:
            continue
        q = copy.deepcopy(src)
        q["num"] = num
        assembled.append(q)

    local_seed = int(seed) if seed is not None else rno_seed(source_title, pick)
    mutated_count = apply_rno_mutations(assembled, subject=subject, seed=local_seed)
    math_mode = subject_is_math(subject)

    # Математика: не подменять подтип чужим прототипом (печи → вклад).
    # Русский: для теста 2–9 всегда пробуем другую формулировку того же слота.
    if pick_alternate and not math_mode:
        for i, q in enumerate(assembled):
            num = _as_num(q.get("num"))
            if num in RUS_LOCKED_SLOTS:
                continue
            src = by_num.get(num)
            if not src:
                continue
            try:
                alt = pick_alternate(src, num)
            except Exception:
                alt = None
            if not alt or not isinstance(alt, dict):
                continue
            alt["num"] = num
            ok = mutate_question_unique(
                alt, seed=int(local_seed) ^ (num * 13007) ^ 4243, math_mode=False
            )
            stamp_rno_meta(alt, source_num=num, mutated=ok)
            attach_figure(alt)
            assembled[i] = alt
            used_alt = True
            if ok:
                mutated_count += 1

    title = rno_title(source_title)
    return {
        "title": title,
        "source_title": str(source_title or ""),
        "questions": assembled,
        "failed_nums": [_as_num(q.get("num")) for q in assembled if _as_num(q.get("num"))],
        "mutated_count": mutated_count,
        "used_alt": used_alt,
        "exam_ui": exam_ui_for_rno(subject, assembled),
    }
