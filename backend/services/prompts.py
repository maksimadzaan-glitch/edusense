"""Общие промпты и разбор JSON-задач от LLM."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from backend.services.figures import attach_figure
from backend.services.subject_blueprints import blueprint_for

SYSTEM_PROMPT = """Ты — старший методист ФИПИ. Пишешь задания КАК В РЕАЛЬНОМ КИМ ЕГЭ/ОГЭ/ВПР.

Верни СТРОГО один JSON-массив [...] без markdown и текста вокруг.
Элемент:
{
  "num": 1,
  "part": 1,
  "type": "Краткий ответ",
  "topic": "тема кодификатора",
  "section": "algebra|planimetry|stereometry|probability|functions|analysis",
  "text": "одно условие, школьный язык",
  "answer": "ключ бланка №1",
  "max_score": 1,
  "needs_figure": false,
  "figure_kind": null
}

figure_kind только: rect|triangle|box3d|circle|numberline|graph_linear|graph_parabola|graph_hyperbola|graph_cubic

════════════════════════════════════
ФОРМУЛЫ — ТОЛЬКО «бумажный» вид (без тяжёлого LaTeX):
✅ Пиши: 3x² − 4x + 5, √(x+1), [[3|4]], 2·π, [2; 5), (−∞; 0] ∪ [3; +∞)
✅ Степени надстрочными: ² ³ ⁴. Корни знаком √. Дроби маркером [[числ|знам]].
✅ Система уравнений ПРОСТЫМ текстом в одну/две строки:
   «Решите систему: 2x + y = 7 и x − y = 2»
   или «Решите систему уравнений: 2x+y=7; x−y=2»
❌ ЗАПРЕЩЕНО: \\begin, \\end, \\frac, \\sqrt, \\cases, $, $$, любой LaTeX с обратным слэшем.
❌ ЗАПРЕЩЕНО разбивать выражение по символам/строкам (нельзя «3 / x / 2 / − / 4»).
════════════════════════════════════

СЛОЖНОСТЬ:
• easy — база 1-й части ФИПИ
• medium — реальный КИМ
• hard — повышенный/высокий уровень, больше part=2

ПОРЯДОК: сначала part=1 (num 1..), затем part=2. nums без дыр.
answer part=1: одна строка (12, -4.5, 0.25, [2;5)). Без «ответ:» и без решения.
Язык: русский. Одно условие = один объект JSON.
"""


DIFFICULTY_HINTS = {
    "easy": (
        "Уровень easy (база ФИПИ): только посильные задачи 1-й части без параметров и без олимпиадных трюков. "
        "Простые числа, короткие условия."
    ),
    "medium": (
        "Уровень medium (реальный КИМ): формулировки как на экзамене, ловушки со знаками/областью определения, "
        "комбинированные условия. Часть 2 — типичные задачи среднего веса."
    ),
    "hard": (
        "Уровень hard (хардкор): параметры, сложная стереометрия, комбинаторика, длинные многошаговые задачи. "
        "Больше веса на part=2; part=1 тоже не тривиальная."
    ),
}


class LLMParseError(RuntimeError):
    pass


_SUP_MAP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

_SECTION_ALIASES = {
    "алгебра": "algebra",
    "algebra": "algebra",
    "планиметр": "planimetry",
    "planimetry": "planimetry",
    "стереометр": "stereometry",
    "stereometry": "stereometry",
    "вероятн": "probability",
    "probability": "probability",
    "функц": "functions",
    "график": "functions",
    "functions": "functions",
    "анализ": "analysis",
    "производн": "analysis",
    "интеграл": "analysis",
    "analysis": "analysis",
}


def _infer_section(topic: str, text: str) -> str:
    blob = f"{topic} {text}".lower()
    for key, code in _SECTION_ALIASES.items():
        if key in blob:
            return code
    return "algebra"


_INTERVAL_RE = re.compile(
    r"^[\[(].*[;,:].*[\])](?:\s*[∪∩\\Uu]\s*[\[(].*[;,:].*[\])])*$"
)


def polish_answer_key(value: str, *, part: int = 1) -> str:
    """Ключ бланка №1: только финальное значение; интервалы не ломаем."""
    text = str(value or "").strip()
    if not text:
        return text

    text = text.replace("$$", "$")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # предпочитаем строку с «Ответ:»
    preferred = None
    for ln in lines:
        m = re.match(r"^(ответ|ключ|ans|answer)\s*[:：\-]?\s*(.+)$", ln, flags=re.I)
        if m:
            preferred = m.group(2).strip()
    if preferred:
        text = preferred.splitlines()[0].strip()
    elif lines:
        # иначе первая короткая строка-ключ (не последняя с решением)
        short = [ln for ln in lines if len(ln) <= 80]
        text = (short[0] if short else lines[0]).splitlines()[0].strip()
    else:
        text = re.sub(r"^(ответ|ключ|ans|answer)\s*[:：\-]?\s*", "", text, flags=re.I)

    text = re.sub(r"^(ответ|ключ|ans|answer)\s*[:：\-]?\s*", "", text, flags=re.I).strip()

    # не режем по «;» внутри интервалов [a;b)
    if _INTERVAL_RE.match(text.replace(" ", "")) or re.search(r"[\[(].*[;].*[\])]", text):
        text = re.sub(r"\s+где\s+.*$", "", text, flags=re.I).strip()
        return text.replace("−", "-")

    # пояснения «где …» — только вне интервалов
    text = re.sub(r"\s+где\s+.*$", "", text, flags=re.I).strip()

    if part == 1:
        compact = text.replace(" ", "")
        m = re.fullmatch(r"\[\[?\s*([-+]?\d+(?:[.,]\d+)?)\s*\|\s*1\s*\]\]?", compact)
        if m:
            return m.group(1).replace(",", ".")
        m = re.fullmatch(r"([-+]?\d+(?:[.,]\d+)?)/1", compact)
        if m:
            return m.group(1).replace(",", ".")
        m = re.fullmatch(r"\$?\\frac\{([-+]?\d+(?:[.,]\d+)?)\}\{1\}\$?", compact)
        if m:
            return m.group(1).replace(",", ".")
        m = re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?", compact)
        if m:
            return compact.replace(",", ".")
        # оставить формулу в $...$ если есть
        if "$" in text:
            return text.strip()
        return text.strip()

    if text.count("$") >= 2:
        return text.strip()
    return text.replace("$", "").strip()


def canonicalize_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Порядок: по умолчанию part1 → part2; при kim_order — по num КИМ (1..N)."""
    if not questions:
        return questions

    kim = any(bool(q.get("kim_order") or q.get("_kim_order")) for q in questions)

    def sort_key(q: dict[str, Any]) -> tuple[int, int]:
        try:
            n = int(q.get("num") or q.get("task_number") or 10**9)
        except (TypeError, ValueError):
            n = 10**9
        return (n, 0)

    if kim:
        ordered = sorted(questions, key=sort_key)
        for q in ordered:
            try:
                q["num"] = int(q.get("num") or q.get("task_number") or q["num"])
            except (TypeError, ValueError, KeyError):
                pass
            q["kim_order"] = True
            q.pop("_kim_order", None)
            # max_score не затирать
            if q.get("max_score") is None:
                part = int(q.get("part") or 1)
                q["max_score"] = 1 if part == 1 else 2
        return ordered

    part1 = [q for q in questions if int(q.get("part") or 1) == 1]
    part2 = [q for q in questions if int(q.get("part") or 1) != 1]
    part1.sort(key=sort_key)
    part2.sort(key=sort_key)
    ordered = part1 + part2
    n1 = len(part1)
    for i, q in enumerate(ordered, start=1):
        q["num"] = i
        q["part"] = 1 if i <= n1 else 2
        if q["part"] == 1:
            typ = str(q.get("type") or "Краткий ответ")
            q["type"] = "Краткий ответ" if "развёрнут" in typ.lower() else typ
        else:
            q["type"] = str(q.get("type") or "Развёрнутый ответ")
        q["max_score"] = int(q.get("max_score") or (1 if q["part"] == 1 else 2))
    return ordered


def _repair_broken_latex(text: str) -> str:
    """Чинит порчу от JSON-escape: \\begin → begin, form-feed+rac → frac и т.п."""
    # управляющие символы после «съеденного» backslash
    text = text.replace("\x08egin", "\\begin").replace("\x08", "")
    text = text.replace("\x0crac", "\\frac").replace("\x0c", "")
    text = text.replace("\x0a", "\n")  # иногда \n внутри строки уже настоящий перевод
    # уже видимый мусор
    text = re.sub(r"\\?egin\{cases\}", r"\\begin{cases}", text, flags=re.I)
    text = re.sub(r"(?<![\\a-zA-Z])egin\{cases\}", r"\\begin{cases}", text, flags=re.I)
    text = re.sub(r"(?<![\\a-zA-Z])rac\{", r"\\frac{", text)
    return text


def _cases_to_plain(text: str) -> str:
    """\\begin{cases}...\\end{cases} → читаемый русский текст."""

    def repl(m: re.Match[str]) -> str:
        body = m.group(1)
        rows = [
            re.sub(r"\s+", " ", r.replace("\\", "")).strip()
            for r in re.split(r"\\\\|\n", body)
        ]
        rows = [r for r in rows if r]
        if len(rows) >= 2:
            return "{ " + " ; ".join(rows) + " }"
        return " ".join(rows)

    text = re.sub(
        r"\\begin\{cases\}([\s\S]*?)\\end\{cases\}",
        repl,
        text,
        flags=re.I,
    )
    text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", "", text)
    return text


_ATOM = (
    r"(?:[0-9]+(?:[.,][0-9]+)?|[a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*|"
    r"[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)"
)


def _slash_to_frac_markers(text: str) -> str:
    """a/b, (expr)/(expr), x/3 → [[числ|знам]]. Не трогает шины 175/70 R13 и уже [[ ]]."""
    saved: list[str] = []

    def _stash(m: re.Match[str]) -> str:
        i = len(saved)
        saved.append(m.group(0))
        return f"\ue000{i}\ue001"

    text = re.sub(r"\[\[[\s\S]*?\]\]", _stash, text)

    for _ in range(3):
        text = re.sub(r"\(([^()]{1,80})\)\s*/\s*\(([^()]{1,80})\)", r"[[\1|\2]]", text)
        text = re.sub(
            rf"\(([^()]{{1,80}})\)\s*/\s*({_ATOM})(?![\w.])",
            r"[[\1|\2]]",
            text,
        )
        text = re.sub(
            rf"({_ATOM})\s*/\s*\(([^()]{{1,80}})\)",
            r"[[\1|\2]]",
            text,
        )

    text = re.sub(
        r"(?<!\[)(?<!\|)([-+−]?)([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)"
        r"\s*/\s*([0-9]+(?:[.,][0-9]+)?|[a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)"
        r"(?!\s*R)(?!\])",
        r"[[\1\2|\3]]",
        text,
    )
    text = re.sub(
        r"(?<!\[)(?<!\|)([-+−]?)([0-9]+(?:[.,][0-9]+)?)"
        r"\s*/\s*([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)(?!\])",
        r"[[\1\2|\3]]",
        text,
    )
    # 15/4 — но не 175/70 R13
    text = re.sub(
        r"(?<!\[)(?<!\|)\b([-+−]?\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\b(?!\s*R)(?!\])",
        r"[[\1|\2]]",
        text,
    )

    def _restore(m: re.Match[str]) -> str:
        try:
            return saved[int(m.group(1))]
        except (IndexError, ValueError):
            return ""

    return re.sub(r"\ue000(\d+)\ue001", _restore, text)


_CARET_SUP = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")


def caret_to_superscripts(value: str) -> str:
    """2^5, 2^{5} → 2⁵. Не оставлять смесь 2^5 : 2²."""

    def _sup(digits: str) -> str:
        return digits.translate(_CARET_SUP)

    text = str(value or "")
    text = re.sub(r"\^\{(-?\d+)\}", lambda m: _sup(m.group(1)), text)
    text = re.sub(r"\^(-?\d+)", lambda m: _sup(m.group(1)), text)
    return text


def polish_fipi_text(value: str) -> str:
    """К школьному виду ФИПИ: unicode + [[дроби]], без битого LaTeX."""
    text = str(value or "").strip()
    if not text:
        return text

    text = _repair_broken_latex(text)
    text = _cases_to_plain(text)

    # схлопнуть «вертикальный» мусор: одиночные символы на строках → одна строка;
    # иначе сохраняем переносы (ОГЭ русский: инструкции + 1) 2) 3) …)
    lines = [ln.strip() for ln in text.splitlines()]
    nonempty = [ln for ln in lines if ln]
    if nonempty and sum(1 for ln in nonempty if len(ln) <= 2) >= max(3, len(nonempty) // 2):
        text = " ".join(nonempty)
    else:
        text = "\n".join(nonempty)

    # убрать $ обёртки — дальше рендерим unicode/маркеры
    text = text.replace("$$", " ").replace("$", " ")

    # LaTeX → школьный вид
    text = re.sub(r"\\dfrac\{([^{}]+)\}\{([^{}]+)\}", r"[[\1|\2]]", text)
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"[[\1|\2]]", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", text)
    text = re.sub(r"\\sqrt\s*([0-9a-zA-Z]+)", r"√\1", text)
    text = re.sub(r"\\cdot|\\times", "·", text)
    text = re.sub(r"\\pm", "±", text)
    text = re.sub(r"\\leq|\\leqslant", "≤", text)
    text = re.sub(r"\\geq|\\geqslant", "≥", text)
    text = re.sub(r"\\neq", "≠", text)
    text = re.sub(r"\\infty", "∞", text)
    text = re.sub(r"\\cup", "∪", text)
    text = re.sub(r"\\left|\\right|\\,", "", text)
    text = caret_to_superscripts(text)
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = text.replace("\\", "")

    text = text.replace("<=", "≤").replace(">=", "≥").replace("!=", "≠")
    text = re.sub(r"(?<![*\w])\*(?![*\w])", "·", text)
    # «3 x 2 − 4 x + 5» (развал степени) → 3x² − 4x + 5
    text = re.sub(r"\b(\d+)\s*[xх]\s*2\b", r"\1x²", text)
    text = re.sub(r"\b(\d+)\s*[xх]\s*3\b", r"\1x³", text)
    text = re.sub(r"\b[xх]\s*2\b", "x²", text)
    text = re.sub(r"\b[xх]\s*3\b", "x³", text)
    text = re.sub(r"\b(\d+)\s+[xх]\b", r"\1x", text)
    text = _slash_to_frac_markers(text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    return text


def _sanitize_json_escapes(text: str) -> str:
    """Экранирует LaTeX/мусорные escape, чтобы JSON не ломался (\frac и т.п.)."""
    # Критично: \f \b \n \r \t внутри буквы — валидные JSON-escape и ломают LaTeX
    for cmd in (
        "begin", "end", "frac", "dfrac", "sqrt", "cdot", "times",
        "left", "right", "infty", "cup", "leq", "geq", "neq", "pm",
    ):
        text = re.sub(r"(?<!\\)\\" + cmd + r"\b", "\\\\" + cmd, text)
    text = re.sub(r"\\([bfnrt])(?=[a-zA-Z])", r"\\\\\1", text)
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch != "\\" or i + 1 >= n:
            out.append(ch)
            i += 1
            continue
        nxt = text[i + 1]
        if nxt in '"\\/bfnrt':
            out.append(text[i : i + 2])
            i += 2
            continue
        if nxt == "u" and i + 5 < n and all(c in "0123456789abcdefABCDEF" for c in text[i + 2 : i + 6]):
            out.append(text[i : i + 6])
            i += 6
            continue
        out.append("\\\\")
        out.append(nxt)
        i += 2
    return "".join(out)


def _strip_fences(text: str) -> str:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json|JSON)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # иногда модель оборачивает несколько блоков
    if "```" in raw:
        parts = re.findall(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw)
        if parts:
            raw = max(parts, key=len).strip()
    return raw.strip()


def _loads_jsonish(text: str) -> Any:
    """Парсит JSON-массив/объект; несколько стратегий починки."""
    raw = _strip_fences(text)
    if not raw:
        raise LLMParseError("Модель вернула пустой ответ")

    starts = [i for i, ch in enumerate(raw) if ch in "[{"]
    if not starts:
        raise LLMParseError("Модель вернула ответ без JSON")

    decoder = json.JSONDecoder()
    last_err: Optional[Exception] = None

    for start in starts[:6]:
        chunk = raw[start:]
        # Сначала sanitize: иначе \frac парсится как JSON \f (form-feed) и портит текст
        candidates = [
            _sanitize_json_escapes(chunk),
            _sanitize_json_escapes(chunk.replace("\r\n", "\n").replace("\r", "\n")),
            _sanitize_json_escapes(
                chunk.replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"')
            ),
            chunk,
        ]
        for candidate in candidates:
            try:
                data, _end = decoder.raw_decode(candidate)
                return data
            except json.JSONDecodeError as exc:
                last_err = exc

    # Последняя попытка: вырезать самый длинный балансный массив [...]
    best = _extract_balanced_array(raw)
    if best:
        for candidate in (_sanitize_json_escapes(best), best):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                last_err = exc

    preview = re.sub(r"\s+", " ", raw)[:180]
    raise LLMParseError(f"Не удалось разобрать JSON задач: {last_err}. Фрагмент: {preview}") from last_err


def _extract_balanced_array(text: str) -> Optional[str]:
    start = text.find("[")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _looks_like_question(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    for key in ("text", "question", "условие", "condition", "problem", "task", "body"):
        if str(item.get(key) or "").strip():
            return True
    return False


def _coerce_questions_list(data: Any) -> list[Any]:
    """Достаёт список задач из массива, объекта-обёртки или одного объекта."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # один объект-задача
        if _looks_like_question(data):
            return [data]
        for key in (
            "tasks",
            "questions",
            "items",
            "data",
            "variant",
            "problems",
            "задания",
            "задачи",
            "result",
        ):
            val = data.get(key)
            if isinstance(val, list) and val:
                return val
            if isinstance(val, dict) and _looks_like_question(val):
                return [val]
        # любая первая непустая list[dict]
        for val in data.values():
            if isinstance(val, list) and val and all(isinstance(x, dict) for x in val[:3]):
                return val
    return []


def _item_text(item: dict[str, Any]) -> str:
    for key in ("text", "question", "условие", "condition", "problem", "task", "body"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val)
    return ""


def _item_answer(item: dict[str, Any]) -> str:
    for key in ("answer", "ключ", "key", "ans", "solution_key"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val)
    return ""


def extract_questions(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    text = _strip_fences(content)
    data = _loads_jsonish(text)
    items = _coerce_questions_list(data)

    if not items:
        preview = re.sub(r"\s+", " ", text)[:180]
        raise LLMParseError(
            "Ожидался непустой JSON-массив задач. "
            f"Модель вернула другой формат. Фрагмент: {preview}"
        )

    normalized: list[dict[str, Any]] = []
    for i, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        part = int(item.get("part") or 1)
        topic = polish_fipi_text(str(item.get("topic") or item.get("тема") or "Общее"))
        qtext = polish_fipi_text(_item_text(item))
        if not qtext:
            continue
        section = str(item.get("section") or "").strip().lower()
        if section not in {
            "algebra",
            "planimetry",
            "stereometry",
            "probability",
            "functions",
            "analysis",
        }:
            section = _infer_section(topic, qtext)
        row = {
            "num": int(item.get("num") or i),
            "part": part,
            "type": str(item.get("type") or ("Развёрнутый ответ" if part == 2 else "Краткий ответ")),
            "topic": topic,
            "section": section,
            "text": qtext,
            "answer": polish_answer_key(_item_answer(item), part=part),
            "max_score": int(item.get("max_score") or item.get("maxScore") or (2 if part == 2 else 1)),
            "needs_figure": bool(item.get("needs_figure")),
            "figure_kind": item.get("figure_kind"),
        }
        normalized.append(attach_figure(row))

    if not normalized:
        raise LLMParseError(
            "Модель вернула JSON, но без текстовмого поля условия (text/question). Попробуйте ещё раз."
        )
    return canonicalize_questions(normalized)


def recommended_count(exam: str, subject: str) -> int:
    """Полная длина КИМ для exam+subject."""
    from backend.services.subject_blueprints import kim_length

    return kim_length(exam=exam, subject=subject)


def build_user_prompt(*, exam: str, subject: str, difficulty: str, count: int) -> str:
    from backend.services.subject_blueprints import part1_last

    diff = (difficulty or "medium").strip().lower()
    if diff not in DIFFICULTY_HINTS:
        diff = "medium"
    hint = DIFFICULTY_HINTS[diff]

    p1_border = part1_last(exam=exam, subject=subject)
    part1 = min(count, p1_border)
    part2 = max(0, count - part1)
    slots = blueprint_for(exam=exam, subject=subject, count=count, part1=part1, part2=part2)

    return (
        f"Сгенерируй вариант как в реальном КИМ ФИПИ (полная структура слотов).\n"
        f"Экзамен: {exam}\n"
        f"Предмет: {subject}\n"
        f"Сложность: {diff}\n"
        f"{hint}\n"
        f"Ровно {count} заданий: num = номер слота КИМ 1…{count}; "
        f"part=1 при num≤{part1}, иначе part=2 ({part2} развёрнутых).\n\n"
        f"{slots}\n\n"
        f"ФОРМУЛЫ только школьные: 3x²−4x+5, √(x+1), [[2|3]], без \\begin и без $. "
        f"Системы текстом: «2x+y=7 и x−y=2».\n"
        f"answer part=1 — одна строка-ключ. Верни только JSON-массив."
    )


def build_missing_slots_prompt(
    *,
    exam: str,
    subject: str,
    difficulty: str,
    slots: list[int],
) -> str:
    """Промпт для догенерации только пустых слотов КИМ."""
    from backend.services.subject_blueprints import missing_slots_blueprint

    diff = (difficulty or "medium").strip().lower()
    if diff not in DIFFICULTY_HINTS:
        diff = "medium"
    hint = DIFFICULTY_HINTS[diff]
    body = missing_slots_blueprint(exam=exam, subject=subject, slots=slots)
    return (
        f"{body}\n"
        f"Сложность: {diff}. {hint}\n"
        f"Поле num каждого задания ОБЯЗАНО быть одним из: {', '.join(str(s) for s in slots)}.\n"
        f"ФОРМУЛЫ только школьные: 3x²−4x+5, √(x+1), [[2|3]], без \\begin и без $.\n"
        f"answer part=1 — одна строка-ключ. Верни только JSON-массив из {len(slots)} объектов."
    )
