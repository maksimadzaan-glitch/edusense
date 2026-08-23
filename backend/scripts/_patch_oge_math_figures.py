# -*- coding: utf-8 -*-
"""One-shot: add figure_kind/figure_params to OGE math prototypes that can auto-draw."""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "universal" / "specs" / "math_oge.json"

# title substring -> (figure_kind, figure_params|None)
PATCHES: dict[str, tuple[str, dict | None]] = {
    "1a:": (
        "plan",
        {
            "title": "план участка",
            "width": 10,
            "height": 8,
            "gate": {"side": "bottom", "at": 5, "width": 1.5},
            "rooms": [
                {"id": "2", "label": "Гараж", "x": 6.5, "y": 5.5, "w": 3, "h": 2.2},
                {"id": "4", "label": "Сарай", "x": 0.5, "y": 5.5, "w": 2.5, "h": 2},
                {"id": "1", "label": "Баня", "x": 0.5, "y": 3.2, "w": 2.5, "h": 2},
                {"id": "3", "label": "Дом", "x": 3.5, "y": 0.5, "w": 4, "h": 3},
            ],
        },
    ),
    "1b:": (
        "plan",
        {
            "title": "план квартиры",
            "width": 10,
            "height": 8,
            "gate": {"side": "bottom", "at": 2.2, "width": 1.2},
            "rooms": [
                {"id": "2", "label": "Прихожая", "x": 1.2, "y": 5.5, "w": 2.2, "h": 2.2},
                {"id": "1", "label": "С/у", "x": 0.2, "y": 5.5, "w": 0.9, "h": 2.2},
                {"id": "6", "label": "Гостиная", "x": 3.6, "y": 2.5, "w": 5.8, "h": 5.2},
                {"id": "4", "label": "Кухня", "x": 0.2, "y": 2.5, "w": 3.2, "h": 2.8},
                {"id": "5", "label": "Лоджия", "x": 0.2, "y": 0.3, "w": 3.2, "h": 1.8},
                {"id": "3", "label": "Спальня", "x": 3.6, "y": 0.3, "w": 5.8, "h": 2},
            ],
        },
    ),
    "7a:": (
        "numberline",
        {
            "min": 5,
            "max": 8,
            "points": [{"x": 6.24, "label": "A"}],
            "label": "√39 ≈ 6,2",
        },
    ),
    "7c:": (
        "numberline",
        {
            "min": -4,
            "max": 3,
            "points": [{"x": -3, "label": "a"}, {"x": 1.5, "label": "b"}],
            "label": "a < 0 < b",
        },
    ),
    "11a:": ("graph_parabola", {"title": "парабола y = ax²+bx+c"}),
    "11b:": ("graph_hyperbola", None),
    "11c:": ("graph_linear", None),
    "15a:": ("triangle", None),
    "15b:": ("triangle", None),
    "15c:": ("triangle", None),
    "16a:": ("circle", None),
    "16b:": ("circle", None),
    "16c:": ("circle", None),
    "17a:": ("rect", None),
    "17b:": ("rect", None),
    "17c:": ("triangle", None),
    "18a:": (
        "grid",
        {
            "cols": 8,
            "rows": 8,
            "title": "угол на клетках",
            "angle": {"vertex": [1, 1], "p1": [1, 5], "p2": [6, 1]},
        },
    ),
    "18b:": (
        "grid",
        {
            "cols": 10,
            "rows": 6,
            "title": "трапеция",
            "polygons": [[[1, 1], [8, 1], [6, 4], [3, 4]]],
        },
    ),
    "18c:": (
        "grid",
        {
            "cols": 8,
            "rows": 6,
            "title": "расстояние до прямой",
            "lines": [[[1, 2], [7, 2]]],
            "points": [{"x": 4, "y": 5, "label": "A"}],
        },
    ),
}


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    n = 0
    for p in data["prototypes"]:
        title = p.get("prototype_title") or ""
        for prefix, (kind, params) in PATCHES.items():
            if title.startswith(prefix):
                p["figure_kind"] = kind
                if params is not None:
                    p["figure_params"] = params
                elif "figure_params" in p and prefix.startswith("11"):
                    pass
                n += 1
                break
    # Improve self-contained texts that still say «на плане» without numbers
    for p in data["prototypes"]:
        title = p.get("prototype_title") or ""
        if title.startswith("2b:"):
            p["template_text"] = (
                "На плане жилой дом занимает прямоугольник 4 клетки на 8,5 клеток "
                "(плюс выступ 1×2 клетки). Сторона одной клетки на плане равна 2 м. "
                "Найдите площадь, которую занимает жилой дом. Ответ дайте в квадратных метрах."
            )
            p["template_answer"] = "72"
            # 4*8.5*4 + 1*2*4 = 136+8=144? Wait recalculate
            # Better: house 5×6 cells + porch 2×2, cell=2m → (30+4)*4 = 136
            p["template_text"] = (
                "На плане жилой дом занимает прямоугольник 5×6 клеток, а пристройка — "
                "квадрат 2×2 клетки. Сторона одной клетки равна 2 м. "
                "Найдите суммарную площадь дома с пристройкой в квадратных метрах."
            )
            p["template_answer"] = "136"
        if title.startswith("3a:"):
            p["template_text"] = (
                "На плане расстояние между ближайшими углами жилого дома и бани "
                "образует прямоугольный треугольник с катетами 3 клетки и 4 клетки. "
                "Сторона клетки равна 2 м. Найдите расстояние от жилого дома до бани "
                "по прямой (в метрах)."
            )
            p["template_answer"] = "10"

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"patched figures on {n} prototypes; wrote {PATH}")


if __name__ == "__main__":
    main()
