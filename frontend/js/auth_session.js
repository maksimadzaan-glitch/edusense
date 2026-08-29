/**
 * EduSense — brand mark + persistent auth session (localStorage only).
 */
(function (global) {
  "use strict";

  const LS_USER = "edusense_user";
  const LS_TOKEN = "edusense_token";

  function logoHtml(opts) {
    const o = opts || {};
    const href = o.href == null ? null : o.href;
    const compact = !!o.compact;
    const tag = href ? "a" : "div";
    const hrefAttr = href ? ` href="${href}"` : "";
    const extraClass = o.className ? ` ${o.className}` : "";
    return `
      <${tag} class="es-logo${compact ? " is-compact" : ""}${extraClass}"${hrefAttr} aria-label="EduSense">
        <span class="es-logo-mark" aria-hidden="true">
          E
          <span class="es-logo-pulse"></span>
        </span>
        <span class="es-logo-text">
          <span class="es-logo-name">EduSense</span>
          <span class="es-logo-beta">BETA</span>
        </span>
      </${tag}>
    `;
  }

  function getToken() {
    try {
      return String(localStorage.getItem(LS_TOKEN) || "").trim();
    } catch {
      return "";
    }
  }

  function getUser() {
    try {
      const user = JSON.parse(localStorage.getItem(LS_USER) || "null");
      return user && typeof user === "object" ? user : null;
    } catch {
      return null;
    }
  }

  function saveSession(user, token) {
    const clean = { ...(user || {}) };
    const access = token || clean.access_token || "";
    delete clean.access_token;
    try {
      localStorage.setItem(LS_USER, JSON.stringify(clean));
      if (access) localStorage.setItem(LS_TOKEN, access);
    } catch {
      /* ignore quota */
    }
    return clean;
  }

  function clearSession() {
    try {
      localStorage.removeItem(LS_TOKEN);
      localStorage.removeItem(LS_USER);
    } catch {
      /* ignore */
    }
  }

  function authHeaders(extra) {
    const headers = { ...(extra || {}) };
    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
      headers["X-EduSense-Token"] = token;
    }
    return headers;
  }

  function showSplash() {
    if (document.getElementById("es-auth-splash")) return;
    document.documentElement.classList.add("es-auth-loading");
    const el = document.createElement("div");
    el.id = "es-auth-splash";
    el.className = "es-auth-splash";
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.innerHTML = `
      <div class="es-auth-splash-card">
        ${logoHtml({ className: "es-auth-splash-brand" })}
        <div class="es-auth-splash-ring" aria-hidden="true"></div>
        <p class="es-auth-splash-label">Проверяем сессию…</p>
      </div>
    `;
    document.body.appendChild(el);
  }

  function hideSplash() {
    document.getElementById("es-auth-splash")?.remove();
    document.documentElement.classList.remove("es-auth-loading");
  }

  /**
   * Restore session from localStorage token via /api/auth/me.
   * @returns {Promise<object|null>} user or null
   */
  async function restore({ splash = true, requireToken = true } = {}) {
    const token = getToken();
    if (!token) {
      if (requireToken) return null;
      return getUser();
    }
    if (splash) showSplash();
    try {
      const res = await fetch("/api/auth/me", {
        method: "GET",
        headers: authHeaders({ Accept: "application/json" }),
        cache: "no-store",
      });
      if (res.status === 401) {
        clearSession();
        return null;
      }
      if (!res.ok) {
        // Сеть/5xx — не выкидываем: оставляем локального пользователя
        return getUser();
      }
      const data = await res.json();
      return saveSession(data, data.access_token || token);
    } catch {
      return getUser();
    } finally {
      if (splash) hideSplash();
    }
  }

  global.EduSenseBrand = { logoHtml };
  global.EduSenseAuth = {
    LS_USER,
    LS_TOKEN,
    getToken,
    getUser,
    saveSession,
    clearSession,
    authHeaders,
    showSplash,
    hideSplash,
    restore,
    logoHtml,
  };
})(window);
