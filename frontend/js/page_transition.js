/**
 * EduSense — top-bar progress + page spinner for SPA tabs and full-page navigation.
 */
(function (global) {
  "use strict";

  const SS_KEY = "edusense_pt_nav";
  const REDUCE = global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NAV_SEL =
    'a[href], [data-tab], [data-quick], [data-tab-jump], .nav-item, button[data-nav-action]';

  let depth = 0;
  let overlayWanted = false;
  let barEl = null;
  let overlayEl = null;
  let trickleTimer = null;
  let progress = 0;

  function ensureBar() {
    if (barEl) return;
    barEl = document.createElement("div");
    barEl.id = "page-progress";
    barEl.className = "page-progress";
    barEl.setAttribute("role", "progressbar");
    barEl.setAttribute("aria-valuemin", "0");
    barEl.setAttribute("aria-valuemax", "100");
    barEl.innerHTML =
      '<div class="page-progress-track"><div class="page-progress-bar"><span class="page-progress-peg"></span></div></div>';
    document.body.appendChild(barEl);
  }

  function ensureOverlay() {
    if (overlayEl) return;
    overlayEl = document.createElement("div");
    overlayEl.id = "page-spinner-overlay";
    overlayEl.className = "page-spinner-overlay";
    overlayEl.setAttribute("aria-hidden", "true");
    overlayEl.innerHTML = `
      <div class="page-spinner-panel" role="status" aria-live="polite">
        <div class="page-spinner-ring" aria-hidden="true"></div>
        <p class="page-spinner-label">Загрузка...</p>
      </div>`;
    document.body.appendChild(overlayEl);
  }

  function setProgress(value) {
    progress = Math.max(0, Math.min(1, value));
    if (!barEl) return;
    const pct = Math.round(progress * 100);
    barEl.style.setProperty("--pp", String(progress));
    barEl.setAttribute("aria-valuenow", String(pct));
    barEl.classList.toggle("is-active", progress > 0 && progress < 1);
    barEl.classList.toggle("is-done", progress >= 1);
  }

  function startTrickle() {
    stopTrickle();
    if (REDUCE) return;
    trickleTimer = global.setInterval(() => {
      if (progress < 0.92) setProgress(progress + (0.92 - progress) * 0.1);
    }, 180);
  }

  function stopTrickle() {
    if (trickleTimer) {
      global.clearInterval(trickleTimer);
      trickleTimer = null;
    }
  }

  function syncBusy() {
    document.documentElement.classList.toggle("nav-busy", depth > 0);
  }

  function start(opts = {}) {
    depth += 1;
    if (opts.overlay) overlayWanted = true;
    ensureBar();
    barEl.classList.add("is-visible");
    if (overlayWanted) {
      ensureOverlay();
      overlayEl.classList.add("is-visible");
      overlayEl.setAttribute("aria-hidden", "false");
      document.documentElement.classList.add("page-spinner-open");
    }
    if (progress < 0.08) setProgress(0.08);
    startTrickle();
    syncBusy();
  }

  function done() {
    if (depth <= 0) return;
    depth -= 1;
    if (depth > 0) return;
    stopTrickle();
    setProgress(1);
    syncBusy();
    global.setTimeout(() => {
      if (depth > 0) return;
      setProgress(0);
      barEl?.classList.remove("is-visible", "is-done", "is-active");
      overlayEl?.classList.remove("is-visible");
      overlayEl?.setAttribute("aria-hidden", "true");
      overlayWanted = false;
      document.documentElement.classList.remove("page-spinner-open");
      syncBusy();
    }, REDUCE ? 0 : 320);
  }

  function isBusy() {
    return depth > 0;
  }

  async function run(fn, opts = {}) {
    if (isBusy() && opts.skipIfBusy) return undefined;
    start(opts);
    const started = Date.now();
    try {
      return await fn();
    } finally {
      const minMs = Number(opts.minMs) || 0;
      const elapsed = Date.now() - started;
      if (minMs > elapsed) {
        await new Promise((r) => global.setTimeout(r, minMs - elapsed));
      }
      done();
    }
  }

  function isInternalNavLink(anchor) {
    if (!anchor || anchor.target === "_blank" || anchor.hasAttribute("download")) return false;
    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) {
      return false;
    }
    try {
      const url = new URL(href, global.location.href);
      if (url.origin !== global.location.origin) return false;
      if (
        url.pathname === global.location.pathname &&
        url.search === global.location.search &&
        url.hash
      ) {
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  function markCrossPageNav() {
    try {
      sessionStorage.setItem(SS_KEY, "1");
    } catch {
      /* ignore */
    }
  }

  function resumeCrossPageNav() {
    try {
      if (sessionStorage.getItem(SS_KEY) !== "1") return;
      sessionStorage.removeItem(SS_KEY);
      start({ overlay: true });
    } catch {
      /* ignore */
    }
  }

  document.addEventListener(
    "click",
    (e) => {
      if (!isBusy()) return;
      const t = e.target.closest(NAV_SEL);
      if (!t) return;
      if (t.matches("a[href]") && !isInternalNavLink(t)) return;
      e.preventDefault();
      e.stopImmediatePropagation();
    },
    true
  );

  document.addEventListener(
    "click",
    (e) => {
      const a = e.target.closest("a[href]");
      if (!a || !isInternalNavLink(a)) return;
      if (isBusy()) {
        e.preventDefault();
        return;
      }
      markCrossPageNav();
      start({ overlay: true });
    },
    true
  );

  function finishPageLoad() {
    if (depth > 0 || sessionStorage.getItem(SS_KEY) === "1") {
      done();
      try {
        sessionStorage.removeItem(SS_KEY);
      } catch {
        /* ignore */
      }
    }
  }

  resumeCrossPageNav();

  if (document.readyState === "complete") {
    global.requestAnimationFrame(finishPageLoad);
  } else {
    global.addEventListener(
      "load",
      () => {
        global.requestAnimationFrame(finishPageLoad);
      },
      { once: true }
    );
  }

  global.addEventListener("pageshow", (e) => {
    if (e.persisted) finishPageLoad();
  });

  global.EduSensePageTransition = {
    start,
    done,
    run,
    isBusy,
    set: setProgress,
  };
})(window);
