"""Проверка прямой, угла, степеней и заморозки ключа.

  py -3 -m backend.scripts._test_oge_math_visual
"""

from __future__ import annotations

import re

from backend.services.figures import (
    attach_figure,
    build_figure_svg,
    svg_numberline,
    svg_triangle_with_angle,
)
from backend.services.math_mutator import personalize_questions
from backend.services.prompts import caret_to_superscripts, polish_fipi_text


def main() -> int:
    errors: list[str] = []

    svg = svg_numberline(
        "На координатной прямой отмечена точка A.",
        {"min": 3, "max": 4, "points": [{"x": 3.7, "label": "A"}]},
    )
    if "[-1" in svg:
        errors.append("numberline: fake interval on point task")
    if "stroke-width=\"2.4\"" in svg:
        errors.append("numberline: thick overlay on axis")
    if "geo-fig-line" not in svg:
        errors.append("numberline: missing geo-fig-line class")

    empty = svg_numberline("x + 5 > 12", {})
    if "stroke-width=\"2.2\"" in empty:
        errors.append("numberline: parsed inequality as interval")

    tri_text = "В треугольнике ABC известно, что AC = BC, угол C равен 60 градусам."
    tri = svg_triangle_with_angle(tri_text, {"angle": 60})
    if "60°" not in tri:
        errors.append("triangle: angle not labeled at vertex")
    # 60 не должно стоять как длина стороны без градуса
    if ">60<" in tri.replace("60°", ""):
        errors.append("triangle: 60 dumped as side length")
    built = build_figure_svg("triangle", tri_text, {"angle": 60}) or ""
    if "60°" not in built:
        errors.append("build_figure_svg triangle: no 60°")

    src = "Найдите значение выражения 2^5 : 2^2"
    polished = polish_fipi_text(src)
    if "2⁵" not in polished or "2²" not in polished:
        errors.append(f"polish powers: {polished!r}")
    if "^" in polished:
        errors.append(f"polish leftover caret: {polished!r}")
    if caret_to_superscripts("2^{5} : 2^{2}") != "2⁵ : 2²":
        errors.append("caret_to_superscripts braced")

    q = {
        "num": 1,
        "part": 1,
        "task_number": 8,
        "text": "Найдите значение выражения 2^5 : 2^2",
        "answer": "8",
        "payload": {"bank_code": "О1", "mutator_values": {"a": 2}},
        "subject_code": "math",
        "exam_code": "OGE",
    }
    out, n = personalize_questions(
        [q], assignment_id=1, student_name="Иванов Иван", subject="Математика"
    )
    if n != 0 or out[0]["answer"] != "8":
        errors.append(f"personalize froze fail n={n} a={out[0].get('answer')}")

    attached = attach_figure(
        {
            "task_number": 1,
            "text": "Шина 195/65 R15",
            "figure_kind": "scheme",
            "figure_params": {"theme": "wheel"},
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    fig = attached.get("figure_svg") or ""
    if "R15" not in fig and "рис." not in fig:
        errors.append("scheme wheel missing")
    if "B" not in fig or "D" not in fig:
        errors.append("scheme wheel missing B/D labels")

    match = build_figure_svg("graph_match", "Установите соответствие между графиками и формулами.", {}) or ""
    if "1)" not in match or "2)" not in match or "3)" not in match:
        errors.append("graph_match missing numbered panels")
    mixed = build_figure_svg(
        "graph_match",
        "",
        {"graphs": ["hyperbola", "parabola", "line_down"], "a": 1, "b": 2, "k": 2},
    ) or ""
    if mixed.count("<polyline") < 6:
        errors.append("graph_match mixed curves too sparse")
    parabs = build_figure_svg(
        "graph_match",
        "",
        {"graphs": ["parabola", "parabola_down", "parabola_shift"]},
    ) or ""
    if parabs.count("<polyline") < 3:
        errors.append("graph_match parabolas too sparse")
    lines = build_figure_svg(
        "graph_match",
        "",
        {"graphs": ["line_up", "line_down", "line_horiz"], "b": 2},
    ) or ""
    if lines.count("<polyline") < 3:
        errors.append("graph_match lines too sparse")
    hyps = build_figure_svg(
        "graph_match",
        "",
        {"graphs": ["hyperbola", "hyperbola_neg", "parabola_shift"], "k": 2},
    ) or ""
    if hyps.count("<polyline") < 5:
        errors.append("graph_match hyperbolas too sparse")
    slot11 = attach_figure(
        {
            "task_number": 11,
            "text": "Установите соответствие между графиками квадратичных функций и формулами.",
            "figure_kind": "graph_parabola",
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    if slot11.get("figure_kind") != "graph_match":
        errors.append(f"slot 11 must be graph_match, got {slot11.get('figure_kind')}")

    plan = build_figure_svg(
        "plan",
        "План квартиры",
        {
            "title": "План",
            "width": 8,
            "height": 8,
            "cell_m": 1,
            "rooms": [{"id": "1", "label": "Кухня", "x": 0, "y": 0, "w": 3, "h": 3}],
            "doors": [{"x": 1, "y": 2.8, "w": 0.8, "h": 0.2}],
            "windows": [{"x": 0, "y": 1, "w": 0.2, "h": 1}],
        },
    ) or ""
    if "м" not in plan:
        errors.append("plan scale missing")
    if re.search(r">[0-9]+<", plan) and "ось" in plan:
        errors.append("plan still looks like a graph axis")

    stove = build_figure_svg("scheme", "печь", {"theme": "stove"}) or ""
    if "R" not in stove:
        errors.append("stove arch missing R")
    if "топка" not in stove or "40" not in stove:
        errors.append("stove missing топка/40")

    paper = build_figure_svg("scheme", "бумага", {"theme": "paper"}) or ""
    if "A0" not in paper or "A1" not in paper:
        errors.append("paper nested A formats missing")

    travel = build_figure_svg("scheme", "местность", {"theme": "travel"}) or ""
    if "шоссе" not in travel:
        errors.append("travel map missing шоссе")

    umbrella = build_figure_svg("scheme", "зонт", {"theme": "umbrella"}) or ""
    if "Рис. 1" not in umbrella or "Рис. 3" not in umbrella:
        errors.append("umbrella missing Рис. 1 / Рис. 3")
    if ">h<" not in umbrella or "Δ" not in umbrella:
        errors.append("umbrella missing hΔ")
    if ">R</text>" not in umbrella:
        errors.append("umbrella missing R")
    for mark in ("O", "C", "M", "D", "ручка зонта"):
        if mark not in umbrella:
            errors.append(f"umbrella missing {mark}")

    from backend.universal.adapt import fold_oge_math_context_group
    from backend.universal.variant_builder import strip_shared_story
    from backend.services.math_mutator import mutate_task, mutate_task_group

    story = "Завод допускает установку шин с разными маркировками. В таблице цены."
    qtext = story + " Какой наименьшей ширины шины можно ставить?"
    stripped = strip_shared_story(qtext, story)
    if "наименьшей" not in stripped or stripped.startswith("Завод допускает"):
        errors.append(f"strip_shared_story failed: {stripped!r}")

    wheel_svg = build_figure_svg("scheme", "шина", {"theme": "wheel"}) or "x"
    grouped = [
        {
            "num": 1,
            "text": story + " Вопрос один про ширину.",
            "figure_kind": "scheme",
            "figure_svg": wheel_svg,
            "payload": {
                "shared_story": story,
                "asset_id": "TireDiagram",
                "context_title": "Шины",
                "context_id": "tires_factory",
            },
        },
        {
            "num": 2,
            "text": story + " Вопрос два про комплект.",
            "figure_kind": "scheme",
            "figure_svg": wheel_svg,
            "payload": {"shared_story": story},
        },
    ]
    fold_oge_math_context_group(grouped)
    ctx = (grouped[0].get("payload") or {}).get("math_context") or {}
    if grouped[0].get("figure_svg") or grouped[1].get("figure_svg"):
        errors.append("fold left figure_svg on subtasks")
    if not ctx.get("figure_svg"):
        errors.append("fold missing group figure_svg")
    if "Вопрос два" not in grouped[1].get("text", "") or grouped[1]["text"].startswith("Завод"):
        errors.append("fold did not strip story from q2")

    if mutate_task({"template": "x", "mutator_logic": {}}, enabled=False) is not None:
        errors.append("mutate_task(enabled=False) should be None")
    n_g = mutate_task_group(
        [
            {"num": 1, "text": "a", "payload": {"base_vars": {"B": 195}}, "figure_params": {"theme": "wheel"}},
            {"num": 2, "text": "b", "payload": {}},
        ],
        enabled=True,
    )
    if n_g < 0:
        errors.append("mutate_task_group failed")

    from backend.services.math_mutator import generate_math_task
    import json
    from pathlib import Path

    spec_path = (
        Path(__file__).resolve().parents[1]
        / "universal"
        / "specs"
        / "math_oge_mutator.json"
    )
    mut = json.loads(spec_path.read_text(encoding="utf-8"))
    proto7 = next(
        p for p in mut["prototypes"] if p.get("figure_params", {}).get("subtype_code") == "math_oge_q07_sqrt_point"
    )
    spec7 = {
        "template": proto7["template_text"],
        "mutator_logic": proto7["figure_params"]["mutator_logic"],
        "explanation_template": proto7["figure_params"]["explanation_template"],
    }
    g7 = generate_math_task(spec7, rng=__import__("random").Random(7))
    if g7["answer"] not in {"A", "B", "C", "D"}:
        errors.append(f"sqrt_point answer {g7['answer']!r}")
    fig7 = g7.get("figure_params") or {}
    pts7 = fig7.get("points") if isinstance(fig7.get("points"), list) else []
    if len(pts7) < 4 or any(not isinstance(pt.get("x"), (int, float)) for pt in pts7 if isinstance(pt, dict)):
        errors.append(f"sqrt_point figure points not numeric: {fig7!r}")
    att7 = attach_figure(
        {
            "task_number": 7,
            "text": g7["text"],
            "figure_kind": "numberline",
            "figure_params": fig7,
            "payload": {"mutator_values": g7.get("values") or {}},
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    svg7 = att7.get("figure_svg") or ""
    if "-2" in svg7 and "7" not in svg7:
        errors.append("sqrt_point attach still default -2..3")
    k7 = (g7.get("values") or {}).get("k")
    if k7 is not None and f">{int(k7)}<" not in svg7 and f">{int(k7)}</text>" not in svg7:
        if str(int(k7)) not in svg7:
            errors.append(f"sqrt_point SVG missing tick {k7}: {svg7[:240]!r}")

    rebuilt = attach_figure(
        {
            "task_number": 7,
            "text": "На координатной прямой отмечены точки A, B, C и D. Какой из них соответствует число √67?",
            "figure_kind": "numberline",
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    svg_r = rebuilt.get("figure_svg") or ""
    if "7" not in svg_r or "9" not in svg_r:
        errors.append("√67 numberline was not reconstructed 7..9")
    if re.search(r">-2<", svg_r):
        errors.append("√67 numberline still has dummy tick -2")

    ineq = attach_figure(
        {
            "task_number": 13,
            "text": "Решите систему неравенств:\nx > 4\nx ≤ 9\nВ ответ запишите наименьшее целое число, которое является решением системы.",
            "figure_kind": "numberline",
            "payload": {"mutator_values": {"a": 4, "b": 9, "answer": 5}},
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    svg13 = ineq.get("figure_svg") or ""
    if "4" not in svg13 or "9" not in svg13:
        errors.append("system ineq numberline missing 4/9")
    if re.search(r">-2<", svg13):
        errors.append("system ineq numberline dummy -2..3")

    match_vals = attach_figure(
        {
            "task_number": 11,
            "text": "Установите соответствие между графиками и формулами.",
            "figure_kind": "graph_match",
            "payload": {"mutator_values": {"g1": "parabola", "g2": "parabola_down", "g3": "parabola_shift"}},
            "subject_code": "math",
            "exam_code": "OGE",
            "_oge_math_figures": True,
        }
    )
    svg11 = match_vals.get("figure_svg") or ""
    if svg11.count("<polyline") < 3:
        errors.append("graph_match from mutator_values too sparse")

    proto8 = next(
        p for p in mut["prototypes"] if p.get("figure_params", {}).get("subtype_code") == "math_oge_q08_radical_product"
    )
    g8 = generate_math_task(
        {
            "template": proto8["template_text"],
            "mutator_logic": proto8["figure_params"]["mutator_logic"],
            "explanation_template": proto8["figure_params"]["explanation_template"],
        },
        rng=__import__("random").Random(8),
    )
    try:
        int(g8["answer"])
    except (TypeError, ValueError):
        errors.append(f"radical_product answer {g8['answer']!r}")

    tang = build_figure_svg("circle", "", {"theme": "two_tangents"}) or ""
    if "<svg" not in tang or "P" not in tang or "A" not in tang:
        errors.append("two_tangents figure missing labels")
    cyclic = build_figure_svg("circle", "", {"theme": "cyclic_quad"}) or ""
    if "<polygon" not in cyclic:
        errors.append("cyclic_quad missing inscribed quad")
    insc = build_figure_svg("circle", "", {"theme": "inscribed_angle"}) or ""
    if "O" not in insc or "C" not in insc:
        errors.append("inscribed_angle missing O/C")
    rho = build_figure_svg("rect", "", {"shape": "rhombus", "side": "a"}) or ""
    if "<polygon" not in rho:
        errors.append("rhombus not drawn as diamond")
    trap = build_figure_svg("rect", "", {"shape": "trapezoid", "a": "6", "b": "12", "h": "4"}) or ""
    if "<polygon" not in trap:
        errors.append("trapezoid not drawn")
    grid_tan = build_figure_svg(
        "grid",
        "",
        {"cols": 8, "rows": 7, "angle": {"vertex": [1, 1], "p1": [1, 4], "p2": [5, 1]}},
    ) or ""
    if "<polyline" not in grid_tan:
        errors.append("grid tan missing angle polyline")

    proto_tan = next(
        p for p in mut["prototypes"] if p.get("figure_params", {}).get("subtype_code") == "math_oge_q18_grid_tan"
    )
    gtan = generate_math_task(
        {
            "template": proto_tan["template_text"],
            "mutator_logic": proto_tan["figure_params"]["mutator_logic"],
            "explanation_template": proto_tan["figure_params"]["explanation_template"],
        },
        rng=__import__("random").Random(18),
    )
    if gtan["answer"] not in {"0.75", "0.4", "0.8", "0.5", "0.6"}:
        errors.append(f"grid_tan answer {gtan['answer']!r}")
    if not (gtan.get("figure_params") or {}).get("angle"):
        errors.append("grid_tan missing angle figure")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("ok visual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
