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
    if (!hasKatex()) {
      return `<span class="math-fallback">${escapeHtml(clean)}</span>`;
    }
    try {
      return global.katex.renderToString(clean, {
        throwOnError: false,
        displayMode: !!displayMode,
        strict: "ignore",
        output: "html",
      });
    } catch (_) {
      return `<span class="math-fallback">${escapeHtml(clean)}</span>`;
    }
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

  /** Нормализация к школьному виду + маркеры дробей */
  function prepareMathSource(raw) {
    let text = repairBrokenLatex(raw);
    text = casesToPlain(text);
    text = collapseVerticalJunk(text);
    text = text.replace(/```+/g, "");
    text = text.replace(/\$\$/g, " ").replace(/\$/g, " ");

    // Не трогаем уже готовые [[числ|знам]] правилами «x 2» → x² (ломали «x − 2»)
    const stashed = [];
    text = text.replace(/\[\[[\s\S]*?\]\]/g, (m) => {
      const i = stashed.length;
      stashed.push(m);
      return `\uE010${i}\uE011`;
    });

    text = text
      .replace(/\\dfrac\{([^{}]+)\}\{([^{}]+)\}/g, "[[$1|$2]]")
      .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, "[[$1|$2]]")
      .replace(/\\sqrt\{([^{}]+)\}/g, "√($1)")
      .replace(/\\sqrt\s*([0-9a-zA-Zа-яА-ЯёЁ]+)/g, "√$1")
      .replace(/\\cdot|\\times/g, "·")
      .replace(/\\pm/g, "±")
      .replace(/\\leq|\\leqslant/g, "≤")
      .replace(/\\geq|\\geqslant/g, "≥")
      .replace(/\\neq/g, "≠")
      .replace(/\\infty/g, "∞")
      .replace(/\\cup/g, "∪")
      .replace(/\\left|\\right|\\,/g, "")
      .replace(/\\begin\{[^}]+\}|\\end\{[^}]+\}/g, "")
      .replace(/\\([A-Za-z]+)/g, "$1")
      .replace(/\\/g, "");

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

  function sqrtHtml(radicand) {
    const inner = String(radicand || "").trim();
    return (
      `<span class="math-sqrt" aria-label="корень">` +
      `<span class="math-sqrt-sign">√</span>` +
      `<span class="math-sqrt-radicand">${inner}</span>` +
      `</span>`
    );
  }

  /** После escape: корни с чертой (vinculum) над подкоренным. */
  function wrapSqrtInEscaped(escaped) {
    let t = String(escaped);
    t = t.replace(/√\(([^)]+)\)/g, (_, inner) => sqrtHtml(inner));
    t = t.replace(
      /√([0-9a-zA-Zа-яА-ЯёЁ]+(?:[²³⁴⁵⁶⁷⁸⁹⁰]*)?)/g,
      (_, atom) => sqrtHtml(atom)
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
    const source = prepareMathSource(raw);
    if (!source) return "";
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
    const parts = t.split(/(\uE200\d+\uE201)/g);
    let html = "";
    for (const part of parts) {
      if (!part) continue;
      const m = part.match(/^\uE200(\d+)\uE201$/);
      if (m) html += placeholders[Number(m[1])] || "";
      else html += wrapSqrtInEscaped(escapeHtml(part));
    }
    return html;
  }

  /**
   * Главный хелпер: HTML без видимых $ и без вертикального развала.
   */
  function formatMathText(raw) {
    const prepared = prepareMathSource(raw);
    if (!prepared) return "";
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

    const parts = t.split(/(\uE200\d+\uE201|\uE300\d+\uE301)/g);
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
      html += wrapSqrtInEscaped(escapeHtml(part)).replace(/\n/g, "<br>");
    }
    return html;
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
})(typeof window !== "undefined" ? window : globalThis);
