"use strict";

/** @deprecated legacy blob — migrated into discrete keys */
const LS_KEY = "edusense_student_entry";
const LS_NAME = "student_name";
const LS_CLASS = "class_code";
const LS_STUDENT_ID = "student_id";
const LS_META = "edusense_student_meta";
const LS_PROGRESS = "edusense_student_progress";
const LS_HOME = "edusense_student_home";
const LS_AUTH = "edusense_user";
const LS_STREAK_VISITS = "edusense_streak_visits";
const LS_BONUS_XP = "edusense_bonus_xp";
const LS_WARMUP = "edusense_warmup_day";

const NAV = [
  { id: "home", label: "Главная", icon: "home" },
  { id: "progress", label: "Мой прогресс", icon: "chart", badge: { text: "PRO", kind: "pro" } },
  { id: "live", label: "Live-Урок", icon: "rocket", action: "live", badge: { text: "LIVE", kind: "live" } },
  { id: "invite", label: "Пригласить человека", icon: "gift", action: "invite", badge: { text: "Бонус", kind: "bonus" } },
];

/** Из ссылки/вставки достаёт EDU-XXXX (или чистый код). */
function normalizeJoinCode(raw) {
  let s = String(raw || "").trim();
  if (!s) return "";
  try {
    s = decodeURIComponent(s);
  } catch {
    /* ignore */
  }
  let candidate = s;
  try {
    let urlStr = s;
    if (/^(t\.me|telegram\.me)\//i.test(urlStr)) urlStr = "https://" + urlStr;
    if (/^https?:\/\//i.test(urlStr)) {
      const u = new URL(urlStr);
      candidate =
        u.searchParams.get("code") ||
        u.searchParams.get("join") ||
        u.searchParams.get("startapp") ||
        u.searchParams.get("start") ||
        candidate;
    }
  } catch {
    /* not a full URL */
  }
  const fromQuery = String(candidate).match(/(?:^|[?&#])(?:code|join|startapp|start)=([^&\s#]+)/i);
  if (fromQuery) candidate = fromQuery[1];
  const edu = String(candidate).match(/EDU-\d{4}/i);
  if (edu) return edu[0].toUpperCase();
  const eduInRaw = s.match(/EDU-\d{4}/i);
  if (eduInRaw) return eduInRaw[0].toUpperCase();
  return String(candidate)
    .replace(/\s+/g, "")
    .replace(/^["'`]+|["'`]+$/g, "")
    .toUpperCase();
}

function applyCodeFromInput(el) {
  if (!el) return "";
  const normalized = normalizeJoinCode(el.value);
  if (normalized && normalized !== el.value.trim().toUpperCase()) {
    el.value = normalized;
  } else if (normalized) {
    el.value = normalized;
  }
  state.code = normalized;
  return normalized;
}

const ICONS = {
  home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"/><path d="M14 3v5h5M9 13h6M9 17h4"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19h16M7 16V9M12 16V5M17 16v-7"/></svg>`,
  gift: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>`,
  rocket: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91 0z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>`,
};

function icon(name) {
  return ICONS[name] || "";
}

function initials(name) {
  return (name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || "")
    .join("");
}

const state = {
  step: "join", // join | dashboard | work | done | review
  tab: "home", // home | progress
  code: "",
  name: "",
  studentId: "",
  classCode: "",
  className: "",
  subject: "",
  exam: "",
  loading: false,
  codeError: "",
  nameError: "",
  closed: false,
  previewTitle: "",
  previewSubject: "",
  savedEntry: null,
  assignment: null,
  answers: {},
  workStarted: false,
  startedAt: null, // ISO string when student opens work
  result: null,
  dashboard: null, // { active, completed, stats, ... }
  reviewItem: null, // completed task card with ai_review
  pendingAssignmentCode: null, // open this after join/dashboard load
  // Timer policy (documented): after expiry allow submit, block changing answers.
  timerEndsAt: null, // ms epoch or null
  timerExpired: false,
  timerPromptShown: false,
  timerPausedRemaining: null, // ms left after leaving work (pause)
  _timerTickId: null,
  lastSavedAt: null, // ms when local autosave fired
  showInvite: false,
  showLive: false,
  showFullBoard: false,
  focusPlayerOpen: false,
};

const FOCUS_TRACKS = [
  {
    title: "Better Days",
    artist: "LAKEY INSPIRED",
    src: "/audio/lofi/better-days.mp3",
  },
  {
    title: "Sweet September",
    artist: "Arulo",
    src: "/audio/lofi/sweet-september.mp3",
  },
  {
    title: "Sleepy Cat",
    artist: "Alejandro Magaña",
    src: "/audio/lofi/sleepy-cat.mp3",
  },
];

let focusAudio = null;
let focusTrackIndex = 0;
let focusBound = false;
let focusLoadAttempts = 0;
let focusPlayerScheduled = false;

function getFocusAudio() {
  if (typeof Audio === "undefined") return null;
  if (!focusAudio) {
    focusAudio = new Audio();
    focusAudio.preload = "none";
    focusAudio.loop = false;
    focusAudio.volume = 0.6;
  }
  return focusAudio;
}

function bindFocusAudioEvents() {
  const audio = getFocusAudio();
  if (!audio || focusBound) return;
  focusBound = true;
  audio.addEventListener("play", syncFocusPlayerDom);
  audio.addEventListener("pause", syncFocusPlayerDom);
  audio.addEventListener("canplay", () => {
    focusLoadAttempts = 0;
  });
  audio.addEventListener("error", handleFocusAudioError);
  audio.addEventListener("ended", () => {
    const next = (focusTrackIndex + 1) % FOCUS_TRACKS.length;
    loadFocusTrack(next, { autoplay: true });
  });
}

function handleFocusAudioError() {
  const track = currentFocusTrack();
  console.warn("[Lo-Fi] Не удалось загрузить трек:", track.title, track.src);
  focusLoadAttempts += 1;
  if (focusLoadAttempts >= FOCUS_TRACKS.length) {
    console.warn("[Lo-Fi] Все fallback-треки недоступны");
    syncFocusPlayerDom();
    return;
  }
  const next = (focusTrackIndex + 1) % FOCUS_TRACKS.length;
  loadFocusTrack(next, { autoplay: focusIsPlaying() });
}

function uuidClient() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "s-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}

function loadSession() {
  try {
    let name = localStorage.getItem(LS_NAME) || "";
    let classCode = (localStorage.getItem(LS_CLASS) || "").trim().toUpperCase();
    let studentId = localStorage.getItem(LS_STUDENT_ID) || "";
    let meta = null;
    try {
      meta = JSON.parse(localStorage.getItem(LS_META) || "null");
    } catch {
      meta = null;
    }

    // migrate legacy
    if ((!name || !classCode) && localStorage.getItem(LS_KEY)) {
      try {
        const legacy = JSON.parse(localStorage.getItem(LS_KEY) || "null");
        if (legacy && typeof legacy === "object") {
          if (!name) name = String(legacy.name || "").trim();
          if (!classCode) classCode = String(legacy.code || "").trim().toUpperCase();
        }
      } catch {
        /* ignore */
      }
    }

    name = String(name || "").trim();
    if (!name || name.length < 2) return null;
    if (!classCode) return null;
    if (!studentId) {
      studentId = uuidClient();
      try {
        localStorage.setItem(LS_STUDENT_ID, studentId);
      } catch {
        /* ignore */
      }
    }
    return {
      name,
      classCode,
      studentId,
      className: (meta && meta.class_name) || "",
      subject: (meta && meta.subject) || "",
      exam: (meta && meta.exam) || "",
      assignmentCode: (meta && meta.assignment_code) || "",
    };
  } catch {
    return null;
  }
}

function saveSession(data) {
  try {
    const name = String(data.student_name || data.name || "").trim();
    const classCode = String(data.class_code || data.classCode || "")
      .trim()
      .toUpperCase();
    const studentId = String(data.student_id || data.studentId || uuidClient());
    localStorage.setItem(LS_NAME, name);
    localStorage.setItem(LS_CLASS, classCode);
    localStorage.setItem(LS_STUDENT_ID, studentId);
    localStorage.setItem(
      LS_META,
      JSON.stringify({
        class_name: data.class_name || data.className || "",
        subject: data.subject || "",
        exam: data.exam || "",
        assignment_code: data.assignment_code || (data.assignment && data.assignment.code) || "",
      })
    );
    // legacy compat for old continue flow
    localStorage.setItem(LS_KEY, JSON.stringify({ code: classCode, name }));
    rememberStudentHome({
      name,
      classCode,
      className: data.class_name || data.className || "",
      subject: data.subject || "",
      exam: data.exam || "",
      studentId,
    });
  } catch {
    /* ignore quota / private mode */
  }
}

function clearSession() {
  try {
    localStorage.removeItem(LS_KEY);
    localStorage.removeItem(LS_NAME);
    localStorage.removeItem(LS_CLASS);
    localStorage.removeItem(LS_STUDENT_ID);
    localStorage.removeItem(LS_META);
    localStorage.removeItem(LS_HOME);
  } catch {
    /* ignore */
  }
}

function rememberStudentHome(data) {
  try {
    const user = readAuthUser();
    const name = String((data && data.name) || "").trim();
    const classCode = String((data && data.classCode) || "").trim().toUpperCase();
    if (!name || !classCode) return;
    localStorage.setItem(
      LS_HOME,
      JSON.stringify({
        userId: user && user.id != null ? user.id : null,
        name,
        class_code: classCode,
        class_name: (data && data.className) || "",
        subject: (data && data.subject) || "",
        exam: (data && data.exam) || "",
        student_id: (data && data.studentId) || "",
      })
    );
  } catch {
    /* ignore */
  }
}

function loadStudentHome() {
  try {
    const raw = JSON.parse(localStorage.getItem(LS_HOME) || "null");
    if (!raw || typeof raw !== "object") return null;
    const name = String(raw.name || "").trim();
    const classCode = String(raw.class_code || "").trim().toUpperCase();
    if (!name || name.length < 2 || !classCode) return null;
    return {
      userId: raw.userId != null ? raw.userId : null,
      name,
      classCode,
      className: raw.class_name || "",
      subject: raw.subject || "",
      exam: raw.exam || "",
      studentId: raw.student_id || "",
    };
  } catch {
    return null;
  }
}

function readAuthUser() {
  try {
    const user = JSON.parse(localStorage.getItem(LS_AUTH) || "null");
    if (!user || typeof user !== "object") return null;
    if (String(user.role || "") !== "student") return null;
    return user;
  } catch {
    return null;
  }
}

function homeMatchesUser(home, user) {
  if (!home || !user) return false;
  if (home.userId != null && user.id != null && Number(home.userId) === Number(user.id)) {
    return true;
  }
  return normalizeNameKey(home.name) === normalizeNameKey(user.full_name);
}

function applyKnownClassroom({ name, classCode, className, subject, exam, studentId }) {
  const nm = String(name || "").trim();
  const code = String(classCode || "").trim().toUpperCase();
  if (!nm || nm.length < 2 || !code) return false;
  state.name = nm;
  state.classCode = code;
  state.className = className || "";
  state.subject = subject || "";
  state.exam = exam || "";
  state.studentId = studentId || state.studentId || uuidClient();
  if (!state.code) state.code = code;
  saveSession({
    student_id: state.studentId,
    student_name: state.name,
    class_code: state.classCode,
    class_name: state.className,
    subject: state.subject,
    exam: state.exam,
  });
  state.savedEntry = { code: state.classCode, name: state.name };
  return true;
}

function loadSavedEntry() {
  const s = loadSession();
  if (!s) return null;
  return { code: s.classCode, name: s.name };
}

function saveEntry(code, name) {
  saveSession({
    name,
    class_code: code,
    student_id: state.studentId || uuidClient(),
    class_name: state.className,
    subject: state.subject,
    exam: state.exam,
  });
}

function clearEntry() {
  clearSession();
}

function normalizeNameKey(name) {
  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

/** Autosave key: assignment code + student name (so siblings on one device don't clash). */
function progressKey(assignmentCode, studentName) {
  const code = String(assignmentCode || "")
    .trim()
    .toUpperCase();
  const name = normalizeNameKey(studentName != null ? studentName : state.name);
  if (!code) return "";
  return name ? `${code}::${name}` : code;
}

function hasLocalProgress(assignmentCode) {
  try {
    const raw = localStorage.getItem(LS_PROGRESS);
    if (!raw) return false;
    const map = JSON.parse(raw);
    const key = progressKey(assignmentCode);
    let item = map && map[key];
    // migrate legacy key = code only
    if ((!item || typeof item !== "object") && map) {
      const legacy = map[String(assignmentCode || "").trim().toUpperCase()];
      if (legacy && typeof legacy === "object") item = legacy;
    }
    if (!item || typeof item !== "object") return false;
    if (item.started_at || item.timer_paused) return true;
    return Object.values(item.answers || {}).some(
      (a) => (a && String(a.text || "").trim()) || (a && a.photoDataUrl)
    );
  } catch {
    return false;
  }
}

function remainingTimerMs() {
  if (state.timerExpired) return 0;
  if (state.timerEndsAt != null) return Math.max(0, state.timerEndsAt - Date.now());
  if (state.timerPausedRemaining != null) return Math.max(0, Number(state.timerPausedRemaining) || 0);
  return null;
}

function saveLocalProgress(assignmentCode, answers, startedAt, extra = {}) {
  try {
    const key = progressKey(assignmentCode);
    if (!key) return;
    const map = JSON.parse(localStorage.getItem(LS_PROGRESS) || "{}") || {};
    const prev = map[key] && typeof map[key] === "object" ? map[key] : {};
    const now = Date.now();
    const pauseTimer = extra.pauseTimer === true;
    const remaining = remainingTimerMs();
    map[key] = {
      answers,
      student_name: state.name || prev.student_name || "",
      started_at: startedAt || prev.started_at || null,
      updated_at: now,
      timer_remaining_ms: remaining != null ? remaining : prev.timer_remaining_ms ?? null,
      timer_paused: pauseTimer,
      timer_expired: !!state.timerExpired,
    };
    localStorage.setItem(LS_PROGRESS, JSON.stringify(map));
    state.lastSavedAt = now;
    if (!pauseTimer) pulseAutosaveHint();
  } catch {
    /* ignore */
  }
}

function formatAutosaveTime(ms) {
  if (!ms) return "";
  try {
    return new Date(ms).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function pulseAutosaveHint() {
  const el = document.getElementById("autosave-hint");
  if (!el) return;
  const t = formatAutosaveTime(state.lastSavedAt);
  el.textContent = t ? `Сохранено автоматически · ${t}` : "Сохранено автоматически";
  el.classList.remove("is-pulse");
  // reflow to restart animation
  void el.offsetWidth;
  el.classList.add("is-pulse");
}

function jumpToTaskNum(num) {
  const n = Number(num);
  if (!Number.isFinite(n)) return;
  const el =
    document.querySelector(`.task[data-num="${n}"]`) ||
    document.querySelector(`[data-oge-task="${n}"]`) ||
    document.getElementById(`oge-task-${n}`) ||
    document.querySelector(`#oge-ans-${n}`) ||
    document.querySelector(`[data-answer="${n}"]`);
  if (!el) return;
  const target = el.closest("article, .oge-exam-task, .task, section") || el;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  target.classList.add("is-jump-flash");
  setTimeout(() => target.classList.remove("is-jump-flash"), 900);
}

function clearLocalProgress(assignmentCode) {
  try {
    const key = progressKey(assignmentCode);
    const legacy = String(assignmentCode || "")
      .trim()
      .toUpperCase();
    const map = JSON.parse(localStorage.getItem(LS_PROGRESS) || "{}") || {};
    let changed = false;
    if (map[key]) {
      delete map[key];
      changed = true;
    }
    if (legacy && map[legacy]) {
      delete map[legacy];
      changed = true;
    }
    if (changed) localStorage.setItem(LS_PROGRESS, JSON.stringify(map));
  } catch {
    /* ignore */
  }
}

function loadLocalProgress(assignmentCode) {
  try {
    const map = JSON.parse(localStorage.getItem(LS_PROGRESS) || "{}") || {};
    const key = progressKey(assignmentCode);
    let item = map[key];
    if ((!item || typeof item !== "object") && map) {
      const legacy = map[String(assignmentCode || "").trim().toUpperCase()];
      if (legacy && typeof legacy === "object") item = legacy;
    }
    if (!item || typeof item !== "object") return null;
    return item;
  } catch {
    return null;
  }
}

function parseApiDate(value) {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const s = String(value).trim();
  if (!s) return null;
  const naive = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)$/;
  const d = new Date(naive.test(s) ? `${s}Z` : s);
  return Number.isNaN(d.getTime()) ? null : d;
}

function isAccepting(data) {
  if (!data || typeof data !== "object") return true;
  if (data.accepting_submissions === false) return false;
  if (String(data.status || "").toLowerCase() === "closed") return false;
  if (isPastDeadline(data)) return false;
  return true;
}

function isPastDeadline(data) {
  const raw = deadlineOf(data);
  if (!raw) return false;
  try {
    const d = parseApiDate(raw);
    if (!d) return false;
    return Date.now() > d.getTime();
  } catch {
    return false;
  }
}

function findCompletedCard(code) {
  const list = (state.dashboard && state.dashboard.completed) || [];
  const needle = String(code || "").trim().toUpperCase();
  return list.find((x) => String(x.code || "").toUpperCase() === needle) || null;
}

function answeredCount() {
  const questions = (state.assignment && state.assignment.questions) || [];
  let n = 0;
  for (const q of questions) {
    const a = state.answers[q.num];
    if (!a) continue;
    if (String(a.text || "").trim() || a.photoDataUrl) n += 1;
  }
  return n;
}

function formatTimerRemain(ms) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function stopWorkTimer() {
  if (state._timerTickId) {
    clearInterval(state._timerTickId);
    state._timerTickId = null;
  }
}

function syncTimerExpiry() {
  if (!state.timerEndsAt) {
    state.timerExpired = false;
    return false;
  }
  const left = state.timerEndsAt - Date.now();
  if (left <= 0) {
    state.timerExpired = true;
    return true;
  }
  state.timerExpired = false;
  return false;
}

/**
 * Timer policy: after countdown hits 0, further answer edits are blocked,
 * but the student may still press «Сдать работу» (soft lock, not hard cutoff).
 */
function startWorkTimer() {
  stopWorkTimer();
  const mins = timerMinutesOf(state.assignment);
  if (!mins) {
    state.timerEndsAt = null;
    state.timerExpired = false;
    state.timerPausedRemaining = null;
    return;
  }
  const pausedLeft = state.timerPausedRemaining;
  state.timerPausedRemaining = null;
  if (pausedLeft != null && Number.isFinite(Number(pausedLeft))) {
    const left = Math.max(0, Number(pausedLeft));
    if (left <= 0) {
      state.timerEndsAt = Date.now() - 1;
      state.timerExpired = true;
    } else {
      state.timerEndsAt = Date.now() + left;
      state.timerExpired = false;
    }
  } else {
    if (!state.startedAt) {
      state.timerEndsAt = null;
      state.timerExpired = false;
      return;
    }
    const startedMs = new Date(state.startedAt).getTime();
    if (Number.isNaN(startedMs)) {
      state.timerEndsAt = null;
      return;
    }
    state.timerEndsAt = startedMs + mins * 60 * 1000;
  }
  syncTimerExpiry();
  updateWorkMetaDom();
  if (state.timerExpired) {
    if (!state.timerPromptShown) {
      state.timerPromptShown = true;
      showToast("Время вышло — ответы зафиксированы, сдайте работу", "info");
      render();
    }
    return;
  }
  state._timerTickId = setInterval(() => {
    const expired = syncTimerExpiry();
    updateWorkMetaDom();
    if (expired) {
      stopWorkTimer();
      if (!state.timerPromptShown) {
        state.timerPromptShown = true;
        showToast("Время вышло — ответы зафиксированы, сдайте работу", "info");
      }
      render();
    }
  }, 1000);
}

function workProgressLabel(answered, total) {
  const m = Math.max(0, Number(total) || 0);
  const x = Math.max(0, Math.min(m, Number(answered) || 0));
  const left = Math.max(0, m - x);
  if (x === 0 && m > 0) return `Осталось ответить: ${left}`;
  return `Отвечено ${x} из ${m} · осталось ${left}`;
}

function updateWorkMetaDom() {
  const prog = document.getElementById("work-progress");
  if (prog) {
    const m = questionCountOf(state.assignment);
    prog.textContent = workProgressLabel(answeredCount(), m);
  }
  const timerEl = document.getElementById("work-timer");
  if (!timerEl) return;
  const mins = timerMinutesOf(state.assignment);
  if (!mins) return;
  const wrap = timerEl.closest(".work-timer-wrap") || timerEl.closest(".work-timer-dock");
  const applyTone = (expired, urgent) => {
    timerEl.classList.toggle("is-expired", expired);
    timerEl.classList.toggle("is-urgent", urgent);
    if (wrap) {
      wrap.classList.toggle("is-expired", expired);
      wrap.classList.toggle("is-urgent", urgent);
    }
  };
  if (!state.timerEndsAt) {
    timerEl.textContent = formatTimerRemain(mins * 60 * 1000);
    applyTone(false, false);
    return;
  }
  const left = state.timerEndsAt - Date.now();
  if (left <= 0) {
    timerEl.textContent = "00:00";
    applyTone(true, false);
    timerEl.setAttribute("aria-label", "Время вышло");
  } else {
    timerEl.textContent = formatTimerRemain(left);
    applyTone(false, left <= 60_000);
    timerEl.setAttribute("aria-label", `Осталось ${formatTimerRemain(left)}`);
  }
}

function resultFromCompletedCard(item) {
  if (!item) return null;
  return {
    score: item.score,
    max_score: item.max_score,
    status: item.status || "submitted",
    ai_review: item.ai_review || null,
    already_submitted: true,
    has_review: !!item.has_review,
    title: item.title,
    code: item.code,
    teacher_score: item.teacher_score ?? null,
    teacher_comment: item.teacher_comment || null,
    teacher_reviewed_at: item.teacher_reviewed_at || null,
    oge: item.oge || (item.ai_review && item.ai_review.oge) || null,
    subject: item.subject || null,
    answers_locked: !!item.answers_locked,
    hide_answers: !!item.hide_answers,
    deadline: item.deadline || item.deadline_at || null,
  };
}

function showToast(message, type = "info") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => {
    el.classList.add("is-out");
    setTimeout(() => el.remove(), 280);
  }, 2800);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function studentOgeResult(source) {
  if (!source) return null;
  if (source.oge && source.oge.grade != null) return source.oge;
  if (source.ai_review && source.ai_review.oge && source.ai_review.oge.grade != null) {
    return source.ai_review.oge;
  }
  if (typeof OgeGrade === "undefined") return null;
  const review = source.ai_review || {};
  return OgeGrade.calculate({
    subject: source.subject || state.subject,
    items: Array.isArray(review.items) ? review.items : [],
    score: source.teacher_score != null ? source.teacher_score : source.score,
    teacherScore: source.teacher_score,
    review,
  });
}

function renderOgeScoreCard(source) {
  const oge = studentOgeResult(source);
  if (!oge || oge.grade == null) return "";
  const mark = String(oge.grade);
  const max = oge.max_score || 31;
  const score = oge.score != null ? oge.score : 0;
  const pct = max ? Math.max(0, Math.min(100, Math.round((100 * score) / max))) : 0;
  const tag = oge.subject === "russian" ? oge.literacy_tag : oge.geometry_tag;
  const tagCls = oge.failed_geometry || oge.failed_literacy ? "is-bad" : String(tag || "").indexOf("проверке") >= 0 || String(tag || "").indexOf("не выставлена") >= 0 ? "is-wait" : "is-ok";
  const mods = (oge.modules || [])
    .map(
      (m) => `
      <div class="oge-score-mod">
        <span>${escapeHtml(m.label)}</span>
        <strong>${m.pending && m.id === "literacy" && oge.literacy_unknown ? "—" : `${m.earned} / ${m.max}`}</strong>
      </div>`
    )
    .join("");
  return `
    <div class="oge-score-card glass">
      <div class="oge-score-mark is-${escapeHtml(mark)}" aria-label="Оценка ${escapeHtml(mark)}">${escapeHtml(mark)}</div>
      <div class="oge-score-main">
        <p class="oge-score-kicker">Результат ОГЭ</p>
        <div class="oge-score-bar" aria-hidden="true"><i style="width:${pct}%"></i></div>
        <p class="oge-score-meta">${escapeHtml(String(score))} / ${escapeHtml(String(max))} баллов</p>
        ${tag ? `<span class="oge-score-tag ${tagCls}">${escapeHtml(tag)}</span>` : ""}
        ${mods ? `<div class="oge-score-mods">${mods}</div>` : ""}
      </div>
    </div>
  `;
}

function studentSubjectCode(assignment) {
  const a = assignment || state.assignment || {};
  const raw = a.subject_code || a.subject || state.subject || "";
  const s = String(raw).toLowerCase().replace(/ё/g, "е").trim();
  if (!s) return "";
  if (s === "math" || s === "mathematics" || s === "math_base" || s.indexOf("матем") >= 0) {
    return "math";
  }
  if (
    s === "russian" ||
    s === "rus" ||
    s === "ru" ||
    s.indexOf("русск") >= 0 ||
    s.indexOf("russian") >= 0
  ) {
    return "russian";
  }
  return s;
}

function formatTaskHtml(raw, task) {
  const subj = studentSubjectCode();
  const asTask =
    task && typeof task === "object"
      ? task
      : typeof raw === "object"
        ? raw
        : null;
  const useRus =
    subj !== "math" &&
    typeof OgeRusUI !== "undefined" &&
    typeof OgeRusUI.isOgeRusTask === "function" &&
    asTask &&
    OgeRusUI.isOgeRusTask(asTask);
  if (useRus && typeof OgeRusUI.formatTaskTextHtml === "function") {
    return OgeRusUI.formatTaskTextHtml(asTask || raw);
  }
  const text =
    asTask && typeof asTask === "object" ? String(asTask.text || "") : String(raw || "");
  if (
    typeof MathOgeUI !== "undefined" &&
    typeof MathOgeUI.formatRichText === "function"
  ) {
    return MathOgeUI.formatRichText(text);
  }
  if (typeof formatMathText === "function") return formatMathText(text);
  return escapeHtml(text).replace(/\$/g, "");
}

function payloadImagesHtml(q) {
  const p = q?.payload || {};
  const urls = Array.isArray(p.image_urls) ? p.image_urls : [];
  if (!urls.length) return "";
  return (
    `<div class="task-media" aria-label="Рисунок к заданию">` +
    urls
      .map((u) => {
        const src = String(u || "").trim();
        if (!src || /^javascript:/i.test(src)) return "";
        return `<img class="task-media-img" src="${escapeHtml(src)}" alt="Рисунок" loading="lazy" />`;
      })
      .filter(Boolean)
      .join("") +
    `</div>`
  );
}

function figureHtml(q) {
  const p = q?.payload || {};
  if (p.oge_rus || p.ui === "oge_rus" || p.ui === "listening" || p.ui === "matching" || p.ui === "essay_choice") {
    return "";
  }
  const n = Number(q?.num);
  if (p.math_context && n >= 1 && n <= 5) return "";
  const kind = q?.figure_kind;
  const svg = q?.figure_svg || "";
  const safe = [
    "rect",
    "triangle",
    "box3d",
    "circle",
    "numberline",
    "graph_linear",
    "graph_parabola",
    "graph_hyperbola",
    "graph_cubic",
    "graph_match",
    "plan",
    "grid",
    "scheme",
    "asset",
  ];
  if (!kind || !safe.includes(kind)) return "";
  if (!/class="[^"]*\b(fipi-fig|geo-fig)\b/.test(svg)) return "";
  if (!/viewBox=["']0 0 \d+(?:\.\d+)? \d+(?:\.\d+)?["']/.test(svg)) return "";
  return `<div class="task-figure" data-figure="${escapeHtml(kind)}" role="button" tabindex="0" title="Увеличить чертёж" aria-label="Увеличить чертёж">${svg}</div>`;
}

function closeFigureLightbox() {
  document.getElementById("figure-lightbox")?.remove();
  document.documentElement.classList.remove("figure-lightbox-open");
}

function openFigureLightbox(figEl) {
  const svg = figEl?.querySelector?.("svg");
  if (!svg) return;
  closeFigureLightbox();
  const clone = svg.cloneNode(true);
  clone.removeAttribute("width");
  clone.removeAttribute("height");
  clone.classList.add("figure-lightbox-svg");
  const overlay = document.createElement("div");
  overlay.id = "figure-lightbox";
  overlay.className = "figure-lightbox";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Чертёж");
  overlay.innerHTML = `
    <button type="button" class="figure-lightbox-close" aria-label="Закрыть">×</button>
    <div class="figure-lightbox-stage"></div>
  `;
  overlay.querySelector(".figure-lightbox-stage").appendChild(clone);
  document.body.appendChild(overlay);
  document.documentElement.classList.add("figure-lightbox-open");
  overlay.querySelector(".figure-lightbox-close")?.focus();
}

function installFigureLightbox() {
  if (window.__figureLightboxInstalled) return;
  window.__figureLightboxInstalled = true;

  document.addEventListener(
    "click",
    (e) => {
      const lb = e.target.closest("#figure-lightbox");
      if (lb) {
        const closeBtn = e.target.closest(".figure-lightbox-close");
        const onBackdrop = e.target.id === "figure-lightbox";
        if (closeBtn || onBackdrop) {
          e.preventDefault();
          e.stopPropagation();
          closeFigureLightbox();
        }
        return;
      }
      const fig = e.target.closest(".task-figure");
      if (!fig || fig.closest("#figure-lightbox")) return;
      e.preventDefault();
      e.stopPropagation();
      openFigureLightbox(fig);
    },
    true
  );

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && document.getElementById("figure-lightbox")) {
      e.preventDefault();
      closeFigureLightbox();
      return;
    }
    if (e.key !== "Enter" && e.key !== " ") return;
    const fig = e.target.closest?.(".task-figure");
    if (!fig || fig.closest("#figure-lightbox")) return;
    e.preventDefault();
    openFigureLightbox(fig);
  });
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(detailMessage(data, "Ошибка запроса"));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function detailMessage(data, fallback) {
  const d = data && data.detail;
  if (typeof d === "string" && d.trim()) return d;
  if (d && typeof d === "object" && !Array.isArray(d) && d.message) return String(d.message);
  if (Array.isArray(d) && d.length) {
    const first = d[0];
    if (typeof first === "string") return first;
    if (first && first.msg) return String(first.msg);
  }
  if (data && data.message) return String(data.message);
  return fallback;
}

function closedDetail(data) {
  const d = data && data.detail;
  if (d && typeof d === "object" && !Array.isArray(d) && d.closed) return d;
  return null;
}

/** GET /api/assignments/{code} with status for 404 / 403 / closed flag. */
async function fetchAssignmentByCode(code) {
  const name = String(state.name || "").trim();
  const qs = name ? `?student_name=${encodeURIComponent(name)}` : "";
  const res = await fetch(`/api/assignments/${encodeURIComponent(code)}${qs}`);
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

function applyClosedPreview(data) {
  state.closed = true;
  state.codeError = "";
  state.nameError = "";
  const detail = data && data.detail && typeof data.detail === "object" ? data.detail : data;
  state.previewTitle = (detail && detail.title) || (data && data.title) || "";
  state.previewSubject = (detail && detail.subject) || (data && data.subject) || "";
  state.assignment = null;
}

function applySessionFromJoin(data) {
  state.studentId = data.student_id || state.studentId || uuidClient();
  state.name = data.student_name || state.name;
  state.classCode = data.class_code || state.classCode;
  state.className = data.class_name || "";
  state.subject = data.subject || "";
  state.exam = data.exam || "";
  state.code = state.classCode;
  saveSession({
    student_id: state.studentId,
    student_name: state.name,
    class_code: state.classCode,
    class_name: state.className,
    subject: state.subject,
    exam: state.exam,
    assignment_code: data.assignment && data.assignment.code,
  });
  state.savedEntry = { code: state.classCode, name: state.name };
}

function navigateStudent(path, { replace = false } = {}) {
  const url = path.startsWith("/") ? path : `/${path}`;
  if (replace) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
}

function pathWantsDashboard() {
  const path = (location.pathname || "").replace(/\/+$/, "") || "/";
  const params = new URLSearchParams(location.search);
  if (params.get("view") === "dashboard") return true;
  return path === "/student/dashboard" || path.endsWith("/student/dashboard");
}

function pathWantsJoin() {
  const path = (location.pathname || "").replace(/\/+$/, "") || "/";
  return path === "/student/join" || path.endsWith("/student/join");
}

function enterWork() {
  if (!state.assignment) return;
  (state.assignment.questions || []).forEach((q) => ensureAnswer(q.num, q.part));
  if (!state.startedAt) {
    state.startedAt = new Date().toISOString();
  }
  state.workStarted = true;
  state.step = "work";
  if (state.assignment.code) {
    saveLocalProgress(state.assignment.code, state.answers, state.startedAt);
  }
}

function hasWorkProgress() {
  return Object.values(state.answers || {}).some(
    (a) => (a && String(a.text || "").trim()) || (a && a.photoDataUrl)
  );
}

function questionCountOf(assignment) {
  const a = assignment || state.assignment || {};
  if (typeof a.question_count === "number" && a.question_count > 0) return a.question_count;
  if (typeof a.questions_count === "number" && a.questions_count > 0) return a.questions_count;
  return (a.questions || []).length;
}

function timerMinutesOf(assignment) {
  const a = assignment || {};
  const n = a.time_limit_minutes ?? a.timer_minutes;
  const v = Number(n);
  return Number.isFinite(v) && v > 0 ? v : null;
}

function deadlineOf(assignment) {
  const a = assignment || {};
  return a.deadline_at || a.deadline || null;
}

function formatDeadline(value) {
  if (!value) return "";
  try {
    const d = parseApiDate(value);
    if (!d) return String(value);
    return d.toLocaleString("ru-RU", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(value);
  }
}

function answersLockedOf(item) {
  return !!(item && item.answers_locked);
}

function reviewLockedHint(item) {
  const d = deadlineOf(item);
  return d
    ? `Разбор откроется ${formatDeadline(d)}`
    : "Разбор откроется после закрытия приёма";
}

function formatDateShort(value) {
  if (!value) return "";
  try {
    const d = parseApiDate(value);
    if (!d) return String(value);
    return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return String(value);
  }
}

function firstNameOf(fullName) {
  const parts = String(fullName || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length >= 2) return parts[1];
  return parts[0] || "ученик";
}

function examLabel(exam) {
  const e = String(exam || "").toLowerCase();
  if (e === "oge") return "ОГЭ";
  if (e === "ege") return "ЕГЭ";
  if (e === "vpr") return "ВПР";
  if (e === "school") return "Школа";
  return exam || "";
}

function subjectDativeLabel() {
  return studentSubjectCode() === "russian" ? "Русскому языку" : "Математике";
}

function nextOgeDate() {
  const rus = studentSubjectCode() === "russian";
  const month = 5;
  const day = rus ? 9 : 2;
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  let exam = new Date(2026, month, day);
  while (exam < today) {
    exam = new Date(exam.getFullYear() + 1, month, day);
  }
  return exam;
}

function daysUntilDate(date) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  return Math.max(0, Math.round((target - today) / 86400000));
}

function formatRuDayMonth(date) {
  const months = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
  ];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

function formatRuExamDate(date) {
  return `${formatRuDayMonth(date)} ${date.getFullYear()}`;
}

function ogeGoalMeta() {
  const rus = studentSubjectCode() === "russian";
  return rus ? { max: 33, five: 29 } : { max: 31, five: 22 };
}

function latestPrimaryScore(data) {
  for (const it of data.completed || []) {
    if (isRnoItem(it)) continue;
    const oge = studentOgeResult({ ...it, subject: it.subject || state.subject });
    if (oge && oge.score != null && Number.isFinite(Number(oge.score))) return Number(oge.score);
    if (it.score != null && Number.isFinite(Number(it.score))) return Number(it.score);
  }
  return null;
}

function renderOgeCountdown() {
  const date = nextOgeDate();
  const days = daysUntilDate(date);
  const dayWord = ruPlural(days, "день", "дня", "дней");
  return `
    <div class="oge-count-chip">
      <span>🎯 До ОГЭ по ${escapeHtml(subjectDativeLabel())}: ${days} ${dayWord} (${escapeHtml(
        formatRuExamDate(date)
      )})</span>
    </div>
  `;
}

function renderGoalCard(data) {
  const meta = ogeGoalMeta();
  const raw = latestPrimaryScore(data);
  const score = raw == null ? 0 : Math.max(0, Math.min(meta.max, raw));
  const pct = Math.round((100 * Math.min(score, meta.five)) / meta.five);
  let foot = "Сдай первый вариант — шкала оживёт";
  let cls = "";
  if (raw != null && score >= meta.five) {
    foot = "🟢 Цель по оценке 5 достигнута";
    cls = "is-ok";
  } else if (raw != null) {
    const left = Math.max(0, meta.five - score);
    foot = `Ещё ${left} ${ruPlural(left, "балл", "балла", "баллов")} до оценки 5`;
    cls = "is-warn";
  }
  return `
    <article class="student-stat student-goal ${cls}">
      <span class="student-stat-label">Цель ОГЭ</span>
      <div class="student-goal-title">Оценка 5 · ${escapeHtml(String(meta.max))}+ балла</div>
      <div class="student-stat-bar" role="progressbar" aria-valuemin="0" aria-valuemax="${meta.five}" aria-valuenow="${Math.min(
        score,
        meta.five
      )}" aria-label="Цель ОГЭ">
        <i style="width:${pct}%"></i>
      </div>
      <span class="student-stat-foot ${cls}">${raw == null ? foot : `${score} из ${meta.five} б. · ${foot}`}</span>
    </article>
  `;
}

function brandBlockHtml() {
  return `
    <div class="brand-block">
      <div class="brand">EduSense <span class="beta-badge" title="Open beta">BETA</span></div>
      <p class="brand-line">ОГЭ · Математика и Русский</p>
    </div>
  `;
}

function ensureAnswer(num, part) {
  if (!state.answers[num]) {
    state.answers[num] = {
      mode: part === 2 ? "photo" : "text",
      text: "",
      photoDataUrl: "",
    };
  }
  return state.answers[num];
}

/* ---------- Render modules (TZ mapping) ---------- */

function classLineText() {
  return [state.className || state.classCode || "—", examLabel(state.exam), state.subject]
    .filter(Boolean)
    .join(" · ");
}

function isRnoItem(item) {
  return isRnoTitle((item && item.title) || "");
}

function activeVariantItems(list) {
  return (list || []).filter((it) => !isRnoItem(it));
}

function activeRnoItems(list) {
  return (list || []).filter((it) => isRnoItem(it));
}

function ruPlural(n, one, few, many) {
  const abs = Math.abs(Number(n) || 0) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return many;
  if (last === 1) return one;
  if (last >= 2 && last <= 4) return few;
  return many;
}

function isoDayKey(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function streakVisitKey() {
  return `${state.studentId || state.name || "anon"}:${String(state.classCode || "").toUpperCase()}`;
}

function streakFromDaySet(days) {
  if (!days || !days.size) return 0;
  const cursor = new Date();
  cursor.setHours(0, 0, 0, 0);
  if (!days.has(isoDayKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (days.has(isoDayKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function loadVisitDaySet() {
  try {
    const bag = JSON.parse(localStorage.getItem(LS_STREAK_VISITS) || "{}") || {};
    const list = bag[streakVisitKey()];
    return new Set(Array.isArray(list) ? list : []);
  } catch {
    return new Set();
  }
}

function noteStreakVisit() {
  const days = loadVisitDaySet();
  days.add(isoDayKey(new Date()));
  try {
    const bag = JSON.parse(localStorage.getItem(LS_STREAK_VISITS) || "{}") || {};
    bag[streakVisitKey()] = [...days].sort().slice(-400);
    localStorage.setItem(LS_STREAK_VISITS, JSON.stringify(bag));
  } catch {
    /* ignore quota */
  }
  return days;
}

function studentStreakDays(completed) {
  const days = new Set();
  (completed || []).forEach((it) => {
    const d = parseApiDate(it.submitted_at);
    if (!d) return;
    days.add(isoDayKey(d));
  });
  return streakFromDaySet(days);
}

function homeStreakDays(completed) {
  const days = noteStreakVisit();
  (completed || []).forEach((it) => {
    const d = parseApiDate(it.submitted_at);
    if (d) days.add(isoDayKey(d));
  });
  return Math.max(1, streakFromDaySet(days));
}

function streakIgniteStorageKey() {
  return `edusense_streak_ignite:${streakVisitKey()}:${isoDayKey(new Date())}`;
}

function streakIgnitePending() {
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return false;
  }
  try {
    return sessionStorage.getItem(streakIgniteStorageKey()) !== "done";
  } catch {
    return true;
  }
}

function markStreakIgniteDone() {
  try {
    sessionStorage.setItem(streakIgniteStorageKey(), "done");
  } catch {
    /* ignore */
  }
}

function streakLitToday(completed) {
  const today = isoDayKey(new Date());
  return (completed || []).some((it) => {
    const d = parseApiDate(it.submitted_at);
    return d && isoDayKey(d) === today;
  });
}

function formatXp(n) {
  return String(Math.max(0, Math.round(Number(n) || 0))).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function latestThresholds(data) {
  const geo = { score: null, need: 2, pending: false };
  const lit = { score: null, need: 4, pending: false };
  for (const it of data.completed || []) {
    const oge = studentOgeResult({ ...it, subject: it.subject || state.subject });
    if (!oge) continue;
    const subj = oge.subject || studentSubjectCode({ subject: it.subject || state.subject });
    if (geo.score == null && subj === "math" && (oge.geometry_score != null || oge.geometry_tag)) {
      geo.score = oge.geometry_score == null ? null : Number(oge.geometry_score);
      geo.pending = !!oge.geometry_pending;
    }
    if (lit.score == null && subj === "russian" && (oge.literacy_score != null || oge.literacy_tag)) {
      lit.score = oge.literacy_score == null ? null : Number(oge.literacy_score);
      lit.pending = !!oge.literacy_unknown;
    }
    if (geo.score != null && lit.score != null) break;
  }
  return { geo, lit };
}

function renderThresholdBar(label, icon, rec) {
  const need = rec.need;
  const raw = rec.score;
  const pending = rec.pending;
  const shown = raw == null ? 0 : Math.max(0, Math.min(need, Number(raw) || 0));
  const pct = Math.round((100 * shown) / need);
  let foot = "Пока нет сдач по этому предмету";
  let cls = "";
  if (pending) {
    foot = "На проверке";
    cls = "is-wait";
  } else if (raw != null && shown >= need) {
    foot = "🟢 Порог пройден";
    cls = "is-ok";
  } else if (raw != null) {
    const left = Math.max(0, need - shown);
    foot = `⚠️ Нужен ещё ${left} ${ruPlural(left, "балл", "балла", "баллов")}!`;
    cls = "is-warn";
  }
  const value = raw == null ? "—" : `${shown}/${need} б.`;
  return `
    <article class="threshold-bar ${cls}">
      <div class="threshold-bar-top">
        <span>${icon} ${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
      </div>
      <div class="student-stat-bar" role="progressbar" aria-valuemin="0" aria-valuemax="${need}" aria-valuenow="${shown}">
        <i style="width:${pct}%"></i>
      </div>
      <span class="student-stat-foot ${cls}">${escapeHtml(foot)}</span>
    </article>
  `;
}

function submissionsOnTime(completed) {
  const rows = (completed || []).filter((it) => deadlineOf(it) && it.submitted_at);
  if (!rows.length) return true;
  return rows.every((it) => {
    const sub = parseApiDate(it.submitted_at);
    const dl = parseApiDate(deadlineOf(it));
    return !!(sub && dl && sub.getTime() <= dl.getTime());
  });
}

function accuracyThemeLabel() {
  return studentSubjectCode({ subject: state.subject }) === "russian" ? "Русский" : "Геометрия";
}

function renderInactiveLivePin() {
  const cells = [0, 1, 2, 3, 4, 5]
    .map((i) => {
      const dash = i === 3 ? `<span class="live-pin-dash" aria-hidden="true">-</span>` : "";
      return `${dash}<span class="live-pin-cell">_</span>`;
    })
    .join("");
  return `<div class="live-pin-boxes is-disabled" aria-hidden="true">${cells}</div>`;
}

function renderLiveModal() {
  if (!state.showLive) return "";
  return `
    <div class="modal-backdrop invite-backdrop" id="live-backdrop">
      <div class="modal-card invite-card live-pin-card" role="dialog" aria-modal="true" aria-labelledby="live-pin-title">
        <span class="invite-glow" aria-hidden="true"></span>
        <div class="invite-inner">
          <h3 class="invite-title" id="live-pin-title">🚀 EduSense Live — Уроки в реальном времени</h3>
          <p class="coming-soon-lead">Подключайтесь к интерактивным урокам учителя с доски по 6-значному PIN-коду прямо со смартфона.</p>
          <div class="coming-soon-pin">
            <span class="student-hero-pin-label">PIN Live-урока</span>
            ${renderInactiveLivePin()}
          </div>
          <span class="invite-status">⏳ В разработке · Скоро в EduSense 2.0</span>
          <button type="button" class="btn btn-ghost invite-close" id="btn-close-live">Закрыть</button>
        </div>
      </div>
    </div>
  `;
}

function renderStudentStats(stats, { variantsN = null, data = null } = {}) {
  const s = stats || {};
  const dash = data || state.dashboard || {};
  const done = s.completed_count ?? (dash.completed || []).length;
  const activeN =
    variantsN != null
      ? variantsN
      : activeVariantItems(dash.active || []).length;
  const rus = studentSubjectCode() === "russian";
  const th = latestThresholds(dash);
  const threshold = rus
    ? renderThresholdBar("Грамотность (Русский)", "✏️", th.lit)
    : renderThresholdBar("Геометрия (Порог 2 балла)", "📐", th.geo);
  return `
    <section class="student-stats" aria-label="Статистика">
      <article class="student-stat">
        <span class="student-stat-label">Открыто к сдаче</span>
        <div class="student-stat-num is-open">${activeN}</div>
        <span class="student-stat-foot">${ruPlural(activeN, "вариант", "варианта", "вариантов")}</span>
      </article>
      <article class="student-stat">
        <span class="student-stat-label">Сдано работ</span>
        <div class="student-stat-num">${done}</div>
        <span class="student-stat-foot">${ruPlural(done, "работа", "работы", "работ")}</span>
      </article>
      ${renderGoalCard(dash)}
    </section>
    <section class="student-thresholds" aria-label="Порог ОГЭ">
      ${threshold}
    </section>
  `;
}

function renderDashTaskCard(item, { mode = "active" } = {}) {
  const qCount = questionCountOf(item);
  const timer = timerMinutesOf(item);
  const deadline = deadlineOf(item);
  const inProgress = mode === "active" && hasLocalProgress(item.code);
  const rno = isRnoItem(item);
  const exam = examLabel(item.exam || state.exam) || "ОГЭ";
  const chip = rno ? "🎯 РНО" : `📝 ${exam} · ${qCount} ${ruPlural(qCount, "задание", "задания", "заданий")}`;
  const timerLabel = timer ? `⏳ Лимит: ${timer} мин` : "⏳ Без лимита";
  const cta = inProgress ? "Продолжить" : "Начать решение";

  if (mode === "completed") {
    const score = item.score != null ? item.score : "—";
    const max = item.max_score != null ? item.max_score : "—";
    const oge = studentOgeResult({ ...item, subject: item.subject || state.subject });
    const grade = oge?.grade || item.grade;
    const gradeBit = grade ? ` · оценка ${escapeHtml(String(grade))}` : "";
    return `
      <article class="glass dash-card dash-card-done reveal" data-code="${escapeHtml(item.code)}">
        <div class="dash-card-head">
          <h3 class="dash-card-title">${escapeHtml(item.title || "Работа")}</h3>
          <span class="status-chip done">Сдано</span>
        </div>
        <p class="dash-card-meta">${escapeHtml(formatDateShort(item.submitted_at))} · ${escapeHtml(
          String(score)
        )}/${escapeHtml(String(max))}${gradeBit}</p>
        ${
          answersLockedOf(item)
            ? `<button type="button" class="btn btn-secondary btn-compact" data-review-locked="${escapeHtml(
                item.code
              )}">${escapeHtml(reviewLockedHint(item))}</button>`
            : `<button type="button" class="btn btn-secondary btn-compact" data-review="${escapeHtml(
                item.code
              )}">Посмотреть ошибки</button>`
        }
      </article>
    `;
  }

  return `
    <article class="task-mod reveal ${rno ? "is-rno" : "is-kim"}" data-code="${escapeHtml(item.code)}">
      <div class="task-mod-top">
        <span class="task-mod-chip">${escapeHtml(chip)}</span>
        <span class="task-mod-timer">${escapeHtml(timerLabel)}</span>
      </div>
      <h3 class="task-mod-title">${escapeHtml(item.title || "Работа")}</h3>
      <p class="task-mod-meta">${
        inProgress ? "Черновик сохранён — можно продолжить" : deadline ? `до ${escapeHtml(formatDeadline(deadline))}` : "Открыто к сдаче"
      }</p>
      <button type="button" class="task-mod-cta" data-start="${escapeHtml(item.code)}">${cta}</button>
    </article>
  `;
}

function renderActiveSection(active) {
  if (!active.length) {
    return `<div class="empty-active glass" role="status">
         <p class="empty-title">Пока нет активных вариантов</p>
         <p class="sub">Когда учитель выдаст КИМ, он появится здесь. РНО смотрите в «Мой прогресс».</p>
         <button type="button" class="btn btn-secondary btn-compact" data-tab-jump="progress" style="margin-top:12px">Мой прогресс</button>
       </div>`;
  }
  return `<div class="dash-list task-mod-grid">${active.map((it) => renderDashTaskCard(it, { mode: "active" })).join("")}</div>`;
}

function renderCompletedSection(completed) {
  if (!completed.length) {
    return `<div class="empty-active glass" role="status">
         <p class="empty-title">Сданных работ пока нет</p>
         <p class="sub">Сдайте первый вариант — оценка появится здесь.</p>
         <button type="button" class="btn btn-primary btn-compact btn-neon" data-tab-jump="home" style="margin-top:12px">К вариантам</button>
       </div>`;
  }
  return `<div class="dash-list">${completed
    .map((it) => renderDashTaskCard(it, { mode: "completed" }))
    .join("")}</div>`;
}

function renderLiveTeaser() {
  return `
    <button type="button" class="student-hero-pin student-hero-live-teaser" data-nav-action="live">
      <span class="student-hero-pin-label">Live-урок с доски</span>
      ${renderInactiveLivePin()}
      <span class="student-hero-live-soon">Скоро в EduSense 2.0</span>
    </button>
  `;
}

function renderStreakCard(data) {
  const streak = homeStreakDays(data.completed || []);
  const ignite = streak === 1 && streakIgnitePending();
  const days = `${streak} ${ruPlural(streak, "ДЕНЬ", "ДНЯ", "ДНЕЙ")}`;
  const cap = streak === 1 ? "Первый день" : "Стрик горит";
  return `
    <aside class="streak-card is-lit${ignite ? " is-ignite" : ""}">
      <span class="streak-card-burst" aria-hidden="true"></span>
      <span class="streak-sparks" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
      <span class="streak-card-flame" aria-hidden="true">🔥</span>
      <strong class="streak-card-days">${escapeHtml(days)}</strong>
      <span class="streak-card-cap">${escapeHtml(cap)}</span>
    </aside>
  `;
}

function fallbackLeaderboard(data) {
  const xp = (data.completed || []).reduce((sum, it) => sum + (Number(it.score) || 0) * 100, 0);
  const short = _displayShortName(state.name);
  return [
    {
      rank: 1,
      name: state.name,
      short_name: short,
      xp: Math.round(xp),
      streak: studentStreakDays(data.completed || []),
      you: true,
    },
  ];
}

function _displayShortName(name) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length >= 2) return `${parts[0]} ${parts[1][0]}.`;
  return parts[0] || "Ученик";
}

function formatClassTitle(name, fallback) {
  const raw = String(name || "").trim();
  if (!raw) return fallback || "классе";
  const m = raw.match(/^(\d+)\s*[-.]?\s*['"«»]?\s*([А-ЯЁа-яёA-Za-z])\s*['"«»]?\s*$/u);
  if (m) return `${m[1]} '${m[2].toUpperCase()}'`;
  return raw;
}

function bonusXpStorageKey() {
  return `${state.studentId || state.name || "anon"}:${String(state.classCode || "").toUpperCase()}`;
}

function loadBonusXp() {
  try {
    const bag = JSON.parse(localStorage.getItem(LS_BONUS_XP) || "{}") || {};
    return Math.max(0, Number(bag[bonusXpStorageKey()]) || 0);
  } catch {
    return 0;
  }
}

function addBonusXp(amount) {
  const n = Math.max(0, Math.round(Number(amount) || 0));
  if (!n) return loadBonusXp();
  try {
    const bag = JSON.parse(localStorage.getItem(LS_BONUS_XP) || "{}") || {};
    const key = bonusXpStorageKey();
    bag[key] = Math.max(0, Number(bag[key]) || 0) + n;
    localStorage.setItem(LS_BONUS_XP, JSON.stringify(bag));
    return bag[key];
  } catch {
    return loadBonusXp();
  }
}

function loadWarmupResult() {
  try {
    const raw = JSON.parse(localStorage.getItem(LS_WARMUP) || "null");
    if (!raw || raw.day !== isoDayKey(new Date()) || raw.key !== bonusXpStorageKey()) return null;
    return raw;
  } catch {
    return null;
  }
}

function saveWarmupResult(payload) {
  try {
    localStorage.setItem(
      LS_WARMUP,
      JSON.stringify({
        day: isoDayKey(new Date()),
        key: bonusXpStorageKey(),
        ...payload,
      })
    );
  } catch {
    /* ignore */
  }
}

function dailyGoalProgress(data) {
  const today = isoDayKey(new Date());
  const done = (data.completed || []).filter((it) => {
    if (isRnoItem(it)) return false;
    const d = parseApiDate(it.submitted_at);
    return d && isoDayKey(d) === today;
  }).length;
  const need = 2;
  return { done: Math.min(done, need), need, raw: done };
}

function warmupQuizSpec() {
  if (studentSubjectCode() === "math") {
    return {
      title: "⚡ Быстрый срез дня: Геометрия (+50 XP)",
      question: "Чему равен третий угол треугольника, если два других — 70° и 60°?",
      options: [
        { id: 1, label: "1. 40°" },
        { id: 2, label: "2. 50°" },
        { id: 3, label: "3. 60°" },
      ],
      correct: 2,
      xp: 50,
    };
  }
  return {
    title: "⚡ Быстрый срез дня: Орфография (+50 XP)",
    question: "В каком слове пишется НН?",
    options: [
      { id: 1, label: "1. Песча..ый" },
      { id: 2, label: "2. Стекля..ый" },
      { id: 3, label: "3. Кожа..ый" },
    ],
    correct: 2,
    xp: 50,
  };
}

function renderDailyGoal(data) {
  const g = dailyGoalProgress(data);
  const pct = Math.round((100 * g.done) / g.need);
  return `
    <div class="daily-goal">
      <span>📊 Дневная цель: ${g.done} из ${g.need} ${ruPlural(g.need, "вариант", "варианта", "вариантов")} решено</span>
      <div class="daily-goal-bar" role="progressbar" aria-valuemin="0" aria-valuemax="${g.need}" aria-valuenow="${g.done}">
        <i style="width:${pct}%"></i>
      </div>
    </div>
  `;
}

function renderWarmupWidget() {
  const quiz = warmupQuizSpec();
  const saved = loadWarmupResult();
  const locked = !!(saved && saved.answered);
  const picked = locked ? Number(saved.choice) : null;
  const ok = locked ? !!saved.correct : false;
  return `
    <section class="warmup-card reveal${locked ? (ok ? " is-ok" : " is-bad") : ""}">
      <div class="warmup-head">
        <h3>${escapeHtml(quiz.title)}</h3>
        ${locked ? `<span class="warmup-chip">${ok ? "+50 XP" : "Попробуй завтра"}</span>` : ""}
      </div>
      <p class="warmup-q">${escapeHtml(quiz.question)}</p>
      <div class="warmup-options">
        ${quiz.options
          .map((opt) => {
            let cls = "";
            if (locked) {
              if (opt.id === quiz.correct) cls = "is-correct";
              else if (opt.id === picked) cls = "is-wrong";
            }
            return `<button type="button" class="warmup-opt ${cls}" data-warmup="${opt.id}" ${
              locked ? "disabled" : ""
            }>${escapeHtml(opt.label)}</button>`;
          })
          .join("")}
      </div>
      ${
        locked
          ? `<p class="warmup-foot">${
              ok
                ? "Верно! XP уже в лидерборде класса."
                : `Правильный ответ: ${escapeHtml(quiz.options.find((o) => o.id === quiz.correct).label)}`
            }</p>`
          : `<p class="warmup-foot">Ответь правильно — получишь +${quiz.xp} XP в топ недели</p>`
      }
    </section>
  `;
}

function withBonusXpRows(rows) {
  const bonus = loadBonusXp();
  const enriched = (rows || []).map((row) => ({
    ...row,
    xp: Math.max(0, Number(row.xp) || 0) + (row.you ? bonus : 0),
  }));
  enriched.sort((a, b) => b.xp - a.xp || b.streak - a.streak || String(a.name || "").localeCompare(String(b.name || ""), "ru"));
  return enriched.map((row, i) => ({ ...row, rank: i + 1 }));
}

function renderClassBoard(data) {
  const raw = withBonusXpRows(
    Array.isArray(data.leaderboard) && data.leaderboard.length ? data.leaderboard : fallbackLeaderboard(data)
  );
  const limit = state.showFullBoard ? raw.length : Math.min(5, raw.length);
  const rows = raw.slice(0, limit);
  const medals = ["🥇", "🥈", "🥉"];
  const klass = formatClassTitle(state.className, state.classCode || "классе");
  return `
    <aside class="class-board reveal">
      <div class="class-board-head">
        <h2>🏆 Топ недели в ${escapeHtml(klass)}</h2>
        <button type="button" class="btn btn-ghost btn-compact" id="btn-board-all">${
          state.showFullBoard ? "Свернуть" : "Все"
        }</button>
      </div>
      <ol class="class-board-list">
        ${rows
          .map((row) => {
            const medal = medals[row.rank - 1] || "";
            const label = row.you
              ? `Ты (${row.short_name || _displayShortName(row.name)})`
              : row.short_name || row.name;
            return `
          <li class="class-board-row${row.you ? " is-you" : ""}">
            <span class="class-board-rank">${medal} ${escapeHtml(String(row.rank))}.</span>
            <span class="class-board-name">${escapeHtml(label)}</span>
            <span class="class-board-meta">${escapeHtml(formatXp(row.xp))} XP <i>🔥 ${escapeHtml(
              String(row.streak || 0)
            )}</i></span>
          </li>`;
          })
          .join("")}
      </ol>
    </aside>
  `;
}

function currentFocusTrack() {
  return FOCUS_TRACKS[focusTrackIndex] || FOCUS_TRACKS[0];
}

function focusIsPlaying() {
  const audio = getFocusAudio();
  return !!(audio && !audio.paused && !audio.ended);
}

function loadFocusTrack(index, { autoplay = false } = {}) {
  const audio = getFocusAudio();
  if (!audio) return;
  bindFocusAudioEvents();
  focusTrackIndex = Math.max(0, Math.min(FOCUS_TRACKS.length - 1, index));
  const track = currentFocusTrack();
  const nextSrc = track.src;
  if (!audio.getAttribute("data-src") || audio.getAttribute("data-src") !== nextSrc) {
    audio.setAttribute("data-src", nextSrc);
    audio.src = nextSrc;
    audio.load();
  }
  if (autoplay) {
    audio.play().catch((err) => console.warn("Playback error:", err));
  }
  syncFocusPlayerDom();
}

function toggleFocusPlay() {
  const audio = getFocusAudio();
  if (!audio) return;
  bindFocusAudioEvents();
  if (!audio.src) loadFocusTrack(focusTrackIndex);
  if (focusIsPlaying()) {
    audio.pause();
  } else {
    audio.play().catch((err) => console.warn("Playback error:", err));
  }
  syncFocusPlayerDom();
}

function renderFocusPlayerHtml() {
  const track = currentFocusTrack();
  const playing = focusIsPlaying();
  const open = !!state.focusPlayerOpen;
  return `
    <div class="focus-player${open ? " is-open" : ""}${playing ? " is-playing" : ""}" id="focus-player" aria-label="Lo-Fi плеер для фокуса">
      <button type="button" class="focus-player-main" id="btn-focus-toggle-panel" title="Плейлист">
        <span class="focus-vinyl" aria-hidden="true">
          <img class="focus-vinyl-mark" src="/assets/logo.png" alt="" />
        </span>
        <span class="focus-meta">
          <strong>${escapeHtml(track.title)}</strong>
          <span>${escapeHtml(track.artist)}</span>
        </span>
      </button>
      <button type="button" class="focus-play" id="btn-focus-play" aria-label="${playing ? "Пауза" : "Играть"}">
        ${playing ? "❚❚" : "▶"}
      </button>
      <div class="focus-playlist"${open ? "" : " hidden"}>
        <p class="focus-playlist-title">Focus playlist</p>
        <ol>
          ${FOCUS_TRACKS.map(
            (t, i) => `
            <li>
              <button type="button" class="focus-track${i === focusTrackIndex ? " is-active" : ""}" data-focus-track="${i}">
                <span class="focus-track-n">${i + 1}.</span>
                <span class="focus-track-copy">${escapeHtml(t.artist)} — ${escapeHtml(t.title)}${
              i === focusTrackIndex ? " (Активен)" : ""
            }</span>
              </button>
            </li>`
          ).join("")}
        </ol>
      </div>
    </div>
  `;
}

function syncFocusPlayerDom() {
  const root = document.getElementById("focus-player-root");
  if (!root || root.hidden) return;
  root.innerHTML = renderFocusPlayerHtml();
  bindFocusPlayer();
}

function ensureFocusPlayer({ visible }) {
  let root = document.getElementById("focus-player-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "focus-player-root";
    document.body.appendChild(root);
  }
  root.hidden = !visible;
  if (!visible) {
    state.focusPlayerOpen = false;
    const audio = getFocusAudio();
    if (audio && !audio.paused) audio.pause();
  } else {
    syncFocusPlayerDom();
  }
}

function scheduleFocusPlayer({ visible }) {
  if (!visible) {
    focusPlayerScheduled = false;
    ensureFocusPlayer({ visible: false });
    return;
  }
  if (focusPlayerScheduled) return;
  focusPlayerScheduled = true;
  const mount = () => {
    focusPlayerScheduled = false;
    if (state.step !== "dashboard") return;
    ensureFocusPlayer({ visible: true });
  };
  if (typeof requestIdleCallback !== "undefined") {
    requestIdleCallback(mount, { timeout: 2500 });
  } else {
    setTimeout(mount, 400);
  }
}

function markDashboardReady() {
  if (typeof document === "undefined") return;
  document.documentElement.classList.remove("dash-ready");
  if (state.step !== "dashboard" || state.loading) return;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.documentElement.classList.add("dash-ready");
    });
  });
}

function bindFocusPlayer() {
  document.getElementById("btn-focus-play")?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleFocusPlay();
  });
  document.getElementById("btn-focus-toggle-panel")?.addEventListener("click", () => {
    state.focusPlayerOpen = !state.focusPlayerOpen;
    syncFocusPlayerDom();
  });
  document.querySelectorAll("[data-focus-track]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.getAttribute("data-focus-track"));
      if (!Number.isFinite(idx)) return;
      loadFocusTrack(idx, { autoplay: true });
      state.focusPlayerOpen = true;
      syncFocusPlayerDom();
    });
  });
}

function renderStudentHero(data) {
  const greet = firstNameOf(state.name);
  return `
    <section class="student-hero reveal">
      <span class="student-hero-stars" aria-hidden="true"></span>
      <span class="student-hero-glow student-hero-glow-a" aria-hidden="true"></span>
      <span class="student-hero-glow student-hero-glow-b" aria-hidden="true"></span>
      <div class="student-hero-inner">
        <div class="student-hero-copy">
          <h2>Привет, ${escapeHtml(greet)}! 👋</h2>
          <p class="student-hero-sub">Твой прогресс подготовки к экзамену</p>
          ${renderOgeCountdown()}
          ${renderDailyGoal(data)}
        </div>
        ${renderStreakCard(data)}
      </div>
    </section>
  `;
}

function renderHomeTab(data) {
  const variants = activeVariantItems(data.active || []);
  return `
    <div class="bento student-home">
      ${renderStudentHero(data)}
      <div class="home-split">
        <div class="home-main-col">
          <section class="home-variants reveal">
            <div class="panel-head">
              <h2>Активные варианты</h2>
            </div>
            ${renderActiveSection(variants)}
          </section>
          ${renderWarmupWidget()}
        </div>
        ${renderClassBoard(data)}
      </div>
    </div>
  `;
}

function latestKimResult(data) {
  for (const it of data.completed || []) {
    if (isRnoItem(it)) continue;
    const oge = studentOgeResult({ ...it, subject: it.subject || state.subject });
    const scoreRaw = oge && oge.score != null ? oge.score : it.score;
    const score = Number(scoreRaw);
    if (!Number.isFinite(score)) continue;
    let grade = oge && oge.grade != null ? String(oge.grade) : it.grade != null ? String(it.grade) : "";
    if (!grade && typeof OgeGrade !== "undefined" && OgeGrade.markFromScale) {
      grade = String(OgeGrade.markFromScale(score, it.subject || state.subject));
    }
    return {
      score,
      grade: grade || "—",
      max: Number(oge && oge.max_score != null ? oge.max_score : it.max_score) || ogeGoalMeta().max,
    };
  }
  return null;
}

function progressOverview(data) {
  const done = (data.completed || []).filter((it) => !isRnoItem(it));
  let scoreSum = 0;
  let scoreN = 0;
  let maxSum = 0;
  let gradeSum = 0;
  let gradeN = 0;
  let pctSum = 0;
  let pctN = 0;
  let geoPass = 0;
  let geoTotal = 0;
  let geoPending = 0;
  done.forEach((it) => {
    const oge = studentOgeResult({ ...it, subject: it.subject || state.subject });
    const max = Number(it.max_score != null ? it.max_score : oge && oge.max_score);
    if (it.score != null && Number.isFinite(Number(it.score))) {
      scoreSum += Number(it.score);
      scoreN += 1;
      if (Number.isFinite(max) && max > 0) {
        maxSum += max;
        pctSum += (100 * Number(it.score)) / max;
        pctN += 1;
      }
    }
    if (oge && oge.grade != null && Number.isFinite(Number(oge.grade))) {
      gradeSum += Number(oge.grade);
      gradeN += 1;
    }
    if (oge && (oge.geometry_score != null || oge.geometry_tag || oge.failed_geometry != null)) {
      geoTotal += 1;
      if (oge.geometry_pending) geoPending += 1;
      else if (!oge.failed_geometry && Number(oge.geometry_score || 0) >= 2) geoPass += 1;
      else if (Number(oge.geometry_score || 0) >= 2) geoPass += 1;
    }
  });
  const statsPct = data.stats && data.stats.avg_accuracy != null ? Number(data.stats.avg_accuracy) : null;
  return {
    kimN: done.length,
    avgScore: scoreN ? scoreSum / scoreN : null,
    avgMax: scoreN && maxSum ? maxSum / scoreN : null,
    avgGrade: gradeN ? gradeSum / gradeN : null,
    avgPct: pctN ? pctSum / pctN : Number.isFinite(statsPct) ? statsPct : null,
    latest: latestKimResult(data),
    geoPass,
    geoTotal,
    geoPending,
  };
}

function renderForecastCard(data) {
  const meta = ogeGoalMeta();
  const latest = latestKimResult(data);
  if (!latest) {
    return `
      <article class="analytics-card">
        <span class="student-stat-label">Прогноз оценки ОГЭ</span>
        <div class="forecast-row">
          <div class="forecast-badge is-empty">—</div>
          <div class="forecast-copy">
            <strong>Пока нет сдач</strong>
            <span>Сдай первый КИМ — здесь появится прогноз оценки</span>
          </div>
        </div>
      </article>
    `;
  }
  const score = Math.round(latest.score);
  const grade = latest.grade || "—";
  const left = Math.max(0, meta.five - score);
  const foot =
    score >= meta.five
      ? "🟢 Цель по оценке 5 уже достигнута"
      : `До оценки 5 не хватает ${left} ${ruPlural(left, "балл", "балла", "баллов")}`;
  return `
    <article class="analytics-card">
      <span class="student-stat-label">Прогноз оценки ОГЭ</span>
      <div class="forecast-row">
        <div class="forecast-badge is-${escapeHtml(grade)}" aria-label="Оценка ${escapeHtml(grade)}">${escapeHtml(grade)}</div>
        <div class="forecast-copy">
          <strong>Оценка ${escapeHtml(grade)} · ${escapeHtml(String(score))} баллов</strong>
          <span>${escapeHtml(foot)}</span>
        </div>
      </div>
    </article>
  `;
}

function renderSafetyCard(data) {
  const rus = studentSubjectCode() === "russian";
  const th = latestThresholds(data);
  const rec = rus ? th.lit : th.geo;
  const label = rus ? "Грамотность (Часть 2)" : "Геометрия";
  const icon = rus ? "✏️" : "📐";
  const need = rec.need;
  const raw = rec.score;
  const shown = raw == null ? 0 : Math.max(0, Math.min(need, Number(raw) || 0));
  const pct = Math.round((100 * shown) / need);
  let status = "Пока нет сдач по этому предмету";
  let cls = "";
  if (rec.pending) {
    status = "⏳ На проверке";
    cls = "is-wait";
  } else if (raw != null && shown >= need) {
    status = `🟢 ${shown}/${need} б. (Порог пройден)`;
    cls = "is-ok";
  } else if (raw != null) {
    const left = Math.max(0, need - shown);
    status = `⚠️ ${shown}/${need} б. (Нужен ещё ${left} ${ruPlural(left, "балл", "балла", "баллов")}!)`;
    cls = "is-warn";
  }
  return `
    <article class="analytics-card ${cls}">
      <span class="student-stat-label">Пороги безопасности ОГЭ</span>
      <div class="safety-row">
        <strong>${icon} ${escapeHtml(label)}</strong>
        <span class="safety-status ${cls}">${escapeHtml(status)}</span>
      </div>
      <div class="student-stat-bar" role="progressbar" aria-valuemin="0" aria-valuemax="${need}" aria-valuenow="${shown}">
        <i style="width:${pct}%"></i>
      </div>
    </article>
  `;
}

function renderKimDoneCard(data) {
  const p = progressOverview(data);
  const pct = p.avgPct == null ? null : Math.round(p.avgPct);
  const works = `${p.kimN} ${ruPlural(p.kimN, "сданная работа", "сданные работы", "сданных работ")}`;
  const foot =
    pct == null
      ? `${works}. Сдай КИМ — появится средний процент.`
      : `${works}, средний процент выполнения: ${pct}%.`;
  return `
    <article class="analytics-card">
      <span class="student-stat-label">Выполнено КИМ</span>
      <div class="student-stat-num is-open">${p.kimN}</div>
      <span class="student-stat-foot">${escapeHtml(foot)}</span>
      <div class="student-stat-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct || 0}">
        <i style="width:${pct || 0}%"></i>
      </div>
    </article>
  `;
}

function renderProgressStats(data) {
  return `
    <section class="analytics-grid" aria-label="Базовая аналитика">
      ${renderForecastCard(data)}
      ${renderSafetyCard(data)}
      ${renderKimDoneCard(data)}
    </section>
  `;
}

function renderProHeatmapPreview() {
  const cells = Array.from({ length: 25 }, (_, i) => {
    const tone = [0, 2, 3][i % 3];
    return `<span class="pro-heat-cell tone-${tone}">${i + 1}</span>`;
  }).join("");
  return `
    <article class="pro-ghost-card">
      <h3>Тепловая карта 25 заданий ОГЭ</h3>
      <div class="pro-heat-grid">${cells}</div>
    </article>
  `;
}

function renderProDiagnosticsPreview() {
  const rus = studentSubjectCode() === "russian";
  const rows = rus
    ? [
        "Часто путаешь -тся / -ться в глаголах",
        "Пропуск запятой в сложном предложении",
        "Неполное сжатие микротемы в изложении",
      ]
    : [
        "Ошибки в подобных треугольниках",
        "Теряешь единицы в текстовых задачах",
        "Слабый порог по геометрии части 2",
      ];
  return `
    <article class="pro-ghost-card">
      <h3>ИИ-диагностика частых ошибок</h3>
      <ul class="pro-diag-list">
        ${rows.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}
      </ul>
    </article>
  `;
}

function renderProChartPreview() {
  return `
    <article class="pro-ghost-card">
      <h3>Динамика баллов за месяц</h3>
      <svg class="pro-chart" viewBox="0 0 220 88" aria-hidden="true">
        <defs>
          <linearGradient id="proChartFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#34d399" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#34d399" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path d="M8 70 L40 58 L72 62 L104 40 L136 46 L168 28 L204 22 L204 80 L8 80 Z" fill="url(#proChartFill)"/>
        <polyline points="8,70 40,58 72,62 104,40 136,46 168,28 204,22" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </article>
  `;
}

function renderProVault() {
  return `
    <section class="pro-vault reveal" aria-label="PRO-аналитика">
      <div class="pro-vault-head">
        <h2>🔥 Глубокая ИИ-Аналитика (PRO)</h2>
        <span class="pro-lock-chip">🔒 Закрыто</span>
      </div>
      <div class="pro-vault-stage">
        <div class="pro-vault-grid" aria-hidden="true">
          ${renderProHeatmapPreview()}
          ${renderProDiagnosticsPreview()}
          ${renderProChartPreview()}
        </div>
        <div class="pro-overlay">
          <h3>🔒 Откройте доступ к PRO-Аналитике</h3>
          <p>Узнайте свои слабые задания ОГЭ, получите персональные ИИ-разборы ошибок и прогноз баллов.</p>
          <button type="button" class="btn-try-pro" id="btn-try-pro">Попробовать PRO бесплатно 🚀</button>
        </div>
      </div>
    </section>
  `;
}

function renderProgressTab(data) {
  const completed = data.completed || [];
  const rno = activeRnoItems(data.active || []);
  return `
    <div class="bento student-progress">
      ${renderProgressStats(data)}
      ${renderProVault()}
      ${
        rno.length
          ? `<section class="students-panel reveal dash-panel task-mod-panel">
              <div class="panel-head"><h2>Работа над ошибками</h2></div>
              ${renderActiveSection(rno)}
            </section>`
          : ""
      }
      <section class="glass students-panel reveal dash-panel">
        <div class="panel-head"><h2>Сданные работы</h2></div>
        ${renderCompletedSection(completed)}
      </section>
    </div>
  `;
}

function navBadgeHtml(badge) {
  if (!badge) return "";
  return `<span class="nav-badge nav-badge-${badge.kind}" aria-hidden="true">${escapeHtml(badge.text)}</span>`;
}

function renderInviteModal() {
  if (!state.showInvite) return "";
  return `
    <div class="modal-backdrop invite-backdrop" id="invite-backdrop">
      <div class="modal-card invite-card" role="dialog" aria-modal="true" aria-labelledby="invite-title">
        <span class="invite-glow" aria-hidden="true"></span>
        <div class="invite-inner">
          <h3 class="invite-title" id="invite-title">🎁 Соревнуйся с друзьями и открывай PRO</h3>
          <p class="coming-soon-lead">Приглашай одноклассников по своей ссылке. Готовьтесь к ОГЭ вместе, отслеживайте прогресс друг друга и получайте доступ к ИИ-разборам.</p>
          <span class="invite-status">⚡ Технология в разработке</span>
          <button type="button" class="btn btn-ghost invite-close" id="btn-close-invite">Закрыть</button>
        </div>
      </div>
    </div>
  `;
}

function hasCabinetSession() {
  return !!(String(state.classCode || "").trim() && String(state.name || "").trim().length >= 2);
}

function renderCabinetShell(mainHtml) {
  const tabMeta = NAV.find((n) => n.id === state.tab) || NAV[0];
  const titles = {
    home: "Главная",
    progress: "Мой прогресс",
  };
  const hellos = {
    home: "Активные варианты и Live-урок",
    progress: "Базовая аналитика и PRO-прогноз",
  };
  const classTitle = state.className || state.classCode || "Класс";

  return `
    <div class="dash" id="dash-shell">
      <div class="sidebar-backdrop" id="sidebar-backdrop" hidden></div>
      <aside class="sidebar" id="app-sidebar">
        <div class="sidebar-brand">
          <span class="brand-name">EduSense</span>
          <span class="beta-badge" title="Open beta">BETA</span>
        </div>

        <div class="class-switch">
          <label>Ваш класс</label>
          <strong title="${escapeHtml(classTitle)}">${escapeHtml(classTitle)}</strong>
          <div class="mini-specs">
            ${examLabel(state.exam) ? `<span>${escapeHtml(examLabel(state.exam))}</span>` : ""}
            ${state.subject ? `<span>${escapeHtml(state.subject)}</span>` : ""}
            ${state.classCode ? `<span>${escapeHtml(state.classCode)}</span>` : ""}
          </div>
        </div>

        <nav class="nav-list" aria-label="Меню ученика">
          ${NAV.map((item) => {
            const hook = item.action
              ? `data-nav-action="${item.action}"`
              : `data-tab="${item.id}"`;
            return `
            <button type="button" class="nav-item ${!item.action && state.tab === item.id ? "is-active" : ""}"
              ${hook} data-tour="nav-${item.id}">
              ${icon(item.icon)}
              <span class="nav-item-label">${item.label}</span>
              ${navBadgeHtml(item.badge)}
            </button>`;
          }).join("")}
        </nav>

        <div class="sidebar-foot">
          <div class="user-chip">
            <span class="avatar">${escapeHtml(initials(state.name))}</span>
            <div class="meta">
              <div class="name">${escapeHtml(state.name || "Ученик")}</div>
              <div class="role"><span class="online-dot" aria-hidden="true"></span> Ученик</div>
            </div>
            <button type="button" class="user-chip-exit js-student-logout" title="Выйти" aria-label="Выйти">
              ${icon("logout")}
            </button>
          </div>
          <a class="sidebar-install" href="/install">Установить приложение</a>
        </div>
      </aside>

      <main class="main">
        <div class="main-inner">
          <div class="main-head">
            <div class="main-head-top">
              <button type="button" class="nav-toggle" id="nav-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="app-sidebar">
                <span class="nav-toggle-bars" aria-hidden="true"></span>
              </button>
              <div class="main-head-text">
                <h1>${titles[state.tab] || "Главная"}</h1>
                <p class="hello">${hellos[state.tab] || escapeHtml(classLineText())}</p>
              </div>
              <div class="main-head-tools main-head-tools-inline">
                <div id="notif-root"></div>
                <button type="button" class="head-logout js-student-logout" title="Выйти">Выйти</button>
              </div>
            </div>
          </div>
          ${mainHtml}
        </div>
      </main>
      ${renderInviteModal()}
      ${renderLiveModal()}
    </div>
  `;
}

function renderDashboardSkeleton() {
  return renderCabinetShell(`
    <div class="dash-skeleton" aria-busy="true" aria-label="Загрузка кабинета">
      <div class="skel skel-hero"></div>
      <div class="skel-grid">
        <div class="skel skel-card"></div>
        <div class="skel skel-card skel-card-tall"></div>
      </div>
    </div>
  `);
}

function renderDashboard() {
  if (state.tab === "tasks" || state.tab === "results") state.tab = "progress";
  if (state.loading && !state.dashboard) {
    return renderDashboardSkeleton();
  }
  const data = state.dashboard || { active: [], completed: [], stats: {} };
  let body = "";
  if (state.tab === "progress") body = renderProgressTab(data);
  else body = renderHomeTab(data);
  return renderCabinetShell(body);
}

function renderJoin() {
  const title = state.previewTitle || "Вход в класс";
  const subjectLine = state.previewSubject
    ? `<p class="kicker">${escapeHtml(state.previewSubject)}</p>`
    : `<p class="kicker">Кабинет ученика</p>`;

  if (state.closed) {
    return `
    ${brandBlockHtml()}
    <div class="card entry-card">
      ${subjectLine}
      <h1>${escapeHtml(title)}</h1>
      <div class="closed-banner" role="status">Приём ответов закрыт</div>
      <p class="sub">Учитель закрыл приём работ по этому коду. Новую попытку можно сделать, только если приём снова откроют.</p>
      <label class="field">
        <span>Код класса или работы</span>
        <input type="text" id="inp-code" value="${escapeHtml(state.code)}" placeholder="EDU-XXXX или ссылка" autocomplete="off" />
        ${state.codeError ? `<span class="field-error" id="err-code">${escapeHtml(state.codeError)}</span>` : ""}
      </label>
      <button class="btn btn-secondary" id="btn-check-code" ${state.loading ? "disabled" : ""}>
        ${state.loading ? "Проверяем…" : "Проверить другой код"}
      </button>
      <button type="button" class="btn btn-ghost js-student-logout">На главную</button>
    </div>
  `;
  }

  const authUser = readAuthUser();
  const nameLocked = !!(authUser && String(authUser.full_name || "").trim().length >= 2);
  if (nameLocked && !state.name) state.name = String(authUser.full_name).trim();

  const canContinue =
    !nameLocked &&
    state.savedEntry &&
    state.savedEntry.name &&
    state.savedEntry.name.length >= 2 &&
    state.classCode;

  return `
    ${brandBlockHtml()}
    <div class="card entry-card">
      ${subjectLine}
      <h1>${escapeHtml(title)}</h1>
      <p class="sub">${
        nameLocked
          ? "Введите код класса или работы от учителя — кабинет откроется под вашим аккаунтом."
          : "Введите код класса или работы от учителя и ФИО — откроется ваш кабинет."
      }</p>
      ${
        nameLocked
          ? `<p class="sub">Вы вошли как <strong>${escapeHtml(state.name)}</strong></p>`
          : ""
      }
      <label class="field">
        <span>Код класса или работы</span>
        <input type="text" id="inp-code" value="${escapeHtml(state.code)}" placeholder="EDU-XXXX или ссылка" autocomplete="off" aria-invalid="${state.codeError ? "true" : "false"}" />
        ${state.codeError ? `<span class="field-error" id="err-code">${escapeHtml(state.codeError)}</span>` : ""}
      </label>
      ${
        nameLocked
          ? ""
          : `<label class="field">
        <span>Имя и фамилия</span>
        <input type="text" id="inp-name" value="${escapeHtml(state.name)}" placeholder="Иванов Иван" autocomplete="name" aria-invalid="${state.nameError ? "true" : "false"}" />
        ${state.nameError ? `<span class="field-error" id="err-name">${escapeHtml(state.nameError)}</span>` : ""}
      </label>`
      }
      <button class="btn btn-primary btn-neon" id="btn-open" data-tour="join-open" ${state.loading ? "disabled" : ""}>
        ${state.loading ? "Открываем…" : "Приступить к работе"}
      </button>
      ${
        hasCabinetSession()
          ? `<button class="btn btn-secondary" id="btn-open-cabinet" ${state.loading ? "disabled" : ""}>
              Открыть главную кабинета
            </button>`
          : ""
      }
      ${
        canContinue
          ? `<button class="btn btn-secondary" id="btn-continue" ${state.loading ? "disabled" : ""}>
              Продолжить как ${escapeHtml(state.savedEntry.name)}
            </button>`
          : ""
      }
      <button type="button" class="btn btn-ghost js-student-logout">На главную</button>
    </div>
  `;
}

function renderTaskCard(q, extrasHtml) {
  const a = ensureAnswer(q.num, q.part);
  const isPhoto = a.mode === "photo";
  const extras = extrasHtml || "";
  const media = payloadImagesHtml(q);
  const locked = !!state.timerExpired;
  const mathShort = studentSubjectCode() === "math" && Number(q.part || 1) === 1;
  return `
    <article class="task" data-num="${q.num}">
      <div class="task-head">
        <span class="pill">№${q.num}</span>
        <span class="pill">Ч.${q.part}</span>
        <span class="pill mint">${escapeHtml(q.type)}</span>
        <span class="pill">${q.max_score} б.</span>
      </div>
      <h3>${escapeHtml(q.topic)}</h3>
      ${media}
      <div class="task-text">${formatTaskHtml(q.text, q)}</div>
      ${extras}
      ${figureHtml(q)}
      <div class="answer-panel${locked ? " is-locked" : ""}">
        <div class="answer-tabs">
          <button type="button" data-mode="text" data-num="${q.num}" class="${!isPhoto ? "is-active" : ""}" ${locked ? "disabled" : ""}>Ответ текстом</button>
          <button type="button" data-mode="photo" data-num="${q.num}" class="${isPhoto ? "is-active" : ""}" ${locked ? "disabled" : ""}>Фото решения</button>
        </div>
        ${
          isPhoto
            ? `<div class="photo-box">
                <label>
                  <strong style="color:var(--text)">Загрузить фото</strong>
                  <div style="margin-top:6px;font-size:.85rem">Сфотографируйте решение в тетради</div>
                  <input type="file" accept="image/*" capture="environment" data-photo="${q.num}" ${locked ? "disabled" : ""} />
                </label>
                ${a.photoDataUrl ? `<img class="photo-preview" src="${a.photoDataUrl}" alt="Фото решения №${q.num}" />` : ""}
              </div>`
            : `<textarea data-answer="${q.num}" placeholder="Введите ответ…" ${mathShort ? 'inputmode="decimal" data-math-decimal="1"' : ""} ${locked ? "readonly" : ""}>${escapeHtml(a.text)}</textarea>`
        }
      </div>
    </article>
  `;
}

function renderWork() {
  const a = state.assignment;
  if (!a) {
    state.step = "dashboard";
    return renderDashboard();
  }
  const questions = a.questions || [];
  const subj = studentSubjectCode(a);
  const locked = !!state.timerExpired;
  const rus =
    subj !== "math" &&
    typeof OgeRusUI !== "undefined" &&
    (typeof OgeRusUI.isOgeRussianExam === "function"
      ? OgeRusUI.isOgeRussianExam(questions, Object.assign({}, a, {
          subject: a.subject,
          subject_code: a.subject_code || a.subject,
          exam_ui: subj === "russian" ? a.exam_ui : a.exam_ui === "oge_rus_kim" ? "" : a.exam_ui,
        }))
      : OgeRusUI.isOgeRusList(questions));
  const tasksHtml = rus
    ? OgeRusUI.renderExamVariant(questions, {
        teacher: false,
        getAnswerText: (num) => ensureAnswer(num).text || "",
        getAnswerState: (num) => ensureAnswer(num),
        readOnly: locked,
      })
    : typeof MathOgeUI !== "undefined" && typeof MathOgeUI.mapTasks === "function"
      ? MathOgeUI.mapTasks(questions, (q) => renderTaskCard(q, ""))
      : questions.map((q) => renderTaskCard(q, "")).join("");
  const m = questions.length;
  const n = answeredCount();
  const timerMins = timerMinutesOf(a);
  let timerHtml = "";
  if (timerMins) {
    const left =
      state.timerEndsAt != null ? Math.max(0, state.timerEndsAt - Date.now()) : timerMins * 60 * 1000;
    const expired = state.timerEndsAt != null && left <= 0;
    const urgent = !expired && left <= 60_000;
    const label = expired
      ? "00:00"
      : state.timerEndsAt
        ? formatTimerRemain(left)
        : formatTimerRemain(timerMins * 60 * 1000);
    timerHtml = `<div class="work-timer-wrap${expired ? " is-expired" : urgent ? " is-urgent" : ""}" title="Лимит ${timerMins} мин">
      <span class="work-timer-label">Таймер</span>
      <span id="work-timer" class="work-timer${expired ? " is-expired" : urgent ? " is-urgent" : ""}" aria-live="polite" aria-label="Осталось ${label}">${label}</span>
    </div>`;
  }
  const deadline = deadlineOf(a);
  const nums = questions.map((q) => q.num).filter((n) => n != null);
  const jumpHtml =
    nums.length > 1
      ? `<div class="task-jump" aria-label="Перейти к заданию">
          <span class="task-jump-label">К заданию</span>
          <div class="task-jump-chips">
            ${nums
              .map(
                (n) =>
                  `<button type="button" class="task-jump-chip" data-jump-num="${escapeHtml(
                    String(n)
                  )}">${escapeHtml(String(n))}</button>`
              )
              .join("")}
          </div>
          <label class="task-jump-select-wrap">
            <span class="sr-only">Номер задания</span>
            <select id="task-jump-select" aria-label="Номер задания">
              ${nums
                .map((n) => `<option value="${escapeHtml(String(n))}">№${escapeHtml(String(n))}</option>`)
                .join("")}
            </select>
          </label>
        </div>`
      : "";
  const savedT = formatAutosaveTime(state.lastSavedAt);
  const autosaveHtml = `<p id="autosave-hint" class="autosave-hint" role="status">${
    state.lastSavedAt
      ? `Сохранено автоматически · ${escapeHtml(savedT)}`
      : "Черновик сохранится сам при вводе"
  }</p>`;
  return `
    <div class="work-focus">
      <div class="work-focus-bar">
        <button type="button" class="btn btn-ghost" id="btn-back-menu" title="Выйти на главную. Вариант можно доделать, таймер встанет на паузу.">← Выйти из варианта</button>
        ${timerHtml}
      </div>
      <div class="card work-card${rus ? " card-oge-rus" : ""}${locked ? " work-locked" : ""}">
        <p class="kicker">${escapeHtml(a.subject || "Работа")}</p>
        <h1>${escapeHtml(a.title)}</h1>
        <div class="work-meta" aria-live="polite">
          <span id="work-progress" class="work-progress">${escapeHtml(workProgressLabel(n, m))}</span>
          ${deadline ? `<span class="work-deadline">до ${escapeHtml(formatDeadline(deadline))}</span>` : ""}
        </div>
        ${autosaveHtml}
        ${jumpHtml}
        ${
          locked
            ? `<div class="work-timer-banner" role="status">Время вышло. Ответы зафиксированы — можно сдать работу.</div>`
            : ""
        }
        ${
          (() => {
            const fromQ = (questions || []).some(
              (q) =>
                q &&
                q.payload &&
                (q.payload.etalon || (q.payload.provenance && q.payload.provenance.variant_code))
            );
            const prov =
              a.provenance ||
              ((questions || []).find((q) => q && q.payload && q.payload.provenance) || {}).payload
                ?.provenance ||
              null;
            const uniqueHtml =
              a.shuffle_variants || a.unique_applied
                ? `<p class="unique-badge" title="Числа и порядок вариантов подобраны под вас">Ваш вариант${
                    a.unique_changed
                      ? " · " + escapeHtml(String(a.unique_changed)) + " заданий отличаются"
                      : ""
                  }</p>`
                : "";
            const showEtalon = !(
              rus ||
              subj === "russian"
            ) && !!(
              a.etalon ||
              a.exam_ui === "etalon" ||
              fromQ ||
              (prov && prov.variant_code)
            );
            const etalonHtml = showEtalon
              ? `<p class="etalon-badge" title="Импортированный эталон (не «официальный КИМ ФИПИ»)">Эталонный вариант${
                  prov && prov.year ? " · " + escapeHtml(String(prov.year)) : ""
                }${
                  prov && prov.variant_code ? " · " + escapeHtml(String(prov.variant_code)) : ""
                }</p>`
              : "";
            return uniqueHtml + etalonHtml;
          })()
        }
        <p class="sub">Код ${escapeHtml(a.code)} · ${escapeHtml(state.name)} · ${questions.length} заданий.
        ${
          rus
            ? "Тестовая часть (2–12) — как в КИМ; изложение и сочинение — развёрнутый ответ."
            : "На каждое задание — свой ответ или фото."
        }
        Проверка: ${
          a.grading_mode === "manual"
            ? "учитель"
            : a.grading_mode === "autopilot"
              ? "автоматическая"
              : "черновик баллов + учитель"
        }.</p>
        ${tasksHtml}
        <div class="work-submit-spacer" aria-hidden="true"></div>
      </div>
      <div class="work-submit-bar">
        <button class="btn btn-primary" id="btn-submit" ${state.loading ? "disabled" : ""}>
          ${state.loading ? "Отправляем…" : "Сдать работу"}
        </button>
      </div>
    </div>
  `;
}

function renderDone() {
  const r = state.result || {};
  const max = r.max_score ?? "—";
  const score = r.score ?? "—";
  const locked = answersLockedOf(r) || answersLockedOf(state.assignment);
  const review = locked ? {} : r.ai_review || {};
  const items = Array.isArray(review.items) ? review.items : [];
  const autoItems = items.filter(
    (it) => it && (it.status === "correct" || it.status === "wrong" || it.status === "empty")
  );
  const pendingItems = items.filter((it) => it && String(it.status || "").includes("pending"));
  const pendingN = pendingItems.length;
  const autoScore =
    review.auto_score != null
      ? review.auto_score
      : autoItems.reduce((sum, it) => sum + (Number(it.earned) || 0), 0);
  const hasAuto = !locked && (autoItems.length > 0 || review.auto_score != null);
  const already = !!r.already_submitted;
  const canReview =
    !locked &&
    (r.has_review ||
      (items.length > 0 &&
        items.some((it) => it && (it.status === "correct" || it.status === "wrong" || String(it.status || "").includes("pending")))));
  const hasScore = r.score != null || r.max_score != null || r.teacher_score != null;
  const teacherComment = String(r.teacher_comment || "").trim();
  const displayScore = r.teacher_score != null ? r.teacher_score : score;

  return `
    <div class="work-focus">
      <div class="work-focus-bar">
        <button type="button" class="btn btn-ghost btn-compact" id="btn-again">← Назад в меню</button>
        <div class="work-focus-brand">EduSense <span class="beta-badge">BETA</span></div>
      </div>
      <div class="card result">
        <p class="kicker">${already ? "Уже сдано" : "Готово"}</p>
        <h1>${already ? "Работа уже была сдана" : "Работа отправлена"}</h1>
        ${renderOgeScoreCard({ ...r, subject: r.subject || state.subject })}
        ${
          hasScore && !studentOgeResult({ ...r, subject: r.subject || state.subject })
            ? `<div class="score">${escapeHtml(String(displayScore))} / ${escapeHtml(String(max))}</div>`
            : ""
        }
        <div class="result-split">
          ${
            hasAuto
              ? `<div class="result-split-block">
                  <h3>Проверено автоматически</h3>
                  <p>Краткие ответы: ${escapeHtml(String(autoScore))}${
                    max !== "—" ? ` из авто-части` : ""
                  }${
                    autoItems.length
                      ? ` · верно ${autoItems.filter((i) => i.status === "correct").length}, ошибки ${
                          autoItems.filter((i) => i.status === "wrong").length
                        }`
                      : ""
                  }</p>
                </div>`
              : ""
          }
          <div class="result-split-block ${pendingN || !hasAuto ? "is-pending" : ""}">
            <h3>${pendingN ? "Учитель проверит" : r.teacher_reviewed_at || r.teacher_score != null ? "Проверено учителем" : "Учитель увидит работу"}</h3>
            <p>${
              pendingN
                ? `Развёрнутые ответы и фото — на проверке${pendingN ? ` (${pendingN})` : ""}. Итоговый балл появится после проверки.`
                : r.teacher_score != null
                  ? "Учитель выставил итоговый балл."
                  : "Если нужна ручная проверка — учитель поставит балл и комментарий."
            }</p>
          </div>
        </div>
        ${
          teacherComment
            ? `<div class="teacher-comment" role="status">
                <p class="teacher-comment-label">Комментарий учителя</p>
                <p>${escapeHtml(teacherComment)}</p>
              </div>`
            : ""
        }
        ${
          already
            ? `<p class="sub">Работа уже сдана. Повторно решить её нельзя${
                locked ? "." : " — можно только посмотреть разбор."
              }</p>`
            : ""
        }
        ${
          locked
            ? `<p class="sub">${escapeHtml(reviewLockedHint(r.deadline ? r : state.assignment || r))}</p>`
            : ""
        }
        <div class="result-actions">
          <button class="btn btn-secondary" id="btn-again-foot">В кабинет</button>
          ${
            canReview
              ? `<button class="btn btn-primary" id="btn-view-review">Посмотреть разбор</button>`
              : ""
          }
          <button class="btn btn-ghost" id="btn-exit-done">Выйти</button>
        </div>
      </div>
    </div>
  `;
}

function renderReview() {
  const item = state.reviewItem || {};
  const review = item.ai_review || {};
  const items = Array.isArray(review.items) ? review.items : [];
  const rows = items
    .map((it) => {
      const st = String(it.status || "");
      const label =
        st === "correct" ? "верно" : st === "wrong" ? "ошибка" : st.includes("pending") ? "на проверке" : st || "—";
      const cls =
        st === "correct" ? "ok" : st === "wrong" ? "closed" : "progress";
      const ag = it.ai_grade && typeof it.ai_grade === "object" ? it.ai_grade : null;
      const pending = st.includes("pending");
      const note = pending
        ? it.comment || it.message || it.hint || ""
        : it.comment || (ag && ag.student_feedback) || it.message || it.hint || "";
      const numN = Number(it.num);
      const rusLong = numN === 1 || numN === 13;
      const extraBits = [];
      if (!pending && ag && ag.criteria && typeof ag.criteria === "object") {
        const labels = { ik1: "ИК1", ik2: "ИК2", ik3: "ИК3", sk1: "СК1", sk2: "СК2", sk3: "СК3" };
        const chips = Object.keys(labels)
          .filter((k) => ag.criteria[k] != null)
          .map((k) => `<span class="review-crit">${labels[k]} ${escapeHtml(String(ag.criteria[k]))}</span>`);
        if (chips.length) extraBits.push(`<div class="review-criteria">${chips.join("")}</div>`);
      }
      if (!pending && !rusLong && ag && ag.model_solution) {
        extraBits.push(`<pre class="review-solution">${escapeHtml(String(ag.model_solution))}</pre>`);
      }
      if (!pending && ag && ag.student_feedback && ag.student_feedback !== note) {
        extraBits.push(`<p class="review-hint">${escapeHtml(String(ag.student_feedback))}</p>`);
      }
      const extra = extraBits.join("");
      return `
        <li class="review-row">
          <span class="review-num">№${escapeHtml(String(it.num ?? "—"))}</span>
          <span class="status-chip ${cls}">${escapeHtml(label)}</span>
          <span class="review-note">${escapeHtml(note)}</span>
          ${extra}
        </li>`;
    })
    .join("");
  const teacherComment = String(item.teacher_comment || "").trim();
  const displayScore = item.teacher_score != null ? item.teacher_score : item.score;
  const lit = review.literacy && typeof review.literacy === "object" ? review.literacy : null;
  const litScore = review.literacy_score;
  const litKeys = [
    ["gk1", "ГК1"],
    ["gk2", "ГК2"],
    ["gk3", "ГК3"],
    ["gk4", "ГК4"],
    ["fk1", "ФК1"],
  ];
  const litHtml = lit
    ? `<div class="review-literacy">
        <p class="review-literacy-title">Грамотность${
          litScore != null && litScore !== "" ? ` · ${escapeHtml(String(litScore))} / 8` : ""
        }</p>
        <div class="review-criteria">${litKeys
          .filter(([k]) => lit[k] != null)
          .map(([k, lab]) => `<span class="review-crit">${lab} ${escapeHtml(String(lit[k]))}</span>`)
          .join("")}</div>
        ${
          lit.fipi_reason
            ? `<p class="review-hint">${escapeHtml(String(lit.fipi_reason))}</p>`
            : ""
        }
      </div>`
    : "";

  return `
    <div class="work-focus">
      <div class="work-focus-bar">
        <button type="button" class="btn btn-ghost btn-compact" id="btn-back-dashboard">← Назад в меню</button>
        <div class="work-focus-brand">EduSense <span class="beta-badge">BETA</span></div>
      </div>
      <div class="card">
        <p class="kicker">Разбор</p>
        <h1>${escapeHtml(item.title || "Работа")}</h1>
        ${renderOgeScoreCard(item)}
        ${
          studentOgeResult(item)
            ? ""
            : `<p class="sub">${escapeHtml(String(displayScore ?? "—"))} / ${escapeHtml(
                String(item.max_score ?? "—")
              )}${item.grade ? ` · оценка ${escapeHtml(String(item.grade))}` : ""}</p>`
        }
        ${
          teacherComment
            ? `<div class="teacher-comment" role="status">
                <p class="teacher-comment-label">Комментарий учителя</p>
                <p>${escapeHtml(teacherComment)}</p>
              </div>`
            : ""
        }
        ${
          rows
            ? `<ul class="review-list">${rows}</ul>${litHtml}`
            : `<p class="sub">Детальный разбор пока недоступен.</p>`
        }
        <button class="btn btn-secondary" id="btn-back-dashboard-foot">Назад в кабинет</button>
      </div>
    </div>
  `;
}

function setNavOpen(open) {
  const dash = document.getElementById("dash-shell");
  const btn = document.getElementById("nav-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!dash) return;
  dash.classList.toggle("is-nav-open", !!open);
  btn?.setAttribute("aria-expanded", open ? "true" : "false");
  btn?.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
  if (backdrop) backdrop.hidden = !open;
}

function bindMobileNav() {
  const toggle = document.getElementById("nav-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  toggle?.addEventListener("click", () => {
    const dash = document.getElementById("dash-shell");
    setNavOpen(!dash?.classList.contains("is-nav-open"));
  });
  backdrop?.addEventListener("click", () => setNavOpen(false));
}

function syncTelegramChrome() {
  const tgApi = typeof window !== "undefined" ? window.EduSenseTG : null;
  if (!tgApi || !tgApi.isTelegramMiniApp) {
    document.documentElement.classList.remove("tg-mainbutton-on");
    return;
  }
  document.documentElement.classList.add("is-telegram-miniapp");
  document.body?.classList.add("is-telegram-miniapp");
  if (state.step === "work" && !state.loading) {
    document.documentElement.classList.add("tg-mainbutton-on");
    tgApi.setMainButton({
      text: "Сдать работу",
      visible: true,
      enabled: true,
      onClick: () => {
        submitWork();
      },
    });
  } else {
    document.documentElement.classList.remove("tg-mainbutton-on");
    tgApi.hideMainButton();
  }
}

function isRnoTitle(title) {
  return String(title || "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .startsWith("работа над ошибками");
}

function collectStudentNotifications() {
  const dash = state.dashboard || {};
  const out = [];
  (dash.active || []).forEach((a) => {
    const title = a.title || a.code || "Работа";
    const rno = isRnoTitle(title);
    out.push({
      id: `${rno ? "rno" : "active"}-${a.id || a.code}`,
      kind: rno ? "rno" : "submit",
      title: rno ? "Назначено РНО" : "Новая работа",
      text: title,
      tab: rno ? "progress" : "home",
      code: a.code,
    });
  });
  (dash.completed || []).forEach((a) => {
    out.push({
      id: `done-${a.id || a.code}-${a.submitted_at || ""}`,
      kind: "ai",
      title: "Результаты проверки",
      text: a.title || a.code || "Работа",
      tab: "progress",
      code: a.code,
    });
  });
  return out;
}

function openStudentNotification(item) {
  if (!item) return;
  if (item.tab) state.tab = item.tab;
  render();
}

function mountStudentChrome() {
  if (state.step !== "dashboard") return;
  if (typeof EduSenseNotifications === "undefined") return;
  EduSenseNotifications.mount(document.getElementById("notif-root"), {
    collect: collectStudentNotifications,
    onSelect: openStudentNotification,
  });
}

function syncExamCopyGuard() {
  const on = state.step === "work" && !!(state.assignment && state.assignment.block_copy);
  document.documentElement.classList.toggle("block-copy-exam", on);
}

let copyGuardInstalled = false;
function installCopyGuard() {
  if (copyGuardInstalled) return;
  copyGuardInstalled = true;
  const blocked = () => state.step === "work" && !!(state.assignment && state.assignment.block_copy);
  const prevent = (e) => {
    if (!blocked()) return;
    e.preventDefault();
  };
  ["copy", "cut", "paste", "contextmenu", "dragstart"].forEach((ev) => {
    document.addEventListener(ev, prevent, true);
  });
  document.addEventListener(
    "keydown",
    (e) => {
      if (!blocked()) return;
      const key = String(e.key || "").toLowerCase();
      if ((e.ctrlKey || e.metaKey) && ["c", "v", "x"].includes(key)) {
        e.preventDefault();
      }
    },
    true
  );
}

function render() {
  const root = document.getElementById("app");
  if (state.step === "work" && !state.assignment) {
    state.step = "dashboard";
  }
  const inShell = state.step === "dashboard";
  const inWork =
    state.step === "work" || state.step === "review" || state.step === "done";
  document.documentElement.classList.toggle("exam-on", inWork);
  root.classList.toggle("is-entry", state.step === "join");
  root.classList.toggle("is-menu", false);
  root.classList.toggle("is-dashboard", inShell);
  root.classList.toggle("is-shell", inShell);
  root.classList.toggle("is-work", inWork);
  if (state.step === "join") root.innerHTML = renderJoin();
  else if (state.step === "dashboard") root.innerHTML = renderDashboard();
  else if (state.step === "work") root.innerHTML = renderWork();
  else if (state.step === "review") root.innerHTML = renderReview();
  else root.innerHTML = renderDone();
  bind();
  syncExamCopyGuard();
  syncTelegramChrome();
  mountStudentChrome();
  if (typeof EduSenseTour !== "undefined") {
    const exam = state.step === "work" || state.step === "review";
    if (!exam) {
      EduSenseTour.maybeStart({
        goToTab: (tab) => {
          if (!tab || state.step !== "dashboard") return;
          if (state.tab === tab) return;
          state.tab = tab;
          render();
        },
        screen: () => state.step,
        tab: () => state.tab,
        hasClass: () => !!(state.classCode && state.step !== "join"),
      });
    }
    EduSenseTour.onRendered();
  }
  if (typeof EduSensePWA !== "undefined") EduSensePWA.sync();
  scheduleFocusPlayer({ visible: state.step === "dashboard" && !state.loading });
  markDashboardReady();
}

function logoutToStart() {
  stopWorkTimer();
  clearSession();
  try {
    localStorage.removeItem(LS_AUTH);
    localStorage.removeItem(LS_HOME);
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined" && window.EduSenseTG?.isTelegramMiniApp) {
    goToJoinFresh({ clearSessionFlag: true });
    return;
  }
  window.location.href = "/?leave=1";
}

function goToJoinFresh({ clearSessionFlag = false } = {}) {
  stopWorkTimer();
  if (clearSessionFlag) {
    clearSession();
    state.savedEntry = null;
    state.name = "";
    state.studentId = "";
    state.classCode = "";
    state.className = "";
    state.subject = "";
    state.exam = "";
    state.dashboard = null;
  }
  state.step = "join";
  state.tab = "home";
  state.assignment = null;
  state.answers = {};
  state.workStarted = false;
  state.startedAt = null;
  state.result = null;
  state.reviewItem = null;
  state.closed = false;
  state.codeError = "";
  state.nameError = "";
  state.previewTitle = "";
  state.previewSubject = "";
  state.timerEndsAt = null;
  state.timerExpired = false;
  state.timerPromptShown = false;
  state.timerPausedRemaining = null;
  if (clearSessionFlag) state.code = "";
  navigateStudent("/student/join", { replace: true });
  render();
}

async function loadDashboard({ navigate = true } = {}) {
  if (!state.classCode || !state.name) {
    goToJoinFresh({ clearSessionFlag: false });
    return;
  }
  state.step = "dashboard";
  state.loading = true;
  render();
  try {
    const data = await api(
      `/api/student/tasks?class_code=${encodeURIComponent(state.classCode)}&student_name=${encodeURIComponent(
        state.name
      )}`
    );
    state.dashboard = data;
    state.className = data.class_name || state.className;
    state.subject = data.subject || state.subject;
    state.exam = data.exam || state.exam;
    state.step = "dashboard";
    if (navigate) navigateStudent("/student/dashboard");
    if (state.pendingAssignmentCode) {
      const code = state.pendingAssignmentCode;
      state.pendingAssignmentCode = null;
      await openWorkByCode(code);
      return;
    }
  } catch (err) {
    showToast(err.message || "Не удалось загрузить список работ", "error");
    state.dashboard = state.dashboard || { active: [], completed: [], stats: {} };
    state.step = "dashboard";
    state.tab = "home";
    if (navigate) navigateStudent("/student/dashboard");
  } finally {
    state.loading = false;
    render();
  }
}

async function openWorkByCode(code) {
  stopWorkTimer();
  state.loading = true;
  render();
  try {
    // already submitted → clear result screen (optional retry if still accepting)
    const doneCard = findCompletedCard(code);
    if (doneCard) {
      state.result = resultFromCompletedCard(doneCard);
      state.assignment = {
        code: doneCard.code,
        title: doneCard.title,
        questions: [],
        accepting_submissions: doneCard.accepting_submissions !== false,
        status: doneCard.status,
        deadline: doneCard.deadline || doneCard.deadline_at,
      };
      state.step = "done";
      showToast("Эта работа уже сдана", "info");
      return;
    }

    const { ok, status, data } = await fetchAssignmentByCode(code);
    if (ok && data && data.already_submitted) {
      const card = findCompletedCard(code);
      if (card) {
        state.result = resultFromCompletedCard(card);
        state.assignment = {
          code: card.code,
          title: card.title,
          questions: [],
          accepting_submissions: false,
          status: card.status,
        };
        state.step = "done";
        showToast("Эта работа уже сдана", "info");
        return;
      }
      showToast("Эта работа уже сдана", "info");
      state.step = "dashboard";
      return;
    }
    if (status === 403 || (ok && !isAccepting(data))) {
      const why = isPastDeadline(data) ? "Срок сдачи истёк" : "Приём ответов закрыт";
      showToast(why, "error");
      state.step = "dashboard";
      return;
    }
    if (!ok) {
      showToast(detailMessage(data, "Работа не найдена"), "error");
      state.step = "dashboard";
      return;
    }
    state.assignment = data;
    state.code = data.code || code;
    state.answers = {};
    state.workStarted = false;
    state.startedAt = null;
    state.result = null;
    state.timerExpired = false;
    state.timerEndsAt = null;
    state.timerPromptShown = false;
    state.timerPausedRemaining = null;
    const savedBag = loadLocalProgress(data.code);
    const saved = savedBag && savedBag.answers ? savedBag.answers : null;
    if (savedBag && savedBag.started_at) {
      state.startedAt = savedBag.started_at;
    }
    if (savedBag && savedBag.timer_paused && savedBag.timer_remaining_ms != null) {
      const left = Number(savedBag.timer_remaining_ms);
      if (Number.isFinite(left)) {
        state.timerPausedRemaining = Math.max(0, left);
        if (savedBag.timer_expired || left <= 0) {
          state.timerExpired = true;
          state.timerPausedRemaining = 0;
        }
      }
    }
    state.lastSavedAt = savedBag && savedBag.updated_at ? Number(savedBag.updated_at) : null;
    (data.questions || []).forEach((q) => {
      ensureAnswer(q.num, q.part);
      if (saved && saved[q.num]) {
        state.answers[q.num] = { ...state.answers[q.num], ...saved[q.num] };
      }
    });
    if (state.classCode && data.class_code) {
      state.classCode = data.class_code;
    }
    enterWork();
  } catch {
    showToast("Не удалось открыть работу", "error");
    state.step = "dashboard";
  } finally {
    state.loading = false;
    render();
    if (state.step === "work") startWorkTimer();
  }
}

function openReview(code) {
  const list = (state.dashboard && state.dashboard.completed) || [];
  const item = list.find((x) => String(x.code).toUpperCase() === String(code).toUpperCase());
  if (!item) {
    showToast("Разбор пока не готов", "info");
    return;
  }
  if (answersLockedOf(item)) {
    showToast(reviewLockedHint(item), "info");
    return;
  }
  const hasItems = !!(item.ai_review && Array.isArray(item.ai_review.items) && item.ai_review.items.length);
  const hasTeacher = !!(item.teacher_comment || item.teacher_score != null);
  if (!item.has_review && !hasItems && !hasTeacher) {
    showToast("Разбор пока не готов", "info");
    return;
  }
  state.reviewItem = item;
  state.step = "review";
  render();
}

function bind() {
  document.getElementById("btn-open")?.addEventListener("click", () => joinStudent(false));
  document.getElementById("btn-board-all")?.addEventListener("click", () => {
    state.showFullBoard = !state.showFullBoard;
    render();
  });
  document.querySelectorAll("[data-warmup]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (loadWarmupResult()) return;
      const quiz = warmupQuizSpec();
      const choice = Number(btn.getAttribute("data-warmup"));
      const correct = choice === quiz.correct;
      saveWarmupResult({ answered: true, choice, correct });
      if (correct) {
        addBonusXp(quiz.xp);
        showToast(`+${quiz.xp} XP · ответ верный!`, "success");
        const card = document.querySelector(".warmup-card");
        card?.classList.add("is-pop");
      } else {
        showToast("Неверно — правильный ответ подсвечен", "info");
      }
      render();
    });
  });
  document.querySelector(".streak-card.is-ignite .streak-card-flame")?.addEventListener("animationend", (e) => {
    if (e.animationName && e.animationName !== "streakIgnite") return;
    markStreakIgniteDone();
    document.querySelector(".streak-card")?.classList.remove("is-ignite");
  });
  document.getElementById("btn-open-cabinet")?.addEventListener("click", () => {
    state.tab = "home";
    state.closed = false;
    loadDashboard({ navigate: true });
  });
  document.getElementById("btn-check-code")?.addEventListener("click", () => previewByCode());
  document.getElementById("inp-code")?.addEventListener("input", (e) => {
    applyCodeFromInput(e.target);
    state.codeError = "";
    const saved = loadSavedEntry();
    state.savedEntry = saved;
    if (state.savedEntry && !String(state.name || "").trim()) {
      state.name = state.savedEntry.name;
    }
    if (state.closed) {
      state.closed = false;
      state.previewTitle = "";
      state.previewSubject = "";
      render();
    }
  });
  document.getElementById("inp-code")?.addEventListener("paste", (e) => {
    const text = (e.clipboardData || window.clipboardData)?.getData("text") || "";
    if (!text) return;
    e.preventDefault();
    const el = e.target;
    el.value = text;
    applyCodeFromInput(el);
    state.codeError = "";
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
  document.getElementById("inp-name")?.addEventListener("input", (e) => {
    state.name = e.target.value;
    state.nameError = "";
  });
  document.getElementById("inp-code")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (state.closed) previewByCode();
      else joinStudent(false);
    }
  });
  document.getElementById("inp-name")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      joinStudent(false);
    }
  });

  document.querySelectorAll(".js-student-logout").forEach((btn) => {
    btn.addEventListener("click", () => logoutToStart());
  });

  bindMobileNav();

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      if (!tab) {
        setNavOpen(false);
        return;
      }
      state.tab = tab;
      setNavOpen(false);
      render();
    });
  });

  document.querySelectorAll("[data-nav-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-nav-action");
      setNavOpen(false);
      if (action === "invite") {
        state.showInvite = true;
        state.showLive = false;
        render();
      }
      if (action === "live") {
        state.showLive = true;
        state.showInvite = false;
        render();
      }
    });
  });

  document.getElementById("btn-try-pro")?.addEventListener("click", () => {
    state.showInvite = true;
    state.showLive = false;
    render();
  });
  document.getElementById("btn-close-invite")?.addEventListener("click", () => {
    state.showInvite = false;
    render();
  });
  document.getElementById("invite-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "invite-backdrop") {
      state.showInvite = false;
      render();
    }
  });
  document.getElementById("btn-close-live")?.addEventListener("click", () => {
    state.showLive = false;
    render();
  });
  document.getElementById("live-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "live-backdrop") {
      state.showLive = false;
      render();
    }
  });

  document.querySelectorAll("[data-tab-jump]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab-jump");
      if (!tab) return;
      state.tab = tab;
      setNavOpen(false);
      render();
    });
  });

  document.querySelectorAll("[data-jump-num]").forEach((btn) => {
    btn.addEventListener("click", () => {
      jumpToTaskNum(btn.getAttribute("data-jump-num"));
    });
  });
  document.getElementById("task-jump-select")?.addEventListener("change", (e) => {
    jumpToTaskNum(e.target.value);
  });

  document.querySelectorAll("[data-start]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-start");
      if (code) openWorkByCode(code);
    });
  });

  document.querySelectorAll("[data-review]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-review");
      if (code) openReview(code);
    });
  });
  document.querySelectorAll("[data-review-locked]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-review-locked");
      const list = (state.dashboard && state.dashboard.completed) || [];
      const item = list.find((x) => String(x.code).toUpperCase() === String(code || "").toUpperCase());
      showToast(reviewLockedHint(item), "info");
    });
  });

  const backToDash = () => {
    state.reviewItem = null;
    state.tab = "progress";
    state.step = "dashboard";
    render();
  };
  document.getElementById("btn-back-dashboard")?.addEventListener("click", backToDash);
  document.getElementById("btn-back-dashboard-foot")?.addEventListener("click", backToDash);

  document.querySelectorAll("[data-mode]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (state.timerExpired) {
        showToast("Время вышло — ответы зафиксированы", "info");
        return;
      }
      const num = Number(btn.getAttribute("data-num"));
      const mode = btn.getAttribute("data-mode");
      ensureAnswer(num).mode = mode;
      render();
    });
  });

  document.querySelectorAll("[data-answer]").forEach((el) => {
    el.addEventListener("input", () => {
      if (state.timerExpired) return;
      const num = Number(el.getAttribute("data-answer"));
      let value = el.value;
      if (el.getAttribute("data-math-decimal") === "1" && typeof coerceMathDecimalInput === "function") {
        const next = coerceMathDecimalInput(value);
        if (next !== value) {
          const pos = el.selectionStart;
          el.value = next;
          value = next;
          if (typeof pos === "number") {
            try {
              el.setSelectionRange(pos, pos);
            } catch (_) {}
          }
        }
      }
      ensureAnswer(num).text = value;
      if (state.assignment) saveLocalProgress(state.assignment.code, state.answers, state.startedAt);
      updateWorkMetaDom();
    });
  });

  document.querySelectorAll("[data-photo]").forEach((input) => {
    input.addEventListener("change", async () => {
      if (state.timerExpired) {
        showToast("Время вышло — ответы зафиксированы", "info");
        return;
      }
      const num = Number(input.getAttribute("data-photo"));
      const file = input.files?.[0];
      if (!file) return;
      if (file.size > 1_400_000) {
        showToast("Сжатое фото лучше до ~1 МБ", "error");
      }
      const dataUrl = await readFileAsDataURL(file, 1280);
      ensureAnswer(num).photoDataUrl = dataUrl;
      ensureAnswer(num).mode = "photo";
      if (state.assignment) saveLocalProgress(state.assignment.code, state.answers, state.startedAt);
      render();
    });
  });

  document.querySelectorAll(".photo-box label").forEach((label) => {
    label.addEventListener("click", (e) => {
      if (state.timerExpired) {
        e.preventDefault();
        return;
      }
      const input = label.querySelector("input");
      if (e.target !== input) input?.click();
    });
  });

  document.getElementById("btn-submit")?.addEventListener("click", submitWork);

  const backToMenu = () => {
    const hadTimer = !!timerMinutesOf(state.assignment);
    stopWorkTimer();
    if (state.assignment) {
      saveLocalProgress(state.assignment.code, state.answers, state.startedAt, { pauseTimer: true });
    }
    state.pendingAssignmentCode = null;
    state.tab = "home";
    state.step = "dashboard";
    state.assignment = null;
    state.answers = {};
    state.workStarted = false;
    state.startedAt = null;
    state.timerEndsAt = null;
    state.timerExpired = false;
    state.timerPausedRemaining = null;
    showToast(
      hadTimer ? "Можно доделать позже · таймер на паузе" : "Черновик сохранён · можно доделать позже",
      "info"
    );
    loadDashboard({ navigate: true });
  };
  document.getElementById("btn-back-menu")?.addEventListener("click", backToMenu);

  const againToDash = () => {
    stopWorkTimer();
    state.pendingAssignmentCode = null;
    state.result = null;
    state.answers = {};
    state.workStarted = false;
    state.startedAt = null;
    state.tab = "progress";
    state.step = "dashboard";
    state.assignment = null;
    state.timerEndsAt = null;
    state.timerExpired = false;
    loadDashboard({ navigate: true });
  };
  document.getElementById("btn-again")?.addEventListener("click", againToDash);
  document.getElementById("btn-again-foot")?.addEventListener("click", againToDash);
  document.getElementById("btn-exit-done")?.addEventListener("click", () => {
    logoutToStart();
  });
  document.getElementById("btn-view-review")?.addEventListener("click", () => {
    if (answersLockedOf(state.result) || answersLockedOf(state.assignment)) {
      showToast(reviewLockedHint(state.result || state.assignment), "info");
      return;
    }
    const code = (state.result && state.result.code) || (state.assignment && state.assignment.code);
    if (code) {
      // ensure dashboard has completed card
      const item = findCompletedCard(code);
      if (item && item.ai_review) {
        state.reviewItem = item;
        state.step = "review";
        render();
        return;
      }
      if (state.result && state.result.ai_review) {
        state.reviewItem = {
          code,
          title: state.result.title || (state.assignment && state.assignment.title) || "Работа",
          score: state.result.score,
          max_score: state.result.max_score,
          ai_review: state.result.ai_review,
          has_review: true,
          teacher_score: state.result.teacher_score ?? null,
          teacher_comment: state.result.teacher_comment || null,
          teacher_reviewed_at: state.result.teacher_reviewed_at || null,
          oge: state.result.oge || (state.result.ai_review && state.result.ai_review.oge) || null,
          subject: state.result.subject || state.subject,
        };
        state.step = "review";
        render();
        return;
      }
    }
    showToast("Разбор пока не готов", "info");
  });

  if (typeof OgeRusUI !== "undefined") {
    const root = document.getElementById("app");
    OgeRusUI.bind(root, {
      onAnswer: (num, value) => {
        if (state.timerExpired) return;
        ensureAnswer(num).text = value;
        if (state.assignment) saveLocalProgress(state.assignment.code, state.answers, state.startedAt);
        updateWorkMetaDom();
      },
      readOnly: !!state.timerExpired,
    });
  }
}

function readFileAsDataURL(file, maxSide = 1280) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale);
      const h = Math.round(img.height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/jpeg", 0.82));
    };
    img.onerror = reject;
    img.src = url;
  });
}

async function previewByCode() {
  state.codeError = "";
  applyCodeFromInput(document.getElementById("inp-code"));
  state.code = normalizeJoinCode(state.code);
  if (!state.code) {
    state.codeError = "Введите код класса или работы";
    render();
    return;
  }
  state.loading = true;
  render();
  try {
    // try join-style discovery via assignment GET first; class codes 404 here — that's ok
    const { ok, status, data } = await fetchAssignmentByCode(state.code);
    if (status === 403 || (ok && !isAccepting(data))) {
      applyClosedPreview(data);
      return;
    }
    if (!ok) {
      // may be a class code — clear hard error, soft hint
      state.closed = false;
      state.previewTitle = "";
      state.previewSubject = "";
      state.codeError = "";
      showToast("Код принят — укажите ФИО и нажмите «Приступить»", "info");
      return;
    }
    state.closed = false;
    state.previewTitle = data.title || "";
    state.previewSubject = data.subject || "";
    state.codeError = "";
  } catch {
    state.codeError = "Не удалось проверить код";
  } finally {
    state.loading = false;
    render();
  }
}

async function joinStudent(useSavedName = false) {
  state.codeError = "";
  state.nameError = "";
  applyCodeFromInput(document.getElementById("inp-code"));
  const code = normalizeJoinCode(state.code);
  state.code = code;
  if (!code) {
    state.codeError = "Введите код класса или работы";
    render();
    return;
  }
  const name = useSavedName
    ? (state.savedEntry && state.savedEntry.name) || state.name
    : state.name;
  if (!name || String(name).trim().length < 2) {
    state.nameError = "Укажите имя и фамилию";
    showToast("Укажите имя и фамилию", "error");
    render();
    return;
  }
  state.loading = true;
  render();
  try {
    const data = await api("/api/student/join", {
      method: "POST",
      body: JSON.stringify({ code, name: String(name).trim() }),
    });
    applySessionFromJoin(data);
    state.closed = false;
    state.codeError = "";
    // после join по коду работы — сразу открыть её с дашборда
    state.pendingAssignmentCode =
      data.join_kind === "assignment" && data.assignment && data.assignment.code
        ? data.assignment.code
        : null;
    await loadDashboard({ navigate: true });
  } catch (err) {
    const closed = closedDetail(err.data);
    if (err.status === 403 || closed) {
      applyClosedPreview(closed || err.data || {});
      if (closed && closed.code) state.code = String(closed.code).toUpperCase();
      if (hasCabinetSession()) {
        showToast("Работа недоступна — открываем кабинет", "info");
        state.pendingAssignmentCode = null;
        await loadDashboard({ navigate: true });
        return;
      }
    } else if (hasCabinetSession()) {
      showToast(err.message || "Не удалось войти по коду", "error");
      state.pendingAssignmentCode = null;
      await loadDashboard({ navigate: true });
      return;
    } else {
      state.codeError = err.message || "Не удалось войти";
      state.closed = false;
    }
  } finally {
    state.loading = false;
    render();
  }
}

async function submitWork() {
  if (!state.assignment) return;
  if (!isAccepting(state.assignment)) {
    showToast(isPastDeadline(state.assignment) ? "Срок сдачи истёк" : "Приём ответов закрыт", "error");
    return;
  }
  if (!window.confirm("Точно сдать?")) return;
  document.querySelectorAll("[data-answer]").forEach((el) => {
    const num = Number(el.getAttribute("data-answer"));
    if (!num) return;
    ensureAnswer(num).text = el.value;
  });
  state.loading = true;
  render();
  try {
    const answers = state.assignment.questions.map((q) => {
      const a = ensureAnswer(q.num, q.part);
      return {
        num: q.num,
        text: a.mode === "text" ? a.text : "",
        photo_data_url: a.mode === "photo" ? a.photoDataUrl || null : null,
      };
    });
    const startedAt = state.startedAt || new Date().toISOString();
    const body = {
      student_name: String(state.name || "").trim(),
      answers,
      started_at: startedAt,
    };
    const result = await api(`/api/assignments/${encodeURIComponent(state.assignment.code)}/submit`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    clearLocalProgress(state.assignment.code);
    stopWorkTimer();
    const locked = answersLockedOf(state.assignment);
    state.result = {
      ...result,
      code: state.assignment.code,
      title: state.assignment.title,
      subject: state.assignment.subject || state.subject,
      has_review: locked
        ? false
        : !!(result.ai_review && Array.isArray(result.ai_review.items)),
      answers_locked: locked,
      hide_answers: !!(state.assignment && state.assignment.hide_answers),
      deadline: state.assignment.deadline || state.assignment.deadline_at || null,
      ai_review: locked ? null : result.ai_review,
    };
    state.startedAt = null;
    state.timerEndsAt = null;
    state.timerExpired = false;
    state.step = "done";
    if (result.already_submitted) {
      showToast("Эта работа уже была сдана", "info");
    } else {
      showToast("Работа сдана", "success");
    }
  } catch (err) {
    showToast(err.message || "Ошибка отправки", "error");
  } finally {
    state.loading = false;
    render();
  }
}

async function boot() {
  installFigureLightbox();
  installCopyGuard();
  window.addEventListener("popstate", () => {
    if (state.step === "work" || state.step === "review" || state.step === "done") return;
    if (pathWantsJoin() && !hasCabinetSession()) {
      state.step = "join";
      render();
      return;
    }
    if (hasCabinetSession() && !pathWantsJoin()) {
      state.tab = "home";
      loadDashboard({ navigate: false });
      return;
    }
    state.step = "join";
    render();
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (state.showInvite) {
        state.showInvite = false;
        render();
        return;
      }
      if (state.showLive) {
        state.showLive = false;
        render();
        return;
      }
      setNavOpen(false);
    }
  });

  const params = new URLSearchParams(location.search);
  const tgEntry =
    (typeof window !== "undefined" && window.EduSenseTG && window.EduSenseTG.entryCode) || "";
  const code = normalizeJoinCode(params.get("code") || params.get("join") || tgEntry || "");
  if (code) state.code = code;
  if (typeof window !== "undefined" && window.EduSenseTG?.isTelegramMiniApp) {
    document.documentElement.classList.add("is-telegram-miniapp");
    document.body?.classList.add("is-telegram-miniapp");
  }

  const authUser = readAuthUser();
  if (authUser && String(authUser.full_name || "").trim()) {
    state.name = String(authUser.full_name).trim();
  }

  let session = loadSession();
  if (!session && authUser) {
    if (authUser.class_code) {
      applyKnownClassroom({
        name: authUser.full_name,
        classCode: authUser.class_code,
        className: authUser.class_name || "",
        subject: authUser.subject || "",
        exam: authUser.exam || "",
      });
      session = loadSession();
    } else {
      const home = loadStudentHome();
      if (home && homeMatchesUser(home, authUser)) {
        applyKnownClassroom(home);
        session = loadSession();
      }
    }
  }

  if (session) {
    state.savedEntry = { code: session.classCode, name: session.name };
    state.name = session.name;
    state.classCode = session.classCode;
    state.studentId = session.studentId;
    state.className = session.className;
    state.subject = session.subject;
    state.exam = session.exam;
    if (!state.code) state.code = session.classCode;
  }

  // Явный /student/join без сессии — форма входа
  if (pathWantsJoin() && !hasCabinetSession()) {
    state.step = "join";
    render();
    return;
  }

  // Есть класс — сразу на главную кабинета (даже если в URL остался ?code=)
  if (hasCabinetSession() && !pathWantsJoin()) {
    const urlCode = String(state.code || "").trim().toUpperCase();
    const classCode = String(state.classCode || "").trim().toUpperCase();
    if (urlCode && urlCode !== classCode) {
      state.pendingAssignmentCode = urlCode;
    }
    await loadDashboard({ navigate: !pathWantsDashboard() });
    return;
  }

  if (authUser && code && !pathWantsJoin()) {
    state.name = String(authUser.full_name || state.name || "").trim();
    await joinStudent(false);
    return;
  }

  if (pathWantsDashboard()) {
    navigateStudent("/student/join", { replace: true });
    state.step = "join";
    render();
    return;
  }

  render();

  if (state.code && !pathWantsJoin()) {
    try {
      const { ok, status, data } = await fetchAssignmentByCode(state.code);
      if (status === 403 || (ok && !isAccepting(data))) {
        applyClosedPreview(data);
        render();
        return;
      }
      if (ok) {
        state.previewTitle = data.title || "";
        state.previewSubject = data.subject || "";
        state.closed = false;
        state.codeError = "";
        render();
      }
    } catch {
      /* сеть — оставляем пустую форму */
    }
  }
}

boot().catch((err) => {
  console.error(err);
  try {
    state.step = hasCabinetSession() ? "dashboard" : "join";
    state.loading = false;
    render();
  } catch (_) {
    const root = document.getElementById("app");
    if (root) {
      root.innerHTML =
        '<div class="card entry-card"><h1>Не удалось открыть кабинет</h1><p class="sub">Обновите страницу. Если не поможет — выйдите и войдите снова.</p></div>';
    }
  }
});
