"""Чертежи в стиле бланка ФИПИ: белый фон, чёрные тонкие линии."""

from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path
from typing import Any, Optional

ALLOWED_KINDS = frozenset(
    {
        "rect",
        "triangle",
        "box3d",
        "circle",
        "numberline",
        "graph_linear",
        "graph_parabola",
        "graph_hyperbola",
        "graph_cubic",
        "plan",
        "grid",
        "scheme",
        "graph_match",  # №11 три графика
        "asset",
    }
)

PACKS_ROOT = Path(__file__).resolve().parent.parent / "universal" / "packs"
DEFAULT_FIGURE_PACK = "oge_math"

# ОГЭ математика: дефолтный вид чертежа по номеру задания (если нет figure_kind).
# plan/grid — только при figure_params (иначе не рисуем фейк).
# Часть 2 (20–25): без авто-чертежей — только явный figure_kind из шаблона
# (ложный rect/circle хуже отсутствия рисунка).
OGE_MATH_DEFAULT_KIND: dict[int, str] = {
    7: "numberline",
    11: "graph_match",
    13: "numberline",
    15: "triangle",
    16: "circle",
    17: "rect",
    18: "grid",
}

# Палитра бланка (не currentColor UI)
STROKE = "#111111"
FILL_DOT = "#111111"
BG = "#ffffff"
FONT = "Times New Roman, Liberation Serif, serif"
GRID_STROKE = "#bbbbbb"


def _esc(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def _nums_from_text(text: str) -> list[float]:
    out: list[float] = []
    for m in re.findall(r"[-+]?\d+(?:[.,]\d+)?", text or ""):
        try:
            out.append(float(m.replace(",", ".")))
        except ValueError:
            continue
    return out


def _svg_wrap(
    inner: str,
    label: str,
    *,
    width: float = 200,
    height: float = 200,
    extra_class: str = "",
) -> str:
    w = int(width) if float(width).is_integer() else width
    h = int(height) if float(height).is_integer() else height
    cls = "geo-fig fipi-fig"
    if extra_class:
        cls += f" {extra_class}"
    return (
        f'<svg class="{cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="xMidYMid meet" aria-label="{_esc(label)}">'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>'
        f'<g fill="none" stroke="{STROKE}" stroke-width="1.15" '
        f'stroke-linecap="butt" stroke-linejoin="miter">{inner}</g>'
        f"</svg>"
    )


def _txt(
    x: float,
    y: float,
    s: str,
    *,
    anchor: str = "middle",
    size: int = 12,
    fill: str | None = None,
    italic: bool = False,
    weight: str = "normal",
) -> str:
    c = fill or STROKE
    style = "italic" if italic else "normal"
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{c}" stroke="none" '
        f'font-size="{size}" font-style="{style}" font-weight="{weight}" '
        f'font-family="{FONT}">{_esc(s)}</text>'
    )


def _dim_h(x1: float, x2: float, y: float, label: str) -> str:
    """Горизонтальный размер с засечками — как на чертеже КИМ."""
    if x2 < x1:
        x1, x2 = x2, x1
    mid = (x1 + x2) / 2
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x1:.1f}" y1="{y - 4:.1f}" x2="{x1:.1f}" y2="{y + 4:.1f}"/>'
        f'<line x1="{x2:.1f}" y1="{y - 4:.1f}" x2="{x2:.1f}" y2="{y + 4:.1f}"/>'
        + _txt(mid, y + 13, label, size=11)
    )


def _dim_v(x: float, y1: float, y2: float, label: str) -> str:
    if y2 < y1:
        y1, y2 = y2, y1
    mid = (y1 + y2) / 2
    return (
        f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"/>'
        f'<line x1="{x - 4:.1f}" y1="{y1:.1f}" x2="{x + 4:.1f}" y2="{y1:.1f}"/>'
        f'<line x1="{x - 4:.1f}" y1="{y2:.1f}" x2="{x + 4:.1f}" y2="{y2:.1f}"/>'
        + _txt(x - 10, mid + 4, label, size=11)
    )


def _axes() -> str:
    return f"""
  <line x1="24" y1="100" x2="186" y2="100"/>
  <line x1="100" y1="176" x2="100" y2="24"/>
  <polyline points="180,96 186,100 180,104"/>
  <polyline points="96,30 100,24 104,30"/>
  {_txt(192, 96, "x", anchor="start", size=11)}
  {_txt(108, 28, "y", anchor="start", size=11)}
  <circle cx="100" cy="100" r="1.4" fill="{FILL_DOT}" stroke="none"/>
"""


def svg_rectangle(a: str = "a", b: str = "b") -> str:
    inner = f"""
  <rect x="40" y="50" width="120" height="80"/>
  {_txt(100, 150, a)}
  {_txt(28, 94, b)}
  {_txt(40, 46, "A", anchor="start", size=11)}
  {_txt(160, 46, "B", anchor="start", size=11)}
  {_txt(160, 146, "C", anchor="start", size=11)}
  {_txt(40, 146, "D", anchor="start", size=11)}
"""
    return _svg_wrap(inner, "Прямоугольник")


def svg_right_triangle(a: str = "a", b: str = "b", c: str = "c") -> str:
    inner = f"""
  <polygon points="42,150 158,150 42,52"/>
  <path d="M42 134 h16 v16"/>
  {_txt(100, 168, a)}
  {_txt(28, 104, b)}
  {_txt(112, 92, c)}
  {_txt(42, 48, "C", anchor="start", size=11)}
  {_txt(36, 166, "A", anchor="start", size=11)}
  {_txt(162, 166, "B", anchor="start", size=11)}
"""
    return _svg_wrap(inner, "Прямоугольный треугольник")


def _unit_vec(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _angle_arc(
    vx: float,
    vy: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    radius: float = 22.0,
) -> str:
    ux1, uy1 = _unit_vec(ax - vx, ay - vy)
    ux2, uy2 = _unit_vec(bx - vx, by - vy)
    sx, sy = vx + ux1 * radius, vy + uy1 * radius
    ex, ey = vx + ux2 * radius, vy + uy2 * radius
    cross = ux1 * uy2 - uy1 * ux2
    sweep = 1 if cross > 0 else 0
    return (
        f'<path d="M {sx:.1f} {sy:.1f} A {radius:.1f} {radius:.1f} 0 0 {sweep} '
        f'{ex:.1f} {ey:.1f}"/>'
    )


def _angle_label_pos(
    vx: float,
    vy: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    dist: float = 38.0,
) -> tuple[float, float]:
    ux1, uy1 = _unit_vec(ax - vx, ay - vy)
    ux2, uy2 = _unit_vec(bx - vx, by - vy)
    bxu, byu = _unit_vec(ux1 + ux2, uy1 + uy2)
    return vx + bxu * dist, vy + byu * dist


def _mid_tick(x1: float, y1: float, x2: float, y2: float, size: float = 5.0) -> str:
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ux, uy = _unit_vec(x2 - x1, y2 - y1)
    px, py = -uy, ux
    return (
        f'<line x1="{mx - px * size:.1f}" y1="{my - py * size:.1f}" '
        f'x2="{mx + px * size:.1f}" y2="{my + py * size:.1f}"/>'
    )


def _extract_vertex_angle(text: str, params: Optional[dict[str, Any]] = None) -> Optional[int]:
    p = params or {}
    for key in ("angle", "angle_c", "c_deg"):
        raw = p.get(key)
        if raw is None:
            continue
        try:
            val = int(round(float(raw)))
            if 1 <= val < 180:
                return val
        except (TypeError, ValueError):
            continue
    blob = text or ""
    patterns = (
        r"угол\s*(?:[ABCАВС]|при\s+вершине\s+[ABCАВС])?\s*(?:равен|=)\s*(\d+)\s*град",
        r"равен[ао]?\s+(\d+)\s*градус",
        r"(\d+)\s*°",
    )
    for pat in patterns:
        m = re.search(pat, blob, flags=re.I)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val < 180:
                    return val
            except (TypeError, ValueError):
                continue
    return None


def svg_triangle_with_angle(text: str = "", params: Optional[dict[str, Any]] = None) -> str:
    """Равнобедренный / произвольный треугольник: дуга угла у вершины, не цифра на стороне."""
    p = params or {}
    angle = _extract_vertex_angle(text, p)
    blob = (text or "").lower()
    isosceles = any(k in blob for k in ("ac = bc", "ac=bc", "равнобедр"))
    exterior = "внешн" in blob
    # C сверху, основание AB
    cx, cy = 100.0, 40.0
    ax, ay = 36.0, 152.0
    bx, by = 164.0, 152.0
    parts = [
        f'<polygon points="{ax:.0f},{ay:.0f} {bx:.0f},{by:.0f} {cx:.0f},{cy:.0f}"/>',
        _txt(ax - 10, ay + 14, "A", size=12),
        _txt(bx + 10, by + 14, "B", size=12),
        _txt(cx, cy - 10, "C", size=12),
    ]
    if isosceles:
        parts.append(_mid_tick(ax, ay, cx, cy))
        parts.append(_mid_tick(bx, by, cx, cy))
    if angle is not None:
        parts.append(_angle_arc(cx, cy, ax, ay, bx, by, radius=24))
        lx, ly = _angle_label_pos(cx, cy, ax, ay, bx, by, dist=42)
        parts.append(_txt(lx, ly + 4, f"{angle}°", size=13))
    if exterior:
        # продолжение основания за B
        dx, dy = bx + 36, by
        parts.append(f'<line x1="{bx:.0f}" y1="{by:.0f}" x2="{dx:.0f}" y2="{dy:.0f}"/>')
        parts.append(_txt(dx + 8, dy + 4, "D", size=11))
        parts.append(_angle_arc(bx, by, dx, dy, cx, cy, radius=18))
    return _svg_wrap("\n".join(parts), "Треугольник ABC")


def svg_box3d(a: str = "a", b: str = "b", c: str = "c") -> str:
    # классический параллелепипед: перед сплошной, зад тонкий пунктир
    inner = f"""
  <polygon points="58,42 148,42 148,112 58,112" stroke-dasharray="2.5 2.5"/>
  <polygon points="36,68 126,68 126,138 36,138"/>
  <line x1="36" y1="68" x2="58" y2="42"/>
  <line x1="126" y1="68" x2="148" y2="42"/>
  <line x1="126" y1="138" x2="148" y2="112"/>
  <line x1="36" y1="138" x2="58" y2="112" stroke-dasharray="2.5 2.5"/>
  {_txt(81, 156, a)}
  {_txt(24, 108, b)}
  {_txt(162, 98, c)}
  {_txt(38, 64, "A", anchor="start", size=10)}
  {_txt(118, 64, "B", anchor="start", size=10)}
  {_txt(118, 152, "C", anchor="start", size=10)}
  {_txt(30, 152, "D", anchor="start", size=10)}
"""
    return _svg_wrap(inner, "Прямоугольный параллелепипед")


def svg_circle(r: str = "R", params: Optional[dict[str, Any]] = None) -> str:
    p = params or {}
    theme = str(p.get("theme") or p.get("shape") or "").strip().lower()
    if theme in {"two_tangents", "tangents"}:
        inner = f"""
  <circle cx="88" cy="108" r="42"/>
  <circle cx="88" cy="108" r="1.8" fill="{FILL_DOT}" stroke="none"/>
  {_txt(78, 104, "O", size=12, italic=True)}
  <line x1="52" y1="80" x2="148" y2="28"/>
  <line x1="118" y1="136" x2="148" y2="28"/>
  <circle cx="148" cy="28" r="2" fill="{FILL_DOT}" stroke="none"/>
  <circle cx="62" cy="74" r="2" fill="{FILL_DOT}" stroke="none"/>
  <circle cx="122" cy="132" r="2" fill="{FILL_DOT}" stroke="none"/>
  {_txt(154, 22, "P", size=12, italic=True)}
  {_txt(48, 68, "A", size=12, italic=True)}
  {_txt(132, 148, "B", size=12, italic=True)}
"""
        return _svg_wrap(inner, "Касательные к окружности")
    if theme in {"cyclic_quad", "inscribed_quad"}:
        inner = f"""
  <circle cx="100" cy="100" r="62"/>
  <polygon points="48,78 128,46 152,118 68,148"/>
  {_txt(38, 74, "A", size=12, italic=True)}
  {_txt(130, 38, "B", size=12, italic=True)}
  {_txt(160, 128, "C", size=12, italic=True)}
  {_txt(58, 166, "D", size=12, italic=True)}
"""
        return _svg_wrap(inner, "Вписанный четырёхугольник")
    if theme in {"inscribed_angle", "central_inscribed"}:
        inner = f"""
  <circle cx="100" cy="108" r="58"/>
  <circle cx="100" cy="108" r="1.8" fill="{FILL_DOT}" stroke="none"/>
  {_txt(108, 104, "O", size=12, italic=True)}
  <line x1="100" y1="108" x2="52" y2="78"/>
  <line x1="100" y1="108" x2="148" y2="78"/>
  <line x1="52" y1="78" x2="100" y2="162"/>
  <line x1="148" y1="78" x2="100" y2="162"/>
  {_txt(40, 72, "A", size=12, italic=True)}
  {_txt(154, 72, "B", size=12, italic=True)}
  {_txt(100, 178, "C", size=12, italic=True)}
"""
        return _svg_wrap(inner, "Вписанный угол")
    inner = f"""
  <circle cx="100" cy="100" r="56"/>
  <line x1="100" y1="100" x2="156" y2="100"/>
  <circle cx="100" cy="100" r="1.6" fill="{FILL_DOT}" stroke="none"/>
  {_txt(130, 94, r, size=12)}
"""
    return _svg_wrap(inner, "Окружность")


def svg_rhombus(side: str = "a") -> str:
    inner = f"""
  <polygon points="100,36 164,100 100,164 36,100"/>
  {_txt(100, 28, "B", size=12, italic=True)}
  {_txt(174, 104, "C", size=12, italic=True)}
  {_txt(100, 178, "D", size=12, italic=True)}
  {_txt(24, 104, "A", size=12, italic=True)}
  {_txt(70, 64, side, size=12, italic=True)}
"""
    return _svg_wrap(inner, "Ромб")


def svg_trapezoid_fig(a: str = "a", b: str = "b", h: str = "h") -> str:
    inner = f"""
  <polygon points="58,56 142,56 172,148 28,148"/>
  <line x1="58" y1="56" x2="58" y2="148" stroke-dasharray="4 3"/>
  {_txt(100, 48, a, size=12, italic=True)}
  {_txt(100, 164, b, size=12, italic=True)}
  {_txt(48, 108, h, size=12, italic=True)}
"""
    return _svg_wrap(inner, "Трапеция")


def _parse_intervals(text: str) -> list[dict[str, Any]]:
    # Русская запись промежутков: только «;» между концами ([a; b], (a; +∞)).
    # Запятая не подходит — иначе ловятся бытовые скобки вроде «(1 дюйм = 25,4 мм)».
    pattern = re.compile(
        r"([\[(])\s*"
        r"([-+]?(?:\d+(?:[.,]\d+)?|∞|inf)|[-−]?∞|\+∞)"
        r"\s*;\s*"
        r"([-+]?(?:\d+(?:[.,]\d+)?|∞|inf)|[-−]?∞|\+∞)"
        r"\s*([\])])",
        re.I,
    )
    found: list[dict[str, Any]] = []
    for m in pattern.finditer(text or ""):
        left_br, a_raw, b_raw, right_br = m.groups()

        def parse_end(raw: str) -> tuple[Optional[float], bool]:
            s = raw.replace("−", "-").replace(",", ".").strip().lower()
            if "∞" in raw or "inf" in s:
                return None, True
            try:
                return float(s), False
            except ValueError:
                return 0.0, False

        a, a_inf = parse_end(a_raw)
        b, b_inf = parse_end(b_raw)
        found.append(
            {
                "left_open": left_br == "(",
                "right_open": right_br == ")",
                "a": a,
                "b": b,
                "a_inf": a_inf,
                "b_inf": b_inf,
            }
        )
    return found


def _as_params(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _coerce_float(v: Any) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _sqrt_n_from_text(text: str) -> Optional[int]:
    blob = str(text or "")
    m = re.search(r"(?:√|sqrt\s*\(?|\\sqrt\{)\s*(\d+)", blob, flags=re.I)
    if not m:
        return None
    try:
        return int(m.group(1))
    except (TypeError, ValueError):
        return None


def _figure_for_sqrt_points(n: int) -> Optional[dict[str, Any]]:
    """A–D как в mutator sqrt_point: четыре корня вокруг √n."""
    for k in range(3, 20):
        cands = [k * k + 1, k * k + 5, (k + 1) * (k + 1) + 3, (k + 1) * (k + 1) + 8]
        if n not in cands:
            continue
        xs = [math.sqrt(c) for c in cands]
        return {
            "kind": "numberline",
            "min": float(k),
            "max": float(k + 2),
            "pad": 0.4,
            "points": [
                {"x": xs[0], "label": "A"},
                {"x": xs[1], "label": "B"},
                {"x": xs[2], "label": "C"},
                {"x": xs[3], "label": "D"},
            ],
        }
    return None


def _enrich_numberline_params(question: dict[str, Any], params: dict[str, Any], text: str) -> dict[str, Any]:
    """Восстановить точки/шкалу из mutator_values или √n в условии."""
    p = dict(params or {})
    payload = question.get("payload") if isinstance(question.get("payload"), dict) else {}
    values = payload.get("mutator_values") if isinstance(payload.get("mutator_values"), dict) else {}

    pts = p.get("points") if isinstance(p.get("points"), list) else []
    coerced: list[dict[str, Any]] = []
    for pt in pts:
        if not isinstance(pt, dict):
            continue
        xv = _coerce_float(pt.get("x"))
        if xv is None:
            raw = str(pt.get("x") or "").strip()
            m = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", raw)
            if m:
                xv = _coerce_float(values.get(m.group(1)))
        if xv is None:
            continue
        coerced.append({"x": xv, "label": str(pt.get("label") or "A")})
    if coerced:
        p["points"] = coerced
    else:
        rebuilt: list[dict[str, Any]] = []
        for lab, key in (("A", "x1"), ("B", "x2"), ("C", "x3"), ("D", "x4")):
            xv = _coerce_float(values.get(key))
            if xv is None:
                continue
            rebuilt.append({"x": xv, "label": lab})
        if len(rebuilt) >= 2:
            p["points"] = rebuilt
        else:
            n = _sqrt_n_from_text(text)
            built = _figure_for_sqrt_points(n) if n else None
            if built:
                p.update(built)
                return p

    if p.get("min") is not None:
        mv = _coerce_float(p.get("min"))
        if mv is not None:
            p["min"] = mv
        else:
            p.pop("min", None)
    if p.get("max") is not None:
        mv = _coerce_float(p.get("max"))
        if mv is not None:
            p["max"] = mv
        else:
            p.pop("max", None)
    if p.get("min") is None and values.get("k") is not None:
        kv = _coerce_float(values.get("k"))
        k2 = _coerce_float(values.get("k2"))
        if kv is not None:
            p["min"] = kv
            p["max"] = k2 if k2 is not None else kv + 2.0
    if p.get("min") is None and values.get("a") is not None and values.get("b") is not None:
        av = _coerce_float(values.get("a"))
        bv = _coerce_float(values.get("b"))
        if av is not None and bv is not None:
            p["min"] = av
            p["max"] = bv
            ans = _coerce_float(values.get("answer"))
            if ans is not None and not p.get("points"):
                p["points"] = [{"x": ans, "label": "x"}]
    return p


def _fmt_tick(t: float) -> str:
    return str(int(t)) if float(t).is_integer() else str(t).replace(".", ",")


def svg_numberline(text: str = "", params: Optional[dict[str, Any]] = None) -> str:
    """Числовая прямая как в КИМ: ровная ось, засечки, ●/○. Без фейк-интервала."""
    p = params or {}
    vw, vh = 320.0, 108.0
    x0, x1 = 36.0, 286.0
    y = 50.0

    points_raw = p.get("points") or []
    marked: list[tuple[float, str]] = []
    for pt in points_raw:
        if isinstance(pt, dict) and pt.get("x") is not None:
            xv = _coerce_float(pt.get("x"))
            if xv is None:
                continue
            marked.append((xv, str(pt.get("label") or "A")))

    intervals: list[dict[str, Any]] = []
    for raw in p.get("intervals") or []:
        if not isinstance(raw, dict):
            continue
        a = raw.get("a")
        b = raw.get("b")
        intervals.append(
            {
                "left_open": bool(raw.get("left_open", False)),
                "right_open": bool(raw.get("right_open", False)),
                "a": float(a) if a is not None and a not in ("-inf", "-∞", None) else None,
                "b": float(b) if b is not None and b not in ("inf", "+inf", "∞", None) else None,
                "a_inf": a in ("-inf", "-∞") or a is None and raw.get("a_inf"),
                "b_inf": b in ("inf", "+inf", "∞") or b is None and raw.get("b_inf"),
            }
        )
    # Скобки из текста — только если нет точек/интервалов в params (неравенство ≠ [a; b]).
    if not marked and not intervals:
        intervals = _parse_intervals(text)

    finite: list[float] = []
    for it in intervals:
        if not it["a_inf"] and it["a"] is not None:
            finite.append(float(it["a"]))
        if not it["b_inf"] and it["b"] is not None:
            finite.append(float(it["b"]))
    for x, _ in marked:
        finite.append(x)

    if p.get("min") is not None:
        mv = _coerce_float(p.get("min"))
        if mv is not None:
            finite.append(mv)
    if p.get("max") is not None:
        mv = _coerce_float(p.get("max"))
        if mv is not None:
            finite.append(mv)

    if not finite:
        blob = str(text or "").lower()
        if any(k in blob for k in ("точк", "√", "sqrt", "неравенств", "координатн")):
            return ""
        finite = [-2.0, 3.0]

    pad = float(p.get("pad", 0.8))
    data_lo, data_hi = min(finite), max(finite)
    if data_hi <= data_lo:
        data_hi = data_lo + 1.0
    lo = data_lo - pad
    hi = data_hi + pad
    if hi <= lo:
        hi = lo + 4

    span = hi - lo

    def x_of(v: Optional[float], *, inf_left: bool = False, inf_right: bool = False) -> float:
        if inf_left:
            return x0
        if inf_right:
            return x1
        assert v is not None
        return x0 + (float(v) - lo) / span * (x1 - x0)

    parts = [
        f'<line x1="{x0 - 8}" y1="{y}" x2="{x1 + 6}" y2="{y}"/>',
        f'<polyline points="{x1},{y - 4} {x1 + 10},{y} {x1},{y + 4}"/>',
        _txt(x1 + 14, y - 6, "x", anchor="start", size=13),
    ]

    # целочисленные засечки; при широком диапазоне — реже
    step = 1
    if span > 16:
        step = 2
    if span > 28:
        step = 5
    tick_set: set[float] = set()
    start_i = int(math.ceil(lo - 1e-9))
    end_i = int(math.floor(hi + 1e-9))
    for i in range(start_i, end_i + 1):
        if i % step == 0:
            tick_set.add(float(i))
    # ключевые концы интервалов — всегда
    for it in intervals:
        if not it["a_inf"] and it["a"] is not None and float(it["a"]).is_integer():
            tick_set.add(float(it["a"]))
        if not it["b_inf"] and it["b"] is not None and float(it["b"]).is_integer():
            tick_set.add(float(it["b"]))
    for xv, _ in marked:
        if float(xv).is_integer():
            tick_set.add(float(xv))

    # координаты подписей засечек (внизу) — пропускаем близкие
    placed_tick_x: list[float] = []
    min_tick_gap = 18.0
    for t in sorted(tick_set):
        if t < lo - 0.05 or t > hi + 0.05:
            continue
        tx = x_of(t)
        if any(abs(tx - px) < min_tick_gap for px in placed_tick_x):
            parts.append(f'<line x1="{tx:.1f}" y1="{y - 4}" x2="{tx:.1f}" y2="{y + 4}"/>')
            continue
        placed_tick_x.append(tx)
        parts.append(f'<line x1="{tx:.1f}" y1="{y - 5}" x2="{tx:.1f}" y2="{y + 5}"/>')
        parts.append(_txt(tx, y + 20, _fmt_tick(t), size=12))

    # интервал — полоса НАД осью, ось не утолщаем (иначе «кривая» прямая)
    for it in intervals[:3]:
        xa = x_of(it["a"], inf_left=bool(it["a_inf"]))
        xb = x_of(it["b"], inf_right=bool(it["b_inf"]))
        if xb < xa:
            xa, xb = xb, xa
        bar_y = y - 12
        parts.append(
            f'<line x1="{xa:.1f}" y1="{bar_y}" x2="{xb:.1f}" y2="{bar_y}" stroke-width="2.2"/>'
        )
        ends = []
        if not it["a_inf"]:
            ends.append((xa, it["left_open"]))
        if not it["b_inf"]:
            ends.append((xb, it["right_open"]))
        for x, open_end in ends:
            if open_end:
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="{BG}" stroke="{STROKE}" stroke-width="1.3"/>'
                )
            else:
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="{FILL_DOT}" stroke="{STROKE}" stroke-width="1.1"/>'
                )

    # точки: чередуем подписи сверху/снизу; при тесноте — два ряда сверху
    marked_sorted = sorted(marked[:8], key=lambda t: t[0])
    label_slots: list[tuple[float, str, str]] = []  # x, lab, side above|below|above2
    for i, (xv, lab) in enumerate(marked_sorted):
        tx = x_of(xv)
        side = "above" if i % 2 == 0 else "below"
        if i > 0:
            prev_x = x_of(marked_sorted[i - 1][0])
            if abs(tx - prev_x) < 22:
                side = "above2" if label_slots[-1][2] != "above2" else "below"
        label_slots.append((tx, lab, side))

    for tx, lab, side in label_slots:
        parts.append(
            f'<circle cx="{tx:.1f}" cy="{y}" r="4" fill="{FILL_DOT}" stroke="{STROKE}" stroke-width="1.1"/>'
        )
        short = lab if len(lab) <= 14 else lab[:12] + "…"
        if side == "above":
            parts.append(_txt(tx, y - 14, short, size=13))
        elif side == "above2":
            parts.append(_txt(tx, y - 28, short, size=12))
        else:
            parts.append(_txt(tx, y + 36, short, size=13))

    caption = str(p.get("label") or "")
    if caption:
        parts.append(_txt(vw / 2, vh - 10, caption[:48], size=11))
    return _svg_wrap("\n".join(parts), "Числовая прямая", width=vw, height=vh, extra_class="geo-fig-line")


def svg_plan(params: Optional[dict[str, Any]] = None) -> Optional[str]:
    """План на клетчатой сетке (ФИПИ): клетки 1×1, легенда масштаба, номера помещений."""
    p = params or {}
    rooms = p.get("rooms") or []
    if not isinstance(rooms, list) or not rooms:
        return None

    max_x = float(p.get("width") or 10)
    max_y = float(p.get("height") or 8)
    for r in rooms:
        if not isinstance(r, dict):
            continue
        try:
            max_x = max(max_x, float(r.get("x", 0)) + float(r.get("w", 1)))
            max_y = max(max_y, float(r.get("y", 0)) + float(r.get("h", 1)))
        except (TypeError, ValueError):
            continue
    # целые клетки для подсчёта
    max_x = max(1.0, math.ceil(max_x - 1e-9))
    max_y = max(1.0, math.ceil(max_y - 1e-9))

    vw, vh = 380.0, 330.0
    left_pad, top_pad = 14.0, 10.0
    right_pad, bottom_pad = 14.0, 32.0
    usable_w = vw - left_pad - right_pad
    usable_h = vh - top_pad - bottom_pad
    # квадратные клетки
    cell = min(usable_w / max_x, usable_h / max_y)
    grid_w, grid_h = cell * max_x, cell * max_y
    ox = left_pad + (usable_w - grid_w) / 2
    oy = top_pad + (usable_h - grid_h) / 2

    def sx(x: float) -> float:
        return ox + x * cell

    def sy(y: float) -> float:
        return oy + y * cell

    parts: list[str] = []
    # сетка каждые 1 клетку
    for i in range(int(max_x) + 1):
        x = sx(i)
        parts.append(
            f'<line x1="{x:.1f}" y1="{oy:.1f}" x2="{x:.1f}" y2="{oy + grid_h:.1f}" '
            f'stroke="{GRID_STROKE}" stroke-width="0.7"/>'
        )
    for j in range(int(max_y) + 1):
        y = sy(j)
        parts.append(
            f'<line x1="{ox:.1f}" y1="{y:.1f}" x2="{ox + grid_w:.1f}" y2="{y:.1f}" '
            f'stroke="{GRID_STROKE}" stroke-width="0.7"/>'
        )
    # внешняя рамка
    parts.append(
        f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{grid_w:.1f}" height="{grid_h:.1f}" '
        f'fill="none" stroke="{STROKE}" stroke-width="1.6"/>'
    )

    # дорожки / плитка
    for path in p.get("paths") or []:
        if not isinstance(path, dict):
            continue
        try:
            x, y = float(path.get("x", 0)), float(path.get("y", 0))
            w, h = float(path.get("w", 1)), float(path.get("h", 1))
        except (TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        parts.append(
            f'<rect x="{sx(x):.1f}" y="{sy(y):.1f}" width="{w * cell:.1f}" height="{h * cell:.1f}" '
            f'fill="#eeeeee" stroke="{STROKE}" stroke-width="0.7"/>'
        )

    for r in rooms:
        if not isinstance(r, dict):
            continue
        try:
            x, y = float(r.get("x", 0)), float(r.get("y", 0))
            w, h = float(r.get("w", 1)), float(r.get("h", 1))
        except (TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        rid = str(r.get("id") or "").strip()
        rx, ry, rw, rh = sx(x), sy(y), w * cell, h * cell
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'fill="{BG}" stroke="{STROKE}" stroke-width="1.45"/>'
        )
        cx, cy = rx + rw / 2, ry + rh / 2
        # на бланке ФИПИ на плане только цифры, без подписей «кухня»
        mark = rid or str(r.get("label") or "").strip()
        if mark:
            parts.append(_txt(cx, cy + 6, mark[:4], size=17))

    def _opening(op: dict[str, Any], *, kind: str) -> None:
        try:
            x, y = float(op.get("x", 0)), float(op.get("y", 0))
            w, h = float(op.get("w", 0.8)), float(op.get("h", 0.2))
        except (TypeError, ValueError):
            return
        if w <= 0 or h <= 0:
            return
        rx, ry, rw, rh = sx(x), sy(y), w * cell, h * cell
        if kind == "door":
            parts.append(
                f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
                f'fill="{BG}" stroke="{BG}" stroke-width="1.2"/>'
            )
            swing = str(op.get("swing") or "in").lower()
            if rw >= rh:
                rad = max(rw, 8.0)
                if swing in {"s", "down", "in"}:
                    parts.append(
                        f'<path d="M {rx:.1f} {ry:.1f} A {rad:.1f} {rad:.1f} 0 0 1 '
                        f'{rx:.1f} {ry + rad:.1f}" fill="none" stroke-width="1.05"/>'
                    )
                    parts.append(
                        f'<line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx:.1f}" y2="{ry + rad:.1f}"/>'
                    )
                else:
                    parts.append(
                        f'<path d="M {rx:.1f} {ry + rh:.1f} A {rad:.1f} {rad:.1f} 0 0 0 '
                        f'{rx:.1f} {ry + rh - rad:.1f}" fill="none" stroke-width="1.05"/>'
                    )
                    parts.append(
                        f'<line x1="{rx:.1f}" y1="{ry + rh:.1f}" '
                        f'x2="{rx:.1f}" y2="{ry + rh - rad:.1f}"/>'
                    )
            else:
                rad = max(rh, 8.0)
                if swing in {"e", "right", "in"}:
                    parts.append(
                        f'<path d="M {rx:.1f} {ry:.1f} A {rad:.1f} {rad:.1f} 0 0 1 '
                        f'{rx + rad:.1f} {ry:.1f}" fill="none" stroke-width="1.05"/>'
                    )
                    parts.append(
                        f'<line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx + rad:.1f}" y2="{ry:.1f}"/>'
                    )
                else:
                    parts.append(
                        f'<path d="M {rx + rw:.1f} {ry:.1f} A {rad:.1f} {rad:.1f} 0 0 0 '
                        f'{rx + rw - rad:.1f} {ry:.1f}" fill="none" stroke-width="1.05"/>'
                    )
                    parts.append(
                        f'<line x1="{rx + rw:.1f}" y1="{ry:.1f}" '
                        f'x2="{rx + rw - rad:.1f}" y2="{ry:.1f}"/>'
                    )
        else:
            parts.append(
                f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
                f'fill="{BG}" stroke="{BG}" stroke-width="1"/>'
            )
            if rw >= rh:
                for t in (0.3, 0.7):
                    yy = ry + rh * t
                    parts.append(
                        f'<line x1="{rx:.1f}" y1="{yy:.1f}" x2="{rx + rw:.1f}" y2="{yy:.1f}" '
                        f'stroke-width="0.9"/>'
                    )
            else:
                for t in (0.3, 0.7):
                    xx = rx + rw * t
                    parts.append(
                        f'<line x1="{xx:.1f}" y1="{ry:.1f}" x2="{xx:.1f}" y2="{ry + rh:.1f}" '
                        f'stroke-width="0.9"/>'
                    )

    for op in p.get("doors") or []:
        if isinstance(op, dict):
            _opening(op, kind="door")
    for op in p.get("windows") or []:
        if isinstance(op, dict):
            _opening(op, kind="window")

    gate = p.get("gate")
    if isinstance(gate, dict):
        side = str(gate.get("side") or "bottom").lower()
        at = float(gate.get("at") or max_x / 2)
        gw = float(gate.get("width") or max(1.0, max_x * 0.12))
        if side == "bottom":
            parts.append(
                f'<line x1="{sx(at - gw / 2):.1f}" y1="{sy(max_y):.1f}" '
                f'x2="{sx(at + gw / 2):.1f}" y2="{sy(max_y):.1f}" stroke-width="3.4"/>'
            )
            parts.append(_txt(sx(at), sy(max_y) + 14, "вход", size=10))
        elif side == "top":
            parts.append(
                f'<line x1="{sx(at - gw / 2):.1f}" y1="{sy(0):.1f}" '
                f'x2="{sx(at + gw / 2):.1f}" y2="{sy(0):.1f}" stroke-width="3.4"/>'
            )

    cell_m = p.get("cell_m")
    cm_s = ""
    if cell_m is not None:
        try:
            cm = float(cell_m)
            cm_s = str(int(cm)) if float(cm).is_integer() else str(cm).replace(".", ",")
        except (TypeError, ValueError):
            cm_s = ""
    # масштаб как в КИМ: одна клетка + подпись, без «легенды приложения»
    tick = min(cell, 16.0)
    lx, ly = ox, oy + grid_h + 10
    parts.append(
        f'<rect x="{lx:.1f}" y="{ly:.1f}" width="{tick:.1f}" height="{tick:.1f}" '
        f'fill="none" stroke="{STROKE}" stroke-width="1.1"/>'
    )
    cap = f"{cm_s} м" if cm_s else "1 клетка"
    parts.append(_txt(lx + tick + 8, ly + tick - 2, cap, anchor="start", size=11))
    return _svg_wrap("\n".join(parts), "План", width=vw, height=vh, extra_class="geo-fig-plan")


def svg_grid(params: Optional[dict[str, Any]] = None, text: str = "") -> Optional[str]:
    """Фигура на клетчатой бумаге: сетка + отрезки/многоугольники/точки."""
    p = params or {}
    cols = int(p.get("cols") or 8)
    rows = int(p.get("rows") or 8)
    cols = max(3, min(cols, 16))
    rows = max(3, min(rows, 16))

    margin = 16.0
    size = 184.0
    cw = size / cols
    ch = size / rows

    def gx(x: float) -> float:
        return margin + x * cw

    def gy(y: float) -> float:
        return margin + size - y * ch

    parts: list[str] = []
    for i in range(cols + 1):
        x = margin + i * cw
        parts.append(
            f'<line x1="{x:.1f}" y1="{margin}" x2="{x:.1f}" y2="{margin + size}" '
            f'stroke="{GRID_STROKE}" stroke-width="0.65"/>'
        )
    for j in range(rows + 1):
        y = margin + j * ch
        parts.append(
            f'<line x1="{margin}" y1="{y:.1f}" x2="{margin + size}" y2="{y:.1f}" '
            f'stroke="{GRID_STROKE}" stroke-width="0.65"/>'
        )
    parts.append(
        f'<rect x="{margin}" y="{margin}" width="{size}" height="{size}" '
        f'fill="none" stroke="{STROKE}" stroke-width="1.3"/>'
    )
    def _poly_pts(pts: list) -> str:
        out = []
        for pt in pts:
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                out.append(f"{gx(float(pt[0])):.1f},{gy(float(pt[1])):.1f}")
            elif isinstance(pt, dict) and "x" in pt and "y" in pt:
                out.append(f"{gx(float(pt['x'])):.1f},{gy(float(pt['y'])):.1f}")
        return " ".join(out)

    for poly in p.get("polygons") or []:
        if not isinstance(poly, list) or len(poly) < 2:
            continue
        pts = _poly_pts(poly)
        if pts:
            parts.append(f'<polygon points="{pts}" fill="none" stroke-width="1.4"/>')

    for line in p.get("lines") or []:
        if not isinstance(line, list) or len(line) < 2:
            continue
        pts = _poly_pts(line)
        if pts:
            parts.append(f'<polyline points="{pts}" fill="none" stroke-width="1.4"/>')

    angle = p.get("angle")
    if isinstance(angle, dict):
        try:
            vx, vy = float(angle["vertex"][0]), float(angle["vertex"][1])
            p1x, p1y = float(angle["p1"][0]), float(angle["p1"][1])
            p2x, p2y = float(angle["p2"][0]), float(angle["p2"][1])
            parts.append(
                f'<polyline points="{gx(p1x):.1f},{gy(p1y):.1f} '
                f'{gx(vx):.1f},{gy(vy):.1f} {gx(p2x):.1f},{gy(p2y):.1f}" '
                f'fill="none" stroke-width="1.5"/>'
            )
        except (KeyError, TypeError, ValueError, IndexError):
            pass

    for pt in p.get("points") or []:
        if not isinstance(pt, dict):
            continue
        try:
            x, y = float(pt["x"]), float(pt["y"])
        except (KeyError, TypeError, ValueError):
            continue
        parts.append(
            f'<circle cx="{gx(x):.1f}" cy="{gy(y):.1f}" r="2.6" fill="{FILL_DOT}" stroke="none"/>'
        )
        lab = str(pt.get("label") or "")
        if lab:
            parts.append(_txt(gx(x) + 6, gy(y) - 4, lab, anchor="start", size=11))

    # эвристика без params: угол 4×5 из текста «катет … 4 … 5»
    if not any(p.get(k) for k in ("polygons", "lines", "angle", "points")):
        nums = _nums_from_text(text)
        a, b = 3.0, 4.0
        if len(nums) >= 2:
            a, b = float(nums[0]), float(nums[1])
        a, b = max(1.0, min(a, cols - 1)), max(1.0, min(b, rows - 1))
        ox, oy = 1.0, 1.0
        parts.append(
            f'<polyline points="{gx(ox):.1f},{gy(oy + b):.1f} '
            f'{gx(ox):.1f},{gy(oy):.1f} {gx(ox + a):.1f},{gy(oy):.1f}" '
            f'fill="none" stroke-width="1.5"/>'
        )

    return _svg_wrap("\n".join(parts), "Клетчатая бумага", width=216, height=216)


def _polyline_from_fn(fn, x0: float, x1: float, n: int = 56) -> str:
    pts: list[str] = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        try:
            y = fn(x)
        except (ValueError, ZeroDivisionError, OverflowError):
            continue
        if y is None or not math.isfinite(y):
            continue
        sx = 100 + x * 18
        sy = 100 - y * 18
        if 12 <= sx <= 188 and 12 <= sy <= 188:
            pts.append(f"{sx:.1f},{sy:.1f}")
    if len(pts) < 2:
        return ""
    return f'<polyline points="{" ".join(pts)}" stroke-width="1.35"/>'


def _parse_linear(text: str) -> tuple[float, float]:
    """Достаёт k,b из y=kx+b; иначе (1,0). Не берёт «первые числа из задачи»."""
    m = re.search(
        r"y\s*=\s*([-+]?\d+(?:[.,]\d+)?)\s*\*?\s*x\s*([-+]\s*\d+(?:[.,]\d+)?)?",
        text or "",
        re.I,
    )
    if m:
        k = float(m.group(1).replace(",", "."))
        b = float(re.sub(r"\s+", "", m.group(2) or "0").replace(",", ".")) if m.group(2) else 0.0
        return max(min(k, 3), -3), max(min(b, 3), -3)
    m = re.search(r"y\s*=\s*([-+]?)\s*x\s*([-+]\s*\d+(?:[.,]\d+)?)?", text or "", re.I)
    if m:
        k = -1.0 if m.group(1) == "-" else 1.0
        b = float(re.sub(r"\s+", "", m.group(2) or "0").replace(",", ".")) if m.group(2) else 0.0
        return k, max(min(b, 3), -3)
    return 1.0, 0.0


def svg_graph_linear(text: str = "") -> str:
    k, b = _parse_linear(text)
    curve = _polyline_from_fn(lambda x: k * x + b, -4.2, 4.2)
    if b == 0:
        label = f"y = {k:g}x"
    elif b > 0:
        label = f"y = {k:g}x + {b:g}"
    else:
        label = f"y = {k:g}x − {abs(b):g}"
    inner = _axes() + curve + _txt(100, 188, label, size=12)
    return _svg_wrap(inner, "График прямой")


def svg_graph_parabola(text: str = "") -> str:
    blob = (text or "").lower()
    down = bool(re.search(r"−\s*x\s*\^?\s*2|-\s*x\s*\^?\s*2|ветв[иь].*вниз", blob))
    a = -0.32 if down else 0.32
    curve = _polyline_from_fn(lambda x: a * x**2, -4.2, 4.2, n=60)
    label = "y = −x²" if down else "y = x²"
    if re.search(r"ax\^?2|квадратич", blob):
        label = "y = ax² + bx + c"
    inner = _axes() + curve + _txt(100, 188, label, size=12)
    return _svg_wrap(inner, "График параболы")


def svg_graph_hyperbola(_text: str = "") -> str:
    k = 1.15
    left = _polyline_from_fn(lambda x: k / x, -4.2, -0.4, n=40)
    right = _polyline_from_fn(lambda x: k / x, 0.4, 4.2, n=40)
    asympt = """
  <line x1="100" y1="24" x2="100" y2="176" stroke-dasharray="2 2"/>
  <line x1="24" y1="100" x2="186" y2="100" stroke-dasharray="2 2"/>
"""
    inner = _axes() + asympt + left + right + _txt(100, 188, "y = k/x", size=12)
    return _svg_wrap(inner, "График гиперболы")


def svg_graph_cubic(_text: str = "") -> str:
    curve = _polyline_from_fn(lambda x: 0.11 * x**3, -4.0, 4.0, n=60)
    inner = _axes() + curve + _txt(100, 188, "y = x³", size=12)
    return _svg_wrap(inner, "График кубической функции")


def _mini_fn_polyline(
    cx: float,
    cy: float,
    scale: float,
    fn,
    x0: float,
    x1: float,
    n: int = 48,
    *,
    skip_near_zero: bool = False,
    max_dx: float = 52.0,
    max_dy: float = 48.0,
) -> str:
    chunks: list[str] = []
    pts: list[str] = []

    def flush() -> None:
        if len(pts) >= 2:
            chunks.append(
                f'<polyline points="{" ".join(pts)}" fill="none" stroke-width="1.45"/>'
            )
        pts.clear()

    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        if skip_near_zero and abs(x) < 0.38:
            flush()
            continue
        try:
            y = fn(x)
        except (ValueError, ZeroDivisionError, OverflowError):
            flush()
            continue
        if y is None or not math.isfinite(y):
            flush()
            continue
        sx = cx + x * scale
        sy = cy - y * scale
        if abs(sx - cx) > max_dx or abs(sy - cy) > max_dy:
            flush()
            continue
        pts.append(f"{sx:.1f},{sy:.1f}")
    flush()
    return "".join(chunks)


def _match_axes(cx: float, cy: float, half: float = 50.0) -> str:
    return (
        f'<line x1="{cx - half:.1f}" y1="{cy:.1f}" x2="{cx + half:.1f}" y2="{cy:.1f}"/>'
        f'<line x1="{cx:.1f}" y1="{cy + half:.1f}" x2="{cx:.1f}" y2="{cy - half:.1f}"/>'
        f'<polyline points="{cx + half - 6:.1f},{cy - 3.2:.1f} {cx + half:.1f},{cy:.1f} '
        f'{cx + half - 6:.1f},{cy + 3.2:.1f}" fill="none"/>'
        f'<polyline points="{cx - 3.2:.1f},{cy - half + 6:.1f} {cx:.1f},{cy - half:.1f} '
        f'{cx + 3.2:.1f},{cy - half + 6:.1f}" fill="none"/>'
        + _txt(cx + half - 2, cy + 14, "x", size=10)
        + _txt(cx + 10, cy - half + 8, "y", size=10)
    )


def _match_curve(kind: str, cx: float, cy: float, scale: float, a: float, b: float, k: float) -> str:
    name = kind.replace(" ", "_").replace("-", "_")
    aa = 0.16 * max(a, 1.0)
    kk = 1.15 * (1.0 + 0.12 * max(abs(k) - 1.0, 0.0))
    intercept = 0.32 * max(b, 1.0)
    if name in {"parabola", "parabola_up", "x2"}:
        return _mini_fn_polyline(cx, cy, scale, lambda x, c=aa: c * x * x, -3.4, 3.4)
    if name in {"parabola_down", "parabola_neg"}:
        return _mini_fn_polyline(cx, cy, scale, lambda x, c=aa: -c * x * x, -3.4, 3.4)
    if name in {"parabola_shift", "parabola_right", "shifted"}:
        return _mini_fn_polyline(
            cx, cy, scale, lambda x, c=aa: c * (x - 1.15) * (x - 1.15) - 0.35, -3.4, 3.4
        )
    if name in {"line_horiz", "horizontal", "const"}:
        return _mini_fn_polyline(
            cx, cy, scale, lambda x, h=intercept: h * 0.55, -3.4, 3.4
        )
    if name in {"hyperbola_neg", "-k/x", "neg_hyperbola"}:
        left = _mini_fn_polyline(
            cx, cy, scale, lambda x, c=kk: -c / x, -3.4, -0.42, skip_near_zero=True
        )
        right = _mini_fn_polyline(
            cx, cy, scale, lambda x, c=kk: -c / x, 0.42, 3.4, skip_near_zero=True
        )
        return left + right
    if name in {"hyperbola", "k/x", "hyperbola_pos"}:
        left = _mini_fn_polyline(
            cx, cy, scale, lambda x, c=kk: c / x, -3.4, -0.42, skip_near_zero=True
        )
        right = _mini_fn_polyline(
            cx, cy, scale, lambda x, c=kk: c / x, 0.42, 3.4, skip_near_zero=True
        )
        return left + right
    if name in {"line_up", "line_pos"}:
        return _mini_fn_polyline(
            cx, cy, scale, lambda x, h=intercept: 0.62 * x + h * 0.4, -3.4, 3.4
        )
    return _mini_fn_polyline(
        cx, cy, scale, lambda x, h=intercept: -0.62 * x + h, -3.4, 3.4
    )


def svg_graph_match(params: Optional[dict[str, Any]] = None, _text: str = "") -> str:
    """№11: три графика 1)–3). Состав задаёт params.graphs (смешанный / параболы / прямые)."""
    p = params or {}
    raw = p.get("graphs")
    if isinstance(raw, list) and raw:
        kinds = [str(x).strip().lower() for x in raw[:3]]
    else:
        kinds = ["parabola", "hyperbola", "line_down"]
    while len(kinds) < 3:
        kinds.append("parabola")

    def _coef(key: str, default: float) -> float:
        try:
            return float(p.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    a, b, k = _coef("a", 1.0), _coef("b", 2.0), _coef("k", 2.0)
    origins = (78.0, 230.0, 382.0)
    cy, scale, half = 86.0, 14.5, 52.0
    panels = []
    for i, kind in enumerate(kinds):
        cx = origins[i]
        box = (
            f'<rect x="{cx - half - 6:.1f}" y="{cy - half - 6:.1f}" '
            f'width="{(half + 6) * 2:.1f}" height="{(half + 6) * 2:.1f}" '
            f'fill="none" stroke="{STROKE}" stroke-width="0.85"/>'
        )
        curve = _match_curve(kind, cx, cy, scale, a, b, k)
        lab = _txt(cx, cy + half + 22, f"{i + 1})", size=13)
        panels.append(box + _match_axes(cx, cy, half) + curve + lab)
    inner = "".join(panels)
    return _svg_wrap(inner, "Соответствие графиков", width=460, height=176, extra_class="geo-fig-match")


def _tire_tread_arc(cx: float, cy: float, r: float, start_deg: float, end_deg: float, teeth: int = 18) -> str:
    """Зубцы протектора по дуге."""
    parts: list[str] = []
    span = end_deg - start_deg
    for i in range(teeth):
        a0 = math.radians(start_deg + span * i / teeth)
        a1 = math.radians(start_deg + span * (i + 0.5) / teeth)
        a2 = math.radians(start_deg + span * (i + 1) / teeth)
        x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
        xt, yt = cx + (r + 7) * math.cos(a1), cy - (r + 7) * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy - r * math.sin(a2)
        parts.append(
            f'<path d="M{x0:.1f} {y0:.1f} L{xt:.1f} {yt:.1f} L{x2:.1f} {y2:.1f}" '
            f'fill="#111" stroke="#111" stroke-width="0.8"/>'
        )
    return "".join(parts)


def _scissors(x: float, y: float) -> str:
    return f"""
  <g transform="translate({x:.1f} {y:.1f})">
    <circle cx="-4" cy="-3" r="2.2" fill="none" stroke="#b42318"/>
    <circle cx="-4" cy="3" r="2.2" fill="none" stroke="#b42318"/>
    <line x1="-2" y1="-2" x2="7" y2="0" stroke="#b42318" stroke-width="1.2"/>
    <line x1="-2" y1="2" x2="7" y2="0" stroke="#b42318" stroke-width="1.2"/>
  </g>
"""


def _horse_icon(x: float, y: float) -> str:
    return f"""
  <g transform="translate({x:.1f} {y:.1f})" fill="#111" stroke="#111" stroke-width="0.7">
    <path d="M2 14 L4 8 L7 8 L8 4 L12 3 L13 6 L11 8 L14 9 L16 14 L13 14 L12 11 L8 11 L7 14 Z"/>
    <circle cx="12.4" cy="4.2" r="0.7" fill="#fff" stroke="none"/>
  </g>
"""


def _flame_icon(x: float, y: float) -> str:
    return (
        f'<path d="M{x:.1f} {y + 8:.1f} C{x - 6:.1f} {y + 2:.1f} {x - 3:.1f} {y - 4:.1f} '
        f'{x:.1f} {y - 8:.1f} C{x + 1:.1f} {y - 1:.1f} {x + 6:.1f} {y + 1:.1f} {x:.1f} {y + 8:.1f} Z" '
        f'fill="#fff" stroke="#fff" stroke-width="0.6"/>'
    )


def _scheme_tire(params: dict[str, Any]) -> str:
    """Рис. 1 — боковина с маркировкой; рис. 2 — сечение B/H/d/D и диск."""
    bv = params.get("base_vars") if isinstance(params.get("base_vars"), dict) else {}
    marking = str(bv.get("marking") or params.get("marking") or "195/65 R15")
    cx1, cy1, r_out, r_in = 118.0, 128.0, 92.0, 38.0
    tread = _tire_tread_arc(cx1, cy1, r_out - 1, 8, 172, teeth=16)
    fig1 = f"""
  <path d="M{cx1 - r_out:.1f} {cy1:.1f} A{r_out:.1f} {r_out:.1f} 0 0 1 {cx1 + r_out:.1f} {cy1:.1f}
           L{cx1 + r_in:.1f} {cy1:.1f} A{r_in:.1f} {r_in:.1f} 0 0 0 {cx1 - r_in:.1f} {cy1:.1f} Z"
        fill="#111" stroke="#111"/>
  {tread}
  <path d="M{cx1 - r_in:.1f} {cy1:.1f} A{r_in:.1f} {r_in:.1f} 0 0 1 {cx1 + r_in:.1f} {cy1:.1f}"
        fill="none" stroke="#fff" stroke-width="1.4"/>
  {_txt(cx1, cy1 - 42, marking, size=14, fill="#fff", weight="bold")}
  {_txt(cx1, 210, "Рис. 1", size=12)}
"""
    cx, cy = 292.0, 108.0
    rx, ry = 34.0, 78.0
    rx_h, ry_h = 18.0, 44.0
    fig2 = f"""
  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#111" stroke="#111"/>
  <ellipse cx="{cx}" cy="{cy}" rx="{rx - 7}" ry="{ry - 10}" fill="#2a2a2a" stroke="#444"/>
  <ellipse cx="{cx}" cy="{cy}" rx="{rx_h}" ry="{ry_h}" fill="#fff" stroke="#111"/>
  <ellipse cx="{cx}" cy="{cy}" rx="8" ry="20" fill="#d0d0d0" stroke="#111"/>
  {_dim_v(cx - rx - 22, cy - ry, cy + ry, "D")}
  {_dim_v(cx - rx_h - 6, cy - ry_h, cy + ry_h, "d")}
  {_dim_h(cx - rx, cx + rx, cy + ry + 18, "B")}
  <line x1="{cx + rx + 10:.1f}" y1="{cy - ry:.1f}" x2="{cx + rx + 10:.1f}" y2="{cy - ry_h:.1f}"/>
  <line x1="{cx + rx + 6:.1f}" y1="{cy - ry:.1f}" x2="{cx + rx + 14:.1f}" y2="{cy - ry:.1f}"/>
  <line x1="{cx + rx + 6:.1f}" y1="{cy - ry_h:.1f}" x2="{cx + rx + 14:.1f}" y2="{cy - ry_h:.1f}"/>
  {_txt(cx + rx + 22, cy - (ry + ry_h) / 2, "H", size=13, italic=True)}
  <line x1="{cx + rx + 10:.1f}" y1="{cy + ry_h:.1f}" x2="{cx + rx + 10:.1f}" y2="{cy + ry:.1f}"/>
  <line x1="{cx + rx + 6:.1f}" y1="{cy + ry:.1f}" x2="{cx + rx + 14:.1f}" y2="{cy + ry:.1f}"/>
  <line x1="{cx + rx + 6:.1f}" y1="{cy + ry_h:.1f}" x2="{cx + rx + 14:.1f}" y2="{cy + ry_h:.1f}"/>
  {_txt(cx + rx + 22, cy + (ry + ry_h) / 2 + 4, "H", size=13, italic=True)}
"""
    rim_x, rim_y = 400.0, 108.0
    rim = f"""
  <ellipse cx="{rim_x + 6:.1f}" cy="{rim_y}" rx="20" ry="36" fill="#cfcfcf" stroke="#111"/>
  <ellipse cx="{rim_x}" cy="{rim_y}" rx="20" ry="36" fill="#e8e8e8" stroke="#111"/>
  <ellipse cx="{rim_x}" cy="{rim_y}" rx="11" ry="20" fill="#fff" stroke="#111"/>
  <ellipse cx="{rim_x}" cy="{rim_y}" rx="4" ry="8" fill="#bbb" stroke="#111"/>
  <line x1="{cx + 8:.1f}" y1="{cy - 20:.1f}" x2="{rim_x - 11:.1f}" y2="{rim_y - 20:.1f}" stroke-dasharray="3 2"/>
  <line x1="{cx + 8:.1f}" y1="{cy + 20:.1f}" x2="{rim_x - 11:.1f}" y2="{rim_y + 20:.1f}" stroke-dasharray="3 2"/>
  {_txt(348, 210, "Рис. 2", size=12)}
"""
    split = '<line x1="228" y1="16" x2="228" y2="216" stroke="#bbb"/>'
    inner = split + fig1 + fig2 + rim
    return _svg_wrap(inner, "Маркировка шины", width=460, height=228, extra_class="geo-fig-scheme")


def _scheme_paper(params: dict[str, Any]) -> str:
    """A0 → A1 / A2 / A3 пунктиром, ножницы у резов."""
    x, y, w, h = 28.0, 22.0, 220.0, 156.0
    mid_x = x + w / 2
    mid_y = y + h / 2
    q_x = x + w / 4
    inner = f"""
  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width="1.6"/>
  <line x1="{mid_x:.1f}" y1="{y}" x2="{mid_x:.1f}" y2="{y + h}" stroke-dasharray="6 3"/>
  <line x1="{x}" y1="{mid_y:.1f}" x2="{mid_x:.1f}" y2="{mid_y:.1f}" stroke-dasharray="6 3"/>
  <line x1="{q_x:.1f}" y1="{y}" x2="{q_x:.1f}" y2="{mid_y:.1f}" stroke-dasharray="5 3"/>
  {_txt(x + 3 * w / 4, y + h / 2 + 5, "A1", size=16, weight="bold")}
  {_txt(x + w / 4, y + 3 * h / 4 + 5, "A2", size=15, weight="bold")}
  {_txt(x + 3 * w / 8, y + h / 4 + 4, "A3", size=14, weight="bold")}
  {_txt(x + w + 28, y + h / 2 + 4, "— A0", size=14, anchor="start")}
  {_scissors(mid_x, y - 10)}
  {_scissors(x - 12, mid_y)}
"""
    return _svg_wrap(inner, "Форматы бумаги", width=310, height=200, extra_class="geo-fig-scheme")


def _scheme_stove(params: dict[str, Any]) -> str:
    """Рис. 1 — объёмный набросок; рис. 2 — чертёж 40 / 50 / 64, топка, R — ?"""
    bv = params.get("base_vars") if isinstance(params.get("base_vars"), dict) else {}
    width_cm = float(bv.get("width") or params.get("width") or 40)
    side_cm = float(bv.get("side") or params.get("side") or 50)
    total_cm = float(bv.get("total") or params.get("total") or 64)
    fig1 = f"""
  <path d="M36 150 L36 88 Q36 70 58 66 L96 66 Q118 70 118 88 L118 150 Z" fill="#1a1a1a" stroke="#111"/>
  <path d="M118 88 L138 78 L138 138 L118 150 Z" fill="#3a3a3a" stroke="#111"/>
  <path d="M58 66 L78 58 L118 58 L138 78 L118 88 Q118 70 96 66 Z" fill="#2a2a2a" stroke="#111"/>
  <rect x="54" y="100" width="44" height="38" fill="#111" stroke="#888"/>
  <circle cx="62" cy="119" r="2.4" fill="#ddd" stroke="none"/>
  <rect x="70" y="72" width="22" height="8" fill="#bbb" stroke="#111"/>
  {_txt(77, 172, "Рис. 1", size=12)}
"""
    scale = 2.55
    w = width_cm * scale
    side_h = side_cm * scale
    total_h = total_cm * scale
    sag = max(8.0, total_h - side_h)
    left = 210.0
    right = left + w
    bottom = 188.0
    top_rect = bottom - side_h
    peak = bottom - total_h
    mid = (left + right) / 2
    r = (sag / 2.0) + (w * w) / (8.0 * sag) if sag else w / 2
    cy_arc = top_rect + (r - sag)
    fire_w, fire_h = w * 0.46, side_h * 0.38
    fx = mid - fire_w / 2
    fy = bottom - fire_h - 14
    cap_h = 16
    w_lab = str(int(width_cm)) if width_cm == int(width_cm) else f"{width_cm:g}"
    s_lab = str(int(side_cm)) if side_cm == int(side_cm) else f"{side_cm:g}"
    t_lab = str(int(total_cm)) if total_cm == int(total_cm) else f"{total_cm:g}"
    fig2 = f"""
  <path d="M{left:.1f} {bottom:.1f} L{left:.1f} {top_rect:.1f}
           A{r:.1f} {r:.1f} 0 0 1 {right:.1f} {top_rect:.1f}
           L{right:.1f} {bottom:.1f} Z" fill="#fff" stroke="#111" stroke-width="1.4"/>
  <rect x="{left:.1f}" y="{peak - cap_h:.1f}" width="{w:.1f}" height="{cap_h:.1f}" fill="#333" stroke="#111"/>
  {_flame_icon(mid, peak - cap_h / 2 - 1)}
  <rect x="{fx:.1f}" y="{fy:.1f}" width="{fire_w:.1f}" height="{fire_h:.1f}" fill="#c8c8c8" stroke="#111"/>
  <line x1="{mid + 8:.1f}" y1="{fy + fire_h / 2:.1f}" x2="{right + 36:.1f}" y2="{fy + fire_h / 2:.1f}"/>
  {_txt(right + 40, fy + fire_h / 2 + 4, "топка", size=12, anchor="start")}
  <line x1="{mid:.1f}" y1="{peak + 4:.1f}" x2="{mid + 48:.1f}" y2="{peak - 18:.1f}"/>
  {_txt(mid + 52, peak - 20, "кожух", size=12, anchor="start")}
  {_dim_h(left, right, bottom + 16, w_lab)}
  {_dim_v(left - 18, top_rect, bottom, s_lab)}
  {_dim_v(right + 16, peak, bottom, t_lab)}
  <line x1="{mid:.1f}" y1="{cy_arc:.1f}" x2="{mid:.1f}" y2="{peak:.1f}"/>
  <polygon points="{mid:.1f},{peak + 1:.1f} {mid - 3:.1f},{peak + 8:.1f} {mid + 3:.1f},{peak + 8:.1f}" fill="#111" stroke="none"/>
  <circle cx="{mid:.1f}" cy="{cy_arc:.1f}" r="2.4" fill="#111" stroke="none"/>
  {_txt(mid + 22, (cy_arc + peak) / 2 + 2, "R — ?", size=13, italic=True)}
  {_txt(mid, 214, "Рис. 2", size=12)}
"""
    inner = fig1 + fig2
    return _svg_wrap(inner, "Чертёж печи", width=430, height=232, extra_class="geo-fig-scheme")


def _map_pin(x: float, y: float, n: int) -> str:
    return (
        f'<path d="M{x:.1f} {y:.1f} C{x:.1f} {y - 16:.1f} {x - 9:.1f} {y - 22:.1f} '
        f'{x:.1f} {y - 22:.1f} C{x + 9:.1f} {y - 22:.1f} {x:.1f} {y - 16:.1f} {x:.1f} {y:.1f}" '
        f'fill="#111" stroke="#111"/>'
        + _txt(x, y - 14, str(n), size=10, fill="#fff", weight="bold")
    )


def _scheme_travel_map(params: dict[str, Any]) -> str:
    """План местности: шоссе Г, просёлок 3–5 / 2–6 / 1–7, река, мосты, пруд, конюшня."""
    hwy = """
  <line x1="48" y1="40" x2="368" y2="40" stroke-width="2.4"/>
  <line x1="48" y1="48" x2="368" y2="48" stroke-width="2.4"/>
  <line x1="48" y1="40" x2="48" y2="268" stroke-width="2.4"/>
  <line x1="56" y1="40" x2="56" y2="268" stroke-width="2.4"/>
"""
    pts = {
        4: (52, 44),
        3: (148, 44),
        2: (236, 44),
        1: (324, 44),
        5: (52, 118),
        6: (52, 186),
        7: (52, 250),
    }
    dirt = (
        f'<line x1="148" y1="44" x2="52" y2="118" stroke-dasharray="6 3.5" stroke-width="1.35"/>'
        f'<line x1="236" y1="44" x2="52" y2="186" stroke-dasharray="6 3.5" stroke-width="1.35"/>'
        f'<line x1="324" y1="44" x2="52" y2="250" stroke-dasharray="6 3.5" stroke-width="1.35"/>'
    )
    pins = "".join(_map_pin(x, y, n) for n, (x, y) in pts.items())
    river = """
  <path d="M20 278 C90 268 130 250 170 228 C230 196 280 168 330 70 C348 42 360 36 380 28"
        stroke-width="3.2" stroke="#111"/>
  <path d="M24 284 C94 274 134 256 174 234 C234 202 286 174 334 76"
        stroke-width="1.1" stroke="#111"/>
"""
    bridges = """
  <path d="M348 34 A7 7 0 0 1 348 54" stroke-width="1.5"/>
  <path d="M362 34 A7 7 0 0 0 362 54" stroke-width="1.5"/>
  <path d="M40 258 A8 8 0 0 0 64 258" stroke-width="1.5"/>
  <path d="M40 272 A8 8 0 0 1 64 272" stroke-width="1.5"/>
"""
    pond = (
        '<path d="M168 148 C186 136 214 138 228 152 C240 166 232 184 208 190 '
        'C184 196 158 178 162 160 Z" fill="#cfcfcf" stroke="#111"/>'
    )
    stable = _horse_icon(96, 68)
    legend = f"""
  <rect x="378" y="70" width="118" height="150" fill="#fff" stroke="#bbb"/>
  <line x1="388" y1="92" x2="418" y2="92" stroke-width="2.4"/>
  <line x1="388" y1="98" x2="418" y2="98" stroke-width="2.4"/>
  {_txt(424, 98, "шоссе", size=11, anchor="start")}
  <line x1="388" y1="118" x2="418" y2="118" stroke-dasharray="6 3"/>
  {_txt(424, 122, "просёлок", size=11, anchor="start")}
  <path d="M392 138 A6 6 0 0 1 392 150"/>
  <path d="M404 138 A6 6 0 0 0 404 150"/>
  {_txt(424, 148, "мост", size=11, anchor="start")}
  <path d="M388 168 Q398 162 408 168 Q418 174 428 166" stroke-width="2"/>
  {_txt(434, 172, "река", size=11, anchor="start")}
  <path d="M392 186 C398 182 408 182 412 188 C408 194 396 194 392 186 Z" fill="#cfcfcf" stroke="#111"/>
  {_txt(424, 192, "пруд", size=11, anchor="start")}
  {_horse_icon(386, 198)}
  {_txt(424, 214, "конюшня", size=11, anchor="start")}
"""
    inner = hwy + dirt + river + bridges + pond + stable + pins + legend
    return _svg_wrap(inner, "План местности", width=508, height=312, extra_class="geo-fig-scheme")


def _bracket_h(x1: float, x2: float, y: float, label: str, *, above: bool = True) -> str:
    """Размерная скобка над/под отрезком (l, m, n на сложенном зонте)."""
    if x2 < x1:
        x1, x2 = x2, x1
    tick = -9 if above else 9
    ly = y + tick - 3 if above else y + tick + 11
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y + tick:.1f}"/>'
        f'<line x1="{x2:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y + tick:.1f}"/>'
        + _txt((x1 + x2) / 2, ly, label, size=13, italic=True)
    )


def _scheme_umbrella(params: dict[str, Any]) -> str:
    """Три чертежа зонта: сложенный (рис. 3), купол сверху (рис. 1), дуга сечения."""
    del params
    # --- Рис. 3: сложенный зонт (чехол + ручка) ---
    x_tip, x_can, x_end, x_h = 52.0, 78.0, 268.0, 356.0
    y_u, cy = 48.0, 62.0
    folds = []
    for i, yy in enumerate((52.5, 56.5, 60.5, 64.5, 68.5, 71.5)):
        x2 = x_end - 6 - (i % 2) * 4
        folds.append(
            f'<path d="M{x_can + 10:.1f} {yy:.1f} C{x_can + 70:.1f} {yy - 1.2:.1f} '
            f'{x_end - 80:.1f} {yy + 1.0:.1f} {x2:.1f} {yy:.1f}" '
            f'fill="none" stroke="#3a3a3a" stroke-width="0.7"/>'
        )
    folded = f"""
  <path d="M{x_tip:.1f} {cy:.1f} L{x_can:.1f} {y_u + 2:.1f} L{x_can:.1f} {y_u + 26:.1f} Z"
        fill="#1a1a1a" stroke="#111"/>
  <path d="M{x_can:.1f} {y_u + 3:.1f}
           Q{x_can + 18:.1f} {y_u - 1:.1f} {x_can + 40:.1f} {y_u:.1f}
           L{x_end - 8:.1f} {y_u + 1:.1f}
           Q{x_end + 2:.1f} {cy:.1f} {x_end - 8:.1f} {y_u + 27:.1f}
           L{x_can + 40:.1f} {y_u + 28:.1f}
           Q{x_can + 18:.1f} {y_u + 29:.1f} {x_can:.1f} {y_u + 25:.1f} Z"
        fill="#2b2b2b" stroke="#111"/>
  {"".join(folds)}
  <ellipse cx="{x_end - 4:.1f}" cy="{cy:.1f}" rx="7" ry="12" fill="#222" stroke="#111"/>
  <line x1="{x_end + 2:.1f}" y1="{cy:.1f}" x2="{x_h - 16:.1f}" y2="{cy:.1f}" stroke-width="3.4"/>
  <path d="M{x_h - 16:.1f} {cy:.1f} C{x_h + 10:.1f} {cy:.1f} {x_h + 10:.1f} {cy + 28:.1f}
           {x_h - 10:.1f} {cy + 28:.1f}" fill="none" stroke-width="4.2" stroke-linecap="round"/>
  {_bracket_h(x_tip, x_end, y_u - 12, "m", above=True)}
  {_bracket_h(x_end, x_h, y_u - 12, "n", above=True)}
  {_txt((x_end + x_h) / 2, y_u - 32, "ручка зонта", size=11)}
  {_bracket_h(x_tip, x_h, y_u + 46, "l", above=False)}
  {_txt(210, 122, "Рис. 3", size=12)}
"""
    # --- Рис. 1: вид сверху (8 равных секторов) + один клин ---
    ocx, ocy, orad = 118.0, 214.0, 64.0
    sectors = []
    for i in range(8):
        a0 = math.radians(-90 + i * 45)
        a1 = math.radians(-90 + (i + 1) * 45)
        x0, y0 = ocx + orad * math.cos(a0), ocy + orad * math.sin(a0)
        x1, y1 = ocx + orad * math.cos(a1), ocy + orad * math.sin(a1)
        fill = "#ececec" if i % 2 else "#fff"
        sectors.append(
            f'<path d="M{ocx:.1f} {ocy:.1f} L{x0:.1f} {y0:.1f} L{x1:.1f} {y1:.1f} Z" '
            f'fill="{fill}" stroke="#111"/>'
        )
    ty = 146.0
    base_l, base_r, base_y = 256.0, 412.0, 274.0
    apex_x = (base_l + base_r) / 2
    h_label = (
        f'<text x="{apex_x + 16:.1f}" y="{(ty + base_y) / 2:.1f}" text-anchor="start" '
        f'fill="{STROKE}" stroke="none" font-size="14" font-style="italic" '
        f'font-family="{FONT}">h<tspan dy="5" font-size="10">Δ</tspan></text>'
    )
    tri = f"""
  {"".join(sectors)}
  <circle cx="{ocx:.1f}" cy="{ocy:.1f}" r="2.2" fill="#111" stroke="none"/>
  <path d="M{apex_x:.1f} {ty:.1f} L{base_l:.1f} {base_y:.1f} L{base_r:.1f} {base_y:.1f} Z"
        fill="#fff" stroke="#111" stroke-width="1.3"/>
  <line x1="{apex_x:.1f}" y1="{ty:.1f}" x2="{apex_x:.1f}" y2="{base_y:.1f}" stroke-dasharray="4 3"/>
  <polyline points="{apex_x - 5:.1f},{base_y:.1f} {apex_x - 5:.1f},{base_y - 5:.1f} {apex_x:.1f},{base_y - 5:.1f}"
            fill="none"/>
  {_txt(apex_x, base_y + 16, "a", size=14, italic=True)}
  {h_label}
  {_txt(210, 298, "Рис. 1", size=12)}
"""
    # --- сечение купола: дуга CD, центр O, высота CM = h, ширина d ---
    mx, chord_y, peak_y = 210.0, 428.0, 348.0
    h_seg = chord_y - peak_y
    d_half = 122.0
    r_len = (d_half * d_half + h_seg * h_seg) / (2.0 * h_seg)
    om = r_len - h_seg
    ox, oy = mx, chord_y + om
    left_x, right_x = mx - d_half, mx + d_half
    section = f"""
  <path d="M{left_x:.1f} {chord_y:.1f} A{r_len:.1f} {r_len:.1f} 0 0 1 {right_x:.1f} {chord_y:.1f}"
        fill="none" stroke="#111" stroke-width="1.45"/>
  <line x1="{left_x:.1f}" y1="{chord_y:.1f}" x2="{right_x:.1f}" y2="{chord_y:.1f}"/>
  <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{left_x:.1f}" y2="{chord_y:.1f}"/>
  <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{right_x:.1f}" y2="{chord_y:.1f}"/>
  <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{mx:.1f}" y2="{peak_y:.1f}"/>
  <circle cx="{ox:.1f}" cy="{oy:.1f}" r="2.3" fill="#111" stroke="none"/>
  <circle cx="{mx:.1f}" cy="{chord_y:.1f}" r="2.1" fill="#111" stroke="none"/>
  <circle cx="{mx:.1f}" cy="{peak_y:.1f}" r="2.1" fill="#111" stroke="none"/>
  <circle cx="{right_x:.1f}" cy="{chord_y:.1f}" r="2.1" fill="#111" stroke="none"/>
  {_txt(ox - 14, oy + 14, "O", size=13, italic=True)}
  {_txt(mx - 14, chord_y - 7, "M", size=13, italic=True)}
  {_txt(mx, peak_y - 11, "C", size=13, italic=True)}
  {_txt(right_x + 14, chord_y + 5, "D", size=13, italic=True)}
  {_txt((ox + left_x) / 2 - 12, (oy + chord_y) / 2 + 2, "R", size=13, italic=True)}
  {_txt((ox + right_x) / 2 + 14, (oy + chord_y) / 2 + 2, "R", size=13, italic=True)}
  {_txt(mx + 14, (peak_y + chord_y) / 2, "h", size=13, italic=True)}
  <line x1="{left_x:.1f}" y1="{chord_y:.1f}" x2="{left_x:.1f}" y2="{chord_y + 30:.1f}"/>
  <line x1="{right_x:.1f}" y1="{chord_y:.1f}" x2="{right_x:.1f}" y2="{chord_y + 30:.1f}"/>
  {_bracket_h(left_x, right_x, chord_y + 30, "d", above=False)}
"""
    inner = folded + tri + section
    return _svg_wrap(inner, "Чертежи зонта", width=440, height=510, extra_class="geo-fig-scheme")


def svg_scheme(params: Optional[dict[str, Any]] = None, text: str = "") -> str:
    """Схемы к сюжету 1–5 по скринам: шина, карта, печь, бумага."""
    p = params or {}
    theme = str(p.get("theme") or p.get("scheme") or "").strip().lower()
    blob = f"{theme} {text}".lower()
    if not theme:
        if any(k in blob for k in ("шин", "колес", "r15", "диск")):
            theme = "wheel"
        elif any(k in blob for k in ("бумаг", "a4", "a5", "лист")):
            theme = "paper"
        elif any(k in blob for k in ("печ", "бан")):
            theme = "stove"
        elif any(k in blob for k in ("шоссе", "просёл", "просел", "местност")):
            theme = "travel"
        elif any(k in blob for k in ("маршрут", "автобус", "остановок")):
            theme = "route"
        elif any(k in blob for k in ("топлив", "бензин", "поездк")):
            theme = "fuel"
        elif any(k in blob for k in ("тариф", "гигабайт", "абонент")):
            theme = "tariff"
        elif any(k in blob for k in ("зонт",)):
            theme = "umbrella"
        elif any(k in blob for k in ("вклад", "кредит", "банк")):
            theme = "deposit"
        else:
            theme = "table"

    if theme == "wheel":
        return _scheme_tire(p)
    if theme == "paper":
        return _scheme_paper(p)
    if theme == "stove":
        return _scheme_stove(p)
    if theme in {"travel", "route"}:
        return _scheme_travel_map(p)
    if theme == "fuel":
        inner = f"""
  <circle cx="36" cy="100" r="6" fill="{FILL_DOT}" stroke="none"/>
  <circle cx="100" cy="70" r="6" fill="{FILL_DOT}" stroke="none"/>
  <circle cx="164" cy="110" r="6" fill="{FILL_DOT}" stroke="none"/>
  <line x1="36" y1="100" x2="100" y2="70"/>
  <line x1="100" y1="70" x2="164" y2="110"/>
  {_txt(36, 124, "A", size=12)}
  {_txt(100, 56, "B", size=12)}
  {_txt(164, 134, "C", size=12)}
  {_txt(100, 178, "маршруты", size=11)}
"""
        return _svg_wrap(inner, "Схема маршрутов", extra_class="geo-fig-scheme")
    if theme == "tariff":
        months = ("Я", "Ф", "М", "А", "М", "И", "И", "А", "С", "О", "Н", "Д")
        mins = (220, 260, 310, 180, 240, 355, 200, 270, 340, 230, 170, 290)
        gbs = (1.4, 2.0, 3.6, 1.1, 2.4, 4.1, 1.7, 2.2, 3.1, 2.7, 1.2, 2.5)
        ox, oy, gw, gh = 40.0, 28.0, 280.0, 110.0
        parts = [
            f'<line x1="{ox}" y1="{oy + gh}" x2="{ox + gw}" y2="{oy + gh}"/>',
            f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy + gh}"/>',
        ]
        lim_y = oy + gh - (300 / 400.0) * gh
        parts.append(
            f'<line x1="{ox}" y1="{lim_y:.1f}" x2="{ox + gw}" y2="{lim_y:.1f}" '
            f'stroke-dasharray="4 3"/>'
        )
        min_pts = []
        gb_pts = []
        for i, (mv, gv) in enumerate(zip(mins, gbs)):
            x = ox + (i + 0.5) * (gw / 12)
            y_m = oy + gh - (mv / 400.0) * gh
            y_g = oy + gh - (gv / 5.0) * gh
            min_pts.append(f"{x:.1f},{y_m:.1f}")
            gb_pts.append(f"{x:.1f},{y_g:.1f}")
            parts.append(_txt(x, oy + gh + 14, months[i], size=9))
        parts.append(f'<polyline points="{" ".join(min_pts)}" stroke-width="1.35"/>')
        parts.append(
            f'<polyline points="{" ".join(gb_pts)}" stroke-width="1.2" stroke-dasharray="3 2"/>'
        )
        for pt in min_pts:
            x, y = pt.split(",")
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="2.1" fill="{FILL_DOT}" stroke="none"/>'
            )
        parts.append(_txt(ox - 6, oy + 10, "мин", size=9))
        parts.append(_txt(ox + gw + 4, oy + 10, "ГБ", size=9))
        inner = "\n".join(parts)
        return _svg_wrap(inner, "График тарифа", width=360, height=168, extra_class="geo-fig-scheme")
    if theme == "umbrella":
        return _scheme_umbrella(p)
    if theme == "deposit":
        inner = f"""
  <rect x="50" y="48" width="100" height="70"/>
  {_txt(100, 80, "%", size=22)}
  {_txt(100, 140, "банк", size=12)}
  {_txt(100, 168, "вклад / кредит", size=11)}
"""
        return _svg_wrap(inner, "Схема банка", extra_class="geo-fig-scheme")
    inner = f"""
  <rect x="40" y="50" width="120" height="80"/>
  <line x1="40" y1="78" x2="160" y2="78"/>
  <line x1="40" y1="106" x2="160" y2="106"/>
  {_txt(100, 22, "таблица", size=12)}
"""
    return _svg_wrap(inner, "Схема к таблице", extra_class="geo-fig-scheme")


def detect_figure_kind(text: str, topic: str = "", explicit: Optional[str] = None) -> Optional[str]:
    if explicit:
        kind = str(explicit).strip().lower()
        aliases = {
            "line": "graph_linear",
            "linear": "graph_linear",
            "parabola": "graph_parabola",
            "hyperbola": "graph_hyperbola",
            "cubic": "graph_cubic",
            "interval": "numberline",
            "intervals": "numberline",
            "numline": "numberline",
            "floorplan": "plan",
            "schema": "plan",
            "схема": "plan",
            "план": "plan",
            "scheme": "scheme",
            "схематич": "scheme",
            "graph_match": "graph_match",
            "graphs": "graph_match",
            "три графика": "graph_match",
            "клетк": "grid",
            "grid_paper": "grid",
        }
        kind = aliases.get(kind, kind)
        if kind in ALLOWED_KINDS:
            return kind

    blob = f"{topic} {text}".lower()

    if any(
        k in blob
        for k in (
            "соответствие между графиками",
            "установите соответствие между графиками",
            "графиками и формулами",
        )
    ):
        return "graph_match"

    if any(k in blob for k in ("клетчатой бумаг", "на клетчатой", "размер клетки")):
        return "grid"

    if any(k in blob for k in ("гипербол", "y = k/x", "y=k/x", "обратной пропорциональ")):
        return "graph_hyperbola"
    if any(k in blob for k in ("парабол", "квадратич")) or (
        "график" in blob and ("x²" in text or "x^2" in blob or "ax²" in text)
    ):
        return "graph_parabola"
    # не путать с «в кубических метрах»
    if any(
        k in blob
        for k in (
            "кубическая функция",
            "кубической функции",
            "y = x³",
            "y=x³",
            "y = x^3",
            "y=x^3",
        )
    ):
        return "graph_cubic"
    if "график" in blob and ("x³" in text or "x^3" in blob):
        return "graph_cubic"
    if any(k in blob for k in ("график прямой", "линейная функция", "угловой коэффициент", "y = kx")) or (
        "график" in blob and re.search(r"y\s*=\s*[-+]?\d*\s*x", blob)
    ):
        return "graph_linear"

    # Интервал только с «;» ([−2; 3), [a; +∞)) — не запятая из «(1 дюйм = 25,4 мм)».
    _bound = r"[-+]?(?:\d+(?:[.,]\d+)?|∞|inf)|[-−]?∞|\+∞"
    _interval_re = re.compile(
        rf"[\[(]\s*(?:{_bound})\s*;\s*(?:{_bound})\s*[\])]",
        re.I,
    )
    intervalish = any(
        k in blob
        for k in (
            "интервал",
            "промежуток",
            "числовой прям",
            "числовая прям",
            "координатной прям",
            "координатная прям",
            "изобразите на числовой",
            "отметьте на числовой",
            "неравенств",
        )
    ) or bool(_interval_re.search(blob))
    if intervalish and "график функц" not in blob and "парабол" not in blob:
        return "numberline"

    # ОД без явной просьбы «на прямой» — рисуем только если есть скобки интервала с «;»
    if "область определения" in blob and _interval_re.search(text or ""):
        return "numberline"

    if any(k in blob for k in ("параллелепипед", "коробк")):
        return "box3d"
    if any(k in blob for k in ("прямоугольный треугольник", "катет", "гипотенуз")):
        return "triangle"
    if "треугольник" in blob and any(k in blob for k in ("см", "сторона", "найдите", "площад", "угол")):
        return "triangle"
    if any(k in blob for k in ("круг", "окружност")) and any(
        k in blob for k in ("радиус", "хорда", "касательн", "центральн", "вписан")
    ):
        return "circle"
    if any(k in blob for k in ("трапец", "ромб", "параллелограмм")):
        return "rect"
    if "площадь прямоугольника" in blob or (
        "прямоугольник" in blob and any(k in blob for k in ("сторон", "см", "площад"))
    ):
        return "rect"
    return None


def oge_math_default_kind(
    task_number: Optional[int],
    text: str = "",
    topic: str = "",
    params: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """Дефолт для ОГЭ math по номеру слота. plan — только при rooms в params."""
    if task_number is None:
        return None
    try:
        num = int(task_number)
    except (TypeError, ValueError):
        return None
    p = params or {}
    # 20–25: алгебра / текстовые / построение / сложная геометрия —
    # без случайных декоративных фигур (только явный kind из шаблона)
    if num in (20, 21, 22, 23, 24, 25):
        return None
    if num in (1, 2, 3, 4, 5):
        rooms = p.get("rooms")
        if isinstance(rooms, list) and rooms:
            return "plan"
        return None
    if num == 7:
        if p.get("points") or "координатн" in f"{topic} {text}".lower():
            return "numberline"
        return None
    if num == 13:
        blob = f"{topic} {text}".lower()
        if p.get("intervals") or p.get("points") or "[" in (text or "") or "прям" in blob:
            return "numberline"
        return None
    if num == 11:
        return "graph_match"
    if num == 18:
        return "grid"
    if num == 19:
        return None
    return OGE_MATH_DEFAULT_KIND.get(num)


def _nums_not_angles(text: str) -> list[float]:
    cleaned = re.sub(r"\d+\s*(?:°|градус\w*)", " ", text or "", flags=re.I)
    cleaned = re.sub(r"угол\s*[A-CАВС]?\s*(?:равен|=)?\s*", " ", cleaned, flags=re.I)
    return _nums_from_text(cleaned)


def _label_nums(text: str, n: int, defaults: list[str]) -> list[str]:
    nums = _nums_not_angles(text)
    labels = [str(int(v)) if float(v).is_integer() else str(v).rstrip("0").rstrip(".") for v in nums]
    while len(labels) < n:
        labels.append(defaults[len(labels)])
    return labels[:n]


def _triangle_is_angle_task(text: str) -> bool:
    blob = (text or "").lower()
    if any(k in blob for k in ("катет", "гипотенуз")):
        return False
    return any(k in blob for k in ("угол", "градус", "внешн", "°"))


def build_figure_svg(
    kind: str,
    text: str = "",
    params: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    p = params or {}
    if kind == "rect":
        shape = str(p.get("shape") or p.get("theme") or "").strip().lower()
        if shape in {"rhombus", "ромб"}:
            side = str(p.get("side") or p.get("a") or "a")
            return svg_rhombus(side)
        if shape in {"trapezoid", "трапеция"}:
            a = str(p.get("a") or "a")
            b = str(p.get("b") or "b")
            h = str(p.get("h") or "h")
            return svg_trapezoid_fig(a, b, h)
        a, b = _label_nums(text, 2, ["a", "b"])
        return svg_rectangle(a, b)
    if kind == "triangle":
        if _triangle_is_angle_task(text) or _extract_vertex_angle(text, p):
            return svg_triangle_with_angle(text, p)
        a, b, c = _label_nums(text, 3, ["a", "b", "c"])
        return svg_right_triangle(a, b, c)
    if kind == "box3d":
        a, b, c = _label_nums(text or "3 4 5", 3, ["3", "4", "5"])
        return svg_box3d(a, b, c)
    if kind == "circle":
        return svg_circle(_label_nums(text, 1, ["R"])[0], p)
    if kind == "numberline":
        return svg_numberline(text, p)
    if kind == "graph_linear":
        return svg_graph_linear(text)
    if kind == "graph_parabola":
        return svg_graph_parabola(text)
    if kind == "graph_hyperbola":
        return svg_graph_hyperbola(text)
    if kind == "graph_cubic":
        return svg_graph_cubic(text)
    if kind == "graph_match":
        return svg_graph_match(p, text)
    if kind == "plan":
        return svg_plan(p)
    if kind == "grid":
        return svg_grid(p, text)
    if kind == "scheme":
        return svg_scheme(p, text)
    # asset — только через load_pack_figure_svg / figure_data
    return None


_SCRIPT_TAG_RE = re.compile(r"<\s*script\b", re.IGNORECASE)
_VIEWBOX_RE = re.compile(
    r'viewBox\s*=\s*["\']0\s+0\s+\d+(?:\.\d+)?\s+\d+(?:\.\d+)?["\']',
    re.IGNORECASE,
)
_GEO_CLASS_RE = re.compile(r'class\s*=\s*["\'][^"\']*\b(?:geo-fig|fipi-fig)\b', re.IGNORECASE)


def is_safe_pack_svg(svg: str) -> bool:
    """Минимальная проверка pack/inline SVG для lightbox."""
    s = (svg or "").strip()
    if not s.lower().startswith("<svg"):
        return False
    if _SCRIPT_TAG_RE.search(s):
        return False
    if not _VIEWBOX_RE.search(s):
        return False
    if not _GEO_CLASS_RE.search(s):
        return False
    return True


def normalize_pack_figure_url(url: str) -> str:
    """Привести URL/путь к относительному пути внутри пака."""
    u = (url or "").strip().replace("\\", "/")
    if not u:
        return ""
    # /packs/oge_math/assets/... → assets/...
    m = re.match(r"^/?packs/[^/]+/(.+)$", u)
    if m:
        return m.group(1).lstrip("/")
    if u.startswith("/"):
        u = u.lstrip("/")
    return u


def resolve_pack_figure_path(
    url: str,
    *,
    pack_id: str = DEFAULT_FIGURE_PACK,
) -> Path | None:
    rel = normalize_pack_figure_url(url)
    if not rel:
        return None
    # запрет path traversal
    if ".." in rel.split("/"):
        return None
    root = (PACKS_ROOT / pack_id).resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.is_file() else None


def load_pack_figure_svg(
    url: str,
    *,
    pack_id: str = DEFAULT_FIGURE_PACK,
) -> str | None:
    path = resolve_pack_figure_path(url, pack_id=pack_id)
    if path is None:
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return raw if is_safe_pack_svg(raw) else None


def parse_figure_data(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    s = str(raw).strip()
    if not s:
        return {}
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _attach_pack_asset_figure(q: dict[str, Any]) -> dict[str, Any] | None:
    """Если есть figure_data / kind=asset / preload asset SVG — прикрепить.

    Возвращает обновлённый dict или None (продолжить процедурный путь).
    """
    fig_data = parse_figure_data(q.get("figure_data"))
    kind_raw = str(q.get("figure_kind") or "").strip().lower()
    wants_asset = bool(fig_data) or kind_raw == "asset"
    if not wants_asset:
        return None

    pack_id = str(q.get("_figure_pack") or DEFAULT_FIGURE_PACK).strip() or DEFAULT_FIGURE_PACK

    preloaded = str(q.get("figure_svg") or "").strip() or None
    if preloaded and not is_safe_pack_svg(preloaded):
        preloaded = None

    existing_sol = str(q.get("solution_figure_svg") or "").strip() or None
    if existing_sol and not is_safe_pack_svg(existing_sol):
        existing_sol = None

    url = str(fig_data.get("main_figure_url") or "").strip()
    from_file = load_pack_figure_svg(url, pack_id=pack_id) if url else None
    svg = from_file or preloaded or existing_sol
    if not svg:
        q["figure_kind"] = None
        q["figure_svg"] = None
        q.pop("solution_figure_svg", None)
        return q

    has_cond = fig_data.get("has_condition_figure")
    has_sol = fig_data.get("has_solution_figure")
    # дефолт для part2 asset: чертёж к решению
    if not fig_data and existing_sol and not preloaded and not from_file:
        # повторный attach опубликованного ключа: только solution
        has_cond, has_sol = False, True
    elif has_cond is None and has_sol is None:
        has_cond, has_sol = False, True
    else:
        has_cond = bool(has_cond) if has_cond is not None else False
        has_sol = bool(has_sol) if has_sol is not None else (not has_cond)

    # OGE math 23–25: геометрия должна быть видна на карточке условия,
    # даже если в seed стояло только has_solution_figure.
    try:
        slot_n = int(q.get("task_number") if q.get("task_number") is not None else q.get("_slot"))
    except (TypeError, ValueError):
        slot_n = None
    exam = str(q.get("exam_code") or q.get("exam") or "").strip().upper()
    subject = str(q.get("subject_code") or q.get("subject") or "").strip().lower()
    oge_geo = (
        slot_n in (23, 24, 25)
        and (
            bool(q.get("_oge_math_figures"))
            or (exam == "OGE" and subject in ("math", "математика"))
        )
    )
    if oge_geo and svg:
        has_cond = True

    q["figure_kind"] = "asset"
    q["needs_figure"] = bool(has_cond or has_sol)
    if has_cond:
        q["figure_svg"] = from_file or preloaded or svg
    else:
        q["figure_svg"] = None
    if has_sol:
        q["solution_figure_svg"] = from_file or existing_sol or svg
    else:
        q.pop("solution_figure_svg", None)
    if fig_data:
        q["figure_data"] = fig_data
    return q


def is_oge_rus_question(question: dict[str, Any] | None) -> bool:
    """ОГЭ русский: никаких math-чертежей (автодетект «коробке» / слот 11-парабола)."""
    q = question if isinstance(question, dict) else {}
    payload = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    params = q.get("figure_params") if isinstance(q.get("figure_params"), dict) else {}
    if payload.get("oge_rus") or params.get("oge_rus"):
        return True
    ui = str(payload.get("ui") or params.get("ui") or "").strip().lower()
    if ui in ("oge_rus", "listening", "essay_choice", "matching"):
        return True
    if str(q.get("exam_ui") or "").strip().lower() == "oge_rus_kim":
        return True
    exam = str(q.get("exam_code") or q.get("exam") or "").strip().upper()
    subject = str(q.get("subject_code") or q.get("subject") or "").strip().lower()
    return exam == "OGE" and subject in ("russian", "rus", "ru")


def strip_math_figures(question: dict[str, Any]) -> dict[str, Any]:
    """Убрать чертёж ОГЭ математики с карточки (русский / чужой pack)."""
    q = question
    q["figure_kind"] = None
    q["figure_svg"] = None
    q["needs_figure"] = False
    params = q.get("figure_params")
    if isinstance(params, dict) and params.get("oge_rus"):
        payload = q.get("payload") if isinstance(q.get("payload"), dict) else None
        if not (payload and payload.get("oge_rus")):
            q["payload"] = dict(params)
    q.pop("figure_params", None)
    q.pop("figure_data", None)
    q.pop("solution_figure_svg", None)
    q.pop("_figure_pack", None)
    return q


def attach_figure(question: dict[str, Any]) -> dict[str, Any]:
    """Шаблонный SVG. Сырой SVG от модели отбрасывается. Без ложных чертежей по умолчанию."""
    q = dict(question)
    if is_oge_rus_question(q):
        return strip_math_figures(q)

    # сохранить уже готовый solution SVG при повторном attach (publish/strip)
    existing_solution = q.get("solution_figure_svg")
    if isinstance(existing_solution, str) and is_safe_pack_svg(existing_solution):
        pass
    else:
        existing_solution = None

    asset_hit = _attach_pack_asset_figure(q)
    if asset_hit is not None:
        if existing_solution and not asset_hit.get("solution_figure_svg"):
            asset_hit["solution_figure_svg"] = existing_solution
        return asset_hit

    params = _as_params(q.get("figure_params"))
    payload_q = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    if isinstance(params, dict) and isinstance(payload_q.get("base_vars"), dict):
        params = dict(params)
        params.setdefault("base_vars", dict(payload_q["base_vars"]))
    if isinstance(params, dict) and params.get("oge_rus"):
        # payload ОГЭ русский — не чертёж
        return strip_math_figures(q)
    if isinstance(params, dict) and params.get("mutator_logic"):
        logic = params.get("mutator_logic")
        nested = logic.get("figure") if isinstance(logic, dict) else None
        stripped = {
            k: v
            for k, v in params.items()
            if k not in {"mutator_logic", "template", "explanation_template"}
        }
        if isinstance(nested, dict):
            params = {**nested, **{k: v for k, v in stripped.items() if k not in nested}}
        else:
            params = stripped
    text = str(q.get("text") or "")
    topic = str(q.get("topic") or "")
    explicit_kind = q.get("figure_kind")
    kind = detect_figure_kind(text, topic, explicit_kind)

    exam = str(q.get("exam_code") or q.get("exam") or "").strip().upper()
    subject = str(q.get("subject_code") or q.get("subject") or "").strip().lower()
    task_number = q.get("task_number")
    if task_number is None:
        task_number = q.get("_slot")
    try:
        slot = int(task_number) if task_number is not None else None
    except (TypeError, ValueError):
        slot = None

    use_oge_defaults = bool(q.get("_oge_math_figures")) or (
        exam == "OGE" and subject in ("math", "математика")
    )

    if use_oge_defaults and slot is not None:
        # 1–5: таблицы/шины/тексты — без авто-детекта; только plan при rooms в params
        if slot in (1, 2, 3, 4, 5):
            rooms = params.get("rooms")
            has_rooms = isinstance(rooms, list) and bool(rooms)
            if has_rooms:
                kind = "plan"
            elif explicit_kind:
                k = detect_figure_kind(text, topic, explicit_kind)
                kind = k if k == "scheme" else None
            else:
                kind = None
        # 20–22: не цепляем авто-детект (3D/сложная геометрия по ключевым словам)
        elif slot == 11:
            kind = "graph_match"
        elif slot in (19, 20, 21):
            kind = detect_figure_kind(text, topic, explicit_kind) if explicit_kind else None
        elif slot == 22:
            # построение графика учеником — только явный простой graph_*
            if explicit_kind:
                k = detect_figure_kind(text, topic, explicit_kind)
                kind = k if k and str(k).startswith("graph_") else None
            else:
                kind = None
        elif slot in (23, 24, 25):
            # только явный простой вид; без авто-дефолта (ложный чертёж хуже пустоты)
            if explicit_kind:
                k = detect_figure_kind(text, topic, explicit_kind)
                kind = k if k in ("rect", "triangle", "circle", "asset") else None
            else:
                kind = None
            if kind in ("box3d", "plan", "grid", "numberline"):
                kind = None
        elif not kind:
            kind = oge_math_default_kind(slot, text, topic, params)
    elif not kind and use_oge_defaults:
        kind = oge_math_default_kind(task_number, text, topic, params)

    # needs_figure без распознанного вида — не клеим случайный прямоугольник / 3D для ОГЭ
    if not kind and q.get("needs_figure"):
        section = str(q.get("section") or "").lower()
        if use_oge_defaults and slot is not None and slot >= 20:
            kind = oge_math_default_kind(slot, text, topic, params)
        elif section == "functions":
            kind = "graph_parabola"
        elif section == "planimetry":
            kind = "triangle"
        elif section == "stereometry" and not use_oge_defaults:
            kind = "box3d"
        else:
            kind = None

    if kind == "box3d" and use_oge_defaults:
        # ОГЭ math КИМ — планиметрия; 3D-коробочки не из бланка
        kind = None

    # plan без rooms — не рисуем фейк
    if kind == "plan" and not (isinstance(params.get("rooms"), list) and params.get("rooms")):
        kind = None

    if kind == "numberline":
        params = _enrich_numberline_params(q, params if isinstance(params, dict) else {}, text)
    if kind == "graph_match":
        params = dict(params or {})
        payload_g = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        vals = payload_g.get("mutator_values") if isinstance(payload_g.get("mutator_values"), dict) else {}
        graphs = params.get("graphs")
        mapped: list[str] = []
        if isinstance(graphs, list) and graphs:
            for g in graphs[:3]:
                raw = str(g or "").strip()
                m = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", raw)
                mapped.append(str(vals.get(m.group(1)) if m else g or "").strip())
        if len(mapped) == 3 and all(mapped) and not any(x.startswith("{") for x in mapped):
            params["graphs"] = mapped
        elif vals:
            trio = [vals.get("g1"), vals.get("g2"), vals.get("g3")]
            if all(isinstance(g, str) and g and not g.startswith("{") for g in trio):
                params["graphs"] = trio

    if kind and kind != "asset":
        svg = build_figure_svg(kind, text, params)
        if svg:
            q["figure_kind"] = kind
            q["figure_svg"] = svg
            q["needs_figure"] = True
            if existing_solution:
                q["solution_figure_svg"] = existing_solution
            return q
    q["figure_kind"] = None
    q["figure_svg"] = None
    if existing_solution:
        q["solution_figure_svg"] = existing_solution
    else:
        q.pop("solution_figure_svg", None)
    return q
