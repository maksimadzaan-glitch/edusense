/**
 * Universal TaskRenderer — vanilla ES module player for
 * CHOICE_SINGLE / CHOICE_MULTI / MATCHING / SHORT_VALUE / FREE_RESPONSE.
 *
 *   import { renderTask, collectAnswer, TaskRenderer } from './task_renderer.js';
 *   renderTask(task, container, { onChange(answer) {} });
 *   const answer = collectAnswer(container, task.type);
 */

const FALLBACK_MSG = "Неизвестный тип задания или повреждены данные";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatText(raw) {
  const fmt =
    typeof globalThis.formatMathText === "function"
      ? globalThis.formatMathText
      : typeof window !== "undefined" && typeof window.formatMathText === "function"
        ? window.formatMathText
        : null;
  if (fmt) return fmt(raw);
  return escapeHtml(String(raw || "")).replace(/\$/g, "");
}

/** Align with backend.services.task_answers.normalize_answer */
export function normalizeAnswer(s, { lower = true } = {}) {
  let text = String(s ?? "").trim().replace(/\u00a0/g, " ");
  text = text.replace(/\s+/g, " ");
  if (lower) text = text.toLowerCase();
  return text;
}

function payloadOf(task) {
  const p = task && task.payload;
  if (p == null) return {};
  if (typeof p === "string") {
    try {
      return JSON.parse(p) || {};
    } catch {
      return {};
    }
  }
  return typeof p === "object" ? p : {};
}

function optionList(payload) {
  const opts = payload && payload.options;
  if (!Array.isArray(opts)) return [];
  return opts.map((o, i) => {
    if (o == null) return { id: String(i + 1), text: "" };
    if (typeof o === "string") return { id: String(i + 1), text: o };
    return {
      id: String(o.id != null ? o.id : i + 1),
      text: String(o.text != null ? o.text : ""),
    };
  });
}

function emitChange(container, type, onChange) {
  if (typeof onChange !== "function") return;
  onChange(collectAnswer(container, type));
}

function bindChange(container, type, onChange) {
  container.addEventListener("change", () => emitChange(container, type, onChange));
  container.addEventListener("input", () => emitChange(container, type, onChange));
}

function renderChoiceSingle(task, payload) {
  const name = `tr-${escapeHtml(task.id || "x")}`;
  const opts = optionList(payload)
    .map(
      (o) => `
      <label class="tr-option">
        <input type="radio" name="${name}" value="${escapeHtml(o.id)}" data-tr-choice />
        <span class="tr-opt-id">${escapeHtml(o.id)}</span>
        <span class="tr-opt-text">${formatText(o.text)}</span>
      </label>`
    )
    .join("");
  return `<div class="tr-choices" data-tr-kind="CHOICE_SINGLE">${opts || `<p class="tr-error">${FALLBACK_MSG}</p>`}</div>`;
}

function renderChoiceMulti(task, payload) {
  const opts = optionList(payload)
    .map(
      (o) => `
      <label class="tr-option">
        <input type="checkbox" value="${escapeHtml(o.id)}" data-tr-multi />
        <span class="tr-opt-id">${escapeHtml(o.id)}</span>
        <span class="tr-opt-text">${formatText(o.text)}</span>
      </label>`
    )
    .join("");
  return `<div class="tr-choices" data-tr-kind="CHOICE_MULTI">${opts || `<p class="tr-error">${FALLBACK_MSG}</p>`}</div>`;
}

function renderMatching(task, payload) {
  const left = Array.isArray(payload.left) ? payload.left : [];
  const right = Array.isArray(payload.right) ? payload.right : [];
  if (!left.length && !right.length) {
    return `<div class="tr-matching" data-tr-kind="MATCHING"><p class="tr-error">${FALLBACK_MSG}</p></div>`;
  }
  const leftHtml = left
    .map((item, i) => {
      const id = String(item && item.id != null ? item.id : String.fromCharCode(65 + i));
      const text = item && item.text != null ? item.text : "";
      return `
        <div class="tr-match-row" data-tr-left="${escapeHtml(id)}">
          <span class="tr-match-left"><strong>${escapeHtml(id)}</strong> ${formatText(text)}</span>
          <input class="tr-match-input" type="text" inputmode="numeric" autocomplete="off"
            data-tr-match="${escapeHtml(id)}" aria-label="Ответ для ${escapeHtml(id)}" />
        </div>`;
    })
    .join("");
  const rightHtml = right
    .map((item, i) => {
      const id = String(item && item.id != null ? item.id : i + 1);
      const text = item && item.text != null ? item.text : "";
      return `<div class="tr-match-right-item"><span class="tr-opt-id">${escapeHtml(id)}</span> ${formatText(text)}</div>`;
    })
    .join("");
  return `
      <div class="tr-matching" data-tr-kind="MATCHING">
        <div class="tr-match-left-col">${leftHtml}</div>
        <div class="tr-match-right-col">${rightHtml}</div>
      </div>`;
}

function renderShort(task, payload) {
  const hint = (payload && (payload.input_hint || payload.unit)) || "";
  return `
      <div class="tr-short" data-tr-kind="SHORT_VALUE">
        <input class="tr-short-input" type="text" autocomplete="off" data-tr-short
          placeholder="${escapeHtml(hint || "Ответ")}" />
        ${payload && payload.unit ? `<span class="tr-unit">${escapeHtml(payload.unit)}</span>` : ""}
      </div>`;
}

function renderFree(task, payload) {
  const hint = (payload && payload.criteria_hint) || "Развёрнутый ответ";
  return `
      <div class="tr-free" data-tr-kind="FREE_RESPONSE">
        <textarea class="tr-free-input" data-tr-free rows="6" placeholder="${escapeHtml(hint)}"></textarea>
      </div>`;
}

function renderBody(task) {
  const type = String((task && task.type) || "").toUpperCase();
  const payload = payloadOf(task);
  switch (type) {
    case "CHOICE_SINGLE":
      return renderChoiceSingle(task, payload);
    case "CHOICE_MULTI":
      return renderChoiceMulti(task, payload);
    case "MATCHING":
      return renderMatching(task, payload);
    case "SHORT_VALUE":
      return renderShort(task, payload);
    case "FREE_RESPONSE":
      return renderFree(task, payload);
    default:
      return `<p class="tr-error">${FALLBACK_MSG}</p>`;
  }
}

/**
 * @param {object} task
 * @param {HTMLElement} container
 * @param {{ onChange?: (answer: string) => void }} [opts]
 */
export function renderTask(task, container, opts) {
  if (!container) {
    console.error("renderTask: container required");
    return null;
  }
  const options = opts || {};
  container.classList.add("tr-root");

  if (!task || typeof task !== "object") {
    container.dataset.trType = "";
    container.dataset.trId = "";
    container.innerHTML = `<p class="tr-error">${FALLBACK_MSG}</p>`;
    return container;
  }

  try {
    const type = String(task.type || "").toUpperCase();
    container.dataset.trType = type;
    container.dataset.trId = task.id != null ? String(task.id) : "";
    container.innerHTML = `
      <div class="tr-meta">
        <span class="tr-pill">${escapeHtml(task.subject || "")}</span>
        <span class="tr-pill">${escapeHtml(task.exam_type || "")}</span>
        <span class="tr-pill">№${escapeHtml(task.task_number)}</span>
        <span class="tr-pill tr-pill-type">${escapeHtml(type || "?")}</span>
        ${task.max_score != null ? `<span class="tr-pill">${escapeHtml(task.max_score)} б.</span>` : ""}
      </div>
      ${task.topic ? `<h3 class="tr-topic">${escapeHtml(task.topic)}</h3>` : ""}
      <div class="tr-statement">${formatText(task.statement)}</div>
      <div class="tr-answer">${renderBody(task)}</div>
    `;
    bindChange(container, type, options.onChange);
    emitChange(container, type, options.onChange);
  } catch (err) {
    console.error("renderTask failed", err);
    container.innerHTML = `<p class="tr-error">${FALLBACK_MSG}</p>`;
  }
  return container;
}

/**
 * @param {HTMLElement} container
 * @param {string} type
 * @returns {string}
 */
export function collectAnswer(container, type) {
  const t = String(type || (container && container.dataset.trType) || "").toUpperCase();
  if (!container) return "";

  if (t === "CHOICE_SINGLE") {
    const checked = container.querySelector("input[data-tr-choice]:checked");
    return checked ? String(checked.value) : "";
  }

  if (t === "CHOICE_MULTI") {
    const ids = Array.from(container.querySelectorAll("input[data-tr-multi]:checked")).map((el) =>
      String(el.value)
    );
    ids.sort((a, b) => {
      const na = Number(a);
      const nb = Number(b);
      if (!Number.isNaN(na) && !Number.isNaN(nb)) return na - nb;
      return a.localeCompare(b, "ru");
    });
    return ids.join("");
  }

  if (t === "MATCHING") {
    const inputs = Array.from(container.querySelectorAll("input[data-tr-match]"));
    return inputs.map((el) => String(el.value || "").trim()).join("");
  }

  if (t === "SHORT_VALUE") {
    const el = container.querySelector("[data-tr-short]");
    return el ? String(el.value || "") : "";
  }

  if (t === "FREE_RESPONSE") {
    const el = container.querySelector("[data-tr-free]");
    return el ? String(el.value || "") : "";
  }

  return "";
}

export const TaskRenderer = { renderTask, collectAnswer, normalizeAnswer, escapeHtml };
