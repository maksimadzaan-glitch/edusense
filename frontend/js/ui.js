"use strict";

(function initMotion() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const root = document.documentElement;
  const CARD =
    "[data-spotlight], .glass, .action-tile, .task-card, .welcome, .code-panel, .card";

  /* ---- Splash on tap and on entering ---- */
  const layer = document.createElement("div");
  layer.className = "fx-ripples";
  layer.setAttribute("aria-hidden", "true");

  function splash(x, y, entry) {
    if (reduce) return;
    const el = document.createElement("span");
    el.className = entry ? "ripple is-entry" : "ripple";
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    layer.appendChild(el);
    setTimeout(() => el.remove(), entry ? 1000 : 420);
  }

  document.addEventListener(
    "pointerdown",
    (e) => splash(e.clientX, e.clientY, false),
    { passive: true }
  );

  /* ---- Cursor bloom follows the pointer with easing ---- */
  const cursor = document.querySelector(".fx-cursor");
  const gridPlane = document.querySelector(".fx-grid3d-plane");
  const markCube = document.querySelector(".mark3d-cube");
  let px = window.innerWidth * 0.5;
  let py = window.innerHeight * 0.18;
  let tx = px;
  let ty = py;
  let lit = null;

  function tick() {
    px += (tx - px) * 0.12;
    py += (ty - py) * 0.12;
    root.style.setProperty("--px", `${px}px`);
    root.style.setProperty("--py", `${py}px`);
    if (cursor) {
      cursor.style.transform = `translate3d(${px}px, ${py}px, 0) translate(-50%, -50%)`;
    }
    if (gridPlane) {
      const gx = ((px / window.innerWidth) - 0.5) * 28;
      const gy = ((py / window.innerHeight) - 0.4) * 18;
      root.style.setProperty("--gtx", `${gx.toFixed(1)}px`);
      root.style.setProperty("--gty", `${gy.toFixed(1)}px`);
    }
    if (markCube) {
      const nx = (px / window.innerWidth) * 2 - 1;
      const ny = (py / window.innerHeight) * 2 - 1;
      markCube.style.setProperty("--rx", `${(-ny * 9).toFixed(2)}deg`);
      markCube.style.setProperty("--ry", `${(nx * 12).toFixed(2)}deg`);
    }
    requestAnimationFrame(tick);
  }

  if (fine) {
    document.addEventListener(
      "pointermove",
      (e) => {
        tx = e.clientX;
        ty = e.clientY;

        const el = e.target instanceof Element ? e.target.closest(CARD) : null;
        if (el !== lit) {
          if (lit) lit.classList.remove("is-lit");
          lit = el;
          if (el) el.classList.add("is-lit");
        }
        if (!el) return;

        const r = el.getBoundingClientRect();
        el.style.setProperty("--x", `${e.clientX - r.left}px`);
        el.style.setProperty("--y", `${e.clientY - r.top}px`);
      },
      { passive: true }
    );

    document.addEventListener("pointerleave", () => {
      if (lit) lit.classList.remove("is-lit");
      lit = null;
    });

    if (!reduce) tick();
  }

  function start() {
    document.body.appendChild(layer);
    const mark = document.querySelector(".fx-mark");
    if (mark) {
      const r = mark.getBoundingClientRect();
      splash(r.left + r.width / 2, r.top + r.height / 2, true);
    } else {
      splash(window.innerWidth / 2, window.innerHeight * 0.4, true);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
