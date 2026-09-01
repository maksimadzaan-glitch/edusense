"use strict";

const LS_NOTIFY = "edusense_notify_prefs";
const LS_AVATAR = "edusense_avatar_data";
const LS_PRO = "edusense_pro_meta";

function toast(msg, type) {
  const root = document.getElementById("toast-root");
  if (!root) return;
  const el = document.createElement("div");
  el.className = `toast ${type || "info"}`;
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(() => { el.classList.add("is-out"); setTimeout(() => el.remove(), 240); }, 2800);
}

function initials(name) {
  const p = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!p.length) return "?";
  if (p.length === 1) return p[0].slice(0, 2).toUpperCase();
  return (p[0][0] + p[p.length - 1][0]).toUpperCase();
}

function readNotify() {
  try { return JSON.parse(localStorage.getItem(LS_NOTIFY) || "{}") || {}; } catch { return {}; }
}
function saveNotify(v) {
  try { localStorage.setItem(LS_NOTIFY, JSON.stringify(v)); } catch {}
}
function readAvatar() {
  try { return localStorage.getItem(LS_AVATAR) || ""; } catch { return ""; }
}
function readPro() {
  try { return JSON.parse(localStorage.getItem(LS_PRO) || "null"); } catch { return null; }
}

let tab = "profile";
let user = null;

async function api(path, opts) {
  const headers = Object.assign(
    { "Content-Type": "application/json", Accept: "application/json" },
    window.EduSenseAuth?.authHeaders ? window.EduSenseAuth.authHeaders({}) : {}
  );
  const res = await fetch(path, Object.assign({}, opts || {}, { headers: Object.assign(headers, (opts && opts.headers) || {}) }));
  let data = null;
  try { data = await res.json(); } catch {}
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : "Ошибка запроса");
  }
  return data;
}

function backHref() {
  if (!user) return "/";
  return user.role === "student" ? "/student/dashboard" : "/teacher";
}

function render() {
  const app = document.getElementById("settings-app");
  const back = document.getElementById("settings-back");
  if (back) back.href = backHref();
  if (!app || !user) return;
  const notify = readNotify();
  const avatar = readAvatar();
  const pro = readPro() || { plan: "Бесплатный", until: null };
  const tabs = [
    ["profile", "Личные данные"],
    ["notify", "Уведомления"],
    ["security", "Безопасность"],
    ["pro", "Подписка PRO"],
  ];
  let body = "";
  if (tab === "profile") {
    body = `
      <section class="settings-card">
        <h2>Личные данные</h2>
        <p class="lead">Обновите ФИО, предмет по умолчанию и аватар профиля.</p>
        <div class="settings-avatar" id="avatar-preview">${avatar ? `<img src="${avatar}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:18px"/>` : initials(user.full_name)}</div>
        <label class="settings-field"><span>ФИО</span><input id="set-name" value="${escapeHtml(user.full_name || "")}" maxlength="100"/></label>
        <label class="settings-field"><span>Роль</span>
          <select id="set-role" disabled>
            <option value="teacher" ${user.role === "teacher" ? "selected" : ""}>Учитель</option>
            <option value="student" ${user.role === "student" ? "selected" : ""}>Ученик</option>
          </select>
        </label>
        <label class="settings-field"><span>Предмет по умолчанию</span>
          <select id="set-subject">
            <option value="">Не выбран</option>
            <option value="Математика" ${user.subject === "Математика" ? "selected" : ""}>Математика</option>
            <option value="Русский язык" ${/русск/i.test(user.subject || "") ? "selected" : ""}>Русский язык</option>
          </select>
        </label>
        <label class="settings-field"><span>Аватар (изображение)</span><input id="set-avatar" type="file" accept="image/*"/></label>
        <label class="settings-field"><span>Телефон / Telegram для шапки PDF (PRO)</span><input id="set-contact" placeholder="+7… или @username" value="${escapeHtml(user.contact || localStorage.getItem("edusense_teacher_contact") || "")}"/></label>
        <div class="settings-actions">
          <button type="button" class="btn btn-primary" id="btn-save-profile">Сохранить</button>
        </div>
      </section>`;
  } else if (tab === "notify") {
    body = `
      <section class="settings-card">
        <h2>Уведомления</h2>
        <p class="lead">Выберите каналы оповещений о сдаче работ и статусе класса.</p>
        <label class="settings-check"><input type="checkbox" id="n-tg" ${notify.telegram ? "checked" : ""}/> Уведомлять о сдаче работ в Telegram</label>
        <label class="settings-check"><input type="checkbox" id="n-email" ${notify.email ? "checked" : ""}/> Уведомлять о сдаче работ по Email</label>
        <label class="settings-check"><input type="checkbox" id="n-live" ${notify.live !== false ? "checked" : ""}/> Звук при сдаче на панели живой сессии</label>
        <div class="settings-actions"><button type="button" class="btn btn-primary" id="btn-save-notify">Сохранить</button></div>
      </section>`;
  } else if (tab === "security") {
    body = `
      <section class="settings-card">
        <h2>Безопасность</h2>
        <p class="lead">Смена пароля учётной записи EduSense.</p>
        <label class="settings-field"><span>Текущий пароль</span><input id="pw-old" type="password" autocomplete="current-password"/></label>
        <label class="settings-field"><span>Новый пароль</span><input id="pw-new" type="password" autocomplete="new-password" minlength="8"/></label>
        <label class="settings-field"><span>Повтор нового пароля</span><input id="pw-new2" type="password" autocomplete="new-password" minlength="8"/></label>
        <div class="settings-actions"><button type="button" class="btn btn-primary" id="btn-save-pw">Сменить пароль</button></div>
      </section>`;
  } else {
    body = `
      <section class="settings-card">
        <h2>Подписка PRO</h2>
        <p class="lead">Тариф, срок действия и управление подпиской.</p>
        <div class="settings-pro-box">
          <strong>Текущий тариф:</strong> ${escapeHtml(pro.plan || "Бесплатный")}<br/>
          <strong>Действует до:</strong> ${escapeHtml(pro.until || "—")}<br/>
          <p style="margin:10px 0 0;color:#cbd5e1;font-size:.9rem">PRO открывает персональный карантин ошибок, расширенную аналитику и шапку преподавателя в PDF.</p>
        </div>
        <div class="settings-actions">
          <button type="button" class="btn btn-primary" id="btn-manage-pro">Управлять подпиской</button>
        </div>
      </section>`;
  }
  app.innerHTML = `
    <div class="settings-tabs" role="tablist">
      ${tabs.map(([id, label]) => `<button type="button" class="settings-tab ${tab === id ? "is-active" : ""}" data-tab="${id}">${label}</button>`).join("")}
    </div>
    ${body}`;
  bind();
}

function escapeHtml(s) {
  return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function bind() {
  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => { tab = btn.getAttribute("data-tab"); render(); });
  });
  document.getElementById("btn-save-profile")?.addEventListener("click", async () => {
    try {
      const full_name = document.getElementById("set-name").value.trim();
      const subject = document.getElementById("set-subject").value;
      const contact = document.getElementById("set-contact").value.trim();
      const updated = await api("/api/auth/profile", { method: "PATCH", body: JSON.stringify({ full_name, subject: subject || null }) });
      user = window.EduSenseAuth.saveSession(updated, updated.access_token || window.EduSenseAuth.getToken());
      try { localStorage.setItem("edusense_teacher_contact", contact); } catch {}
      toast("Профиль сохранён", "success");
      render();
    } catch (e) { toast(e.message, "error"); }
  });
  document.getElementById("set-avatar")?.addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try { localStorage.setItem(LS_AVATAR, String(reader.result || "")); } catch {}
      toast("Аватар обновлён на этом устройстве", "success");
      render();
    };
    reader.readAsDataURL(file);
  });
  document.getElementById("btn-save-notify")?.addEventListener("click", () => {
    saveNotify({
      telegram: !!document.getElementById("n-tg")?.checked,
      email: !!document.getElementById("n-email")?.checked,
      live: !!document.getElementById("n-live")?.checked,
    });
    toast("Настройки уведомлений сохранены", "success");
  });
  document.getElementById("btn-save-pw")?.addEventListener("click", async () => {
    const old_password = document.getElementById("pw-old").value;
    const new_password = document.getElementById("pw-new").value;
    const again = document.getElementById("pw-new2").value;
    if (new_password.length < 8) return toast("Новый пароль — не короче 8 символов", "error");
    if (new_password !== again) return toast("Пароли не совпадают", "error");
    try {
      await api("/api/auth/password", { method: "POST", body: JSON.stringify({ old_password, new_password }) });
      toast("Пароль изменён", "success");
      document.getElementById("pw-old").value = "";
      document.getElementById("pw-new").value = "";
      document.getElementById("pw-new2").value = "";
    } catch (e) { toast(e.message, "error"); }
  });
  document.getElementById("btn-manage-pro")?.addEventListener("click", () => {
    toast("Управление подпиской PRO скоро будет доступно", "info");
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const token = window.EduSenseAuth?.getToken?.();
  if (!token) {
    location.replace("/#auth");
    return;
  }
  user = await window.EduSenseAuth.restore({ splash: true, requireToken: true });
  if (!user) {
    location.replace("/#auth");
    return;
  }
  render();
});
