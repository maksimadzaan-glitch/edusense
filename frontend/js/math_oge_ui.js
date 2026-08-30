/**
 * ОГЭ математика 1–5: общий сюжет и чертёж один раз сверху.
 * <ContextTaskGroup/> + <TaskAssetViewer/> на vanilla JS.
 *
 * @typedef {Object} TaskContext
 * @property {string} [group_id]
 * @property {string} [title]
 * @property {string} [story_text]
 * @property {string} [asset_id]
 * @property {Object<string, *>} [base_vars]
 * @property {string|null} [figure_kind]
 * @property {string|null} [figure_svg]
 * @property {string|null} [figure_url]
 *
 * @typedef {Object} TaskGroup
 * @property {string} group_id
 * @property {TaskContext} context
 * @property {Array<{task_num:number, question:string, type:string}>} subtasks
 *
 * @typedef {Object} TaskTemplate
 * @property {string} template_text
 * @property {Object} [mutator_logic]
 * @property {string} [explanation_template]
 */
(function (global) {
  "use strict";

  var ASSET_REGISTRY = {
    TireDiagram: "scheme",
    PaperFormatDiagram: "scheme",
    StoveDiagram: "scheme",
    TravelMapDiagram: "scheme",
    UmbrellaDiagram: "scheme",
    PlanDiagram: "plan",
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function payloadOf(task) {
    var p = task && (task.payload || task.Payload);
    if (p == null) return null;
    if (typeof p === "string") {
      try {
        return JSON.parse(p);
      } catch (e) {
        return null;
      }
    }
    return typeof p === "object" ? p : null;
  }

  function numOf(task) {
    var n = Number(task && (task.num != null ? task.num : task.task_number));
    return Number.isFinite(n) ? n : 0;
  }

  function isPipeTableRow(line) {
    var s = String(line || "");
    if (s.indexOf("|") < 0) return false;
    if (/\[\[/.test(s)) return false;
    return s.split("|").length >= 2;
  }

  function formatRichText(raw) {
    var text = String(raw || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!text) return "";
    var blocks = text.split(/\n\n+/);
    return blocks.map(formatRichBlock).join("");
  }

  function formatRichBlock(block) {
    var lines = String(block || "")
      .split("\n")
      .map(function (l) {
        return l.trim();
      })
      .filter(Boolean);
    if (!lines.length) return "";
    var html = "";
    var i = 0;
    while (i < lines.length) {
      var tableStart =
        isPipeTableRow(lines[i]) && i + 1 < lines.length && isPipeTableRow(lines[i + 1]);
      if (tableStart) {
        var tableLines = [];
        while (i < lines.length && isPipeTableRow(lines[i])) {
          tableLines.push(lines[i]);
          i += 1;
        }
        html += renderPipeTable(tableLines);
        continue;
      }
      var prose = [];
      while (i < lines.length) {
        if (
          isPipeTableRow(lines[i]) &&
          i + 1 < lines.length &&
          isPipeTableRow(lines[i + 1])
        ) {
          break;
        }
        prose.push(lines[i]);
        i += 1;
      }
      html += '<p class="math-oge-p">' + formatPlain(prose.join("\n")) + "</p>";
    }
    return html;
  }

  function formatPlain(block) {
    var text = String(block || "").trim();
    if (!text) return "";
    if (typeof global.formatMathText === "function") {
      return global.formatMathText(text);
    }
    return escapeHtml(text).replace(/\n/g, "<br>");
  }

  function formatTableCell(raw) {
    var text = String(raw || "").trim();
    if (!text || text === "—" || text === "-" || text === "–") return "";
    if (typeof global.formatMathText === "function" && /\[\[|\\frac|\\sqrt|√|\^/.test(text)) {
      return global.formatMathText(text);
    }
    return escapeHtml(text);
  }

  function isTableSepRow(cells) {
    if (!cells || !cells.length) return false;
    return cells.every(function (c) {
      var s = String(c || "").replace(/\s/g, "");
      return !s || /^:?-{2,}:?$/.test(s) || s === "---";
    });
  }

  function isAnswerGridHead(head) {
    if (!head || head.length < 2 || head.length > 4) return false;
    return head.every(function (c) {
      return /^[А-ЯA-Z]$/.test(String(c || "").trim());
    });
  }

  function renderPipeTable(lines) {
    var rows = lines.map(function (line) {
      return line.split("|").map(function (c) {
        return c.trim();
      });
    });
    rows = rows.filter(function (r) {
      return !isTableSepRow(r);
    });
    var width = 0;
    rows.forEach(function (r) {
      if (r.length > width) width = r.length;
    });
    rows = rows.map(function (r) {
      while (r.length < width) r.push("");
      return r;
    });
    if (!rows.length) return "";
    var head = rows[0];
    var body = rows.slice(1);
    var answer = isAnswerGridHead(head);
    var html =
      '<div class="math-oge-table-wrap' +
      (answer ? " is-answer-grid" : "") +
      '"><table class="math-oge-table' +
      (answer ? " is-answer" : "") +
      '"><thead><tr>';
    head.forEach(function (c) {
      html += "<th>" + formatTableCell(c) + "</th>";
    });
    html += "</tr></thead><tbody>";
    if (!body.length && answer) {
      html += "<tr>";
      head.forEach(function () {
        html += '<td class="math-oge-blank">&nbsp;</td>';
      });
      html += "</tr>";
    }
    body.forEach(function (r) {
      html += "<tr>";
      r.forEach(function (c, idx) {
        var cls = "";
        if (answer) cls = ' class="math-oge-blank"';
        else if (idx > 0 && /^-?\d+([.,]\d+)?$/.test(String(c).trim())) cls = ' class="math-oge-num"';
        html += "<td" + cls + ">" + formatTableCell(c) + "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  function formatStory(raw) {
    return formatRichText(raw);
  }

  function safeSvg(kind, svg) {
    var s = String(svg || "");
    if (!s) return "";
    if (typeof global._safeFigureSvg === "function") {
      return global._safeFigureSvg(kind || "scheme", s);
    }
    if (!/class="[^"]*\b(fipi-fig|geo-fig)\b/.test(s)) return "";
    if (!/viewBox=["']0 0 \d+(?:\.\d+)? \d+(?:\.\d+)?["']/.test(s)) return "";
    return s;
  }

  /**
   * Реестр ассетов: http(s) → <img>, иначе SVG с сервера по asset_id.
   * @param {string} assetId
   * @param {Object<string, *>} [vars]
   * @param {TaskContext} [ctx]
   */
  function renderTaskAssetViewer(assetId, vars, ctx) {
    var context = ctx || {};
    var id = String(assetId || context.asset_id || "").trim();
    var url = String(context.figure_url || "").trim();
    if (!url && /^https?:\/\//i.test(id)) url = id;
    if (url && /^https?:\/\//i.test(url) && !/^javascript:/i.test(url)) {
      var img =
        typeof global.edusenseTaskImgHtml === "function"
          ? global.edusenseTaskImgHtml(url, "1–5", "Чертёж к заданиям 1–5")
          : '<img class="task-media-img" src="' +
            escapeHtml(url) +
            '" alt="Чертёж к заданиям 1–5" loading="lazy" data-task-num="1–5" />';
      return (
        '<div class="task-figure math-oge-asset" data-figure="img" role="button" tabindex="0" title="Увеличить чертёж" aria-label="Увеличить чертёж">' +
        img +
        "</div>"
      );
    }
    var kind =
      context.figure_kind ||
      ASSET_REGISTRY[id] ||
      "scheme";
    var svg = safeSvg(kind, context.figure_svg || "");
    if (!svg) return "";
    return (
      '<div class="task-figure math-oge-asset" data-figure="' +
      escapeHtml(kind) +
      '" role="button" tabindex="0" title="Увеличить чертёж" aria-label="Увеличить чертёж">' +
      svg +
      "</div>"
    );
  }

  function findMathContext(tasks) {
    var list = Array.isArray(tasks) ? tasks : [];
    var i;
    for (i = 0; i < list.length; i++) {
      var p = payloadOf(list[i]) || {};
      if (p.math_context && typeof p.math_context === "object") {
        return p.math_context;
      }
    }
    var group = list.filter(function (t) {
      var n = numOf(t);
      return n >= 1 && n <= 5;
    });
    if (!group.length) return null;
    var p0 = payloadOf(group[0]) || {};
    if (!p0.shared_story && !p0.asset_id && !group[0].figureSvg && !group[0].figure_svg) {
      return null;
    }
    return {
      group_id: p0.context_id || "math_oge_1_5",
      title: p0.context_title || "",
      story_text: p0.shared_story || "",
      asset_id: p0.asset_id || "",
      base_vars: p0.base_vars || {},
      figure_kind: group[0].figureKind || group[0].figure_kind || "scheme",
      figure_svg: group[0].figureSvg || group[0].figure_svg || null,
      figure_url: null,
    };
  }

  /** Блок общего сюжета — аналог ContextTaskGroup. */
  function renderContextTaskGroup(ctx) {
    if (!ctx) return "";
    var title = String(ctx.title || "Задания 1–5").trim();
    var story = formatStory(ctx.story_text);
    var asset = renderTaskAssetViewer(ctx.asset_id, ctx.base_vars, ctx);
    if (!story && !asset) return "";
    return (
      '<aside class="math-oge-context" data-math-group="' +
      escapeHtml(ctx.group_id || "") +
      '">' +
      '<p class="math-oge-context-kicker">Задания 1–5 · общий сюжет</p>' +
      "<h3 class=\"math-oge-context-title\">" +
      escapeHtml(title) +
      "</h3>" +
      (story ? '<div class="math-oge-context-story">' + story + "</div>" : "") +
      asset +
      "</aside>"
    );
  }

  function mapTasks(tasks, renderCard) {
    var list = Array.isArray(tasks) ? tasks : [];
    var ctx = findMathContext(list);
    var out = [];
    var shown = false;
    for (var i = 0; i < list.length; i++) {
      var task = list[i];
      var n = numOf(task);
      if (!shown && ctx && n >= 1 && n <= 5) {
        out.push(renderContextTaskGroup(ctx));
        shown = true;
      }
      if (typeof renderCard === "function") {
        out.push(renderCard(task));
      }
    }
    return out.join("");
  }

  global.MathOgeUI = {
    ASSET_REGISTRY: ASSET_REGISTRY,
    findMathContext: findMathContext,
    renderContextTaskGroup: renderContextTaskGroup,
    renderTaskAssetViewer: renderTaskAssetViewer,
    mapTasks: mapTasks,
    formatRichText: formatRichText,
  };
})(typeof window !== "undefined" ? window : globalThis);
