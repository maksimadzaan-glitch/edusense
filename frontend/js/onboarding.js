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
    if (user?.full_name) {
      localStorage.setItem(
        "edusense_last_account",
        JSON.stringify({
          id: user.id,
          full_name: user.full_name,
          role: user.role === "student" ? "student" : "teacher",
        })
      );
    }
  } catch (_) {}
  return user;
}

function readLastAccount() {
  if (window.EduSenseAuth?.getLastAccount) return window.EduSenseAuth.getLastAccount();
  try {
    const last = JSON.parse(localStorage.getItem("edusense_last_account") || "null");
    if (last && last.full_name) return last;
  } catch (_) {}
  return readStoredUser();
}

function initialsFromName(name) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function roleLabel(role) {
  return role === "student" ? "Ученик" : "Учитель";
}

function applySavedAccount(account, { focusPassword = true } = {}) {
  if (!account) return;
  selectRole(account.role === "student" ? "student" : "teacher");
  setAuthMode("login");
  const name = els.nameInput();
  const pass = els.passwordInput();
  if (name) name.value = account.full_name || "";
  if (pass) {
    pass.value = "";
    if (focusPassword) {
      requestAnimationFrame(() => pass.focus());
    }
  }
}

function hideSavedAccountCard() {
  const root = document.getElementById("saved-account");
  if (root) {
    root.hidden = true;
    root.innerHTML = "";
  }
}

function renderSavedAccountCard(account) {
  const root = document.getElementById("saved-account");
  if (!root || !account?.full_name) {
    hideSavedAccountCard();
    return;
  }
  const hasToken = !!(window.EduSenseAuth?.getToken?.() || "");
  root.hidden = false;
  root.innerHTML = `
    <div class="saved-account-row">
      <span class="saved-account-avatar" aria-hidden="true">${initialsFromName(account.full_name)}</span>
      <div class="saved-account-meta">
        <span class="saved-account-name">${escapeHtml(account.full_name)}</span>
        <span class="saved-account-role">${roleLabel(account.role)} · сохранённый аккаунт</span>
      </div>
    </div>
    <div class="saved-account-actions">
      <button type="button" class="btn btn-primary" id="saved-continue">
        ${hasToken ? "Продолжить" : "Войти снова"}
      </button>
      <button type="button" class="btn btn-ghost" id="saved-fill">Подставить имя</button>
    </div>
    <button type="button" class="saved-account-forget" id="saved-forget">Это не я — забыть аккаунт</button>
  `;

  document.getElementById("saved-continue")?.addEventListener("click", async () => {
    if (hasToken && window.EduSenseAuth?.restore) {
      const user = await window.EduSenseAuth.restore({ splash: true, requireToken: true });
      if (user && user.role) {
        window.location.href = studentDestForUser(user);
        return;
      }
    }
    applySavedAccount(account, { focusPassword: true });
    showToast("Введите пароль, чтобы войти", "info");
  });

  document.getElementById("saved-fill")?.addEventListener("click", () => {
    applySavedAccount(account, { focusPassword: true });
  });

  document.getElementById("saved-forget")?.addEventListener("click", () => {
    window.EduSenseAuth?.forgetAccount?.();
    window.EduSenseAuth?.clearSession?.({ forgetAccount: true });
    try {
      localStorage.removeItem("edusense_last_account");
      localStorage.removeItem("edusense_user");
      localStorage.removeItem("edusense_token");
    } catch (_) {}
    hideSavedAccountCard();
    const name = els.nameInput();
    const pass = els.passwordInput();
    if (name) name.value = "";
    if (pass) pass.value = "";
    showToast("Сохранённый аккаунт удалён", "info");
  });
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
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
  if (!els.launchBtn().disabled) els.launchLabel().textContent = launchLabelText();
}

function moveTabIndicator() {
  const indicator = els.tabIndicator();
  const active = authMode === "login" ? els.tabLogin() : els.tabRegister();
  if (!indicator || !active) return;
  indicator.style.width = `${active.offsetWidth}px`;
  indicator.style.transform = `translateX(${active.offsetLeft}px)`;
}

function setAuthMode(mode) {
  authMode = mode;
  els.tabLogin().classList.toggle("active", mode === "login");
  els.tabRegister().classList.toggle("active", mode === "register");
  els.tabLogin().setAttribute("aria-selected", mode === "login" ? "true" : "false");
  els.tabRegister().setAttribute("aria-selected", mode === "register" ? "true" : "false");
  moveTabIndicator();

  const btn = els.launchBtn();
  btn.classList.remove("is-success");
  els.launchLabel().textContent = launchLabelText();
  const pass = els.passwordInput();
  if (pass) {
    pass.minLength = mode === "register" ? 8 : 4;
    pass.placeholder = mode === "register" ? "Пароль · от 8 символов" : "Пароль";
  }
}

function togglePassword() {
  const input = els.passwordInput();
  const btn = document.getElementById("toggle-pass");
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  btn.setAttribute("aria-label", show ? "Скрыть пароль" : "Показать пароль");
  btn.innerHTML = show
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
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
  btn.classList.add("is-success");
  btn.disabled = true;
  els.launchLabel().textContent = "Готово";
}

async function handleLaunch(event) {
  event.preventDefault();

  const fullName = els.nameInput().value.trim();
  const password = els.passwordInput().value;

  if (fullName.length < 2) {
    showToast("Введите имя и фамилию", "error");
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
      /* Beta: без тура — сразу на главный экран */
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
    }, 600);
  } catch (err) {
    showToast(err.message, "error");
    setLaunchLoading(false);
  }
}

function handleTelegramLogin(event) {
  event.preventDefault();
  showToast("Вход через Telegram скоро будет доступен", "info");
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
  const onAuthHash = String(window.location.hash || "") === "#auth";

  if (!onLanding) {
    return;
  }

  if (params.get("leave") === "1") {
    try {
      // Soft logout: drop session, keep last account for “continue as”
      window.EduSenseAuth?.clearSession?.({ forgetAccount: false });
      localStorage.removeItem("edusense_user");
      localStorage.removeItem("edusense_token");
      localStorage.removeItem("edusense_student_entry");
      localStorage.removeItem("student_name");
      localStorage.removeItem("class_code");
      localStorage.removeItem("student_id");
      localStorage.removeItem("edusense_student_meta");
      localStorage.removeItem("edusense_student_home");
    } catch (_) {}
    history.replaceState(null, "", onAuthHash ? "/#auth" : "/");
  }

  let stored = null;
  if (window.EduSenseAuth?.restore) {
    stored = await window.EduSenseAuth.restore({ splash: !onAuthHash, requireToken: false });
  } else {
    stored = readStoredUser();
  }

  const hasToken = !!(window.EduSenseAuth?.getToken?.() || "");

  if (joinCode && stored && stored.role === "student" && hasToken) {
    window.location.replace(`/student?code=${encodeURIComponent(joinCode)}`);
    return;
  }
  if (!onAuthHash && !joinCode && stored && stored.role === "student" && hasToken) {
    window.location.replace("/student/dashboard");
    return;
  }
  if (!onAuthHash && !joinCode && stored && stored.role === "teacher" && hasToken) {
    window.location.replace("/teacher");
    return;
  }

  selectRole(params.get("role") === "student" || joinCode ? "student" : "teacher");
  setAuthMode(params.get("mode") === "register" ? "register" : "login");

  const last = readLastAccount();
  if (last?.full_name) {
    renderSavedAccountCard(last);
    // Prefill name so password managers / quick re-login work
    if (authMode === "login") {
      applySavedAccount(last, { focusPassword: onAuthHash || params.get("leave") === "1" });
    }
  }

  requestAnimationFrame(moveTabIndicator);
  window.addEventListener("resize", moveTabIndicator);

  els.roleTeacher().addEventListener("click", () => selectRole("teacher"));
  els.roleStudent().addEventListener("click", () => selectRole("student"));
  els.tabLogin().addEventListener("click", () => {
    setAuthMode("login");
    const again = readLastAccount();
    if (again?.full_name) renderSavedAccountCard(again);
  });
  els.tabRegister().addEventListener("click", () => {
    setAuthMode("register");
    hideSavedAccountCard();
  });

  document.getElementById("toggle-pass").addEventListener("click", togglePassword);
  document.getElementById("auth-form").addEventListener("submit", handleLaunch);
  document.getElementById("telegram-btn")?.addEventListener("click", handleTelegramLogin);
});
