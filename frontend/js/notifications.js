/**
 * Центр уведомлений (колокольчик) в шапке кабинета.
 */
(function (global) {
  "use strict";

  var READ_KEY = "edusense_notif_read";
  var MIRROR_KEY = "edusense_notif_mirror";
  var adapter = { collect: function () { return []; }, onSelect: null };
  var open = false;
  var items = [];
  var slot = null;

  function loadJson(key, fallback) {
    try {
      var raw = global.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function saveJson(key, value) {
    try {
      global.localStorage.setItem(key, JSON.stringify(value));
    } catch (_) {}
  }

  function readSet() {
    var arr = loadJson(READ_KEY, []);
    return new Set(Array.isArray(arr) ? arr : []);
  }

  function saveRead(set) {
    saveJson(READ_KEY, Array.from(set));
  }

  function mirrorPref() {
    var p = loadJson(MIRROR_KEY, { telegram: false, push: false });
    return {
      telegram: !!p.telegram,
      push: !!p.push,
    };
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function unreadCount() {
    var read = readSet();
    return items.filter(function (it) { return !read.has(it.id); }).length;
  }

  function bellSvg() {
    return (
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">' +
      '<path d="M6 9a6 6 0 0 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9"/>' +
      '<path d="M10 20a2 2 0 0 0 4 0"/>' +
      "</svg>"
    );
  }

  function kindLabel(kind) {
    if (kind === "ai") return "ИИ-проверка";
    if (kind === "rno") return "Работа над ошибками";
    return "Сдача";
  }

  function html() {
    var n = unreadCount();
    var pref = mirrorPref();
    var read = readSet();
    var rows = items
      .map(function (it) {
        var unread = !read.has(it.id);
        return (
          '<li><button type="button" class="notif-item' +
          (unread ? " is-unread" : "") +
          '" data-notif-id="' +
          escapeHtml(it.id) +
          '">' +
          '<span class="notif-item-kind">' +
          escapeHtml(kindLabel(it.kind)) +
          "</span>" +
          '<span class="notif-item-title">' +
          escapeHtml(it.title) +
          "</span>" +
          '<span class="notif-item-text">' +
          escapeHtml(it.text || "") +
          "</span></button></li>"
        );
      })
      .join("");
    return (
      '<div class="notif-wrap">' +
      '<button type="button" class="notif-bell' +
      (open ? " is-open" : "") +
      '" id="notif-bell-btn" aria-label="Уведомления" aria-expanded="' +
      (open ? "true" : "false") +
      '">' +
      bellSvg() +
      '<span class="notif-badge"' +
      (n ? "" : " hidden") +
      ">" +
      (n > 9 ? "9+" : String(n)) +
      "</span></button>" +
      '<div class="notif-pop" id="notif-pop"' +
      (open ? "" : " hidden") +
      ' role="dialog" aria-label="Уведомления">' +
      '<div class="notif-pop-head"><strong>Уведомления</strong>' +
      '<button type="button" class="notif-mark" id="notif-mark-all">Отметить всё как прочитанное</button></div>' +
      (rows ? '<ul class="notif-list">' + rows + "</ul>" : '<p class="notif-empty">Пока тихо — сдачи и Работа над ошибками появятся здесь.</p>') +
      '<label class="notif-mirror">Дублировать в Telegram / Push' +
      '<span class="notif-switch"><input type="checkbox" id="notif-mirror-toggle"' +
      (pref.telegram || pref.push ? " checked" : "") +
      ' /><span></span></span></label>' +
      "</div></div>"
    );
  }

  function bind() {
    if (!slot) return;
    slot.querySelector("#notif-bell-btn")?.addEventListener("click", function (e) {
      e.stopPropagation();
      open = !open;
      paint();
    });
    slot.querySelector("#notif-mark-all")?.addEventListener("click", function (e) {
      e.stopPropagation();
      var set = readSet();
      items.forEach(function (it) { set.add(it.id); });
      saveRead(set);
      paint();
    });
    slot.querySelectorAll("[data-notif-id]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var id = btn.getAttribute("data-notif-id");
        var set = readSet();
        set.add(id);
        saveRead(set);
        var found = items.find(function (it) { return it.id === id; });
        open = false;
        paint();
        if (found && typeof adapter.onSelect === "function") adapter.onSelect(found);
      });
    });
    slot.querySelector("#notif-mirror-toggle")?.addEventListener("change", function (e) {
      e.stopPropagation();
      var on = !!e.target.checked;
      saveJson(MIRROR_KEY, { telegram: on, push: on });
      if (on && global.Notification && Notification.permission === "default") {
        Notification.requestPermission().catch(function () {});
      }
    });
  }

  function paint() {
    if (!slot) return;
    slot.innerHTML = html();
    bind();
  }

  function maybePush(fresh) {
    var pref = mirrorPref();
    if (!pref.push || !global.Notification || Notification.permission !== "granted") return;
    var read = readSet();
    var newest = fresh.find(function (it) { return !read.has(it.id); });
    if (!newest) return;
    try {
      new Notification(newest.title, { body: newest.text || "", icon: "/assets/edusense-mark-192.png" });
    } catch (_) {}
  }

  function refresh() {
    var next = adapter.collect() || [];
    var prevIds = items.map(function (it) { return it.id; }).join("|");
    items = next.slice(0, 24);
    var nowIds = items.map(function (it) { return it.id; }).join("|");
    if (nowIds !== prevIds) maybePush(items);
    if (slot) paint();
  }

  function mount(el, opts) {
    if (opts) {
      if (typeof opts.collect === "function") adapter.collect = opts.collect;
      if (opts.onSelect) adapter.onSelect = opts.onSelect;
    }
    slot = el || document.getElementById("notif-root");
    if (!slot) return;
    refresh();
  }

  if (!global.__notifDocBound) {
    global.__notifDocBound = true;
    document.addEventListener("click", function (e) {
      if (!open) return;
      if (e.target && e.target.closest && e.target.closest(".notif-wrap")) return;
      open = false;
      paint();
    });
  }

  global.EduSenseNotifications = {
    configure: function (opts) {
      adapter.collect = opts.collect || adapter.collect;
      adapter.onSelect = opts.onSelect || adapter.onSelect;
    },
    mount: mount,
    refresh: refresh,
  };
})(typeof window !== "undefined" ? window : this);
