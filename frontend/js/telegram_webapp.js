/**
 * EduSense — Telegram Mini App bootstrap (safe without BotFather / token).
 * Loads only if telegram-web-app.js is present. No initData validation yet.
 */
(function (global) {
  "use strict";

  const HEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

  function getWebApp() {
    try {
      return global.Telegram && global.Telegram.WebApp ? global.Telegram.WebApp : null;
    } catch {
      return null;
    }
  }

  /** True when opened inside Telegram (initData / user / start_param). */
  function detectMiniApp(tg) {
    if (!tg) return false;
    try {
      if (tg.initData && String(tg.initData).length > 0) return true;
      const unsafe = tg.initDataUnsafe || {};
      if (unsafe.user || unsafe.receiver || unsafe.chat) return true;
      if (unsafe.start_param) return true;
      return false;
    } catch {
      return false;
    }
  }

  function safeHex(value) {
    if (!value || typeof value !== "string") return null;
    const v = value.trim();
    return HEX.test(v) ? v : null;
  }

  function applyTheme(tg) {
    const tp = (tg && tg.themeParams) || {};
    const root = document.documentElement;
    const map = [
      ["--tg-bg", tp.bg_color],
      ["--tg-text", tp.text_color],
      ["--tg-hint", tp.hint_color],
      ["--tg-button", tp.button_color],
      ["--tg-button-text", tp.button_text_color],
      ["--tg-secondary", tp.secondary_bg_color],
      ["--tg-link", tp.link_color],
    ];
    map.forEach(([cssVar, raw]) => {
      const hex = safeHex(raw);
      if (hex) root.style.setProperty(cssVar, hex);
    });

    // Light mapping onto EduSense tokens only when values look safe
    const bg = safeHex(tp.bg_color);
    const text = safeHex(tp.text_color);
    const hint = safeHex(tp.hint_color);
    const accent = safeHex(tp.button_color);
    if (bg) root.style.setProperty("--bg", bg);
    if (text) root.style.setProperty("--text", text);
    if (hint) root.style.setProperty("--muted", hint);
    if (accent) root.style.setProperty("--accent", accent);
  }

  function readEntryCode(tg) {
    try {
      const params = new URLSearchParams(global.location.search);
      const fromQuery = (params.get("code") || params.get("join") || "").trim();
      if (fromQuery) return fromQuery.toUpperCase();
    } catch {
      /* ignore */
    }
    try {
      const sp = tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param;
      if (sp) return String(sp).trim().toUpperCase();
    } catch {
      /* ignore */
    }
    return "";
  }

  const tg = getWebApp();
  const isTelegramMiniApp = detectMiniApp(tg);

  if (tg) {
    try {
      tg.ready();
      if (typeof tg.expand === "function") tg.expand();
      if (isTelegramMiniApp) applyTheme(tg);
      if (typeof tg.disableVerticalSwipes === "function") {
        try {
          tg.disableVerticalSwipes();
        } catch {
          /* older clients */
        }
      }
    } catch {
      /* ignore bootstrap errors outside Telegram */
    }
  }

  if (isTelegramMiniApp) {
    document.documentElement.classList.add("is-telegram-miniapp");
    document.body?.classList.add("is-telegram-miniapp");
  }

  function setMainButton({ text, visible, enabled, onClick }) {
    if (!tg || !tg.MainButton) return;
    try {
      if (text) tg.MainButton.setText(text);
      if (enabled === false) tg.MainButton.disable();
      else if (enabled === true) tg.MainButton.enable();
      if (typeof onClick === "function") {
        tg.MainButton.offClick?.(setMainButton._handler);
        setMainButton._handler = onClick;
        tg.MainButton.onClick(onClick);
      }
      if (visible) tg.MainButton.show();
      else tg.MainButton.hide();
    } catch {
      /* ignore */
    }
  }

  function hideMainButton() {
    setMainButton({ visible: false });
  }

  global.EduSenseTG = {
    webApp: tg,
    isTelegramMiniApp,
    entryCode: readEntryCode(tg),
    applyTheme: () => tg && applyTheme(tg),
    setMainButton,
    hideMainButton,
  };
})(typeof window !== "undefined" ? window : globalThis);
