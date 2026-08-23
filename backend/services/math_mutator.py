"""Детерминированный мутатор ОГЭ математики — без LLM.

«Каждому свой»: от seed (работа + ФИО) слегка меняются числа / порядок
вариантов ответа. Тип и сложность те же, ключ пересчитывается.

Не трогаем: часть 2 (20–25). Сюжет 1–5 тот же, числа пересчитываются.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import operator
import random
import re
from pathlib import Path
from typing import Any, Optional

_PYTHAGOREAN = (
    (6, 8, 10),
    (5, 12, 13),
    (9, 12, 15),
    (8, 15, 17),
    (7, 24, 25),
    (20, 21, 29),
    (12, 16, 20),
    (9, 40, 41),
    (11, 60, 61),
    (12, 35, 37),
    (16, 30, 34),
    (18, 24, 30),
    (15, 20, 25),
    (10, 24, 26),
)


def _seed_int(assignment_id: int, student_name: str) -> int:
    raw = f"{int(assignment_id)}|{str(student_name or '').strip().casefold()}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:16], 16)


def seed_int(assignment_id: int, student_name: str) -> int:
    return _seed_int(assignment_id, student_name)


def _rng(assignment_id: int, student_name: str) -> random.Random:
    return random.Random(_seed_int(assignment_id, student_name))


def _subject_is_math(subject: Optional[str]) -> bool:
    s = (subject or "").strip().lower().replace("ё", "е")
    return "матем" in s or s in {"math", "mathematics", "math_base", "oge_math"}


def _num_of(q: dict[str, Any]) -> int:
    try:
        return int(q.get("num") or q.get("task_number") or 0)
    except (TypeError, ValueError):
        return 0


def _part_of(q: dict[str, Any]) -> int:
    try:
        return int(q.get("part") or 1)
    except (TypeError, ValueError):
        return 1


def _text_of(q: dict[str, Any]) -> str:
    return str(q.get("text") or "")


def _mark(q: dict[str, Any], kind: str) -> None:
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    pl = dict(pl)
    pl["unique"] = True
    pl["unique_kind"] = kind
    q["payload"] = pl


def _set_answer(q: dict[str, Any], primary: str, extras: Optional[list[str]] = None) -> None:
    q["answer"] = primary
    acc = [primary]
    for x in extras or []:
        if x and x not in acc:
            acc.append(x)
    if "," not in primary and "." in primary:
        acc.append(primary.replace(".", ","))
    if "." not in primary and "," in primary:
        acc.append(primary.replace(",", "."))
    q["acceptable_answers"] = acc


def _set_numeric(q: dict[str, Any], value: float | int, *, ndigits: int = 4) -> None:
    if isinstance(value, int) or abs(float(value) - round(float(value))) < 1e-9:
        s = str(int(round(float(value))))
        _set_answer(q, s)
        return
    v = round(float(value), ndigits)
    s = f"{v:.{ndigits}f}".rstrip("0").rstrip(".")
    if s.startswith("."):
        s = "0" + s
    if s.startswith("-."):
        s = "-0" + s[1:]
    _set_answer(q, s)


def _replace_once(text: str, old: str, new: str) -> Optional[str]:
    if old not in text:
        return None
    return text.replace(old, new, 1)


def _pick_other(rng: random.Random, options: list[Any], current: Any) -> Any:
    pool = [x for x in options if x != current]
    if not pool:
        return current
    return rng.choice(pool)


# ----- JSON-шаблоны (generate_math_task) -----

_AST_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_AST_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
def _pick(seq: Any, idx: Any) -> Any:
    items = list(seq)
    i = int(idx)
    if i < 0 or i >= len(items):
        raise ValueError("pick: индекс вне диапазона")
    return items[i]


_SAFE_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "int": int,
    "round": round,
    "pow": pow,
    "gcd": math.gcd,
    "sqrt": math.sqrt,
    "pick": _pick,
}

_RE_RAND_INT = re.compile(
    r"^random_int\(\s*(-?\d+)\s*,\s*(-?\d+)\s*(?:,\s*exclude\s*=\s*(\[[^\]]*\]))?\s*\)$"
)
_RE_RAND_CHOICE = re.compile(
    r"^random_choice\(\s*(\[[^\]]+\])\s*(?:,\s*exclude\s*=\s*(\[[^\]]*\]))?\s*\)$"
)


class _TemplateFmt(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _fmt_num(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        s = f"{value:.6f}".rstrip("0").rstrip(".")
        if s.startswith("."):
            s = "0" + s
        if s.startswith("-."):
            s = "-0" + s[1:]
        return s
    return str(value)


def _parse_exclude_list(raw: str | None, env: dict[str, Any]) -> set[Any]:
    if not raw:
        return set()
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    out: set[Any] = set()
    for part in inner.split(","):
        token = part.strip()
        if not token:
            continue
        if token in env:
            out.add(env[token])
            continue
        try:
            out.add(ast.literal_eval(token))
        except (ValueError, SyntaxError):
            continue
    return out


def _eval_ast(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, env)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _SAFE_FUNCS:
            return _SAFE_FUNCS[node.id]
        raise ValueError(f"неизвестное имя {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _AST_BINOPS:
        return _AST_BINOPS[type(node.op)](_eval_ast(node.left, env), _eval_ast(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _AST_UNARY:
        return _AST_UNARY[type(node.op)](_eval_ast(node.operand, env))
    if isinstance(node, ast.Call):
        func = _eval_ast(node.func, env)
        if func not in _SAFE_FUNCS.values():
            raise ValueError("вызов функции запрещён")
        args = [_eval_ast(a, env) for a in node.args]
        return func(*args)
    if isinstance(node, ast.List):
        return [_eval_ast(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_ast(elt, env) for elt in node.elts)
    raise ValueError(f"небезопасное выражение: {type(node).__name__}")


def _eval_expr(expr: str, env: dict[str, Any]) -> Any:
    tree = ast.parse(str(expr).strip(), mode="eval")
    return _eval_ast(tree, env)


def _eval_variable(spec: str, env: dict[str, Any], rng: random.Random) -> Any:
    raw = str(spec).strip()
    m_int = _RE_RAND_INT.fullmatch(raw)
    if m_int:
        lo, hi = int(m_int.group(1)), int(m_int.group(2))
        if lo > hi:
            lo, hi = hi, lo
        banned = _parse_exclude_list(m_int.group(3), env)
        pool = [n for n in range(lo, hi + 1) if n not in banned]
        if not pool:
            raise ValueError(f"random_int({lo}, {hi}) пуст после exclude")
        return rng.choice(pool)
    m_ch = _RE_RAND_CHOICE.fullmatch(raw)
    if m_ch:
        options = _eval_expr(m_ch.group(1), env)
        if not isinstance(options, (list, tuple)) or not options:
            raise ValueError("random_choice: пустой список")
        banned = _parse_exclude_list(m_ch.group(2), env)
        pool = [x for x in options if x not in banned]
        if not pool:
            pool = list(options)
        return rng.choice(pool)
    return _eval_expr(raw, env)


def _inject_display(env: dict[str, Any]) -> None:
    for key, val in list(env.items()):
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            continue
        env[f"{key}_abs"] = abs(val)
        env[f"{key}_pm"] = "−" if val < 0 else "+"
        env[key] = int(val) if abs(float(val) - round(float(val))) < 1e-9 else val


def _fill_text(template: str, env: dict[str, Any]) -> str:
    mapping = _TemplateFmt({k: _fmt_num(v) for k, v in env.items()})
    text = str(template or "").format_map(mapping)
    text = re.sub(r"\+\s*-", "− ", text)
    text = re.sub(r"-\s*-", "+ ", text)
    text = re.sub(r"\+\s*−", "− ", text)
    text = re.sub(r"−\s*−", "+ ", text)
    text = re.sub(r"\+\s*0x\b", "", text)
    text = re.sub(r"\+\s*0(?!\d)", "", text)
    text = re.sub(r" {2,}", " ", text).strip()
    try:
        from backend.services.prompts import caret_to_superscripts

        text = caret_to_superscripts(text)
    except Exception:
        pass
    return text


_RE_PLACEHOLDER = re.compile(r"^\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def _fill_structure(obj: Any, env: dict[str, Any]) -> Any:
    """Подставить {key} в figure: числа оставляем числами (не «7,07» через текст)."""
    if isinstance(obj, str):
        m = _RE_PLACEHOLDER.fullmatch(obj.strip())
        if m and m.group(1) in env:
            return env[m.group(1)]
        filled = _fill_text(obj, env)
        try:
            if re.fullmatch(r"-?\d+", filled):
                return int(filled)
            if re.fullmatch(r"-?\d+\.\d+", filled):
                return float(filled)
        except ValueError:
            return filled
        return filled
    if isinstance(obj, list):
        return [_fill_structure(x, env) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _fill_structure(v, env) for k, v in obj.items()}
    return obj


def _answer_extras(primary: str, env: dict[str, Any]) -> list[str]:
    extras = [primary]
    if "," not in primary and "." in primary:
        extras.append(primary.replace(".", ","))
    if "." not in primary and "," in primary:
        extras.append(primary.replace(",", "."))
    num = env.get("num")
    den = env.get("den")
    if isinstance(num, int) and isinstance(den, int) and den:
        extras.extend([f"{num}/{den}", f"[[{num}|{den}]]"])
    extra_raw = env.get("acceptable")
    if isinstance(extra_raw, (list, tuple)):
        extras.extend(str(x) for x in extra_raw if x is not None)
    out: list[str] = []
    for x in extras:
        s = str(x).strip()
        if s and s not in out:
            out.append(s)
    return out


def generate_math_task(
    template: dict[str, Any] | str,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Подставить переменные шаблона и вернуть готовое задание + ключ.

    ``template`` — dict с полями ``template`` / ``mutator_logic`` /
    ``explanation_template`` (как в ТЗ) либо строка условия с ``{b}``.
    """
    spec = {"template": template} if isinstance(template, str) else dict(template or {})
    logic = spec.get("mutator_logic") if isinstance(spec.get("mutator_logic"), dict) else {}
    variables = logic.get("variables") if isinstance(logic.get("variables"), dict) else {}
    computed = logic.get("computed") if isinstance(logic.get("computed"), dict) else {}
    text_tpl = str(spec.get("template") or spec.get("template_text") or "")
    expl_tpl = str(spec.get("explanation_template") or spec.get("template_solution") or "")
    local_rng = rng or random.Random()
    env: dict[str, Any] = {}
    last_error: Exception | None = None
    for _ in range(12):
        env = {}
        try:
            for name, expr in variables.items():
                env[str(name)] = _eval_variable(str(expr), env, local_rng)
            for name, expr in computed.items():
                env[str(name)] = _eval_variable(str(expr), env, local_rng)
            if "answer" not in env:
                raise ValueError("mutator_logic.computed.answer обязателен")
            break
        except Exception as exc:
            last_error = exc
            env = {}
    if "answer" not in env:
        raise ValueError(f"не удалось сгенерировать задание: {last_error}")
    _inject_display(env)
    text = _fill_text(text_tpl, env)
    solution = _fill_text(expl_tpl, env) if expl_tpl else ""
    answer = _fmt_num(env["answer"])
    figure = None
    fig_spec = logic.get("figure")
    if isinstance(fig_spec, dict):
        figure = _fill_structure(fig_spec, env)
    return {
        "text": text,
        "answer": answer,
        "acceptable_answers": _answer_extras(answer, env),
        "solution": solution or None,
        "values": env,
        "figure_params": figure,
    }


def mutate_task(
    template: dict[str, Any] | str,
    rng: random.Random | None = None,
    *,
    enabled: bool = True,
) -> dict[str, Any] | None:
    """Публичное ядро: template_text + mutator_logic → текст и ключ.

    ``enabled=False`` — статический вариант класса, подстановки нет.
    """
    if not enabled:
        return None
    return generate_math_task(template, rng)


def _eval_group_vars(logic: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    env: dict[str, Any] = {}
    variables = logic.get("variables") if isinstance(logic.get("variables"), dict) else {}
    computed = logic.get("computed") if isinstance(logic.get("computed"), dict) else {}
    last_error: Exception | None = None
    for _ in range(12):
        env = {}
        try:
            for name, expr in variables.items():
                env[str(name)] = _eval_variable(str(expr), env, rng)
            for name, expr in computed.items():
                env[str(name)] = _eval_variable(str(expr), env, rng)
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            env = {}
    if last_error and not env:
        raise last_error
    _inject_display(env)
    return env


def mutate_task_group(
    questions: list[dict[str, Any]],
    rng: random.Random | None = None,
    *,
    enabled: bool = True,
) -> int:
    """Общие base_vars на группу 1–5, чтобы все подзадачи шли от одних цифр.

    Сюжет/чертёж те же, числа чуть другие. Шаблон с ``{placeholders}``
    сохраняется в payload, чтобы при выдаче ученику можно было пересчитать.
    """
    group = [q for q in questions or [] if isinstance(q, dict) and _num_of(q) in {1, 2, 3, 4, 5}]
    if len(group) < 2:
        return 0
    group.sort(key=_num_of)
    first = group[0]
    pl0 = first.get("payload") if isinstance(first.get("payload"), dict) else {}
    fp = first.get("figure_params") if isinstance(first.get("figure_params"), dict) else {}
    logic = pl0.get("group_mutator_logic") if isinstance(pl0.get("group_mutator_logic"), dict) else None
    if logic is None and isinstance(fp.get("group_mutator_logic"), dict):
        logic = fp.get("group_mutator_logic")
    if isinstance(logic, dict):
        for q in group:
            pq = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
            pq["group_mutator_logic"] = logic
            q["payload"] = pq
    base = dict(pl0.get("base_vars") or {})
    if not base and isinstance(fp.get("base_vars"), dict):
        base = dict(fp["base_vars"])
    local = rng or random.Random()
    changed = 0
    if enabled and isinstance(logic, dict) and (logic.get("variables") or logic.get("computed")):
        try:
            env = _eval_group_vars(logic, local)
            base.update({k: v for k, v in env.items() if not str(k).endswith(("_abs", "_pm"))})
            story_live = str(pl0.get("shared_story") or "")
            story_tpl = str(pl0.get("shared_story_template") or story_live)
            if "{" in story_live and not pl0.get("shared_story_template"):
                story_tpl = story_live
            if "{" in story_tpl:
                new_story = _fill_text(story_tpl, env)
                for q in group:
                    pq = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
                    pq["shared_story_template"] = story_tpl
                    pq["shared_story"] = new_story
                    q["payload"] = pq
            for q in group:
                pq = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
                live = str(q.get("text") or "")
                tpl = str(pq.get("mutator_template") or live)
                if "{" in live and not pq.get("mutator_template"):
                    tpl = live
                if "{" not in tpl:
                    q["payload"] = pq
                    continue
                pq["mutator_template"] = tpl
                q["text"] = _fill_text(tpl, env)
                ans_key = f"answer_{_num_of(q)}"
                if ans_key in env:
                    _set_answer(q, _fmt_num(env[ans_key]))
                elif "answer" in env and _num_of(q) == 1:
                    _set_answer(q, _fmt_num(env["answer"]))
                q["payload"] = pq
                changed += 1
        except Exception:
            pass
    if not base:
        return changed
    for q in group:
        pq = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
        pq["base_vars"] = dict(base)
        ctx = pq.get("math_context") if isinstance(pq.get("math_context"), dict) else None
        if ctx is not None:
            ctx = dict(ctx)
            ctx["base_vars"] = dict(base)
            pq["math_context"] = ctx
        q["payload"] = pq
        fpq = q.get("figure_params") if isinstance(q.get("figure_params"), dict) else {}
        if fpq is not None:
            fpq = dict(fpq)
            fpq["base_vars"] = dict(base)
            q["figure_params"] = fpq
    return changed


_MUTATOR_FILE_SPECS: dict[str, dict[str, Any]] | None = None


def _mutator_file_specs() -> dict[str, dict[str, Any]]:
    """Актуальные шаблоны 6–19 из math_oge_mutator.json — без пересейва PG."""
    global _MUTATOR_FILE_SPECS
    if _MUTATOR_FILE_SPECS is not None:
        return _MUTATOR_FILE_SPECS
    path = Path(__file__).resolve().parents[1] / "universal" / "specs" / "math_oge_mutator.json"
    out: dict[str, dict[str, Any]] = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _MUTATOR_FILE_SPECS = out
        return out
    for proto in data.get("prototypes") or []:
        if not isinstance(proto, dict):
            continue
        fp = proto.get("figure_params") if isinstance(proto.get("figure_params"), dict) else {}
        code = str(fp.get("subtype_code") or "").strip()
        logic = fp.get("mutator_logic") if isinstance(fp.get("mutator_logic"), dict) else None
        if not code or not logic:
            continue
        out[code] = {
            "template": str(proto.get("template_text") or fp.get("template") or ""),
            "mutator_logic": logic,
            "explanation_template": str(
                fp.get("explanation_template") or proto.get("template_solution") or ""
            ),
            "figure_kind": proto.get("figure_kind"),
        }
    _MUTATOR_FILE_SPECS = out
    return out


def _mutator_spec_from_question(q: dict[str, Any]) -> dict[str, Any] | None:
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    fp = q.get("figure_params") if isinstance(q.get("figure_params"), dict) else {}
    code = str(pl.get("subtype_code") or fp.get("subtype_code") or "").strip()
    if _num_of(q) == 11 and not code.startswith("math_oge_q11_"):
        code = "math_oge_q11_graph_match"
    file_spec = _mutator_file_specs().get(code) if code else None
    if file_spec and file_spec.get("template") and file_spec.get("mutator_logic"):
        return {
            "template": str(file_spec["template"]),
            "mutator_logic": file_spec["mutator_logic"],
            "explanation_template": str(file_spec.get("explanation_template") or ""),
        }
    logic = pl.get("mutator_logic") if isinstance(pl.get("mutator_logic"), dict) else None
    if logic is None and isinstance(fp.get("mutator_logic"), dict):
        logic = fp.get("mutator_logic")
    if not isinstance(logic, dict):
        return None
    template = (
        pl.get("mutator_template")
        or fp.get("template")
        or (q.get("text") if "{" in str(q.get("text") or "") else None)
    )
    if not template:
        return None
    expl = (
        pl.get("explanation_template")
        or fp.get("explanation_template")
        or q.get("solution")
        or ""
    )
    return {
        "template": str(template),
        "mutator_logic": logic,
        "explanation_template": str(expl or ""),
    }


def apply_mutator_logic_to_question(q: dict[str, Any], rng: random.Random) -> bool:
    """Заполнить JSON-шаблон на карточке. False — шаблона нет."""
    spec = _mutator_spec_from_question(q)
    if not spec:
        return False
    try:
        result = generate_math_task(spec, rng)
    except Exception:
        return False
    q["text"] = result["text"]
    _set_answer(q, result["answer"], result.get("acceptable_answers"))
    if result.get("solution"):
        q["solution"] = result["solution"]
    fig = result.get("figure_params")
    if isinstance(fig, dict):
        q["figure_params"] = fig
        kind = fig.get("kind") or fig.get("figure_kind")
        if kind:
            q["figure_kind"] = kind
    else:
        fp = q.get("figure_params")
        if isinstance(fp, dict) and fp.get("mutator_logic"):
            clean = {
                k: v
                for k, v in fp.items()
                if k not in {"mutator_logic", "template", "explanation_template"}
            }
            q["figure_params"] = clean or None
    pl = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
    pl["mutator_logic"] = spec["mutator_logic"]
    pl["mutator_template"] = spec["template"]
    if spec.get("explanation_template"):
        pl["explanation_template"] = spec["explanation_template"]
    pl["mutator_values"] = {
        k: v for k, v in (result.get("values") or {}).items() if isinstance(k, str) and not k.endswith(("_abs", "_pm"))
    }
    pl["unique"] = True
    pl["unique_kind"] = "template"
    q["payload"] = pl
    return True


_MATH_KITS_CACHE: dict[str, dict[str, str]] | None = None


def _load_math_kits() -> dict[str, dict[str, str]]:
    global _MATH_KITS_CACHE
    if _MATH_KITS_CACHE is not None:
        return _MATH_KITS_CACHE
    path = (
        Path(__file__).resolve().parents[1]
        / "universal"
        / "packs"
        / "oge_math"
        / "oge_math_kits.json"
    )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _MATH_KITS_CACHE = {}
        return _MATH_KITS_CACHE
    kits = data.get("kits") if isinstance(data, dict) else None
    out: dict[str, dict[str, str]] = {}
    if isinstance(kits, dict):
        for cid, row in kits.items():
            if isinstance(row, dict):
                out[str(cid)] = {str(k): str(v) for k, v in row.items() if v}
    _MATH_KITS_CACHE = out
    return out


def _plot_context_id(questions: list[dict[str, Any]]) -> str:
    for q in questions or []:
        if not isinstance(q, dict) or _num_of(q) not in {1, 2, 3, 4, 5}:
            continue
        pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        cid = str(pl.get("context_id") or q.get("context_id") or "").strip()
        if cid:
            return cid
    return ""


def _stamp_kit_subtypes(questions: list[dict[str, Any]]) -> None:
    """Подтип 6–19 берём из комплекта сюжета 1–5, даже если в PG старый шаблон."""
    kit = _load_math_kits().get(_plot_context_id(questions)) or {}
    if not kit:
        return
    for q in questions or []:
        if not isinstance(q, dict) or _part_of(q) != 1:
            continue
        n = _num_of(q)
        if n < 6 or n > 19:
            continue
        want = str(kit.get(str(n)) or "").strip()
        if not want:
            continue
        pl = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
        pl["subtype_code"] = want
        q["payload"] = pl
        fp = q.get("figure_params") if isinstance(q.get("figure_params"), dict) else {}
        if fp:
            fp = dict(fp)
            fp["subtype_code"] = want
            q["figure_params"] = fp


def fill_math_templates(
    questions: list[dict[str, Any]],
    rng: random.Random | None = None,
    *,
    enabled: bool = True,
) -> int:
    """Заполнить шаблоны мутатора у списка заданий (generate / preview).

    ``enabled=False`` — не рандомить 6–19; группа 1–5 всё равно получает base_vars.
    """
    local = rng or random.Random()
    changed = mutate_task_group(questions, local, enabled=enabled)
    if not enabled:
        return changed
    _stamp_kit_subtypes(questions)
    for q in questions or []:
        if not isinstance(q, dict):
            continue
        if _part_of(q) != 1:
            continue
        slot_rng = random.Random(local.randint(1, 2**31 - 1) ^ (_num_of(q) * 10007))
        if apply_mutator_logic_to_question(q, slot_rng):
            changed += 1
    return changed


# ----- handlers (return True if mutated) -----


def _mcq_shuffle(q: dict[str, Any], rng: random.Random) -> bool:
    """Переставить пункты 1) 2) 3)… и пересчитать номер верного."""
    text = _text_of(q)
    ans = str(q.get("answer") or "").strip()
    if not re.fullmatch(r"[1-9]", ans):
        return False
    matches = list(re.finditer(r"(?m)^(\d+)\)\s+(.+?)(?=\n\d+\)|\Z)", text, re.S))
    if len(matches) < 3:
        return False
    try:
        correct_old = int(ans)
    except ValueError:
        return False
    bodies = [m.group(2).rstrip() for m in matches]
    nums = [int(m.group(1)) for m in matches]
    if sorted(nums) != list(range(1, len(nums) + 1)):
        return False
    if correct_old not in nums:
        return False
    paired = list(zip(nums, bodies))
    rng.shuffle(paired)
    if [n for n, _ in paired] == nums:
        paired = paired[1:] + paired[:1]
    new_correct = next(i + 1 for i, (old_n, _) in enumerate(paired) if old_n == correct_old)
    new_bodies = [b for _, b in paired]
    head = text[: matches[0].start()]
    block = "\n".join(f"{i}) {body}" for i, body in enumerate(new_bodies, start=1))
    new_text = head + block
    if new_text == text:
        return False
    q["text"] = new_text
    _set_answer(q, str(new_correct))
    _mark(q, "mcq")
    return True


def _option_set_shuffle(q: dict[str, Any], rng: random.Random) -> bool:
    """Русский / мат: ответ «345» — переставить пункты 1)… и пересчитать цифры."""
    text = _text_of(q)
    ans = str(q.get("answer") or "").strip().replace(" ", "")
    if not re.fullmatch(r"[1-9]{2,6}", ans):
        return False
    matches = list(re.finditer(r"(?m)^(\d+)\)\s+(.+?)(?=\n\d+\)|\Z)", text, re.S))
    if len(matches) < 3:
        return False
    nums = [int(m.group(1)) for m in matches]
    if sorted(nums) != list(range(1, len(nums) + 1)):
        return False
    chosen = [int(ch) for ch in ans]
    if any(n not in nums for n in chosen):
        return False
    bodies = [m.group(2).rstrip() for m in matches]
    paired = list(zip(nums, bodies))
    rng.shuffle(paired)
    if [n for n, _ in paired] == nums:
        paired = paired[1:] + paired[:1]
    old_to_new = {old_n: i + 1 for i, (old_n, _) in enumerate(paired)}
    new_ans = "".join(str(old_to_new[n]) for n in chosen)
    # порядок цифр в ключе как в бланке — по возрастанию номеров
    new_ans = "".join(sorted(new_ans))
    head = text[: matches[0].start()]
    block = "\n".join(f"{i}) {body}" for i, (_, body) in enumerate(paired, start=1))
    q["text"] = head + block
    acc = list(q.get("acceptable_answers") or [])
    acc = [new_ans] + [a for a in acc if str(a) != ans]
    _set_answer(q, new_ans, acc)
    _mark(q, "option_set")
    return True


def _matching_shuffle(q: dict[str, Any], rng: random.Random) -> bool:
    """Переставить правый столбец соответствия и пересчитать ключ АБВ."""
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    matching = pl.get("matching") if isinstance(pl.get("matching"), dict) else None
    if not matching:
        return False
    right = matching.get("right")
    if not isinstance(right, list) or len(right) < 3:
        return False
    ans = str(q.get("answer") or "").strip().replace(" ", "")
    if not re.fullmatch(r"[1-9]{2,6}", ans):
        return False
    items = [dict(x) if isinstance(x, dict) else None for x in right]
    if any(x is None for x in items):
        return False
    old_ids = [str(x.get("id") or "") for x in items]
    if any(not i.isdigit() for i in old_ids):
        return False
    rng.shuffle(items)
    if [str(x.get("id")) for x in items] == old_ids:
        items = items[1:] + items[:1]
    old_to_new = {str(item.get("id")): str(i + 1) for i, item in enumerate(items)}
    for i, item in enumerate(items, start=1):
        item["id"] = str(i)
    try:
        new_ans = "".join(old_to_new[ch] for ch in ans)
    except KeyError:
        return False
    matching = dict(matching)
    matching["right"] = items
    pl = dict(pl)
    pl["matching"] = matching
    q["payload"] = pl
    _set_answer(q, new_ans)
    _mark(q, "matching")
    return True


def _linear_eq(q: dict[str, Any], rng: random.Random) -> bool:
    """ax − b = c  →  x = (c+b)/a."""
    text = _text_of(q)
    m = re.search(r"(\d+)\s*x\s*[−\-]\s*(\d+)\s*=\s*(\d+)", text)
    if not m:
        return False
    a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if a == 0 or (c + b) % a != 0:
        return False
    new_a = _pick_other(rng, [2, 3, 4, 5, 6], a)
    new_x = _pick_other(rng, list(range(2, 12)), (c + b) // a)
    new_b = _pick_other(rng, list(range(1, 15)), b)
    new_c = new_a * new_x - new_b
    if new_c <= 0:
        return False
    new_text = text[: m.start()] + f"{new_a}x − {new_b} = {new_c}" + text[m.end() :]
    q["text"] = new_text
    _set_numeric(q, float(new_x))
    _mark(q, "linear")
    return True


def _percent_of(q: dict[str, Any], rng: random.Random) -> bool:
    """Найдите p% от n."""
    text = _text_of(q)
    m = re.search(r"(\d+)\s*%\s+от\s+(\d+)", text, re.I)
    if not m:
        return False
    p, n = int(m.group(1)), int(m.group(2))
    if p % 5 or n % 10:
        return False
    new_p = _pick_other(rng, [10, 15, 20, 25, 30, 40, 50], p)
    new_n = _pick_other(rng, [40, 60, 80, 100, 120, 150, 200], n)
    new_text = text[: m.start()] + f"{new_p}% от {new_n}" + text[m.end() :]
    q["text"] = new_text
    _set_numeric(q, new_n * new_p / 100.0)
    _mark(q, "percent")
    return True


def _objects_table(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"Объекты:\s*(.+?)(?:\.|$)", text)
    ans = str(q.get("answer") or "").strip()
    if not m or not re.fullmatch(r"\d{3,6}", ans):
        return False
    raw = m.group(1)
    names = [x.strip() for x in re.split(r",\s*", raw) if x.strip()]
    if len(names) != len(ans):
        return False
    pairs = list(zip(names, list(ans)))
    rng.shuffle(pairs)
    if [n for n, _ in pairs] == names:
        pairs = pairs[1:] + pairs[:1]
    new_names = [n for n, _ in pairs]
    new_ans = "".join(d for _, d in pairs)
    new_list = ", ".join(new_names)
    new_text = text[: m.start(1)] + new_list + text[m.end(1) :]
    q["text"] = new_text
    _set_answer(q, new_ans)
    _mark(q, "mapping")
    return True


def _frac_plus_dec(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"\\frac\{1\}\{(\d+)\}", text)
    m2 = re.search(r"0\{,\}(\d{1,2})", text)
    if not m or not m2:
        return False
    den = int(m.group(1))
    frac_ok = {2, 4, 5, 8, 10}
    new_den = _pick_other(rng, sorted(frac_ok), den)
    tenths = int(m2.group(1))
    scale = 10 ** len(m2.group(1))
    new_tenths = _pick_other(rng, list(range(1, 9)), tenths if tenths < 10 else tenths // 10)
    if new_den == den and new_tenths == tenths:
        new_den = 5 if den != 5 else 4
    dec = new_tenths / 10.0
    value = 1.0 / new_den + dec
    t = text.replace(m.group(0), f"\\frac{{1}}{{{new_den}}}", 1)
    old_dec = m2.group(0)
    new_dec = "0{,}" + str(new_tenths)
    t2 = _replace_once(t, old_dec, new_dec)
    if t2 is None:
        return False
    q["text"] = t2
    _set_numeric(q, value, ndigits=2)
    _mark(q, "frac")
    return True


def _power_at_a(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"при\s*\$a\s*=\s*(-?\d+)\$", text)
    if not m:
        return False
    # (a^p)^{-q} · a^r  → a^{r - p q}
    exp = re.search(
        r"\(a\^(\d+)\)\^\{?-?(\d+)\}?\s*\\cdot\s*a\^\{?(\d+)\}?",
        text,
    )
    if not exp:
        return False
    p, qexp, r = int(exp.group(1)), int(exp.group(2)), int(exp.group(3))
    power = r - p * qexp
    old_a = int(m.group(1))
    new_a = _pick_other(rng, [2, 3, 4, 5], old_a)
    if new_a == old_a:
        new_a = 3 if old_a != 3 else 2
    t = _replace_once(text, m.group(0), f"при $a = {new_a}$")
    if t is None:
        return False
    q["text"] = t
    _set_numeric(q, new_a ** power)
    _mark(q, "power")
    return True


def _square_eq(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"\$x\^2\s*-\s*(\d+)\s*=\s*0\$", text)
    if not m:
        return False
    old = int(m.group(1))
    squares = [4, 9, 16, 25, 36, 49, 64, 81]
    new_n = _pick_other(rng, squares, old)
    t = _replace_once(text, m.group(0), f"$x^2 - {new_n} = 0$")
    if t is None:
        return False
    q["text"] = t
    _set_numeric(q, int(math.isqrt(new_n)))
    _mark(q, "square")
    return True


def _taxi_prob(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(
        r"свободно\s+(\d+)\s+машин:\s+(\d+)\s+черных,\s+(\d+)\s+желтых\s+и\s+(\d+)\s+белых",
        text,
        re.I,
    )
    if not m:
        return False
    pairs = (
        (1, 10),
        (2, 10),
        (1, 8),
        (2, 8),
        (1, 5),
        (2, 5),
        (1, 4),
        (3, 10),
        (1, 20),
        (3, 20),
        (4, 20),
        (5, 25),
        (2, 25),
        (1, 16),
        (4, 16),
    )
    yellow, total = rng.choice(pairs)
    rest = total - yellow
    black = rng.randint(1, max(1, rest - 1))
    white = rest - black
    if white < 1:
        white = 1
        black = rest - 1
    if black < 1:
        black = 1
        white = rest - 1
    old = m.group(0)
    new = (
        f"свободно {total} машин: {black} черных, {yellow} желтых и {white} белых"
    )
    t = _replace_once(text, old, new)
    if t is None:
        return False
    q["text"] = t
    _set_numeric(q, yellow / total, ndigits=4)
    _mark(q, "prob")
    return True


def _fahrenheit(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"соответствует\s+(\$?-?\d+)\s*\^?\\circ", text)
    if not m:
        m = re.search(r"(-?\d+)\s*\^\\circ\\text\{C\}", text)
    if not m:
        m = re.search(r"(-?\d+)\^\\circ", text)
    if not m:
        return False
    old_t = int(re.sub(r"[^\d\-]", "", m.group(1)))
    new_t = _pick_other(rng, [-20, -15, -10, -5, 0, 5, 10, 15], old_t)
    # keep the same visual wrapper
    old_span = m.group(0)
    new_span = old_span.replace(str(old_t), str(new_t), 1)
    t = _replace_once(text, old_span, new_span)
    if t is None:
        return False
    q["text"] = t
    _set_numeric(q, 1.8 * new_t + 32, ndigits=1)
    _mark(q, "formula")
    return True


def _progression(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(
        r"в первом ряду\s+(\d+)\s+штук,\s+а в каждом следующем на\s+(\d+)\s+штуки больше.*"
        r"в\s+(\d+)\s+рядах",
        text,
        re.I | re.S,
    )
    if not m:
        return False
    a1 = _pick_other(rng, [8, 10, 12, 14, 15, 16], int(m.group(1)))
    d = _pick_other(rng, [2, 3, 4, 5], int(m.group(2)))
    n = _pick_other(rng, [6, 7, 8, 9, 10], int(m.group(3)))
    t = text
    t = t.replace(m.group(1), str(a1), 1)
    t = t.replace(m.group(2), str(d), 1)
    t = t.replace(m.group(3), str(n), 1)
    s = n * (2 * a1 + (n - 1) * d) // 2
    q["text"] = t
    _set_numeric(q, s)
    _mark(q, "progress")
    return True


def _median_hyp(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"\$AB\s*=\s*(\d+)\$\s*,\s*\$BC\s*=\s*(\d+)\$", text)
    if not m:
        return False
    old_ab, old_bc = int(m.group(1)), int(m.group(2))
    pool = [t for t in _PYTHAGOREAN if t[2] != old_ab]
    bc, _ac, ab = rng.choice(pool) if pool else (old_bc, 0, old_ab)
    # BC is a leg
    old = m.group(0)
    new = f"$AB = {ab}$, $BC = {bc}$"
    t = _replace_once(text, old, new)
    if t is None:
        return False
    q["text"] = t
    _set_numeric(q, ab / 2)
    _mark(q, "median")
    return True


def _inscribed_angles(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m1 = re.search(r"Угол\s*\$ABC\$\s*равен\s*\$(\d+)\^\\circ\$", text)
    m2 = re.search(r"угол\s*\$CAD\$\s*равен\s*\$(\d+)\^\\circ\$", text)
    if not m1 or not m2:
        return False
    abc = rng.choice([100, 105, 110, 115, 120, 125])
    cad = rng.choice([20, 25, 30, 35, 40])
    if abc <= cad:
        abc = cad + 70
    t = text
    t = t[: m1.start(1)] + str(abc) + t[m1.end(1) :]
    m2b = re.search(r"угол\s*\$CAD\$\s*равен\s*\$(\d+)\^\\circ\$", t)
    if not m2b:
        return False
    t = t[: m2b.start(1)] + str(cad) + t[m2b.end(1) :]
    q["text"] = t
    _set_numeric(q, abc - cad)
    _mark(q, "circle")
    return True


def _rhombus_area(q: dict[str, Any], rng: random.Random) -> bool:
    text = _text_of(q)
    m = re.search(r"Периметр ромба равен\s+(\d+),\s+а один из углов равен\s+\$(\d+)\^\\circ\$", text)
    if not m:
        return False
    old_p = int(m.group(1))
    ang = int(m.group(2))
    if ang != 30:
        return False  # sin known only for 30 in this template
    new_p = _pick_other(rng, [20, 24, 28, 32, 36, 40, 44, 48, 52], old_p)
    if new_p % 4:
        new_p = 40
    t = _replace_once(text, str(old_p), str(new_p))
    if t is None:
        return False
    q["text"] = t
    a = new_p / 4.0
    _set_numeric(q, a * a * 0.5)
    _mark(q, "rhombus")
    return True


_MATH_BY_NUM = {
    1: _objects_table,
    6: _frac_plus_dec,
    8: _power_at_a,
    9: _square_eq,
    10: _taxi_prob,
    12: _fahrenheit,
    14: _progression,
    15: _median_hyp,
    16: _inscribed_angles,
    17: _rhombus_area,
}


def _mutate_one(q: dict[str, Any], rng: random.Random, *, math_mode: bool) -> bool:
    if _part_of(q) != 1:
        return False
    num = _num_of(q)
    if math_mode:
        if num >= 20:
            return False
        # 1–5 — общий сюжет, числа считает mutate_task_group
        if num in {1, 2, 3, 4, 5}:
            return False
        if apply_mutator_logic_to_question(q, rng):
            return True
        if num in _MATH_BY_NUM:
            try:
                if _MATH_BY_NUM[num](q, rng):
                    return True
            except Exception:
                pass
        for fn in (_linear_eq, _percent_of):
            try:
                if fn(q, rng):
                    return True
            except Exception:
                pass
        if num in {7, 13, 19}:
            try:
                if _mcq_shuffle(q, rng):
                    return True
            except Exception:
                pass
        return False
    for fn in (_matching_shuffle, _option_set_shuffle, _mcq_shuffle):
        try:
            if fn(q, rng):
                return True
        except Exception:
            pass
    return False


def personalize_questions(
    questions: list[dict[str, Any]],
    *,
    assignment_id: int,
    student_name: str,
    subject: Optional[str] = None,
    enabled: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """Вернуть копию вопросов, уникальную для ученика.

    Если enabled=False или нет ФИО — исходный список (копия верхнего уровня).
    """
    src = [copy.deepcopy(q) if isinstance(q, dict) else q for q in (questions or [])]
    name = str(student_name or "").strip()
    if not enabled or len(name) < 2:
        return src, 0
    rng = _rng(int(assignment_id), name)
    math_mode = _subject_is_math(subject)
    changed = 0
    if math_mode:
        changed += mutate_task_group(src, rng, enabled=True)
    for q in src:
        if not isinstance(q, dict):
            continue
        if math_mode and _num_of(q) in {1, 2, 3, 4, 5}:
            continue
        slot_rng = random.Random(rng.randint(1, 2**31 - 1) ^ (_num_of(q) * 10007))
        if _mutate_one(q, slot_rng, math_mode=math_mode):
            changed += 1
    return src, changed
