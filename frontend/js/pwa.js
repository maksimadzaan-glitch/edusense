/**
 * Баннер установки: один клик через системный запрос браузера,
 * иначе — ссылка на страницу с пошаговой инструкцией. Без оверлея.
 */
(function (global) {
  "use strict";

  var BANNER_KEY = "edusense_install_banner_v4";
  var MARK = "/assets/edusense-mark-192.png";
  var GUIDE = "/install";

  var deferredPrompt = global.__edusenseBip || null;

  global.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    paint();
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
    return !!(global.EduSenseTG && global.EduSenseTG.isTelegramMiniApp);
  }
  function detectName() {
    var ua = String(navigator.userAgent || "");
    if (/iPhone|iPad|iPod/i.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)) return "iPhone";
    if (/Android/i.test(ua)) return "Android";
    if (/Mac/i.test(ua)) return "Mac";
    if (/YaBrowser|Yowser/i.test(ua)) return "Яндекс Браузер";
    if (/Windows/i.test(ua)) return "Windows";
    return "компьютер";
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
        if (res && res.outcome === "accepted") {
          lsSet(BANNER_KEY, "1");
        }
        paint();
      })
      .catch(paint);
  }

  function paint() {
    if (!document.body) return;
    var leftover = document.getElementById("pwa-guide-dialog");
    if (leftover) leftover.remove();
    var root = rootEl();
    if (inStandalone() || inTelegram() || lsGet(BANNER_KEY) === "1") {
      root.hidden = true;
      root.innerHTML = "";
      return;
    }
    if (document.documentElement.classList.contains("tour-on") ||
        document.documentElement.classList.contains("exam-on") ||
        document.querySelector(".work-focus")) {
      root.hidden = true;
      root.innerHTML = "";
      return;
    }
    var oneClick = !!deferredPrompt;
    root.hidden = false;
    root.innerHTML =
      '<div class="pwa-banner" role="region" aria-label="Установить приложение">' +
      '<img class="pwa-banner-mark" src="' + MARK + '" alt="" width="48" height="48" />' +
      '<div class="pwa-banner-copy"><strong>Установите приложение EduSense</strong>' +
      "<span>Сейчас у вас: " + detectName() + ". " +
      (oneClick ? "Один клик — и значок сохранится." : "Откроется страница с шагами.") +
      "</span></div>" +
      '<a class="pwa-banner-install" id="pwa-banner-cta" href="' + GUIDE + '">' +
      (oneClick ? "Установить" : "Как установить") +
      "</a>" +
      '<button type="button" class="pwa-banner-close" id="pwa-banner-x" aria-label="Закрыть">✕</button>' +
      "</div>";
    var x = document.getElementById("pwa-banner-x");
    if (x) {
      x.onclick = function () {
        lsSet(BANNER_KEY, "1");
        paint();
      };
    }
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
    /* Beta: SW off — offline page masked real server hangs on mobile/Yandex. */
    if (!("serviceWorker" in navigator) || inTelegram()) {
      killSw();
      return;
    }
    killSw();
  }

  function hideInstallLinks(hide) {
    document.querySelectorAll("[data-pwa-install]").forEach(function (el) {
      el.hidden = hide;
    });
  }

  function boot() {
    registerSw();
    hideInstallLinks(inStandalone() || inTelegram());
    paint();
  }

  /* Любая ссылка «установить» ставит приложение сразу, пока браузер это разрешает.
     Делегирование нужно из-за сайдбаров, которые перерисовываются на ходу. */
  document.addEventListener("click", function (e) {
    if (!deferredPrompt || !e.target || !e.target.closest) return;
    if (e.target.closest('a[href="' + GUIDE + '"], #pwa-nav-btn')) install(e);
  });

  global.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    lsSet(BANNER_KEY, "1");
    paint();
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
      paint();
    },
  };
})(typeof window !== "undefined" ? window : this);
