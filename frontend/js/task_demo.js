/**
 * Universal Task Player demo — ES module.
 * Imports renderer via ES import graph (no global player race).
 */
import { renderTask, collectAnswer, normalizeAnswer } from "./task_renderer.js?v=3";

const state = { tasks: [], current: null, answer: "" };

function hostEl() {
  return document.getElementById("task-host");
}

function resultEl() {
  return document.getElementById("demo-result");
}

function setResult(text, cls) {
  const el = resultEl();
  if (!el) return;
  el.className = "demo-result " + (cls || "is-pending");
  el.textContent = text;
}

function setHostLoading(msg) {
  const host = hostEl();
  if (!host) return;
  host.innerHTML = `<p class="demo-loading">${msg || "Загрузка заданий..."}</p>`;
}

function setHostError(msg) {
  const host = hostEl();
  if (!host) return;
  host.innerHTML = `<p class="tr-error demo-error">${msg}</p>`;
}

function formatError(data, status) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  }
  return "Ошибка " + status;
}

async function loadList() {
  const subjectEl = document.getElementById("flt-subject");
  const examEl = document.getElementById("flt-exam");
  const sel = document.getElementById("sel-task");
  if (!subjectEl || !examEl || !sel) {
    setResult("На странице нет элементов управления", "is-bad");
    return;
  }

  setHostLoading("Загрузка заданий...");
  setResult("Загрузка заданий...", "is-pending");

  const qs = new URLSearchParams();
  if (subjectEl.value) qs.set("subject", subjectEl.value);
  if (examEl.value) qs.set("exam_type", examEl.value);
  const q = qs.toString();

  let res;
  let data = {};
  try {
    res = await fetch("/api/tasks" + (q ? "?" + q : ""));
    data = await res.json().catch(() => ({}));
  } catch (err) {
    const msg = "Не удалось загрузить список: " + (err.message || err);
    setHostError(msg);
    setResult(msg, "is-bad");
    return;
  }

  if (!res.ok) {
    const msg = formatError(data, res.status);
    setHostError(msg);
    setResult(msg, "is-bad");
    return;
  }

  state.tasks = data.tasks || [];
  sel.innerHTML = state.tasks
    .map((t) => `<option value="${t.id}">${t.id} · ${t.type}</option>`)
    .join("");

  if (!state.tasks.length) {
    state.current = null;
    const msg =
      "Нет заданий. Шаблон должен подтянуться автоматически; если нет — " +
      "python -m backend.scripts.import_tasks backend/universal/packs/tasks_template.json";
    setHostError(msg);
    setResult(msg, "is-bad");
    return;
  }

  sel.value = state.tasks[0].id;
  await showTask(sel.value);
}

async function showTask(id) {
  if (!id) return;
  setHostLoading("Загрузка задания...");
  setResult("Загрузка задания...", "is-pending");

  let res;
  let data = {};
  try {
    res = await fetch("/api/tasks/" + encodeURIComponent(id));
    data = await res.json().catch(() => ({}));
  } catch (err) {
    const msg = "Не удалось загрузить задание: " + (err.message || err);
    setHostError(msg);
    setResult(msg, "is-bad");
    return;
  }

  if (!res.ok) {
    const msg = formatError(data, res.status);
    setHostError(msg);
    setResult(msg, "is-bad");
    return;
  }

  state.current = data.task;
  state.answer = "";
  const host = hostEl();
  if (!host) {
    setResult("Нет контейнера #task-host", "is-bad");
    return;
  }
  host.innerHTML = "";
  renderTask(state.current, host, {
    onChange(a) {
      state.answer = a;
      const shown = normalizeAnswer(state.answer) || "—";
      setResult("Текущий ответ: «" + shown + "»", "is-pending");
    },
  });
  const shown = normalizeAnswer(state.answer) || "—";
  setResult("Текущий ответ: «" + shown + "»", "is-pending");
}

async function check() {
  if (!state.current) {
    setResult("Сначала загрузите и выберите задание", "is-bad");
    return;
  }
  const host = hostEl();
  const answer = collectAnswer(host, state.current.type);
  state.answer = answer;
  const normalized = normalizeAnswer(answer);

  let res;
  let data = {};
  try {
    res = await fetch("/api/tasks/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: state.current.id, answer }),
    });
    data = await res.json().catch(() => ({}));
  } catch (err) {
    setResult("Не удалось проверить: " + (err.message || err), "is-bad");
    return;
  }

  if (!res.ok) {
    setResult(formatError(data, res.status), "is-bad");
    return;
  }
  if (data.ok === null) {
    setResult(
      "FREE_RESPONSE: автопроверка отключена (score=" + data.score + "/" + data.max_score + ")",
      "is-pending"
    );
    return;
  }
  setResult(
    (data.ok ? "Верно" : "Неверно") +
      ": " +
      data.score +
      "/" +
      data.max_score +
      " · ответ «" +
      (normalized || answer) +
      "»",
    data.ok ? "is-ok" : "is-bad"
  );
}

function boot() {
  const btnLoad = document.getElementById("btn-load");
  const selTask = document.getElementById("sel-task");
  const btnCheck = document.getElementById("btn-check");
  if (!btnLoad || !selTask || !btnCheck) {
    setResult("На странице нет элементов управления", "is-bad");
    console.error("task_demo: missing controls");
    return;
  }
  btnLoad.addEventListener("click", () =>
    loadList().catch((e) => {
      setHostError(String(e.message || e));
      setResult(String(e.message || e), "is-bad");
    })
  );
  selTask.addEventListener("change", (e) =>
    showTask(e.target.value).catch((err) => {
      setHostError(String(err.message || err));
      setResult(String(err.message || err), "is-bad");
    })
  );
  btnCheck.addEventListener("click", () =>
    check().catch((e) => setResult(String(e.message || e), "is-bad"))
  );
  loadList().catch((e) => {
    setHostError(String(e.message || e));
    setResult(String(e.message || e), "is-bad");
  });
}

boot();
