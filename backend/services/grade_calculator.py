"""Пересчёт первичных баллов ОГЭ → оценка 2–5 (математика и русский)."""

from __future__ import annotations

from typing import Any, Iterable, Optional

MATH_MAX = 31
RUS_MAX = 33
LIT_MAX = 8
GEO_NUMS = (15, 16, 17, 18, 19, 23, 24, 25)
GEO_DEFAULT_MAX = {
    15: 1,
    16: 1,
    17: 1,
    18: 1,
    19: 1,
    23: 2,
    24: 2,
    25: 2,
}
MATH_MODULES = (
    ("practice", "Практика 1–5", (1, 2, 3, 4, 5)),
    ("algebra", "Алгебра", (6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 21, 22)),
    ("geometry", "Геометрия", GEO_NUMS),
)
RUS_CONTENT_MODULES = (
    ("izlozhenie", "Изложение", (1,)),
    ("test", "Тест", (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)),
    ("sochinenie", "Сочинение", (13,)),
)
LIT_KEYS = ("gk1", "gk2", "gk3", "gk4", "fk1", "literacy")


def normalize_subject(raw: Any) -> str:
    s = str(raw or "").lower().replace("ё", "е").strip()
    if not s:
        return "math"
    if s in ("math", "mathematics", "math_base") or "матем" in s:
        return "math"
    if (
        s in ("russian", "rus", "ru")
        or "русск" in s
        or "russian" in s
    ):
        return "russian"
    return s


def max_primary(subject: Any) -> int:
    return RUS_MAX if normalize_subject(subject) == "russian" else MATH_MAX


def mark_from_scale(score: int, subject: Any) -> str:
    """Оценка только по шкале, без порога геометрии/грамотности."""
    p = int(score)
    if normalize_subject(subject) == "russian":
        if p <= 14:
            return "2"
        if p <= 22:
            return "3"
        if p <= 28:
            return "4"
        return "5"
    if p <= 7:
        return "2"
    if p <= 14:
        return "3"
    if p <= 21:
        return "4"
    return "5"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _item_num(item: dict[str, Any]) -> int:
    try:
        return int(item.get("num") or 0)
    except (TypeError, ValueError):
        return 0


def _is_pending(item: dict[str, Any]) -> bool:
    status = str(item.get("status") or "").lower()
    return "pending" in status or status in ("ai_pending", "manual_pending")


def _item_max(item: dict[str, Any], fallback: float = 1.0) -> float:
    if item.get("max_score") is not None:
        return max(0.0, _as_float(item.get("max_score"), fallback))
    if item.get("maxScore") is not None:
        return max(0.0, _as_float(item.get("maxScore"), fallback))
    return fallback


def _item_earned(item: dict[str, Any]) -> float:
    if _is_pending(item):
        return 0.0
    if item.get("earned") is not None:
        return max(0.0, _as_float(item.get("earned")))
    status = str(item.get("status") or "").lower()
    if status == "correct":
        return _item_max(item, 1.0)
    return 0.0


def item_num(item: Optional[dict[str, Any]]) -> int:
    if not isinstance(item, dict):
        return 0
    return _item_num(item)


def item_failed(item: Optional[dict[str, Any]]) -> bool:
    """True, если задание проверено и балл строго ниже максимума."""
    if not isinstance(item, dict):
        return False
    if _is_pending(item):
        return False
    if not _item_num(item):
        return False
    mx = _item_max(item)
    if mx <= 0:
        return False
    return _item_earned(item) + 1e-9 < mx


def _sum_literacy(blob: Any) -> Optional[float]:
    if blob is None:
        return None
    if isinstance(blob, (int, float)):
        return float(blob)
    if not isinstance(blob, dict):
        return None
    total = 0.0
    found = False
    for key, val in blob.items():
        lk = str(key).lower()
        if lk in LIT_KEYS or lk.startswith("gk") or lk.startswith("fk"):
            if isinstance(val, dict):
                total += _as_float(val.get("earned", val.get("score")))
            else:
                total += _as_float(val)
            found = True
    return total if found else None


def extract_literacy_score(review: Optional[dict[str, Any]], items: Iterable[dict[str, Any]]) -> Optional[float]:
    if isinstance(review, dict):
        if review.get("literacy_score") is not None:
            return _as_float(review.get("literacy_score"))
        lit = review.get("literacy")
        got = _sum_literacy(lit)
        if got is not None:
            return got
        criteria = _sum_literacy(review.get("criteria") or review.get("rubric_scores"))
        if criteria is not None:
            return criteria
    total = 0.0
    found = False
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("literacy_earned") is not None:
            total += _as_float(item.get("literacy_earned"))
            found = True
            continue
        got = _sum_literacy(
            item.get("literacy") or item.get("criteria") or item.get("rubric_scores")
        )
        if got is not None:
            total += got
            found = True
    return total if found else None


def _module_block(
    items_by_num: dict[int, dict[str, Any]],
    module_id: str,
    label: str,
    nums: Iterable[int],
    default_max: Optional[dict[int, int]] = None,
) -> dict[str, Any]:
    earned = 0.0
    max_score = 0.0
    pending = False
    present = False
    for n in nums:
        item = items_by_num.get(n)
        fallback = float((default_max or {}).get(n, 1))
        if item:
            present = True
            earned += _item_earned(item)
            max_score += _item_max(item, fallback)
            if _is_pending(item):
                pending = True
        elif default_max and n in default_max:
            max_score += fallback
    if not present and not max_score:
        max_score = float(sum((default_max or {}).get(n, 1) for n in nums))
    return {
        "id": module_id,
        "label": label,
        "earned": int(round(earned)),
        "max": int(round(max_score)),
        "pending": pending,
        "present": present,
    }


def calculate_oge_grade(
    subject: Any,
    *,
    items: Optional[Iterable[Any]] = None,
    score: Any = None,
    teacher_score: Any = None,
    literacy_score: Any = None,
    review: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Вернуть карточку ОГЭ: первичный балл, оценка, флаги порогов, модули."""
    kind = normalize_subject(subject)
    cap = max_primary(kind)
    raw_items = [it for it in (items or []) if isinstance(it, dict)]
    items_by_num = {}
    for it in raw_items:
        n = _item_num(it)
        if n:
            items_by_num[n] = it

    if teacher_score is not None and teacher_score != "":
        primary = int(round(_as_float(teacher_score)))
    elif score is not None and score != "":
        primary = int(round(_as_float(score)))
    else:
        primary = int(round(sum(_item_earned(it) for it in raw_items)))
    primary = max(0, min(primary, cap))

    lit: Optional[float] = None
    if literacy_score is not None and literacy_score != "":
        lit = _as_float(literacy_score)
    else:
        lit = extract_literacy_score(review, raw_items)
    lit_unknown = lit is None
    lit_i = int(round(lit)) if lit is not None else None

    scale = mark_from_scale(primary, kind)
    grade = scale
    failed_geometry = False
    failed_literacy = False
    geo_pending = False
    geo_score = None
    geo_max = int(sum(GEO_DEFAULT_MAX.values()))

    modules: list[dict[str, Any]] = []
    geometry_tag = None
    literacy_tag = None

    if kind == "math":
        for mid, label, nums in MATH_MODULES:
            modules.append(
                _module_block(items_by_num, mid, label, nums, GEO_DEFAULT_MAX if mid == "geometry" else None)
            )
        geo = next((m for m in modules if m["id"] == "geometry"), None)
        if geo:
            geo_score = int(geo["earned"])
            geo_max = int(geo["max"] or geo_max)
            geo_pending = bool(geo["pending"])
        if primary >= 8 and geo and geo.get("present") and geo_score is not None:
            if geo_score < 2 and not geo_pending:
                failed_geometry = True
                grade = "2"
        if geo and geo.get("present"):
            if geo_pending:
                geometry_tag = f"⏳ Геометрия на проверке ({geo_score}/{geo_max})"
            elif geo_score is not None and geo_score >= 2:
                geometry_tag = f"✓ Геометрия сдана ({geo_score}/{geo_max})"
            elif geo_score is not None:
                geometry_tag = f"⚠️ Завал Геометрии ({geo_score}/{geo_max})"
    else:
        for mid, label, nums in RUS_CONTENT_MODULES:
            modules.append(_module_block(items_by_num, mid, label, nums))
        modules.append(
            {
                "id": "literacy",
                "label": "Грамотность",
                "earned": lit_i if lit_i is not None else 0,
                "max": LIT_MAX,
                "pending": lit_unknown,
            }
        )
        if not lit_unknown and scale in ("4", "5"):
            need = 6 if scale == "5" else 4
            if (lit_i or 0) < need:
                failed_literacy = True
                grade = "4" if scale == "5" else "3"
        if lit_unknown:
            literacy_tag = "Грамотность не выставлена"
        elif failed_literacy:
            literacy_tag = f"⚠️ Не хватило грамотности ({lit_i}/{LIT_MAX})"
        else:
            literacy_tag = f"✓ Грамотность ({lit_i}/{LIT_MAX})"

    return {
        "subject": kind,
        "score": primary,
        "max_score": cap,
        "grade": str(grade),
        "scale_grade": str(scale),
        "failed_geometry": failed_geometry,
        "failed_literacy": failed_literacy,
        "geometry_score": geo_score,
        "geometry_max": geo_max if kind == "math" else None,
        "geometry_pending": geo_pending,
        "literacy_score": lit_i,
        "literacy_max": LIT_MAX if kind == "russian" else None,
        "literacy_unknown": lit_unknown if kind == "russian" else False,
        "modules": modules,
        "geometry_tag": geometry_tag,
        "literacy_tag": literacy_tag,
    }


def result_from_review(
    subject: Any,
    review: Optional[dict[str, Any]] = None,
    *,
    score: Any = None,
    teacher_score: Any = None,
) -> dict[str, Any]:
    items = []
    if isinstance(review, dict) and isinstance(review.get("items"), list):
        items = [it for it in review["items"] if isinstance(it, dict)]
    return calculate_oge_grade(
        subject,
        items=items,
        score=score,
        teacher_score=teacher_score,
        review=review if isinstance(review, dict) else None,
    )


def attach_to_review(
    review: Optional[dict[str, Any]],
    subject: Any,
    *,
    score: Any = None,
    teacher_score: Any = None,
) -> dict[str, Any]:
    out = dict(review) if isinstance(review, dict) else {}
    out["oge"] = result_from_review(subject, out, score=score, teacher_score=teacher_score)
    return out


def part_of_item(item: dict[str, Any], subject: Any) -> int:
    try:
        raw = item.get("part")
        part = int(raw) if raw is not None and raw != "" else 0
    except (TypeError, ValueError):
        part = 0
    if part in (1, 2):
        return part
    n = _item_num(item)
    if normalize_subject(subject) == "russian":
        return 1 if 2 <= n <= 12 else 2
    return 1 if 1 <= n <= 19 else 2


def part_scores_from_items(subject: Any, items: Optional[Iterable[Any]] = None) -> tuple[int, int]:
    """Сумма баллов части 1 и части 2 (математика 1–19 / 20–25; русский тест / изложение+сочинение)."""
    p1 = 0.0
    p2 = 0.0
    for it in items or []:
        if not isinstance(it, dict):
            continue
        earned = _item_earned(it)
        if part_of_item(it, subject) == 1:
            p1 += earned
        else:
            p2 += earned
    return int(round(p1)), int(round(p2))


def threshold_status_label(
    *,
    submitted: bool,
    failed_geometry: bool = False,
    failed_literacy: bool = False,
    geometry_tag: Optional[str] = None,
    literacy_tag: Optional[str] = None,
    subject: Any = None,
) -> str:
    if not submitted:
        return "не сдал"
    kind = normalize_subject(subject)
    if kind == "math":
        if failed_geometry:
            return "⚠️ Геометрия"
        tag = str(geometry_tag or "")
        if "проверке" in tag:
            return "⏳ Геометрия"
        if tag:
            return "✓ Геометрия"
        return "норма"
    if kind == "russian":
        if failed_literacy:
            return "⚠️ Грамотность"
        tag = str(literacy_tag or "")
        if "не выставлена" in tag.lower():
            return "⏳ Грамотность"
        if tag:
            return "✓ Грамотность"
        return "норма"
    return "норма"
