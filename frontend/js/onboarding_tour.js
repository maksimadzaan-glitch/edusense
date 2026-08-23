/**
 * Пошаговый гид: подсветка кнопки. Дальше — только по «Далее».
 */
(function (global) {
  "use strict";

  var NEED_KEY = "edusense_needs_tour";
  var STORE_PREFIX = "edusense_tour_v9:";

  var TEACHER_STEPS = [
    {
      target: "#btn-create",
      title: "Создайте класс",
      body: "Заполните название и предмет, затем нажмите эту кнопку.",
      waitTarget: true,
      skipIf: function () {
        if (typeof hooks.hasClass === "function" && hooks.hasClass()) return true;
        var s = screenOf();
        return !!(s && s !== "create");
      },
    },
    {
      target: "#btn-copy-link, #btn-copy-dash",
      title: "Отправьте код",
      body: "Нажмите, чтобы скопировать ссылку, и отправьте её классу.",
      waitTarget: true,
    },
    {
      needDash: true,
      target: "[data-tour='nav-tests']",
      title: "Откройте «Тесты»",
      body: "Нажмите этот пункт меню слева.",
      waitTarget: true,
      skipIf: function () {
        return tabOf() === "tests" && screenOf() === "dashboard";
      },
    },
    {
      needDash: true,
      tab: "tests",
      target: "#btn-gen-full",
      title: "Соберите КИМ",
      body: "Нажмите «Полный КИМ». Когда вариант соберётся, нажмите «Далее».",
      waitTarget: true,
      skipIf: function () {
        return typeof hooks.hasVariant === "function" && hooks.hasVariant();
      },
    },
    {
      needDash: true,
      tab: "tests",
      target: "#btn-open-publish",
      title: "Выдайте классу",
      body: "Нажмите «Выдать классу». Дальше всё в этом окне — обучение закончится.",
      waitTarget: true,
      endOnPublish: true,
    },
  ];

  var STUDENT_STEPS = [
    {
      target: "#btn-open",
      title: "Войдите в класс",
      body: "Введите код от учителя и нажмите эту кнопку.",
      skipIf: function () {
        if (typeof hooks.hasClass === "function" && hooks.hasClass()) return true;
        var s = screenOf();
        return !!(s && s !== "join");
      },
    },
    {
      target: "[data-start]",
      title: "Начните вариант",
      body: "Нажмите «Начать решение» у открытого КИМа.",
      waitTarget: true,
    },
    {
      target: "[data-tour='nav-progress']",
      title: "Мой прогресс",
      body: "Здесь оценки, точность и разбор сданных работ.",
    },
  ];

  var root = null;
  var hl = null;
  var els = {};
  var enrolled = false;
  var collapsed = false;
  var dismissed = false;
  var boundDoc = false;
  var boundWin = false;
  var paintTimer = 0;
  var rafId = 0;
  var stepIndex = 0;
  var hooks = {};
  var lastActAt = 0;
  var lastScrollStep = -1;
  var waitTries = 0;
  var navTimer = 0;

  function currentUser() {
    try {
      return JSON.parse(global.localStorage.getItem("edusense_user") || "null");
    } catch (_) {
      return null;
    }
  }

  function userKey() {
    var user = currentUser();
    if (user && user.id != null) return String(user.id);
    if (user && user.full_name) return String(user.full_name).trim().toLowerCase();
    return "anon";
  }

  function storeKey() {
    return STORE_PREFIX + userKey();
  }

  function roleOf() {
    var user = currentUser();
    return user && user.role === "student" ? "student" : "teacher";
  }

  function stepsOf() {
    return roleOf() === "student" ? STUDENT_STEPS : TEACHER_STEPS;
  }

  function screenOf() {
    return typeof hooks.screen === "function" ? hooks.screen() : "";
  }

  function tabOf() {
    return typeof hooks.tab === "function" ? hooks.tab() : "";
  }

  function loadState() {
    try {
      var raw = JSON.parse(global.localStorage.getItem(storeKey()) || "null");
      if (raw && typeof raw === "object") {
        stepIndex = Math.max(0, Number(raw.step) || 0);
        return !!raw.done;
      }
    } catch (_) {}
    stepIndex = 0;
    return false;
  }

  function saveState(done) {
    try {
      global.localStorage.setItem(storeKey(), JSON.stringify({ step: stepIndex, done: !!done }));
    } catch (_) {}
  }

  function persistDone() {
    saveState(true);
    try {
      global.localStorage.removeItem(NEED_KEY);
      var user = currentUser();
      if (user && user.needs_onboarding) {
        user.needs_onboarding = false;
        global.localStorage.setItem("edusense_user", JSON.stringify(user));
      }
    } catch (_) {}
  }

  function isNewAccount() {
    if (loadState()) return false;
    try {
      if (global.localStorage.getItem(NEED_KEY) === "1") return true;
      var user = currentUser();
      return !!(user && user.needs_onboarding);
    } catch (_) {
      return false;
    }
  }

  function ensureMask() {
    hl = document.getElementById("tour-hl");
    if (!hl) {
      hl = document.createElement("div");
      hl.id = "tour-hl";
      hl.className = "tour-hl";
      hl.setAttribute("aria-hidden", "true");
      document.body.appendChild(hl);
    }
  }

  function ensureRoot() {
    root = document.getElementById("tour-root");
    if (root && root.tagName === "DIALOG") {
      try {
        if (root.open) root.close();
      } catch (_) {}
      root.remove();
      root = null;
    }
    if (!root) {
      root = document.createElement("div");
      root.id = "tour-root";
      document.body.appendChild(root);
    }
    root.className = "tour-root";
    if (!root._built) {
      root.innerHTML =
        '<div class="tour-chip" data-tour-chip hidden>Обучение</div>' +
        '<div class="tour-sheet">' +
        '<button type="button" class="tour-x" data-tour-act="hide" aria-label="Скрыть">×</button>' +
        '<p class="tour-step" data-tour-step></p>' +
        "<h3 data-tour-title></h3>" +
        '<p class="tour-body" data-tour-body></p>' +
        '<div class="tour-actions">' +
        '<button type="button" class="tour-btn tour-btn-skip" data-tour-act="skip">Пропустить</button>' +
        '<button type="button" class="tour-btn tour-btn-next" data-tour-act="next">Далее</button>' +
        "</div></div>";
      root._built = true;
    }
    els.chip = root.querySelector("[data-tour-chip]");
    els.sheet = root.querySelector(".tour-sheet");
    els.step = root.querySelector("[data-tour-step]");
    els.title = root.querySelector("[data-tour-title]");
    els.body = root.querySelector("[data-tour-body]");
    els.next = root.querySelector('[data-tour-act="next"]');
    ensureMask();
    bindSheet();
    bindDocumentOnce();
    bindWindowOnce();
    return root;
  }

  function eventEl(e) {
    var t = e && e.target;
    if (t && t.nodeType !== 1) t = t.parentElement;
    return t || null;
  }

  function actFromEvent(e) {
    var t = eventEl(e);
    if (!t || !t.closest) return "";
    var btn = t.closest("[data-tour-act]");
    if (btn && root && root.contains(btn)) return btn.getAttribute("data-tour-act") || "";
    if (t.closest("[data-tour-chip]") && root && root.contains(t)) return "expand";
    return "";
  }

  function runAct(act) {
    var now = Date.now();
    if (now - lastActAt < 450) return;
    lastActAt = now;
    if (act === "skip") finish();
    else if (act === "next") next();
    else if (act === "hide") collapse();
    else if (act === "expand") expand();
  }

  function intercept(e) {
    var act = actFromEvent(e);
    if (!act) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();
    runAct(act);
  }

  function bindSheet() {
    if (!root || root._sheetBound) return;
    root._sheetBound = true;
    root.addEventListener("pointerdown", intercept, true);
    root.addEventListener("click", intercept, true);
  }

  function bindDocumentOnce() {
    if (boundDoc) return;
    boundDoc = true;
    document.addEventListener(
      "pointerdown",
      function (e) {
        if (!enrolled || !root || root.hidden) return;
        intercept(e);
      },
      true
    );
  }

  function bindWindowOnce() {
    if (boundWin) return;
    boundWin = true;
    global.addEventListener("resize", schedulePaint);
    global.addEventListener("scroll", schedulePaint, true);
  }

  function startTrack() {
    /* рамка только на scroll/resize/render — постоянный rAF дёргал подсветку */
  }

  function stopTrack() {
    if (rafId) global.cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function collapse() {
    collapsed = true;
    stopTrack();
    paint();
  }

  function expand() {
    collapsed = false;
    paint();
    startTrack();
  }

  function next() {
    var spec = stepsOf()[stepIndex];
    if (spec && spec.waitTarget && !findTarget(spec)) return;
    var steps = stepsOf();
    if (stepIndex >= steps.length - 1) {
      finish();
      return;
    }
    stepIndex += 1;
    lastScrollStep = -1;
    waitTries = 0;
    saveState(false);
    applyStep();
  }

  function finish() {
    dismissed = true;
    enrolled = false;
    collapsed = false;
    stopTrack();
    persistDone();
    document.documentElement.classList.remove("tour-on");
    if (root) root.hidden = true;
    hideMask();
    if (global.EduSensePWA && typeof global.EduSensePWA.sync === "function") {
      global.EduSensePWA.sync();
    }
  }

  function skipPrefix() {
    var steps = stepsOf();
    while (stepIndex < steps.length) {
      var spec = steps[stepIndex];
      if (spec && typeof spec.skipIf === "function" && spec.skipIf()) {
        stepIndex += 1;
        waitTries = 0;
        continue;
      }
      break;
    }
    saveState(false);
    if (stepIndex >= steps.length) {
      persistDone();
      return true;
    }
    return false;
  }

  function isVisible(el) {
    if (!el || !el.getBoundingClientRect) return false;
    var r = el.getBoundingClientRect();
    return r.width > 2 && r.height > 2;
  }

  function findTarget(spec) {
    if (!spec || !spec.target) return null;
    var parts = String(spec.target).split(",");
    for (var i = 0; i < parts.length; i += 1) {
      var el = document.querySelector(parts[i].trim());
      if (el && isVisible(el)) return el;
    }
    return null;
  }

  function hideMask() {
    if (hl) hl.hidden = true;
  }

  function snap(n) {
    var dpr = window.devicePixelRatio || 1;
    return Math.round(n * dpr) / dpr;
  }

  function boxOf(el) {
    var r = el.getBoundingClientRect();
    var pad = 4;
    var l = snap(r.left - pad);
    var t = snap(r.top - pad);
    var ri = snap(r.right + pad);
    var b = snap(r.bottom + pad);
    return {
      x: l,
      y: t,
      w: Math.max(0, ri - l),
      h: Math.max(0, b - t),
      right: ri,
      bottom: b,
    };
  }

  function placeMask(target) {
    if (!hl) return;
    if (!target) {
      hideMask();
      return;
    }
    var box = boxOf(target);
    var radius = "12px";
    try {
      radius = global.getComputedStyle(target).borderRadius || radius;
    } catch (_) {}
    hl.hidden = false;
    hl.style.width = box.w + "px";
    hl.style.height = box.h + "px";
    hl.style.borderRadius = radius;
    hl.style.transform = "translate3d(" + box.x + "px," + box.y + "px,0)";
  }

  function placeCard(target) {
    if (!root || !els.sheet) return;
    var gap = 14;
    var margin = 16;
    var w = Math.min(320, window.innerWidth - margin * 2);
    root.style.width = w + "px";
    root.style.right = "auto";
    root.style.bottom = "auto";
    if (!target) {
      root.style.transform = "none";
      root.style.left = snap(window.innerWidth - w - margin) + "px";
      root.style.top = "auto";
      root.style.bottom = margin + "px";
      root.setAttribute("data-place", "float");
      return;
    }
    var sheetH = els.sheet.offsetHeight || 200;
    var box = boxOf(target);
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var spaceRight = vw - box.right - gap - margin;
    var spaceLeft = box.x - gap - margin;
    var spaceBottom = vh - box.bottom - gap - margin;
    var place;
    var left;
    var top;
    if (spaceRight >= w) {
      place = "right";
      left = box.right + gap;
      top = box.y + box.h / 2 - sheetH / 2;
    } else if (spaceLeft >= w) {
      place = "left";
      left = box.x - gap - w;
      top = box.y + box.h / 2 - sheetH / 2;
    } else if (spaceBottom >= sheetH) {
      place = "bottom";
      top = box.bottom + gap;
      left = box.x + box.w / 2 - w / 2;
    } else {
      place = "top";
      top = box.y - gap - sheetH;
      left = box.x + box.w / 2 - w / 2;
    }
    left = snap(Math.min(Math.max(margin, left), vw - w - margin));
    top = snap(Math.min(Math.max(margin, top), vh - sheetH - margin));
    root.style.left = "0px";
    root.style.top = "0px";
    root.style.transform = "translate3d(" + left + "px," + top + "px,0)";
    root.setAttribute("data-place", place);
    var arrow;
    if (place === "right" || place === "left") {
      arrow = snap(box.y + box.h / 2 - top);
    } else {
      arrow = snap(box.x + box.w / 2 - left);
    }
    arrow = Math.max(22, Math.min((place === "right" || place === "left" ? sheetH : w) - 22, arrow));
    root.style.setProperty("--tour-arrow", arrow + "px");
  }

  function maybeScroll(target) {
    if (!target || lastScrollStep === stepIndex) return;
    lastScrollStep = stepIndex;
    var r = target.getBoundingClientRect();
    if (r.top >= 16 && r.bottom <= window.innerHeight - 16 && r.left >= 8 && r.right <= window.innerWidth - 8) {
      return;
    }
    try {
      target.scrollIntoView({ block: "nearest", inline: "nearest" });
    } catch (_) {}
  }

  function applyStep() {
    var spec = stepsOf()[stepIndex];
    if (!spec) {
      finish();
      return;
    }
    waitTries = 0;
    var moveDash = spec.needDash && screenOf() === "code" && typeof hooks.goDashboard === "function";
    var moveTab =
      spec.tab && screenOf() === "dashboard" && tabOf() !== spec.tab && typeof hooks.goToTab === "function";
    if (moveDash || moveTab) {
      if (navTimer) clearTimeout(navTimer);
      navTimer = setTimeout(function () {
        navTimer = 0;
        if (moveDash) hooks.goDashboard();
        if (moveTab && spec.tab) hooks.goToTab(spec.tab);
        schedulePaint();
      }, 0);
      return;
    }
    schedulePaint();
  }

  function examHidden() {
    var s = screenOf();
    return s === "work" || s === "review";
  }

  function publishOpen() {
    if (typeof hooks.modalOpen === "function" && hooks.modalOpen() && document.querySelector("#publish-backdrop")) {
      return true;
    }
    return !!document.querySelector("#publish-backdrop");
  }

  function modalOpen() {
    return publishOpen();
  }

  function paint() {
    if (!enrolled || !root) return;
    if (examHidden()) {
      stopTrack();
      root.hidden = true;
      hideMask();
      document.documentElement.classList.remove("tour-on");
      return;
    }
    if (skipPrefix()) {
      finish();
      return;
    }
    var steps = stepsOf();
    var spec = steps[stepIndex];
    if (!spec) {
      finish();
      return;
    }
    if (publishOpen() && spec.endOnPublish) {
      finish();
      return;
    }
    if (modalOpen()) {
      stopTrack();
      root.hidden = true;
      hideMask();
      document.documentElement.classList.remove("tour-on");
      return;
    }
    var target = findTarget(spec);
    if (spec.waitTarget && !target && waitTries < 12) {
      waitTries += 1;
      paintTimer = setTimeout(function () {
        paintTimer = 0;
        paint();
      }, 80);
    }
    els.step.textContent = "Шаг " + (stepIndex + 1) + " из " + steps.length;
    els.title.textContent = spec.title;
    els.body.textContent =
      spec.waitTarget && !target
        ? spec.body + " Кнопка ещё не на экране — сделайте этот шаг, рамка подхватит."
        : spec.body;
    if (els.next) {
      els.next.textContent = stepIndex >= steps.length - 1 ? "Готово" : "Далее";
      els.next.disabled = !!(spec.waitTarget && !target);
    }
    root.hidden = false;
    document.documentElement.classList.add("tour-on");
    if (collapsed) {
      els.sheet.hidden = true;
      els.chip.hidden = false;
      hideMask();
      stopTrack();
      root.removeAttribute("data-place");
      root.style.transform = "none";
      root.style.left = "auto";
      root.style.right = "16px";
      root.style.top = "auto";
      root.style.bottom = "16px";
      return;
    }
    els.sheet.hidden = false;
    els.chip.hidden = true;
    maybeScroll(target);
    layoutAround();
    startTrack();
  }

  function layoutAround() {
    if (!enrolled || collapsed || !root) return;
    if (publishOpen()) {
      var spec = stepsOf()[stepIndex];
      if (spec && spec.endOnPublish) {
        finish();
        return;
      }
      hideMask();
      root.hidden = true;
      return;
    }
    var spec = stepsOf()[stepIndex];
    var target = findTarget(spec);
    placeMask(target);
    placeCard(target);
  }

  function schedulePaint() {
    if (paintTimer) clearTimeout(paintTimer);
    paintTimer = setTimeout(function () {
      paintTimer = 0;
      paint();
    }, 40);
  }

  function maybeStart(opts) {
    if (opts) hooks = Object.assign(hooks, opts);
    if (dismissed) return;
    if (enrolled) {
      schedulePaint();
      return;
    }
    if (!isNewAccount()) return;
    loadState();
    if (skipPrefix()) return;
    ensureRoot();
    enrolled = true;
    lastScrollStep = -1;
    applyStep();
    startTrack();
  }

  function onRendered() {
    if (enrolled) schedulePaint();
  }

  global.EduSenseTour = {
    maybeStart: maybeStart,
    onRendered: onRendered,
    isActive: function () {
      return enrolled && !collapsed && !dismissed;
    },
  };
})(typeof window !== "undefined" ? window : this);
