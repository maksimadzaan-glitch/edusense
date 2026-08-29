/**
 * EduSense — brand mark + persistent auth session (localStorage).
 *
 * Keys:
 *  - edusense_token  — active session (cleared on logout / 401)
 *  - edusense_user   — current user while logged in
 *  - edusense_last_account — last account hint (kept after logout for “continue as”)
 */
(function (global) {
  "use strict";

  const LS_USER = "edusense_user";
  const LS_TOKEN = "edusense_token";
  const LS_LAST = "edusense_last_account";

  function markHtml() {
    return `<img src="/assets/edusense-mark-192.png?v=9" alt="" width="38" height="38" decoding="async"/>`;
  }

  function logoHtml(opts) {
    const o = opts || {};
    const href = o.href == null ? null : o.href;
    const compact = !!o.compact;
    const tag = href ? "a" : "div";
    const hrefAttr = href ? ` href="${href}"` : "";
    const extraClass = o.className ? ` ${o.className}` : "";
    return `
      <${tag} class="es-logo${compact ? " is-compact" : ""}${extraClass}"${hrefAttr} aria-label="EduSense">
        <span class="es-logo-mark" aria-hidden="true">${markHtml()}</span>
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

  function accountHint(user) {
    if (!user || typeof user !== "object") return null;
    const full_name = String(user.full_name || "").trim();
    if (!full_name) return null;
    const role = user.role === "student" ? "student" : "teacher";
    const hint = { full_name, role };
    if (user.id != null) hint.id = user.id;
    return hint;
  }

  function rememberAccount(user) {
    const hint = accountHint(user);
    if (!hint) return null;
    try {
      localStorage.setItem(LS_LAST, JSON.stringify(hint));
    } catch {
      /* ignore */
    }
    return hint;
  }

  function getLastAccount() {
    try {
      const last = JSON.parse(localStorage.getItem(LS_LAST) || "null");
      if (last && typeof last === "object" && String(last.full_name || "").trim()) {
        return {
          id: last.id,
          full_name: String(last.full_name).trim(),
          role: last.role === "student" ? "student" : "teacher",
        };
      }
    } catch {
      /* ignore */
    }
    // Fallback: still-logged-in user, or legacy user without token
    return accountHint(getUser());
  }

  function forgetAccount() {
    try {
      localStorage.removeItem(LS_LAST);
    } catch {
      /* ignore */
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
    rememberAccount(clean);
    return clean;
  }

  /**
   * End active session.
   * @param {{ forgetAccount?: boolean }} [opts] — forgetAccount:true wipes “continue as”
   */
  function clearSession(opts) {
    const forget = !!(opts && opts.forgetAccount);
    const last = forget ? null : getLastAccount() || accountHint(getUser());
    try {
      localStorage.removeItem(LS_TOKEN);
      localStorage.removeItem(LS_USER);
      if (forget) localStorage.removeItem(LS_LAST);
      else if (last) localStorage.setItem(LS_LAST, JSON.stringify(last));
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
        // Token dead — keep last account for “continue as”, drop active session
        clearSession({ forgetAccount: false });
        return null;
      }
      if (!res.ok) {
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
    LS_LAST,
    getToken,
    getUser,
    getLastAccount,
    rememberAccount,
    forgetAccount,
    saveSession,
    clearSession,
    authHeaders,
    showSplash,
    hideSplash,
    restore,
    logoHtml,
  };
})(window);
