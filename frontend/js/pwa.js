/**
 * PWA helpers. Bottom install banner is disabled (beta UX).
 * Manual install stays on /install and header link (desktop).
 */
(function (global) {
  "use strict";

  var BANNER_KEY = "edusense_install_banner_v5";
  var GUIDE = "/install";
  /** Beta: never auto-show bottom install banner */
  var AUTO_BANNER = false;

  var deferredPrompt = global.__edusenseBip || null;

  global.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
  });

  function lsGet(key) {
    try {
      return global.localStorage.getItem(key);
    } catch (_) {
      return null;
    }
  }
  function lsSet(key, val) {
    try {
      global.localStorage.setItem(key, val);
    } catch (_) {}
  }
  function inStandalone() {
    return global.matchMedia("(display-mode: standalone)").matches || global.navigator.standalone === true;
  }
  function inTelegram() {
    try {
      if (global.EduSenseTG && global.EduSenseTG.isTelegramMiniApp) return true;
      var tg = global.Telegram && global.Telegram.WebApp;
      if (!tg) return false;
      if (tg.initData || tg.initDataUnsafe) return true;
      if (typeof tg.platform === "string" && tg.platform !== "unknown") return true;
    } catch (_) {}
    return false;
  }
  function isMobile() {
    try {
      if (global.matchMedia && global.matchMedia("(max-width: 720px)").matches) return true;
    } catch (_) {}
    return /Android|iPhone|iPad|iPod|Mobile/i.test(String(navigator.userAgent || ""));
  }

  function rootEl() {
    var root = document.getElementById("pwa-install-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "pwa-install-root";
      document.body.appendChild(root);
    }
    return root;
  }

  function hideBanner() {
    var root = rootEl();
    root.hidden = true;
    root.innerHTML = "";
    var leftover = document.getElementById("pwa-guide-dialog");
    if (leftover) leftover.remove();
  }

  function install(e) {
    if (!deferredPrompt) return;
    if (e) e.preventDefault();
    var bip = deferredPrompt;
    deferredPrompt = null;
    try {
      bip.prompt();
    } catch (_) {
      deferredPrompt = bip;
      return;
    }
    bip.userChoice
      .then(function (res) {
        if (res && res.outcome === "accepted") lsSet(BANNER_KEY, "1");
        hideBanner();
      })
      .catch(hideBanner);
  }

  function paint() {
    /* Auto bottom banner off: mobile / Telegram / beta */
    if (!AUTO_BANNER || inStandalone() || inTelegram() || isMobile() || lsGet(BANNER_KEY) === "1") {
      hideBanner();
      return;
    }
    hideBanner();
  }

  function killSw() {
    if (!("serviceWorker" in navigator)) return Promise.resolve();
    return navigator.serviceWorker
      .getRegistrations()
      .then(function (regs) {
        return Promise.all(
          regs.map(function (r) {
            return r.unregister();
          })
        );
      })
      .then(function () {
        if (!("caches" in global)) return;
        return caches.keys().then(function (keys) {
          return Promise.all(
            keys.map(function (k) {
              return caches.delete(k);
            })
          );
        });
      })
      .catch(function () {});
  }

  function registerSw() {
    killSw();
  }

  function hideInstallLinks(hide) {
    document.querySelectorAll("[data-pwa-install], #pwa-nav-btn, .sidebar-install").forEach(function (el) {
      if (hide) el.setAttribute("hidden", "");
      else if (!el.classList.contains("pwa-nav-btn")) el.removeAttribute("hidden");
    });
    /* Header install: hide on Telegram always; CSS handles tiny screens */
    var nav = document.getElementById("pwa-nav-btn");
    if (nav && (hide || inTelegram())) nav.setAttribute("hidden", "");
  }

  function boot() {
    registerSw();
    hideInstallLinks(inStandalone() || inTelegram());
    hideBanner();
    document.documentElement.classList.toggle("is-telegram-miniapp", inTelegram());
    document.body && document.body.classList.toggle("is-telegram-miniapp", inTelegram());
  }

  document.addEventListener("click", function (e) {
    if (!deferredPrompt || !e.target || !e.target.closest) return;
    if (e.target.closest('a[href="' + GUIDE + '"], #pwa-nav-btn')) install(e);
  });

  global.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    lsSet(BANNER_KEY, "1");
    hideBanner();
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  global.EduSensePWA = {
    canInstall: function () {
      return !!deferredPrompt;
    },
    prompt: function () {
      if (deferredPrompt) install(null);
      else global.location.href = GUIDE;
    },
    next: function () {
      global.location.href = GUIDE;
    },
    sync: function () {
      hideInstallLinks(inStandalone() || inTelegram());
      hideBanner();
    },
  };
})(typeof window !== "undefined" ? window : this);
