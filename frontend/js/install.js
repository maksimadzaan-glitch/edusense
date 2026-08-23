(function () {
  var ua = String(navigator.userAgent || "");
  var ios = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var android = /Android/i.test(ua);
  var yandex = /YaBrowser|Yowser/i.test(ua);
  var os = ios ? "ios" : android ? "android" : "win";
  var step = 0;

  var installBtn = document.getElementById("btn-install");
  var note = document.getElementById("in-note");
  var ok = document.getElementById("in-ok");
  var sub = document.getElementById("in-sub");
  var bar = document.getElementById("in-bar");
  var strip = document.getElementById("in-strip");
  var shelf = document.getElementById("in-shelf");
  var tabs = [].slice.call(document.querySelectorAll("[data-os-tab]"));
  var guides = [].slice.call(document.querySelectorAll("[data-os-guide]"));

  var installed =
    window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;

  function setNote(text) {
    if (note) note.textContent = text || "";
  }

  function setOk(text) {
    if (!ok) return;
    ok.hidden = !text;
    ok.textContent = text || "";
  }

  function shortcutBody() {
    return "[InternetShortcut]\r\nURL=" + location.origin + "/\r\n";
  }

  function render() {
    tabs.forEach(function (tab) {
      tab.classList.toggle("is-on", tab.getAttribute("data-os-tab") === os);
    });

    var cards = [];
    guides.forEach(function (guide) {
      var match = guide.getAttribute("data-os-guide") === os;
      guide.hidden = !match;
      if (!match) return;
      cards = [].slice.call(guide.querySelectorAll("[data-step]"));
      if (step > cards.length - 1) step = cards.length - 1;
      if (step < 0) step = 0;
      cards.forEach(function (card) {
        card.hidden = Number(card.getAttribute("data-step")) !== step;
      });
    });

    if (!bar) return;
    bar.innerHTML = "";
    cards.forEach(function (_, i) {
      var dot = document.createElement("span");
      dot.className = "in-dot" + (i <= step ? " is-on" : "");
      bar.appendChild(dot);
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      os = tab.getAttribute("data-os-tab");
      step = 0;
      render();
    });
  });

  document.addEventListener("click", function (e) {
    var next = e.target.closest("[data-next]");
    var prev = e.target.closest("[data-prev]");
    if (!next && !prev) return;
    step += next ? 1 : -1;
    render();
  });

  function successMode(msg) {
    if (installBtn) {
      installBtn.disabled = true;
      installBtn.textContent = "Готово";
    }
    setOk(msg || "Готово. Сверните окна — на рабочем столе значок EduSense. Откройте его двойным щелчком.");
    setNote("");
    if (shelf) shelf.hidden = true;
    step = 2;
    render();
  }

  function fallbackDownload() {
    var a = document.createElement("a");
    a.href = "/shortcut";
    a.download = "EduSense.url";
    document.body.appendChild(a);
    a.click();
    a.remove();
    if (shelf) shelf.hidden = false;
    setOk("Файл ушёл вниз экрана, в панель загрузок Chrome. Нажмите на него → «Показать в папке» и перетащите на рабочий стол.");
    step = 1;
    render();
  }

  function saveToDesktop() {
    if (!window.showSaveFilePicker) return Promise.resolve(false);
    return window
      .showSaveFilePicker({
        suggestedName: "EduSense.url",
        startIn: "desktop",
        types: [
          {
            description: "Ярлык EduSense",
            accept: { "text/plain": [".url"] },
          },
        ],
      })
      .then(function (handle) {
        return handle.createWritable().then(function (writable) {
          return writable
            .write(new Blob([shortcutBody()], { type: "text/plain" }))
            .then(function () {
              return writable.close();
            });
        });
      })
      .then(function () {
        return "ok";
      })
      .catch(function (err) {
        if (err && err.name === "AbortError") return "abort";
        return false;
      });
  }

  function tryNative() {
    var bip = window.__edusenseBip;
    if (!bip) return Promise.resolve(false);
    window.__edusenseBip = null;
    try {
      bip.prompt();
    } catch (_) {
      window.__edusenseBip = bip;
      return Promise.resolve(false);
    }
    return bip.userChoice.then(function (res) {
      return !!(res && res.outcome === "accepted");
    }).catch(function () {
      return false;
    });
  }

  function runInstall() {
    tryNative().then(function (nativeOk) {
      if (nativeOk) {
        successMode("Chrome сам поставил EduSense. Значок на рабочем столе и в меню «Пуск».");
        return;
      }
      return saveToDesktop().then(function (saved) {
        if (saved === "ok") {
          successMode();
          return;
        }
        if (saved === "abort") {
          setNote("Окно закрыли. Не сохраняйте файл — это снова откроет Яндекс. Нужно: меню ☰ → «Установить EduSense».");
          step = 1;
          render();
          return;
        }
        setNote("Яндекс не показал установку сам. Откройте ☰ справа вверху → «Установить EduSense» или «Добавить на рабочий стол».");
        step = 1;
        render();
        var guide = guides.filter(function (g) {
          return g.getAttribute("data-os-guide") === "win";
        })[0];
        if (guide) guide.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }

  if (strip) strip.hidden = ios;
  if (ios && sub) {
    sub.textContent = "На iPhone ярлык ставит Safari — 3 шага ниже.";
  }

  if (installBtn) {
    if (ios) {
      installBtn.textContent = "Показать шаги для iPhone";
      installBtn.addEventListener("click", function () {
        os = "ios";
        step = 0;
        render();
        var guide = guides.filter(function (g) {
          return g.getAttribute("data-os-guide") === "ios";
        })[0];
        if (guide) guide.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      setNote("Откройте эту страницу в Safari и пройдите шаги.");
    } else {
      installBtn.addEventListener("click", runInstall);
      if (yandex) {
        setNote("У вас Яндекс Браузер. Нажмите кнопку — если запрос не выйдет, меню ☰ справа вверху → «Установить EduSense».");
      } else {
        setNote("Нажмите кнопку. Если запроса нет — в Chrome/Edge меню ⋮ → «Установить EduSense». Файл .url не нужен: он открывается как вкладка Яндекса.");
      }
    }
  }

  if (installed) {
    if (sub) sub.textContent = "EduSense уже установлен на этом устройстве.";
    successMode("Уже стоит. Откройте значок на рабочем столе.");
  }

  window.addEventListener("appinstalled", function () {
    successMode("Chrome сам поставил EduSense. Значок на рабочем столе и в меню «Пуск».");
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
  }

  render();
})();
