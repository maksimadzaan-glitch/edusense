"use strict";

const API_BASE = "";

let selectedRole = "teacher";
let authMode = "login";

const els = {
  tabLogin: () => document.getElementById("tab-login"),
  tabRegister: () => document.getElementById("tab-register"),
  tabIndicator: () => document.getElementById("tab-indicator"),
  nameInput: () => document.getElementById("full-name"),
  passwordInput: () => document.getElementById("password"),
  launchBtn: () => document.getElementById("launch-btn"),
  launchLabel: () => document.getElementById("launch-label"),
  roleTeacher: () => document.getElementById("role-teacher"),
  roleStudent: () => document.getElementById("role-student"),
  toastRoot: () => document.getElementById("toast-root"),
  modeLabel: () => document.getElementById("auth-mode-label"),
  switchText: () => document.getElementById("auth-switch-text"),
  switchBtn: () => document.getElementById("auth-switch-btn"),
};

function showToast(message, type = "info") {
  const root = els.toastRoot();
  if (!root) return;
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => {
    el.classList.add("is-out");
    setTimeout(() => el.remove(), 240);
  }, 2800);
}

function launchLabelText() {
  if (authMode === "login") return "Войти";
  return selectedRole === "student" ? "Создать профиль ученика" : "Создать кабинет";
}

function joinCodeFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    return String(params.get("join") || params.get("code") || "").trim();
  } catch (_) {
    return "";
  }
}

function studentDestForUser(user) {
  if (!user || user.role !== "student") return "/teacher";
  const code = joinCodeFromUrl();
  if (code) return `/student?code=${encodeURIComponent(code)}`;
  return "/student/dashboard";
}

function readStoredUser() {
  if (window.EduSenseAuth?.getUser) return window.EduSenseAuth.getUser();
  try {
    const user = JSON.parse(localStorage.getItem("edusense_user") || "null");
    return user && typeof user === "object" ? user : null;
  } catch (_) {
    return null;
  }
}

function persistAuthUser(user) {
  if (window.EduSenseAuth?.saveSession) {
    return window.EduSenseAuth.saveSession(user, user?.access_token);
  }
  try {
    localStorage.setItem("edusense_user", JSON.stringify(user));
    if (user?.access_token) localStorage.setItem("edusense_token", user.access_token);
  } catch (_) {}
  return user;
}

function selectRole(role) {
  selectedRole = role;
  const teacher = els.roleTeacher();
  const student = els.roleStudent();
  if (!teacher || !student) return;
  teacher.classList.toggle("active", role === "teacher");
  student.classList.toggle("active", role === "student");
  teacher.setAttribute("aria-pressed", role === "teacher" ? "true" : "false");
  student.setAttribute("aria-pressed", role === "student" ? "true" : "false");
  const seg = teacher.closest(".seg");
  if (seg) seg.dataset.role = role;
  if (!els.launchBtn()?.disabled && els.launchLabel()) {
    els.launchLabel().textContent = launchLabelText();
  }
}

function syncAuthChrome() {
  const modeLabel = els.modeLabel();
  const switchText = els.switchText();
  const switchBtn = els.switchBtn();
  const roleSeg = document.querySelector(".seg[data-role], .card.auth .seg");
  if (modeLabel) {
    modeLabel.textContent = authMode === "login" ? "Вход в EduSense" : "Регистрация";
  }
  if (switchText && switchBtn) {
    if (authMode === "login") {
      switchText.textContent = "Нет аккаунта?";
      switchBtn.textContent = "Зарегистрироваться";
    } else {
      switchText.textContent = "Уже есть аккаунт?";
      switchBtn.textContent = "Войти";
    }
  }
  if (roleSeg) {
    roleSeg.hidden = authMode === "login";
    roleSeg.style.display = authMode === "login" ? "none" : "";
  }
  const name = els.nameInput();
  if (name) {
    name.placeholder =
      authMode === "register" ? "Имя и фамилия" : "Логин, email или телефон";
    const lab = document.querySelector('label[for="full-name"]');
    if (lab) {
      lab.textContent =
        authMode === "register" ? "Имя и фамилия" : "Логин / Email / Телефон";
    }
  }
}

function setAuthMode(mode) {
  authMode = mode === "register" ? "register" : "login";
  els.tabLogin()?.classList.toggle("active", authMode === "login");
  els.tabRegister()?.classList.toggle("active", authMode === "register");
  els.tabLogin()?.setAttribute("aria-selected", authMode === "login" ? "true" : "false");
  els.tabRegister()?.setAttribute("aria-selected", authMode === "register" ? "true" : "false");

  const btn = els.launchBtn();
  if (btn) btn.classList.remove("is-success");
  if (els.launchLabel()) els.launchLabel().textContent = launchLabelText();
  const pass = els.passwordInput();
  if (pass) {
    pass.minLength = authMode === "register" ? 8 : 4;
    pass.placeholder = authMode === "register" ? "Пароль · от 8 символов" : "Пароль";
    pass.autocomplete = authMode === "register" ? "new-password" : "current-password";
  }
  syncAuthChrome();
}

function togglePassword() {
  const input = els.passwordInput();
  const btn = document.getElementById("toggle-pass");
  if (!input || !btn) return;
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  btn.classList.toggle("is-on", show);
  btn.setAttribute("aria-label", show ? "Скрыть пароль" : "Показать пароль");
  btn.innerHTML = show
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 10.6a3 3 0 0 0 4.2 4.2"/><path d="M9.9 5.1A10.8 10.8 0 0 1 12 5c6.2 0 10 7 10 7a18.3 18.3 0 0 1-2.2 3.1"/><path d="M6.7 6.7C4.2 8.4 2.5 12 2.5 12S6.3 19 12 19c1.3 0 2.5-.3 3.6-.8"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>`;
}

async function apiRequest(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (_) {
    throw new Error("Не удалось подключиться к серверу. Запустите backend.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch (_) {}

  if (!response.ok) {
    const detail = data?.detail ?? `Ошибка ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function setLaunchLoading(loading) {
  const btn = els.launchBtn();
  const label = els.launchLabel();
  if (!btn || !label) return;
  if (loading) {
    btn.disabled = true;
    btn.classList.remove("is-success");
    label.innerHTML = `<span class="spinner"></span> Подождите…`;
  } else {
    btn.disabled = false;
    label.textContent = launchLabelText();
  }
}

function setLaunchSuccess() {
  const btn = els.launchBtn();
  if (!btn) return;
  btn.classList.add("is-success");
  btn.disabled = true;
  if (els.launchLabel()) els.launchLabel().textContent = "Готово";
}

async function handleLaunch(event) {
  event.preventDefault();

  const fullName = els.nameInput().value.trim();
  const password = els.passwordInput().value;

  if (fullName.length < 2) {
    showToast(authMode === "register" ? "Введите имя и фамилию" : "Введите логин", "error");
    return;
  }
  if (authMode === "register" && password.length < 8) {
    showToast("Пароль должен быть не короче 8 символов", "error");
    return;
  }
  if (authMode === "login" && password.length < 1) {
    showToast("Введите пароль", "error");
    return;
  }

  setLaunchLoading(true);
  try {
    let user;
    if (authMode === "register") {
      user = await apiRequest("/api/register", {
        full_name: fullName,
        password,
        role: selectedRole,
      });
      user.needs_onboarding = false;
      try {
        localStorage.removeItem("edusense_needs_tour");
      } catch (_) {}
      showToast(`Добро пожаловать, ${user.full_name}`, "success");
    } else {
      user = await apiRequest("/api/login", {
        full_name: fullName,
        password,
      });
      user.needs_onboarding = false;
      try {
        localStorage.removeItem("edusense_needs_tour");
      } catch (_) {}
      showToast(`С возвращением, ${user.full_name}`, "success");
    }

    persistAuthUser(user);
    setLaunchSuccess();

    setTimeout(() => {
      window.location.href = studentDestForUser(user);
    }, 450);
  } catch (err) {
    showToast(err.message, "error");
    setLaunchLoading(false);
  }
}

function handleTelegramLogin(event) {
  event.preventDefault();
  showToast("Вход через Telegram скоро будет доступен", "info");
}

function hardClearSession() {
  try {
    window.EduSenseAuth?.clearSession?.({ forgetAccount: true });
    localStorage.removeItem("edusense_user");
    localStorage.removeItem("edusense_token");
    localStorage.removeItem("edusense_last_account");
    localStorage.removeItem("edusense_student_entry");
    localStorage.removeItem("student_name");
    localStorage.removeItem("class_code");
    localStorage.removeItem("student_id");
    localStorage.removeItem("edusense_student_meta");
    localStorage.removeItem("edusense_student_home");
  } catch (_) {}
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const tg = window.EduSenseTG;
    if (tg && tg.isTelegramMiniApp) {
      const code = tg.entryCode || "";
      window.location.replace(code ? `/student?code=${encodeURIComponent(code)}` : "/student");
      return;
    }
  } catch {
    /* ignore */
  }

  const params = new URLSearchParams(window.location.search);
  const path = String(window.location.pathname || "").replace(/\/+$/, "") || "/";
  const onLanding = path === "/" || path.endsWith("/index.html");
  const joinCode = joinCodeFromUrl();
  const leaving = params.get("leave") === "1";

  if (!onLanding) return;

  if (leaving) {
    hardClearSession();
    history.replaceState(null, "", "/#auth");
  }

  // Auto-login: valid token → cabinet without showing form
  const token = window.EduSenseAuth?.getToken?.() || localStorage.getItem("edusense_token") || "";
  if (token && !leaving) {
    let stored = null;
    if (window.EduSenseAuth?.restore) {
      stored = await window.EduSenseAuth.restore({ splash: true, requireToken: true });
    } else {
      stored = readStoredUser();
    }
    if (stored && stored.role) {
      if (joinCode && stored.role === "student") {
        window.location.replace(`/student?code=${encodeURIComponent(joinCode)}`);
        return;
      }
      window.location.replace(studentDestForUser(stored));
      return;
    }
  }

  // Clean login form (no "Войти снова" / "Подставить имя")
  selectRole(params.get("role") === "student" || joinCode ? "student" : "teacher");
  setAuthMode(params.get("mode") === "register" ? "register" : "login");

  els.roleTeacher()?.addEventListener("click", () => selectRole("teacher"));
  els.roleStudent()?.addEventListener("click", () => selectRole("student"));
  document.getElementById("auth-switch-btn")?.addEventListener("click", () => {
    setAuthMode(authMode === "login" ? "register" : "login");
  });
  document.getElementById("forgot-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    showToast("Сброс пароля: напишите в поддержку EduSense или учителю класса.", "info");
  });
  document.getElementById("toggle-pass")?.addEventListener("click", togglePassword);
  document.getElementById("auth-form")?.addEventListener("submit", handleLaunch);
  document.getElementById("telegram-btn")?.addEventListener("click", handleTelegramLogin);

  if (String(window.location.hash || "") === "#auth") {
    document.getElementById("auth")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
});
