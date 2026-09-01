/**
 * EduSense PrintLayout / PDFDocumentTemplate (vanilla)
 * Isolated A4 print styles + mobile preview modal.
 * Does not inherit the dark site theme.
 */
(function (global) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Core A4 CSS — mm units, Times New Roman, forced light */
  function getPrintCss() {
    return `
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
html, body {
  margin: 0 !important;
  padding: 0 !important;
  background: #ffffff !important;
  color: #000000 !important;
  font-family: "Times New Roman", Times, serif !important;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.es-print-root, .a4-sheet, .es-print-page {
  width: 210mm;
  max-width: 210mm;
  min-height: 297mm;
  margin: 0 auto 8mm;
  padding: 15mm 20mm;
  background: #ffffff !important;
  color: #000000 !important;
  font-family: "Times New Roman", Times, serif !important;
  font-size: 11pt;
  line-height: 1.35;
  box-shadow: none;
  border-radius: 0;
  position: relative;
  overflow: visible;
}
.a4-inner, .es-print-inner { position: relative; z-index: 1; color: #000 !important; }

/* Images & geometry — hard clamp (tasks 1, 24, 25 etc.) */
.es-print-root img,
.a4-sheet img,
.es-print-page img,
.es-print-media img,
.ep-print-media img,
.task-figure img,
.task-media-img,
.es-print-root svg,
.a4-sheet svg {
  max-width: 100% !important;
  max-height: 80mm !important;
  width: auto !important;
  height: auto !important;
  object-fit: contain !important;
  display: block !important;
  margin: 10px auto !important;
  background: transparent !important;
}
.es-print-media,
.ep-print-media,
.task-figure,
.pdf-task-card,
.ep-task,
.es-print-task {
  page-break-inside: avoid !important;
  break-inside: avoid !important;
}

/* Shared reading / grammar texts */
.es-print-text-frame,
.oge-rus-shared.is-print,
.a4-sheet .oge-rus-shared {
  border: 1px solid #000 !important;
  padding: 12px !important;
  margin: 0 0 15px !important;
  font-size: 11pt !important;
  line-height: 1.4 !important;
  background: #fff !important;
  color: #000 !important;
  orphans: 3;
  widows: 3;
  page-break-inside: auto;
}
.es-print-text-frame p,
.oge-rus-shared.is-print p {
  margin: 0 0 0.55em;
  orphans: 3;
  widows: 3;
}

.es-print-task-title {
  font-weight: 700;
  font-size: 12pt;
  margin: 0 0 6px;
  color: #000 !important;
}
.es-print-task-body {
  margin: 0 0 8px;
  color: #000 !important;
}
.es-print-answer-line {
  margin: 10px 0 4px;
  padding: 8px 10px;
  border: 1px solid #000;
  font-size: 11pt;
  page-break-inside: avoid;
  break-inside: avoid;
}
.es-print-answer-line em {
  font-style: normal;
  letter-spacing: 0.12em;
}

.pdf-exam-header, .es-print-header {
  margin: 0 0 12px;
  page-break-after: avoid;
}
.pdf-exam-fields, .es-print-fields {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  margin: 10px 0;
}
.pdf-exam-field, .es-print-field {
  border-bottom: 1px solid #000;
  padding: 4px 0 6px;
  font-size: 10.5pt;
}
.pdf-exam-field span, .es-print-field span {
  display: block;
  font-size: 9pt;
  font-weight: 700;
  margin-bottom: 2px;
}
.pdf-exam-field em, .es-print-field em { font-style: normal; letter-spacing: 0.08em; }

.pdf-pro-banner {
  font-size: 10pt;
  font-weight: 700;
  margin: 0 0 10px;
  padding: 6px 8px;
  border: 1px solid #000;
}
.pdf-qr-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 0 0 12px;
  padding: 8px;
  border: 1px dashed #333;
  page-break-inside: avoid;
}
.pdf-qr-row img {
  max-width: 28mm !important;
  max-height: 28mm !important;
  margin: 0 !important;
}

.ans-blank-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-top: 10px;
}
.ans-blank-cell {
  border: 1px solid #000;
  min-height: 14mm;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  page-break-inside: avoid;
}
.ans-blank-cell b { font-size: 9pt; }
.ans-blank-cell span {
  flex: 1;
  border: 1px solid #999;
  min-height: 8mm;
}

.keys-sheet, .es-print-keys {
  page-break-before: always;
  break-before: page;
}
.key-table { width: 100%; border-collapse: collapse; margin: 0 0 10px; }
.key-table th, .key-table td {
  border: 1px solid #000;
  padding: 5px 7px;
  background: #fff !important;
  color: #000 !important;
}
.key-p2 {
  border: 1px solid #000;
  padding: 10px;
  margin: 0 0 10px;
  page-break-inside: avoid;
  break-inside: avoid;
}

.ep-wm-layer { opacity: 0.04 !important; }
.muted { color: #222 !important; }
.no-print { display: none !important; }

@media print {
  html, body { background: #fff !important; }
  .a4-sheet, .es-print-page {
    width: auto;
    max-width: none;
    min-height: auto;
    margin: 0;
    box-shadow: none;
    page-break-after: always;
  }
  .a4-sheet:last-child, .es-print-page:last-child { page-break-after: auto; }
  .pdf-task-card, .ep-task, .es-print-task, .key-p2, .es-print-media {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
}
`;
  }

  function clampImagesIn(root) {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll("img, svg, canvas").forEach(function (el) {
      el.style.setProperty("max-width", "100%", "important");
      el.style.setProperty("max-height", "80mm", "important");
      el.style.setProperty("width", "auto", "important");
      el.style.setProperty("height", "auto", "important");
      el.style.setProperty("object-fit", "contain", "important");
      el.style.setProperty("display", "block", "important");
      el.style.setProperty("margin", "10px auto", "important");
    });
    root.querySelectorAll(".oge-rus-shared").forEach(function (el) {
      el.classList.add("is-print");
    });
  }

  function openMobilePreview(opts) {
    const o = opts || {};
    const title = o.title || "Превью печати A4";
    const html = o.html || "";
    const css = (o.css || "") + "\n" + getPrintCss();
    const onDownload = typeof o.onDownload === "function" ? o.onDownload : null;
    const onPrint = typeof o.onPrint === "function" ? o.onPrint : null;

    closeMobilePreview();
    const modal = document.createElement("div");
    modal.id = "es-print-modal";
    modal.className = "es-print-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.innerHTML =
      '<div class="es-print-modal-bar no-print">' +
      "<h3>" +
      esc(title) +
      "</h3>" +
      '<div class="es-print-modal-actions">' +
      '<button type="button" class="es-print-btn-primary" id="es-print-download">Скачать PDF</button>' +
      '<button type="button" class="es-print-btn-ghost" id="es-print-window">Печать</button>' +
      '<button type="button" class="es-print-btn-ghost" id="es-print-close">Закрыть</button>' +
      "</div></div>" +
      '<div class="es-print-modal-scroll" id="es-print-scroll"></div>';
    document.body.appendChild(modal);
    document.documentElement.classList.add("es-print-open");

    const scroll = modal.querySelector("#es-print-scroll");
    const style = document.createElement("style");
    style.textContent = css;
    scroll.appendChild(style);
    const wrap = document.createElement("div");
    wrap.className = "es-print-root";
    wrap.innerHTML = html;
    scroll.appendChild(wrap);
    clampImagesIn(wrap);

    modal.querySelector("#es-print-close").addEventListener("click", closeMobilePreview);
    modal.querySelector("#es-print-download").addEventListener("click", function () {
      if (onDownload) onDownload();
      else if (onPrint) onPrint();
      else window.print();
    });
    modal.querySelector("#es-print-window").addEventListener("click", function () {
      if (onPrint) onPrint();
      else window.print();
    });
    return modal;
  }

  function closeMobilePreview() {
    document.getElementById("es-print-modal")?.remove();
    document.documentElement.classList.remove("es-print-open");
  }

  function isMobileViewport() {
    try {
      return window.matchMedia("(max-width: 820px)").matches || /Mobi|Android|iPhone/i.test(navigator.userAgent || "");
    } catch (_) {
      return false;
    }
  }

  global.EduSensePrint = {
    getPrintCss: getPrintCss,
    clampImagesIn: clampImagesIn,
    openMobilePreview: openMobilePreview,
    closeMobilePreview: closeMobilePreview,
    isMobileViewport: isMobileViewport,
  };
})(window);
