(function (global) {
  "use strict";
  const KEY = "edusense_announce_v4";

  function dismissed() {
    try {
      return global.localStorage.getItem(KEY) === "1";
    } catch {
      return false;
    }
  }

  function persistDismiss() {
    try {
      global.localStorage.setItem(KEY, "1");
    } catch {
      /* ignore */
    }
  }

  function dismiss(root) {
    persistDismiss();
    const banner = root && root.querySelector(".announce-banner");
    const finish = () => {
      if (root) root.hidden = true;
      document.body.classList.remove("has-announce");
    };
    if (!banner || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      finish();
      return;
    }
    banner.classList.add("is-out");
    banner.addEventListener("animationend", finish, { once: true });
    setTimeout(finish, 280);
  }

  function learnMore() {
    if (/\/updates|\/news/i.test(location.pathname)) {
      const top = document.getElementById("updates");
      if (top && typeof top.scrollIntoView === "function") {
        top.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      return;
    }
    location.href = "/updates";
  }

  function mount() {
    if (dismissed()) return;
    let root = document.getElementById("announce-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "announce-root";
      document.body.insertBefore(root, document.body.firstChild);
    }
    root.hidden = false;
    root.innerHTML = `
      <div class="announce-banner" role="region" aria-label="Новости EduSense">
        <div class="announce-inner">
          <span class="announce-new"><span aria-hidden="true">✨</span> NEW</span>
          <p class="announce-text">Внедрена ИИ-проверка Части 2 и режим Live-уроков.</p>
          <button type="button" class="announce-more" id="announce-more">Узнать больше</button>
        </div>
        <button type="button" class="announce-close" id="announce-close" aria-label="Закрыть">✕</button>
      </div>
    `;
    document.body.classList.add("has-announce");
    document.getElementById("announce-close")?.addEventListener("click", () => dismiss(root));
    document.getElementById("announce-more")?.addEventListener("click", learnMore);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})(typeof window !== "undefined" ? window : globalThis);
