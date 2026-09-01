/**
 * EduSense math: школьный вид ФИПИ (unicode + [[дроби]] + аккуратный KaTeX).
 * Без «вертикального» развала 3/x/2/−/4 и без битого \begin.
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hasKatex() {
    return typeof global.katex === "object" && typeof global.katex.renderToString === "function";
  }

  function renderLatex(tex, displayMode) {
    const clean = String(tex || "")
      .replace(/^\s*\$+|\$+\s*$/g, "")
      .trim();
    if (!clean) return "";
    let html;
    if (!hasKatex()) {
      html = `<span class="math-fallback">${escapeHtml(clean)}</span>`;
    } else {
      try {
        html = global.katex.renderToString(clean, {
          throwOnError: false,
          displayMode: !!displayMode,
          strict: "ignore",
          output: "html",
        });
      } catch (_) {
        html = `<span class="math-fallback">${escapeHtml(clean)}</span>`;
      }
    }
    if (displayMode) {
      return `<div class="katex-scroll overflow-x-auto py-1">${html}</div>`;
    }
    return `<span class="katex-scroll overflow-x-auto">${html}</span>`;
  }

  /** Relative /media|/packs|/assets → absolute URL (PDF/html2canvas need full URL). */
  function absolutizeMediaUrl(src) {
    const s = String(src || "").trim();
    if (!s || /^javascript:/i.test(s) || /^data:/i.test(s) || /^blob:/i.test(s)) return s;
    if (/^https?:\/\//i.test(s)) return s;
    try {
      const origin =
        (typeof global.location !== "undefined" && global.location.origin) ||
        "https://edusence.ru";
      if (s.startsWith("//")) return (global.location?.protocol || "https:") + s;
      return new URL(s, origin.endsWith("/") ? origin : origin + "/").href;
    } catch (_) {
      const base = "https://edusence.ru";
      return s.startsWith("/") ? base + s : base + "/" + s;
    }
  }

  function taskImgHtml(src, taskNum, altText) {
    const s = absolutizeMediaUrl(src);
    if (!s || /^javascript:/i.test(s)) return "";
    const n = taskNum != null && taskNum !== "" ? String(taskNum) : "";
    const alt = altText || (n ? `Изображение к заданию №${n}` : "Изображение к заданию");
    return (
      `<img class="task-media-img" src="${escapeHtml(s)}" alt="${escapeHtml(alt)}" ` +
      `loading="lazy" crossorigin="anonymous" data-task-num="${escapeHtml(n)}" />`
    );
  }

  function imgFallbackEl(img) {
    if (!img || img.dataset.fallback === "1") return;
    img.dataset.fallback = "1";
    const n = String(img.getAttribute("data-task-num") || "").trim();
    const ph = document.createElement("div");
    ph.className = "task-media-fallback";
    ph.setAttribute("role", "img");
    ph.textContent = n ? `[Изображение к заданию №${n}]` : "[Изображение к заданию]";
    if (img.parentNode) img.replaceWith(ph);
  }

  if (typeof document !== "undefined" && !global.__edusenseImgErrorBound) {
    global.__edusenseImgErrorBound = true;
    document.addEventListener(
      "error",
      function (e) {
        const t = e.target;
        if (!t || t.tagName !== "IMG") return;
        if (!t.classList || !t.classList.contains("task-media-img")) return;
        imgFallbackEl(t);
      },
      true
    );
  }

  function repairBrokenLatex(text) {
    let t = String(text ?? "");
    t = t.replace(/\u0008egin/g, "\\begin").replace(/\u0008/g, "");
    t = t.replace(/\u000crac/g, "\\frac").replace(/\u000c/g, "");
    t = t.replace(/\\?egin\{cases\}/gi, "\\begin{cases}");
    t = t.replace(/(?<![\\a-zA-Z])egin\{cases\}/gi, "\\begin{cases}");
    t = t.replace(/(?<![\\a-zA-Z])rac\{/g, "\\frac{");
    return t;
  }

  function casesToPlain(text) {
    return String(text).replace(/\\begin\{cases\}([\s\S]*?)\\end\{cases\}/gi, (_, body) => {
      const rows = String(body)
        .split(/\\\\|\n/)
        .map((s) => s.replace(/\\/g, "").replace(/\s+/g, " ").trim())
        .filter(Boolean);
      if (rows.length >= 2) return `{ ${rows.join(" ; ")} }`;
      return rows.join(" ");
    });
  }

  function collapseVerticalJunk(text) {
    const lines = String(text).split(/\n/).map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return "";
    const short = lines.filter((l) => l.length <= 2).length;
    // Только «вертикальный мусор» (много коротких строк) → одна строка;
    // иначе сохраняем переносы (проза / списки 1) 2) 3)).
    if (short >= Math.max(3, Math.floor(lines.length / 2))) {
      return lines.join(" ");
    }
    return lines.join("\n");
  }

  const ATOM =
    "[0-9]+(?:[.,][0-9]+)?|[a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*|[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+";

  /** a/b, (expr)/(expr), x/3 → [[числ|знам]]; не трогаем шины 175/70 R13 и уже [[ ]]. */
  function slashToFracMarkers(text) {
    let t = String(text ?? "");
    const saved = [];
    t = t.replace(/\[\[[\s\S]*?\]\]/g, (m) => {
      const i = saved.length;
      saved.push(m);
      return `\uE000${i}\uE001`;
    });

    for (let pass = 0; pass < 3; pass++) {
      t = t.replace(/\(([^()]{1,80})\)\s*\/\s*\(([^()]{1,80})\)/g, "[[$1|$2]]");
      t = t.replace(
        new RegExp(`\\(([^()]{1,80})\\)\\s*/\\s*(${ATOM})(?![\\w.])`, "g"),
        "[[$1|$2]]"
      );
      t = t.replace(
        new RegExp(`(${ATOM})\\s*/\\s*\\(([^()]{1,80})\\)`, "g"),
        "[[$1|$2]]"
      );
    }

    // x/3, a/b, −6/x (не даты и не шины)
    t = t.replace(
      /(?<!\[)(?<!\|)([-+−]?)([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)\s*\/\s*([0-9]+(?:[.,][0-9]+)?|[a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)(?!\s*R)(?!\])/g,
      (_, sign, a, b) => `[[${sign}${a}|${b}]]`
    );
    t = t.replace(
      /(?<!\[)(?<!\|)([-+−]?)([0-9]+(?:[.,][0-9]+)?)\s*\/\s*([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9₀-₉]*)(?!\])/g,
      (_, sign, a, b) => `[[${sign}${a}|${b}]]`
    );

    // 15/4, 1/3 — но не 175/70 R13
    t = t.replace(
      /(?<!\[)(?<!\|)\b([-+−]?\d+(?:[.,]\d+)?)\s*\/\s*(\d+(?:[.,]\d+)?)\b(?!\s*R)(?!\])/g,
      "[[$1|$2]]"
    );

    t = t.replace(/\uE000(\d+)\uE001/g, (_, i) => saved[Number(i)] || "");
    return t;
  }

  const SUP_MAP = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "-": "⁻", "+": "⁺",
  };

  function caretToSuperscripts(s) {
    const sup = (digits) => [...String(digits)].map((c) => SUP_MAP[c] || c).join("");
    return String(s || "")
      .replace(/\^\{(-?\d+)\}/g, (_, d) => sup(d))
      .replace(/\^(-?\d+)/g, (_, d) => sup(d));
  }

  /** Нормализация к школьному виду + маркеры дробей. Не трогает \uE400/\uE500 маркеры. */
  function prepareMathSource(raw) {
    let text = repairBrokenLatex(raw);
    text = normalizeDegrees(text);
    text = normalizeSubscripts(text);
    text = casesToPlain(text);
    text = collapseVerticalJunk(text);
    text = text.replace(/```+/g, "");
    // Одиночные $ уже вырезаны в stashDollarLatex; остатки убираем
    text = text.replace(/\$\$/g, " ").replace(/\$/g, " ");

    // Не трогаем уже готовые [[числ|знам]] правилами «x 2» → x² (ломали «x − 2»)
    const stashed = [];
    text = text.replace(/\[\[[\s\S]*?\]\]/g, (m) => {
      const i = stashed.length;
      stashed.push(m);
      return `\uE010${i}\uE011`;
    });
    // Не трогаем KaTeX/subscript маркеры
    text = text.replace(/\uE400\d+\uE401/g, (m) => {
      const i = stashed.length;
      stashed.push(m);
      return `\uE010${i}\uE011`;
    });
    text = text.replace(/\uE500[^|]+\|[^\uE501]+\uE501/g, (m) => {
      const i = stashed.length;
      stashed.push(m);
      return `\uE010${i}\uE011`;
    });

    // Вложенные корни: \\sqrt{\\sqrt{x}} — несколько проходов
    for (let i = 0; i < 4; i += 1) {
      const next = text
        .replace(/\\sqrt\{([^{}]+)\}/g, "√($1)")
        .replace(/\\sqrt\s*([0-9a-zA-Zа-яА-ЯёЁ]+)/g, "√$1");
      if (next === text) break;
      text = next;
    }

    text = text
      .replace(/\\dfrac\{([^{}]+)\}\{([^{}]+)\}/g, "[[$1|$2]]")
      .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, "[[$1|$2]]")
      .replace(/\\cdot|\\times/g, "·")
      .replace(/\\pm/g, "±")
      .replace(/\\leq|\\leqslant/g, "≤")
      .replace(/\\geq|\\geqslant/g, "≥")
      .replace(/\\neq/g, "≠")
      .replace(/\\infty/g, "∞")
      .replace(/\\cup/g, "∪")
      .replace(/\\circ/g, "°")
      .replace(/\\left|\\right|\\,/g, "")
      .replace(/\\begin\{[^}]+\}|\\end\{[^}]+\}/g, "")
      .replace(/\\([A-Za-z]+)/g, "$1")
      .replace(/\\/g, "");
    text = normalizeDegrees(text);

    text = caretToSuperscripts(text);
    text = text.replace(/<=/g, "≤").replace(/>=/g, "≥").replace(/!=/g, "≠");
    text = text.replace(/(?<![*\w])\*(?![*\w])/g, "·");
    // «3 x 2 − 4 x» → 3x² − 4x (только пробел/таб, не перевод строки: иначе «x > 4\nx ≤ 9» → «4x»)
    text = text.replace(/\b(\d+)[ \t]+[xх][ \t]+2\b/g, "$1x²");
    text = text.replace(/\b(\d+)[ \t]+[xх][ \t]+3\b/g, "$1x³");
    text = text.replace(/\b[xх][ \t]+2\b/g, "x²");
    text = text.replace(/\b[xх][ \t]+3\b/g, "x³");
    text = text.replace(/\b(\d+)[ \t]+[xх]\b/g, "$1x");
    text = slashToFracMarkers(text);
    text = text.replace(/\uE010(\d+)\uE011/g, (_, i) => stashed[Number(i)] || "");
    return text.replace(/[ \t]{2,}/g, " ").trim();
  }

  function fracHtml(num, den) {
    const n = String(num).trim();
    const d = String(den).trim();
    // Алгебраические дроби — только CSS (KaTeX+unicode давал «лестницу» x/−/2/x/2/…)
    const algebraic = /[a-zA-Zа-яА-ЯёЁxх]/i.test(n + d);
    let inner;
    if (!algebraic && hasKatex()) {
      const toTex = (s) =>
        String(s)
          .replace(/⁰/g, "^{0}")
          .replace(/¹/g, "^{1}")
          .replace(/²/g, "^{2}")
          .replace(/³/g, "^{3}")
          .replace(/⁴/g, "^{4}")
          .replace(/⁵/g, "^{5}")
          .replace(/⁶/g, "^{6}")
          .replace(/⁷/g, "^{7}")
          .replace(/⁸/g, "^{8}")
          .replace(/⁹/g, "^{9}")
          .replace(/⁻/g, "^{-}")
          .replace(/−/g, "-")
          .replace(/·/g, "\\cdot ");
      inner = renderLatex(`\\dfrac{${toTex(n)}}{${toTex(d)}}`, false);
    } else {
      inner =
        `<span class="frac">` +
        `<span class="num">${escapeHtml(n)}</span>` +
        `<span class="den">${escapeHtml(d)}</span>` +
        `</span>`;
    }
    return `<span class="math-frac">${inner}</span>`;
  }

  function normalizeDegrees(text) {
    let t = String(text ?? "");
    t = t.replace(/градусах\s+Цельсия/gi, "°C");
    t = t.replace(/градуса[х]?\s+Цельсия/gi, "°C");
    t = t.replace(/градус(?:ах|а|ов)?\s+по\s+Цельсию/gi, "°C");
    t = t.replace(/\bdegC\b/gi, "°C");
    // 90^° / 90^\circ / 90°C / 90_C / 90 °C
    t = t.replace(/(\d+(?:[.,]\d+)?)\s*\^\s*\\?circ\s*([CFКК])?/gi, (_, n, u) =>
      u ? `${n}°${u.toUpperCase() === "К" || u.toUpperCase() === "K" ? "C" : u.toUpperCase()}` : `${n}°`
    );
    t = t.replace(/(\d+(?:[.,]\d+)?)\s*\^\s*[°˚]\s*([CFКК])?/gi, (_, n, u) =>
      u ? `${n}°${/[кk]/i.test(u) ? "C" : u.toUpperCase()}` : `${n}°`
    );
    t = t.replace(/(\d+(?:[.,]\d+)?)\s*_\s*([CFКК])\b/g, (_, n, u) =>
      `${n}°${/[кk]/i.test(u) ? "C" : u.toUpperCase()}`
    );
    t = t.replace(/(\d+(?:[.,]\d+)?)\s*°\s*([CFКК])\b/g, (_, n, u) =>
      `${n}°${/[кk]/i.test(u) ? "C" : u.toUpperCase()}`
    );
    t = t.replace(/\\circ/g, "°");
    t = t.replace(/\^°/g, "°");
    t = t.replace(/°\s*C\b/g, "°C");
    return t;
  }

  /** t_C / t_{C} → маркеры подстрочного индекса (не путать с 90_C → °C). */
  function normalizeSubscripts(text) {
    let t = String(text ?? "");
    t = t.replace(/\b([A-Za-zА-Яа-яЁё])_\{([A-Za-zА-Яа-яЁё0-9]+)\}/g, (_, base, sub) => {
      return `\uE500${base}|${sub}\uE501`;
    });
    t = t.replace(/\b([A-Za-zА-Яа-яЁё])_([A-Za-zА-Яа-яЁё])\b/g, (_, base, sub) => {
      return `\uE500${base}|${sub}\uE501`;
    });
    return t;
  }

  function expandSubscriptMarkers(escaped) {
    return String(escaped).replace(/\uE500([^|]+)\|([^\uE501]+)\uE501/g, (_, base, sub) => {
      if (hasKatex()) {
        const rendered = renderLatex(`${base}_{${sub}}`, false);
        if (rendered && !rendered.includes("math-fallback")) return rendered;
      }
      return `${base}<sub>${sub}</sub>`;
    });
  }

  /** Вырезаем $...$ / $$...$$ до нормализации, рендерим через KaTeX. */
  function stashDollarLatex(text) {
    const chunks = [];
    let t = String(text ?? "");
    t = t.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
      const i = chunks.length;
      chunks.push({ display: true, tex: String(tex).trim() });
      return `\uE400${i}\uE401`;
    });
    t = t.replace(/\$([^$\n]+?)\$/g, (_, tex) => {
      const i = chunks.length;
      chunks.push({ display: false, tex: String(tex).trim() });
      return `\uE400${i}\uE401`;
    });
    return { text: t, chunks };
  }

  function expandDollarMarkers(html, chunks) {
    if (!chunks || !chunks.length) return html;
    return String(html).replace(/\uE400(\d+)\uE401/g, (_, i) => {
      const c = chunks[Number(i)];
      if (!c) return "";
      return renderLatex(c.tex, c.display);
    });
  }

  function radicandToTex(s) {
    return String(s || "")
      .replace(/⁰/g, "^{0}")
      .replace(/¹/g, "^{1}")
      .replace(/²/g, "^{2}")
      .replace(/³/g, "^{3}")
      .replace(/⁴/g, "^{4}")
      .replace(/⁵/g, "^{5}")
      .replace(/⁶/g, "^{6}")
      .replace(/⁷/g, "^{7}")
      .replace(/⁸/g, "^{8}")
      .replace(/⁹/g, "^{9}")
      .replace(/⁻/g, "^{-}")
      .replace(/−/g, "-")
      .replace(/·/g, "\\cdot ")
      .replace(/°/g, "^\\circ ");
  }

  function sqrtHtml(radicand, alreadyEscaped) {
    const inner = String(radicand || "").trim();
    if (!inner) return "";
    if (hasKatex()) {
      const texInner = alreadyEscaped
        ? radicandToTex(inner.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/&quot;/g, '"'))
        : radicandToTex(inner);
      const rendered = renderLatex(`\\sqrt{${texInner}}`, false);
      if (rendered && !rendered.includes("math-fallback")) {
        return `<span class="math-sqrt is-katex" aria-label="корень">${rendered}</span>`;
      }
    }
    const safe = alreadyEscaped ? inner : escapeHtml(inner);
    return (
      `<span class="math-sqrt" aria-label="корень">` +
      `<span class="math-sqrt-sign">√</span>` +
      `<span class="math-sqrt-radicand">${safe}</span>` +
      `</span>`
    );
  }

  /** После escape: корни с чертой (vinculum) над подкоренным. */
  function wrapSqrtInEscaped(escaped) {
    let t = String(escaped);
    t = t.replace(/√\(([^)]+)\)/g, (_, inner) => sqrtHtml(inner, true));
    t = t.replace(
      /√([0-9a-zA-Zа-яА-ЯёЁ]+(?:[²³⁴⁵⁶⁷⁸⁹⁰]*)?)/g,
      (_, atom) => sqrtHtml(atom, true)
    );
    return t;
  }

  function systemHtml(rows) {
    const body = (rows || [])
      .map((row) => `<span class="math-system-row">${formatMathInline(row)}</span>`)
      .join("");
    return (
      `<span class="math-system" aria-label="система уравнений">` +
      `<span class="math-system-brace" aria-hidden="true">{</span>` +
      `<span class="math-system-rows">${body}</span>` +
      `</span>`
    );
  }

  function stashEquationSystems(text) {
    const systems = [];
    const out = String(text || "").replace(/\{([^{}]+)\}/g, (full, inner) => {
      const rows = String(inner)
        .split(";")
        .map((s) => s.trim())
        .filter(Boolean);
      if (rows.length < 2 || !rows.every((r) => r.includes("="))) return full;
      const i = systems.length;
      systems.push(rows);
      return `\uE300${i}\uE301`;
    });
    return { text: out, systems };
  }

  function formatMathInline(raw) {
    const dollars = stashDollarLatex(raw);
    const source = prepareMathSource(dollars.text);
    if (!source && !dollars.chunks.length) return "";
    const placeholders = [];
    let t = source;
    for (let guard = 0; guard < 24; guard++) {
      const next = t.replace(/\[\[([^\[\]|]+)\|([^\[\]|]+)\]\]/g, (_, n, d) => {
        const i = placeholders.length;
        placeholders.push(fracHtml(n, d));
        return `\uE200${i}\uE201`;
      });
      if (next === t) break;
      t = next;
    }
    const parts = t.split(/(\uE200\d+\uE201|\uE400\d+\uE401|\uE500[^|]+\|[^\uE501]+\uE501)/g);
    let html = "";
    for (const part of parts) {
      if (!part) continue;
      const m = part.match(/^\uE200(\d+)\uE201$/);
      if (m) {
        html += placeholders[Number(m[1])] || "";
        continue;
      }
      if (/^\uE400\d+\uE401$/.test(part) || /^\uE500/.test(part)) {
        html += expandSubscriptMarkers(expandDollarMarkers(part, dollars.chunks));
        continue;
      }
      html += expandSubscriptMarkers(wrapSqrtInEscaped(escapeHtml(part)));
    }
    return expandDollarMarkers(html, dollars.chunks);
  }

  /**
   * Главный хелпер: KaTeX для $...$, корни/дроби, без вертикального развала.
   */
  function formatMathText(raw) {
    const dollars = stashDollarLatex(raw);
    const prepared = prepareMathSource(dollars.text);
    if (!prepared && !dollars.chunks.length) return "";
    const { text, systems } = stashEquationSystems(prepared);
    const placeholders = [];
    let t = text;
    for (let guard = 0; guard < 24; guard++) {
      const next = t.replace(/\[\[([^\[\]|]+)\|([^\[\]|]+)\]\]/g, (_, n, d) => {
        const i = placeholders.length;
        placeholders.push(fracHtml(n, d));
        return `\uE200${i}\uE201`;
      });
      if (next === t) break;
      t = next;
    }

    const parts = t.split(/(\uE200\d+\uE201|\uE300\d+\uE301|\uE400\d+\uE401|\uE500[^|]+\|[^\uE501]+\uE501)/g);
    let html = "";
    for (const part of parts) {
      if (!part) continue;
      const frac = part.match(/^\uE200(\d+)\uE201$/);
      if (frac) {
        html += placeholders[Number(frac[1])] || "";
        continue;
      }
      const sys = part.match(/^\uE300(\d+)\uE301$/);
      if (sys) {
        html += systemHtml(systems[Number(sys[1])] || []);
        continue;
      }
      if (/^\uE400\d+\uE401$/.test(part) || /^\uE500/.test(part)) {
        html += expandSubscriptMarkers(expandDollarMarkers(part, dollars.chunks));
        continue;
      }
      html += expandSubscriptMarkers(wrapSqrtInEscaped(escapeHtml(part))).replace(/\n/g, "<br>");
    }
    return expandDollarMarkers(html, dollars.chunks);
  }

  function formatAnswerKey(raw, part = 1) {
    if (Number(part) === 2) return "";
    let text = prepareMathSource(raw);
    if (!text) return "";

    const lines = text.split(/\n/).map((l) => l.trim()).filter(Boolean);
    let preferred = null;
    for (const ln of lines) {
      const m = ln.match(/^(ответ|ключ|ans|answer)\s*[:：\-]?\s*(.+)$/i);
      if (m) preferred = m[2].trim();
    }
    if (preferred) text = preferred;
    else if (lines.length) text = lines.find((l) => l.length <= 80) || lines[0];
    text = text.replace(/^(ответ|ключ|ans|answer)\s*[:：\-]?\s*/i, "");

    const compact = text.replace(/\s/g, "");
    if (/^[\[(].*[;,:].*[\])](?:[∪∩Uu][\[(].*[;,:].*[\])])*$/.test(compact)) {
      return `<span class="kim-key-value">${escapeHtml(text)}</span>`;
    }

    let m = compact.match(/^\[\[?([-+]?\d+(?:[.,]\d+)?)\|1\]\]?$/);
    if (m) text = m[1];
    else if ((m = compact.match(/^([-+]?\d+(?:[.,]\d+)?)\/1$/))) text = m[1];

    const plainNum = /^[-+]?\d+(?:[.,]\d+)?$/.test(text.replace(/\s/g, ""));
    if (plainNum) {
      const shown = text.replace(/\s/g, "").replace(".", ",");
      return `<span class="kim-key-value">${escapeHtml(shown)}</span>`;
    }
    return `<span class="kim-key-value">${formatMathText(text)}</span>`;
  }

  /** Десятичная запятая → точка, не трогая последовательности цифр (3412). */
  function coerceMathDecimalInput(raw) {
    const s = String(raw ?? "");
    const trimmed = s.trim();
    if (/^-?\d+,\d*$/.test(trimmed)) return trimmed.replace(",", ".");
    return s;
  }

  global.formatMathText = formatMathText;
  global.formatTaskHtml = formatMathText;
  global.formatAnswerKey = formatAnswerKey;
  global.prepareMathSource = prepareMathSource;
  global.coerceMathDecimalInput = coerceMathDecimalInput;
  global.edusenseTaskImgHtml = taskImgHtml;
  global.absolutizeMediaUrl = absolutizeMediaUrl;
  global.__edusenseImgError = imgFallbackEl;
})(typeof window !== "undefined" ? window : globalThis);
