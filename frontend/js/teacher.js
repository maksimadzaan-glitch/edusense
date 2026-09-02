"use strict";

const API_BASE = "";

const EXAM_TYPES = [{ id: "oge", label: "ОГЭ" }];

const SUBJECTS = {
  oge: ["Математика", "Русский язык"],
};

const SUBJECT_TILES = [
  {
    id: "Математика",
    label: "Математика",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 20 12 4l8 16H4z"/><path d="M8.2 16h7.6"/></svg>`,
  },
  {
    id: "Русский язык",
    label: "Русский язык",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 20h6"/><path d="M8 20c0-7 4-12 10-14"/><path d="M14.5 8.5c1.8 2.2 3.2 5.2 3.5 9"/><path d="m16 5 2.2-1.2 1.3 2.3"/></svg>`,
  },
];

const GRADES = {};

const NAV = [
  { id: "home", label: "Главная", icon: "layoutDashboard" },
  { id: "live", label: "Живой урок", icon: "rocket", badge: { text: "LIVE", kind: "live" } },
  { id: "students", label: "Ученики", icon: "users" },
  { id: "assignments", label: "Задания", icon: "bookOpen" },
  { id: "tests", label: "Тесты", icon: "fileCheck" },
  { id: "analytics", label: "Аналитика", icon: "barChart3", badge: { text: "PRO", kind: "pro" } },
  { id: "invite", label: "Пригласить", icon: "gift", action: "invite" },
];

// Настройки убраны из основного меню и живут в подвале сайдбара.
const NAV_SETTINGS = { id: "settings", label: "Настройки", icon: "settings" };

const ICONS = {
  home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z"/></svg>`,
  layoutDashboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  bookOpen: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/></svg>`,
  fileCheck: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg>`,
  barChart3: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"/><path d="M14 3v5h5M9 13h6M9 17h4"/></svg>`,
  flask: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 3h6M10 3v6.2L5.4 18a2.4 2.4 0 0 0 2.1 3.5h9a2.4 2.4 0 0 0 2.1-3.5L14 9.2V3"/><path d="M8.2 14h7.6"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19h16M7 16V9M12 16V5M17 16v-7"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>`,
  copy: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>`,
  qr: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM15 13h2v2h-2zM19 13h2v2h-2zM15 17h2v2h-2zM19 17h2v4h-6v-2"/></svg>`,
  printer: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 8V4h10v4"/><rect x="4" y="8" width="16" height="9" rx="2"/><path d="M7 17v4h10v-4"/><path d="M7 12h2"/></svg>`,
  spark: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3z"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 4v11"/><path d="m8 11 4 4 4-4"/><path d="M5 19h14"/></svg>`,
  key: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="8" cy="15" r="4"/><path d="M11.5 12.5 20 4h3v3l-5 5"/><path d="M16 8h3"/></svg>`,
  rocket: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91 0z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>`,
  gift: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>`,
};

function icon(name) {
  return ICONS[name] || "";
}

const GRADING_MODES = [
  {
    id: "ai_assist",
    title: "Черновик баллов + утверждение",
    desc: "ИИ проверяет Часть 2 по критериям ФИПИ и готовит баллы, вы утверждаете в 1 клик.",
    mark: "Ч",
    badge: "ai",
  },
  {
    id: "manual",
    title: "Только ручная проверка",
    desc: "Ученики сдают фото/текст, вы оцениваете вручную.",
    mark: "Р",
  },
  {
    id: "autopilot",
    title: "Автоматическая проверка",
    desc: "Оценка выставляется сразу только за тестовую часть (Часть 1).",
    mark: "А",
  },
];

const BETA_VARIANT_LIMIT = 5;

/** App state (аналог React state) */
const state = {
  user: null,
  step: "create", // create | code | dashboard
  tab: "home",
  form: {
    name: "",
    examType: "oge",
    grade: "9",
    subject: "Математика",
  },
  classroom: null,
  classrooms: [],
  submitting: false,
  showQr: false,
  showInvite: false,
  /** true = комната урока; false = хаб /live */
  liveInRoom: false,
  connectedStudents: [],
  liveStudents: [],
  liveSubmittedCount: 0,
  studentsBoard: {
    loading: false,
    loadedFor: null,
    error: null,
    roster: [],
    students: [],
    inviteOpen: false,
    rosterDraft: "",
    saving: false,
    query: "",
    sort: "name",
    profileName: null,
    profileLoading: false,
    profileAnalytics: null,
    profileHistory: [],
    targetMark: 4,
    remediating: false,
  },
  assignmentsBoard: {
    loading: false,
    loadedFor: null, // class access_code
    error: null,
    items: [],
    expandedCode: null,
    submissions: {}, // code -> { loading, error, items }
    answerKeys: {}, // code -> { loading, error, items }
    listFilter: "active", // active | closed | all
    issueOpen: false,
    issueStep: "choose", // choose | settings | recent
    issueSettings: {
      deadlineAt: "",
      timeLimitMinutes: "",
      shuffleVariants: true,
    },
    menuOpenCode: null,
    whoModalCode: null,
    whoTab: "submitted", // submitted | not_started
    gradingId: null, // submission id being saved
    expandedSubId: null, // submission id with answers open
    patchingCode: null,
  },
  analyticsBoard: {
    loading: false,
    loadedFor: null, // class code + query key
    error: null,
    mode: "class", // class | student
    student: "",
    assignmentCode: "",
    data: null,
    creatingRemediation: false,
    creatingRno: false,
    selectedNum: null,
    drawer: null,
    subjectFilter: "",
  },
  generator: {
    generating: false,
    variant: null,
    selectedTaskId: null,
    _readyToast: "",
    publishOpen: false,
    publishSuccess: null,
    publishBusy: false,
    publishAudience: "",
    publishAudienceNames: [],
    publishBlockCopy: false,
    publishHideAnswers: true,
    gradingMode: "ai_assist",
    publishDeadline: "",
    publishTimeLimit: "",
    publishTimeCustom: false,
    publishShuffle: true,
    size: "standard", // mini | standard | full
    difficulty: "medium", // easy | medium | hard
    focusId: "",
    _slots: null,
    _flipBook: 0,
    vary: false, // опционально чуть изменить формулировки
    // эталон по умолчанию выкл.; для русского включается при выборе класса
    etalon: false,
    lastSourceNote: "",
    examUi: "",
    export: {
      pngWithAnswer: false,
      pdfAnswerSheet: false,
      previewTheme: "dark",
      linkQrOpen: false,
      a4Preview: false,
    },
    published: [],
  },
  part2Grades: {},
};

const TEACHER_TAB_OVERLAY = new Set(["assignments", "students", "analytics", "home"]);

function pageTransition(fn, opts) {
  const PT = window.EduSensePageTransition;
  if (PT?.run) return PT.run(fn, opts);
  return fn();
}

async function switchTeacherTab(next) {
  if (!next || next === state.tab) return;
  if (window.EduSensePageTransition?.isBusy?.()) return;
  await pageTransition(
    async () => {
      state.tab = next;
      if (next !== "live") state.liveInRoom = false;
      setNavOpen(false);
      render();
      const tasks = [];
      if (next === "assignments") {
        tasks.push(loadAssignmentsBoard());
        tasks.push(loadStudentsBoard());
      } else if (next === "students") {
        tasks.push(loadStudentsBoard());
      } else if (next === "home") {
        tasks.push(loadStudentsBoard());
        tasks.push(loadAssignmentsBoard());
        tasks.push(loadHomeInsights());
      } else if (next === "analytics") {
        tasks.push(loadAnalyticsBoard());
      } else if (next === "live") {
        startLiveRoster();
      }
      await Promise.all(tasks);
    },
    { overlay: TEACHER_TAB_OVERLAY.has(next), minMs: TEACHER_TAB_OVERLAY.has(next) ? 0 : 200 }
  );
}

const DIFFICULTY_LEVELS = [
  { id: "easy", label: "Лёгкий", hint: "5 простых сюжетов 1–5, базовые №6–19" },
  { id: "medium", label: "Обычный", hint: "Как на экзамене: печи, участок, маршруты" },
  { id: "hard", label: "Сложный", hint: "Плотнее расчёты в 1–5 и геометрия" },
];

const DIFFICULTY_LEVELS_RUS = [
  { id: "easy", label: "База", hint: "Проще 2–9, проще изложение и сочинение" },
  { id: "medium", label: "КИМ", hint: "Как на экзамене" },
  { id: "hard", label: "Хардкор", hint: "Жёстче 2–9, сложнее тексты, изложение ≥80, сочинение ≥90" },
];

function difficultyLevelsForUi() {
  return teacherSubjectCode() === "russian" ? DIFFICULTY_LEVELS_RUS : DIFFICULTY_LEVELS;
}

/** Полные длины КИМ (синхрон с backend/services/subject_blueprints.py). */
const KIM_COUNTS = {
  oge: {
    Математика: 25,
    "Русский язык": 13,
  },
};

function kimCount(exam, subject) {
  const ex = String(exam || "oge").toLowerCase();
  const sub = String(subject || "").trim();
  const table = KIM_COUNTS[ex] || {};
  if (table[sub]) return table[sub];
  if (ex === "oge") return 15;
  return 10;
}

/** Размеры варианта: standard/full = полный КИМ выбранного предмета. */
function genSizesFor(exam, subject) {
  const full = kimCount(exam, subject);
  const mini = Math.max(5, Math.ceil(full / 3));
  return {
    mini: { count: mini, label: `Мини · ${mini}` },
    standard: { count: full, label: `КИМ · ${full}` },
    full: { count: full, label: `Полный · ${full}` },
  };
}

function currentGenSizes() {
  const exam = state.classroom?.exam_type || state.form.examType || "oge";
  const subject = state.classroom?.subject || state.form.subject || "Математика";
  return genSizesFor(exam, subject);
}

/** Эталон для русского скрыт: учитель собирает обычный банк, не фиксированный КИМ. */
function supportsEtalonMode(_exam, _subject) {
  return false;
}

/** Эталон не включаем сами: иначе русский всегда собирает один КИМ про соль. */
function defaultEtalonForSubject(_exam, _subject) {
  return false;
}

function wantsEtalonGenerate() {
  const exam = state.classroom?.exam_type || state.form.examType || "oge";
  const subject = state.classroom?.subject || state.form.subject || "Математика";
  return supportsEtalonMode(exam, subject) && !!state.generator.etalon;
}

function etalonBadgeHtml(variant) {
  if (!variant || !variant.etalon) return "";
  if (teacherSubjectCode(variant) === "russian") return "";
  const prov = variant.provenance || null;
  const bits = ["Эталонный вариант"];
  if (prov && prov.year) bits.push(String(prov.year));
  if (prov && prov.variant_code) bits.push(String(prov.variant_code));
  return `<p class="etalon-badge" title="Импортированный эталон (не «официальный КИМ ФИПИ»)">${escapeHtml(
    bits.join(" · ")
  )}</p>`;
}

function renderEtalonToggle(g) {
  const exam = state.classroom?.exam_type || state.form.examType || "oge";
  const subject = state.classroom?.subject || state.form.subject || "Математика";
  if (!supportsEtalonMode(exam, subject)) return "";
  return `
    <label class="gen-etalon-opt" title="Целиком импортированный вариант без AI-правок">
      <input type="checkbox" id="chk-etalon" ${g.etalon ? "checked" : ""} />
      <span>Эталонный вариант</span>
      <em>без AI · фиксированные формулировки и ключи</em>
    </label>
  `;
}

function renderMutatorToggle(g) {
  if (wantsEtalonGenerate()) return "";
  return `<label class="tc-mutator" title="Математика: сюжет 1–5 общий, числа разные. Русский: изложение и сочинение общие, тест 2–9 — те же правила, другие формулировки.">
    <input type="checkbox" id="chk-mutator" ${g.publishShuffle ? "checked" : ""} />
    <span><i class="tc-die" aria-hidden="true"><b></b><b></b><b></b><b></b><b></b><b></b></i> Генератор аналогичных заданий</span>
  </label>`;
}

function loadUser() {
  if (window.EduSenseAuth?.getUser) return window.EduSenseAuth.getUser();
  try {
    return JSON.parse(localStorage.getItem("edusense_user") || "null");
  } catch (_) {
    return null;
  }
}

function examLabel(id) {
  return EXAM_TYPES.find((x) => x.id === id)?.label || id;
}

function gradeDisplay(classroom) {
  if (!classroom) return "—";
  if (classroom.exam_type === "oge") return "9";
  if (classroom.exam_type === "ege") return classroom.grade || "10–11";
  return classroom.grade || "—";
}

/** Красивое отображаемое имя — без путаницы «11» vs «кл. 4» */
function classTitle(classroom) {
  if (!classroom) return "Класс";
  const name = String(classroom.name || "").trim();
  const subject = String(classroom.subject || "").trim();
  const grade = String(gradeDisplay(classroom));
  const exam = examLabel(classroom.exam_type);

  const bare = name.match(/^(\d{1,2})(?:\s*[·\-–]\s*(.+))?$/i);
  if (bare) {
    const typed = bare[1];
    const rest = (bare[2] || subject || "").trim();
    // Цифра в названии не совпадает с классом экзамена — собираем из спецификаций
    if (typed !== grade) {
      return rest ? `${exam} ${grade} · ${rest}` : `${exam} · кл. ${grade}`;
    }
    return rest ? `${typed} · ${rest}` : `${typed} · ${exam}`;
  }

  if (!name) return subject ? `${subject} · ${exam}` : exam;
  return name;
}

function classLetterOf(classroom) {
  const name = String(classroom?.name || "").trim();
  const m = name.match(/(\d{1,2})\s*['"«]?\s*([A-Za-zА-Яа-яЁё])/);
  return m ? m[2].toUpperCase() : "";
}

function classSwitcherTitle(classroom) {
  const grade = gradeDisplay(classroom);
  const letter = classLetterOf(classroom);
  const subject = String(classroom?.subject || "").trim() || "Класс";
  const letterBit = letter ? ` '${letter}'` : "";
  return `👥 ${grade}${letterBit} · ${subject}`;
}

function sidebarStudentCount() {
  const roster = state.studentsBoard.roster || [];
  if (roster.length) return roster.length;
  const students = state.studentsBoard.students || [];
  return students.length || 0;
}

function classSubtitle(classroom) {
  if (!classroom) return "";
  const parts = [
    examLabel(classroom.exam_type),
    classroom.subject,
    `кл. ${gradeDisplay(classroom)}`,
  ].filter(Boolean);
  return parts.join(" · ");
}

function initials(name) {
  return (name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || "")
    .join("");
}

function shortStudentName(name) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "Ученик";
  if (parts.length === 1) return parts[0];
  return `${parts[0]} ${parts[1][0].toUpperCase()}.`;
}

const TOPIC_RU = {
  "syntax basis": "Грамматическая основа",
  syntax_basis: "Грамматическая основа",
  "punctuation matching": "Пунктуация",
  punctuation_matching: "Пунктуация",
  "punctuation placement": "Знаки препинания",
  punctuation_placement: "Знаки препинания",
  "spelling explanation": "Орфография",
  spelling_explanation: "Орфография",
  "grammar form": "Грамматика",
  grammar_form: "Грамматика",
  "summary writing": "Изложение",
  summary_writing: "Изложение",
  "essay writing": "Сочинение",
  essay_writing: "Сочинение",
};

function topicLabelRu(raw) {
  const t = String(raw || "").trim();
  if (!t) return t;
  if (/[А-Яа-яЁё]/.test(t)) return t;
  const key = t.toLowerCase().replace(/[_\s]+/g, " ");
  const snake = t.toLowerCase().replace(/[\s]+/g, "_");
  return TOPIC_RU[key] || TOPIC_RU[snake] || t;
}

function showToast(message, type = "info") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => {
    el.classList.add("is-out");
    setTimeout(() => el.remove(), 250);
  }, 2600);
}

async function api(path, options = {}) {
  let response;
  const headers = {
    "Content-Type": "application/json",
    ...(window.EduSenseAuth?.authHeaders ? window.EduSenseAuth.authHeaders(options.headers || {}) : options.headers || {}),
  };
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch (_) {
    throw new Error("Не удалось подключиться к серверу.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch (_) {}

  if (response.status === 401 && !String(path).includes("/auth/me")) {
    window.EduSenseAuth?.clearSession?.({ forgetAccount: false });
    window.location.href = "/#auth";
    throw new Error("Сессия истекла. Войдите снова.");
  }

  if (!response.ok) {
    const detail = data?.detail ?? `Ошибка ${response.status}`;
    let msg;
    if (typeof detail === "string") msg = detail;
    else if (Array.isArray(detail) && detail.length) {
      const first = detail[0];
      msg =
        (first && (first.msg || first.message)) ||
        "Не удалось выполнить запрос. Обновите страницу.";
    } else if (detail && typeof detail === "object" && detail.message) {
      msg = String(detail.message);
    } else {
      msg = "Не удалось выполнить запрос. Обновите страницу.";
    }
    throw new Error(msg);
  }
  return data;
}

function syncFormDefaults() {
  state.form.examType = "oge";
  state.form.grade = "9";
  const subjects = SUBJECTS.oge || [];
  if (!subjects.includes(state.form.subject)) {
    state.form.subject = subjects[0] || "Математика";
  }
}

function inviteUrl(code) {
  return `${window.location.origin}/student?code=${encodeURIComponent(code)}`;
}

function qrImageUrl(code, size = 360) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(inviteUrl(code))}`;
}

async function copyText(text, okMsg = "Скопировано") {
  const value = String(text || "");
  if (!value) return false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      showToast(okMsg, "success");
      return true;
    }
  } catch (_) {
    /* fallback below */
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = value;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, value.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    if (ok) {
      showToast(okMsg, "success");
      return true;
    }
  } catch (_) {
    /* ignore */
  }
  window.prompt("Скопируйте код вручную (Ctrl+C):", value);
  return false;
}

async function copyClassCode() {
  const code = state.classroom?.access_code;
  if (!code) return;
  await copyText(code, "Код скопирован");
}

async function copyInvite() {
  return copyClassCode();
}

async function copyInviteLink() {
  return copyClassCode();
}

async function copyClassInviteLink() {
  const code = state.classroom?.access_code;
  if (!code) return;
  await copyText(inviteUrl(code), "Ссылка скопирована");
}

function printClassQr() {
  const code = state.classroom?.access_code;
  if (!code) return;
  const url = inviteUrl(code);
  const opened = openPrintWindow(
    `QR · ${code}`,
    `<div class="a4-sheet" style="min-height:auto;display:flex;align-items:center;justify-content:center;">
      ${eduSenseWatermarkHtml()}
      <div class="a4-inner" style="text-align:center;">
        ${eduSenseBrandHtml()}
        <h1>Код класса</h1>
        <p class="muted">Отсканируйте, чтобы войти</p>
        <img alt="QR" src="${qrImageUrl(code, 360)}" width="360" height="360" style="width:360px;height:360px;border:10px solid #0f172a;border-radius:18px;background:#fff;"/>
        <p style="margin:22px 0 8px;font-family:ui-monospace,monospace;font-size:32px;font-weight:800;letter-spacing:.16em;">${escapeHtml(
          code
        )}</p>
        <p class="muted">${escapeHtml(url)}</p>
      </div>
    </div>`,
    brandedExamPrintCss()
  );
  if (!opened) showToast("Разрешите всплывающие окна для печати QR", "error");
}


function playSoftSubmitChime() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    if (!state._audioCtx) state._audioCtx = new Ctx();
    const ctx = state._audioCtx;
    if (ctx.state === "suspended") ctx.resume();
    const t0 = ctx.currentTime;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(523.25, t0);
    o.frequency.exponentialRampToValueAtTime(659.25, t0 + 0.12);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(0.08, t0 + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.45);
    o.connect(g);
    g.connect(ctx.destination);
    o.start(t0);
    o.stop(t0 + 0.5);
  } catch (_) {}
}

function liveFeedHtml(names) {
  const students = state.liveStudents || [];
  if (students.length) {
    return students
      .map((s) => {
        const name = s.name || "";
        return `
      <div class="live-chip live-chip-${escapeHtml(s.badge || "offline")}">
        <span class="live-avatar">${escapeHtml(initials(name))}</span>
        <span>${escapeHtml(s.emoji || "")} ${escapeHtml(shortStudentName(name))} — ${escapeHtml(s.label || "")}</span>
      </div>`;
      })
      .join("");
  }
  if (!names.length) {
    return `<p class="live-empty">Пока никого — пусть ученики введут код на телефоне</p>`;
  }
  return names
    .map(
      (name) => `
      <div class="live-chip">
        <span class="live-avatar">${escapeHtml(initials(name))}</span>
        <span>🟢 ${escapeHtml(shortStudentName(name))} в сети</span>
      </div>`
    )
    .join("");
}

function liveRosterActive() {
  if (!state.classroom?.access_code) return false;
  if (state.step === "code") return true;
  if (state.step !== "dashboard") return false;
  return state.tab === "home" || state.tab === "live";
}

function openLiveRoom() {
  state.tab = "live";
  state.liveInRoom = true;
  state.showQr = false;
  startLiveRoster();
  render();
}

function openLiveHub() {
  state.tab = "live";
  state.liveInRoom = false;
  state.showQr = false;
  startLiveRoster();
  render();
}

function patchLiveUi() {
  const names = state.connectedStudents || [];
  const n = names.length;
  const count = document.getElementById("live-count");
  const label = document.getElementById("live-label");
  const feed = document.getElementById("live-feed");
  if (count) count.textContent = String(n);
  if (label) {
    label.textContent = n ? "Ученики подключаются" : "Ожидаем учеников…";
  }
  if (feed) feed.innerHTML = liveFeedHtml(names);

  const people = homeLivePeople();
  const homeCount = document.getElementById("home-live-count");
  const homeGrid = document.getElementById("home-live-grid");
  if (homeCount) homeCount.textContent = String(people.length);
  if (homeGrid) {
    homeGrid.innerHTML = people.length ? homeLiveCardsHtml(people) : homeLiveEmptyHtml();
    homeGrid.classList.toggle("is-empty", !people.length);
  }
  const pulse = document.getElementById("dash-hero-pulse");
  if (pulse) pulse.textContent = homeHeroAccessLine();
}

function applyLivePayload(payload, announce) {
  const data = payload && typeof payload === "object" ? payload : {};
  const students = Array.isArray(data.students) ? data.students : [];
  const names = (data.names || students.map((s) => s.name) || [])
    .map((n) => String(n || "").trim())
    .filter(Boolean);
  const prev = new Set((state.connectedStudents || []).map((n) => n.toLowerCase()));
  const prevSubmitted = Number(state.liveSubmittedCount || 0);
  const submitted = Number(data.submitted_count || 0);
  if (announce) {
    names.forEach((name) => {
      if (!prev.has(name.toLowerCase())) {
        showToast(`${shortStudentName(name)} в сети`, "success");
      }
    });
    if (submitted > prevSubmitted && prevSubmitted >= 0 && state._liveReady) {
      const delta = submitted - prevSubmitted;
      playSoftSubmitChime();
      showToast(delta === 1 ? "Ученик сдал работу" : `Сдано работ: +${delta}`, "success");
      // refresh assignments counter without full page reload
      try {
        loadAssignmentsBoard(true);
      } catch (_) {}
    }
  }
  state.connectedStudents = names;
  state.liveStudents = students;
  state.liveSubmittedCount = submitted;
  if (data.active_assignment_code) {
    state._liveActiveAssignment = data.active_assignment_code;
  }
  // mirror submissions progress into board cache when present
  if (students.length && data.active_assignment_code) {
    const key = String(data.active_assignment_code).toUpperCase();
    const items = students
      .filter((s) => s && s.submitted)
      .map((s) => ({
        student_name: s.name,
        status: "submitted",
        score: s.score,
        answers: [],
        submitted_at: true,
      }));
    const prevBox = state.assignmentsBoard.submissions[key] || {};
    state.assignmentsBoard.submissions[key] = {
      loading: false,
      error: null,
      items: items.length ? items : prevBox.items || [],
    };
  }
  patchLiveUi();
}

function applyLiveNames(names, announce) {
  applyLivePayload({ names, students: [], submitted_count: state.liveSubmittedCount || 0 }, announce);
}

function stopLiveRoster() {
  if (state._liveEs) {
    try {
      state._liveEs.close();
    } catch (_) {}
    state._liveEs = null;
  }
  if (state._liveTimer) {
    clearInterval(state._liveTimer);
    state._liveTimer = null;
  }
  state._liveFor = null;
  state._liveReady = false;
}

async function pollLiveRoster(announce) {
  const code = state.classroom?.access_code;
  if (!code || !liveRosterActive()) return;
  try {
    const data = await api(`/api/classes/${encodeURIComponent(code)}/live-status`);
    const first = !state._liveReady;
    state._liveReady = true;
    applyLivePayload(data || {}, announce && !first);
  } catch (_) {
    try {
      const data = await api(`/api/classes/${encodeURIComponent(code)}/roster`);
      const first = !state._liveReady;
      state._liveReady = true;
      applyLiveNames(data?.names || [], announce && !first);
    } catch (__) {}
  }
}

function startLiveRoster() {
  const code = state.classroom?.access_code;
  if (!code || !liveRosterActive()) {
    stopLiveRoster();
    return;
  }
  if (state._liveFor === code && state._liveTimer) return;

  stopLiveRoster();
  state._liveFor = code;
  state._liveReady = false;
  pollLiveRoster(false);
  // Authenticated short poll every 4s (EventSource cannot send Bearer token)
  state._liveTimer = setInterval(() => pollLiveRoster(true), 4000);
}

function stepsBar(active) {
  return `
    <div class="steps" aria-hidden="true">
      <div class="step-dot ${active >= 1 ? "is-active" : ""} ${active > 1 ? "is-done" : ""}"><span></span></div>
      <div class="step-dot ${active >= 2 ? "is-active" : ""}"><span></span></div>
    </div>
  `;
}

function brandRow() {
  if (window.EduSenseBrand?.logoHtml) return window.EduSenseBrand.logoHtml({ className: "brand-row" });
  return window.EduSenseAuth?.logoHtml
    ? window.EduSenseAuth.logoHtml({ className: "brand-row" })
    : `<div class="brand-row es-logo"><span class="es-logo-mark" aria-hidden="true"><img src="/assets/edusense-mark-192.png?v=9" alt="" width="38" height="38"/></span><span class="es-logo-text"><span class="es-logo-name">EduSense</span><span class="es-logo-beta">BETA</span></span></div>`;
}

function hasExistingClasses() {
  return Array.isArray(state.classrooms) && state.classrooms.length > 0;
}

async function refreshTeacherClasses() {
  if (!state.user?.id) return [];
  const list = await api(`/api/classes/by-teacher/${state.user.id}`);
  state.classrooms = Array.isArray(list) ? list : [];
  return state.classrooms;
}

function selectClassroom(classroom, opts) {
  if (!classroom) return;
  const keepTab = !!(opts && opts.keepTab);
  const tab = state.tab;
  state.classroom = classroom;
  state.step = "dashboard";
  state.tab = keepTab ? tab : "home";
  state.generator.variant = null;
  state.generator.selectedTaskId = null;
  state.generator.publishOpen = false;
  state.generator.examUi = "";
  state.generator.lastSourceNote = "";
  // math → обычный банк; русский → эталон kim по умолчанию
  state.generator.etalon = defaultEtalonForSubject(
    classroom.exam_type,
    classroom.subject
  );
  state.connectedStudents = [];
  state.studentsBoard = {
    loading: false,
    loadedFor: null,
    error: null,
    roster: [],
    students: [],
    inviteOpen: false,
    rosterDraft: "",
    saving: false,
    query: "",
    sort: "name",
    profileName: null,
    profileLoading: false,
    profileAnalytics: null,
    profileHistory: [],
    targetMark: 4,
    remediating: false,
  };
  state.assignmentsBoard = {
    loading: false,
    loadedFor: null,
    error: null,
    items: [],
    expandedCode: null,
    submissions: {},
    answerKeys: {},
    listFilter: "active",
    issueOpen: false,
    issueStep: "choose",
    issueSettings: {
      deadlineAt: "",
      timeLimitMinutes: "",
      shuffleVariants: true,
    },
    menuOpenCode: null,
    whoModalCode: null,
    whoTab: "submitted",
    gradingId: null,
    expandedSubId: null,
    patchingCode: null,
  };
  state.analyticsBoard = {
    loading: false,
    loadedFor: null,
    error: null,
    mode: "class",
    student: "",
    assignmentCode: "",
    data: null,
    creatingRemediation: false,
    creatingRno: false,
    selectedNum: null,
    drawer: null,
    subjectFilter: teacherSubjectCode() || "",
  };
  localStorage.setItem("edusense_classroom", JSON.stringify(classroom));
}

function startCreateClass() {
  state.step = "create";
  state.form.name = "";
  syncFormDefaults();
  render();
}

function cancelCreateClass() {
  if (state.classroom) {
    state.step = "dashboard";
    render();
    return;
  }
  const fallback = state.classrooms[0];
  if (fallback) {
    selectClassroom(fallback);
    render();
    return;
  }
  state.step = "create";
  render();
}

function renderCreate() {
  syncFormDefaults();
  const { name, examType, subject } = state.form;
  const extra = hasExistingClasses();

  return `
    <div class="flow-shell">
      <div class="orb orb-a"></div>
      <div class="orb orb-b"></div>
      <div class="flow-wrap">
        ${brandRow()}
        ${stepsBar(1)}
        <div class="flow-card">
          <p class="flow-eyebrow">${extra ? "Новая комната" : "Шаг 1 · Создание"}</p>
          <h1 class="flow-title">${
            extra ? "Создайте ещё<br/>один класс" : "Соберите класс<br/>за минуту"
          }</h1>
          <p class="flow-sub">${
            extra
              ? "Тот же аккаунт учителя — новый предмет ОГЭ. Старые классы останутся в списке."
              : "ОГЭ: математика или русский язык — сразу получите код для учеников."
          }</p>

          <div class="field">
            <label for="class-name">Название класса</label>
            <input id="class-name" type="text" maxlength="120" value="${escapeHtml(name)}"
              placeholder="Например, 9-А Математика" />
          </div>

          <div class="field">
            <label>Экзамен</label>
            <div class="exam-grid" role="radiogroup" aria-label="Экзамен">
              ${EXAM_TYPES.map(
                (t) => `
                <button type="button" class="exam-option ${examType === t.id ? "is-active" : ""}"
                  data-exam="${t.id}" aria-pressed="${examType === t.id}">${t.label}</button>`
              ).join("")}
            </div>
          </div>

          <p class="hint-fixed">Для ОГЭ класс фиксирован: 9</p>

          <div class="field">
            <label>Предмет</label>
            <div class="subject-seg" role="radiogroup" aria-label="Предмет">
              ${SUBJECT_TILES.map(
                (s) => `
                <button type="button" class="subject-pill ${subject === s.id ? "is-active" : ""}"
                  data-subject="${escapeHtml(s.id)}" aria-pressed="${subject === s.id}">
                  ${s.icon}
                  <span>${escapeHtml(s.label)}</span>
                </button>`
              ).join("")}
            </div>
          </div>

          <button class="btn-primary" id="btn-create" data-tour="create-class" ${state.submitting ? "disabled" : ""}>
            ${state.submitting ? "Создание…" : "Получить код доступа →"}
          </button>
          ${
            extra
              ? `<button type="button" class="btn-ghost" id="btn-cancel-create" style="width:100%;margin-top:10px">← Назад к классам</button>`
              : ""
          }
        </div>
      </div>
    </div>
  `;
}

function renderCode() {
  const c = state.classroom;
  if (!c) return renderCreate();
  const names = state.connectedStudents || [];
  const n = names.length;

  return `
    <div class="flow-shell">
      <div class="orb orb-a"></div>
      <div class="orb orb-b"></div>
      <div class="flow-wrap">
        ${brandRow()}
        ${stepsBar(2)}
        <div class="flow-card">
          <p class="flow-eyebrow">Шаг 2 · Готово</p>
          <h1 class="flow-title" style="font-size:1.55rem;margin-bottom:12px">${escapeHtml(classTitle(c))}</h1>

          <div class="spec-pills">
            <span class="spec-pill">${examLabel(c.exam_type)}</span>
            <span class="spec-pill">Класс ${escapeHtml(gradeDisplay(c))}</span>
            <span class="spec-pill">${escapeHtml(c.subject)}</span>
          </div>

          <div class="code-hero">
            <p class="code-kicker">Код класса</p>
            <p class="code-display" id="class-code-value">${escapeHtml(c.access_code)}</p>
            <button type="button" class="btn-copy-link" id="btn-copy-link" data-tour="copy-code">
              ${icon("copy")}
              Скопировать код
            </button>
          </div>

          <div class="live-status" aria-live="polite">
            <span class="live-ping" aria-hidden="true"></span>
            <div class="live-copy">
              <strong id="live-label">${n ? "Ученики подключаются" : "Ожидаем учеников…"}</strong>
              <span>Подключилось: <b id="live-count">${n}</b></span>
            </div>
          </div>
          <div class="live-feed" id="live-feed">${liveFeedHtml(names)}</div>

          <div class="code-actions">
            <button type="button" class="btn-secondary" id="btn-qr">
              ${icon("qr")}
              QR на проектор
            </button>
            <button type="button" class="btn-secondary" id="btn-print-qr">
              ${icon("printer")}
              Печать QR-кода
            </button>
          </div>

          <button class="btn-primary" id="btn-to-dashboard">
            Перейти в рабочую панель →
          </button>
        </div>
      </div>
    </div>

    ${renderQrProjector(c.access_code)}
  `;
}

function renderQrProjector(code) {
  if (!state.showQr || !code) return "";
  return `
    <div class="modal-backdrop qr-projector" id="qr-backdrop">
      <div class="modal-card qr-projector-card" role="dialog" aria-modal="true" aria-labelledby="qr-modal-title">
        <button type="button" class="qr-modal-close" id="btn-close-qr" aria-label="Закрыть">×</button>
        <p class="qr-projector-kicker" id="qr-modal-title">Наведите камеру</p>
        <img alt="QR код класса" src="${qrImageUrl(code, 420)}" />
        <p class="qr-projector-code">${escapeHtml(code)}</p>
        <p class="qr-projector-hint">Покажите этот экран на проекторе</p>
        <button type="button" class="btn-primary qr-copy-link" id="btn-copy-qr-link">
          ${icon("copy")}
          Скопировать ссылку на урок
        </button>
      </div>
    </div>`;
}

function liveClassBadge(classroom) {
  const grade = String(gradeDisplay(classroom) || "");
  const letter = classLetterOf(classroom);
  return letter ? `${grade}${letter}` : grade || "Кл";
}

function liveClassLabel(classroom) {
  const grade = String(gradeDisplay(classroom) || "—");
  const letter = classLetterOf(classroom);
  return letter ? `Класс ${grade}"${letter}"` : `Класс ${grade}`;
}

function renderLiveHub() {
  const c = state.classroom;
  const names = state.connectedStudents || [];
  const n = names.length;
  const onlineLabel = n ? `${n} в сети` : "Никого нет";
  const code = c?.access_code || "—";
  return `
    <div class="live-hub-page reveal">
      <div class="live-hub-page-top">
        <button type="button" class="nav-toggle" id="nav-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="app-sidebar">
          <span class="nav-toggle-bars" aria-hidden="true"></span>
        </button>
        <div class="live-hub-page-head">
          <h1 class="live-hub-page-title">
            <span class="live-hub-page-title-text">Живой урок</span>
            <span class="live-hub-live-pill">LIVE</span>
          </h1>
          <p class="live-hub-page-sub">Комната урока в реальном времени</p>
        </div>
        <div class="live-hub-page-tools" id="notif-root"></div>
      </div>

      <div class="live-hub-panel">
        <div class="live-hub-panel-head">
          <div>
            <span class="live-hub-kicker">LIVE · Хаб комнаты</span>
            <h2 class="live-hub-panel-title">Управление уроком</h2>
            <p class="live-hub-panel-lead">
              Откройте комнату текущего класса, следите за подключением учеников и выведите QR-код на проектор.
            </p>
          </div>
        </div>

        <div class="live-hub-class-row">
          <div class="live-hub-class-meta">
            <div class="live-hub-class-avatar" aria-hidden="true">${escapeHtml(liveClassBadge(c))}</div>
            <div>
              <div class="live-hub-class-line">
                <span class="live-hub-class-name">${escapeHtml(liveClassLabel(c))}</span>
                <span class="live-hub-online">${escapeHtml(onlineLabel)}</span>
              </div>
              <p class="live-hub-class-code">
                Код подключения:
                <span class="live-hub-code-mono">${escapeHtml(code)}</span>
              </p>
            </div>
          </div>
          <button type="button" class="live-hub-open-btn" id="btn-enter-live-room">
            Открыть комнату →
          </button>
        </div>
      </div>
    </div>
  `;
}

function renderLiveLesson() {
  const c = state.classroom;
  const names = state.connectedStudents || [];
  const n = names.length;
  const title = classTitle(c);
  return `
    <div class="live-room reveal">
      <header class="live-room-header">
        <button type="button" class="nav-toggle live-room-nav-toggle" id="nav-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="app-sidebar">
          <span class="nav-toggle-bars" aria-hidden="true"></span>
        </button>
        <button type="button" class="live-room-back" id="btn-live-back" aria-label="Назад к Live">
          ← Назад
        </button>
        <div class="live-room-title-wrap">
          <h2 class="live-room-title">${escapeHtml(title)}</h2>
          <span class="live-onair">
            <span class="live-onair-dot" aria-hidden="true"></span>
            В эфире
          </span>
        </div>
        <button type="button" class="btn-secondary live-room-qr-btn" id="btn-qr">
          ${icon("qr")}
          QR-код
        </button>
      </header>

      <section class="glass live-room-body">
        <div class="live-status" aria-live="polite">
          <span class="live-ping" aria-hidden="true"></span>
          <div class="live-copy">
            <strong id="live-label">${n ? "Ученики подключаются" : "Ожидаем учеников…"}</strong>
            <span>Подключилось: <b id="live-count">${n}</b></span>
          </div>
        </div>
        <div class="live-feed" id="live-feed">${liveFeedHtml(names)}</div>
        <div class="live-room-actions">
          <button type="button" class="btn-secondary" id="btn-print-qr">
            ${icon("printer")}
            Печать QR-кода
          </button>
          <button type="button" class="btn-primary" id="btn-qr-secondary">
            ${icon("qr")}
            Показать QR для подключения
          </button>
        </div>
      </section>
    </div>
    ${renderQrProjector(c.access_code)}
  `;
}

function renderLiveTab() {
  if (state.liveInRoom) return renderLiveLesson();
  return renderLiveHub();
}

function emptyStudentsSvg() {
  return `
    <svg viewBox="0 0 320 140" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <rect x="20" y="30" width="280" height="90" rx="18" stroke="rgba(255,255,255,0.1)" fill="rgba(94,234,212,0.05)"/>
      <circle cx="70" cy="75" r="18" fill="rgba(94,234,212,0.18)" stroke="rgba(153,246,228,0.5)"/>
      <circle cx="118" cy="75" r="18" fill="rgba(232,168,124,0.12)" stroke="rgba(232,168,124,0.35)"/>
      <circle cx="166" cy="75" r="18" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" stroke-dasharray="4 4"/>
      <path d="M210 62h70M210 75h54M210 88h62" stroke="rgba(255,255,255,0.15)" stroke-width="4" stroke-linecap="round"/>
      <path d="M48 22l4 12 12 4-12 4-4 12-4-12-12-4 12-4 4-12z" fill="#5eead4" opacity="0.8"/>
    </svg>
  `;
}

function codeChars(code) {
  return String(code || "")
    .split("")
    .map((ch) => `<span class="ch">${escapeHtml(ch)}</span>`)
    .join("");
}

function homeActiveAssignment() {
  const items = mergeAssignmentLists(state.assignmentsBoard.items, state.generator.published);
  return (
    items.find(
      (a) => a.status !== "closed" && a.acceptingSubmissions && a.status !== "draft"
    ) || null
  );
}

function homeTaskTotal() {
  const active = homeActiveAssignment();
  if (active?.tasksCount) return Number(active.tasksCount);
  return kimCount(state.classroom?.exam_type, state.classroom?.subject);
}

function homeLivePeople() {
  const byKey = new Map();
  (state.liveStudents || []).forEach((s) => {
    if (!s?.name) return;
    byKey.set(normalizeStudentKey(s.name), { name: s.name, ...s });
  });
  if (byKey.size) return [...byKey.values()];
  (state.studentsBoard.students || []).forEach((s) => {
    if (!s?.name) return;
    byKey.set(normalizeStudentKey(s.name), s);
  });
  (state.connectedStudents || []).forEach((name) => {
    const key = normalizeStudentKey(name);
    if (!key || byKey.has(key)) return;
    byKey.set(key, { name, last_activity_at: new Date().toISOString(), submissions_count: 0 });
  });
  return [...byKey.values()];
}

function filledAnswersCount(sub) {
  const answers = Array.isArray(sub?.answers) ? sub.answers : [];
  return answers.filter((a) => {
    const text = String(a?.text || a?.answer || "").trim();
    return !!(text || a?.has_photo || a?.hasPhoto || a?.photo_data_url || a?.photoDataUrl);
  }).length;
}

function homeStudentProgress(student, total) {
  const n = Math.max(0, Number(total) || 0);
  const live = (state.liveStudents || []).find(
    (s) => normalizeStudentKey(s.name) === normalizeStudentKey(student.name)
  );
  if (live) {
    const done = Math.min(Number(live.filled_answers || 0), n || Number(live.filled_answers || 0));
    if (live.badge === "submitted") {
      const grade = live.grade != null ? ` · ${live.grade}` : "";
      return { done: n || done, total: n, status: `🏁 Сдал${grade}`, cls: "is-done", emoji: "🏁" };
    }
    if (live.badge === "working") {
      return { done, total: n, status: "🟡 Приступил к работе", cls: "is-busy", emoji: "🟡" };
    }
    if (live.badge === "online") {
      return { done, total: n, status: "🟢 В сети", cls: "is-online", emoji: "🟢" };
    }
    return { done, total: n, status: "🔴 Не в сети", cls: "is-idle", emoji: "🔴" };
  }
  const active = homeActiveAssignment();
  if (!active) {
    return { done: 0, total: n, status: "🔴 Не в сети", cls: "is-idle", emoji: "🔴" };
  }
  const key = normalizeStudentKey(student.name);
  const items = state.assignmentsBoard.submissions[String(active.code).toUpperCase()]?.items || [];
  const sub = items.find((s) => normalizeStudentKey(s.student_name) === key);
  const filled = filledAnswersCount(sub);
  const submitted = !!(
    sub &&
    (sub.submitted_at ||
      ["submitted", "graded", "reviewed", "done"].includes(String(sub.status || "").toLowerCase()))
  );
  if (submitted) {
    const sc = sub.score != null ? ` · ${sub.score}` : "";
    return { done: n || filled, total: n, status: `🏁 Сдал${sc}`, cls: "is-done", emoji: "🏁" };
  }
  if (filled > 0) return { done: Math.min(filled, n || filled), total: n, status: "🟡 Приступил к работе", cls: "is-busy", emoji: "🟡" };
  return { done: 0, total: n, status: "🔴 Не в сети", cls: "is-idle", emoji: "🔴" };
}

function homeLiveEmptyHtml() {
  const code = state.classroom?.access_code || "EDU-XXXX";
  return `<p class="home-live-empty">Передайте код <strong>${escapeHtml(
    code
  )}</strong> ученикам. Их прогресс появится здесь в реальном времени.</p>`;
}

function homeLiveCardsHtml(people) {
  const total = homeTaskTotal();
  return people
    .map((s) => {
      const prog = homeStudentProgress(s, total);
      const pct = total ? Math.round((prog.done / total) * 100) : 0;
      return `
        <article class="home-live-card ${prog.cls}">
          <div class="home-live-card-top">
            <span class="live-avatar">${escapeHtml(initials(s.name))}</span>
            <div>
              <strong>${escapeHtml(s.name)}</strong>
              <span class="home-live-status">${escapeHtml(prog.status)}</span>
            </div>
          </div>
          <div class="home-live-bar" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">
            <i style="width:${pct}%"></i>
          </div>
          <p class="home-live-meta">${prog.done}/${total} решено</p>
        </article>`;
    })
    .join("");
}

function homeWeakTopicsInner() {
  const heat = state.analyticsBoard?.data?.heatmap || [];
  if (!heat.length) {
    return `<p class="home-widget-empty">После первых сдач здесь появятся подтипы с наименьшим % верных.</p>`;
  }
  const rows = heat
    .slice()
    .sort((a, b) => (b.wrong_pct || 0) - (a.wrong_pct || 0) || a.num - b.num)
    .slice(0, 5);
  return `<ul class="home-weak-list">${rows
    .map((h) => {
      const correct = Math.max(0, Math.round(100 - Number(h.wrong_pct || 0)));
      const topic = topicLabelRu(h.topic || "") || "без темы";
      return `<li><span>№${escapeHtml(String(h.num))} ${escapeHtml(topic)}</span><b>${correct}%</b></li>`;
    })
    .join("")}</ul>`;
}

function homeRecentWorksInner() {
  const recent = mergeAssignmentLists(
    state.assignmentsBoard.items,
    state.generator.published
  ).slice(0, 4);
  if (!recent.length) {
    return `<p class="home-widget-empty">Пока нет выданных работ. Соберите КИМ и выдайте классу.</p>`;
  }
  return `<ul class="home-recent-list">${recent
    .map((a) => {
      const n = Number(a.uniqueSubmitters || a.submissionsCount || 0);
      return `<li>
        <button type="button" data-quick="assignments">
          <strong>${escapeHtml(a.title || a.code)}</strong>
          <span>${escapeHtml(a.code)} · ${escapeHtml(submissionsCountLabel(n))}</span>
        </button>
      </li>`;
    })
    .join("")}</ul>`;
}

function startQuickTrainer() {
  state.generator.size = "mini";
  state.generator.difficulty = "easy";
  state.generator.publishTimeLimit = "5";
  state.generator._quickCount = 5;
  state.generator._autoStart = true;
  state.tab = "tests";
  render();
}

async function loadHomeInsights() {
  if (state.step !== "dashboard" || state.tab !== "home") return;
  const code = state.classroom?.access_code;
  if (!code) return;

  if (!state.analyticsBoard.data && !state.analyticsBoard.loading) {
    try {
      const data = await api(`/api/classes/${encodeURIComponent(code)}/analytics`);
      state.analyticsBoard.data = data;
      if (data?.selected_assignment_code && !state.analyticsBoard.assignmentCode) {
        state.analyticsBoard.assignmentCode = data.selected_assignment_code;
      }
      state.analyticsBoard.loadedFor = analyticsQueryKey(code, state.analyticsBoard);
      const box = document.getElementById("home-weak-body");
      if (box) box.innerHTML = homeWeakTopicsInner();
      const pulse = document.getElementById("dash-hero-pulse");
      if (pulse) pulse.textContent = homeHeroAccessLine();
    } catch (_) {}
  }

  const active = homeActiveAssignment();
  if (active?.code) {
    const key = String(active.code).toUpperCase();
    const prev = state.assignmentsBoard.submissions[key];
    if (!prev?.items && !prev?.loading) {
      try {
        const data = await api(`/api/assignments/${encodeURIComponent(key)}/submissions`);
        state.assignmentsBoard.submissions[key] = {
          loading: false,
          error: null,
          items: Array.isArray(data) ? data : [],
        };
        patchLiveUi();
      } catch (_) {}
    }
  }
}

function classHeroBadge(classroom) {
  const grade = gradeDisplay(classroom);
  const letter = classLetterOf(classroom);
  const klass = letter ? `${grade}-${letter}` : String(grade);
  return `КЛАСС ${klass} В СЕТИ`;
}

function failsCountLabel(n, topicGenitive) {
  const abs = Math.abs(Number(n) || 0) % 100;
  const last = abs % 10;
  let word = "завалов";
  if (!(abs > 10 && abs < 20)) {
    if (last === 1) word = "завал";
    else if (last >= 2 && last <= 4) word = "завала";
  }
  return `${n} ${word} ${topicGenitive}`;
}

function homeHeroAccessLine() {
  const live = (state.connectedStudents || []).length;
  const roster = sidebarStudentCount();
  if (live > 0) return `🟢 ${studentsCountLabel(live)} в сети`;
  if (roster > 0) return `🟢 ${studentsCountLabel(roster)} подключатся по коду`;
  return "🟢 Ученики подключатся по коду";
}

function renderHome() {
  const c = state.classroom;
  const people = homeLivePeople();
  const onlineN = people.length;
  const code = c.access_code || "EDU-XXXX";

  return `
    <div class="bento">
      <section class="dash-hero reveal">
        <div class="hero-orbit" aria-hidden="true">
          <div class="hero-orbit-stage">
            <span class="hero-orbit-halo"></span>
            <span class="hero-orbit-core"></span>
            <span class="hero-orbit-ring hero-orbit-ring-1"><i class="hero-orbit-dot dot-a"></i></span>
            <span class="hero-orbit-ring hero-orbit-ring-2"><i class="hero-orbit-dot dot-b"></i><i class="hero-orbit-dot dot-c"></i></span>
            <span class="hero-orbit-ring hero-orbit-ring-3"><i class="hero-orbit-dot dot-d"></i></span>
          </div>
        </div>
        <span class="dash-hero-glow dash-hero-glow-a" aria-hidden="true"></span>
        <span class="dash-hero-glow dash-hero-glow-b" aria-hidden="true"></span>
        <div class="dash-hero-inner">
          <div class="dash-hero-copy">
            <span class="dash-hero-badge">🟢 ${escapeHtml(classHeroBadge(c))}</span>
            <h2>Учительская ведомость успеваемости</h2>
            <p>Назначение работ классу, контроль живой сессии и анализ освоения тем ФИПИ.</p>
            <div class="dash-hero-actions">
              <button type="button" class="dash-hero-cta" data-quick="tests" id="btn-home-cta">Сформировать КИМ</button>
              <button type="button" class="dash-hero-live" id="btn-home-live">Живой урок</button>
            </div>
          </div>
          <div class="dash-hero-code">
            <div class="label">Живой доступ класса</div>
            <div class="big" aria-label="${escapeHtml(code)}">${escapeHtml(code)}</div>
            <button type="button" class="dash-hero-copy-btn" id="btn-copy-dash" data-tour="copy-code">📋 Скопировать ссылку для учеников</button>
            <p class="dash-hero-pulse" id="dash-hero-pulse">${escapeHtml(homeHeroAccessLine())}</p>
          </div>
        </div>
      </section>

      <section class="glass home-live reveal" id="home-live">
        <div class="home-live-head">
          <div class="home-live-badge">
            <span class="live-ping" aria-hidden="true"></span>
            Живая сессия урока
          </div>
          <span class="home-live-count">В классе: <b id="home-live-count">${onlineN}</b></span>
        </div>
        <div class="home-live-grid ${people.length ? "" : "is-empty"}" id="home-live-grid">
          ${people.length ? homeLiveCardsHtml(people) : homeLiveEmptyHtml()}
        </div>
      </section>

            <div class="home-widgets reveal">
        <section class="glass home-widget home-widget-drill">
          <div class="home-widget-head">
            <h3>Быстрая генерация КИМ</h3>
          </div>
          <p>Соберите диагностическую контрольную работу на 5 минут (задания 1–5) и назначьте классу.</p>
          <button type="button" class="btn-primary" id="btn-quick-drill">Сформировать КИМ</button>
        </section>
        <section class="glass home-widget">
          <div class="home-widget-head">
            <h3>Последние выданные работы</h3>
            <button type="button" class="btn-ghost" data-quick="assignments">Ведомость</button>
          </div>
          ${homeRecentWorksInner()}
        </section>
        <section class="glass home-widget">
          <div class="home-widget-head">
            <h3>Статистика освоения тем ФИПИ</h3>
            <button type="button" class="btn-ghost" data-quick="analytics">Открыть</button>
          </div>
          <div id="home-weak-body">${homeWeakTopicsInner()}</div>
        </section>
      </div>
    </div>
    ${renderQrProjector(c.access_code)}
  `;
}

function renderShellScreen({ title, lead, note, extraHtml = "", kicker = "В продуктовой карте" }) {
  return `
    <div class="bento">
      <section class="glass shell-screen reveal">
        <div class="kicker">${escapeHtml(kicker)}</div>
        <h2>${escapeHtml(title)}</h2>
        <p class="shell-lead">${escapeHtml(lead)}</p>
        <p class="shell-note">${escapeHtml(
          note || "Сейчас в фокусе — классы и сборка варианта. Этот раздел подключается следующим шагом."
        )}</p>
        ${extraHtml}
        <div class="actions" style="margin-top:18px">
          <button type="button" class="btn-secondary" data-quick="tests">Собрать вариант</button>
          <button type="button" class="btn-ghost" data-quick="home" style="width:auto">На главную</button>
        </div>
      </section>
    </div>
  `;
}

function demoVariant() {
  const subjectRaw = state.classroom?.subject || "Математика";
  const subject = /русск/i.test(subjectRaw) ? "Русский язык" : "Математика";
  const exam = examLabel(state.classroom?.exam_type || "oge");
  const isRus = subject === "Русский язык";
  const tasks = isRus
    ? [
        {
          id: "t1",
          num: 2,
          part: 1,
          type: "Краткий ответ",
          topic: "Орфография",
          text: "Укажите вариант ответа, в котором во всех словах одного ряда пропущена одна и та же буква.",
          answer: "1",
          maxScore: 1,
        },
        {
          id: "t2",
          num: 3,
          part: 1,
          type: "Краткий ответ",
          topic: "Пунктуация",
          text: "Расставьте знаки препинания: укажите все цифры, на месте которых должны стоять запятые.",
          answer: "124",
          maxScore: 1,
        },
      ]
    : [
        {
          id: "t1",
          num: 1,
          part: 1,
          type: "Краткий ответ",
          topic: "Числа и вычисления",
          text: "Найдите значение выражения: 2,4 · 1,5 + 3,6.",
          answer: "7,2",
          maxScore: 1,
        },
        {
          id: "t2",
          num: 2,
          part: 1,
          type: "Краткий ответ",
          topic: "Уравнения",
          text: "Решите уравнение: 3x − 7 = 8.",
          answer: "5",
          maxScore: 1,
        },
        {
          id: "t3",
          num: 20,
          part: 2,
          type: "Развёрнутый ответ",
          topic: "Геометрия",
          text: "В треугольнике ABC сторона AB равна 6, BC равна 8, угол B равен 90°. Найдите длину медианы из вершины B.",
          answer: "5",
          maxScore: 2,
        },
      ];
  return {
    id: `var-${Date.now()}`,
    title: `${exam} · ${subject} · Вариант A`,
    subject,
    exam,
    code: `ES-${Math.random().toString(36).slice(2, 6).toUpperCase()}`,
    createdAt: new Date().toISOString(),
    tasks,
  };
}

function isVariantPublished(variant) {
  if (!variant) return false;
  if (variant.isPublished) return true;
  return (state.generator.published || []).some(
    (p) => p.id === variant.id || (p.code && variant.code && p.code === variant.code)
  );
}

function markVariantPublished(variant) {
  if (!variant) return;
  variant.isPublished = true;
}

function variantShareUrl(variant) {
  if (!variant) return `${window.location.origin}/student`;
  const published = state.generator.published.find(
    (p) => p.id === variant.id || p.code === variant.code
  );
  const code = published?.code || variant.code;
  return `${window.location.origin}/student?code=${encodeURIComponent(code || "")}`;
}

function currentExportTask() {
  const v = state.generator.variant;
  if (!v) return null;
  if (!state.generator.selectedTaskId) return null;
  return v.tasks.find((t) => t.id === state.generator.selectedTaskId) || null;
}

function exportPreviewPayload() {
  const v = state.generator.variant;
  const task = currentExportTask();
  if (!v) return null;
  if (task) {
    return {
      title: `${v.title} · №${task.num}`,
      badge: `Часть ${task.part} · ${task.type}`,
      meta: task.topic,
      tasks: [task],
      answers: [{ num: task.num, answer: task.answer }],
    };
  }
  return {
    title: v.title,
    badge: `${v.exam} · ${tasksCountLabel(v.tasks.length)}`,
    meta: v.subject,
    tasks: v.tasks,
    answers: v.tasks.map((t) => ({ num: t.num, answer: t.answer })),
  };
}

const SAFE_FIGURE_KINDS = new Set([
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
]);

function _safeFigureSvg(kind, svg) {
  if (!kind || !SAFE_FIGURE_KINDS.has(kind)) return "";
  if (!svg) return "";
  if (!/class="[^"]*\b(fipi-fig|geo-fig)\b/.test(svg)) return "";
  if (!/viewBox=["']0 0 \d+(?:\.\d+)? \d+(?:\.\d+)?["']/.test(svg)) return "";
  return svg;
}

function payloadImagesHtml(task) {
  const p = task?.payload || {};
  const n = Number(task?.num);
  if (p.math_context && n >= 1 && n <= 5) return "";
  const urls = Array.isArray(p.image_urls) ? p.image_urls.slice() : [];
  const single = p.image_url || p.figure_url || task?.imageUrl || task?.image_url;
  if (single && !urls.includes(single)) urls.unshift(single);
  if (!urls.length) return "";
  const num = task?.num != null ? task.num : "";
  return (
    `<div class="task-media" aria-label="Рисунок к заданию">` +
    urls
      .map((u) => {
        let src = String(u || "").trim();
        if (!src || /^javascript:/i.test(src)) return "";
        if (typeof absolutizeMediaUrl === "function") src = absolutizeMediaUrl(src);
        if (typeof edusenseTaskImgHtml === "function") {
          return edusenseTaskImgHtml(src, num, "Рисунок");
        }
        return `<img class="task-media-img" src="${escapeHtml(src)}" alt="Рисунок" loading="lazy" crossorigin="anonymous" data-task-num="${escapeHtml(String(num))}" />`;
      })
      .filter(Boolean)
      .join("") +
    `</div>`
  );
}

function _isOgeRusTask(task) {
  const p = task?.payload || {};
  if (p.oge_rus) return true;
  const ui = String(p.ui || "");
  return ui === "oge_rus" || ui === "listening" || ui === "matching" || ui === "essay_choice";
}

function figureHtml(task) {
  if (_isOgeRusTask(task)) return "";
  const p = task?.payload || {};
  const n = Number(task?.num);
  if (p.math_context && n >= 1 && n <= 5) return "";
  const hasSvg = !!(task?.figureSvg || task?.solutionFigureSvg);
  const kind = task?.figureKind || (hasSvg ? "asset" : null);
  const mainSvg = _safeFigureSvg(kind, task?.figureSvg || "");
  const solOnly =
    !mainSvg && !!task?.solutionFigureSvg
      ? _safeFigureSvg(kind || "asset", task.solutionFigureSvg)
      : "";
  const svg = mainSvg || solOnly;
  if (!svg) return "";
  const label = solOnly
    ? `<span class="ep-solution-figure-label">Чертёж</span>`
    : "";
  return `${label}<div class="task-figure" data-figure="${escapeHtml(kind || "asset")}" role="button" tabindex="0" title="Увеличить чертёж" aria-label="Увеличить чертёж">${svg}</div>`;
}

function solutionFigureHtml(task) {
  if (_isOgeRusTask(task)) return "";
  // если чертёж уже показан на карточке из solution_figure_svg — не дублируем
  const mainSvg = _safeFigureSvg(task?.figureKind, task?.figureSvg || "");
  if (!mainSvg && task?.solutionFigureSvg) return "";
  const svg = _safeFigureSvg(task?.figureKind || "asset", task?.solutionFigureSvg || "");
  if (!svg) return "";
  // тот же SVG, что в условии — не дублируем блок «к решению»
  if (mainSvg && mainSvg === svg) return "";
  return `<div class="ep-solution-figure"><span class="ep-solution-figure-label">Чертёж к решению</span><div class="task-figure" data-figure="asset" role="button" tabindex="0" title="Увеличить чертёж" aria-label="Увеличить чертёж к решению">${svg}</div></div>`;
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

/** Предмет класса/варианта — нормализованный код math|russian|… */
function teacherSubjectCode(variant) {
  const v = variant || state.generator.variant;
  const c = state.classroom || {};
  const raw =
    (v && (v.subject_code || v.subject)) || c.subject || state.form.subject || "";
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

/** ОГЭ русский КИМ — только russian + (exam_ui/payload), без fuzzy и без math. */
function isTeacherOgeRusExam(variant) {
  if (typeof OgeRusUI === "undefined") return false;
  if (teacherSubjectCode(variant) === "math") return false;
  const v = variant || state.generator.variant;
  const c = state.classroom || {};
  const subjectRaw = (v && (v.subject || v.subject_code)) || c.subject || "";
  const meta = Object.assign({}, v || {}, {
    exam_ui: (v && v.exam_ui) || state.generator.examUi || "",
    subject: subjectRaw,
    subject_code: subjectRaw,
    exam: (v && (v.exam_code || v.exam)) || c.exam_type,
    exam_code: (v && v.exam_code) || c.exam_type,
    exam_type: c.exam_type,
  });
  // Sticky oge_rus_kim после русского не должен переживать math-класс
  if (teacherSubjectCode(variant) !== "russian" && meta.exam_ui === "oge_rus_kim") {
    meta.exam_ui = "";
  }
  if (typeof OgeRusUI.isOgeRussianExam === "function") {
    return OgeRusUI.isOgeRussianExam((v && v.tasks) || [], meta);
  }
  return typeof OgeRusUI.isOgeRusList === "function" && OgeRusUI.isOgeRusList((v && v.tasks) || []);
}

/** Текст задания: ОГЭ русский → сплит 1) 2) 3); иначе math formatter. */
function formatTeacherTaskText(taskOrText) {
  const asTask = taskOrText && typeof taskOrText === "object" ? taskOrText : null;
  const useRus =
    asTask &&
    typeof OgeRusUI !== "undefined" &&
    typeof OgeRusUI.isOgeRusTask === "function" &&
    OgeRusUI.isOgeRusTask(asTask);
  if (
    useRus &&
    typeof OgeRusUI !== "undefined" &&
    typeof OgeRusUI.formatTaskTextHtml === "function"
  ) {
    return OgeRusUI.formatTaskTextHtml(taskOrText);
  }
  const raw =
    taskOrText && typeof taskOrText === "object"
      ? String(taskOrText.text || "")
      : String(taskOrText || "");
  if (
    typeof MathOgeUI !== "undefined" &&
    typeof MathOgeUI.formatRichText === "function"
  ) {
    return MathOgeUI.formatRichText(raw);
  }
  return typeof formatMathText === "function" ? formatMathText(raw) : escapeHtml(raw);
}

function exportMediaHtml(task, paper) {
  const fig = figureHtml(task);
  const media = payloadImagesHtml(task);
  const sol = "";
  const block = `${fig}${media}${sol}`.trim();
  if (!block) return "";
  return paper ? `<div class="ep-print-media">${block}</div>` : block;
}

function isEssayPrintAnswer(task) {
  const n = Number(task?.num);
  const ui = String(task?.payload?.ui || task?.ui || "").toLowerCase();
  if (ui === "listening" || ui === "essay_choice" || ui === "essay" || ui === "summary") return true;
  return isTeacherOgeRusExam() && (n === 1 || n === 13);
}

function isExtendedPrintAnswer(task) {
  const n = Number(task?.num);
  const part = Number(task?.part);
  if (isEssayPrintAnswer(task)) return true;
  if (part === 2) return true;
  return n >= 19 && n <= 25;
}

function printAnswerLineHtml(task, paper) {
  if (!paper) return "";
  if (isExtendedPrintAnswer(task)) {
    const essay = isEssayPrintAnswer(task);
    const label = essay ? "Место для развёрнутого ответа" : "Место для решения";
    return `<div class="lined-box${essay ? " is-essay" : " is-math"}"><span class="lined-box-label">${label}</span></div>`;
  }
  return `<div class="es-print-answer-line"><b>Ответ:</b> <em>________________</em></div>`;
}

function renderPrintTaskCard(t, extras, showAnswer, paper) {
  return `
      <section class="ep-task pdf-task-card es-print-task">
        <div class="es-print-task-title">Задание №${escapeHtml(String(t.num))}</div>
        <div class="ep-task-head">
          <span class="ep-pill">Часть ${escapeHtml(String(t.part || 1))}</span>
          ${t.type ? `<span class="ep-pill">${escapeHtml(t.type)}</span>` : ""}
        </div>
        ${t.topic ? `<div class="ep-topic">${formatMathText(t.topic)}</div>` : ""}
        ${extras || `<div class="ep-body es-print-task-body">${formatTeacherTaskText(t)}</div>`}
        ${exportMediaHtml(t, paper)}
        ${printAnswerLineHtml(t, paper)}
        ${showAnswer ? solutionFigureHtml(t) : ""}
        ${
          showAnswer && Number(t.part) === 1 && t.answer
            ? `<div class="ep-answer"><span>Ключ</span><div class="ep-answer-body">${formatAnswerKey(
                t.answer,
                1
              )}</div></div>`
            : ""
        }
      </section>`;
}

function renderExportTaskBlocks(tasks, showAnswer, paper) {
  const rus = isTeacherOgeRusExam();
  if (
    rus &&
    typeof OgeRusUI !== "undefined" &&
    typeof OgeRusUI.mapTasksWithShared === "function"
  ) {
    const body = OgeRusUI.mapTasksWithShared(
      tasks || [],
      (t, extras) => renderPrintTaskCard(t, extras, showAnswer, paper),
      { teacher: true, examBody: true, exam: true, showKey: !!showAnswer, print: !!paper }
    );
    return `<div class="oge-rus-exam${paper ? " is-paper" : ""}" data-exam-ui="kim-v2"><div class="oge-rus-exam-sheet">${body}</div></div>`;
  }
  if (
    typeof MathOgeUI !== "undefined" &&
    typeof MathOgeUI.mapTasks === "function" &&
    MathOgeUI.findMathContext(tasks || [])
  ) {
    return MathOgeUI.mapTasks(tasks || [], (t) =>
      renderPrintTaskCard(t, "", showAnswer, paper)
    );
  }
  return (tasks || []).map((t) => renderPrintTaskCard(t, "", showAnswer, paper)).join("");
}

function renderExportPanel(scope = "variant") {
  if (!state.generator.export) {
    state.generator.export = {
      pngWithAnswer: false,
      pdfAnswerSheet: false,
      previewTheme: "dark",
      linkQrOpen: false,
      a4Preview: false,
    };
  }
  const ex = state.generator.export;
  const payload = exportPreviewPayload();
  if (!payload) return "";
  const a4 = !!ex.a4Preview;
  const paper = a4 || ex.previewTheme === "light";
  const theme = a4 ? "is-light is-a4" : ex.previewTheme === "light" ? "is-light" : "is-dark";
  const showAnswer = a4 ? false : ex.pngWithAnswer;

  return `
    <div class="export-panel glass" data-export-scope="${scope}">
      <div class="export-head">
        <div>
          <div class="export-kicker">Preview Panel</div>
          <h3>Экспорт ${scope === "task" ? "карточки" : "карточек варианта"}</h3>
        </div>
        <div class="export-head-actions">
          <div class="theme-switch" role="group" aria-label="Тема превью">
            <button type="button" class="theme-btn ${ex.previewTheme === "dark" && !a4 ? "is-active" : ""}" data-ep-action="theme" data-preview-theme="dark">Dark</button>
            <button type="button" class="theme-btn ${ex.previewTheme === "light" || a4 ? "is-active" : ""}" data-ep-action="theme" data-preview-theme="light">Light</button>
          </div>
          <button type="button" class="ep-quick ep-quick-pdf" data-ep-action="pdf-students" id="btn-export-pdf-students">${icon("file")} PDF ученикам</button>
          <label class="ep-keys-check" style="display:inline-flex;align-items:center;gap:6px;font-size:.82rem;margin-right:8px">
            <input type="checkbox" id="pdf-include-keys" ${ex.pdfAnswerSheet ? "checked" : ""}/>
            Включать страницу с ключами и критериями для учителя
          </label>
          <button type="button" class="ep-quick ep-quick-keys" data-ep-action="pdf-keys" id="btn-export-pdf-keys">${icon("key")} Ключи</button>
          <button type="button" class="ep-quick ep-quick-qr" data-ep-action="qr-board" id="btn-export-qr-board">${icon("qr")} QR на доску</button>
          <button type="button" class="ep-quick ep-quick-a4 ${a4 ? "is-active" : ""}" data-ep-action="a4" id="btn-preview-a4">${icon("printer")} А4</button>
        </div>
      </div>

      <div class="export-preview-wrap ${a4 ? "is-a4-mode" : ""}">
        <div class="export-preview ${theme}" id="export-preview-card">
          ${eduSenseWatermarkHtml()}
          <div class="ep-sheet">
            ${eduSenseBrandHtml()}
            <div class="ep-badge">${escapeHtml(payload.badge)}</div>
            <h4>${escapeHtml(payload.title)}</h4>
            <p class="ep-meta">${escapeHtml(payload.meta)}</p>
            <div class="ep-tasks">${renderExportTaskBlocks(payload.tasks, showAnswer, paper)}</div>
            ${
              showAnswer
                ? ""
                : `<div class="ep-answer is-hidden-key"><span>Без ответов</span><div class="ep-answer-body">Ключи скрыты для учеников</div></div>`
            }
          </div>
        </div>
      </div>

      <div class="export-actions">
        <div class="export-block export-download">
          <button type="button" class="btn-primary export-download-btn" data-ep-action="png" id="btn-export-png">
            ${icon("download")}
            <span>Скачать</span>
          </button>
          <label class="export-toggle">
            <span>Без ответа</span>
            <input type="checkbox" id="toggle-png-answer" ${ex.pngWithAnswer ? "checked" : ""} />
            <span class="switch"></span>
            <span>С ответом</span>
          </label>
        </div>
      </div>
    </div>
  `;
}

function toLocalDatetimeValue(date) {
  const d = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}

function publishAudienceValue() {
  if (state.generator.publishAudience) return state.generator.publishAudience;
  const id = state.classroom?.id;
  return id ? `class:${id}` : "all";
}

function publishTargetClassroom() {
  const val = publishAudienceValue();
  const m = String(val).match(/^class:(\d+)$/);
  if (m) {
    const id = Number(m[1]);
    return (state.classrooms || []).find((c) => Number(c.id) === id) || state.classroom;
  }
  return state.classroom;
}

function renderPublishToggle({ id, checked, title, hint }) {
  return `<label class="pub-toggle ${checked ? "is-on" : ""}">
    <input type="checkbox" id="${escapeHtml(id)}" ${checked ? "checked" : ""} />
    <span class="pub-switch" aria-hidden="true"></span>
    <span class="pub-toggle-copy">
      <strong>${escapeHtml(title)}</strong>
      ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
    </span>
  </label>`;
}

function publishDeadlinePresetOf(value) {
  if (!value) return "none";
  const at18 = (days) => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    d.setHours(18, 0, 0, 0);
    return toLocalDatetimeValue(d);
  };
  if (value === at18(1)) return "tomorrow";
  if (value === at18(3)) return "3d";
  return "";
}

function renderPublishSuccess(done) {
  const url = studentWorkUrl(done.code, done.studentUrl);
  const qr = qrDataImage(url, 280);
  const canShare = typeof navigator !== "undefined" && typeof navigator.share === "function";
  return `
    <div class="publish-success" id="publish-success">
      <p class="export-kicker">Готово</p>
      <h2>Вариант опубликован!</h2>
      <p class="publish-sub">${escapeHtml(done.title || "Работа")}</p>
      <p class="publish-code" aria-label="Код работы">${escapeHtml(done.code)}</p>
      <img class="publish-qr" alt="QR-код ссылки для класса" src="${escapeHtml(qr)}" width="180" height="180" />
      <a class="publish-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
        url
      )}</a>
      <div class="publish-success-actions">
        <button type="button" class="btn-publish" id="btn-copy-publish-link">📋 Скопировать ссылку для класса</button>
        ${
          canShare
            ? `<button type="button" class="btn-secondary" id="btn-share-publish">Поделиться</button>`
            : ""
        }
        <button type="button" class="btn-secondary" id="btn-publish-to-journal">Открыть журнал</button>
        <button type="button" class="btn-ghost" id="btn-close-publish-success">Закрыть</button>
      </div>
    </div>
  `;
}

function renderPublishModal() {
  if (!state.generator.publishOpen || !state.generator.variant) return "";
  const v = state.generator.variant;
  const done = state.generator.publishSuccess;
  const mode = state.generator.gradingMode;
  const issue = state.assignmentsBoard.issueSettings || {};
  const deadlineVal = futureDatetimeLocalValue(
    state.generator.publishDeadline || issue.deadlineAt || ""
  );
  const timeLimitVal =
    state.generator.publishTimeLimit !== "" && state.generator.publishTimeLimit != null
      ? state.generator.publishTimeLimit
      : issue.timeLimitMinutes || "";
  const shuffleOn = wantsEtalonGenerate()
    ? false
    : !!(state.generator.publishShuffle || issue.shuffleVariants);
  const audience = publishAudienceValue();
  const classes = [...(state.classrooms || [])];
  if (state.classroom && !classes.some((c) => Number(c.id) === Number(state.classroom.id))) {
    classes.unshift(state.classroom);
  }
  const roster = state.studentsBoard.roster || [];
  const picked = new Set((state.generator.publishAudienceNames || []).map((n) => normalizeStudentKey(n)));
  const timeNum = timeLimitVal !== "" && timeLimitVal != null ? Number(timeLimitVal) : null;
  const deadlinePreset = publishDeadlinePresetOf(deadlineVal);
  const timeCustom =
    !!state.generator.publishTimeCustom ||
    (!!timeNum && timeNum !== 45 && timeNum !== 90 && timeNum !== 235);

  const classOptions = classes
    .map((c) => {
      const val = `class:${c.id}`;
      return `<option value="${escapeHtml(val)}" ${audience === val ? "selected" : ""}>${escapeHtml(
        classTitle(c)
      )}</option>`;
    })
    .join("");

  return `
    <div class="modal-backdrop publish-backdrop" id="publish-backdrop">
      <div class="publish-modal ${done ? "is-success" : ""}" role="dialog" aria-modal="true" aria-labelledby="publish-title">
        <div class="publish-top">
          <div>
            <p class="export-kicker">Публикация</p>
            <h2 id="publish-title">${done ? "Вариант опубликован" : "Назначить работу классу"}</h2>
            <p class="publish-sub">${escapeHtml(v.title)} · ${tasksCountLabel(v.tasks.length)}</p>
          </div>
          <button type="button" class="icon-x" id="btn-close-publish" aria-label="Закрыть">×</button>
        </div>
        ${
          done
            ? renderPublishSuccess(done)
            : `
        <div class="publish-section">
          <h3>Кому выдать</h3>
          <label class="assign-field">
            <span>👥 Кому выдать</span>
            <select id="publish-audience">
              ${classOptions || `<option value="all">Текущий класс</option>`}
              <option value="all" ${audience === "all" ? "selected" : ""}>Все ученики</option>
              <option value="individual" ${audience === "individual" ? "selected" : ""}>Индивидуально</option>
            </select>
          </label>
          ${
            audience === "individual"
              ? roster.length
                ? `<div class="pub-roster" role="group" aria-label="Ученики">
                    ${roster
                      .map((name) => {
                        const on = picked.has(normalizeStudentKey(name));
                        return `<label class="pub-roster-item">
                          <input type="checkbox" data-pub-student="${escapeHtml(name)}" ${on ? "checked" : ""} />
                          <span>${escapeHtml(name)}</span>
                        </label>`;
                      })
                      .join("")}
                  </div>`
                : `<p class="publish-hint">Список класса пуст — добавьте ФИО в «Ученики», либо выдайте всем.</p>`
              : `<p class="publish-hint">${
                  audience === "all"
                    ? "Работу увидят все ученики выбранного класса."
                    : "Работа уйдёт в выбранный класс."
                }</p>`
          }
        </div>

        <div class="publish-section">
          <h3>Режим проверки 2-й части</h3>
          <div class="grade-modes" role="radiogroup" aria-label="Режим проверки">
            ${GRADING_MODES.map(
              (m) => `
              <label class="grade-mode ${mode === m.id ? "is-active" : ""} ${
                m.badge === "ai" ? "is-ai" : ""
              }" data-mode="${m.id}">
                <input type="radio" name="grading-mode" value="${m.id}" ${mode === m.id ? "checked" : ""} />
                <span class="gm-body">
                  <strong>${m.title}${
                    m.badge === "ai"
                      ? ` <span class="gm-ai-badge">🤖 AI Helper</span>`
                      : ""
                  }</strong>
                  <small>${m.desc}</small>
                </span>
              </label>`
            ).join("")}
          </div>
        </div>

        <div class="publish-section">
          <h3>Сроки</h3>
          <label class="assign-field">
            <span>Дедлайн (местное время)</span>
            <input type="datetime-local" id="publish-deadline" value="${escapeHtml(deadlineVal)}" />
          </label>
          <div class="pub-chips is-tiny" role="group" aria-label="Быстрый дедлайн">
            <button type="button" class="pub-chip ${deadlinePreset === "tomorrow" ? "is-active" : ""}" data-deadline-preset="tomorrow">Завтра 18:00</button>
            <button type="button" class="pub-chip ${deadlinePreset === "3d" ? "is-active" : ""}" data-deadline-preset="3d">3 дня</button>
            <button type="button" class="pub-chip ${deadlinePreset === "none" ? "is-active" : ""}" data-deadline-preset="none">Без дедлайна</button>
          </div>
          <div class="pub-timer-block">
            <p class="pub-timer-label">Лимит времени</p>
            <div class="pub-seg" role="radiogroup" aria-label="Лимит времени">
              <button type="button" class="pub-seg-btn ${!timeNum && !timeCustom ? "is-active" : ""}" data-timer-preset="none">Без лимита</button>
              <button type="button" class="pub-seg-btn ${!timeCustom && timeNum === 45 ? "is-active" : ""}" data-timer-preset="45">45 мин</button>
              <button type="button" class="pub-seg-btn ${!timeCustom && timeNum === 90 ? "is-active" : ""}" data-timer-preset="90">90 мин</button>
              <button type="button" class="pub-seg-btn ${!timeCustom && timeNum === 235 ? "is-active" : ""}" data-timer-preset="235">235 мин</button>
              <button type="button" class="pub-seg-btn ${timeCustom ? "is-active" : ""}" data-timer-preset="custom">Свой</button>
            </div>
            ${
              timeCustom
                ? `<label class="assign-field pub-timer-custom">
                    <span>Минуты</span>
                    <input type="number" id="publish-time-limit" min="1" max="600" placeholder="мин" value="${escapeHtml(
                      timeLimitVal !== "" && timeLimitVal != null ? String(timeLimitVal) : ""
                    )}" />
                  </label>`
                : `<input type="hidden" id="publish-time-limit" value="${escapeHtml(
                    timeLimitVal !== "" && timeLimitVal != null ? String(timeLimitVal) : ""
                  )}" />`
            }
          </div>
        </div>

        <div class="publish-section">
          <h3>Безопасность</h3>
          <div class="pub-toggles">
          ${
            wantsEtalonGenerate()
              ? `<p class="publish-hint">Эталон: генератор аналогичных заданий выключен, формулировки общие.</p>`
              : renderPublishToggle({
                  id: "publish-shuffle",
                  checked: shuffleOn,
                  title: "Каждому ученику свой вариант",
                  hint: "Генератор аналогичных заданий",
                })
          }
          ${renderPublishToggle({
            id: "publish-block-copy",
            checked: !!state.generator.publishBlockCopy,
            title: "Запретить копирование текста",
            hint: "",
          })}
          ${renderPublishToggle({
            id: "publish-hide-answers",
            checked: state.generator.publishHideAnswers !== false,
            title: "Скрывать ответы до окончания дедлайна",
            hint: "",
          })}
          </div>
        </div>

        ${betaLimitNoteHtml()}
        <div class="publish-foot">
          <button type="button" class="btn-ghost" id="btn-cancel-publish">Отмена</button>
          <button type="button" class="btn-publish" id="btn-confirm-publish" ${
            state.generator.publishBusy || betaLimitReached() ? "disabled" : ""
          }>${
            state.generator.publishBusy
              ? "Выдаём…"
              : betaLimitReached()
                ? "Лимит беты"
                : "Назначить работу классу"
          }</button>
        </div>`
        }
      </div>
    </div>
  `;
}

function renderLinkQrModal() {
  if (!state.generator.export.linkQrOpen || !state.generator.variant) return "";
  const url = variantShareUrl(state.generator.variant);
  const code = state.generator.variant.code;
  return `
    <div class="modal-backdrop" id="link-qr-backdrop">
      <div class="modal-card link-qr-card">
        <h3 style="margin:0 0 8px;font-size:1.1rem">Быстрая ссылка</h3>
        <p style="margin:0 0 12px">Код: <strong>${escapeHtml(code)}</strong></p>
        <img alt="QR" src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(url)}" />
        <p class="link-url">${escapeHtml(url)}</p>
        <button type="button" class="btn-secondary" id="btn-copy-share-link" style="width:100%;margin-top:12px">Скопировать ссылку</button>
        <button type="button" class="btn-ghost" id="btn-close-link-qr" style="width:100%;margin-top:6px">Закрыть</button>
      </div>
    </div>
  `;
}

function polishFipiText(raw) {
  // Plain-text path (clipboard / Telegram): readable math, no bare $
  if (typeof formatMathText === "function") {
    const html = formatMathText(raw);
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return String(tmp.textContent || "")
      .replace(/\s+/g, " ")
      .trim();
  }
  if (typeof prepareMathSource === "function") {
    return prepareMathSource(String(raw || "").replace(/\$+/g, " "))
      .replace(/\s+/g, " ")
      .trim();
  }
  return String(raw || "")
    .replace(/\$+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function fracCssForPrint() {
  return `
    .katex { font-size: 1.05em; }
    .math-frac {
      display: inline-flex; align-items: center; white-space: nowrap;
      vertical-align: middle; max-width: 100%;
    }
    .frac {
      display: inline-flex; flex-direction: column; align-items: center;
      vertical-align: middle; margin: 0 0.18em; font-weight: 700; line-height: 1.05;
      white-space: nowrap;
    }
    .frac .num, .frac .den { display: block; padding: 0 0.22em; }
    .frac .num { border-bottom: 1.6px solid currentColor; padding-bottom: 0.1em; margin-bottom: 0.1em; }
    .math-sqrt {
      display: inline-flex; flex-direction: row; flex-wrap: nowrap; align-items: stretch;
      white-space: nowrap; vertical-align: middle; margin: 0 0.04em; line-height: 1.15;
    }
    .math-sqrt.is-katex { display: inline-block; }
    .math-sqrt-sign { font-size: 1.18em; line-height: 1; padding-right: 0.02em; align-self: center; }
    .math-sqrt-radicand {
      border-top: 1.65px solid currentColor; padding: 0.02em 0.14em 0.04em;
      margin-top: 0.14em; line-height: 1.2;
    }
    .answer-blank { display:inline-block; font-weight:800; letter-spacing:.04em;
      padding:4px 12px; border:1.5px solid currentColor; border-radius:6px; }
    .answer-math { display:inline-block; max-width:100%; }
    .answer-math .katex { font-size:1.1em; }
    .ep-answer-body { display:block; width:auto; }
    .ep-solution-figure { margin-top:10px; }
    .ep-solution-figure-label { display:block; font-size:.78rem; font-weight:700; opacity:.75; margin-bottom:4px; font-family: "Plus Jakarta Sans", system-ui, sans-serif; }
    .task-figure { max-width:200px; margin:10px auto; color:inherit; }
    .task-figure svg { width:100%; height:auto; display:block; }
    .body, .ep-body { white-space:pre-wrap; font-family:inherit; line-height:1.65; font-size:1.05rem; }
  `;
}

function eduSenseMarkUrl() {
  try {
    return `${String(location.origin || "").replace(/\/$/, "")}/assets/edusense-mark-192.png`;
  } catch (_) {
    return "/assets/edusense-mark-192.png";
  }
}

function eduSenseBrandHtml(extra) {
  const tail = extra
    ? `<span class="ep-brand-extra">${escapeHtml(extra)}</span>`
    : "";
  return `<div class="ep-brand">
    <span class="ep-brand-mark" aria-hidden="true">
      <img src="${eduSenseMarkUrl()}" alt="" width="28" height="28"/>
    </span>
    <span class="ep-brand-name">EduSense</span>${tail}
  </div>`;
}

function eduSenseWatermarkHtml() {
  return `<div class="ep-watermark" aria-hidden="true"><div class="ep-wm-layer"><span class="ep-wm-text">EDUSENCE · КИМ ОГЭ</span></div></div>`;
}

function pdfExamHeaderHtml(payload) {
  const title = payload?.title || "Вариант";
  const badge = payload?.badge || "";
  const meta = payload?.meta || "";
  const dateLabel = new Date().toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  const maxScore = (payload?.tasks || []).reduce(
    (sum, t) => sum + (Number(t.maxScore) || Number(t.max_score) || 0),
    0
  );
  return `
    <header class="pdf-exam-header">
      ${eduSenseBrandHtml()}
      <div class="pdf-exam-title-row">
        <div>
          <div class="ep-badge">${escapeHtml(badge || "КИМ")}</div>
          <h1 class="pdf-exam-title">${escapeHtml(title)}</h1>
          <p class="pdf-exam-meta">${escapeHtml(meta)}</p>
        </div>
        <div class="pdf-exam-date">${escapeHtml(dateLabel)}</div>
      </div>
      <div class="pdf-exam-fields">
        <div class="pdf-exam-field"><span>ФИО ученика</span><em>____________________</em></div>
        <div class="pdf-exam-field"><span>Класс</span><em>________</em></div>
        <div class="pdf-exam-field"><span>Вариант</span><em>${escapeHtml(payload?.code || "____")}</em></div>
        <div class="pdf-exam-field"><span>Баллы</span><em>____ / ${maxScore || "—"}</em></div>
      </div>
      <p class="muted" style="font-size:.82rem;margin:8px 0 0">Инструкция: внимательно прочитайте задания. Ответы части 1 внесите в бланк ответов №1 на последней странице.</p>
    </header>`;
}

function eduSensePrintWatermarkCss() {
  return `
    .a4-sheet {
      position: relative;
      overflow: hidden;
      page-break-after: always;
      break-after: page;
    }
    .ep-watermark {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      user-select: none;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .ep-wm-layer {
      transform: rotate(-35deg);
      opacity: 0.06;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .ep-wm-text {
      font-family: "Plus Jakarta Sans", Inter, system-ui, sans-serif;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-size: 42px;
      line-height: 1.1;
      color: #0f172a;
      white-space: nowrap;
    }
    .a4-inner, .print-inner, .ep-sheet {
      position: relative;
      z-index: 1;
    }
    .ep-brand {
      display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
      font-family: "Plus Jakarta Sans", Inter, system-ui, sans-serif;
      font-size: 1.15rem; font-weight: 800; letter-spacing: -0.045em; color: #0f172a;
    }
    .ep-brand-mark {
      width: 28px; height: 28px; border-radius: 7px; overflow: hidden;
      display: inline-flex; align-items: center; justify-content: center;
      background: transparent; box-shadow: none; flex-shrink: 0;
    }
    .ep-brand-mark img, .ep-brand-mark svg { display: block; width: 28px; height: 28px; object-fit: cover; }
    .ep-brand-name { letter-spacing: -0.04em; }
    .ep-brand-extra { margin-left: 4px; font-size: 0.78rem; font-weight: 650; letter-spacing: 0; color: #64748b; }
    .a4-inner[style*="text-align:center"] .ep-brand { justify-content: center; }
    .pdf-exam-header {
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 2px solid #e2e8f0;
    }
    .pdf-exam-title-row {
      display: flex; justify-content: space-between; gap: 16px; align-items: flex-start;
    }
    .pdf-exam-title {
      font-size: 1.28rem; margin: 6px 0 4px; letter-spacing: -0.03em; line-height: 1.25;
    }
    .pdf-exam-meta { margin: 0; color: #64748b; font-size: 0.9rem; }
    .pdf-exam-date {
      flex-shrink: 0; font-size: 0.82rem; font-weight: 650; color: #475569;
      padding: 6px 10px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc;
    }
    .pdf-exam-fields {
      display: grid; grid-template-columns: 1.6fr 0.8fr 0.9fr; gap: 10px; margin-top: 14px;
    }
    .pdf-exam-field {
      display: flex; align-items: baseline; gap: 8px;
      padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff;
      font-size: 0.88rem; color: #334155;
    }
    .pdf-exam-field span { font-weight: 700; color: #64748b; white-space: nowrap; }
    .pdf-exam-field em { font-style: normal; font-weight: 650; letter-spacing: 0.04em; }
    .pdf-task-card,
    .ep-task,
    .key-p2 {
      page-break-inside: avoid !important;
      break-inside: avoid !important;
      margin-bottom: 1.5rem;
    }
    .pdf-page-footer {
      display: none;
    }
    ${examPrintMediaCss()}
  `;
}

function examPrintMediaCss() {
  return `
    .ep-print-media,
    .task-media {
      width: 100%;
      max-width: 100%;
      margin: 12px 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .task-media-img,
    .ep-body img,
    .ep-task img:not(.ep-brand img),
    .task-figure,
    .task-figure img {
      display: block;
      width: auto;
      max-width: min(100%, 520px);
      min-width: 0;
      height: auto;
      object-fit: contain;
      margin: 0 auto;
      box-sizing: border-box;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .task-figure {
      width: 100%;
      max-width: min(100%, 560px);
      border: 1px solid #cbd5e1;
      background: #fff;
      padding: 4px;
      cursor: default;
      overflow: hidden;
    }
    .task-figure svg {
      display: block;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      height: auto !important;
      margin: 0 auto;
      background: #fff;
    }
    .kim-table-scroll,
    table {
      max-width: 100%;
      overflow: hidden;
    }
  `;
}

function brandedExamPrintCss() {
  const printKit =
    typeof window !== "undefined" && window.EduSensePrint && window.EduSensePrint.getPrintCss
      ? window.EduSensePrint.getPrintCss()
      : "";
  return `
    ${printKit}
    /* Fallback + html2canvas pixel sheet sizing (794×1123 ≈ A4 @96dpi) */
    @page { size: A4; margin: 12mm; }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      background: #ffffff !important;
      color: #000000 !important;
      font-family: "Times New Roman", Times, serif !important;
    }
    .a4-sheet {
      position: relative;
      overflow: hidden;
      background: #fff !important;
      color: #000 !important;
      width: 210mm;
      max-width: 210mm;
      min-height: 297mm;
      margin: 0 auto 8mm;
      padding: 15mm 20mm;
      box-shadow: none;
      border-radius: 0;
      font-family: "Times New Roman", Times, serif !important;
    }
    ${eduSensePrintWatermarkCss()}
    .ep-badge {
      display: inline-block; font-size: 9pt; font-weight: 700;
      padding: 2px 8px; border: 1px solid #000; margin-bottom: 8px; color: #000; background: #fff;
    }
    h1, .pdf-exam-title { font-family: "Times New Roman", Times, serif; font-size: 16pt; margin: 6px 0; color: #000 !important; }
    h2 { font-size: 11pt; margin: 14px 0 8px; letter-spacing: .04em; text-transform: uppercase; color: #000 !important; font-weight: 700; }
    .muted { color: #222 !important; font-size: 10pt; margin: 0 0 12px; }
    .pdf-task-card,
    .ep-task,
    .es-print-task {
      background: #fff !important;
      border: 0;
      border-bottom: 1px solid #333;
      color: #000 !important;
      padding: 10px 0 12px;
      margin: 0 0 12px;
      page-break-inside: avoid !important;
      break-inside: avoid !important;
    }
    .ep-task-head { display: flex; flex-wrap: wrap; gap: 6px; font-size: 10pt; color: #000; margin-bottom: 4px; }
    .ep-num, .ep-pill {
      display: inline-flex; align-items: center; padding: 1px 6px; border: 1px solid #000;
      font-size: 9pt; font-weight: 700; background: #fff; color: #000;
    }
    .ep-topic, .es-print-task-title { font-weight: 700; margin-bottom: 6px; color: #000 !important; }
    .a4-sheet img, .a4-sheet svg, .ep-print-media img, .task-figure img, .task-media-img,
    .math-oge-context img, .math-oge-context svg {
      max-width: 100% !important;
      max-height: 70mm !important;
      object-fit: contain !important;
      display: block !important;
      margin: 10px auto !important;
      height: auto !important;
      width: auto !important;
    }
    .ep-print-media, .task-figure, .math-oge-context, .passage-box, .reading-passage-box, .oge-rus-shared {
      page-break-inside: avoid !important;
      break-inside: avoid !important;
    }
    .math-oge-context {
      border: 1px solid #000;
      padding: 10px 12px;
      margin: 0 0 14px;
      background: #fff;
      color: #000;
    }
    .math-oge-context-kicker { font-size: 9pt; font-weight: 700; margin: 0 0 4px; text-transform: uppercase; }
    .math-oge-context-title { font-size: 12pt; margin: 0 0 8px; }
    .math-oge-context-story { font-size: 11pt; line-height: 1.4; margin: 0 0 8px; }
    .oge-rus-shared, .es-print-text-frame, .passage-box, .reading-passage-box {
      border: 1px solid #334155 !important;
      padding: 14px 16px !important;
      margin: 0 0 15px !important;
      font-size: 10.5pt !important;
      line-height: 1.6 !important;
      background: #ffffff !important;
      color: #1e293b !important;
      orphans: 3; widows: 3;
      page-break-inside: avoid;
      border-radius: 4px;
    }
    .oge-rus-shared-title, .passage-box .oge-rus-shared-title, .reading-passage-box .oge-rus-shared-title {
      color: #0f172a !important;
      font-weight: 700 !important;
      text-transform: uppercase !important;
      font-size: 11pt !important;
      letter-spacing: 0.04em;
      margin: 0 0 10px !important;
    }
    .lined-box {
      border: 1px dashed #94a3b8;
      width: 100%;
      margin-top: 10px;
      padding: 8px 10px 0;
      background:
        repeating-linear-gradient(
          to bottom,
          transparent,
          transparent 21px,
          #e2e8f0 21px,
          #e2e8f0 22px
        );
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .lined-box.is-essay { min-height: 280px; height: 300px; }
    .lined-box.is-math { min-height: 180px; height: 196px; }
    .lined-box-label {
      display: block;
      font-size: 9pt;
      font-weight: 700;
      color: #64748b;
      margin-bottom: 6px;
    }
    .es-print-answer-line {
      margin: 8px 0 2px; padding: 8px 10px; border: 1px solid #000; font-size: 11pt;
      page-break-inside: avoid; break-inside: avoid;
    }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #000; color: #000; background: #fff; padding: 5px 7px; }
    .key-table { margin: 0 0 8px; }
    .key-table th.n { width: 52px; text-align: center; font-variant-numeric: tabular-nums; }
    .key-table td.ans { font-weight: 700; }
    .key-p2 {
      border: 1px solid #000; padding: 10px 12px; margin: 8px 0 12px;
      page-break-inside: avoid !important; break-inside: avoid !important;
    }
    .keys-sheet { page-break-before: always; break-before: page; }
    .answer-row { margin: 8px 0; }
    .no-print { display: none !important; }
    @media print {
      html, body { background: #fff !important; }
      .a4-sheet { box-shadow: none; margin: 0 auto; max-width: none; height: auto; min-height: auto; width: auto; }
      .ep-wm-layer { opacity: 0.04; }
      .pdf-task-card, .ep-task, .key-p2, .ep-print-media {
        page-break-inside: avoid !important;
        break-inside: avoid !important;
      }
      .no-print { display: none !important; }
    }
    ${fracCssForPrint()}
  `;
}

function qrDataImage(data, size = 520) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(
    data
  )}`;
}

function buildPrintDocument(title, html, css) {
  const safeHtml = String(html || "").replace(/<\/script/gi, "<\\/script");
  return `<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"/>
  <title>${escapeHtml(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=PT+Serif:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" crossorigin/>
  <link rel="stylesheet" href="/css/oge_rus_exam.css?v=152"/>
  <style>${css}</style></head><body>
  ${safeHtml}
  <script>
    window.addEventListener("load", function () {
      setTimeout(function () { try { window.focus(); window.print(); } catch (e) {} }, 280);
    });
  <\/script>
  </body></html>`;
}

function printViaHiddenFrame(docHtml) {
  const prev = document.getElementById("ep-print-frame");
  if (prev) prev.remove();
  const iframe = document.createElement("iframe");
  iframe.id = "ep-print-frame";
  iframe.setAttribute("aria-hidden", "true");
  iframe.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;";
  document.body.appendChild(iframe);
  const doc = iframe.contentDocument;
  if (!doc) {
    showToast("Не удалось открыть печать", "error");
    iframe.remove();
    return false;
  }
  doc.open();
  doc.write(docHtml);
  doc.close();
  const run = () => {
    try {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    } catch (_) {}
    setTimeout(() => iframe.remove(), 1500);
  };
  iframe.onload = run;
  setTimeout(run, 400);
  return true;
}

function openPrintWindow(title, html, css) {
  const docHtml = buildPrintDocument(title, html, css);
  try {
    const blob = new Blob([docHtml], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    // Не передавать noopener в 3-й аргумент: Chrome тогда возвращает null.
    const win = window.open(url, "_blank", "width=920,height=1100");
    if (win) {
      try {
        win.opener = null;
      } catch (_) {}
      setTimeout(() => URL.revokeObjectURL(url), 120000);
      return win;
    }
    URL.revokeObjectURL(url);
  } catch (_) {}
  const ok = printViaHiddenFrame(docHtml);
  return ok ? true : null;
}

function ensureGeneratorExport() {
  if (!state.generator.export) {
    state.generator.export = {
      pngWithAnswer: false,
      pdfAnswerSheet: false,
      previewTheme: "dark",
      linkQrOpen: false,
      a4Preview: false,
    };
  }
  return state.generator.export;
}

function handleExportPanelClick(e) {
  const btn = e.target && e.target.closest ? e.target.closest("[data-ep-action]") : null;
  if (!btn || btn.disabled) return;
  const action = btn.getAttribute("data-ep-action");
  if (!action) return;
  const ex = ensureGeneratorExport();
  if (action === "theme") {
    ex.previewTheme = btn.getAttribute("data-preview-theme") || "dark";
    ex.a4Preview = false;
    render();
    return;
  }
  if (action === "a4") {
    ex.a4Preview = !ex.a4Preview;
    render();
    return;
  }
  if (action === "pdf-students") {
    exportBrandedPdf({ keys: !!state.generator.export.pdfAnswerSheet });
    return;
  }
  if (action === "pdf-keys") {
    exportBrandedPdf({ keys: true });
    return;
  }
  if (action === "qr-board") {
    printVariantQrBoard();
    return;
  }
  if (action === "png") {
    exportPng();
  }
}

function bindExportPanelOnce() {
  if (window.__epExportBound) return;
  window.__epExportBound = true;
  document.addEventListener("click", handleExportPanelClick);
  document.addEventListener("change", (e) => {
    if (e.target && e.target.id === "pdf-include-keys") {
      ensureGeneratorExport().pdfAnswerSheet = !!e.target.checked;
    }
  });
}
bindExportPanelOnce();

function loadScriptOnce(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[data-src="${src}"]`)) {
      resolve();
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.dataset.src = src;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Не удалось загрузить ${src}`));
    document.head.appendChild(s);
  });
}

function jsPdfCtor() {
  return (window.jspdf && window.jspdf.jsPDF) || window.jsPDF || null;
}

async function ensurePdfLibs() {
  if (!window.html2canvas) {
    await loadScriptOnce("https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js");
  }
  if (!jsPdfCtor()) {
    await loadScriptOnce("https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js");
  }
}

function pdfSafeName(title) {
  return (
    String(title || "variant")
      .replace(/[\\/:*?"<>|]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 60) || "variant"
  );
}

function showPdfExportOverlay() {
  closePdfExportOverlay();
  const el = document.createElement("div");
  el.id = "pdf-export-overlay";
  el.className = "pdf-export-overlay";
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-label", "Генерация PDF");
  el.innerHTML = `
    <div class="gen-loading-bg"></div>
    ${forgeParticlesHtml()}
    ${forgeSceneHtml("pdf")}
    <div class="pdf-export-panel gen-loading-copy">
      <p class="pdf-export-title">Собираем PDF</p>
      <p class="pdf-export-sub">Верстка A4, тексты и чертежи</p>
    </div>
  `;
  document.body.appendChild(el);
  document.documentElement.classList.add("pdf-export-busy");
}

function closePdfExportOverlay() {
  document.getElementById("pdf-export-overlay")?.remove();
  document.documentElement.classList.remove("pdf-export-busy");
}

async function waitPdfAssets(root) {
  if (document.fonts && document.fonts.ready) {
    try {
      await document.fonts.ready;
    } catch {
      /* ignore */
    }
  }
  const imgs = [...(root?.querySelectorAll("img") || [])];
  await Promise.all(
    imgs.map(
      (img) =>
        new Promise((resolve) => {
          if (img.complete && img.naturalWidth) {
            resolve();
            return;
          }
          img.addEventListener("load", resolve, { once: true });
          img.addEventListener("error", resolve, { once: true });
        })
    )
  );
  if (window.EduSensePrint?.clampImagesIn) {
    window.EduSensePrint.clampImagesIn(root);
  }
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
}

async function downloadHtmlAsPdf(title, innerHtml, css, filename) {
  await ensurePdfLibs();
  const JsPDF = jsPdfCtor();
  if (!window.html2canvas || !JsPDF) throw new Error("Нет библиотек PDF");
  const host = document.createElement("div");
  host.setAttribute("data-pdf-host", "1");
  host.style.cssText =
    "position:fixed;left:-14000px;top:0;width:794px;max-width:794px;overflow:hidden;background:#fff;z-index:-1;pointer-events:none;";
  const style = document.createElement("style");
  style.textContent = css;
  host.appendChild(style);
  const body = document.createElement("div");
  body.innerHTML = innerHtml;
  host.appendChild(body);
  document.body.appendChild(host);
  try {
    await waitPdfAssets(host);
    packPdfSheets(host);
    const sheets = [...host.querySelectorAll(".a4-sheet")];
    if (!sheets.length) throw new Error("Пустой бланк PDF");

    const pdf = new JsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
    const pageW = pdf.internal.pageSize.getWidth();
    const pageH = pdf.internal.pageSize.getHeight();
    const total = sheets.length;

    for (let i = 0; i < total; i += 1) {
      const sheet = sheets[i];
      sheet.style.width = "794px";
      sheet.style.maxWidth = "794px";
      sheet.style.height = "1123px";
      sheet.style.minHeight = "1123px";
      sheet.style.margin = "0";
      sheet.style.boxShadow = "none";
      sheet.style.overflow = "hidden";
      sheet.style.boxSizing = "border-box";
      const canvas = await window.html2canvas(sheet, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: true,
        allowTaint: false,
        logging: false,
        width: 794,
        height: 1123,
        windowWidth: 794,
        scrollX: 0,
        scrollY: 0,
        onclone: (doc) => {
          const cloned = doc.querySelectorAll(".a4-sheet")[i] || doc.querySelector(".a4-sheet");
          if (!cloned) return;
          cloned.style.background = "#ffffff";
          cloned.style.color = "#000000";
          cloned.style.width = "794px";
          cloned.style.maxWidth = "794px";
          cloned.style.height = "1123px";
          cloned.style.overflow = "hidden";
          if (window.EduSensePrint?.clampImagesIn) {
            window.EduSensePrint.clampImagesIn(cloned);
          } else {
            cloned.querySelectorAll(".task-figure, .task-media-img, img, svg").forEach((el) => {
              el.style.setProperty("max-width", "100%", "important");
              el.style.setProperty("max-height", "80mm", "important");
              el.style.setProperty("object-fit", "contain", "important");
              el.style.setProperty("display", "block", "important");
              el.style.setProperty("margin", "10px auto", "important");
              el.style.height = "auto";
            });
          }
        },
      });
      if (i) pdf.addPage();
      pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, pageW, pageH, undefined, "FAST");
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(8);
      pdf.setTextColor(100);
      pdf.text(
        `Сгенерировано в edusence.ru  |  Страница ${i + 1} из ${total}`,
        pageW / 2,
        pageH - 6,
        { align: "center" }
      );
    }
    pdf.save(filename);
  } finally {
    host.remove();
  }
}

/** Раскладывает задания по фиксированным A4-листам без разрыва карточек и текстов. */
function packPdfSheets(host) {
  const source = host.querySelector(".a4-sheet:not(.keys-sheet)");
  if (!source) return;
  const innerSrc = source.querySelector(".a4-inner") || source;
  // Берём ВСЕ смысловые блоки по порядку: тексты, сюжет 1–5, задания, QR…
  const keepSel = [
    ".pdf-pro-banner",
    ".pdf-qr-row",
    ".math-oge-context",
    ".passage-box",
    ".reading-passage-box",
    ".oge-rus-shared",
    ".oge-section-label",
    ".pdf-task-card",
    ".ep-task",
    ".es-print-task",
    ".oge-exam-task",
    ".key-p2",
    ".key-table",
    "h2",
  ].join(",");
  const cards = [...innerSrc.querySelectorAll(keepSel)].filter((el) => {
    // Не брать вложенные (например task внутри уже выбранного контейнера)
    const parent = el.parentElement?.closest(keepSel);
    if (parent && parent !== el && innerSrc.contains(parent)) return false;
    if (el.closest(".pdf-exam-header") && !el.classList.contains("pdf-exam-header")) return false;
    if (el.classList.contains("oge-exam-banner") || el.closest(".oge-exam-banner")) return false;
    return true;
  });
  if (!cards.length) {
    source.style.height = "1123px";
    source.style.minHeight = "1123px";
    source.style.overflow = "hidden";
    if (!source.querySelector(".ep-watermark")) {
      source.insertAdjacentHTML("afterbegin", eduSenseWatermarkHtml());
    }
    return;
  }

  const header = source.querySelector(".pdf-exam-header");
  const brandOnly = !header ? source.querySelector(".a4-inner > .ep-brand") : null;
  const badge = !header ? source.querySelector(".a4-inner > .ep-badge") : null;
  const title = !header ? source.querySelector(".a4-inner > h1") : null;
  const muted = !header ? source.querySelector(".a4-inner > .muted") : null;

  const PAGE_H = 1123;
  const PAD_Y = 56 + 48;
  const usable = PAGE_H - PAD_Y - 8;

  const pages = [];
  let current = [];
  let used = 0;
  let needHeader = true;

  const headerBlock = document.createElement("div");
  if (header) headerBlock.appendChild(header.cloneNode(true));
  else {
    if (brandOnly) headerBlock.appendChild(brandOnly.cloneNode(true));
    if (badge) headerBlock.appendChild(badge.cloneNode(true));
    if (title) headerBlock.appendChild(title.cloneNode(true));
    if (muted) headerBlock.appendChild(muted.cloneNode(true));
  }
  const measureHost = document.createElement("div");
  measureHost.className = "a4-sheet";
  measureHost.style.cssText =
    "position:absolute;left:0;top:0;width:794px;visibility:hidden;height:auto;min-height:0;padding:28px 36px 48px;";
  const measureInner = document.createElement("div");
  measureInner.className = "a4-inner";
  measureHost.appendChild(measureInner);
  host.appendChild(measureHost);

  function measureEl(node) {
    measureInner.innerHTML = "";
    measureInner.appendChild(node.cloneNode(true));
    // Сжать огромные чертежи перед замером
    measureInner.querySelectorAll("img, svg").forEach((el) => {
      el.style.maxWidth = "100%";
      el.style.maxHeight = "70mm";
      el.style.height = "auto";
      el.style.width = "auto";
      el.style.objectFit = "contain";
      el.style.display = "block";
      el.style.margin = "8px auto";
    });
    return measureInner.getBoundingClientRect().height || node.offsetHeight || 80;
  }

  let headerH = 0;
  if (headerBlock.childNodes.length) {
    headerH = measureEl(headerBlock) + 12;
  }

  cards.forEach((card) => {
    const clone = card.cloneNode(true);
    clone.querySelectorAll("img, svg").forEach((el) => {
      el.style.maxWidth = "100%";
      el.style.maxHeight = "70mm";
      el.style.height = "auto";
      el.style.width = "auto";
      el.style.objectFit = "contain";
      el.style.display = "block";
      el.style.margin = "8px auto";
    });
    const h = Math.ceil(measureEl(clone) + 10);
    if (!current.length) {
      used = needHeader ? headerH : 0;
    }
    if (current.length && used + h > usable) {
      pages.push({ items: current });
      current = [];
      used = 0;
      needHeader = false;
    }
    if (!current.length) {
      used = needHeader ? headerH : 0;
    }
    // Если один блок выше страницы — всё равно кладём (лучше целиком, чем потерять)
    current.push(clone);
    used += Math.min(h, usable);
    needHeader = false;
  });
  if (current.length) pages.push({ items: current });
  measureHost.remove();

  if (!pages.length) return;

  const parent = source.parentNode;
  // Убираем только исходный student sheet; ключи (.keys-sheet) не трогаем
  source.remove();
  pages.forEach((page, idx) => {
    const sheet = document.createElement("div");
    sheet.className = "a4-sheet es-print-page";
    sheet.innerHTML = eduSenseWatermarkHtml();
    const inner = document.createElement("div");
    inner.className = "a4-inner";
    if (idx === 0 && headerBlock.childNodes.length) {
      [...headerBlock.childNodes].forEach((n) => inner.appendChild(n.cloneNode(true)));
    }
    page.items.forEach((n) => inner.appendChild(n));
    sheet.appendChild(inner);
    parent.insertBefore(sheet, parent.querySelector(".keys-sheet") || null);
  });
}

function renderPart1KeysSheet(tasks) {
  const part1 = (tasks || []).filter((t) => Number(t.part) === 1 && t.answer);
  if (!part1.length) return "";
  const rows = part1
    .map(
      (t) =>
        `<li><span class="kim-keys-num">${t.num}</span><span class="kim-keys-ans">${formatAnswerKey(
          t.answer,
          1
        )}</span></li>`
    )
    .join("");
  return `
    <div class="kim-keys-sheet glass">
      <div class="kim-keys-title">Ключи части 1</div>
      <ol class="kim-keys-list">${rows}</ol>
      <p class="kim-keys-note">Часть 2 — развёрнутый ответ, на бланк не выносится.</p>
    </div>  `;
}

function isRusPart2Item(item, assignCode) {
  const num = Number(item && item.num);
  if (num !== 1 && num !== 13) return false;
  if (teacherSubjectCode() === "russian") return true;
  return !!(assignCode && typeof assignmentIsOgeRus === "function" && assignmentIsOgeRus(assignCode));
}

function p2KindForItem(item, assignCode) {
  if (!isRusPart2Item(item, assignCode)) return "math";
  return Number(item && item.num) === 13 ? "soch" : "izlo";
}

function p2MaxForItem(item, kind) {
  let maxS = Number(item && (item.maxScore != null ? item.maxScore : item.max_score));
  if (Number.isFinite(maxS) && maxS > 0) return Math.round(maxS);
  return kind === "math" ? 2 : 7;
}

function isPart2AiGradeable(item, assignCode) {
  if (isRusPart2Item(item, assignCode)) return true;
  if (teacherSubjectCode() === "russian") return false;
  if (assignCode && typeof assignmentIsOgeRus === "function" && assignmentIsOgeRus(assignCode)) {
    return false;
  }
  const num = Number(item && item.num);
  const part = Number(item && (item.part != null ? item.part : 0));
  let maxS = Number(item && (item.maxScore != null ? item.maxScore : item.max_score));
  if (!Number.isFinite(maxS) || maxS <= 0) {
    maxS = num >= 20 ? 2 : part === 2 ? 2 : 1;
  }
  if (maxS > 2) return false;
  if (part === 2) return true;
  return Number.isFinite(num) && num >= 20 && num <= 25;
}

function unwrapSourceText(val) {
  if (!val) return "";
  if (typeof val === "string") return val.trim();
  if (typeof val === "object") {
    return String(val.text || val.script || val.audio_script || val.body || "").trim();
  }
  return "";
}

function sourceTextFromPayload(obj, num) {
  const p = (obj && obj.payload) || {};
  if (Number(num) === 1) {
    return unwrapSourceText(p.listening_text || obj.listening_text || obj.source_text);
  }
  return unwrapSourceText(p.reading_text || p.source_text || obj.reading_text || obj.source_text);
}

function criteriaChipsHtml(criteria) {
  if (!criteria || typeof criteria !== "object") return "";
  const labels = {
    ik1: "ИК1",
    ik2: "ИК2",
    ik3: "ИК3",
    sk1: "СК1",
    sk2: "СК2",
    sk3: "СК3",
  };
  const parts = Object.keys(labels)
    .filter((k) => criteria[k] != null)
    .map((k) => `<span class="p2-crit">${labels[k]} ${escapeHtml(String(criteria[k]))}</span>`);
  return parts.length ? `<div class="p2-criteria">${parts.join("")}</div>` : "";
}

function getPart2State(key) {
  if (!state.part2Grades) state.part2Grades = {};
  if (!state.part2Grades[key]) state.part2Grades[key] = {};
  return state.part2Grades[key];
}

function seedPart2FromAnswer(key, a) {
  if (!a) return;
  const st = getPart2State(key);
  const status = String(a.status || "");
  const pending = status.toLowerCase().indexOf("pending") >= 0;
  const earned = Number(a.earned);
  const maxS = p2MaxForItem(a, p2KindForItem(a));
  const overridden = !!(a.teacher_override || a.teacherOverride);
  if (st.teacherScore == null && Number.isFinite(earned) && overridden) {
    st.teacherScore = Math.max(0, Math.min(maxS, Math.round(earned)));
  }
  const ag = a.ai_grade || a.aiGrade;
  if (ag && typeof ag === "object") {
    if (st.score == null && ag.score != null) st.score = Number(ag.score);
    if (!st.fipi_reason && ag.fipi_reason) st.fipi_reason = String(ag.fipi_reason);
    if (!st.student_feedback && ag.student_feedback) st.student_feedback = String(ag.student_feedback);
    if (!st.model_solution && ag.model_solution) st.model_solution = String(ag.model_solution);
    if (!st.criteria && ag.criteria && typeof ag.criteria === "object") st.criteria = ag.criteria;
  }
  if (!st.fipi_reason && a.comment && !pending) st.fipi_reason = String(a.comment);
}

function highlightP2Reason(text) {
  if (typeof AiGrader !== "undefined" && typeof AiGrader.highlightFipiReason === "function") {
    return AiGrader.highlightFipiReason(text);
  }
  return escapeHtml(text || "");
}

function renderPart2GradeCard(spec) {
  const key = spec.key;
  const st = getPart2State(key);
  if (spec.seedAnswer) seedPart2FromAnswer(key, spec.seedAnswer);
  const kind = spec.kind || "math";
  const isRus = kind === "izlo" || kind === "soch";
  const maxS = Number(spec.maxScore) > 0 ? Math.round(Number(spec.maxScore)) : isRus ? 7 : 2;
  const loading = !!st.loading;
  const loadingSolution = !!st.loadingSolution;
  const busy = loading || loadingSolution;
  const hasResult = st.score != null || st.teacherScore != null || !!st.fipi_reason || !!st.model_solution;
  const rec = st.score != null ? Number(st.score) : null;
  const chosen = st.teacherScore != null ? Number(st.teacherScore) : null;
  const needsConfirm = rec != null && st.teacherScore == null;
  const draft = spec.mode === "preview" ? String(st.draftAnswer || "") : "";
  const chips = [];
  for (let n = 0; n <= maxS; n += 1) {
    const on = chosen != null && Number(chosen) === n;
    chips.push(
      `<button type="button" class="p2-chip${on ? " is-on" : ""}" data-p2-action="set-score" data-p2-key="${escapeHtml(
        key
      )}" data-p2-score="${n}">${n}б</button>`
    );
  }
  const reasonHtml = st.fipi_reason ? `<p class="p2-reason">${highlightP2Reason(st.fipi_reason)}</p>` : "";
  const feedbackHtml = st.student_feedback
    ? `<p class="p2-feedback">${escapeHtml(st.student_feedback)}</p>`
    : "";
  const recLine = needsConfirm
    ? `<div class="p2-rec is-draft">Черновик ИИ: <strong>${rec}</strong> из ${maxS} — это не оценка, пока не подтвердите</div>
       <button type="button" class="p2-grade-btn p2-accept-draft" data-p2-action="accept-draft">Принять черновик ИИ (${escapeHtml(
         String(rec)
       )} б)</button>`
    : chosen != null
      ? `<div class="p2-rec">Балл учителя: <strong>${chosen}</strong> из ${maxS}${
          rec != null && Number(rec) !== Number(chosen) ? ` · черновик ИИ был ${rec}` : ""
        }</div>`
      : rec != null
        ? `<div class="p2-rec is-draft">Черновик ИИ: <strong>${rec}</strong> из ${maxS}</div>`
        : "";
  const solutionHtml =
    !isRus && st.model_solution
      ? `<div class="p2-solution"><p class="p2-solution-label">Полное решение (математика)</p><pre class="p2-solution-text">${escapeHtml(
          st.model_solution
        )}</pre></div>`
      : "";
  const critHtml = isRus ? criteriaChipsHtml(st.criteria) : "";
  const kicker =
    kind === "izlo" ? "Изложение · №1" : kind === "soch" ? "Сочинение · №13" : "Проверка ФИПИ · Часть 2";
  const attrs = [
    `data-p2-card="${escapeHtml(key)}"`,
    `data-p2-mode="${escapeHtml(spec.mode || "preview")}"`,
    `data-p2-kind="${escapeHtml(kind)}"`,
    `data-p2-max="${escapeHtml(String(maxS))}"`,
    spec.taskId ? `data-p2-task-id="${escapeHtml(String(spec.taskId))}"` : "",
    spec.num != null && spec.num !== "" ? `data-p2-num="${escapeHtml(String(spec.num))}"` : "",
    spec.subId != null && spec.subId !== "" ? `data-p2-sub="${escapeHtml(String(spec.subId))}"` : "",
    spec.assignCode ? `data-p2-assign="${escapeHtml(String(spec.assignCode))}"` : "",
  ]
    .filter(Boolean)
    .join(" ");
  const draftPlaceholder =
    kind === "izlo"
      ? "Вставьте сжатое изложение ученика"
      : kind === "soch"
        ? "Вставьте сочинение ученика"
        : "Вставьте решение ученика — ИИ сверит шаги и ОДЗ с критериями ФИПИ";
  const draftBlock =
    spec.mode === "preview"
      ? `<label class="p2-draft-label">Черновик решения ученика
          <textarea class="p2-draft" data-p2-action="draft" data-p2-key="${escapeHtml(
            key
          )}" rows="4" placeholder="${escapeHtml(draftPlaceholder)}">${escapeHtml(draft)}</textarea>
        </label>`
      : "";
  const solveBtn = isRus
    ? ""
    : `<button type="button" class="p2-grade-btn p2-grade-btn-ghost" data-p2-action="solve" data-p2-key="${escapeHtml(
        key
      )}" ${busy ? "disabled" : ""}>
            ${loadingSolution ? "Пишем решение…" : "Полное решение"}
          </button>`;
  const loadingText = loadingSolution
    ? "ИИ пишет полное решение…"
    : isRus
      ? "ИИ проверяет работу по критериям ФИПИ…"
      : "ИИ сверяет фото и шаги с критериями ФИПИ…";
  return `
    <div class="p2-grade-card" data-tour="ai-p2" ${attrs}>
      <div class="p2-grade-head">
        <span class="p2-grade-kicker">${escapeHtml(kicker)}</span>
        <div class="p2-grade-actions">
          <button type="button" class="p2-grade-btn" data-p2-action="grade" data-p2-key="${escapeHtml(
            key
          )}" ${busy ? "disabled" : ""}>
            ${loading ? "Проверяем…" : "Проверить через ИИ"}
          </button>
          ${solveBtn}
        </div>
      </div>
      ${draftBlock}
      <div class="p2-grade-loading${busy ? " is-on" : ""}"${busy ? "" : " hidden"}>
        <span class="p2-spinner" aria-hidden="true"></span>
        <span>${loadingText}</span>
      </div>
      ${
        hasResult && !busy
          ? `<div class="p2-grade-result">
              ${recLine}
              <div class="p2-chips" role="group" aria-label="Балл учителя">${chips.join("")}</div>
              ${critHtml}
              ${reasonHtml}
              ${feedbackHtml}
              ${solutionHtml}
            </div>`
          : ""
      }
    </div>`;
}

function renderPart2GradeCardForTask(task) {
  if (!task || !isPart2AiGradeable(task)) return "";
  const kind = p2KindForItem(task);
  return renderPart2GradeCard({
    key: `preview-${task.id}`,
    mode: "preview",
    taskId: task.id,
    num: task.num,
    kind,
    maxScore: p2MaxForItem(task, kind),
  });
}

function renderPart2GradeCardForAnswer(a, subId, assignCode) {
  if (!a || !isPart2AiGradeable(a, assignCode)) return "";
  const kind = p2KindForItem(a, assignCode);
  return renderPart2GradeCard({
    key: `sub-${subId}-${a.num}`,
    mode: "review",
    num: a.num,
    subId,
    assignCode,
    seedAnswer: a,
    kind,
    maxScore: p2MaxForItem(a, kind),
  });
}

function replacePart2CardFromEl(el) {
  if (!el) return;
  const spec = {
    key: el.getAttribute("data-p2-card") || el.getAttribute("data-p2-key"),
    mode: el.getAttribute("data-p2-mode") || "preview",
    taskId: el.getAttribute("data-p2-task-id") || "",
    num: el.getAttribute("data-p2-num"),
    subId: el.getAttribute("data-p2-sub"),
    assignCode: el.getAttribute("data-p2-assign") || "",
    kind: el.getAttribute("data-p2-kind") || "math",
    maxScore: Number(el.getAttribute("data-p2-max") || 2),
  };
  el.outerHTML = renderPart2GradeCard(spec);
}

function findReviewAnswer(assignCode, subId, num) {
  const key = String(assignCode || "").toUpperCase();
  const pack = state.assignmentsBoard.submissions[key];
  const sub =
    pack && Array.isArray(pack.items)
      ? pack.items.find((s) => Number(s.id) === Number(subId))
      : null;
  const ans =
    sub && Array.isArray(sub.answers)
      ? sub.answers.find((a) => Number(a.num) === Number(num))
      : null;
  return { sub, ans };
}

function collectPart2Payload(el) {
  const key = el.getAttribute("data-p2-card");
  const st = getPart2State(key);
  const mode = el.getAttribute("data-p2-mode") || "preview";
  const kind = el.getAttribute("data-p2-kind") || "math";
  let taskText = "";
  let studentAnswer = "";
  let correctSolution = "";
  let photoDataUrl = "";
  let sourceText = "";
  let taskNum = Number(el.getAttribute("data-p2-num") || 0);
  if (mode === "preview") {
    const taskId = el.getAttribute("data-p2-task-id");
    const task = ((state.generator.variant && state.generator.variant.tasks) || []).find(
      (t) => t.id === taskId
    );
    if (!task) return null;
    taskText = String(task.text || "").trim();
    correctSolution = String(task.solution || task.answer || "").trim();
    taskNum = Number(task.num || taskNum);
    sourceText = sourceTextFromPayload(task, taskNum);
    const ta = el.querySelector("[data-p2-action='draft']");
    studentAnswer = ta ? String(ta.value || "") : String(st.draftAnswer || "");
    st.draftAnswer = studentAnswer;
  } else {
    const subId = el.getAttribute("data-p2-sub");
    const assignCode = el.getAttribute("data-p2-assign") || "";
    const found = findReviewAnswer(assignCode, subId, taskNum);
    const ans = found && found.ans;
    taskText = String((ans && (ans.question_text || ans.questionText)) || "").trim();
    correctSolution = String(
      (ans && (ans.solution || ans.correct_answer || ans.correctAnswer)) || ""
    ).trim();
    studentAnswer = String((ans && ans.text) || "").trim();
    photoDataUrl = String((ans && (ans.photo_data_url || ans.photoDataUrl)) || "").trim();
    sourceText = String((ans && (ans.source_text || ans.sourceText)) || "").trim();
  }
  return { taskText, studentAnswer, correctSolution, photoDataUrl, sourceText, taskNum, kind };
}

async function runPart2Grade(el) {
  const key = el.getAttribute("data-p2-card");
  const st = getPart2State(key);
  const payload = collectPart2Payload(el);
  if (!payload) {
    showToast("Задание не найдено", "error");
    return;
  }
  if (!payload.studentAnswer && !payload.photoDataUrl) {
    showToast("Нет текста и нет фото — нечего проверять", "info");
    return;
  }
  const maxS = Number(el.getAttribute("data-p2-max") || (payload.kind === "math" ? 2 : 7));
  st.loading = true;
  replacePart2CardFromEl(el);
  try {
    let result;
    if (payload.kind === "izlo" || payload.kind === "soch") {
      const grader = typeof gradeRusTask === "function" ? gradeRusTask : null;
      if (!grader) throw new Error("Модуль ИИ-проверки не загружен");
      result = await grader({
        kind: payload.kind === "soch" ? "sochinenie" : "izlozhenie",
        taskText: payload.taskText,
        studentAnswer: payload.studentAnswer,
        sourceText: payload.sourceText,
        photoDataUrl: payload.photoDataUrl || undefined,
      });
      st.criteria = result.criteria || {};
    } else {
      const rubric =
        typeof AiGrader !== "undefined" && typeof AiGrader.fipiRubricFor === "function"
          ? AiGrader.fipiRubricFor(payload.taskNum)
          : "";
      const grader = typeof gradePart2Task === "function" ? gradePart2Task : null;
      if (!grader) throw new Error("Модуль ИИ-проверки не загружен");
      result = await grader({
        taskText: payload.taskText,
        studentAnswer: payload.studentAnswer,
        correctSolution: payload.correctSolution,
        fipiRubric: rubric,
        taskNum: payload.taskNum,
        photoDataUrl: payload.photoDataUrl || undefined,
      });
      if (result.model_solution) st.model_solution = result.model_solution;
    }
    st.score = result.score;
    st.fipi_reason = result.fipi_reason;
    st.student_feedback = result.student_feedback;
    st.source = result.source;
    showToast(`Черновик ИИ: ${result.score} из ${maxS}. Подтвердите балл.`, "success");
  } catch (err) {
    showToast((err && err.message) || "Не удалось проверить через ИИ", "error");
  } finally {
    st.loading = false;
    const card = document.querySelector(`[data-p2-card="${key}"]`);
    replacePart2CardFromEl(card);
  }
}

async function runMathSolution(el) {
  if ((el.getAttribute("data-p2-kind") || "math") !== "math") {
    showToast("Полное решение пишется только для математики", "info");
    return;
  }
  const key = el.getAttribute("data-p2-card");
  const st = getPart2State(key);
  const payload = collectPart2Payload(el);
  if (!payload || !payload.taskText) {
    showToast("Нет условия задания", "error");
    return;
  }
  const writer = typeof writeMathSolution === "function" ? writeMathSolution : null;
  if (!writer) {
    showToast("Модуль ИИ-проверки не загружен", "error");
    return;
  }
  st.loadingSolution = true;
  replacePart2CardFromEl(el);
  try {
    const result = await writer({
      taskText: payload.taskText,
      correctSolution: payload.correctSolution,
      taskNum: payload.taskNum,
      photoDataUrl: payload.photoDataUrl || undefined,
    });
    st.model_solution = result.solution || "";
    showToast("Полное решение готово — проверьте перед показом ученику", "success");
  } catch (err) {
    showToast((err && err.message) || "Не удалось написать решение", "error");
  } finally {
    st.loadingSolution = false;
    const card = document.querySelector(`[data-p2-card="${key}"]`);
    replacePart2CardFromEl(card);
  }
}

async function applyPart2TeacherScore(el, score) {
  const key = el.getAttribute("data-p2-card");
  const st = getPart2State(key);
  const maxS = Number(el.getAttribute("data-p2-max") || 2);
  const n = Math.max(0, Math.min(maxS, Number(score)));
  st.teacherScore = n;
  const mode = el.getAttribute("data-p2-mode");
  if (mode === "review") {
    const assignCode = el.getAttribute("data-p2-assign");
    const subId = el.getAttribute("data-p2-sub");
    const num = Number(el.getAttribute("data-p2-num"));
    if (assignCode && subId && Number.isFinite(num)) {
      try {
        await patchSubmissionGrade(assignCode, Number(subId), {
          item_num: num,
          item_earned: n,
          item_comment: st.fipi_reason || undefined,
          ai_grade:
            st.score != null || st.model_solution || st.criteria
              ? {
                  score: st.score,
                  fipi_reason: st.fipi_reason || "",
                  student_feedback: st.student_feedback || "",
                  model_solution: st.model_solution || "",
                  source: st.source || "",
                  criteria: st.criteria || {},
                }
              : undefined,
        });
        return;
      } catch (_) {
        return;
      }
    }
  }
  replacePart2CardFromEl(el);
}

async function acceptAllPart2Drafts(assignCode, subId) {
  const cards = document.querySelectorAll(`[data-p2-card][data-p2-sub="${String(subId || "")}"]`);
  let n = 0;
  for (const card of cards) {
    const key = card.getAttribute("data-p2-card");
    const st = getPart2State(key);
    if (st.teacherScore != null || st.score == null) continue;
    await applyPart2TeacherScore(card, st.score);
    n += 1;
  }
  showToast(n ? `Приняты черновики ИИ: ${n}` : "Нет черновиков для принятия", n ? "success" : "info");
}

function part2DraftPendingCount(s, assignCode) {
  return (Array.isArray(s && s.answers) ? s.answers : []).filter((a) => {
    if (!isPart2AiGradeable(a, assignCode)) return false;
    if (a.teacher_override || a.teacherOverride) return false;
    const key = `sub-${s.id}-${a.num}`;
    const st = (state.part2Grades && state.part2Grades[key]) || {};
    if (st.teacherScore != null) return false;
    const rec = st.score != null ? st.score : a.ai_grade && a.ai_grade.score;
    return rec != null;
  }).length;
}

function bindPart2GradeOnce() {
  if (window.__p2GradeBound) return;
  window.__p2GradeBound = true;
  document.addEventListener("click", (e) => {
    const start = e.target && e.target.nodeType === 1 ? e.target : e.target && e.target.parentElement;
    if (!start || typeof start.closest !== "function") return;
    const btn = start.closest("[data-p2-action]");
    if (!btn) return;
    const action = btn.getAttribute("data-p2-action");
    if (action === "draft") return;
    if (action === "accept-all-drafts") {
      e.preventDefault();
      e.stopPropagation();
      acceptAllPart2Drafts(btn.getAttribute("data-p2-assign"), btn.getAttribute("data-p2-sub"));
      return;
    }
    const card = btn.closest("[data-p2-card]");
    if (!card) return;
    e.preventDefault();
    e.stopPropagation();
    if (action === "grade") {
      runPart2Grade(card);
    } else if (action === "solve") {
      runMathSolution(card);
    } else if (action === "set-score") {
      applyPart2TeacherScore(card, btn.getAttribute("data-p2-score"));
    } else if (action === "accept-draft") {
      const rec = getPart2State(card.getAttribute("data-p2-card")).score;
      if (rec == null) {
        showToast("Нет черновика ИИ", "info");
        return;
      }
      applyPart2TeacherScore(card, rec);
    }
  });
  document.addEventListener("input", (e) => {
    const ta = e.target.closest("[data-p2-action='draft']");
    if (!ta) return;
    const key = ta.getAttribute("data-p2-key");
    if (!key) return;
    getPart2State(key).draftAnswer = ta.value;
  });
}
bindPart2GradeOnce();

function renderTaskCard(task, active, extrasHtml) {
  const extras = extrasHtml || "";
  const oge =
    typeof OgeRusUI !== "undefined" &&
    typeof OgeRusUI.isOgeRusTask === "function" &&
    OgeRusUI.isOgeRusTask(task);
  const media = payloadImagesHtml(task);
  // При examBody extras уже содержат инструкцию + варианты — не дублировать плоский text
  const bodyHtml =
    oge && extras
      ? ""
      : `<div class="task-text">${formatTeacherTaskText(task)}</div>`;
  return `
    <article class="task-card glass ${active ? "is-active" : ""}" data-task-id="${task.id}">
      <div class="task-card-head">
        <div>
          <span class="task-num">№${task.num}</span>
          <span class="task-pill">Ч.${task.part}</span>
          <span class="task-pill">${escapeHtml(task.type)}</span>
        </div>
        <span class="task-score">${task.maxScore} б.</span>
      </div>
      <h4>${formatMathText(task.topic)}</h4>
      ${media}
      ${bodyHtml}
      ${extras}
      ${figureHtml(task)}
      ${solutionFigureHtml(task)}
      ${!oge && Number(task.part) === 1 && task.answer
        ? `<div class="task-teacher-key"><span>Ключ</span><div class="task-teacher-key-ans">${formatAnswerKey(
            task.answer,
            1
          )}</div></div>`
        : ""}
      ${!oge && Number(task.part) === 1 && task.solution
        ? `<div class="task-teacher-sol"><span>Решение</span><div class="task-teacher-sol-body">${formatMathText(
            task.solution
          )}</div></div>`
        : ""}
      ${!oge && Number(task.part) === 2 && task.solution
        ? `<div class="task-teacher-sol"><span>Эталон</span><div class="task-teacher-sol-body">${formatMathText(
            task.solution
          )}</div></div>`
        : ""}
      ${renderPart2GradeCardForTask(task)}
      <div class="task-card-actions">
        <button type="button" class="btn-ghost btn-sm" data-open-task="${task.id}">Открыть карточку</button>
      </div>
    </article>
  `;
}

function renderKimBook(mode = "idle") {
  const busy = mode === "busy";
  const flip = !busy && Number(state.generator._flipBook || 0) > 0;
  return `
    <div class="kim-book ${busy ? "is-lg is-busy" : "is-idle"}${flip ? " is-flip" : ""}" aria-hidden="true" data-flip="${state.generator._flipBook || 0}">
      <span class="kim-book-glow"></span>
      <div class="kim-book-stage">
        <div class="kim-cover-left"><span class="kim-brand">EduSense</span></div>
        <div class="kim-cover-right"><span class="kim-brand-sub">КИМ</span><span class="kim-lines"></span></div>
        <div class="kim-page kim-page-a"><span class="kim-lines"></span></div>
        <div class="kim-page kim-page-b"><span class="kim-lines"></span></div>
        <div class="kim-page kim-page-c"><span class="kim-lines"></span></div>
      </div>
      ${
        busy
          ? `<div class="kim-sheet"><b>КИМ</b><i></i><i></i><i></i></div>`
          : ""
      }
    </div>
  `;
}

function expressKimCount() {
  const full = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  if (teacherSubjectCode() === "math") return Math.min(9, full);
  return Math.max(5, Math.min(9, Math.ceil(full / 3)));
}

function generatorFocusPresets() {
  const subj = teacherSubjectCode();
  const full = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  if (subj === "russian") {
    return [
      { id: "1", name: "Изложение", nums: "№ 1", hint: "Сжатое изложение", slots: [1] },
      { id: "2-9", name: "Тест", nums: "№ 2–9", hint: "Задания с кратким ответом", slots: [2, 3, 4, 5, 6, 7, 8, 9].filter((n) => n <= full) },
      { id: "10-12", name: "Текст", nums: "№ 10–12", hint: "Чтение и анализ текста", slots: [10, 11, 12].filter((n) => n <= full) },
      { id: "13", name: "Сочинение", nums: "№ 13", hint: "Развёрнутый ответ", slots: [13].filter((n) => n <= full) },
    ].filter((p) => p.slots.length);
  }
  return [
    { id: "1-5", name: "Практика", nums: "№ 1–5", hint: "План, карты, таблицы", slots: [1, 2, 3, 4, 5].filter((n) => n <= full) },
    { id: "alg1", name: "Алгебра", nums: "№ 6–14", hint: "Вычисления, уравнения, вероятность, графики", slots: [6, 7, 8, 9, 10, 11, 12, 13, 14].filter((n) => n <= full) },
    { id: "geo1", name: "Геометрия", nums: "№ 15–19", hint: "Фигуры, клетка, утверждения", slots: [15, 16, 17, 18, 19].filter((n) => n <= full) },
    { id: "p2", name: "Часть 2", nums: "№ 20–25", hint: "Развёрнутые решения", slots: [20, 21, 22, 23, 24, 25].filter((n) => n <= full) },
  ].filter((p) => p.slots.length);
}

function currentFocusPreset() {
  const presets = generatorFocusPresets();
  return presets.find((p) => p.id === state.generator.focusId) || presets[0] || null;
}

function generatorRequestCount() {
  const slots = state.generator._slots;
  if (Array.isArray(slots) && slots.length) return slots.length;
  if (state.generator._quickCount) return state.generator._quickCount;
  const size = currentGenSizes()[state.generator.size] || currentGenSizes().standard;
  return size.count;
}

function renderGeneratorModes() {
  const g = state.generator;
  const full = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  const express = expressKimCount();
  const presets = generatorFocusPresets();
  const focus = currentFocusPreset();
  const diff = g.difficulty || "medium";
  const diffs = [
    { id: "easy", label: "Легкий" },
    { id: "medium", label: "Стандарт" },
    { id: "hard", label: "Сложный" },
  ];
  return `
    <div class="gen-modes grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch my-6">
      <article class="tc-card tc-card-kim" data-mode="full">
        <div class="tc-glow" aria-hidden="true"></div>
        <div class="tc-body">
          <div class="tc-head">
            <div class="tc-titles">
              <h3>Полноформатный КИМ</h3>
              <p class="tc-sub">${full} заданий</p>
            </div>
            <div class="tc-badge" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
          </div>
          <p class="tc-desc">Полный вариант по спецификации: ключи, чертежи и часть 2.</p>
          ${renderEtalonToggle(g)}
          <div class="tc-chips" role="group" aria-label="Сложность">
            ${diffs
              .map(
                (d) => `
              <button type="button" class="tc-chip ${diff === d.id ? "is-active" : ""}" data-difficulty="${d.id}">${d.label}</button>`
              )
              .join("")}
          </div>
        </div>
        <button type="button" class="tc-cta tc-cta-kim" id="btn-gen-full" data-tour="gen-full">
          ⚡ Собрать КИМ (${full} заданий)
        </button>
      </article>

      <article class="tc-card tc-card-focus" data-mode="focus">
        <div class="tc-glow" aria-hidden="true"></div>
        <div class="tc-body">
          <div class="tc-head">
            <div class="tc-titles">
              <h3>Отработка</h3>
              <p class="tc-sub">Комплекс заданий</p>
            </div>
            <div class="tc-badge" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932h13.788a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
              </svg>
            </div>
          </div>
          <p class="tc-desc">Тренажёр по блоку КИМ — без полного варианта.</p>
          <div class="tc-chips tc-chips-grid" role="group" aria-label="Комплекс заданий">
            ${presets
              .map(
                (p) => `
              <button type="button" class="tc-tag ${focus && focus.id === p.id ? "is-active" : ""}" data-focus-id="${p.id}" title="${escapeHtml(p.hint)}">
                <span class="tc-tag-name">${escapeHtml(p.name)}</span>
                <span class="tc-tag-nums">${escapeHtml(p.nums)}</span>
              </button>`
              )
              .join("")}
          </div>
        </div>
        <button type="button" class="tc-cta tc-cta-focus" id="btn-gen-focus">
          Собрать тренажёр
        </button>
      </article>

      <article class="tc-card tc-card-express" data-mode="express">
        <div class="tc-glow" aria-hidden="true"></div>
        <div class="tc-body">
          <div class="tc-head">
            <div class="tc-titles">
              <h3>Экспресс-контрольная</h3>
              <p class="tc-sub">15 минут · ${express} заданий</p>
            </div>
            <div class="tc-badge" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p class="tc-desc">Краткая диагностическая работа на урок. При выдаче ставится таймер 15 минут.</p>
        </div>
        <button type="button" class="tc-cta tc-cta-express" id="btn-gen-express">
          Сгенерировать экспресс-вариант
        </button>
      </article>
    </div>
  `;
}

function genForgeCardsHtml(n = 5) {
  return Array.from({ length: n })
    .map(
      (_, i) => `
        <div class="gen-forge-card" style="--i:${i}">
          <span class="gen-forge-card-tag"></span>
          <i></i><i></i><i></i>
          <span class="gen-forge-card-seam"></span>
        </div>`,
    )
    .join("");
}

function forgeParticlesHtml() {
  return `<div class="gen-particles" aria-hidden="true">${"<i></i>".repeat(8)}</div>`;
}

function forgeSceneHtml(kind = "kim") {
  const pdf = kind === "pdf";
  return `
    <div class="gen-forge${pdf ? " is-pdf" : ""}" aria-hidden="true">
      <div class="gen-forge-ambient"></div>
      <div class="gen-forge-scene">
        <span class="gen-forge-shadow"></span>
        <span class="gen-forge-ring gen-forge-ring-a"></span>
        <span class="gen-forge-ring gen-forge-ring-b"></span>
        <div class="gen-forge-deck">${genForgeCardsHtml(pdf ? 4 : 5)}</div>
        <div class="gen-forge-core"><em></em></div>
      </div>
    </div>`;
}

function renderGeneratingStage() {
  const subject = state.classroom?.subject || "предмету";
  const exam = examLabel(state.classroom?.exam_type || "oge");
  const steps = ["Кодификатор", "Тексты", "Чертежи", "Готово"];
  return `
    <div class="gen-loading" id="gen-loading" data-step="0" aria-live="polite" aria-busy="true">
      <div class="gen-loading-bg"></div>
      ${forgeParticlesHtml()}
      ${forgeSceneHtml("kim")}
      <div class="gen-loading-copy">
        <p class="gen-loading-kicker">КИМ · ${escapeHtml(exam)}</p>
        <h2 class="gen-loading-title">Собираем вариант</h2>
        <p class="gen-loading-sub">${escapeHtml(subject)} · ${generatorRequestCount()} заданий</p>
        <ol class="gen-steps" id="gen-steps">
          ${steps
            .map(
              (label, i) => `
            <li class="${i === 0 ? "is-active" : ""}">
              <i aria-hidden="true">${i === 0 ? "●" : ""}</i>
              <span>${label}</span>
            </li>`,
            )
            .join("")}
        </ol>
        <p class="gen-progress-label" id="gen-progress-label">
          <span id="gen-progress-text">Сверяем кодификатор…</span>
        </p>
      </div>
    </div>
  `;
}

function renderTests() {
  const g = state.generator;

  if (g.generating) {
    return `
      ${renderGeneratingStage()}
      ${renderPublishModal()}
      ${renderLinkQrModal()}
    `;
  }

  if (!g.variant) {
    return `
      ${renderGeneratorModes()}
      ${renderPublishModal()}
      ${renderLinkQrModal()}
    `;
  }

  const v = g.variant;
  const selected = currentExportTask();
  const ogeRus = isTeacherOgeRusExam(v);
  const variantPublished = isVariantPublished(v);

  return `
    <div class="gen-layout">
      <section class="variant-viewer glass reveal">
        <div class="variant-toolbar">
          <div class="variant-toolbar-meta">
            <p class="export-kicker">${v.variant_label || v.code ? `Вариант ${escapeHtml(v.code || "")}` : "Вариант"}</p>
            ${etalonBadgeHtml(v)}
            <h2>${escapeHtml(v.title)}</h2>
            <p class="variant-meta">${escapeHtml(v.subject)} · код ${escapeHtml(v.code)} · ${tasksCountLabel(v.tasks.length)}</p>
            ${
              g.lastSourceNote
                ? `<p class="variant-meta" style="margin-top:6px;opacity:.85">${escapeHtml(g.lastSourceNote)}</p>`
                : `<p class="variant-meta" style="margin-top:6px;opacity:.85">Вариант собран</p>`
            }
          </div>
          <div class="variant-toolbar-extras">
            ${renderMutatorToggle(g)}
            <div class="gen-size-row" role="group" aria-label="Сложность">
              ${difficultyLevelsForUi()
                .map(
                  (d) => `
                <button type="button" class="chip ${g.difficulty === d.id ? "is-active" : ""}" data-difficulty="${d.id}" title="${d.hint}">${d.label}</button>`
                )
                .join("")}
            </div>
          </div>
          <div class="variant-toolbar-controls">
            <button type="button" class="btn-ghost" id="btn-gen-modes">← Режимы</button>
            <button type="button" class="btn-secondary" id="btn-regen" ${g.generating ? "disabled" : ""}>Пересобрать</button>
            ${
              variantPublished
                ? `<button type="button" class="btn-secondary btn-issue-done" disabled aria-disabled="true">Уже выдано ✓</button>
            <button type="button" class="btn-primary" id="btn-goto-journal-from-variant">Перейти в Журнал</button>`
                : `<button type="button" class="btn-primary btn-issue-class" id="btn-open-publish" data-tour="issue">Назначить работу классу</button>`
            }
          </div>
        </div>

        <div class="task-filter">
          <button type="button" class="chip task-filter-all ${!g.selectedTaskId ? "is-active" : ""}" data-open-task="">Весь вариант</button>
          <div class="task-filter-grid" role="group" aria-label="Номера заданий">
            ${v.tasks
              .map(
                (t) =>
                  `<button type="button" class="chip task-filter-num ${g.selectedTaskId === t.id ? "is-active" : ""}" data-open-task="${t.id}">№${t.num}</button>`
              )
              .join("")}
          </div>
        </div>

        ${renderExportPanel(selected ? "task" : "variant")}
        ${ogeRus ? "" : renderPart1KeysSheet(v.tasks)}

        <div class="task-grid${ogeRus ? " oge-rus-exam" : ""}" id="oge-rus-task-list" data-exam-ui="${
          ogeRus ? "kim-v2" : ""
        }">
          ${
            ogeRus && typeof OgeRusUI !== "undefined"
              ? `<div class="oge-rus-exam-sheet">${OgeRusUI.mapTasksWithShared(
                  v.tasks,
                  (t, extras) => renderTaskCard(t, g.selectedTaskId === t.id, extras),
                  { teacher: true, examBody: true, exam: true, showKey: true }
                )}</div>`
              : typeof MathOgeUI !== "undefined" && typeof MathOgeUI.mapTasks === "function"
                ? MathOgeUI.mapTasks(v.tasks, (t) =>
                    renderTaskCard(t, g.selectedTaskId === t.id, "")
                  )
                : v.tasks.map((t) => renderTaskCard(t, g.selectedTaskId === t.id, "")).join("")
          }
        </div>
      </section>
    </div>
    ${renderPublishModal()}
    ${renderLinkQrModal()}
  `;
}

function gradingModeLabel(id) {
  return GRADING_MODES.find((m) => m.id === id)?.title || id;
}

function tasksCountLabel(n) {
  const abs = Math.abs(Number(n) || 0) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return `${n} заданий`;
  if (last === 1) return `${n} задание`;
  if (last >= 2 && last <= 4) return `${n} задания`;
  return `${n} заданий`;
}

function submissionsCountLabel(n) {
  const abs = Math.abs(Number(n) || 0) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return `${n} сдали`;
  if (last === 1) return `${n} сдал`;
  if (last >= 2 && last <= 4) return `${n} сдали`;
  return `${n} сдали`;
}

function assignmentStatusMeta(a) {
  const status = String(a?.status || "active");
  const accepting = a?.acceptingSubmissions !== false && a?.accepting_submissions !== false;
  if (status === "draft") {
    return { key: "draft", label: "Черновик", cls: "is-draft" };
  }
  if (status === "closed" || !accepting) {
    return { key: "closed", label: "Завершено", cls: "is-closed" };
  }
  return { key: "active", label: "В процессе", cls: "is-active" };
}

function assignmentStatusLabel(status) {
  const map = {
    active: "В процессе",
    closed: "Завершено",
    draft: "Черновик",
    archived: "Архив",
  };
  return map[status] || status || "—";
}

function submissionStatusLabel(status) {
  const map = {
    pending: "на проверке",
    ai_reviewed: "AI проверил",
    graded: "оценено",
    approved: "принято",
  };
  return map[status] || status || "—";
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

function formatAssignDate(value) {
  const d = parseApiDate(value);
  if (!d) return value ? "—" : "—";
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDurationSeconds(secs) {
  if (secs == null || Number.isNaN(Number(secs))) return null;
  const n = Math.max(0, Math.floor(Number(secs)));
  const h = Math.floor(n / 3600);
  const m = Math.floor((n % 3600) / 60);
  const s = n % 60;
  if (h > 0) return `${h} ч ${m} мин`;
  if (m > 0) return `${m} мин ${s} с`;
  return `${s} с`;
}

function toDatetimeLocalValue(isoOrEmpty) {
  if (!isoOrEmpty) return "";
  const d = parseApiDate(isoOrEmpty);
  if (!d) return "";
  const pad = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromDatetimeLocalValue(local) {
  if (!local || !String(local).trim()) return null;
  const d = new Date(local);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function futureDatetimeLocalValue(val) {
  const s = String(val || "").trim();
  if (!s) return "";
  const d = new Date(s);
  if (Number.isNaN(d.getTime()) || d.getTime() <= Date.now()) return "";
  return s;
}

function studentWorkUrl(code, studentUrl) {
  if (studentUrl && /^https?:\/\//i.test(studentUrl)) return studentUrl;
  const path = studentUrl || `/student?code=${code}`;
  return `${window.location.origin}${path.startsWith("/") ? path : `/${path}`}`;
}

function mergeAssignmentLists(apiItems, sessionPublished) {
  const byCode = new Map();
  (apiItems || []).forEach((a) => {
    if (!a || !a.code) return;
    byCode.set(String(a.code).toUpperCase(), {
      id: a.id,
      code: a.code,
      title: a.title,
      subject: a.subject || state.classroom?.subject || "",
      exam: a.exam || state.classroom?.exam_type || "",
      status: a.status || "active",
      gradingMode: a.grading_mode || a.gradingMode || "ai_assist",
      createdAt: a.created_at || a.createdAt || null,
      deadlineAt: a.deadline_at || a.deadline || null,
      timeLimitMinutes: a.time_limit_minutes ?? a.timer_minutes ?? null,
      shuffleVariants: !!(a.shuffle_variants ?? a.shuffleVariants),
      acceptingSubmissions: a.accepting_submissions !== false && a.acceptingSubmissions !== false,
      expectedStudents: a.expected_students ?? a.expectedStudents ?? null,
      studentUrl: a.student_url || a.student_path || `/student?code=${a.code}`,
      submissionsCount: Number(a.submissions_count ?? a.submissionsCount ?? 0),
      uniqueSubmitters: Number(a.unique_submitters ?? a.uniqueSubmitters ?? a.submissions_count ?? 0),
      submissionsToday: Number(a.submissions_today ?? a.submissionsToday ?? 0),
      tasksCount: Number(a.questions_count ?? a.tasksCount ?? 0),
      fromApi: true,
    });
  });
  (sessionPublished || []).forEach((p) => {
    if (!p || !p.code) return;
    const key = String(p.code).toUpperCase();
    const existing = byCode.get(key);
    if (existing) {
      if (!existing.tasksCount && p.tasksCount) existing.tasksCount = p.tasksCount;
      if (!existing.subject && p.subject) existing.subject = p.subject;
      return;
    }
    byCode.set(key, {
      id: p.id,
      code: p.code,
      title: p.title,
      subject: p.subject || state.classroom?.subject || "",
      exam: state.classroom?.exam_type || "",
      status: "active",
      gradingMode: p.gradingMode || "ai_assist",
      createdAt: p.publishedAt || null,
      deadlineAt: p.deadlineAt || null,
      timeLimitMinutes: p.timeLimitMinutes || null,
      shuffleVariants: !!p.shuffleVariants,
      acceptingSubmissions: true,
      expectedStudents: null,
      studentUrl: p.studentUrl || `/student?code=${p.code}`,
      submissionsCount: 0,
      uniqueSubmitters: 0,
      submissionsToday: 0,
      tasksCount: p.tasksCount || 0,
      fromApi: false,
    });
  });
  return [...byCode.values()].sort((a, b) => {
    const ta = a.createdAt ? new Date(a.createdAt).getTime() : 0;
    const tb = b.createdAt ? new Date(b.createdAt).getTime() : 0;
    return tb - ta;
  });
}

function issuedVariantCount() {
  return mergeAssignmentLists(state.assignmentsBoard.items, state.generator.published).filter(
    (a) => a.status === "active" || a.status === "closed"
  ).length;
}

function betaLimitReached() {
  return issuedVariantCount() >= BETA_VARIANT_LIMIT;
}

function betaLimitNoteHtml() {
  const n = issuedVariantCount();
  const atCap = n >= BETA_VARIANT_LIMIT;
  return `<p class="beta-limit-note${atCap ? " is-cap" : ""}">Бета: выдано ${n} из ${BETA_VARIANT_LIMIT}${
    atCap ? " — лимит. Напишите нам, если для пилота нужно больше." : ""
  }</p>`;
}

function rnoCreatedToast(created) {
  const n = Number(created && created.unique_changed);
  const alt = !!(created && created.unique_applied);
  let extra = "";
  if (Number.isFinite(n) && n > 0) extra = ` · новые числа/формулировки: ${n}`;
  else if (alt) extra = " · другой текст заданий";
  return `Создано: ${created.title} · ${created.code}${extra}`;
}

function findAssignmentByCode(code) {
  const list = mergeAssignmentLists(state.assignmentsBoard.items, state.generator.published);
  const key = String(code || "").toUpperCase();
  return list.find((a) => String(a.code).toUpperCase() === key) || null;
}

async function patchSubmissionGrade(assignCode, submissionId, body) {
  const board = state.assignmentsBoard;
  board.gradingId = submissionId;
  render();
  try {
    const data = await api(
      `/api/assignments/${encodeURIComponent(assignCode)}/submissions/${encodeURIComponent(submissionId)}`,
      { method: "PATCH", body: JSON.stringify(body) }
    );
    const key = String(assignCode).toUpperCase();
    const pack = board.submissions[key];
    if (pack && Array.isArray(pack.items)) {
      pack.items = pack.items.map((s) => (Number(s.id) === Number(submissionId) ? { ...s, ...data } : s));
    }
    showToast("Оценка сохранена", "success");
    return data;
  } catch (err) {
    showToast(err.message || "Не удалось сохранить оценку", "error");
    throw err;
  } finally {
    board.gradingId = null;
    render();
  }
}

async function patchAssignment(code, body) {
  const board = state.assignmentsBoard;
  board.patchingCode = code;
  render();
  try {
    const data = await api(`/api/assignments/${encodeURIComponent(code)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    board.loadedFor = null;
    await loadAssignmentsBoard(true);
    return data;
  } finally {
    board.patchingCode = null;
    render();
  }
}

async function loadAssignmentsBoard(force = false) {
  const code = state.classroom?.access_code;
  const board = state.assignmentsBoard;
  if (!code || !board) return;
  if (!force && board.loadedFor === code && !board.loading) return;
  if (board.loading && board.loadedFor === code) return;

  board.loading = true;
  board.error = null;
  render();

  try {
    const data = await api(`/api/assignments/by-class/${encodeURIComponent(code)}`);
    board.items = Array.isArray(data) ? data : [];
    board.error = null;
    board.loadedFor = code;
  } catch (err) {
    board.items = [];
    board.error = err.message || "Не удалось загрузить задания";
    board.loadedFor = null;
  } finally {
    board.loading = false;
    render();
    if (state.tab === "assignments") prefetchVisibleSubmissions();
  }
}

async function loadAssignmentSubmissions(assignCode, force = false, silent = false) {
  const board = state.assignmentsBoard;
  if (!assignCode || !board) return;
  const key = String(assignCode).toUpperCase();
  const prev = board.submissions[key] || { loading: false, error: null, items: null };
  if (!force && prev.items && !prev.loading) return;
  if (prev.loading) return;

  board.submissions[key] = { loading: true, error: null, items: prev.items };
  if (!silent) render();

  try {
    const data = await api(`/api/assignments/${encodeURIComponent(key)}/submissions`);
    board.submissions[key] = {
      loading: false,
      error: null,
      items: Array.isArray(data) ? data : [],
    };
  } catch (err) {
    board.submissions[key] = {
      loading: false,
      error: err.message || "Не удалось загрузить сдачи",
      items: prev.items || [],
    };
  }
  if (!silent) render();
}

async function loadAnswerKey(assignCode, force = false) {
  const board = state.assignmentsBoard;
  if (!assignCode || !board) return;
  const key = String(assignCode).toUpperCase();
  const prev = board.answerKeys[key];
  if (!force && prev?.items && !prev.loading) return;
  if (prev?.loading) return;
  board.answerKeys[key] = { loading: true, error: null, items: prev?.items || [] };
  try {
    const data = await api(`/api/assignments/${encodeURIComponent(key)}/answer-key`);
    board.answerKeys[key] = {
      loading: false,
      error: null,
      items: Array.isArray(data) ? data : [],
    };
  } catch (err) {
    board.answerKeys[key] = {
      loading: false,
      error: err.message || "Не удалось загрузить ключ",
      items: prev?.items || [],
    };
  }
}

async function prefetchVisibleSubmissions() {
  const board = state.assignmentsBoard;
  const all = mergeAssignmentLists(board.items, state.generator.published);
  const filter = board.listFilter || "active";
  const list = all
    .filter((a) => {
      const closed = a.status === "closed" || !a.acceptingSubmissions;
      if (filter === "active") return !closed && a.status !== "draft";
      if (filter === "closed") return closed || a.status === "draft";
      return true;
    })
    .slice(0, 8);
  await Promise.all(list.map((a) => loadAssignmentSubmissions(a.code, false, true)));
  if (state.tab === "assignments") render();
}

function openGradebook(code) {
  if (!code) return;
  const board = state.assignmentsBoard;
  const key = String(code).toUpperCase();
  if (board.expandedCode && String(board.expandedCode).toUpperCase() === key) {
    board.expandedCode = null;
    board.expandedSubId = null;
    render();
    return;
  }
  board.expandedCode = code;
  board.whoModalCode = null;
  board.issueOpen = false;
  board.whoTab = "submitted";
  board.expandedSubId = null;
  board.menuOpenCode = null;
  render();
  loadAssignmentSubmissions(code, true);
  loadAnswerKey(code, true).then(() => {
    if (state.tab === "assignments") render();
  });
  loadStudentsBoard();
}

async function copyAssignmentShare(code, studentUrl) {
  const url = studentWorkUrl(code, studentUrl);
  const text = `Код работы EduSense: ${code}\n${url}`;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Код и ссылка скопированы", "success");
  } catch (_) {
    showToast("Не удалось скопировать", "error");
  }
}

async function copyRemindText(assign) {
  if (!assign) return;
  const url = studentWorkUrl(assign.code, assign.studentUrl);
  const key = String(assign.code).toUpperCase();
  const items = state.assignmentsBoard.submissions[key]?.items || [];
  const submittedKeys = new Set(items.map((s) => normalizeStudentKey(s.student_name)).filter(Boolean));
  const roster = state.studentsBoard.roster || [];
  const missing = roster.filter((name) => !submittedKeys.has(normalizeStudentKey(name)));
  const names = missing.length ? missing.join(", ") : "[имена не сдавших — заполните ростер в Учениках]";
  const text =
    `Напоминание: сдайте работу «${assign.title}»\n` +
    `Ссылка: ${url}\n` +
    `Код: ${assign.code}\n` +
    `Кому: ${names}`;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Текст напоминания скопирован", "success");
  } catch (_) {
    showToast("Не удалось скопировать", "error");
  }
}

function expectedStudentsOf(a) {
  const expected = a?.expectedStudents != null ? Number(a.expectedStudents) : null;
  if (expected && expected > 0) return expected;
  const rosterN = (state.studentsBoard?.roster || []).length;
  return rosterN > 0 ? rosterN : null;
}

function renderProgressLine(a) {
  const n = Number(a.uniqueSubmitters || a.submissionsCount || 0);
  const expected = expectedStudentsOf(a);
  if (expected && expected > 0) {
    const pct = Math.min(100, Math.round((n / expected) * 100));
    return `
      <div class="assign-progress">
        <div class="assign-progress-top">
          <span>${escapeHtml(String(n))} из ${escapeHtml(String(expected))} сдали</span>
          <span>${pct}%</span>
        </div>
        <div class="assign-progress-bar" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">
          <i style="width:${pct}%"></i>
        </div>
      </div>`;
  }
  return `<p class="assign-progress-plain">${escapeHtml(String(n))} сдали</p>`;
}

function submissionPrimaryScore(s) {
  if (!s) return null;
  const raw = s.teacher_score != null ? s.teacher_score : s.score;
  if (raw == null || !Number.isFinite(Number(raw))) return null;
  return Number(raw);
}

function submissionOgeMark(s, subject) {
  const raw = submissionPrimaryScore(s);
  if (raw == null) return null;
  const max = s.max_score != null ? Number(s.max_score) : null;
  const ogeMax = ogeMaxPrimary(subject);
  if (max != null && max >= 20) return ogeMarkFromPrimary(raw, subject);
  if (max != null && max > 0) return ogeMarkFromPercent(Math.round((raw / max) * 100), subject);
  if (raw <= ogeMax + 2) return ogeMarkFromPrimary(raw, subject);
  return ogeMarkFromPercent(raw, subject);
}

function renderSubmitterChips(assignCode, subject) {
  const key = String(assignCode || "").toUpperCase();
  const items = state.assignmentsBoard.submissions[key]?.items || [];
  if (!items.length) return "";
  const shown = items.slice(0, 8);
  const extra = items.length - shown.length;
  const chips = shown
    .map((s) => {
      const raw = submissionPrimaryScore(s);
      const mark = submissionOgeMark(s, subject);
      const tone = mark != null ? `is-${mark}` : "is-empty";
      const scoreTxt = raw != null ? `${Math.round(raw)}б` : "—";
      const markTxt = mark != null ? `(${mark})` : "";
      const title = `${s.student_name || ""} · ${scoreTxt} ${markTxt}`.trim();
      return `<span class="submit-chip ${tone}" title="${escapeHtml(title)}">
        <span class="avatar avatar-xs">${escapeHtml(initials(s.student_name))}</span>
        <span>${escapeHtml(scoreTxt)}${markTxt ? ` ${escapeHtml(markTxt)}` : ""}</span>
      </span>`;
    })
    .join("");
  return `<div class="submit-chips">${chips}${
    extra > 0 ? `<span class="submit-chip is-more">+${extra}</span>` : ""
  }</div>`;
}

function answersMatch(student, correct) {
  const a = String(student || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
  const b = String(correct || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
  if (!a || !b) return null;
  return a === b;
}

function renderSubmissionAnswers(s, assignCode) {
  const answers = Array.isArray(s.answers) ? s.answers : [];
  if (!answers.length) {
    return `<p class="assign-sub-hint" style="margin:8px 0 0">Ответы не сохранены или пусты.</p>`;
  }
  return `
    <ol class="assign-answers-list">
      ${answers
        .map((a) => {
          const num = a.num != null ? a.num : "—";
          const qText = String(a.question_text || a.questionText || "").trim();
          const topic = String(a.topic || "").trim();
          const text = String(a.text || "").trim();
          const correct = String(a.correct_answer || a.correctAnswer || "").trim();
          const solution = String(a.solution || "").trim();
          const photo = a.photo_data_url || a.photoDataUrl || null;
          const hasPhoto = !!(a.has_photo || a.hasPhoto || photo);
          const match = answersMatch(text, correct);
          const tone = match == null ? "" : match ? "is-ok" : "is-bad";
          const isP2 = Number(a.part) === 2 || Number(num) >= 20;
          let body = "";
          if (text) {
            body += `<div class="assign-answer-text"><span class="assign-answer-label">Ответ ученика:</span> ${escapeHtml(text)}</div>`;
          }
          if (correct) {
            body += `<div class="assign-answer-key"><span class="assign-answer-label">Ключ:</span> ${escapeHtml(correct)}</div>`;
          }
          if (isP2 && solution && solution !== correct) {
            body += `<pre class="answer-key-p2-sol">${escapeHtml(solution)}</pre>`;
          }
          if (hasPhoto && photo) {
            body += `<div class="assign-answer-photo"><img src="${escapeHtml(photo)}" alt="Фото к заданию ${escapeHtml(String(num))}" /></div>`;
          } else if (hasPhoto) {
            body += `<div class="assign-sub-hint">Есть фото</div>`;
          }
          if (!body) {
            body = `<div class="assign-sub-hint">Нет ответа</div>`;
          }
          const p2Card = renderPart2GradeCardForAnswer(a, s.id, assignCode);
          return `
        <li class="assign-answer-item ${tone}">
          <div class="assign-answer-num">№ ${escapeHtml(String(num))}${
            topic ? ` · ${escapeHtml(topic)}` : ""
          }</div>
          ${qText ? `<div class="assign-answer-q">${escapeHtml(qText)}</div>` : ""}
          ${body}
          ${p2Card}
        </li>`;
        })
        .join("")}
    </ol>`;
}

function submissionRowStatus(s) {
  const scoreRaw =
    s.teacher_score != null ? s.teacher_score : s.score != null ? s.score : null;
  const score =
    scoreRaw != null
      ? `${scoreRaw}${s.max_score != null ? ` / ${s.max_score}` : ""}`
      : "—";
  const dur = formatDurationSeconds(s.duration_seconds);
  const bits = [String(score)];
  if (dur) bits.push(dur);
  return bits.join(" · ");
}

function assignmentIsOgeRus(assignCode) {
  const a = findAssignmentByCode(assignCode);
  const examUi = String((a && a.exam_ui) || "").toLowerCase();
  if (examUi === "oge_rus_kim") return true;
  const subj = (a && (a.subject || a.subject_code)) || state.classroom?.subject || "";
  return teacherSubjectCode({ subject: subj, subject_code: subj, exam_ui: examUi }) === "russian";
}

const OGE_RUS_RUBRIC = {
  ik: [
    { id: "ik1", title: "ИК1 · микротемы", max: 2 },
    { id: "ik2", title: "ИК2 · сжатие", max: 3 },
    { id: "ik3", title: "ИК3 · смысловая цельность", max: 2 },
  ],
  sk: [
    { id: "sk1", title: "СК1 · понимание / тезис", max: 2 },
    { id: "sk2", title: "СК2 · аргументы", max: 3 },
    { id: "sk3", title: "СК3 · композиция", max: 2 },
  ],
  gk: [
    { id: "gk1", title: "ГК1 · орфография", max: 2 },
    { id: "gk2", title: "ГК2 · пунктуация", max: 2 },
    { id: "gk3", title: "ГК3 · грамматика", max: 2 },
    { id: "gk4", title: "ГК4 · речь", max: 2 },
  ],
};

function rusRubricSelectHtml(item, subId, busy) {
  let opts = '<option value="">—</option>';
  for (let i = 0; i <= item.max; i++) {
    opts += `<option value="${i}">${i}</option>`;
  }
  return `<label class="assign-rubric-item">
    <span>${escapeHtml(item.title)}</span>
    <select data-rubric-key="${escapeHtml(item.id)}" data-rubric-max="${item.max}" data-rubric-sub="${escapeHtml(String(subId))}" ${busy ? "disabled" : ""}>${opts}</select>
  </label>`;
}

function renderRusRubric(assignCode, subId, busy) {
  if (!assignmentIsOgeRus(assignCode)) return "";
  const groups = [
    { title: "Изложение · ИК (макс. 7)", items: OGE_RUS_RUBRIC.ik },
    { title: "Сочинение · СК (макс. 7)", items: OGE_RUS_RUBRIC.sk },
    { title: "Грамотность · ГК за оба текста (макс. 8)", items: OGE_RUS_RUBRIC.gk },
  ];
  const blocks = groups
    .map((g) => {
      const rows = g.items.map((it) => rusRubricSelectHtml(it, subId, busy)).join("");
      return `<div class="assign-rubric-group"><h5 class="assign-rubric-title">${escapeHtml(g.title)}</h5><div class="assign-rubric-row">${rows}</div></div>`;
    })
    .join("");
  return `<div class="assign-rus-rubric" data-rus-rubric="${escapeHtml(String(subId))}">
    <p class="assign-sub-hint">Шкала ОГЭ: изложение 7 + тест 2–12 (11) + сочинение 7 + ГК 8 = <strong>33</strong>. Отметьте критерии и баллы за тест — итоговый балл сложится сам.</p>
    ${blocks}
    <label class="assign-field assign-field-inline">
      <span>Тест 2–12 (0–11)</span>
      <input type="number" min="0" max="11" step="1" inputmode="numeric" data-rubric-test="${escapeHtml(String(subId))}" placeholder="11" ${busy ? "disabled" : ""} />
    </label>
    <p class="assign-rubric-sum">ИК+СК: <strong data-rubric-content="${escapeHtml(String(subId))}">0</strong> · ГК: <strong data-rubric-gk="${escapeHtml(String(subId))}">0</strong> · тест: <strong data-rubric-test-out="${escapeHtml(String(subId))}">0</strong> · <strong>итого <span data-rubric-total="${escapeHtml(String(subId))}">0</span> / 33</strong></p>
  </div>`;
}

function sumRusRubric(subId) {
  const root = document.querySelector(`[data-rus-rubric="${subId}"]`);
  if (!root) return null;
  let iksk = 0;
  let gk = 0;
  root.querySelectorAll("select[data-rubric-key]").forEach((sel) => {
    const key = sel.getAttribute("data-rubric-key") || "";
    const n = Number(sel.value);
    if (!Number.isFinite(n) || sel.value === "") return;
    if (key.indexOf("gk") === 0) gk += n;
    else iksk += n;
  });
  const testEl = root.querySelector(`[data-rubric-test="${subId}"]`);
  const testN = testEl && String(testEl.value || "").trim() !== "" ? Number(testEl.value) : 0;
  const test = Number.isFinite(testN) ? Math.max(0, Math.min(11, testN)) : 0;
  return { iksk, gk, test, total: iksk + gk + test };
}

function applyRusRubricSum(subId) {
  const sum = sumRusRubric(subId);
  if (!sum) return;
  const setTxt = (sel, v) => {
    const el = document.querySelector(sel);
    if (el) el.textContent = String(v);
  };
  setTxt(`[data-rubric-content="${subId}"]`, sum.iksk);
  setTxt(`[data-rubric-gk="${subId}"]`, sum.gk);
  setTxt(`[data-rubric-test-out="${subId}"]`, sum.test);
  setTxt(`[data-rubric-total="${subId}"]`, sum.total);
  const scoreEl = document.querySelector(`[data-grade-score="${subId}"]`);
  if (scoreEl) scoreEl.value = String(sum.total);
}

function rusRubricCommentLine(subId) {
  const root = document.querySelector(`[data-rus-rubric="${subId}"]`);
  if (!root) return "";
  const bits = [];
  root.querySelectorAll("select[data-rubric-key]").forEach((sel) => {
    if (sel.value === "") return;
    const lab = sel.closest("label")?.querySelector("span")?.textContent || sel.getAttribute("data-rubric-key");
    bits.push(`${String(lab).split("·")[0].trim()} ${sel.value}/${sel.getAttribute("data-rubric-max")}`);
  });
  const sum = sumRusRubric(subId);
  if (!bits.length || !sum) return "";
  return `Критерии: ${bits.join("; ")}. Тест 2–12: ${sum.test}/11. Итого ${sum.total}/33.`;
}

function renderSubmissionWorkView(assignCode, s) {
  const assign = findAssignmentByCode(assignCode);
  const gradingId = state.assignmentsBoard.gradingId;
  const busy = gradingId != null && Number(gradingId) === Number(s.id);
  const commentVal = s.teacher_comment || "";
  const scoreVal =
    s.teacher_score != null ? s.teacher_score : s.score != null ? s.score : "";
  const summary = String(s.review_summary || "").trim();
  const statusLine = summary || submissionStatusLabel(s.status);
  const studentPath = assign?.studentUrl || `/student?code=${assignCode}`;
  const studentHref = studentWorkUrl(assignCode, studentPath);
  const ansN = Array.isArray(s.answers) ? s.answers.length : 0;
  const draftN = part2DraftPendingCount(s, assignCode);

  return `
    <div class="who-work-view" data-sub-id="${escapeHtml(String(s.id))}">
      <button type="button" class="btn-ghost who-back-btn" id="btn-who-back-list">← К списку сдавших</button>
      <header class="who-work-head">
        <div class="student-cell">
          <span class="avatar avatar-lg">${escapeHtml(initials(s.student_name))}</span>
          <div>
            <h3 class="who-work-name">${escapeHtml(s.student_name)}</h3>
            <p class="who-work-summary">${escapeHtml(statusLine)}</p>
            <p class="assign-sub-hint" style="margin:4px 0 0">
              ${escapeHtml(submissionRowStatus(s))}
              · сдано ${escapeHtml(formatAssignDate(s.submitted_at || s.created_at))}
            </p>
          </div>
        </div>
        <a class="who-preview-link" href="${escapeHtml(studentHref)}" target="_blank" rel="noopener noreferrer">
          Открыть вариант как ученик
        </a>
      </header>
      <section class="who-work-answers" aria-label="Ответы ученика">
        <h4 class="who-section-title">Ответы${ansN ? ` (${ansN})` : ""}</h4>
        ${
          draftN
            ? `<div class="p2-draft-banner">
                <p>ИИ подготовил черновик по ${draftN} заданиям части 2 — балл не засчитан, пока не подтвердите.</p>
                <button type="button" class="btn-secondary" data-p2-action="accept-all-drafts" data-p2-assign="${escapeHtml(
                  String(assignCode)
                )}" data-p2-sub="${escapeHtml(String(s.id))}">Принять все черновики ИИ</button>
              </div>`
            : ""
        }
        <div class="assign-answers-panel is-expanded">${renderSubmissionAnswers(s, assignCode)}</div>
      </section>
      <section class="who-work-grade" aria-label="Оценка учителя">
        <h4 class="who-section-title">Оценка учителя</h4>
        ${renderRusRubric(assignCode, s.id, busy)}
        <div class="assign-grade-form">
          <label class="assign-field assign-field-inline">
            <span>Балл</span>
            <input type="number" min="0" max="500" step="0.5" inputmode="decimal"
              data-grade-score="${escapeHtml(String(s.id))}"
              value="${escapeHtml(scoreVal === "" ? "" : String(scoreVal))}"
              placeholder="например 12" ${busy ? "disabled" : ""} />
          </label>
          <label class="assign-field assign-field-grow">
            <span>Комментарий ученику</span>
            <textarea rows="3" data-grade-comment="${escapeHtml(String(s.id))}"
              placeholder="Коротко: что хорошо и что поправить"
              ${busy ? "disabled" : ""}>${escapeHtml(commentVal)}</textarea>
          </label>
          <button type="button" class="btn-primary who-save-grade" data-save-grade="${escapeHtml(
            String(s.id)
          )}" data-assign-code="${escapeHtml(assignCode)}" ${busy ? "disabled" : ""}>
            ${busy ? "Сохраняем…" : "Сохранить"}
          </button>
        </div>
      </section>
    </div>`;
}

function renderSubmissionsBlock(assignCode) {
  const key = String(assignCode).toUpperCase();
  const pack = state.assignmentsBoard.submissions[key];
  if (!pack) {
    return `<p class="assign-sub-hint">Загрузка сдач…</p>`;
  }
  if (pack.loading && !pack.items) {
    return `<p class="assign-sub-hint">Загрузка сдач…</p>`;
  }
  if (pack.error && (!pack.items || !pack.items.length)) {
    return `<p class="assign-sub-hint is-error">${escapeHtml(pack.error)}</p>`;
  }
  const items = pack.items || [];
  if (!items.length) {
    const assign = findAssignmentByCode(assignCode);
    const path = assign?.studentUrl || `/student?code=${assignCode}`;
    return `<div class="who-empty">
      <p class="empty-title">Пока никто не сдал</p>
      <p class="assign-sub-hint">Скопируйте ссылку и отправьте ученикам.</p>
      <button type="button" class="btn-secondary" data-copy-assign="${escapeHtml(assignCode)}" data-copy-url="${escapeHtml(path)}" style="width:auto;margin-top:10px">Скопировать ссылку</button>
    </div>`;
  }

  const expandedSubId = state.assignmentsBoard.expandedSubId;
  if (expandedSubId != null) {
    const openSub = items.find((s) => Number(s.id) === Number(expandedSubId));
    if (openSub) {
      return renderSubmissionWorkView(assignCode, openSub);
    }
  }

  return `
    <div class="assign-grade-list who-submitters">
      ${items
        .map((s) => {
          const statusShort = submissionRowStatus(s);
          const summary = String(s.review_summary || "").trim();
          return `
        <article class="who-submitter-row" data-sub-id="${escapeHtml(String(s.id))}">
          <div class="student-cell">
            <span class="avatar">${escapeHtml(initials(s.student_name))}</span>
            <div class="who-meta">
              <strong>${escapeHtml(s.student_name)}</strong>
              <span>${escapeHtml(statusShort)}${
                summary ? ` · ${escapeHtml(summary)}` : ""
              }</span>
            </div>
          </div>
          <button type="button" class="btn-primary who-view-work" data-view-work="${escapeHtml(
            String(s.id)
          )}">Смотреть работу</button>
        </article>`;
        })
        .join("")}
    </div>
    ${pack.error ? `<p class="assign-sub-hint is-error">${escapeHtml(pack.error)}</p>` : ""}
    ${pack.loading ? `<p class="assign-sub-hint">Обновляем…</p>` : ""}
  `;
}

function renderAnswerKey(assignCode) {
  const key = String(assignCode || "").toUpperCase();
  const pack = state.assignmentsBoard.answerKeys[key];
  if (!pack || pack.loading) {
    return `<p class="assign-sub-hint">Загрузка мастер-ключа…</p>`;
  }
  if (pack.error && !(pack.items || []).length) {
    return `<p class="assign-sub-hint is-error">${escapeHtml(pack.error)}</p>`;
  }
  const items = pack.items || [];
  if (!items.length) {
    return `<p class="assign-sub-hint">Ключ ответов для этого варианта пока недоступен.</p>`;
  }
  const part2 = items.filter((item) => Number(item.part) === 2 || Number(item.num) >= 20);
  const part1 = items.filter((item) => !part2.includes(item));

  const shortRow = (item) => {
    const topic = topicLabelRu(item.topic || "");
    return `<li>
      <b>№${escapeHtml(String(item.num))}</b>
      ${topic ? `<span class="answer-key-topic">${escapeHtml(topic)}</span>` : ""}
      <code>${escapeHtml(item.answer || "—")}</code>
    </li>`;
  };

  const part2Card = (item) => {
    const topic = topicLabelRu(item.topic || "");
    const body = String(item.solution || item.answer || "").trim() || "—";
    const short = String(item.answer || "").trim();
    const showShort = short && short !== body && short.length < 120;
    return `<article class="answer-key-p2">
      <header>
        <b>№${escapeHtml(String(item.num))}</b>
        ${topic ? `<span class="answer-key-topic">${escapeHtml(topic)}</span>` : ""}
        <span class="answer-key-pts">${escapeHtml(String(item.max_score || 2))} б</span>
      </header>
      ${showShort ? `<p class="answer-key-p2-ans">Ответ: <code>${escapeHtml(short)}</code></p>` : ""}
      <pre class="answer-key-p2-sol">${escapeHtml(body)}</pre>
    </article>`;
  };

  return `
    ${
      part2.length
        ? `<div class="answer-key-p2-block">
            <h5 class="answer-key-h">Часть 2 — ответы сразу</h5>
            ${part2.map(part2Card).join("")}
          </div>`
        : ""
    }
    ${
      part1.length
        ? `<div class="answer-key-p1-block">
            <h5 class="answer-key-h">Часть 1</h5>
            <ol class="answer-key-list">${part1.map(shortRow).join("")}</ol>
          </div>`
        : ""
    }
  `;
}

function renderGradebookAccordion(assign) {
  const board = state.assignmentsBoard;
  const code = assign.code;
  const tab = board.whoTab || "submitted";
  const viewingWork =
    tab === "submitted" &&
    board.expandedSubId != null &&
    (board.submissions[String(code).toUpperCase()]?.items || []).some(
      (s) => Number(s.id) === Number(board.expandedSubId)
    );

  let body = "";
  if (tab === "key") {
    body = `<div class="gradebook-key">
      <h4 class="who-section-title">Мастер-ключ</h4>
      <p class="assign-sub-hint">Часть 2 сверху, целиком. Часть 1 — краткие ключи ниже. У персонализированных работ числа у ученика могут отличаться.</p>
      ${renderAnswerKey(code)}
    </div>`;
  } else if (tab === "not_started") {
    const roster = state.studentsBoard.roster || [];
    const pack = board.submissions[String(code).toUpperCase()] || { items: [] };
    const items = pack.items || [];
    if (!roster.length) {
      body = `<div class="who-empty">
        <p class="empty-title">Список класса пуст</p>
        <p class="assign-sub-hint">Добавьте ФИО в разделе «Ученики».</p>
        <button type="button" class="btn-secondary" id="btn-who-to-students" style="width:auto;margin-top:12px">Открыть Ученики</button>
      </div>`;
    } else {
      const submittedKeys = new Set(items.map((s) => normalizeStudentKey(s.student_name)).filter(Boolean));
      const missing = roster.filter((name) => !submittedKeys.has(normalizeStudentKey(name)));
      body = missing.length
        ? `<ul class="who-list">${missing
            .map(
              (name) => `<li>
            <div class="who-row">
              <span class="avatar">${escapeHtml(initials(name))}</span>
              <div class="who-meta"><strong>${escapeHtml(name)}</strong><span>не приступил</span></div>
            </div>
          </li>`
            )
            .join("")}</ul>`
        : `<p class="assign-sub-hint">Все из списка уже сдали.</p>`;
    }
  } else {
    body = renderSubmissionsBlock(code);
  }

  return `
    <div class="gradebook" data-gradebook="${escapeHtml(code)}">
      <div class="gradebook-toolbar">
        ${
          viewingWork
            ? ""
            : `<div class="who-tabs" role="tablist">
          <button type="button" class="who-tab ${tab === "submitted" ? "is-active" : ""}" data-who-tab="submitted">Сдавшие</button>
          <button type="button" class="who-tab ${tab === "not_started" ? "is-active" : ""}" data-who-tab="not_started">Не приступили</button>
          <button type="button" class="who-tab ${tab === "key" ? "is-active" : ""}" data-who-tab="key">Мастер-ключ</button>
        </div>`
        }
        <div class="gradebook-export">
          <span>Скачать результаты</span>
          <button type="button" class="btn-ghost assign-btn" data-export-csv="${escapeHtml(code)}">CSV</button>
          <button type="button" class="btn-ghost assign-btn" data-export-pdf="${escapeHtml(code)}">PDF</button>
        </div>
      </div>
      <div class="gradebook-body">${body}</div>
    </div>`;
}

function exportGradebookCsv(code) {
  const assign = findAssignmentByCode(code);
  if (!assign) return;
  const key = String(code).toUpperCase();
  const items = state.assignmentsBoard.submissions[key]?.items || [];
  const subject = assign.subject || state.classroom?.subject || "";
  const header = ["ФИО", "Балл", "Максимум", "Оценка", "Статус", "Дата"];
  const lines = [header.join(";")];
  items.forEach((s) => {
    const raw = submissionPrimaryScore(s);
    const mark = submissionOgeMark(s, subject);
    const cells = [
      s.student_name || "",
      raw != null ? String(raw).replace(".", ",") : "",
      s.max_score != null ? String(s.max_score).replace(".", ",") : "",
      mark != null ? String(mark) : "",
      submissionStatusLabel(s.status),
      s.submitted_at || s.created_at || "",
    ].map((cell) => {
      const v = String(cell ?? "");
      if (/[;"\n]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
      return v;
    });
    lines.push(cells.join(";"));
  });
  const blob = new Blob(["\uFEFF" + lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `edusense-${assign.code}-vedomost.csv`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 0);
  showToast("CSV скачан", "success");
}

function exportGradebookPdf(code) {
  const assign = findAssignmentByCode(code);
  if (!assign) return;
  const key = String(code).toUpperCase();
  const items = state.assignmentsBoard.submissions[key]?.items || [];
  const subject = assign.subject || state.classroom?.subject || "";
  const keyItems = state.assignmentsBoard.answerKeys[key]?.items || [];
  const rows = items
    .map((s) => {
      const raw = submissionPrimaryScore(s);
      const mark = submissionOgeMark(s, subject);
      return `<tr>
        <td>${escapeHtml(s.student_name || "")}</td>
        <td>${raw != null ? escapeHtml(String(raw)) : "—"}</td>
        <td>${s.max_score != null ? escapeHtml(String(s.max_score)) : "—"}</td>
        <td>${mark != null ? escapeHtml(String(mark)) : "—"}</td>
      </tr>`;
    })
    .join("");
  const keyRows = keyItems
    .map(
      (item) =>
        `<tr><td>№${escapeHtml(String(item.num))}</td><td>${escapeHtml(
          topicLabelRu(item.topic || "") || ""
        )}</td><td>${escapeHtml(item.answer || "—")}</td></tr>`
    )
    .join("");
  const win = window.open("", "_blank");
  if (!win) {
    showToast("Разрешите всплывающие окна для PDF", "error");
    return;
  }
  win.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"/><title>${escapeHtml(
    assign.title
  )}</title>
    <style>
      @page { size: A4; margin: 12mm; }
      * { box-sizing: border-box; }
      body { font-family: Inter, system-ui, sans-serif; color:#111; margin:0; background:#fff; }
      .a4-sheet { position:relative; overflow:hidden; padding:28px; min-height:100vh; }
      ${eduSensePrintWatermarkCss()}
      h1 { font-size: 20px; margin: 0 0 6px; }
      p { color:#555; margin: 0 0 16px; }
      table { width:100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 13px; }
      th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; }
      th { background: #f4f5f7; }
    </style></head><body>
      <div class="a4-sheet">
      ${eduSenseWatermarkHtml()}
      <div class="print-inner">
      ${eduSenseBrandHtml()}
      <h1>${escapeHtml(assign.title)}</h1>
      <p>Код ${escapeHtml(assign.code)} · ${escapeHtml(subject)} · ведомость</p>
      <h2>Результаты</h2>
      <table><thead><tr><th>ФИО</th><th>Балл</th><th>Макс</th><th>Оценка</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="4">Нет сдач</td></tr>`}</tbody></table>
      <h2>Мастер-ключ</h2>
      <table><thead><tr><th>№</th><th>Тема</th><th>Ответ</th></tr></thead>
      <tbody>${keyRows || `<tr><td colspan="3">Ключ недоступен</td></tr>`}</tbody></table>
      </div>
      </div>
      <script>window.onload=()=>{setTimeout(()=>window.print(),250);}<\/script>
    </body></html>`);
  win.document.close();
  showToast("Отчёт открыт · сохраните как PDF", "success");
}

function renderWhoModal() {
  const board = state.assignmentsBoard;
  const code = board.whoModalCode;
  if (!code) return "";
  const assign = findAssignmentByCode(code);
  if (!assign) return "";
  const key = String(code).toUpperCase();
  const pack = board.submissions[key] || { loading: true, items: null, error: null };
  const tab = board.whoTab || "submitted";
  const items = pack.items || [];
  const meta = assignmentStatusMeta(assign);
  const accepting = !!assign.acceptingSubmissions && assign.status !== "closed";
  const patching = board.patchingCode && String(board.patchingCode).toUpperCase() === key;
  const viewingWork =
    tab === "submitted" &&
    board.expandedSubId != null &&
    (pack.items || []).some((s) => Number(s.id) === Number(board.expandedSubId));
  const studentPath = assign.studentUrl || `/student?code=${assign.code}`;
  const studentHref = studentWorkUrl(assign.code, studentPath);

  let body = "";
  if (tab === "not_started") {
    const roster = state.studentsBoard.roster || [];
    if (!roster.length) {
      body = `
      <div class="who-empty">
        <p class="empty-title">Список класса пуст</p>
        <p class="assign-sub-hint">Добавьте ФИО в разделе «Ученики», чтобы видеть, кто не приступил.</p>
        <button type="button" class="btn-secondary" id="btn-who-to-students" style="width:auto;margin-top:12px">Открыть Ученики</button>
      </div>`;
    } else if (pack.loading && !pack.items) {
      body = `<p class="assign-sub-hint">Загрузка сдач…</p>`;
    } else {
      const submittedKeys = new Set(
        (items || []).map((s) => normalizeStudentKey(s.student_name)).filter(Boolean)
      );
      const missing = roster.filter((name) => !submittedKeys.has(normalizeStudentKey(name)));
      if (!missing.length) {
        body = `<p class="assign-sub-hint">Все из списка уже сдали.</p>`;
      } else {
        body = `
      <ul class="who-list">
        ${missing
          .map(
            (name) => `
          <li>
            <div class="who-row">
              <span class="avatar">${escapeHtml(initials(name))}</span>
              <div class="who-meta">
                <strong>${escapeHtml(name)}</strong>
                <span>не приступил</span>
              </div>
            </div>
          </li>`
          )
          .join("")}
      </ul>`;
      }
    }
  } else {
    body = renderSubmissionsBlock(code);
  }

  return `
    <div class="modal-backdrop who-backdrop" id="who-backdrop">
      <div class="who-modal who-modal-wide ${viewingWork ? "is-work-view" : ""}" role="dialog" aria-modal="true" aria-labelledby="who-title">
        <div class="publish-top">
          <div>
            <p class="export-kicker">Работа</p>
            <h2 id="who-title">${escapeHtml(assign.title)}</h2>
            <p class="publish-sub who-meta-line">
              <span class="assign-badge ${meta.cls}">${escapeHtml(meta.label)}</span>
              <span class="who-code">код ${escapeHtml(assign.code)}</span>
              ${assign.deadlineAt ? `<span>до ${escapeHtml(formatAssignDate(assign.deadlineAt))}</span>` : ""}
            </p>
          </div>
          <button type="button" class="icon-x" id="btn-close-who" aria-label="Закрыть">×</button>
        </div>
        <div class="who-intake-bar">
          <button type="button" class="btn-secondary who-action-btn" data-extend-deadline="${escapeHtml(
            assign.code
          )}" ${patching ? "disabled" : ""}>+1 день</button>
          ${
            accepting
              ? `<button type="button" class="btn-ghost who-action-btn" data-close-intake="${escapeHtml(
                  assign.code
                )}" ${patching ? "disabled" : ""}>Закрыть приём</button>`
              : `<button type="button" class="btn-primary who-action-btn" data-reopen-intake="${escapeHtml(
                  assign.code
                )}" ${patching ? "disabled" : ""}>Открыть приём</button>`
          }
          <button type="button" class="btn-ghost who-action-btn" data-copy-assign="${escapeHtml(
            assign.code
          )}" data-copy-url="${escapeHtml(assign.studentUrl || "")}">Скопировать ссылку</button>
        </div>
        ${
          viewingWork
            ? ""
            : `<div class="who-tabs" role="tablist">
          <button type="button" class="who-tab ${tab === "submitted" ? "is-active" : ""}" data-who-tab="submitted">Кто сдал</button>
          <button type="button" class="who-tab ${tab === "not_started" ? "is-active" : ""}" data-who-tab="not_started">Не приступили</button>
        </div>`
        }
        <div class="who-body ${viewingWork ? "is-work-view" : ""}">${body}</div>
        ${
          viewingWork
            ? `<div class="publish-foot">
          <a class="who-preview-link" href="${escapeHtml(studentHref)}" target="_blank" rel="noopener noreferrer">Открыть вариант как ученик</a>
          <button type="button" class="btn-secondary" id="btn-close-who-foot" style="width:auto">Закрыть</button>
        </div>`
            : `<div class="publish-foot">
          <button type="button" class="btn-ghost" id="btn-remind-missing" style="width:auto">Напомнить не сдавшим</button>
          <button type="button" class="btn-secondary" id="btn-close-who-foot" style="width:auto">Закрыть</button>
        </div>`
        }
      </div>
    </div>
  `;
}

function renderIssueModal() {
  const board = state.assignmentsBoard;
  if (!board.issueOpen) return "";
  const step = board.issueStep || "choose";
  const s = board.issueSettings || {};
  const recent = mergeAssignmentLists(board.items, state.generator.published).slice(0, 6);

  let body = "";
  if (step === "settings") {
    body = `
      <div class="publish-section">
        <h3>Параметры выдачи</h3>
        <p class="publish-hint">Сохранятся при сборке в «Тестах» и при повторной выдаче</p>
        <label class="assign-field">
          <span>Дедлайн (местное время, можно пустым)</span>
          <input type="datetime-local" id="issue-deadline" value="${escapeHtml(futureDatetimeLocalValue(s.deadlineAt || ""))}" />
        </label>
        <label class="assign-field">
          <span>Лимит времени (мин)</span>
          <input type="number" id="issue-time-limit" min="1" max="600" placeholder="без лимита" value="${escapeHtml(
            s.timeLimitMinutes != null && s.timeLimitMinutes !== "" ? String(s.timeLimitMinutes) : ""
          )}" />
        </label>
      </div>
      <div class="publish-foot">
        <button type="button" class="btn-ghost" data-issue-step="choose">Назад</button>
        <button type="button" class="btn-primary" id="btn-issue-to-tests" style="width:auto;min-width:200px">К сборке в Тестах →</button>
      </div>`;
  } else if (step === "recent") {
    body = `
      <div class="publish-section">
        <h3>Последние выданные работы</h3>
        <p class="publish-hint">Откройте карточку или скопируйте ссылку. Полный re-publish вопросов — из «Тестов».</p>
        ${
          recent.length
            ? `<ul class="issue-recent">
                ${recent
                  .map(
                    (a) => `
                  <li>
                    <button type="button" class="issue-recent-item" data-open-who="${escapeHtml(a.code)}">
                      <strong>${escapeHtml(a.title)}</strong>
                      <span>${escapeHtml(a.code)} · ${escapeHtml(submissionsCountLabel(a.uniqueSubmitters || a.submissionsCount || 0))}</span>
                    </button>
                    <button type="button" class="btn-ghost assign-btn" data-copy-assign="${escapeHtml(a.code)}" data-copy-url="${escapeHtml(
                      a.studentUrl || ""
                    )}">${icon("copy")}</button>
                  </li>`
                  )
                  .join("")}
              </ul>`
            : `<p class="assign-sub-hint">Пока нет выданных работ.</p>`
        }
      </div>
      <div class="publish-foot">
        <button type="button" class="btn-ghost" data-issue-step="choose">Назад</button>
      </div>`;
  } else {
    body = `
      <div class="issue-choices">
        <button type="button" class="issue-choice" data-issue-step="settings">
          <strong>Собрать новую</strong>
          <span>Перейти в «Тесты», задать дедлайн и лимит, выдать классу</span>
        </button>
        <button type="button" class="issue-choice" data-issue-step="recent">
          <strong>Из недавних</strong>
          <span>Открыть уже выданные работы и ссылки ученикам</span>
        </button>
      </div>`;
  }

  return `
    <div class="modal-backdrop who-backdrop" id="issue-backdrop">
      <div class="who-modal issue-modal" role="dialog" aria-modal="true" aria-labelledby="issue-title">
        <div class="publish-top">
          <div>
            <p class="export-kicker">Задания</p>
            <h2 id="issue-title">Назначить новую работу классу</h2>
            <p class="publish-sub">${escapeHtml(classTitle(state.classroom))}</p>
          </div>
          <button type="button" class="icon-x" id="btn-close-issue" aria-label="Закрыть">×</button>
        </div>
        ${body}
      </div>
    </div>
  `;
}

function renderAssignments() {
  const board = state.assignmentsBoard;
  const all = mergeAssignmentLists(board.items, state.generator.published);
  const filter = board.listFilter || "active";
  const list = all.filter((a) => {
    const closed = a.status === "closed" || !a.acceptingSubmissions;
    if (filter === "active") return !closed && a.status !== "draft";
    if (filter === "closed") return closed || a.status === "draft";
    return true;
  });
  const counts = {
    active: all.filter((a) => a.status !== "closed" && a.acceptingSubmissions && a.status !== "draft")
      .length,
    closed: all.filter((a) => a.status === "closed" || !a.acceptingSubmissions || a.status === "draft")
      .length,
    all: all.length,
  };

  const filterBar = `
    <div class="assign-filter" role="tablist" aria-label="Фильтр заданий">
      <button type="button" class="assign-filter-btn ${filter === "active" ? "is-active" : ""}" data-assign-filter="active">Активные (${counts.active})</button>
      <button type="button" class="assign-filter-btn ${filter === "closed" ? "is-active" : ""}" data-assign-filter="closed">Закрытые (${counts.closed})</button>
      <button type="button" class="assign-filter-btn ${filter === "all" ? "is-active" : ""}" data-assign-filter="all">Все (${counts.all})</button>
    </div>`;

  const header = `
    ${filterBar}
    ${betaLimitNoteHtml()}
    ${
      board.error
        ? `<p class="assign-sub-hint is-error">${escapeHtml(board.error)}${
            all.length ? " · показаны данные сессии" : ""
          }</p>`
        : ""
    }
  `;

  if (board.loading && !all.length) {
    return `
      <div class="assign-hub">
        ${header}
        <p class="assign-sub-hint">Загружаем выданные работы…</p>
        ${renderIssueModal()}
        ${renderWhoModal()}
      </div>`;
  }

  if (!all.length) {
    return `
      <div class="assign-hub">
        ${header}
        <section class="glass shell-screen reveal assign-empty">
          <p class="empty-title">Пока нет выданных работ</p>
          <p class="shell-note">Соберите вариант и выдайте классу — ученики зайдут по коду.</p>
          <div class="actions" style="margin-top:18px">
            <button type="button" class="btn-primary" id="btn-issue-new-empty" style="width:auto;min-width:220px">
              + Назначить работу классу
            </button>
          </div>
        </section>
        ${renderIssueModal()}
        ${renderWhoModal()}
      </div>`;
  }

  if (!list.length) {
    const emptyHint =
      filter === "active"
        ? "Нет активных работ. Откройте приём у закрытой или выдайте новую."
        : filter === "closed"
          ? "Закрытых работ нет — все ещё принимают ответы."
          : "Список пуст.";
    return `
      <div class="assign-hub">
        ${header}
        <section class="glass shell-screen reveal assign-empty">
          <p class="empty-title">${escapeHtml(
            filter === "active" ? "Нет активных" : filter === "closed" ? "Нет закрытых" : "Пусто"
          )}</p>
          <p class="shell-note">${escapeHtml(emptyHint)}</p>
          <div class="actions" style="margin-top:18px">
            <button type="button" class="btn-primary" id="btn-issue-new-empty" style="width:auto;min-width:220px">
              + Назначить работу классу
            </button>
          </div>
        </section>
        ${renderIssueModal()}
        ${renderWhoModal()}
      </div>`;
  }

  return `
    <div class="assign-hub">
      ${header}
      <div class="assign-list">
        ${list
          .map((a) => {
            const codeKey = String(a.code).toUpperCase();
            const meta = assignmentStatusMeta(a);
            const path = a.studentUrl || `/student?code=${a.code}`;
            const accepting = !!a.acceptingSubmissions && a.status !== "closed";
            const expanded = board.expandedCode && String(board.expandedCode).toUpperCase() === codeKey;
            const deadlineLine = a.deadlineAt
              ? `до ${formatAssignDate(a.deadlineAt)}`
              : "без дедлайна";
            const timerLine = a.timeLimitMinutes ? `${a.timeLimitMinutes} мин` : null;
            const patching =
              board.patchingCode && String(board.patchingCode).toUpperCase() === codeKey;
            const subject = a.subject || state.classroom?.subject || "";
            const issuedAt = a.createdAt || a.created_at || a.deadlineAt || null;
            const issuedLabel = issuedAt ? formatAssignDate(issuedAt) : "—";
            const doneN = Number(a.uniqueSubmitters || a.submissionsCount || 0);
            const totalN = expectedStudentsOf(a) || sidebarStudentCount() || 0;
            const ratio = totalN ? `${doneN}/${totalN}` : String(doneN);
            return `
        <article class="glass assign-card assign-card-v2 ${expanded ? "is-open" : ""}" data-assign-code="${escapeHtml(a.code)}">
          <div class="assign-top">
            <div>
              <h3>${escapeHtml(a.title)}</h3>
              <div class="assign-meta-grid">
                <span><b>Предмет:</b> ${escapeHtml(a.subject || subject || "—")}</span>
                <span><b>Дата выдачи:</b> ${escapeHtml(issuedLabel)}</span>
                <span><b>Сдано:</b> ${escapeHtml(ratio)} учеников</span>
                <span><b>Код:</b> ${escapeHtml(a.code)}</span>
              </div>
            </div>
            <span class="assign-badge ${meta.cls}">${escapeHtml(meta.label)}</span>
          </div>
          ${renderSubmitterChips(a.code, subject) || renderProgressLine(a)}
          <div class="assign-actions assign-actions-v2">
            <button type="button" class="btn-secondary assign-btn" data-assign-view="${escapeHtml(a.code)}">👁️ Посмотреть варианты/ответы</button>
            <button type="button" class="btn-secondary assign-btn" data-assign-analytics="${escapeHtml(a.code)}">📊 Аналитика сдачи</button>
            <button type="button" class="btn-secondary assign-btn" data-assign-pdf="${escapeHtml(a.code)}" data-keys="0">🖨️ Печать PDF без ключей</button>
            <button type="button" class="btn-secondary assign-btn" data-assign-pdf="${escapeHtml(a.code)}" data-keys="1">🖨️ Печать PDF с ключами</button>
            <button type="button" class="btn-ghost assign-btn" data-copy-assign="${escapeHtml(a.code)}" data-copy-url="${escapeHtml(path)}">🔗 Скопировать ссылку</button>
            <button type="button" class="btn-ghost assign-btn" data-assign-qr="${escapeHtml(a.code)}">QR-код</button>
            <button type="button" class="btn-primary assign-btn assign-btn-vedomost" data-toggle-gradebook="${escapeHtml(a.code)}" aria-expanded="${expanded ? "true" : "false"}">Ведомость успеваемости класса</button>
            <button type="button" class="btn-ghost assign-btn" data-extend-deadline="${escapeHtml(a.code)}" ${patching ? "disabled" : ""}>+1 день</button>
            ${
              accepting
                ? `<button type="button" class="btn-ghost assign-btn" data-close-intake="${escapeHtml(a.code)}" ${patching ? "disabled" : ""}>Закрыть приём</button>`
                : `<button type="button" class="btn-secondary assign-btn" data-reopen-intake="${escapeHtml(a.code)}" ${patching ? "disabled" : ""}>Открыть приём</button>`
            }
          </div>
          ${expanded ? renderGradebookAccordion(a) : ""}
        </article>`;
          })
          .join("")}
      </div>
      ${renderIssueModal()}
      ${renderWhoModal()}
    </div>
  `;
}

function formatRelativeActivity(value) {
  if (!value) return "Ещё не был активен";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "Ещё не был активен";
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return `Был активен ${formatAssignDate(value)}`;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "Был активен только что";
  if (mins < 60) return `Был активен ${mins} мин назад`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Был активен ${hours} ч назад`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Был активен ${days} дн. назад`;
  return `Был активен ${formatAssignDate(value)}`;
}

function formatRosterActivity(value) {
  if (!value) return "ещё не был активен";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "ещё не был активен";
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return formatAssignDate(value);
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "активен только что";
  if (mins < 60) return `активен ${mins} мин назад`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `активен ${hours} ч назад`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `активен ${days} дн. назад`;
  return formatAssignDate(value);
}

function studentPercent(s) {
  if (s == null || s.avg_percent == null) return null;
  const n = Number(s.avg_percent);
  return Number.isFinite(n) ? Math.round(n) : null;
}

function percentToneClass(pct) {
  if (pct == null) return "is-empty";
  if (pct >= 70) return "is-good";
  if (pct >= 45) return "is-mid";
  return "is-bad";
}

function ogeMaxPrimary(subject) {
  if (typeof OgeGrade !== "undefined") return OgeGrade.maxPrimary(subject);
  return /русск/i.test(String(subject || "")) ? 33 : 31;
}

function ogeMarkFromPrimary(primary, subject) {
  if (primary == null || !Number.isFinite(Number(primary))) return null;
  if (typeof OgeGrade !== "undefined") {
    return Number(OgeGrade.markFromScale(primary, subject));
  }
  const p = Math.round(Number(primary));
  if (/русск/i.test(String(subject || ""))) {
    if (p >= 29) return 5;
    if (p >= 23) return 4;
    if (p >= 15) return 3;
    return 2;
  }
  if (p >= 22) return 5;
  if (p >= 15) return 4;
  if (p >= 8) return 3;
  return 2;
}

function ogeMarkFromPercent(pct, subject) {
  if (pct == null || !Number.isFinite(Number(pct))) return null;
  const max = ogeMaxPrimary(subject);
  return ogeMarkFromPrimary(Math.round((Number(pct) / 100) * max), subject);
}

function weakestSubtypeBadge(s) {
  const tags = s.weak_topics || [];
  if (!tags.length) return `<span class="roster-badge is-ok">без пробелов</span>`;
  let label = topicLabelRu(tags[0]);
  const heat = state.analyticsBoard?.data?.heatmap || [];
  const hit = heat.find((h) => {
    const topic = topicLabelRu(h.topic || "");
    return topic && (topic === label || label.includes(topic) || topic.includes(label));
  });
  if (hit && !/^№/.test(label)) label = `№${hit.num} ${label}`;
  const short = label.length > 28 ? `${label.slice(0, 26)}…` : label;
  return `<span class="roster-badge is-warn">⚠️ ${escapeHtml(short)}</span>`;
}

function filterRoster(rows, query) {
  const q = String(query || "")
    .trim()
    .toLowerCase();
  if (!q) return rows;
  return rows.filter((s) => String(s.name || "").toLowerCase().includes(q));
}

function rosterActivityTs(s) {
  const t = s?.last_activity_at ? new Date(s.last_activity_at).getTime() : 0;
  return Number.isFinite(t) ? t : 0;
}

function sortRoster(rows, sort) {
  const copy = (rows || []).slice();
  if (sort === "score") {
    copy.sort((a, b) => (Number(b.avg_percent) || -1) - (Number(a.avg_percent) || -1));
  } else if (sort === "activity") {
    copy.sort((a, b) => rosterActivityTs(b) - rosterActivityTs(a));
  } else {
    copy.sort((a, b) => String(a.name || "").localeCompare(String(b.name || ""), "ru"));
  }
  return copy;
}

function ogeThresholds(subject) {
  if (/русск/i.test(String(subject || ""))) {
    return { max: 33, 3: 15, 4: 23, 5: 29 };
  }
  return { max: 31, 3: 8, 4: 15, 5: 22 };
}

function currentPrimaryFromStudent(s, subject) {
  if (!s) return null;
  const max = ogeMaxPrimary(subject);
  if (s.avg_score != null && Number.isFinite(Number(s.avg_score)) && Number(s.avg_score) <= max + 2) {
    return Math.round(Number(s.avg_score));
  }
  const pct = studentPercent(s);
  if (pct == null) return null;
  return Math.round((pct / 100) * max);
}

function classRosterStats(students, rosterN) {
  const rows = students || [];
  const withPct = rows.filter((s) => studentPercent(s) != null);
  const avg = withPct.length
    ? Math.round(withPct.reduce((sum, s) => sum + studentPercent(s), 0) / withPct.length)
    : null;
  const submitted = rows.filter((s) => Number(s.submissions_count) > 0).length;
  const denom = Math.max(Number(rosterN) || rows.length, 0);
  const submitPct = denom ? Math.round((submitted / denom) * 100) : null;
  let weak = "";
  const heat = state.analyticsBoard?.data?.heatmap || [];
  if (heat.length) {
    const worst = heat
      .slice()
      .sort((a, b) => (b.wrong_pct || 0) - (a.wrong_pct || 0) || a.num - b.num)[0];
    if (worst && Number(worst.wrong_pct || 0) > 0) {
      const topic = topicLabelRu(worst.topic || "");
      weak = topic ? `№${worst.num} ${topic}` : `№${worst.num}`;
    }
  }
  if (!weak) {
    const counts = new Map();
    rows.forEach((s) => {
      const t = (s.weak_topics || [])[0];
      if (!t) return;
      const label = topicLabelRu(t);
      counts.set(label, (counts.get(label) || 0) + 1);
    });
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    if (top) weak = top[0];
  }
  return { avg, submitPct, submitted, denom, weak };
}

function visibleRoster() {
  const board = state.studentsBoard;
  return sortRoster(filterRoster(board.students || [], board.query), board.sort || "name");
}

function ensureStudentSelection() {
  const board = state.studentsBoard;
  const students = board.students || [];
  if (!students.length) {
    board.profileName = null;
    return null;
  }
  const key = normalizeStudentKey(board.profileName);
  const exists = students.some((s) => normalizeStudentKey(s.name) === key);
  if (!exists) {
    board.profileName = students[0].name;
    board.profileAnalytics = null;
    board.profileHistory = [];
  }
  return board.profileName;
}

function maybeLoadSelectedProfile() {
  const board = state.studentsBoard;
  if (state.tab !== "students") return;
  const name = ensureStudentSelection();
  if (name && !board.profileLoading && !board.profileAnalytics) {
    openStudentProfile(name);
  }
}

async function issueRemediationForStudent(name) {
  const code = state.classroom?.access_code;
  const board = state.studentsBoard;
  const analytics = board.profileAnalytics;
  if (!code || !name) return;
  if (betaLimitReached()) {
    showToast(
      `В открытой бете на класс можно выдать ${BETA_VARIANT_LIMIT} вариантов. Сейчас выдано ${issuedVariantCount()}.`,
      "error"
    );
    return;
  }
  if (!analytics?.weakest_nums?.length) {
    showToast("Пока нет слабых заданий — нужны сдачи с проверкой", "error");
    return;
  }
  board.remediating = true;
  render();
  try {
    const created = await api(`/api/classes/${encodeURIComponent(code)}/analytics/remediation`, {
      method: "POST",
      body: JSON.stringify({
        student: name,
        assignment_code: analytics.selected_assignment_code || null,
        max_tasks: Math.min(8, Math.max(3, analytics.weakest_nums.length)),
        grading_mode: "ai_assist",
      }),
    });
    state.generator.published.unshift({
      id: created.id,
      code: created.code,
      title: created.title,
      subject: created.subject || state.classroom?.subject,
      tasksCount: (created.questions || []).length,
      gradingMode: created.grading_mode,
      publishedAt: new Date().toISOString(),
      studentUrl: created.student_url || `/student?code=${created.code}`,
    });
    state.assignmentsBoard.loadedFor = null;
    showToast(rnoCreatedToast(created), "success");
    state.tab = "assignments";
    render();
    await loadAssignmentsBoard(true);
  } catch (err) {
    showToast(err.message || "Не удалось создать работу", "error");
  } finally {
    board.remediating = false;
    render();
  }
}

async function openStudentProfile(name) {
  if (!name) return;
  const board = state.studentsBoard;
  if (
    board.profileName === name &&
    board.profileAnalytics &&
    !board.profileLoading &&
    !board.profileAnalytics.error
  ) {
    return;
  }
  board.profileName = name;
  board.profileLoading = true;
  board.profileAnalytics = null;
  board.profileHistory = [];
  render();
  const code = state.classroom?.access_code;
  if (!code) {
    board.profileLoading = false;
    render();
    return;
  }
  try {
    const data = await api(
      `/api/classes/${encodeURIComponent(code)}/analytics?student=${encodeURIComponent(name)}`
    );
    if (board.profileName !== name) return;
    board.profileAnalytics = data;
    const assigns = Array.isArray(data.assignments) ? data.assignments : [];
    const key = normalizeStudentKey(name);
    const history = await Promise.all(
      assigns.slice(0, 12).map(async (a) => {
        const packKey = String(a.code || "").toUpperCase();
        if (!packKey) return null;
        let items = state.assignmentsBoard.submissions[packKey]?.items;
        if (!Array.isArray(items)) {
          try {
            const rows = await api(`/api/assignments/${encodeURIComponent(packKey)}/submissions`);
            items = Array.isArray(rows) ? rows : [];
            state.assignmentsBoard.submissions[packKey] = {
              loading: false,
              error: null,
              items,
            };
          } catch (_) {
            items = [];
          }
        }
        const sub = items.find((s) => normalizeStudentKey(s.student_name) === key) || null;
        if (!sub && a.avg_percent == null) return null;
        return { assign: a, sub };
      })
    );
    if (board.profileName !== name) return;
    board.profileHistory = history.filter(Boolean);
  } catch (err) {
    if (board.profileName === name) {
      board.profileAnalytics = { error: err.message || "Не удалось загрузить профиль" };
      board.profileHistory = [];
    }
  } finally {
    if (board.profileName === name) board.profileLoading = false;
    render();
  }
}

function openStudentReview(assignCode, subId) {
  if (!assignCode) return;
  state.tab = "assignments";
  state.assignmentsBoard.expandedCode = assignCode;
  state.assignmentsBoard.whoModalCode = null;
  state.assignmentsBoard.whoTab = "submitted";
  state.assignmentsBoard.menuOpenCode = null;
  state.assignmentsBoard.expandedSubId = subId ? Number(subId) : null;
  render();
  loadAssignmentSubmissions(assignCode, true);
  loadAnswerKey(assignCode, true).then(() => {
    if (state.tab === "assignments") render();
  });
}

function renderCodifierGrid(analytics, subject, exam) {
  const max = kimCount(exam, subject);
  const byNum = new Map((analytics?.heatmap || []).map((h) => [Number(h.num), h]));
  const weakest = new Set((analytics?.weakest_nums || []).map(Number));
  const cells = [];
  for (let n = 1; n <= max; n += 1) {
    const h = byNum.get(n);
    let cls = "is-empty";
    if (h && (h.total > 0 || h.correct_count || h.wrong_count || h.empty_count)) {
      if (weakest.has(n) || Number(h.wrong_pct || 0) >= 40) cls = "is-bad";
      else if ((h.correct_count || 0) > 0 && Number(h.wrong_pct || 0) < 40) cls = "is-ok";
      else if ((h.empty_count || 0) > 0 && !(h.correct_count || 0)) cls = "is-bad";
    }
    const title = h?.topic ? `№${n} · ${topicLabelRu(h.topic)}` : `№${n}`;
    cells.push(
      `<span class="codifier-cell ${cls}" title="${escapeHtml(title)}">${n}</span>`
    );
  }
  return `<div class="codifier-grid is-kim">${cells.join("")}</div>`;
}

function renderOgeForecast(student, subject, targetMark) {
  const th = ogeThresholds(subject);
  const current = currentPrimaryFromStudent(student, subject);
  const mark = ogeMarkFromPrimary(current, subject);
  const target = [3, 4, 5].includes(Number(targetMark)) ? Number(targetMark) : 4;
  const need = th[target];
  const fill = current == null ? 0 : Math.min(100, Math.round((current / th.max) * 100));
  const markPct = Math.round((need / th.max) * 100);
  const gap = current == null ? null : need - current;
  const targetWord = { 3: "тройку", 4: "четвёрку", 5: "пятёрку" }[target];
  const gapLine =
    current == null
      ? "После первых сдач появится прогноз по первичным баллам."
      : gap > 0
        ? `До ${targetWord} не хватает ${gap} ${gap === 1 ? "первичного балла" : "первичных баллов"}.`
        : `Проходной на ${targetWord} уже набран.`;
  const pills = [3, 4, 5]
    .map(
      (n) =>
        `<button type="button" class="oge-target-btn ${n === target ? "is-active" : ""}" data-target-mark="${n}">${n}</button>`
    )
    .join("");
  return `
    <section class="profile-widget">
      <h3>Прогноз ОГЭ</h3>
      <div class="oge-forecast">
        <div class="oge-forecast-nums">
          <div>
            <span>Текущий балл</span>
            <strong>${current != null ? `${current} / ${th.max}` : "—"}</strong>
            <em>${mark != null ? `оценка ${mark}` : "нет сдач"}</em>
          </div>
          <div>
            <span>Проходной на ${target}</span>
            <strong>${need} / ${th.max}</strong>
            <em>желаемая оценка</em>
          </div>
        </div>
        <div class="oge-track" aria-hidden="true">
          <i style="width:${fill}%"></i>
          <b style="left:${markPct}%"></b>
        </div>
        <p class="profile-block-lead">${escapeHtml(gapLine)}</p>
        <div class="oge-target">
          <span>Желаемая оценка</span>
          <div class="oge-target-pills">${pills}</div>
        </div>
      </div>
    </section>
  `;
}

function renderStudentDetailPane() {
  const board = state.studentsBoard;
  const name = board.profileName;
  const students = board.students || [];
  if (!students.length) {
    return `
      <section class="student-detail">
        <div class="student-detail-empty">
          ${emptyStudentsSvg()}
          <p>Добавьте учеников слева — профиль откроется здесь.</p>
        </div>
      </section>`;
  }
  if (!name) {
    return `<section class="student-detail"><p class="assign-sub-hint">Выберите ученика в списке.</p></section>`;
  }
  const c = state.classroom;
  const student = students.find((s) => normalizeStudentKey(s.name) === normalizeStudentKey(name));
  const subject = c?.subject || "";
  const exam = c?.exam_type || "oge";
  const analytics = board.profileAnalytics;
  const history = board.profileHistory || [];
  const historyItems = history.length
    ? history
        .map((item) => {
          const title = item.assign?.title || item.assign?.code || "Вариант";
          const date = formatAssignDate(item.assign?.created_at || item.sub?.created_at);
          const code = item.assign?.code || "";
          const subId = item.sub?.id;
          const reviewBtn = code
            ? `<button type="button" class="roster-link" data-review-assign="${escapeHtml(
                code
              )}" data-review-sub="${escapeHtml(String(subId || ""))}">Разбор</button>`
            : "";
          return `<li class="profile-history-item">
            <div>
              <strong>${escapeHtml(title)}</strong>
              <span>${escapeHtml(date)}</span>
            </div>
            <span class="profile-history-score">${historyScoreCell(item, subject)}</span>
            ${reviewBtn}
          </li>`;
        })
        .join("")
    : `<li class="profile-history-empty">Пока нет сданных вариантов</li>`;

  const body = board.profileLoading
    ? `<p class="assign-sub-hint">Загрузка профиля…</p>`
    : analytics?.error
      ? `<p class="assign-sub-hint is-error">${escapeHtml(analytics.error)}</p>`
      : `
        ${renderOgeForecast(student, subject, board.targetMark)}
        <section class="profile-widget">
          <h3>Матрица знаний (1–${kimCount(exam, subject)})</h3>
          <p class="profile-block-lead">Зелёный — освоено, красный — ошибки в истории ответов.</p>
          ${renderCodifierGrid(analytics, subject, exam)}
        </section>
        <section class="profile-widget">
          <h3>История вариантов</h3>
          <ul class="profile-history-list">${historyItems}</ul>
        </section>`;

  return `
    <section class="student-detail" aria-labelledby="student-profile-title">
      <header class="student-detail-head">
        <div class="student-detail-id">
          <span class="avatar avatar-lg">${escapeHtml(initials(student?.name || name))}</span>
          <div>
            <h2 id="student-profile-title">${escapeHtml(student?.name || name)}</h2>
            <p>${escapeHtml(formatRosterActivity(student?.last_activity_at))}</p>
          </div>
        </div>
        <button type="button" class="students-cta" id="btn-issue-remediation" ${
          board.remediating ? "disabled" : ""
        }>${board.remediating ? "Собираем…" : "🎲 Назначить работу над ошибками"}</button>
      </header>
      <div class="student-detail-body">${body}</div>
    </section>
  `;
}

function historyScoreCell(item, subject) {
  const sub = item.sub;
  const pct = item.assign?.avg_percent;
  let score = "—";
  if (sub) {
    const raw = sub.teacher_score != null ? sub.teacher_score : sub.score;
    if (raw != null) {
      score = sub.max_score != null ? `${raw} / ${sub.max_score}` : String(raw);
    } else if (pct != null) {
      score = `${Math.round(Number(pct))}%`;
    }
  } else if (pct != null) {
    score = `${Math.round(Number(pct))}%`;
  }
  const mark = ogeMarkFromPercent(pct, subject);
  return mark != null ? `${escapeHtml(score)} · ${mark}` : escapeHtml(score);
}

function normalizeStudentKey(name) {
  return String(name || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function parseRosterText(raw) {
  const seen = new Set();
  const names = [];
  String(raw || "")
    .replace(/;/g, "\n")
    .split(/\n|,/)
    .forEach((part) => {
      const name = String(part || "").trim().replace(/\s+/g, " ");
      if (!name) return;
      const key = name.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      names.push(name);
    });
  return names;
}

function mergeRosterNames(existing, added) {
  const seen = new Set();
  const out = [];
  [...(existing || []), ...(added || [])].forEach((name) => {
    const n = String(name || "").trim().replace(/\s+/g, " ");
    if (!n) return;
    const key = n.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    out.push(n);
  });
  return out;
}

function studentsCountLabel(n) {
  const abs = Math.abs(Number(n) || 0) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return `${n} учеников`;
  if (last === 1) return `${n} ученик`;
  if (last >= 2 && last <= 4) return `${n} ученика`;
  return `${n} учеников`;
}

async function loadStudentsBoard(force = false) {
  const code = state.classroom?.access_code;
  if (!code) return;
  const board = state.studentsBoard;
  if (!force && board.loadedFor === code && !board.loading) {
    maybeLoadSelectedProfile();
    return;
  }
  board.loading = true;
  board.error = null;
  board.loadedFor = code;
  render();
  try {
    const [studentsData, rosterData] = await Promise.all([
      api(`/api/classes/${encodeURIComponent(code)}/students`),
      api(`/api/classes/${encodeURIComponent(code)}/roster`),
    ]);
    board.students = Array.isArray(studentsData?.students) ? studentsData.students : [];
    board.roster = Array.isArray(rosterData?.names) ? rosterData.names : [];
    board.error = null;
    ensureStudentSelection();
  } catch (err) {
    board.error = err.message || "Не удалось загрузить учеников";
  } finally {
    board.loading = false;
    render();
    maybeLoadSelectedProfile();
  }
}

async function saveRosterNames(names) {
  const code = state.classroom?.access_code;
  if (!code) return null;
  const board = state.studentsBoard;
  board.saving = true;
  render();
  try {
    const data = await api(`/api/classes/${encodeURIComponent(code)}/roster`, {
      method: "PUT",
      body: JSON.stringify({ names }),
    });
    board.roster = Array.isArray(data?.names) ? data.names : names;
    board.inviteOpen = false;
    board.rosterDraft = "";
    showToast(`В списке: ${studentsCountLabel(board.roster.length)}`, "success");
    // обновить карточки и знаменатель прогресса в заданиях
    board.loadedFor = null;
    state.assignmentsBoard.loadedFor = null;
    await loadStudentsBoard(true);
    return data;
  } catch (err) {
    showToast(err.message || "Не удалось сохранить список", "error");
    throw err;
  } finally {
    board.saving = false;
    render();
  }
}

function exportStudentsCsv() {
  const board = state.studentsBoard;
  const rows = board.students || [];
  const header = ["ФИО", "В ростере", "Средний балл", "Средний %", "Сдач", "Слабые темы", "Последняя активность"];
  const lines = [header.join(";")];
  rows.forEach((s) => {
    const cells = [
      s.name || "",
      s.in_roster === false ? "нет" : "да",
      s.avg_score != null ? String(s.avg_score).replace(".", ",") : "",
      s.avg_percent != null ? String(s.avg_percent).replace(".", ",") : "",
      String(s.submissions_count || 0),
      (s.weak_topics || []).join(", "),
      s.last_activity_at || "",
    ].map((cell) => {
      const v = String(cell ?? "");
      if (/[;"\n]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
      return v;
    });
    lines.push(cells.join(";"));
  });
  // BOM for Excel
  const blob = new Blob(["\uFEFF" + lines.join("\r\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const a = document.createElement("a");
  const code = state.classroom?.access_code || "class";
  a.href = URL.createObjectURL(blob);
  a.download = `edusense-students-${code}.csv`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 0);
  showToast("CSV скачан", "success");
}

function renderStudentsInviteModal() {
  const board = state.studentsBoard;
  if (!board.inviteOpen) return "";
  const c = state.classroom;
  if (!c) return "";
  return `
    <div class="modal-backdrop who-backdrop" id="students-invite-backdrop">
      <div class="who-modal students-invite-modal" role="dialog" aria-modal="true" aria-labelledby="students-invite-title">
        <div class="publish-top">
          <div>
            <p class="export-kicker">Приглашение</p>
            <h2 id="students-invite-title">Добавить учеников</h2>
            <p class="publish-sub">QR и код класса · опционально список ФИО</p>
          </div>
          <button type="button" class="icon-x" id="btn-close-students-invite" aria-label="Закрыть">×</button>
        </div>
        <div class="students-invite-grid">
          <div class="students-qr-card">
            <img alt="QR код класса"
              src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(inviteUrl(c.access_code))}" />
            <button type="button" class="code-box students-code-btn" id="btn-copy-students-code-modal" title="Скопировать">
              <span class="code-value">${escapeHtml(c.access_code)}</span>
            </button>
            <p class="assign-sub-hint">Скопируйте код или дайте отсканировать QR</p>
          </div>
          <div class="students-roster-form">
            <label for="roster-names-input">Вставить ФИО списком</label>
            <textarea id="roster-names-input" rows="8" placeholder="Иванов Иван&#10;Петрова Анна&#10;Сидоров Пётр">${escapeHtml(
              board.rosterDraft || ""
            )}</textarea>
            <p class="assign-sub-hint">Каждое ФИО с новой строки. Без паролей — только список для прогресса и «Не приступили».</p>
          </div>
        </div>
        <div class="publish-foot">
          <button type="button" class="btn-ghost" id="btn-close-students-invite-foot" style="width:auto">Отмена</button>
          <button type="button" class="btn-primary" id="btn-save-roster" style="width:auto;min-width:180px" ${
            board.saving ? "disabled" : ""
          }>${board.saving ? "Сохранение…" : "Сохранить список →"}</button>
        </div>
      </div>
    </div>
  `;
}

function renderRosterCard(s, subject, selectedName) {
  const pct = studentPercent(s);
  const mark = ogeMarkFromPercent(pct, subject);
  const active = normalizeStudentKey(s.name) === normalizeStudentKey(selectedName);
  return `
    <button type="button" class="roster-card ${active ? "is-active" : ""}" data-select-student="${escapeHtml(
      s.name
    )}" ${active ? 'aria-current="true"' : ""}>
      <span class="avatar">${escapeHtml(initials(s.name))}</span>
      <span class="roster-card-name">${escapeHtml(s.name)}</span>
      <span class="roster-mark ${mark ? `is-${mark}` : "is-empty"}">${mark != null ? mark : "—"}</span>
      <span class="roster-pct ${percentToneClass(pct)}">${pct != null ? `${pct}%` : "—"}</span>
    </button>
  `;
}

function renderStudentsTab() {
  const c = state.classroom;
  const board = state.studentsBoard;
  const students = board.students || [];
  const rosterN = board.roster?.length || students.filter((s) => s.in_roster !== false).length;
  const filtered = visibleRoster();
  const subject = c?.subject || "";
  const stats = classRosterStats(students, rosterN);
  const selected = board.profileName || "";

  let listHtml;
  if (board.loading && !students.length) {
    listHtml = `<p class="assign-sub-hint">Загрузка списка…</p>`;
  } else if (board.error && !students.length) {
    listHtml = `<p class="assign-sub-hint is-error">${escapeHtml(board.error)}</p>`;
  } else if (!students.length) {
    listHtml = `<div class="empty-illus">
      ${emptyStudentsSvg()}
      <p>Добавьте ФИО или отправьте код — список появится здесь.</p>
    </div>`;
  } else if (!filtered.length) {
    listHtml = `<p class="assign-sub-hint">Никого не нашли по запросу «${escapeHtml(
      board.query || ""
    )}».</p>`;
  } else {
    listHtml = `<div class="roster-list">${filtered
      .map((s) => renderRosterCard(s, subject, selected))
      .join("")}</div>`;
  }

  return `
    <div class="students-hub">
      <section class="class-bar">
        <button type="button" class="roster-code-btn" id="btn-copy-students-code" title="Скопировать код">
          <span class="students-code-label">Код класса</span>
          <span class="roster-code-value">${escapeHtml(c?.access_code || "")}</span>
        </button>
        <div class="class-bar-stats">
          <div>
            <span>Ср. балл</span>
            <b>${stats.avg != null ? `${stats.avg}%` : "—"}</b>
          </div>
          <div>
            <span>Процент сдачи</span>
            <b>${stats.submitPct != null ? `${stats.submitPct}%` : "—"}</b>
          </div>
          <div class="class-bar-weak">
            <span>Слабое место</span>
            <b>${stats.weak ? escapeHtml(stats.weak) : "пока нет данных"}</b>
          </div>
        </div>
        <div class="students-invite-actions">
          <button type="button" class="students-cta" id="btn-open-students-invite">Пригласить</button>
          <button type="button" class="students-quiet" id="btn-export-students" ${
            students.length ? "" : "disabled"
          }>CSV</button>
        </div>
      </section>
      <div class="students-split">
        <aside class="students-master">
          <div class="roster-toolbar">
            <input type="search" id="roster-search" class="roster-search" placeholder="Поиск по ФИО"
              value="${escapeHtml(board.query || "")}" autocomplete="off" />
          </div>
          ${board.loading && students.length ? `<p class="assign-sub-hint">Обновляем…</p>` : ""}
          ${listHtml}
        </aside>
        ${renderStudentDetailPane()}
      </div>
    </div>
    ${renderStudentsInviteModal()}
  `;
}

function analyticsQueryKey(code, board) {
  return [
    code || "",
    board.mode || "class",
    board.student || "",
    board.assignmentCode || "",
  ].join("|");
}

async function loadAnalyticsBoard(force = false) {
  const code = state.classroom?.access_code;
  const board = state.analyticsBoard;
  if (!code || !board) return;
  const key = analyticsQueryKey(code, board);
  if (!force && board.loadedFor === key && board.data && !board.loading) return;
  if (board.loading && board.loadedFor === key) return;

  board.loading = true;
  board.error = null;
  render();
  try {
    const params = new URLSearchParams();
    if (board.assignmentCode) params.set("assignment_code", board.assignmentCode);
    if (board.mode === "student" && board.student) params.set("student", board.student);
    const qs = params.toString();
    const data = await api(
      `/api/classes/${encodeURIComponent(code)}/analytics${qs ? `?${qs}` : ""}`
    );
    board.data = data;
    board.loadedFor = key;
    if (!board.assignmentCode && data.selected_assignment_code) {
      board.assignmentCode = data.selected_assignment_code;
      board.loadedFor = analyticsQueryKey(code, board);
    }
    if (board.mode === "student" && !board.student && (data.students || []).length) {
      board.student = data.students[0];
      board.loadedFor = null;
      board.loading = false;
      return loadAnalyticsBoard(true);
    }
  } catch (err) {
    board.error = err.message || "Не удалось загрузить аналитику";
    board.data = null;
    board.loadedFor = key;
  } finally {
    board.loading = false;
    render();
  }
}

function analyticsHeatBarClass(pct) {
  if (pct >= 65) return "is-crit";
  if (pct >= 40) return "is-warn";
  if (pct >= 20) return "is-soft";
  return "is-ok";
}

function renderAnalyticsTrendSvg(trend) {
  const points = (trend || [])
    .filter((p) => p.avg_percent != null)
    .slice()
    .sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
      return ta - tb;
    });
  if (points.length < 2) {
    if (points.length === 1) {
      return `<p class="an-empty-inline">Пока одна точка · ${escapeHtml(
        String(points[0].avg_percent)
      )}% по «${escapeHtml(points[0].title)}». После следующей работы появится динамика.</p>`;
    }
    return `<p class="an-empty-inline">Нужны сдачи по нескольким работам, чтобы показать динамику.</p>`;
  }
  const w = 560;
  const h = 160;
  const padX = 28;
  const padY = 18;
  const vals = points.map((p) => Number(p.avg_percent));
  const minY = Math.max(0, Math.min(...vals) - 8);
  const maxY = Math.min(100, Math.max(...vals) + 8);
  const spanY = Math.max(1, maxY - minY);
  const coords = points.map((p, i) => {
    const x = padX + (i * (w - padX * 2)) / (points.length - 1);
    const y = h - padY - ((Number(p.avg_percent) - minY) / spanY) * (h - padY * 2);
    return { x, y, p };
  });
  const line = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
  const area = `${line} L${coords[coords.length - 1].x.toFixed(1)},${h - padY} L${coords[0].x.toFixed(1)},${h - padY} Z`;
  const dots = coords
    .map(
      (c) =>
        `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="4.5" class="an-trend-dot">
          <title>${escapeHtml(c.p.title)}: ${escapeHtml(String(c.p.avg_percent))}%</title>
        </circle>`
    )
    .join("");
  const labels = coords
    .map((c, i) => {
      if (points.length > 6 && i !== 0 && i !== points.length - 1 && i % 2 === 1) return "";
      const short = String(c.p.title || "").slice(0, 16);
      return `<text x="${c.x.toFixed(1)}" y="${h - 2}" text-anchor="middle" class="an-trend-label">${escapeHtml(
        short
      )}</text>`;
    })
    .join("");
  return `
    <svg class="an-trend-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Динамика среднего балла">
      <defs>
        <linearGradient id="anTrendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(94,234,212,0.35)"/>
          <stop offset="100%" stop-color="rgba(94,234,212,0)"/>
        </linearGradient>
      </defs>
      <path d="${area}" fill="url(#anTrendFill)"/>
      <path d="${line}" class="an-trend-line" fill="none"/>
      ${dots}
      ${labels}
    </svg>
  `;
}

function heatSuccessPct(h) {
  if (!h) return null;
  if (h.success_pct != null && Number.isFinite(Number(h.success_pct))) {
    return Number(h.success_pct);
  }
  const scored = (h.correct_count || 0) + (h.wrong_count || 0) + (h.empty_count || 0);
  if (!scored) return null;
  return Math.round((1000 * (h.correct_count || 0)) / scored) / 10;
}

function heatTone(pct) {
  if (pct == null || !Number.isFinite(Number(pct))) return "empty";
  if (pct > 80) return "good";
  if (pct >= 50) return "mid";
  return "bad";
}

function analyticsMatrixBlocks() {
  const subj = teacherSubjectCode();
  if (subj === "russian") {
    return [
      { id: "izl", icon: "📝", label: "Изложение", from: 1, to: 1 },
      { id: "test", icon: "✏️", label: "Тест", from: 2, to: 9 },
      { id: "text", icon: "📖", label: "Текст", from: 10, to: 12 },
      { id: "essay", icon: "✍️", label: "Сочинение", from: 13, to: 13 },
    ];
  }
  return [
    { id: "plot", icon: "🗺️", label: "Сюжет", from: 1, to: 5 },
    { id: "alg", icon: "∑", label: "Алгебра", from: 6, to: 14 },
    { id: "geo", icon: "📐", label: "Геометрия", from: 15, to: 19 },
    { id: "p2", icon: "②", label: "Часть 2", from: 20, to: 25 },
  ];
}

function analyticsHeatByNum(data) {
  return new Map((data?.heatmap || []).map((h) => [Number(h.num), h]));
}

function analyticsRedNums(data) {
  const max = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  const byNum = analyticsHeatByNum(data);
  const red = [];
  for (let n = 1; n <= max; n += 1) {
    const pct = heatSuccessPct(byNum.get(n));
    if (pct != null && pct < 50) red.push(n);
  }
  return red;
}

function analyticsFailedNums(data) {
  const max = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  const byNum = analyticsHeatByNum(data);
  const failed = [];
  for (let n = 1; n <= max; n += 1) {
    const h = byNum.get(n);
    if (!h) continue;
    const misses = (h.wrong_count || 0) + (h.empty_count || 0);
    if (misses > 0) failed.push(n);
  }
  return failed;
}

function analyticsThemeExtremes(data) {
  const items = (data?.heatmap || [])
    .map((h) => ({ h, pct: heatSuccessPct(h) }))
    .filter((x) => x.pct != null);
  if (!items.length) return { worst: null, best: null };
  const worst = items.reduce((a, b) => (b.pct < a.pct ? b : a));
  const best = items.reduce((a, b) => (b.pct > a.pct ? b : a));
  return { worst, best };
}

function formatThemeKpi(item) {
  if (!item?.h) return { title: "—", sub: "недостаточно сдач" };
  const topic = topicLabelRu(item.h.topic || "") || "подтип КИМ";
  return {
    title: `№${item.h.num}`,
    sub: `${topic} · ${item.pct}%`,
  };
}

function predictedOgeFromPercent(pct, subject) {
  if (pct == null || !Number.isFinite(Number(pct))) return null;
  const max = ogeMaxPrimary(subject);
  const primary = Math.round((Number(pct) / 100) * max);
  const mark = ogeMarkFromPrimary(primary, subject);
  return { primary, max, mark };
}

function classroomSubjectCode(classroom) {
  const raw = (classroom && (classroom.subject || classroom.subject_code)) || "";
  return teacherSubjectCode({ subject: raw, subject_code: raw });
}

function switchAnalyticsSubject(code) {
  const board = state.analyticsBoard;
  const current = teacherSubjectCode() || board.subjectFilter || "math";
  if (current === code && classroomSubjectCode(state.classroom) === code) {
    board.subjectFilter = code;
    render();
    return;
  }
  const next = (state.classrooms || []).find((c) => classroomSubjectCode(c) === code);
  if (!next) {
    showToast(
      code === "russian" ? "Нет класса по русскому языку" : "Нет класса по математике",
      "info"
    );
    return;
  }
  selectClassroom(next, { keepTab: true });
  state.analyticsBoard.subjectFilter = code;
  render();
  loadAnalyticsBoard(true);
}

function analyticsBlockStats(data) {
  const byNum = analyticsHeatByNum(data);
  return analyticsMatrixBlocks().map((block) => {
    let correct = 0;
    let scored = 0;
    for (let n = block.from; n <= block.to; n += 1) {
      const h = byNum.get(n);
      if (!h) continue;
      const s = (h.correct_count || 0) + (h.wrong_count || 0) + (h.empty_count || 0);
      correct += h.correct_count || 0;
      scored += s;
    }
    return {
      ...block,
      success_pct: scored ? Math.round((1000 * correct) / scored) / 10 : null,
    };
  });
}

function analyticsRiskList(data) {
  if (Array.isArray(data?.risk_students) && data.risk_students.length) return data.risk_students;
  const red = new Set(analyticsRedNums(data));
  const hits = new Map();
  (data?.heatmap || []).forEach((h) => {
    if (!red.has(Number(h.num))) return;
    const names = [...(h.wrong_students || []), ...(h.empty_students || [])];
    names.forEach((name) => {
      const cur = hits.get(name) || { name, nums: [] };
      if (!cur.nums.includes(h.num)) cur.nums.push(h.num);
      hits.set(name, cur);
    });
  });
  return [...hits.values()]
    .map((x) => ({ ...x, red_count: x.nums.length }))
    .filter((x) => x.red_count >= 2)
    .sort((a, b) => b.red_count - a.red_count || a.name.localeCompare(b.name, "ru"))
    .slice(0, 6);
}

function renderAnalyticsSpark(trend) {
  const pts = (trend || []).filter((p) => p.avg_percent != null);
  if (pts.length < 2) return "";
  const w = 88;
  const h = 26;
  const ys = pts.map((p) => Number(p.avg_percent));
  const min = Math.min(...ys, 0);
  const max = Math.max(...ys, 100);
  const span = Math.max(1, max - min);
  const d = pts
    .map((p, i) => {
      const x = (i * (w - 4)) / (pts.length - 1) + 2;
      const y = h - 3 - ((Number(p.avg_percent) - min) / span) * (h - 6);
      return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return `<svg class="an-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${d}" /></svg>`;
}

function renderAnalyticsMarks(data) {
  const buckets = data?.mark_distribution || [];
  const total = buckets.reduce((s, b) => s + (b.count || 0), 0);
  if (!total) {
    return `<div class="an-insight"><span class="an-insight-kicker">Оценки ОГЭ</span><p>Появятся после сдач с баллом</p></div>`;
  }
  const max = Math.max(...buckets.map((b) => b.count || 0), 1);
  const rows = [2, 3, 4, 5]
    .map((mark) => {
      const hit = buckets.find((b) => Number(b.mark) === mark) || { count: 0 };
      const w = Math.round(((hit.count || 0) / max) * 100);
      return `<div class="an-mark-row"><b>${mark}</b><i style="width:${w}%"></i><span>${hit.count || 0}</span></div>`;
    })
    .join("");
  return `<div class="an-insight"><span class="an-insight-kicker">Оценки ОГЭ</span><div class="an-marks">${rows}</div></div>`;
}

function renderAnalyticsInsights(data) {
  const blocks = analyticsBlockStats(data)
    .map((b) => {
      const pct = b.success_pct == null ? "—" : `${Math.round(b.success_pct)}%`;
      const tone = heatTone(b.success_pct);
      return `<span class="an-block-chip is-${tone}">${b.icon} ${escapeHtml(b.label)} ${escapeHtml(pct)}</span>`;
    })
    .join("");
  const risk = analyticsRiskList(data);
  const riskHtml = risk.length
    ? risk
        .map(
          (r) =>
            `<button type="button" class="an-risk-chip" data-an-student="${escapeHtml(r.name)}" title="${escapeHtml(
              (r.nums || []).map((n) => `№${n}`).join(", ")
            )}">${escapeHtml(r.name)} · ${r.red_count}</button>`
        )
        .join("")
    : `<span class="an-insight-muted">Пока нет учеников с 2+ красными номерами</span>`;
  const compare = data?.compare_assignment_title
    ? `<span class="an-insight-muted">Δ к «${escapeHtml(data.compare_assignment_title)}»</span>`
    : `<span class="an-insight-muted">Дельта появится после второй работы</span>`;
  return `
    <div class="an-strip">
      ${renderAnalyticsMarks(data)}
      <div class="an-insight">
        <span class="an-insight-kicker">Блоки КИМ</span>
        <div class="an-block-chips">${blocks}</div>
        ${compare}
      </div>
      <div class="an-insight">
        <span class="an-insight-kicker">Группа риска</span>
        <div class="an-risk-list">${riskHtml}</div>
      </div>
    </div>`;
}

function renderAnalyticsDrawer(data) {
  const which = state.analyticsBoard.drawer;
  if (!which) return "";
  const part = data?.participation || {};
  if (which === "missing") {
    const missing = part.missing_students || [];
    const submitted = part.submitted_students || [];
    return `
      <div class="an-drawer" id="an-drawer">
        <div>
          <span class="an-insight-kicker">Не сдали</span>
          <p>${
            missing.length
              ? missing.map((n) => escapeHtml(n)).join(", ")
              : "Все из списка сдали — или список учеников пуст."
          }</p>
        </div>
        <div>
          <span class="an-insight-kicker">Сдали</span>
          <p>${submitted.length ? submitted.map((n) => escapeHtml(n)).join(", ") : "Пока нет сдач"}</p>
        </div>
      </div>`;
  }
  if (which === "marks") {
    return `<div class="an-drawer" id="an-drawer">${renderAnalyticsMarks(data)}</div>`;
  }
  if (which === "risk") {
    const risk = analyticsRiskList(data);
    return `
      <div class="an-drawer" id="an-drawer">
        <div>
          <span class="an-insight-kicker">Группа риска</span>
          <p>${
            risk.length
              ? risk.map((r) => `${escapeHtml(r.name)} (${(r.nums || []).map((n) => `№${n}`).join(", ")})`).join(" · ")
              : "Никто не красный сразу в двух номерах."
          }</p>
        </div>
      </div>`;
  }
  return "";
}

function renderAnalyticsHeatmap(data, extra = {}) {
  const max = kimCount(state.classroom?.exam_type, state.classroom?.subject);
  const byNum = analyticsHeatByNum(data);
  const selected = Number(state.analyticsBoard?.selectedNum) || 0;
  const blocks = analyticsMatrixBlocks()
    .map((block) => {
      const tiles = [];
      for (let n = block.from; n <= Math.min(block.to, max); n += 1) {
        const h = byNum.get(n);
        const pct = heatSuccessPct(h);
        const tone = heatTone(pct);
        const pctLabel = pct == null ? "—" : `${pct % 1 ? pct : Math.round(pct)}%`;
        const delta = h?.delta_pct;
        const deltaHtml =
          delta == null || !Number.isFinite(Number(delta))
            ? ""
            : `<span class="an-tile-delta ${delta >= 0 ? "is-up" : "is-down"}">${
                delta > 0 ? "+" : ""
              }${Math.round(delta)}</span>`;
        tiles.push(`
          <button type="button" class="an-tile is-${tone}${selected === n ? " is-open" : ""}" data-an-num="${n}" aria-pressed="${
            selected === n ? "true" : "false"
          }">
            <span class="an-tile-top"><span class="an-tile-num">${n}</span>${deltaHtml}</span>
            <span class="an-tile-pct">${escapeHtml(pctLabel)}</span>
          </button>`);
      }
      if (!tiles.length) return "";
      const range = block.to > block.from ? `№${block.from}–${block.to}` : `№${block.from}`;
      return `
        <div class="an-mx-block">
          <div class="an-mx-tag">${block.icon} ${escapeHtml(block.label)} ${escapeHtml(range)}</div>
          <div class="an-mx-tiles">
            ${tiles.join("")}
          </div>
        </div>`;
    })
    .join("");

  const hit = selected ? byNum.get(selected) : null;

  return `
    <div class="an-mx">
      ${blocks || `<p class="an-empty-inline">Нет разобранных заданий по выбранной работе.</p>`}
    </div>
    ${renderAnalyticsBanner(selected, hit, extra)}`;
}

function renderAnalyticsBanner(num, h, extra = {}) {
  const canFix = !!extra.canFix;
  const redHint = extra.remHint || "";
  let copy = "";
  if (num) {
    const pct = heatSuccessPct(h);
    const topic = topicLabelRu(h?.topic || "") || "подтип пока не размечен";
    const wrong = h?.wrong_students || [];
    const empty = h?.empty_students || [];
    const names = [...wrong, ...empty.filter((n) => !wrong.includes(n))];
    const who = names.length
      ? names.slice(0, 6).join(", ") + (names.length > 6 ? ` и ещё ${names.length - 6}` : "")
      : "имён пока нет — нужна проверка с разбором";
    const pctLabel = pct == null ? "нет данных" : `${pct}%`;
    const typical = h?.typical_wrong
      ? `Частый ответ: «${h.typical_wrong}»${h.typical_wrong_count > 1 ? ` ×${h.typical_wrong_count}` : ""}. `
      : "";
    const delta =
      h?.delta_pct != null && Number.isFinite(Number(h.delta_pct))
        ? `Δ ${h.delta_pct > 0 ? "+" : ""}${h.delta_pct} п.п. к прошлой работе. `
        : "";
    copy = `
      <div class="an-banner-kicker">Разбор номера</div>
      <h3>№${escapeHtml(String(num))} · ${escapeHtml(topic)} · ${escapeHtml(pctLabel)}</h3>
      <p>${escapeHtml(typical + delta + who)}</p>`;
  } else {
    copy = `
      <div class="an-banner-kicker">Работа над ошибками</div>
      <h3>Красные подтипы класса</h3>
      <p>${escapeHtml(redHint)}</p>`;
  }
  const oneBtn = num
    ? `<button type="button" class="an-ghost-btn" id="btn-an-one-slot" data-an-one-slot="${num}">Только №${escapeHtml(
        String(num)
      )}</button>`
    : "";
  return `
    <div class="an-banner${num ? ` is-${heatTone(heatSuccessPct(h))}` : ""}" id="an-tile-card">
      <div class="an-banner-copy">${copy}</div>
      <div class="an-banner-actions">
        ${oneBtn}
        <button type="button" class="an-shimmer" id="btn-an-remediation" ${
          canFix && !state.generator.generating && !state.analyticsBoard?.creatingRno ? "" : "disabled"
        }>
          ${
            state.analyticsBoard?.creatingRno
              ? "Собираем работу над ошибками…"
              : "🎲 Сформировать работу над ошибками"
          }
        </button>
      </div>
    </div>`;
}

function buildParentMeetingReportHtml(classroom, data) {
  const c = classroom || {};
  const d = data || {};
  const part = d.participation || {};
  const heat = (d.heatmap || [])
    .slice()
    .sort((a, b) => b.wrong_pct - a.wrong_pct)
    .slice(0, 8);
  const flags = d.flags || [];
  const trend = d.trend || [];
  const avg = d.class_avg_percent != null ? `${d.class_avg_percent}%` : "—";
  const gradeAvg = classGradeAverages(d);
  const who =
    d.mode === "student" && d.student
      ? `Ученик: ${escapeHtml(d.student)}`
      : "Класс в целом";
  const heatRows = heat
    .map(
      (h) => `<tr>
      <td>№${escapeHtml(String(h.num))}</td>
      <td>${escapeHtml(h.topic || "—")}</td>
      <td><strong>${escapeHtml(String(h.wrong_pct))}%</strong></td>
      <td>${escapeHtml(String(h.wrong_count + h.empty_count))}/${escapeHtml(String(h.correct_count + h.wrong_count + h.empty_count))}</td>
    </tr>`
    )
    .join("");
  const trendRows = trend
    .map(
      (t) => `<tr>
      <td>${escapeHtml(t.title)}</td>
      <td>${escapeHtml(t.avg_percent != null ? `${t.avg_percent}%` : "—")}</td>
      <td>${escapeHtml(String(t.submissions_count || 0))}</td>
    </tr>`
    )
    .join("");
  const flagLis = flags.map((f) => `<li>${escapeHtml(f)}</li>`).join("") || "<li>Явных красных флагов нет</li>";
  const when = new Date().toLocaleString("ru-RU");
  const gradeRowsHtml = (d.grade_rows || [])
    .map((r, i) => {
      const status = r.threshold_status || parentThresholdStatus(r);
      const statusClass = /⚠️|завал|не хватило|не сдал/i.test(status) ? "is-warn" : /✓/.test(status) ? "is-ok" : "";
      const total =
        r.submitted && r.primary != null ? `${r.primary} / ${r.max_primary || "—"}` : "—";
      const p1 = r.submitted && r.part1_score != null ? String(r.part1_score) : "—";
      const p2 = r.submitted && r.part2_score != null ? String(r.part2_score) : "—";
      return `<tr>
      <td class="n">${i + 1}</td>
      <td>${escapeHtml(r.name)}</td>
      <td>${escapeHtml(p1)}</td>
      <td>${escapeHtml(p2)}</td>
      <td>${escapeHtml(total)}</td>
      <td>${escapeHtml(r.grade || "—")}</td>
      <td class="${statusClass}">${escapeHtml(status)}</td>
    </tr>`;
    })
    .join("");
  const subjectLabel = /русск/i.test(String(d.subject || c.subject || ""))
    ? "Русский язык"
    : "Математика";
  const avgPrimaryLabel =
    gradeAvg.avgPrimary != null ? `${formatRuNum(gradeAvg.avgPrimary, 1)} / ${gradeAvg.max}` : "—";
  const avgGradeLabel = gradeAvg.avgGrade != null ? formatRuNum(gradeAvg.avgGrade, 1) : "—";
  return `<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/>
<title>Ведомость класса · ${escapeHtml(classTitle(c))}</title>
<style>
  :root { --bg:#0b0f17; --card:#121a27; --text:#f2f5f9; --muted:#93a0b5; --accent:#5eead4; --warn:#e8a87c; --line:rgba(255,255,255,.1); }
  * { box-sizing:border-box; }
  body { margin:0; font-family:"Plus Jakarta Sans",system-ui,sans-serif; background:var(--bg); color:var(--text); }
  .sheet { position:relative; overflow:hidden; max-width:920px; margin:28px auto; padding:32px; background:linear-gradient(180deg,rgba(18,26,39,.98),rgba(11,15,23,.98)); border:1px solid var(--line); border-radius:18px; }
  ${eduSensePrintWatermarkCss().replace(/#0f172a/g, "#e2e8f0")}
  .print-inner { position:relative; z-index:1; }
  .brand { color:var(--accent); font-weight:700; letter-spacing:.04em; text-transform:uppercase; font-size:.78rem; }
  h1 { font-size:1.65rem; margin:10px 0 6px; }
  .muted { color:var(--muted); }
  .kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:22px 0; }
  .kpi { padding:14px 16px; border-radius:14px; background:rgba(255,255,255,.03); border:1px solid var(--line); }
  .kpi b { display:block; font-size:1.45rem; margin-top:4px; }
  h2 { font-size:1.05rem; margin:26px 0 10px; }
  table { width:100%; border-collapse:collapse; font-size:.92rem; }
  th,td { text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; }
  td.n { text-align:center; width:36px; color:var(--muted); }
  .is-warn { color:var(--warn); font-weight:700; }
  .is-ok { color:var(--accent); }
  ul { margin:0; padding-left:18px; }
  li { margin:6px 0; }
  .foot { margin-top:28px; font-size:.8rem; color:var(--muted); }
  .details { page-break-before: always; }
  @media print {
    @page { size: A4 portrait; margin: 10mm 8mm; }
    body { background:#fff !important; color:#111 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    .sheet { border:none; box-shadow:none; margin:0; max-width:none; padding:0; background:#fff; border-radius:0; }
    .brand, .muted, th { color:#555 !important; }
    .kpi { border-color:#ddd; background:#f7f7f7; }
    th,td { border-color:#d4d4d4; }
    .vedomost { page-break-after: always; }
    .vedomost h2 { font-size:14pt; margin:0 0 8px; }
    .vedomost table { font-size:10pt; }
    .vedomost th, .vedomost td { padding:5px 6px; border:1px solid #ccc; }
    .vedomost th { background:#f3f4f6 !important; color:#111 !important; text-transform:none; letter-spacing:0; font-size:8.5pt; }
    .vedomost td.n { width:28px; }
    .is-warn { color:#9a3412 !important; }
    .is-ok { color:#166534 !important; }
    .no-print { display:none !important; }
    .ep-wm-layer { opacity:0.06; color:#0f172a !important; }
  }
</style></head><body>
  <div class="sheet">
    ${eduSenseWatermarkHtml()}
    <div class="print-inner">
    <div class="brand">EduSense · Отчёт для родительского собрания</div>
    <h1>${escapeHtml(classTitle(c))}</h1>
    <p class="muted">${escapeHtml(subjectLabel)} · ${examLabel(c.exam_type)} · ${who}<br/>Работа: ${escapeHtml(
      d.selected_assignment_title || "—"
    )} · сформировано ${escapeHtml(when)}</p>
    <div class="kpis">
      <div class="kpi"><span class="muted">Средний первичный</span><b>${escapeHtml(avgPrimaryLabel)}</b></div>
      <div class="kpi"><span class="muted">Средняя оценка ОГЭ</span><b>${escapeHtml(avgGradeLabel)}</b></div>
      <div class="kpi"><span class="muted">Сдали</span><b>${escapeHtml(
        String(part.submitters_count || 0)
      )}${part.roster_count ? ` / ${escapeHtml(String(part.roster_count))}` : ""}</b></div>
    </div>
    <section class="vedomost" id="vedomost">
      <h2>Ведомость класса</h2>
      <table>
        <thead>
          <tr>
            <th class="n">№</th>
            <th>ФИО Ученика</th>
            <th>Баллы (1 часть)</th>
            <th>Баллы (2 часть)</th>
            <th>Итоговый балл</th>
            <th>Оценка ОГЭ</th>
            <th>Статус порогов (Геометрия/Грамотность)</th>
          </tr>
        </thead>
        <tbody>${gradeRowsHtml || `<tr><td colspan="7">Нет сдач</td></tr>`}</tbody>
      </table>
    </section>
    <div class="details">
    <h2>Слабые задания</h2>
    <p class="muted">Средний результат: ${escapeHtml(avg)}</p>
    <ul>${flagLis}</ul>
    <h2>Детализация по номерам</h2>
    <table><thead><tr><th>№</th><th>Тема</th><th>% ошибок</th><th>Ошибки / ответов</th></tr></thead>
    <tbody>${heatRows || `<tr><td colspan="4">Нет данных</td></tr>`}</tbody></table>
    <h2>Динамика по работам</h2>
    <table><thead><tr><th>Работа</th><th>Средний %</th><th>Сдач</th></tr></thead>
    <tbody>${trendRows || `<tr><td colspan="3">Пока нет работ</td></tr>`}</tbody></table>
    <p class="foot">EduSense · материал для обсуждения с родителями. Рекомендуется работа над ошибками по слабым номерам.</p>
    </div>
    </div>
  </div>
  <script>window.onload=()=>{setTimeout(()=>window.print(),250);};<\/script>
</body></html>`;
}

function openParentMeetingReport() {
  const data = state.analyticsBoard?.data;
  if (!data) {
    showToast("Сначала загрузите аналитику", "error");
    return;
  }
  const html = buildParentMeetingReportHtml(state.classroom, data);
  try {
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const win = window.open(url, "_blank", "width=920,height=1100");
    if (win) {
      try {
        win.opener = null;
      } catch (_) {}
      setTimeout(() => URL.revokeObjectURL(url), 120000);
      showToast("Отчёт открыт · можно печатать", "success");
      return;
    }
    URL.revokeObjectURL(url);
  } catch (_) {}
  if (printViaHiddenFrame(html)) {
    showToast("Отчёт открыт · можно печатать", "success");
    return;
  }
  showToast("Разрешите всплывающие окна для отчёта", "error");
}

async function createRemediationWork() {
  const code = state.classroom?.access_code;
  const board = state.analyticsBoard;
  if (!code || !board?.data) {
    showToast("Сначала загрузите аналитику", "error");
    return;
  }
  if (betaLimitReached()) {
    showToast(
      `В открытой бете на класс можно выдать ${BETA_VARIANT_LIMIT} вариантов. Сейчас выдано ${issuedVariantCount()}.`,
      "error"
    );
    return;
  }
  if (!board.data.remediation_ready) {
    showToast(board.data.remediation_hint || "Работа над ошибками пока недоступна", "error");
    return;
  }
  if (!board.data.weakest_nums?.length) {
    showToast("Нет слабых заданий для работы над ошибками", "error");
    return;
  }
  board.creatingRemediation = true;
  render();
  try {
    const body = {
      assignment_code: board.assignmentCode || board.data.selected_assignment_code || null,
      max_tasks: Math.min(8, Math.max(3, board.data.weakest_nums.length)),
      grading_mode: "ai_assist",
    };
    if (board.mode === "student" && board.student) body.student = board.student;
    const created = await api(`/api/classes/${encodeURIComponent(code)}/analytics/remediation`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    state.generator.published.unshift({
      id: created.id,
      code: created.code,
      title: created.title,
      subject: created.subject || state.classroom?.subject,
      tasksCount: (created.questions || []).length,
      gradingMode: created.grading_mode,
      publishedAt: new Date().toISOString(),
      studentUrl: created.student_url || `/student?code=${created.code}`,
    });
    state.assignmentsBoard.loadedFor = null;
    showToast(rnoCreatedToast(created), "success");
    state.tab = "assignments";
    render();
    await loadAssignmentsBoard(true);
  } catch (err) {
    showToast(err.message || "Не удалось создать работу", "error");
    board.creatingRemediation = false;
    render();
  } finally {
    board.creatingRemediation = false;
  }
}

function sendSlotsToGenerator(slots) {
  const nums = (slots || []).filter((n) => Number(n) > 0).map(Number);
  if (!nums.length) {
    showToast("Нет номеров для генератора", "info");
    return;
  }
  state.generator.variant = null;
  state.generator.selectedTaskId = null;
  state.generator._slots = nums;
  state.generator._quickCount = nums.length;
  state.tab = "tests";
  startKimGenerate();
}

function sendRedSlotsToGenerator() {
  const red = analyticsRedNums(state.analyticsBoard?.data);
  if (!red.length) {
    showToast("Красных номеров нет — проблемных подтипов у класса не видно", "info");
    return;
  }
  sendSlotsToGenerator(red);
}

async function generateRNO() {
  const code = state.classroom?.access_code;
  const board = state.analyticsBoard;
  const data = board?.data;
  if (!code || !data) {
    showToast("Сначала загрузите аналитику", "error");
    return;
  }
  const failed = analyticsFailedNums(data);
  if (!failed.length) {
    showToast("Нет заданий с баллом ниже максимума", "info");
    return;
  }
  board.creatingRno = true;
  render();
  try {
    const body = {
      assignment_code: board.assignmentCode || data.selected_assignment_code || null,
      max_tasks: 25,
    };
    if (board.mode === "student" && (board.student || data.student)) {
      body.student = board.student || data.student;
    }
    const preview = await api(`/api/classes/${encodeURIComponent(code)}/analytics/rno`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    const questions = preview.questions || [];
    if (!questions.length) {
      showToast("Не удалось собрать задания РНО", "error");
      return;
    }
    state.generator.examUi = preview.exam_ui || "";
    const variant = questionsToVariant(questions, preview);
    variant.title = preview.title || `Работа над ошибками: ${data.selected_assignment_title || "тест"}`;
    variant.rno = true;
    state.generator.variant = variant;
    state.generator.selectedTaskId = null;
    state.generator._slots = preview.failed_nums || failed;
    const nums = (preview.failed_nums || failed).map((n) => `№${n}`).join(", ");
    state.generator.lastSourceNote = `Работа над ошибками · ${nums}`;
    state.tab = "tests";
    showToast(
      `Собрана работа над ошибками · ${questions.length} заданий (только ошибки и пропуски)`,
      "success"
    );
  } catch (err) {
    showToast(err.message || "Не удалось создать работу над ошибками", "error");
  } finally {
    board.creatingRno = false;
    render();
  }
}

function formatRuNum(n, digits = 1) {
  if (n == null || !Number.isFinite(Number(n))) return "—";
  return Number(n).toLocaleString("ru-RU", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function classGradeAverages(data) {
  const subject = data?.subject || state.classroom?.subject;
  const max = ogeMaxPrimary(subject);
  if (data?.class_avg_primary != null && Number.isFinite(Number(data.class_avg_primary))) {
    const avgGrade =
      data.class_avg_grade != null && Number.isFinite(Number(data.class_avg_grade))
        ? Number(data.class_avg_grade)
        : null;
    const n = (data.grade_rows || []).filter((r) => r.submitted).length;
    return {
      avgPrimary: Number(data.class_avg_primary),
      avgGrade,
      max: (data.grade_rows && data.grade_rows[0] && data.grade_rows[0].max_primary) || max,
      n,
    };
  }
  const rows = (data?.grade_rows || []).filter((r) => r.submitted && r.primary != null);
  if (!rows.length) {
    const forecast = predictedOgeFromPercent(data?.class_avg_percent, subject);
    return {
      avgPrimary: forecast ? forecast.primary : null,
      avgGrade: forecast ? forecast.mark : null,
      max,
      n: 0,
    };
  }
  const avgPrimary = rows.reduce((s, r) => s + Number(r.primary), 0) / rows.length;
  const grades = rows.map((r) => Number(r.grade)).filter((g) => Number.isFinite(g) && g > 0);
  const avgGrade = grades.length ? grades.reduce((a, b) => a + b, 0) / grades.length : null;
  return { avgPrimary, avgGrade, max: rows[0].max_primary || max, n: rows.length };
}

function antiThemesTop3(data) {
  return (data?.heatmap || [])
    .filter((h) => heatSuccessPct(h) != null)
    .slice()
    .sort((a, b) => heatSuccessPct(a) - heatSuccessPct(b))
    .slice(0, 3);
}

function parentThresholdStatus(row) {
  if (!row || !row.submitted) return "не сдал";
  if (row.failed_geometry) return "⚠️ Геометрия";
  if (row.failed_literacy) return "⚠️ Грамотность";
  if (row.geometry_tag) return String(row.geometry_tag);
  if (row.literacy_tag) return String(row.literacy_tag);
  return "норма";
}

function buildParentChatText(classroom, data) {
  const d = data || {};
  const c = classroom || {};
  const avg = classGradeAverages(d);
  const anti = antiThemesTop3(d);
  const part = d.participation || {};
  const subjectLabel = /русск/i.test(String(d.subject || c.subject || ""))
    ? "Русский язык"
    : "Математика";
  const lines = [
    `📌 Сводка по классу · ${classTitle(c)}`,
    `Предмет: ${subjectLabel} · ${examLabel(c.exam_type)}`,
    `Работа: ${d.selected_assignment_title || "—"}`,
    "",
    `Средний первичный балл: ${
      avg.avgPrimary != null ? `${formatRuNum(avg.avgPrimary, 1)} / ${avg.max}` : "—"
    }`,
    `Средняя оценка ОГЭ: ${avg.avgGrade != null ? formatRuNum(avg.avgGrade, 1) : "—"}`,
    `Сдали: ${part.submitters_count || 0}${part.roster_count ? ` из ${part.roster_count}` : ""}`,
    "",
    "🔻 Анти-темы (топ-3):",
  ];
  if (!anti.length) {
    lines.push("пока недостаточно данных по номерам");
  } else {
    anti.forEach((h, i) => {
      const topic = topicLabelRu(h.topic || "") || "подтип КИМ";
      lines.push(`${i + 1}. №${h.num} · ${topic} — ${heatSuccessPct(h)}%`);
    });
  }
  lines.push("");
  lines.push("Рекомендуем работу над ошибками по этим номерам.");
  return lines.join("\n");
}

async function copyTextToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (_) {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    } catch (e) {
      return false;
    }
  }
}

async function copyParentChatSummary() {
  const data = state.analyticsBoard?.data;
  if (!data) {
    showToast("Сначала загрузите аналитику", "error");
    return;
  }
  const text = buildParentChatText(state.classroom, data);
  const ok = await copyTextToClipboard(text);
  if (ok) showToast("Текст для родительского чата скопирован", "success");
  else showToast("Не удалось скопировать текст", "error");
}

function bindAnalyticsControls() {
  const board = state.analyticsBoard;
  document.getElementById("an-mode")?.addEventListener("change", (e) => {
    board.mode = e.target.value === "student" ? "student" : "class";
    if (board.mode === "class") board.student = "";
    board.selectedNum = null;
    board.loadedFor = null;
    loadAnalyticsBoard(true);
  });
  document.getElementById("an-student")?.addEventListener("change", (e) => {
    board.student = e.target.value || "";
    board.selectedNum = null;
    board.loadedFor = null;
    loadAnalyticsBoard(true);
  });
  document.getElementById("an-assignment")?.addEventListener("change", (e) => {
    board.assignmentCode = e.target.value || "";
    board.selectedNum = null;
    board.loadedFor = null;
    loadAnalyticsBoard(true);
  });
  document.getElementById("btn-an-refresh")?.addEventListener("click", () => {
    board.loadedFor = null;
    loadAnalyticsBoard(true);
  });
  document.getElementById("btn-an-remediation")?.addEventListener("click", () => {
    generateRNO();
  });
  document.getElementById("btn-an-one-slot")?.addEventListener("click", () => {
    const num = Number(document.getElementById("btn-an-one-slot")?.getAttribute("data-an-one-slot"));
    if (num) sendSlotsToGenerator([num]);
  });
  document.getElementById("btn-an-report")?.addEventListener("click", () => {
    openParentMeetingReport();
  });
  document.getElementById("btn-an-parent-chat")?.addEventListener("click", () => {
    copyParentChatSummary();
  });
  document.querySelectorAll("[data-an-subject]").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchAnalyticsSubject(btn.getAttribute("data-an-subject") || "math");
    });
  });
  document.querySelectorAll("[data-an-drawer]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-an-drawer") || "";
      board.drawer = board.drawer === id ? null : id;
      render();
    });
  });
  document.querySelectorAll("[data-an-student]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.getAttribute("data-an-student") || "";
      if (!name) return;
      board.mode = "student";
      board.student = name;
      board.drawer = null;
      board.loadedFor = null;
      loadAnalyticsBoard(true);
    });
  });
  document.getElementById("btn-an-to-assign")?.addEventListener("click", () => {
    state.tab = "assignments";
    render();
    loadAssignmentsBoard();
  });
  document.querySelectorAll("[data-an-num]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const num = Number(btn.getAttribute("data-an-num"));
      board.selectedNum = board.selectedNum === num ? null : num;
      render();
      document.getElementById("an-tile-card")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });
}


function analyticsRiskGroup(data) {
  const rows = Array.isArray(data?.matrix?.students) ? data.matrix.students : [];
  // Fallback: students with low avg from participation/heatmap not enough — use board students grades
  const boardStudents = state.studentsBoard?.students || [];
  const risk = [];
  boardStudents.forEach((s) => {
    const mark = ogeMarkFromPercent(studentPercent(s), state.classroom?.subject);
    if (mark != null && mark <= 2) risk.push({ name: s.name, reason: "низкая успеваемость" });
  });
  // Also scan recent submissions grades if available
  const items = mergeAssignmentLists(state.assignmentsBoard.items, state.generator.published).slice(0, 5);
  const fails = new Map();
  items.forEach((a) => {
    const box = state.assignmentsBoard.submissions[String(a.code).toUpperCase()];
    (box?.items || []).forEach((sub) => {
      const sc = sub.score != null ? Number(sub.score) : null;
      const mark = ogeMarkFromPrimary(sc, a.subject || state.classroom?.subject);
      if (mark === 2) {
        const key = normalizeStudentKey(sub.student_name);
        fails.set(key, (fails.get(key) || 0) + 1);
      }
    });
  });
  fails.forEach((n, key) => {
    if (n >= 3) {
      const display =
        (state.studentsBoard?.students || []).find((s) => normalizeStudentKey(s.name) === key)?.name || key;
      if (!risk.some((r) => normalizeStudentKey(r.name) === key)) {
        risk.push({ name: display, reason: "три оценки «2» подряд" });
      }
    }
  });
  return risk.slice(0, 12);
}

function renderRiskGroupHtml(data) {
  const risk = analyticsRiskGroup(data);
  if (!risk.length) {
    return `<section class="glass an-card"><h3>Группа риска</h3><p class="muted">Учеников с тремя двойками подряд пока нет.</p></section>`;
  }
  return `<section class="glass an-card an-risk">
    <h3>Группа риска</h3>
    <p class="muted">Автоподсветка учеников с устойчиво низкой успеваемостью.</p>
    <ul class="an-risk-list">${risk
      .map((r) => `<li><strong>${escapeHtml(r.name)}</strong><span>${escapeHtml(r.reason)}</span></li>`)
      .join("")}</ul>
  </section>`;
}

function renderAnalytics() {
  const c = state.classroom;
  const board = state.analyticsBoard;
  const data = board.data;
  const students = data?.students || [];
  const assignments = data?.assignments || [];
  const part = data?.participation || {};

  const modeSelect = `
    <select id="an-mode" class="an-select" aria-label="Режим анализа">
      <option value="class" ${board.mode === "class" ? "selected" : ""}>Анализ по классу</option>
      <option value="student" ${board.mode === "student" ? "selected" : ""}>По ученику</option>
    </select>`;

  const studentSelect =
    board.mode === "student"
      ? `<select id="an-student" class="an-select" aria-label="Ученик">
          ${
            students.length
              ? students
                  .map(
                    (n) =>
                      `<option value="${escapeHtml(n)}" ${
                        board.student === n ? "selected" : ""
                      }>${escapeHtml(n)}</option>`
                  )
                  .join("")
              : `<option value="">Нет сдавших</option>`
          }
        </select>`
      : "";

  const assignSelect = `
    <select id="an-assignment" class="an-select" aria-label="Работа">
      ${
        assignments.length
          ? assignments
              .map((a) => {
                const sel =
                  (board.assignmentCode || data?.selected_assignment_code || "") === a.code
                    ? "selected"
                    : "";
                return `<option value="${escapeHtml(a.code)}" ${sel}>${escapeHtml(
                  a.title
                )} · ${escapeHtml(a.code)}</option>`;
              })
              .join("")
          : `<option value="">Нет работ</option>`
      }
    </select>`;

  let body = "";
  if (board.loading && !data) {
    body = `<p class="assign-sub-hint">Считаем статистику…</p>`;
  } else if (board.error && !data) {
    body = `<p class="assign-sub-hint is-error">${escapeHtml(board.error)}</p>`;
  } else if (!assignments.length) {
    body = `
      <div class="an-empty">
        <h3>Пока недостаточно данных для аналитики</h3>
        <p>Выдайте работу в «Заданиях» и дождитесь первых сдач — здесь появятся матрица успеваемости и группа риска.</p>
        <button type="button" class="btn-primary" id="btn-an-to-assign" style="width:auto;margin-top:12px">К заданиям</button>
      </div>`;
  } else {
    const avg =
      data?.class_avg_percent != null ? `${data.class_avg_percent}%` : "—";
    const forecast = predictedOgeFromPercent(data?.class_avg_percent, c?.subject);
    const forecastLine = forecast
      ? `прогноз ОГЭ · ${forecast.primary} из ${forecast.max} · оценка ${forecast.mark}`
      : "прогноз появится после сдач";
    const partPct =
      part.participation_pct != null ? `${part.participation_pct}%` : "—";
    const partSub = `${part.submitters_count || 0}${
      part.roster_count ? ` из ${part.roster_count}` : ""
    } сдали`;
    const { worst, best } = analyticsThemeExtremes(data);
    const anti = formatThemeKpi(worst);
    const top = formatThemeKpi(best);
    const failed = analyticsFailedNums(data);
    const canFix = failed.length > 0;
    const remHint = canFix
      ? `В работу над ошибками войдут номера: ${failed.map((n) => `№${n}`).join(", ")}.`
      : "Нет номеров с баллом ниже максимума — кнопка ждёт ошибки после проверки.";

    const spark = renderAnalyticsSpark(data?.trend);
    const dur =
      data?.time?.avg_duration_seconds != null
        ? ` · ${formatDurationSeconds(data.time.avg_duration_seconds)}`
        : "";
    const drawer = board.drawer;

    body = `
      <div class="an-kpis grid grid-cols-1 lg:grid-cols-4 gap-4">
        <article class="an-kpi is-click" data-an-drawer="marks">
          <span class="an-kpi-label">Средний %</span>
          <div class="an-kpi-row"><strong>${escapeHtml(avg)}</strong>${spark}</div>
          <em>${escapeHtml(forecastLine)}</em>
        </article>
        <article class="an-kpi is-click${drawer === "missing" ? " is-open" : ""}" data-an-drawer="missing">
          <span class="an-kpi-label">Процент сдачи</span>
          <strong>${escapeHtml(partPct)}</strong>
          <em>${escapeHtml(partSub)}${escapeHtml(dur)}</em>
        </article>
        <article class="an-kpi is-anti">
          <span class="an-kpi-label">Анти-тема</span>
          <strong>${escapeHtml(anti.title)}</strong>
          <em>${escapeHtml(anti.sub)}</em>
        </article>
        <article class="an-kpi is-best">
          <span class="an-kpi-label">Лучшая тема</span>
          <strong>${escapeHtml(top.title)}</strong>
          <em>${escapeHtml(top.sub)}</em>
        </article>
      </div>
      ${renderAnalyticsInsights(data)}
      ${renderAnalyticsDrawer(data)}

      <section class="an-panel an-matrix-panel">
        ${board.loading ? `<p class="assign-sub-hint">Обновляем…</p>` : ""}
        ${renderAnalyticsHeatmap(data, { canFix, remHint })}
        ${renderRiskGroupHtml(data)}
      </section>
    `;
  }

  const subj = board.subjectFilter || teacherSubjectCode() || classroomSubjectCode(c) || "math";
  const subjectSwitch = `
        <div class="an-subject-switch" role="group" aria-label="Предмет отчёта">
          <button type="button" class="an-subject-btn ${subj === "math" ? "is-active" : ""}" data-an-subject="math">📐 Математика</button>
          <button type="button" class="an-subject-btn ${subj === "russian" ? "is-active" : ""}" data-an-subject="russian">📝 Русский язык</button>
        </div>`;

  return `
    <div class="an-hub">
      <section class="an-toolbar" data-tour="parents">
        <span class="an-toolbar-kicker">Аналитика</span>
        <strong class="an-toolbar-class">${escapeHtml(classTitle(c))}</strong>
        ${subjectSwitch}
        ${modeSelect}
        ${studentSelect}
        ${assignSelect}
        <button type="button" class="an-toolbar-refresh an-toolbar-report" id="btn-an-report">📄 Сформировать отчёт для родителей (PDF/Печать)</button>
        <button type="button" class="an-toolbar-refresh an-toolbar-report" id="btn-an-parent-chat">💬 Скопировать для родительского чата</button>
        <button type="button" class="an-toolbar-refresh" id="btn-an-refresh">Обновить</button>
      </section>
      ${body}
    </div>
  `;
}

function renderTab() {
  switch (state.tab) {
    case "home":
      return renderHome();
    case "live":
      return renderLiveTab();
    case "students":
      return renderStudentsTab();
    case "assignments":
      return renderAssignments();
    case "tests":
      return renderTests();
    case "analytics":
      return renderAnalytics();
    case "settings":
      return `
        <div class="bento">
          <section class="glass shell-screen reveal">
            <div class="kicker">Профиль и класс</div>
            <h2>Настройки</h2>
            <p class="shell-lead">${escapeHtml(classTitle(state.classroom))}</p>
            <div class="spec-pills" style="margin:14px 0 18px">
              <span class="spec-pill">${examLabel(state.classroom.exam_type)}</span>
              <span class="spec-pill">Класс ${escapeHtml(gradeDisplay(state.classroom))}</span>
              <span class="spec-pill">${escapeHtml(state.classroom.subject)}</span>
              <span class="spec-pill">Код: ${escapeHtml(state.classroom.access_code)}</span>
            </div>
            <p class="shell-note">Управляйте личными данными, паролем, уведомлениями и подпиской PRO на отдельной странице.</p>
            <div class="actions" style="margin-top:18px">
              <a class="btn-primary" href="/settings" style="width:auto;min-width:220px;display:inline-flex;align-items:center;justify-content:center;text-decoration:none">Открыть настройки профиля</a>
              <button type="button" class="btn-secondary js-new-class" style="width:auto;min-width:180px">Создать класс</button>
              <button type="button" class="btn-ghost" data-quick="home" style="width:auto">На главную</button>
            </div>
          </section>
        </div>`;
    default:
      return "";
  }
}

function navBadgeHtml(badge) {
  if (!badge) return "";
  const kind = String(badge.kind || "");
  if (kind === "bonus") return "";
  if (kind === "live") {
    return `<span class="nav-badge nav-badge-live" aria-hidden="true"><i class="nav-live-dot"></i></span>`;
  }
  return `<span class="nav-badge nav-badge-${escapeHtml(kind)}">${escapeHtml(badge.text)}</span>`;
}

const REF_NOTIFY_KEY = "edusense_ref_notify";

function refNotifyRequested() {
  try {
    return localStorage.getItem(REF_NOTIFY_KEY) === "1";
  } catch (_) {
    return false;
  }
}

function referralPreviewLink() {
  const seed = state.user?.id || state.classroom?.access_code || "";
  const code = String(seed).replace(/[^a-zA-Z0-9]/g, "").slice(-6).toUpperCase() || "XXXXXX";
  const origin = String(location.origin || "https://edusense.app").replace(/\/$/, "");
  return `${origin}/r/${code}`;
}

function renderInviteModal() {
  if (!state.showInvite) return "";
  const notified = refNotifyRequested();
  return `
    <div class="modal-backdrop invite-backdrop" id="invite-backdrop">
      <div class="modal-card invite-card" role="dialog" aria-modal="true" aria-labelledby="invite-title">
        <span class="invite-glow" aria-hidden="true"></span>
        <div class="invite-inner">
          <h3 class="invite-title" id="invite-title">🎁 Приглашайте друзей и коллег в EduSense</h3>
          <span class="invite-status">⏳ Технология в разработке · Скоро доступно</span>

          <ul class="invite-perks">
            <li class="is-you">
              <b>Если вы учитель</b>
              <span>Приглашайте коллег из своей школы и получайте бесконечный PRO-доступ за каждого активного учителя.</span>
            </li>
            <li>
              <b>Если вы ученик</b>
              <span>Зовите одноклассников, соревнуйтесь в Live-уроках и открывайте новые тренажёры.</span>
            </li>
          </ul>

          <label class="invite-link-label" for="invite-link">Ваша реферальная ссылка</label>
          <div class="invite-link-row">
            <input id="invite-link" class="invite-link" type="text"
              value="${escapeHtml(referralPreviewLink())}"
              readonly disabled aria-describedby="invite-note" />
            <button type="button" class="invite-notify" id="btn-invite-notify" ${notified ? "disabled" : ""}>
              ${notified ? "✓ Сообщим на старте" : "Уведомить о запуске"}
            </button>
          </div>
          <p class="invite-note" id="invite-note">
            ${
              notified
                ? "Вы в списке ожидания — пришлём письмо в день запуска программы."
                : "Ссылка станет активной после релиза реферальной программы."
            }
          </p>

          <button type="button" class="btn-ghost invite-close" id="btn-close-invite">Закрыть</button>
        </div>
      </div>
    </div>
  `;
}

function renderDashboard() {
  const c = state.classroom;
  const u = state.user;
  const inLiveRoom = state.tab === "live" && state.liveInRoom;
  const inLiveHub = state.tab === "live" && !state.liveInRoom;
  const hideMainHead = inLiveRoom || inLiveHub;
  const titles = {
    home: "Главная",
    live: "Живой урок",
    students: "Ученики",
    assignments: "Назначенные работы",
    tests: "Тесты",
    analytics: "Аналитика",
    settings: "Настройки",
  };
  const hellos = {
    home: "ОГЭ · Математика и Русский",
    live: "Комната урока в реальном времени",
    students: "Список класса и профиль ученика",
    assignments: "Мониторинг сданных вариантов и ведомости",
    tests: "Генератор КИМ",
    analytics: "Матрица знаний и прогноз ОГЭ",
    settings: "Параметры текущего класса",
  };

  const tabMeta = [...NAV, NAV_SETTINGS].find((n) => n.id === state.tab) || NAV[0];

  return `
    <div class="dash ${state.tab === "students" ? "is-students" : ""}${inLiveRoom ? " is-live-room" : ""}${inLiveHub ? " is-live-hub" : ""}" id="dash-shell">
      <div class="sidebar-backdrop" id="sidebar-backdrop" hidden></div>
      <aside class="sidebar" id="app-sidebar">
        <div class="sidebar-brand">
          ${
            window.EduSenseBrand?.logoHtml
              ? window.EduSenseBrand.logoHtml({ compact: true })
              : `<span class="es-logo is-compact"><span class="es-logo-mark" aria-hidden="true"><img src="/assets/edusense-mark-192.png?v=9" alt="" width="34" height="34"/></span><span class="es-logo-text"><span class="es-logo-name">EduSense</span></span></span>`
          }
        </div>

        <div class="class-switch">
          <div class="class-switch-card ${state.classrooms.length > 1 ? "is-select" : ""}">
            <div class="class-switch-copy">
              <strong>${escapeHtml(classSwitcherTitle(c))}</strong>
              <small>${escapeHtml(studentsCountLabel(sidebarStudentCount()))}</small>
            </div>
            ${
              state.classrooms.length > 1
                ? `<span class="class-switch-caret" aria-hidden="true">▼</span>
                   <select id="class-select" class="class-select" title="Переключить класс" aria-label="Переключить класс">
                    ${state.classrooms
                      .map(
                        (item) => `
                      <option value="${item.id}" ${item.id === c.id ? "selected" : ""}>
                        ${escapeHtml(classSwitcherTitle(item))}
                      </option>`
                      )
                      .join("")}
                   </select>`
                : ""
            }
          </div>
          <button type="button" class="class-switch-new js-new-class">+ Новый класс</button>
        </div>

        <nav class="nav-list" aria-label="Меню учителя">
          ${NAV.map((item, idx) => {
            const hook = item.action
              ? `data-nav-action="${item.action}"`
              : `data-tab="${item.id}"`;
            return `
            <button type="button" class="nav-item ${state.tab === item.id ? "is-active" : ""}"
              style="--nav-i:${idx}"
              ${hook} data-tour="nav-${item.id}">
              ${icon(item.icon)}
              <span class="nav-item-label">${item.label}</span>
              ${navBadgeHtml(item.badge)}
            </button>`;
          }).join("")}
        </nav>

        <div class="sidebar-foot">
          <div class="user-chip">
            <span class="avatar">${escapeHtml(initials(u.full_name))}</span>
            <div class="meta">
              <div class="name">${escapeHtml(u.full_name || "Учитель")}</div>
              <div class="role"><span class="online-dot" aria-hidden="true"></span> В сети</div>
            </div>
            <button type="button" class="user-chip-exit" id="btn-logout" title="Выйти" aria-label="Выйти">
              ${icon("logout")}
            </button>
          </div>
          <button type="button" class="sidebar-mini ${state.tab === "settings" ? "is-active" : ""}"
            data-tab="settings" data-tour="nav-settings">
            ${icon(NAV_SETTINGS.icon)}
            <span>Настройки класса</span>
          </button>
          <a class="sidebar-install" href="/install">Установить приложение</a>
        </div>
      </aside>

      <main class="main">
        <div class="tab-watermark" aria-hidden="true" data-tab="${tabMeta.id}">
          ${icon(tabMeta.icon)}
        </div>
        <div class="main-inner">
          ${
            hideMainHead
              ? ""
              : `<div class="main-head">
            <div class="main-head-top">
              <button type="button" class="nav-toggle" id="nav-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="app-sidebar">
                <span class="nav-toggle-bars" aria-hidden="true"></span>
              </button>
              <div class="main-head-text">
                <h1>${titles[state.tab] || "Главная"}</h1>
                <p class="hello">${hellos[state.tab] || ""}</p>
              </div>
              <div class="main-head-tools main-head-tools-inline">
                <div id="notif-root"></div>
              </div>
            </div>
            ${
              state.tab === "assignments"
                ? `<div class="main-head-actions">
              <button type="button" class="btn-primary head-issue-btn" id="btn-issue-new">
                <span class="head-issue-full">+ Назначить работу классу</span>
                <span class="head-issue-short" aria-hidden="true">+</span>
              </button>
            </div>`
                : ""
            }
          </div>`
          }
          ${renderTab()}
        </div>
      </main>
      ${renderInviteModal()}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

let genStepsTimer = null;

function startGenStepsCycle() {
  if (genStepsTimer) {
    clearInterval(genStepsTimer);
    genStepsTimer = null;
  }
  const root = document.getElementById("gen-steps");
  const stage = document.getElementById("gen-loading");
  const label = document.getElementById("gen-progress-text");
  const bar = document.getElementById("gen-progress-bar");
  const track = document.getElementById("gen-progress");
  if (!root) return;
  const items = [...root.querySelectorAll("li")];
  if (!items.length) return;
  const stepMs = 1400;
  const captions = [
    "Сверяем кодификатор…",
    "Подставляем тексты и задания…",
    "Подгоняем чертежи и ключи…",
    "Вариант почти готов…",
  ];
  const stitchIndex = 2;

  const paint = (i) => {
    items.forEach((el, idx) => {
      el.classList.toggle("is-done", idx < i);
      el.classList.toggle("is-active", idx === i);
      const mark = el.querySelector("i");
      if (mark) mark.textContent = idx < i ? "✓" : idx === i ? "●" : "";
    });
    if (stage) {
      stage.dataset.step = String(i);
      stage.classList.toggle("is-stitching", i === stitchIndex);
    }
    if (label) label.textContent = captions[i] || "Генерация…";
  };

  let i = 0;
  if (stage) stage.style.setProperty("--gen-step-ms", `${stepMs}ms`);
  paint(0);
  genStepsTimer = setInterval(() => {
    i = Math.min(i + 1, items.length - 1);
    paint(i);
  }, stepMs);
}

function enhanceEffects() {
  if (state.generator?.generating) startGenStepsCycle();
  else if (genStepsTimer) {
    clearInterval(genStepsTimer);
    genStepsTimer = null;
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  document.querySelectorAll(".glass").forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", `${((e.clientX - r.left) / r.width) * 100}%`);
      el.style.setProperty("--my", `${((e.clientY - r.top) / r.height) * 100}%`);
    });
  });

  const sidebar = document.getElementById("app-sidebar");
  if (sidebar && !sidebar.dataset.spotBound) {
    sidebar.dataset.spotBound = "1";
    sidebar.addEventListener("pointermove", (e) => {
      const r = sidebar.getBoundingClientRect();
      sidebar.style.setProperty("--spot-x", `${((e.clientX - r.left) / r.width) * 100}%`);
      sidebar.style.setProperty("--spot-y", `${((e.clientY - r.top) / r.height) * 100}%`);
    });
  }

  document.querySelectorAll(".num[data-count]").forEach((el) => {
    const target = Number(el.getAttribute("data-count") || 0);
    if (!target) {
      el.textContent = "0";
      return;
    }
    const start = performance.now();
    const dur = 700;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(target * eased));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

function setNavOpen(open) {
  const dash = document.getElementById("dash-shell");
  const btn = document.getElementById("nav-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!dash) return;
  dash.classList.toggle("is-nav-open", !!open);
  document.documentElement.classList.toggle("is-nav-open", !!open);
  document.body?.classList.toggle("is-nav-open", !!open);
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

function isRnoTitle(title) {
  return String(title || "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .startsWith("работа над ошибками");
}

function collectTeacherNotifications() {
  const out = [];
  const assigns = state.assignmentsBoard.items || [];
  assigns.forEach((a) => {
    const code = String(a.code || "").toUpperCase();
    const title = a.title || code;
    if (isRnoTitle(title)) {
      out.push({
        id: `rno-${a.id}`,
        kind: "rno",
        title: "Назначено РНО",
        text: title,
        at: a.created_at || "",
        tab: "assignments",
        code,
      });
    }
    const today = Number(a.submissions_today || 0);
    const total = Number(a.submissions_count || a.unique_submitters || 0);
    if (today > 0) {
      out.push({
        id: `sub-today-${a.id}-${today}`,
        kind: "submit",
        title: "Сдача тестов",
        text: `${today} сегодня · ${title}`,
        at: a.created_at || "",
        tab: "assignments",
        code,
      });
    } else if (total > 0) {
      out.push({
        id: `sub-${a.id}-${total}`,
        kind: "submit",
        title: "Сдача тестов",
        text: `${total} сдач · ${title}`,
        at: a.created_at || "",
        tab: "assignments",
        code,
      });
    }
    const pack = state.assignmentsBoard.submissions[code];
    const subs = pack && Array.isArray(pack.items) ? pack.items : [];
    subs.forEach((s) => {
      const st = String(s.status || "");
      if (st !== "ai_reviewed" && st !== "graded") return;
      out.push({
        id: `ai-${s.id}`,
        kind: "ai",
        title: st === "ai_reviewed" ? "Результаты ИИ-проверки" : "Работа проверена",
        text: `${s.student_name || "Ученик"} · ${title}`,
        at: s.submitted_at || "",
        tab: "assignments",
        code,
        subId: s.id,
      });
    });
  });
  out.sort((a, b) => String(b.at || "").localeCompare(String(a.at || "")));
  return out;
}

function openTeacherNotification(item) {
  if (!item) return;
  if (item.tab) state.tab = item.tab;
  if (item.code) {
    state.assignmentsBoard.expandedCode = item.code;
    if (item.subId) state.assignmentsBoard.expandedSubId = item.subId;
  }
  render();
  if (item.tab === "assignments") {
    loadAssignmentsBoard();
    if (item.code) loadAssignmentSubmissions(item.code);
  }
}

function teacherGoToTab(id) {
  if (state.step !== "dashboard" || !id) return;
  if (state.tab !== id) {
    state.tab = id;
    render();
    if (id === "analytics") loadAnalyticsBoard();
    if (id === "assignments") loadAssignmentsBoard();
  }
}

function mountTeacherChrome() {
  if (state.step !== "dashboard") return;
  if (typeof EduSenseNotifications !== "undefined") {
    EduSenseNotifications.mount(document.getElementById("notif-root"), {
      collect: collectTeacherNotifications,
      onSelect: openTeacherNotification,
    });
  }
  if (typeof EduSenseTour !== "undefined") EduSenseTour.onRendered();
  if (typeof EduSensePWA !== "undefined") EduSensePWA.sync();
}

function render() {
  const root = document.getElementById("app");
  if (state.step === "create") root.innerHTML = renderCreate();
  else if (state.step === "code") root.innerHTML = renderCode();
  else root.innerHTML = renderDashboard();
  bind();
  enhanceEffects();
  if (typeof OgeRusUI !== "undefined") OgeRusUI.bind(root);
  if (typeof window !== "undefined" && window.EduSenseTG?.isTelegramMiniApp) {
    document.documentElement.classList.add("is-telegram-miniapp");
    document.body?.classList.add("is-telegram-miniapp");
  }
  mountTeacherChrome();
  if (typeof EduSenseTour !== "undefined") {
    EduSenseTour.maybeStart({
      goToTab: teacherGoToTab,
      goDashboard: function () {
        if (state.step === "dashboard") return;
        state.step = "dashboard";
        render();
      },
      screen: () => state.step,
      tab: () => state.tab,
      hasClass: () => !!(state.classroom && state.classroom.access_code),
      hasVariant: () => !!(state.generator && state.generator.variant),
      modalOpen: () => !!(state.generator && state.generator.publishOpen) || !!state.showQr,
    });
    EduSenseTour.onRendered();
  }
}

function bind() {
  if (!liveRosterActive()) stopLiveRoster();

  if (state.step === "create") {
    document.querySelectorAll("[data-exam]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.form.examType = btn.getAttribute("data-exam");
        syncFormDefaults();
        render();
      });
    });

    const nameInput = document.getElementById("class-name");
    nameInput?.addEventListener("input", (e) => {
      state.form.name = e.target.value;
    });

    document.querySelectorAll("[data-subject]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.form.subject = btn.getAttribute("data-subject");
        document.querySelectorAll("[data-subject]").forEach((b) => {
          const on = b.getAttribute("data-subject") === state.form.subject;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
      });
    });

    document.getElementById("btn-create")?.addEventListener("click", submitCreate);
    document.getElementById("btn-cancel-create")?.addEventListener("click", cancelCreateClass);
    return;
  }

  if (state.step === "code") {
    document.getElementById("btn-copy-link")?.addEventListener("click", copyInviteLink);
    document.getElementById("class-code-value")?.addEventListener("click", copyInviteLink);
    document.getElementById("btn-qr")?.addEventListener("click", () => {
      state.showQr = true;
      render();
    });
    document.getElementById("btn-print-qr")?.addEventListener("click", printClassQr);
    document.getElementById("btn-close-qr")?.addEventListener("click", () => {
      state.showQr = false;
      render();
    });
    document.getElementById("btn-copy-qr-link")?.addEventListener("click", () => {
      const code = state.classroom?.access_code;
      if (code) copyClassInviteLink();
    });
    document.getElementById("qr-backdrop")?.addEventListener("click", (e) => {
      if (e.target.id === "qr-backdrop") {
        state.showQr = false;
        render();
      }
    });
    document.getElementById("btn-to-dashboard")?.addEventListener("click", () => {
      pageTransition(async () => {
        stopLiveRoster();
        state.step = "dashboard";
        state.tab = "home";
        localStorage.setItem("edusense_classroom", JSON.stringify(state.classroom));
        render();
        await Promise.all([loadStudentsBoard(), loadAssignmentsBoard(), loadHomeInsights()]);
      }, { overlay: true });
    });
    startLiveRoster();
    return;
  }

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTeacherTab(btn.getAttribute("data-tab"));
    });
  });

  document.querySelectorAll("[data-nav-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-nav-action");
      setNavOpen(false);
      if (action === "invite") {
        state.showInvite = true;
        render();
      }
    });
  });

  bindMobileNav();

  document.querySelectorAll("[data-quick]").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTeacherTab(btn.getAttribute("data-quick"));
    });
  });


  document.querySelectorAll("[data-assign-view]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-assign-view");
      openGradebook(code);
    });
  });
  document.querySelectorAll("[data-assign-analytics]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-assign-analytics");
      if (code) state.analyticsBoard.assignmentCode = String(code).toUpperCase();
      switchTeacherTab("analytics");
    });
  });
  document.querySelectorAll("[data-assign-pdf]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-assign-pdf");
      const withKeys = btn.getAttribute("data-keys") === "1";
      try {
        await exportAssignmentPdf(code, { keys: withKeys });
      } catch (err) {
        showToast(err?.message || "Не удалось сформировать PDF", "error");
      }
    });
  });
  document.querySelectorAll("[data-assign-qr]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-assign-qr");
      printAssignmentSolveQr(code);
    });
  });

  document.querySelectorAll("[data-copy-assign]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      copyAssignmentShare(
        btn.getAttribute("data-copy-assign"),
        btn.getAttribute("data-copy-url")
      );
    });
  });

  const openIssue = () => {
    state.assignmentsBoard.issueOpen = true;
    state.assignmentsBoard.issueStep = "choose";
    state.assignmentsBoard.menuOpenCode = null;
    render();
  };
  document.getElementById("btn-issue-new")?.addEventListener("click", openIssue);
  document.getElementById("btn-issue-new-empty")?.addEventListener("click", openIssue);

  const closeIssue = () => {
    state.assignmentsBoard.issueOpen = false;
    render();
  };
  document.getElementById("btn-close-issue")?.addEventListener("click", closeIssue);
  document.getElementById("issue-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "issue-backdrop") closeIssue();
  });
  document.querySelectorAll("[data-issue-step]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.assignmentsBoard.issueStep = btn.getAttribute("data-issue-step") || "choose";
      render();
    });
  });
  document.getElementById("issue-deadline")?.addEventListener("change", (e) => {
    state.assignmentsBoard.issueSettings.deadlineAt = e.target.value || "";
  });
  document.getElementById("issue-time-limit")?.addEventListener("change", (e) => {
    state.assignmentsBoard.issueSettings.timeLimitMinutes = e.target.value || "";
  });
  document.getElementById("btn-issue-to-tests")?.addEventListener("click", () => {
    const s = state.assignmentsBoard.issueSettings;
    state.generator.publishDeadline = s.deadlineAt || "";
    state.generator.publishTimeLimit = s.timeLimitMinutes || "";
    state.assignmentsBoard.issueOpen = false;
    state.tab = "tests";
    render();
  });

  document.querySelectorAll("[data-assign-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.getAttribute("data-assign-filter") || "active";
      state.assignmentsBoard.listFilter = next;
      state.assignmentsBoard.menuOpenCode = null;
      render();
    });
  });

  document.querySelectorAll("[data-assign-menu]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-assign-menu");
      const board = state.assignmentsBoard;
      if (board.menuOpenCode && String(board.menuOpenCode).toUpperCase() === String(code).toUpperCase()) {
        board.menuOpenCode = null;
      } else {
        board.menuOpenCode = code;
      }
      render();
    });
  });

  document.querySelectorAll("[data-extend-deadline]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-extend-deadline");
      if (!code) return;
      try {
        await patchAssignment(code, { extend_deadline_days: 1 });
        showToast("Дедлайн +1 день", "success");
        state.assignmentsBoard.menuOpenCode = null;
      } catch (err) {
        showToast(err.message || "Не удалось продлить дедлайн", "error");
      }
    });
  });

  document.querySelectorAll("[data-close-intake]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-close-intake");
      if (!code || btn.disabled) return;
      try {
        await patchAssignment(code, { accepting_submissions: false, status: "closed" });
        showToast("Приём работ закрыт", "success");
        state.assignmentsBoard.menuOpenCode = null;
      } catch (err) {
        showToast(err.message || "Не удалось закрыть приём", "error");
      }
    });
  });

  document.querySelectorAll("[data-reopen-intake]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = btn.getAttribute("data-reopen-intake");
      if (!code || btn.disabled) return;
      try {
        await patchAssignment(code, { accepting_submissions: true, status: "active" });
        showToast("Приём работ снова открыт", "success");
        state.assignmentsBoard.menuOpenCode = null;
      } catch (err) {
        showToast(err.message || "Не удалось открыть приём", "error");
      }
    });
  });

  document.querySelectorAll("[data-rus-rubric]").forEach((root) => {
    const subId = root.getAttribute("data-rus-rubric");
    if (!subId || root.dataset.bound) return;
    root.dataset.bound = "1";
    root.querySelectorAll("select[data-rubric-key], input[data-rubric-test]").forEach((el) => {
      el.addEventListener("change", () => applyRusRubricSum(subId));
      el.addEventListener("input", () => applyRusRubricSum(subId));
    });
  });

  document.querySelectorAll("[data-save-grade]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const subId = btn.getAttribute("data-save-grade");
      const assignCode =
        btn.getAttribute("data-assign-code") || state.assignmentsBoard.whoModalCode;
      if (!subId || !assignCode || btn.disabled) return;
      const scoreEl = document.querySelector(`[data-grade-score="${subId}"]`);
      const commentEl = document.querySelector(`[data-grade-comment="${subId}"]`);
      const body = {};
      const rawScore = scoreEl ? String(scoreEl.value || "").trim() : "";
      if (rawScore !== "") {
        const n = Number(rawScore);
        if (!Number.isFinite(n) || n < 0) {
          showToast("Введите корректный балл", "error");
          return;
        }
        body.teacher_score = n;
      }
      if (commentEl) {
        body.teacher_comment = String(commentEl.value || "");
        const rubricLine = rusRubricCommentLine(subId);
        if (rubricLine && !body.teacher_comment.includes("Критерии:")) {
          body.teacher_comment = [body.teacher_comment.trim(), rubricLine].filter(Boolean).join("\n");
        }
      }
      if (body.teacher_score == null && body.teacher_comment == null) {
        showToast("Укажите балл или комментарий", "error");
        return;
      }
      if (body.teacher_score == null && !String(body.teacher_comment || "").trim()) {
        showToast("Укажите балл или комментарий", "error");
        return;
      }
      try {
        await patchSubmissionGrade(assignCode, Number(subId), body);
      } catch (_) {
        /* toast already shown */
      }
    });
  });

  document.querySelectorAll("[data-view-work]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const subId = btn.getAttribute("data-view-work");
      if (!subId) return;
      state.assignmentsBoard.expandedSubId = Number(subId);
      state.assignmentsBoard.whoTab = "submitted";
      render();
    });
  });

  document.getElementById("btn-who-back-list")?.addEventListener("click", (e) => {
    e.stopPropagation();
    state.assignmentsBoard.expandedSubId = null;
    state.assignmentsBoard.whoTab = "submitted";
    render();
  });

  const openWho = (code) => openGradebook(code);

  document.querySelectorAll("[data-toggle-gradebook]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openGradebook(btn.getAttribute("data-toggle-gradebook"));
    });
  });
  document.querySelectorAll("[data-export-csv]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      exportGradebookCsv(btn.getAttribute("data-export-csv"));
    });
  });
  document.querySelectorAll("[data-export-pdf]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      exportGradebookPdf(btn.getAttribute("data-export-pdf"));
    });
  });

  document.querySelectorAll("[data-open-who]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openWho(btn.getAttribute("data-open-who"));
    });
  });

  const closeWho = () => {
    state.assignmentsBoard.whoModalCode = null;
    state.assignmentsBoard.expandedSubId = null;
    render();
  };
  document.getElementById("btn-close-who")?.addEventListener("click", closeWho);
  document.getElementById("btn-close-who-foot")?.addEventListener("click", closeWho);
  document.getElementById("who-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "who-backdrop") closeWho();
  });
  document.querySelectorAll("[data-who-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.assignmentsBoard.whoTab = btn.getAttribute("data-who-tab") || "submitted";
      state.assignmentsBoard.expandedSubId = null;
      render();
      if (state.assignmentsBoard.whoTab === "not_started") loadStudentsBoard();
    });
  });
  document.getElementById("btn-remind-missing")?.addEventListener("click", () => {
    copyRemindText(findAssignmentByCode(state.assignmentsBoard.whoModalCode));
  });
  document.getElementById("btn-who-to-students")?.addEventListener("click", () => {
    state.assignmentsBoard.whoModalCode = null;
    state.assignmentsBoard.expandedSubId = null;
    state.tab = "students";
    render();
    loadStudentsBoard();
  });

  // Ученики: QR / ростер / экспорт
  document.getElementById("btn-copy-students-code")?.addEventListener("click", copyInvite);
  document.getElementById("btn-copy-students-code-modal")?.addEventListener("click", copyInvite);
  document.getElementById("btn-export-students")?.addEventListener("click", () => {
    if (!(state.studentsBoard.students || []).length) {
      showToast("Сначала добавьте учеников", "error");
      return;
    }
    exportStudentsCsv();
  });
  document.getElementById("btn-open-students-invite")?.addEventListener("click", () => {
    state.studentsBoard.inviteOpen = true;
    state.studentsBoard.rosterDraft = "";
    render();
  });
  const closeStudentsInvite = () => {
    state.studentsBoard.inviteOpen = false;
    state.studentsBoard.rosterDraft = "";
    render();
  };
  document.getElementById("btn-close-students-invite")?.addEventListener("click", closeStudentsInvite);
  document.getElementById("btn-close-students-invite-foot")?.addEventListener("click", closeStudentsInvite);
  document.getElementById("students-invite-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "students-invite-backdrop") closeStudentsInvite();
  });
  document.getElementById("roster-names-input")?.addEventListener("input", (e) => {
    state.studentsBoard.rosterDraft = e.target.value || "";
  });
  document.getElementById("btn-save-roster")?.addEventListener("click", async () => {
    const added = parseRosterText(state.studentsBoard.rosterDraft);
    if (!added.length && !(state.studentsBoard.roster || []).length) {
      showToast("Вставьте хотя бы одно ФИО или закройте окно", "error");
      return;
    }
    const names = mergeRosterNames(state.studentsBoard.roster || [], added);
    try {
      await saveRosterNames(names);
    } catch (_) {
      /* toast already shown */
    }
  });

  const rosterSearch = document.getElementById("roster-search");
  rosterSearch?.addEventListener("input", (e) => {
    state.studentsBoard.query = e.target.value || "";
    state._rosterSearchCaret = e.target.selectionStart;
    render();
  });
  document.querySelectorAll("[data-select-student]").forEach((el) => {
    el.addEventListener("click", () => {
      const name = el.getAttribute("data-select-student");
      if (name) openStudentProfile(name);
    });
  });
  document.querySelectorAll("[data-target-mark]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const n = Number(btn.getAttribute("data-target-mark"));
      if ([3, 4, 5].includes(n)) {
        state.studentsBoard.targetMark = n;
        render();
      }
    });
  });
  document.getElementById("btn-issue-remediation")?.addEventListener("click", () => {
    const name = state.studentsBoard.profileName;
    if (name) issueRemediationForStudent(name);
  });
  document.querySelectorAll("[data-review-assign]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openStudentReview(btn.getAttribute("data-review-assign"), btn.getAttribute("data-review-sub"));
    });
  });
  if (rosterSearch && state._rosterSearchCaret != null) {
    rosterSearch.focus();
    const pos = Math.min(Number(state._rosterSearchCaret), rosterSearch.value.length);
    rosterSearch.setSelectionRange(pos, pos);
    state._rosterSearchCaret = null;
  }

  document.getElementById("btn-invite-header")?.addEventListener("click", () => {
    state.showQr = true;
    render();
  });
  document.getElementById("btn-copy-dash")?.addEventListener("click", copyClassInviteLink);
  document.getElementById("btn-home-live")?.addEventListener("click", () => {
    openLiveRoom();
  });
  document.getElementById("btn-enter-live-room")?.addEventListener("click", () => {
    openLiveRoom();
  });
  document.getElementById("btn-live-back")?.addEventListener("click", () => {
    openLiveHub();
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
  document.getElementById("btn-invite-notify")?.addEventListener("click", () => {
    try {
      localStorage.setItem(REF_NOTIFY_KEY, "1");
    } catch (_) {}
    showToast("Сообщим, как только реферальная программа заработает", "success");
    render();
  });
  document.getElementById("btn-quick-drill")?.addEventListener("click", startQuickTrainer);
  document.getElementById("btn-qr")?.addEventListener("click", () => {
    state.showQr = true;
    render();
  });
  document.getElementById("btn-print-qr")?.addEventListener("click", printClassQr);
  document.getElementById("btn-close-qr")?.addEventListener("click", () => {
    state.showQr = false;
    render();
  });
  document.getElementById("btn-copy-qr-link")?.addEventListener("click", () => {
    const code = state.classroom?.access_code;
    if (code) copyClassInviteLink();
  });
  document.getElementById("btn-qr-secondary")?.addEventListener("click", () => {
    state.showQr = true;
    render();
  });
  document.getElementById("qr-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "qr-backdrop") {
      state.showQr = false;
      render();
    }
  });
  document.querySelectorAll(".js-new-class").forEach((btn) => {
    btn.addEventListener("click", startCreateClass);
  });
  document.getElementById("class-select")?.addEventListener("change", (e) => {
    const id = Number(e.target.value);
    const next = state.classrooms.find((item) => item.id === id);
    if (next && next.id !== state.classroom?.id) {
      selectClassroom(next);
      render();
    }
  });
  document.getElementById("btn-logout")?.addEventListener("click", () => {
    window.EduSenseAuth?.clearSession?.({ forgetAccount: false });
    try {
      localStorage.removeItem("edusense_user");
      localStorage.removeItem("edusense_token");
      localStorage.removeItem("edusense_classroom");
    } catch (_) {}
    window.location.href = "/#auth";
  });

  bindAnalyticsControls();
  bindGenerator();
  bindExportPanelOnce();
  bindPart2GradeOnce();
  if (liveRosterActive()) startLiveRoster();
  if (state.step === "dashboard" && state.tab === "home") loadHomeInsights();
}

function questionsToVariant(questions, apiMeta) {
  const c = state.classroom;
  const exam = examLabel(c?.exam_type || "oge");
  const subject = c?.subject || "Математика";
  const subjectNorm = teacherSubjectCode({ subject, subject_code: subject });
  const raw = [...(questions || [])];
  let examUi = (apiMeta && apiMeta.exam_ui) || "";
  // oge_rus_kim только для русского; math-эталон может прийти с exam_ui=etalon
  if (subjectNorm === "math" && examUi === "oge_rus_kim") examUi = "";
  if (subjectNorm !== "russian" && examUi === "oge_rus_kim") examUi = "";
  const isRusKim =
    subjectNorm === "russian" &&
    (examUi === "oge_rus_kim" ||
      raw.some((q) => q.payload && (q.payload.oge_rus || q.payload.grammar_text || q.payload.listening_text)));
  // Эталон math: сохраняем номера КИМ 1–25, но без флага kim_order (он = UI русского)
  const keepKimNums = isRusKim || subjectNorm === "math" || !!(apiMeta && apiMeta.etalon);

  let ordered;
  if (keepKimNums) {
    ordered = raw.slice().sort((a, b) => Number(a.num || 999) - Number(b.num || 999));
  } else {
    const p1 = raw.filter((q) => Number(q.part || 1) === 1);
    const p2 = raw.filter((q) => Number(q.part || 1) !== 1);
    const byNum = (a, b) => Number(a.num || 999) - Number(b.num || 999);
    p1.sort(byNum);
    p2.sort(byNum);
    ordered = [...p1, ...p2];
  }

  const p1Count = raw.filter((q) => Number(q.part || 1) === 1).length;
  const examType = String(c?.exam_type || "").toLowerCase();
  const tasks = ordered.map((q, i) => {
    const part = keepKimNums ? Number(q.part || 1) : i < p1Count ? 1 : 2;
    const etalonFlag = !!(apiMeta && apiMeta.etalon);
    const provenanceMeta = (apiMeta && apiMeta.provenance) || null;
    let payload = q.payload || null;
    if (etalonFlag) {
      payload = { ...(payload && typeof payload === "object" ? payload : {}) };
      payload.etalon = true;
      if (provenanceMeta && !payload.provenance) payload.provenance = provenanceMeta;
    }
    // Стереть случайный oge_rus с math-заданий
    if (subjectNorm === "math" && payload && typeof payload === "object") {
      payload = { ...payload };
      delete payload.oge_rus;
      if (payload.ui === "oge_rus" || payload.ui === "listening" || payload.ui === "essay_choice") {
        delete payload.ui;
      }
      delete payload.grammar_text;
      delete payload.listening_text;
      delete payload.reading_text;
      delete payload.essay_options;
      delete payload.matching;
    }
    return {
      id: `task-${i + 1}`,
      num: keepKimNums ? Number(q.num || i + 1) : i + 1,
      part,
      type: q.type || (part === 2 ? "Развёрнутый ответ" : "Краткий ответ"),
      topic: q.topic || "Общее",
      section: q.section || "",
      text: q.text || "",
      answer: q.answer || "",
      solution: q.solution || "",
      acceptable_answers: Array.isArray(q.acceptable_answers) ? q.acceptable_answers : null,
      maxScore: q.max_score || (part === 2 ? 2 : 1),
      figureKind: q.figure_kind || null,
      figureSvg: q.figure_svg || null,
      solutionFigureSvg: q.solution_figure_svg || null,
      payload,
      kim_order: !!isRusKim,
      subject,
      subject_code: subject,
      exam_code: examType || exam,
      exam: examType || exam,
    };
  });
  const etalon = subjectNorm === "russian" ? false : !!(apiMeta && apiMeta.etalon);
  const provenance = (apiMeta && apiMeta.provenance) || null;
  const bank = (apiMeta && apiMeta.bank) || null;
  let bankLabel = String((apiMeta && apiMeta.variant_label) || (bank && bank.label) || "").trim();
  let bankCode = String((apiMeta && apiMeta.bank_code) || (bank && bank.code) || "").trim();
  if (!bankLabel || !bankCode) {
    const fromPayload = tasks.find((t) => t.payload && (t.payload.bank_label || t.payload.bank_code));
    if (fromPayload && fromPayload.payload) {
      bankLabel = bankLabel || String(fromPayload.payload.bank_label || "").trim();
      bankCode = bankCode || String(fromPayload.payload.bank_code || "").trim();
    }
  }
  const etalonTitle = etalon
    ? `${exam} · ${subject} · Эталонный вариант`
    : `${exam} · ${subject} · Вариант A`;
  const rusTitle = bankLabel ? `${exam} · ${bankLabel}` : etalonTitle;
  return {
    id: `var-${Date.now()}`,
    title: bankLabel ? rusTitle : etalonTitle,
    subject,
    subject_code: subject,
    exam,
    exam_code: examType || exam,
    exam_ui: isRusKim ? "oge_rus_kim" : examUi && examUi !== "oge_rus_kim" ? examUi : undefined,
    etalon,
    provenance: provenance || undefined,
    bank: bank || undefined,
    variant_label: bankLabel || undefined,
    code: bankCode || `ES-${Math.random().toString(36).slice(2, 6).toUpperCase()}`,
    createdAt: new Date().toISOString(),
    tasks: tasks.length ? tasks : demoVariant().tasks,
  };
}

function waitMs(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function startKimGenerate() {
  if (state.generator.generating) return;
  state.generator.generating = true;
  render();
  const started = performance.now();
  let failed = false;
  try {
    const c = state.classroom;
    const size = currentGenSizes()[state.generator.size] || currentGenSizes().standard;
    const useEtalon = teacherSubjectCode({ subject: c?.subject }) !== "russian" && wantsEtalonGenerate();
    const slots =
      Array.isArray(state.generator._slots) && state.generator._slots.length
        ? state.generator._slots
        : null;
    const payload = {
      exam: c?.exam_type || "oge",
      subject: c?.subject || "Математика",
      difficulty: state.generator.difficulty || "medium",
      count: slots
        ? kimCount(c?.exam_type, c?.subject)
        : state.generator._quickCount || size.count,
      vary: useEtalon ? false : !!state.generator.vary,
    };
    if (slots) payload.slots = slots;
    if (useEtalon) payload.mode = "etalon";
    const data = await api("/api/ai/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    {
      const subj = teacherSubjectCode({
        subject: c?.subject,
        subject_code: c?.subject,
      });
      let ui = data.exam_ui || "";
      if (subj === "math" || (subj && subj !== "russian" && ui === "oge_rus_kim")) {
        ui = ui === "oge_rus_kim" ? "" : ui;
      }
      if (subj !== "russian" && ui === "oge_rus_kim") ui = "";
      state.generator.examUi = ui;
    }
    state.generator.variant = questionsToVariant(data.questions, data);
    state.generator.selectedTaskId = null;
    const note = String(data.message || "Вариант собран");
    const rus = teacherSubjectCode({ subject: c?.subject }) === "russian";
    if (data.etalon && !rus) {
      state.generator.lastSourceNote = note || "Эталонный вариант";
    } else if (useEtalon) {
      state.generator.lastSourceNote =
        "Запрошен эталон, но сервер не пометил вариант как эталонный";
      showToast(state.generator.lastSourceNote, "error");
    } else {
      const label = data.variant_label || (data.bank && data.bank.label);
      state.generator.lastSourceNote = label
        ? `${label}. Чтобы указать ошибку, напишите: ${String(label).split(" · ")[0]}, задание 11`
        : /банк|из\s*проверенн/i.test(note)
          ? "Вариант собран"
          : note;
    }
    const ogeHint = data.etalon && !rus
      ? " · Эталонный вариант"
      : data.exam_ui === "oge_rus_kim" || isTeacherOgeRusExam(state.generator.variant)
        ? " · режим КИМ ОГЭ"
        : "";
    if (!(useEtalon && !data.etalon)) {
      state.generator._readyToast = `Готово: ${tasksCountLabel(data.questions?.length || 0)}${ogeHint}`;
    }
  } catch (err) {
    failed = true;
    const msg = err.message || "Ошибка генерации";
    showToast(msg, "error");
    if (/mode=etalon|эталон/i.test(msg)) {
      state.generator.lastSourceNote = msg;
    }
  } finally {
    if (!failed) {
      const minHold = 3400 + Math.round(Math.random() * 1600);
      const left = minHold - (performance.now() - started);
      if (left > 0) await waitMs(left);
    }
    const readyToast = state.generator._readyToast;
    state.generator._readyToast = "";
    state.generator.generating = false;
    state.generator._quickCount = 0;
    render();
    if (readyToast) showToast(readyToast, "success");
  }
}

function bindGenerator() {

  document.querySelectorAll("[data-gen-size]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.generator.size = btn.getAttribute("data-gen-size") || "standard";
      render();
    });
  });

  document.querySelectorAll("[data-difficulty]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.generator.difficulty = btn.getAttribute("data-difficulty") || "medium";
      render();
    });
  });

  document.querySelectorAll("[data-focus-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.generator.focusId = btn.getAttribute("data-focus-id") || "";
      render();
    });
  });

  document.getElementById("chk-mutator")?.addEventListener("change", (e) => {
    const on = !!e.target.checked;
    state.generator.publishShuffle = on;
    if (state.assignmentsBoard?.issueSettings) {
      state.assignmentsBoard.issueSettings.shuffleVariants = on;
    }
  });

  document.getElementById("chk-etalon")?.addEventListener("change", (e) => {
    state.generator.etalon = !!e.target.checked;
    render();
  });

  document.getElementById("btn-generate")?.addEventListener("click", startKimGenerate);
  document.getElementById("btn-regen")?.addEventListener("click", startKimGenerate);
  document.getElementById("btn-gen-modes")?.addEventListener("click", () => {
    state.generator.variant = null;
    state.generator.selectedTaskId = null;
    state.generator._slots = null;
    state.generator._quickCount = 0;
    render();
  });
  document.getElementById("btn-gen-full")?.addEventListener("click", () => {
    state.generator.size = "standard";
    state.generator._quickCount = 0;
    state.generator._slots = null;
    startKimGenerate();
  });
  document.getElementById("btn-gen-focus")?.addEventListener("click", () => {
    const preset = currentFocusPreset();
    if (!preset) return;
    state.generator.focusId = preset.id;
    state.generator._slots = preset.slots.slice();
    state.generator._quickCount = preset.slots.length;
    startKimGenerate();
  });
  document.getElementById("btn-gen-express")?.addEventListener("click", () => {
    state.generator.size = "mini";
    state.generator._quickCount = expressKimCount();
    state.generator._slots = null;
    state.generator.publishTimeLimit = "15";
    startKimGenerate();
  });

  document.querySelectorAll("[data-open-task]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-open-task") || "";
      state.generator.selectedTaskId = id || null;
      render();
    });
  });

  document.querySelectorAll(".task-card").forEach((card) => {
    card.addEventListener("click", (e) => {
      if (e.target.closest("button, .task-figure, #figure-lightbox")) return;
      state.generator.selectedTaskId = card.getAttribute("data-task-id");
      render();
    });
  });

  document.getElementById("btn-open-publish")?.addEventListener("click", () => {
    if (isVariantPublished(state.generator.variant)) {
      showToast("Эта работа уже выписана ученикам", "info");
      return;
    }
    state.generator.publishOpen = true;
    state.generator.publishSuccess = null;
    state.generator.publishBusy = false;
    if (!state.generator.publishAudience) {
      state.generator.publishAudience = state.classroom?.id ? `class:${state.classroom.id}` : "all";
    }
    if (state.generator.publishHideAnswers == null) state.generator.publishHideAnswers = true;
    render();
    if (!(state.studentsBoard.roster || []).length) loadStudentsBoard();
    if (!state.assignmentsBoard.items.length && !state.assignmentsBoard.loading) {
      loadAssignmentsBoard();
    }
  });

  const closePublish = () => {
    state.generator.publishOpen = false;
    state.generator.publishSuccess = null;
    state.generator.publishBusy = false;
    render();
  };
  document.getElementById("btn-close-publish")?.addEventListener("click", closePublish);
  document.getElementById("btn-cancel-publish")?.addEventListener("click", closePublish);
  document.getElementById("btn-close-publish-success")?.addEventListener("click", closePublish);
  document.getElementById("publish-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "publish-backdrop") closePublish();
  });

  document.getElementById("btn-copy-publish-link")?.addEventListener("click", async () => {
    const done = state.generator.publishSuccess;
    if (!done) return;
    const url = studentWorkUrl(done.code, done.studentUrl);
    try {
      await navigator.clipboard.writeText(url);
      showToast("Ссылка скопирована", "success");
    } catch (_) {
      showToast("Не удалось скопировать", "error");
    }
  });
  document.getElementById("btn-share-publish")?.addEventListener("click", async () => {
    const done = state.generator.publishSuccess;
    if (!done) return;
    const url = studentWorkUrl(done.code, done.studentUrl);
    try {
      await navigator.share({
        title: done.title || "Работа",
        text: `${done.title || "Работа"} · код ${done.code}`,
        url,
      });
    } catch (err) {
      if (err && err.name === "AbortError") return;
      try {
        await navigator.clipboard.writeText(url);
        showToast("Ссылка скопирована", "success");
      } catch (_) {
        showToast("Не удалось поделиться", "error");
      }
    }
  });
  document.getElementById("btn-publish-to-journal")?.addEventListener("click", () => {
    state.generator.publishOpen = false;
    state.generator.publishSuccess = null;
    state.tab = "assignments";
    state.assignmentsBoard.loadedFor = null;
    render();
    loadAssignmentsBoard(true);
  });
  document.getElementById("btn-goto-journal-from-variant")?.addEventListener("click", () => {
    state.tab = "assignments";
    state.assignmentsBoard.loadedFor = null;
    render();
    loadAssignmentsBoard(true);
  });

  document.getElementById("publish-audience")?.addEventListener("change", (e) => {
    state.generator.publishAudience = e.target.value || "all";
    render();
    if (e.target.value === "individual" && !(state.studentsBoard.roster || []).length) {
      loadStudentsBoard();
    }
  });
  document.querySelectorAll("[data-pub-student]").forEach((input) => {
    input.addEventListener("change", () => {
      const names = [...document.querySelectorAll("[data-pub-student]:checked")].map((el) =>
        el.getAttribute("data-pub-student")
      );
      state.generator.publishAudienceNames = names.filter(Boolean);
    });
  });

  document.querySelectorAll('input[name="grading-mode"]').forEach((input) => {
    input.addEventListener("change", () => {
      state.generator.gradingMode = input.value;
      render();
    });
  });

  const savePublishDeadline = (e) => {
    state.generator.publishDeadline = e.target.value || "";
  };
  const savePublishTimeLimit = (e) => {
    state.generator.publishTimeLimit = e.target.value || "";
    const n = Number(e.target.value);
    state.generator.publishTimeCustom = !e.target.value || ![45, 90, 235].includes(n);
  };
  document.getElementById("publish-deadline")?.addEventListener("input", savePublishDeadline);
  document.getElementById("publish-deadline")?.addEventListener("change", savePublishDeadline);
  document.getElementById("publish-time-limit")?.addEventListener("input", savePublishTimeLimit);
  document.getElementById("publish-time-limit")?.addEventListener("change", savePublishTimeLimit);
  document.querySelectorAll("[data-deadline-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.getAttribute("data-deadline-preset");
      if (kind === "none") {
        state.generator.publishDeadline = "";
      } else {
        const d = new Date();
        d.setDate(d.getDate() + (kind === "3d" ? 3 : 1));
        d.setHours(18, 0, 0, 0);
        state.generator.publishDeadline = toLocalDatetimeValue(d);
      }
      render();
    });
  });
  document.querySelectorAll("[data-timer-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.getAttribute("data-timer-preset");
      if (kind === "custom") {
        state.generator.publishTimeCustom = true;
        if ([45, 90, 235].includes(Number(state.generator.publishTimeLimit))) {
          state.generator.publishTimeLimit = "";
        }
      } else {
        state.generator.publishTimeCustom = false;
        state.generator.publishTimeLimit = kind === "none" ? "" : kind;
      }
      render();
    });
  });
  document.getElementById("publish-shuffle")?.addEventListener("change", (e) => {
    state.generator.publishShuffle = !!e.target.checked;
    if (state.assignmentsBoard?.issueSettings) {
      state.assignmentsBoard.issueSettings.shuffleVariants = !!e.target.checked;
    }
    e.target.closest(".pub-toggle")?.classList.toggle("is-on", !!e.target.checked);
  });
  document.getElementById("publish-block-copy")?.addEventListener("change", (e) => {
    state.generator.publishBlockCopy = !!e.target.checked;
    e.target.closest(".pub-toggle")?.classList.toggle("is-on", !!e.target.checked);
  });
  document.getElementById("publish-hide-answers")?.addEventListener("change", (e) => {
    state.generator.publishHideAnswers = !!e.target.checked;
    e.target.closest(".pub-toggle")?.classList.toggle("is-on", !!e.target.checked);
  });

  document.getElementById("btn-confirm-publish")?.addEventListener("click", async () => {
    const v = state.generator.variant;
    const classroom = publishTargetClassroom() || state.classroom;
    if (!v || !classroom || state.generator.publishBusy) return;
    if (isVariantPublished(v)) {
      showToast("Эта работа уже выписана ученикам", "info");
      return;
    }
    const audience = publishAudienceValue();
    const allowed =
      audience === "individual" ? (state.generator.publishAudienceNames || []).filter(Boolean) : [];
    if (audience === "individual" && !allowed.length) {
      showToast("Выберите хотя бы одного ученика", "error");
      return;
    }
    const deadlineEl = document.getElementById("publish-deadline");
    const timeEl = document.getElementById("publish-time-limit");
    const deadlineAt = fromDatetimeLocalValue(deadlineEl?.value || state.generator.publishDeadline || "");
    if (deadlineAt && new Date(deadlineAt).getTime() <= Date.now()) {
      showToast("Дедлайн уже прошёл. Укажите время в будущем или оставьте поле пустым", "error");
      return;
    }
    const timeRaw = timeEl?.value ?? state.generator.publishTimeLimit;
    const timeLimit =
      timeRaw !== "" && timeRaw != null && !Number.isNaN(Number(timeRaw)) && Number(timeRaw) > 0
        ? Number(timeRaw)
        : null;
    const shuffle = wantsEtalonGenerate() ? false : !!state.generator.publishShuffle;
    if (betaLimitReached()) {
      showToast(
        `В открытой бете на класс можно выдать ${BETA_VARIANT_LIMIT} вариантов. Сейчас выдано ${issuedVariantCount()}.`,
        "error"
      );
      return;
    }
    state.generator.publishBusy = true;
    render();
    try {
      const body = {
        class_code: classroom.access_code || classroom.code,
        title: v.title,
        grading_mode: state.generator.gradingMode,
        shuffle_variants: shuffle,
        difficulty: state.generator.difficulty || "medium",
        block_copy: !!state.generator.publishBlockCopy,
        hide_answers: state.generator.publishHideAnswers !== false,
        questions: v.tasks.map((t) => ({
          num: t.num,
          part: t.part,
          type: t.type,
          topic: t.topic,
          section: t.section || null,
          text: t.text,
          answer: t.answer,
          solution: t.solution || null,
          max_score: t.maxScore,
          figure_kind: t.figureKind,
          figure_svg: t.figureSvg,
          solution_figure_svg: t.solutionFigureSvg,
          payload: t.payload || null,
          kim_order: !!t.kim_order,
          acceptable_answers: Array.isArray(t.acceptable_answers)
            ? t.acceptable_answers
            : Array.isArray(t.acceptableAnswers)
              ? t.acceptableAnswers
              : null,
        })),
      };
      if (allowed.length) body.allowed_students = allowed;
      if (deadlineAt) {
        body.deadline_at = deadlineAt;
        body.deadline = deadlineAt;
      }
      if (timeLimit) {
        body.time_limit_minutes = timeLimit;
        body.timer_minutes = timeLimit;
      }
      const data = await api("/api/assignments/publish", {
        method: "POST",
        body: JSON.stringify(body),
      });
      const workCode = data.code || v.code;
      const studentUrl = data.student_url || `/student?code=${workCode}`;
      state.generator.published.unshift({
        id: data.id || v.id,
        title: v.title,
        subject: v.subject,
        code: workCode,
        studentUrl,
        tasksCount: v.tasks.length,
        gradingMode: state.generator.gradingMode,
        deadlineAt: deadlineAt,
        timeLimitMinutes: timeLimit,
        shuffleVariants: shuffle,
        publishedAt: new Date().toISOString(),
      });
      markVariantPublished(v);
      state.generator.publishBusy = false;
      state.generator.publishSuccess = {
        code: workCode,
        title: v.title,
        studentUrl,
      };
      state.assignmentsBoard.loadedFor = null;
      render();
      loadAssignmentsBoard(true);
    } catch (err) {
      state.generator.publishBusy = false;
      render();
      showToast(err.message || "Не удалось выдать работу", "error");
    }
  });

  document.getElementById("toggle-png-answer")?.addEventListener("change", (e) => {
    ensureGeneratorExport().pngWithAnswer = !!e.target.checked;
    render();
  });

  document.getElementById("btn-close-link-qr")?.addEventListener("click", () => {
    state.generator.export.linkQrOpen = false;
    render();
  });
  document.getElementById("link-qr-backdrop")?.addEventListener("click", (e) => {
    if (e.target.id === "link-qr-backdrop") {
      state.generator.export.linkQrOpen = false;
      render();
    }
  });
  document.getElementById("btn-copy-share-link")?.addEventListener("click", () => copyShareLink(true));

  if (state.generator._autoStart && !state.generator.generating && !state.generator.variant) {
    state.generator._autoStart = false;
    startKimGenerate();
  }
}

async function copyShareLink(toast = true) {
  const url = variantShareUrl(state.generator.variant);
  try {
    await navigator.clipboard.writeText(url);
    if (toast) showToast("Ссылка скопирована", "success");
  } catch (_) {
    showToast("Не удалось скопировать ссылку", "error");
  }
}

async function exportPng() {
  const card = document.getElementById("export-preview-card");
  if (!card) return;

  const download = (dataUrl) => {
    const a = document.createElement("a");
    a.download = `${(state.generator.variant?.code || "variant").toLowerCase()}${
      state.generator.export.pngWithAnswer ? "-answers" : ""
    }.png`;
    a.href = dataUrl;
    a.click();
    showToast("PNG скачан", "success");
  };

  try {
    if (!window.html2canvas) {
      await loadScriptOnce("https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js");
    }
    const a4 = !!state.generator.export.a4Preview;
    const theme = state.generator.export.previewTheme;
    const canvas = await window.html2canvas(card, {
      backgroundColor: a4 || theme === "light" ? "#ffffff" : "#0b0f17",
      scale: 2,
      useCORS: true,
      logging: false,
    });
    download(canvas.toDataURL("image/png"));
  } catch (_) {
    // fallback: текстовый canvas, дроби уже как «числ⁄знам» (читаемее [[ ]])
    exportPngFallback();
  }
}

function toReadableMath(raw) {
  return polishFipiText(raw).replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "($1)⁄($2)");
}

function exportPngFallback() {
  const payload = exportPreviewPayload();
  if (!payload) return;
  const theme = state.generator.export.previewTheme;
  const w = 900;
  const h = 1200;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  const bg = theme === "light" ? "#f7f8fb" : "#0b0f17";
  const fg = theme === "light" ? "#111827" : "#f4f7fb";
  const muted = theme === "light" ? "#4b5563" : "#93a0b5";
  const accent = "#5eead4";

  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = accent;
  ctx.font = "800 22px Plus Jakarta Sans, sans-serif";
  ctx.fillText("EduSense", 48, 64);
  ctx.fillStyle = muted;
  ctx.font = "600 16px Plus Jakarta Sans, sans-serif";
  ctx.fillText(payload.badge, 48, 100);
  ctx.fillStyle = fg;
  ctx.font = "800 34px Plus Jakarta Sans, sans-serif";
  wrapCanvasText(ctx, payload.title, 48, 150, w - 96, 42);
  ctx.fillStyle = muted;
  ctx.font = "500 18px Plus Jakarta Sans, sans-serif";
  ctx.fillText(payload.meta, 48, 240);
  ctx.fillStyle = fg;
  ctx.font = "500 20px Plus Jakarta Sans, sans-serif";
  const bodyText = (payload.tasks || [])
    .map((t) => `№${t.num}. ${toReadableMath(t.text)}`)
    .join("\n\n");
  const bodyEnd = wrapCanvasText(ctx, bodyText, 48, 290, w - 96, 30);
  if (state.generator.export.pngWithAnswer) {
    const answerText = (payload.answers || [])
      .map((a) => `${a.num}) ${toReadableMath(a.answer)}`)
      .join("\n");
    ctx.fillStyle = theme === "light" ? "#eef2ff" : "#1a2236";
    ctx.fillRect(48, bodyEnd + 24, w - 96, 220);
    ctx.fillStyle = accent;
    ctx.font = "700 16px Plus Jakarta Sans, sans-serif";
    ctx.fillText("Ответ / ключ", 72, bodyEnd + 56);
    ctx.fillStyle = fg;
    ctx.font = "500 18px Plus Jakarta Sans, sans-serif";
    wrapCanvasText(ctx, answerText, 72, bodyEnd + 90, w - 144, 28);
  }

  const a = document.createElement("a");
  a.download = `${(state.generator.variant?.code || "variant").toLowerCase()}${
    state.generator.export.pngWithAnswer ? "-answers" : ""
  }.png`;
  a.href = canvas.toDataURL("image/png");
  a.click();
  showToast("PNG скачан", "success");
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const paragraphs = String(text || "").split("\n");
  let cursorY = y;
  for (const para of paragraphs) {
    const words = para.split(/\s+/).filter(Boolean);
    let line = "";
    for (const word of words) {
      const test = line ? `${line} ${word}` : word;
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line, x, cursorY);
        line = word;
        cursorY += lineHeight;
      } else {
        line = test;
      }
    }
    if (line) {
      ctx.fillText(line, x, cursorY);
      cursorY += lineHeight;
    }
    cursorY += lineHeight * 0.35;
  }
  return cursorY;
}

function exportPdf() {
  exportBrandedPdf({ keys: !!state.generator.export.pdfAnswerSheet });
}

function renderTeacherKeysPrintHtml(payload) {
  const tasks = Array.isArray(payload?.tasks) ? payload.tasks.slice() : [];
  tasks.sort((a, b) => Number(a.num || 0) - Number(b.num || 0));
  const part1 = tasks.filter((t) => Number(t.part) !== 2);
  const part2 = tasks.filter((t) => Number(t.part) === 2);
  const formatKey = (raw) =>
    typeof formatAnswerKey === "function" ? formatAnswerKey(raw, 1) : escapeHtml(String(raw || "—"));
  const p1Rows = part1
    .map((t) => {
      const ans = String(t.answer || "").trim();
      return `<tr>
        <th class="n">${escapeHtml(String(t.num))}</th>
        <td class="ans">${ans ? formatKey(ans) : "—"}</td>
        <td class="topic">${escapeHtml(topicLabelRu(t.topic || "") || t.topic || "")}</td>
      </tr>`;
    })
    .join("");
  const p1Table = p1Rows
    ? `<h2>Часть 1</h2>
      <table class="key-table">
        <thead><tr><th class="n">№</th><th>Ключ</th><th>Тема</th></tr></thead>
        <tbody>${p1Rows}</tbody>
      </table>`
    : "";
  const p2Cards = part2
    .map((t) => {
      const short = String(t.answer || "").trim();
      const sol = String(t.solution || "").trim();
      return `<article class="key-p2">
        <header><b>№${escapeHtml(String(t.num))}</b><span class="muted">${escapeHtml(
          topicLabelRu(t.topic || "") || t.topic || ""
        )}</span></header>
        ${short ? `<p class="key-short">Ответ: <strong>${formatKey(short)}</strong></p>` : ""}
        ${sol ? `<pre class="key-sol">${escapeHtml(sol)}</pre>` : `<p class="muted">Развёрнутый ответ</p>`}
      </article>`;
    })
    .join("");
  const p2Block = p2Cards ? `<h2>Часть 2</h2>${p2Cards}` : "";
  return `<div class="a4-sheet keys-sheet">
    ${eduSenseWatermarkHtml()}
    <div class="a4-inner">
      ${eduSenseBrandHtml("только для учителя")}
      <div class="ep-badge">Ключи и критерии проверки</div>
      <h1>КЛЮЧИ И КРИТЕРИИ ПРОВЕРКИ</h1>
      <p class="muted">${escapeHtml(payload.title || "Вариант")} · ${escapeHtml(payload.meta || "")}</p>
      ${p1Table}
      ${p2Block}
    </div>
  </div>`;
}


function solveShareUrl(code) {
  const origin = String(location.origin || "https://edusence.ru").replace(/\/$/, "");
  return `${origin}/solve?kim=${encodeURIComponent(String(code || "").toUpperCase())}`;
}

function printAssignmentSolveQr(code) {
  const c = String(code || "").trim().toUpperCase();
  if (!c) return;
  const url = solveShareUrl(c);
  const opened = openPrintWindow(
    `QR · ${c}`,
    `<div class="a4-sheet" style="min-height:auto;display:flex;align-items:center;justify-content:center;">
      ${eduSenseWatermarkHtml()}
      <div class="a4-inner" style="text-align:center;">
        ${eduSenseBrandHtml()}
        <h1>Код работы ${escapeHtml(c)}</h1>
        <p class="muted">Отсканируйте QR, чтобы открыть вариант в EduSense</p>
        <img alt="QR" src="${qrDataImage(url, 520)}" width="520" height="520" style="width:360px;height:360px;border:10px solid #0f172a;border-radius:18px;background:#fff;"/>
        <p class="muted" style="margin-top:14px;word-break:break-all">${escapeHtml(url)}</p>
      </div>
    </div>`,
    brandedExamPrintCss()
  );
  if (!opened) showToast("Разрешите всплывающие окна для печати QR", "error");
}

function pdfAnswerBlankHtml(payload) {
  const tasks = (payload?.tasks || []).filter((t) => Number(t.part) !== 2);
  const cells = tasks
    .map(
      (t) => `<div class="ans-blank-cell"><b>${escapeHtml(String(t.num))}</b><span></span></div>`
    )
    .join("");
  return `<div class="a4-sheet ans-blank-sheet">
    ${eduSenseWatermarkHtml()}
    <div class="a4-inner">
      ${eduSenseBrandHtml("бланк ответов")}
      <div class="ep-badge">Бланк ответов №1</div>
      <h1>Бланк ответов №1</h1>
      <p class="muted">${escapeHtml(payload?.title || "")} · запишите ответы в квадраты</p>
      <div class="ans-blank-grid">${cells || "<p class='muted'>Нет заданий части 1</p>"}</div>
    </div>
  </div>`;
}

function pdfProTeacherBannerHtml() {
  try {
    const name = state.user?.full_name || "";
    const contact = localStorage.getItem("edusense_teacher_contact") || "";
    const pro = JSON.parse(localStorage.getItem("edusense_pro_meta") || "null");
    if (!pro || !name) return "";
    return `<div class="pdf-pro-banner">Преподаватель: ${escapeHtml(name)}${
      contact ? ` | Контакты: ${escapeHtml(contact)}` : ""
    }</div>`;
  } catch (_) {
    return "";
  }
}

async function exportAssignmentPdf(code, { keys = false } = {}) {
  const c = String(code || "").trim().toUpperCase();
  if (!c) return;
  // Prefer current generator variant if same code; else fetch assignment
  let payload = null;
  if (state.generator?.variant && String(state.generator.variant.code || "").toUpperCase() === c) {
    payload = exportPreviewPayload();
  }
  if (!payload) {
    const data = await api(`/api/assignments/${encodeURIComponent(c)}`);
    const questions = Array.isArray(data.questions) ? data.questions : [];
    payload = {
      title: data.title || c,
      code: c,
      badge: "КИМ",
      meta: `${data.subject || state.classroom?.subject || ""} · ${c}`,
      tasks: questions.map((q) => ({
        num: q.num,
        part: q.part || 1,
        topic: q.topic || "",
        text: q.text || q.stem || "",
        answer: q.answer || q.key || "",
        solution: q.solution || "",
        maxScore: q.max_score || q.maxScore || 1,
      })),
    };
  }
  const includeKeys = !!keys;
  const qrUrl = solveShareUrl(c);
  const qrBlock = `<div class="pdf-qr-row"><img alt="QR" src="${qrDataImage(qrUrl, 180)}" width="120" height="120"/><div><b>Открыть в EduSense</b><p class="muted" style="margin:4px 0 0;word-break:break-all;font-size:.75rem">${escapeHtml(qrUrl)}</p></div></div>`;
  const studentInner = `<div class="a4-sheet es-print-page">
    ${eduSenseWatermarkHtml()}
    <div class="a4-inner">
      ${pdfProTeacherBannerHtml()}
      ${pdfExamHeaderHtml(payload)}
      ${qrBlock}
      ${renderExportTaskBlocks(payload.tasks, false, true)}
    </div>
  </div>${pdfAnswerBlankHtml(payload)}`;
  const keysBlock = includeKeys
    ? renderTeacherKeysPrintHtml(payload).replace(
        'class="a4-sheet keys-sheet"',
        'class="a4-sheet keys-sheet es-print-page es-print-keys"'
      )
    : "";
  const keysInner = includeKeys ? studentInner + keysBlock : studentInner;
  const filename = `${pdfSafeName(payload.title || c)}${includeKeys ? "-kluchi" : ""}.pdf`;
  const css =
    brandedExamPrintCss() +
    `
    .pdf-pro-banner{font-size:.85rem;font-weight:700;margin:0 0 10px;padding:8px 10px;border:1px solid #cbd5e1;background:#f8fafc;border-radius:8px}
    .pdf-qr-row{display:flex;gap:12px;align-items:center;margin:0 0 16px;padding:10px;border:1px dashed #cbd5e1;border-radius:10px}
    .ans-blank-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:12px}
    .ans-blank-cell{border:1px solid #94a3b8;border-radius:8px;min-height:64px;padding:6px;display:flex;flex-direction:column;gap:6px}
    .ans-blank-cell b{font-size:.8rem;color:#64748b}
    .ans-blank-cell span{flex:1;border:1px solid #e2e8f0;border-radius:4px;background:#fff}
    .pdf-exam-fields{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;margin:12px 0 8px}
    .pdf-exam-field{border-bottom:1px solid #cbd5e1;padding:6px 0;font-size:.9rem}
    .pdf-exam-field span{display:block;font-size:.72rem;color:#64748b;font-weight:700;margin-bottom:4px}
    .pdf-exam-field em{font-style:normal;letter-spacing:.08em}
  `;
  const runDownload = async () => {
    if (window.__pdfExportBusy) return;
    window.__pdfExportBusy = true;
    showPdfExportOverlay();
    try {
      await downloadHtmlAsPdf(payload.title, keysInner, css, filename);
      showToast(includeKeys ? "PDF с ключами скачан" : "PDF скачан", "success");
    } catch (_) {
      const opened = openPrintWindow(payload.title, keysInner, css);
      if (opened) showToast("Открыта печать — сохраните как PDF", "info");
      else showToast("Не удалось сформировать PDF", "error");
    } finally {
      window.__pdfExportBusy = false;
      closePdfExportOverlay();
    }
  };
  if (window.EduSensePrint?.isMobileViewport?.() && window.EduSensePrint?.openMobilePreview) {
    window.EduSensePrint.openMobilePreview({
      title: "Превью бланка A4",
      html: keysInner,
      css,
      onDownload: () => {
        window.EduSensePrint.closeMobilePreview();
        runDownload();
      },
      onPrint: () => {
        window.EduSensePrint.closeMobilePreview();
        const opened = openPrintWindow(payload.title, keysInner, css);
        if (!opened) showToast("Разрешите всплывающие окна для печати", "error");
      },
    });
    return;
  }
  await runDownload();
}


function exportBrandedPdf({ keys = false } = {}) {
  const payload = exportPreviewPayload();
  if (!payload) {
    showToast("Сначала сформируйте вариант", "error");
    return;
  }
  const code = payload.code || state.generator?.variant?.code || "";
  const qrUrl = code ? solveShareUrl(code) : "";
  const qrBlock = qrUrl
    ? `<div class="pdf-qr-row"><img alt="QR" src="${qrDataImage(qrUrl, 180)}" width="120" height="120"/><div><b>Открыть в EduSense</b><p class="muted" style="margin:4px 0 0;word-break:break-all;font-size:.75rem">${escapeHtml(qrUrl)}</p></div></div>`
    : "";
  const studentDoc = `<div class="a4-sheet es-print-page">
    ${eduSenseWatermarkHtml()}
    <div class="a4-inner">
      ${pdfProTeacherBannerHtml()}
      ${pdfExamHeaderHtml(payload)}
      ${qrBlock}
      ${renderExportTaskBlocks(payload.tasks, false, true)}
    </div>
  </div>${pdfAnswerBlankHtml(payload)}`;
  const keysBlock = keys
    ? renderTeacherKeysPrintHtml(payload).replace('class="a4-sheet keys-sheet"', 'class="a4-sheet keys-sheet es-print-page es-print-keys"')
    : "";
  const inner = keys ? studentDoc + keysBlock : studentDoc;
  const filename = `${pdfSafeName(payload.title || payload.code || "variant")}${
    keys ? "-kluchi" : ""
  }.pdf`;
  const css = brandedExamPrintCss();
  const runDownload = () => {
    if (window.__pdfExportBusy) return;
    window.__pdfExportBusy = true;
    showPdfExportOverlay();
    downloadHtmlAsPdf(payload.title, inner, css, filename)
      .then(() => showToast(keys ? "PDF с ключами скачан" : "PDF скачан", "success"))
      .catch(() => {
        const opened = openPrintWindow(
          keys ? `Ключи · ${payload.title}` : payload.title,
          inner,
          css
        );
        if (opened) showToast("Открыта печать — сохраните как PDF", "info");
        else showToast("Не удалось сформировать PDF", "error");
      })
      .finally(() => {
        window.__pdfExportBusy = false;
        closePdfExportOverlay();
      });
  };
  const runPrint = () => {
    const opened = openPrintWindow(
      keys ? `Ключи · ${payload.title}` : payload.title,
      inner,
      css
    );
    if (!opened) showToast("Разрешите всплывающие окна для печати", "error");
  };

  // Mobile: A4 preview modal first — avoid freezing / theme bleed
  if (window.EduSensePrint?.isMobileViewport?.() && window.EduSensePrint?.openMobilePreview) {
    window.EduSensePrint.openMobilePreview({
      title: "Превью бланка A4",
      html: inner,
      css,
      onDownload: () => {
        window.EduSensePrint.closeMobilePreview();
        runDownload();
      },
      onPrint: () => {
        window.EduSensePrint.closeMobilePreview();
        runPrint();
      },
    });
    return;
  }
  runDownload();
}

function printVariantQrBoard() {
  const variant = state.generator.variant;
  if (!variant) {
    showToast("Сначала сформируйте вариант", "error");
    return;
  }
  const url = variantShareUrl(variant);
  const code = variant.code || "";
  const opened = openPrintWindow(
    `QR · ${code || variant.title || "вариант"}`,
    `<div class="a4-sheet" style="min-height:auto;display:flex;align-items:center;justify-content:center;">
      ${eduSenseWatermarkHtml()}
      <div class="a4-inner" style="text-align:center;">
        ${eduSenseBrandHtml()}
        <h1>${escapeHtml(variant.title || "Вариант")}</h1>
        <p class="muted">QR для доски · отсканируйте, чтобы открыть работу</p>
        <img alt="QR" src="${qrDataImage(url, 520)}" width="520" height="520" style="width:360px;height:360px;border:10px solid #0f172a;border-radius:18px;background:#fff;"/>
        <p style="margin:22px 0 8px;font-family:ui-monospace,monospace;font-size:32px;font-weight:800;letter-spacing:.16em;">${escapeHtml(
          code
        )}</p>
        <p class="muted">${escapeHtml(url)}</p>
      </div>
    </div>`,
    brandedExamPrintCss()
  );
  if (opened) showToast("QR для доски готов к печати", "success");
}

async function submitCreate() {
  let name = state.form.name.trim();
  if (name.length < 2) {
    showToast("Введите название класса, например: 9-А Математика", "error");
    return;
  }
  if (!state.form.subject) {
    showToast("Выберите предмет", "error");
    return;
  }
  if (!state.user?.id) {
    showToast("Войдите как учитель, чтобы создать класс", "error");
    return;
  }

  syncFormDefaults();

  // Если ввели только «11» — соберём название из направления / класса / предмета
  if (/^\d{1,2}$/.test(name)) {
    name = `${examLabel(state.form.examType)} ${state.form.grade} · ${state.form.subject}`;
    state.form.name = name;
  }

  state.submitting = true;
  render();

  try {
    const classroom = await api("/api/classes", {
      method: "POST",
      body: JSON.stringify({
        name,
        exam_type: state.form.examType,
        grade: state.form.grade,
        subject: state.form.subject,
        teacher_id: state.user.id,
      }),
    });
    state.classroom = classroom;
    state.step = "code";
    state.showQr = false;
    state.generator.etalon = defaultEtalonForSubject(
      classroom.exam_type,
      classroom.subject
    );
    state.generator.examUi = "";
    localStorage.setItem("edusense_classroom", JSON.stringify(classroom));
    try {
      await refreshTeacherClasses();
      if (!state.classrooms.some((item) => item.id === classroom.id)) {
        state.classrooms = [classroom, ...state.classrooms];
      }
    } catch (_) {
      state.classrooms = [
        classroom,
        ...state.classrooms.filter((item) => item.id !== classroom.id),
      ];
    }
    showToast(
      hasExistingClasses() && state.classrooms.length > 1
        ? "Новая комната создана"
        : "Класс создан",
      "success"
    );
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    state.submitting = false;
    render();
  }
}

async function boot() {
  try {
    const p = String(location.pathname || "");
    if (/\/teacher\/analytics\/?$/i.test(p)) state.tab = "analytics";
    if (/\/teacher\/settings\/?$/i.test(p)) state.tab = "settings";
  } catch (_) {}

  let user = null;
  if (window.EduSenseAuth?.restore) {
    user = await window.EduSenseAuth.restore({ splash: true, requireToken: true });
  } else {
    user = loadUser();
  }
  if (!user || user.role !== "teacher") {
    window.location.href = "/#auth";
    return;
  }
  installFigureLightbox();
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setNavOpen(false);
  });
  if (typeof window !== "undefined" && window.EduSenseTG?.isTelegramMiniApp) {
    document.documentElement.classList.add("is-telegram-miniapp");
    document.body?.classList.add("is-telegram-miniapp");
  }
  state.user = user;
  syncFormDefaults();

  try {
    const list = await refreshTeacherClasses();
    const saved = JSON.parse(localStorage.getItem("edusense_classroom") || "null");
    const fromSaved =
      saved?.id && saved?.teacher_id === user.id
        ? list.find((item) => item.id === saved.id) || saved
        : null;
    const active = fromSaved || list[0] || null;
    if (active) {
      state.classroom = active;
      state.step = "dashboard";
      state.generator.etalon = defaultEtalonForSubject(
        active.exam_type,
        active.subject
      );
      state.generator.examUi = "";
      localStorage.setItem("edusense_classroom", JSON.stringify(active));
    } else {
      state.step = "create";
    }
  } catch (_) {
    /* remain on create */
  }

  render();
  if (state.step === "dashboard" && state.classroom?.access_code) {
    pageTransition(
      () => Promise.all([loadStudentsBoard(), loadAssignmentsBoard(), loadHomeInsights()]),
      { overlay: true }
    );
  }
}

document.addEventListener("DOMContentLoaded", boot);
