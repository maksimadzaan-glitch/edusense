/**
 * ОГЭ русский: listening (TTS×2), shared grammar/reading, matching, essay 13.x
 * + exam-like renderer for test part (types 2–12).
 * Подключается как обычный script → window.OgeRusUI
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeNewlines(raw) {
    return String(raw ?? "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  }

  /** Проза ОГЭ: не гонять через formatMathText (collapseVerticalJunk склеивает всё в одну строку). */
  function formatText(raw) {
    const text = normalizeNewlines(raw).trim();
    if (!text) return "";
    const needsMath = /\[\[|\\frac|\\sqrt|√/.test(text);
    let html;
    if (needsMath && typeof global.formatMathText === "function") {
      // Математика редка в русском; всё равно восстанавливаем абзацы по исходным \\n
      const parts = text.split(/(\n\n+)/);
      html = parts
        .map(function (chunk) {
          if (/^\n+$/.test(chunk)) return "\n\n";
          return global.formatMathText(chunk);
        })
        .join("");
    } else {
      html = escapeHtml(text);
    }
    if (/\n\n/.test(html)) {
      return html
        .split(/\n\n+/)
        .map(function (p) {
          const inner = p.replace(/^\n+|\n+$/g, "").replace(/\n/g, "<br>");
          return inner ? '<p class="oge-fmt-p">' + inner + "</p>" : "";
        })
        .join("");
    }
    return html.replace(/\n/g, "<br>");
  }

  /** Вставить перевод строки перед нумерованными предложениями (N), если в JSON нет \\n. */
  function breakBeforeSentenceNums(text) {
    let t = normalizeNewlines(text);
    // «…конец. (2) Далее» или «! (3)» → новая строка
    t = t.replace(/([.!?…»"])\s+(?=\(\d+\))/g, "$1\n");
    // Диалог: конец фразы перед «— (19)»
    t = t.replace(/([.!?…»:"])\s+(?=[\u2014—\-]\s*\(\d+\))/g, "$1\n");
    // Склейка без пробела после точки: «баланс.(2)»
    t = t.replace(/([.!?…»"])(?=\(\d+\))/g, "$1\n");
    return t;
  }

  /**
   * Текст грамматики/чтения: абзацы + каждое (N)-предложение с новой строки, маркеры выделены.
   */
  function formatPassageHtml(raw) {
    const text = breakBeforeSentenceNums(String(raw || "")).trim();
    if (!text) return "";
    const paragraphs = text.split(/\n\n+/);
    return paragraphs
      .map(function (para) {
        const lines = para
          .split(/\n/)
          .map(function (l) {
            return l.trim();
          })
          .filter(Boolean);
        if (!lines.length) return "";
        const body = lines
          .map(function (line) {
            const marked = escapeHtml(line).replace(
              /\((\d+)\)/g,
              '<span class="oge-sent-num">($1)</span>'
            );
            if (/^(?:[\u2014—\-]\s*)?\(\d+\)/.test(line)) {
              return '<span class="oge-sent-line">' + marked + "</span>";
            }
            return '<span class="oge-sent-line oge-sent-line--plain">' + marked + "</span>";
          })
          .join("");
        return '<p class="oge-passage-p">' + body + "</p>";
      })
      .join("");
  }

  function payloadOf(task) {
    const p = task && (task.payload || task.Payload);
    if (p == null) return null;
    if (typeof p === "string") {
      try {
        return JSON.parse(p);
      } catch {
        return null;
      }
    }
    return typeof p === "object" ? p : null;
  }

  function minWordsOf(payload, fallback) {
    const n = Number(payload && payload.min_words);
    if (Number.isFinite(n) && n >= 50 && n <= 200) return Math.round(n);
    return fallback == null ? 70 : fallback;
  }

  function essayMinWords(payload, fallback) {
    return minWordsOf(payload, fallback);
  }

  function normSubjectCode(value) {
    const s = String(value || "")
      .toLowerCase()
      .replace(/ё/g, "е")
      .replace(/\s+/g, " ")
      .trim();
    if (!s) return "";
    if (
      s === "math" ||
      s === "mathematics" ||
      s === "math_base" ||
      s.indexOf("матем") >= 0
    ) {
      return "math";
    }
    if (
      s === "russian" ||
      s === "rus" ||
      s === "ru" ||
      s.indexOf("русск") >= 0 ||
      s.indexOf("russian") >= 0
    ) {
      return "russian";
    }
    return s;
  }

  function normExamCode(value) {
    const s = String(value || "")
      .toUpperCase()
      .replace(/\s+/g, " ")
      .trim();
    if (!s) return "";
    if (s === "OGE" || s.indexOf("ОГЭ") >= 0 || s.indexOf("OGE") >= 0) return "OGE";
    return s;
  }

  function subjectOf(obj) {
    if (!obj || typeof obj !== "object") return "";
    return normSubjectCode(
      obj.subject_code || obj.subjectCode || obj.subject
    );
  }

  function examOf(obj) {
    if (!obj || typeof obj !== "object") return "";
    return normExamCode(
      obj.exam_code ||
        obj.examCode ||
        obj.exam ||
        obj.exam_type ||
        obj.examType ||
        obj.target_exam ||
        obj.targetExam
    );
  }

  /** Явные маркеры payload ОГЭ русский (не kim_order/kim_type — они бывают и у math-эталона). */
  function hasOgeRusPayloadMarkers(p) {
    if (!p || typeof p !== "object") return false;
    if (p.oge_rus === true || p.oge_rus === 1 || p.oge_rus === "true") return true;
    if (p.ui === "oge_rus" || p.ui === "listening" || p.ui === "essay_choice") return true;
    if (p.ui === "matching" && (p.matching || p.oge_rus)) return true;
    if (p.grammar_text || p.reading_text || p.listening_text) return true;
    if (p.essay_options || p.matching) return true;
    return false;
  }

  function isOgeRusTask(task) {
    if (!task) return false;
    const sc = subjectOf(task);
    // Жёстко: математика никогда не идёт в UI ОГЭ русский
    if (sc === "math") return false;
    const p = payloadOf(task);
    if (hasOgeRusPayloadMarkers(p)) return true;
    const ec = examOf(task);
    return sc === "russian" && ec === "OGE";
  }

  function isOgeRusList(tasks) {
    return Array.isArray(tasks) && tasks.some(isOgeRusTask);
  }

  /** Строгий детект: exam_ui с сервера, subject=russian+OGE, или payload.oge_rus / rus-поля. */
  function isOgeRussianExam(tasksOrMeta, maybeMeta) {
    const tasks = Array.isArray(tasksOrMeta) ? tasksOrMeta : null;
    const meta =
      maybeMeta ||
      (!tasks && tasksOrMeta && typeof tasksOrMeta === "object" ? tasksOrMeta : null);

    const metaSubject = subjectOf(meta);
    if (metaSubject === "math") return false;

    // Sticky exam_ui=oge_rus_kim на math-классе — игнор
    const ui = meta && (meta.exam_ui || meta.examUi);
    if (ui === "oge_rus_kim") {
      if (metaSubject && metaSubject !== "russian") return false;
      if (metaSubject === "russian") return true;
      // subject неизвестен — доверяем флагу только если задания не math
      if (tasks && tasks.length && tasks.every(function (t) {
        return subjectOf(t) === "math";
      })) {
        return false;
      }
      if (tasks && isOgeRusList(tasks)) return true;
      if (!tasks || !tasks.length) return true;
      return false;
    }

    if (tasks && isOgeRusList(tasks)) return true;

    if (meta) {
      const sc = metaSubject;
      const ec = examOf(meta);
      if (sc === "russian" && ec === "OGE") return true;
    }
    return false;
  }

  /** Баннер «новый UI» убран — не показывать декоративный preview до действия. */
  function examModeBannerHtml() {
    return "";
  }

  function kimTypeOf(task) {
    const p = payloadOf(task) || {};
    const fromPayload = Number(p.kim_type);
    if (fromPayload > 0) return fromPayload;
    const n = Number(task && (task.num != null ? task.num : task.task_number));
    return n > 0 ? n : 0;
  }

  function taskText(task) {
    return String((task && (task.text || task.template_text)) || "").replace(/\r\n/g, "\n");
  }

  function optionsFromPayload(p) {
    if (!p || !Array.isArray(p.options) || !p.options.length) return null;
    return p.options.map(function (o, i) {
      if (o == null) return { id: String(i + 1), text: "" };
      if (typeof o === "string" || typeof o === "number") {
        return { id: String(i + 1), text: String(o).trim() };
      }
      return {
        id: String(o.id != null ? o.id : i + 1),
        text: String(o.text != null ? o.text : "").trim(),
      };
    });
  }

  /**
   * Разбор инструкции и вариантов 1) 2) 3).
   * Работает и когда сервер/кэш склеил текст в одну строку (без \\n).
   * Не режет «(предложение 1)» — цифра после буквы/слова не считается маркером варианта.
   * Alias: splitNumberedOptions
   */
  function splitNumberedOptions(text) {
    const raw = normalizeNewlines(String(text || "")).trim();
    if (!raw) return { stem: "", options: [] };

    // 1) Классика: каждый вариант с новой строки
    const lineRe = /^(\d+)\)\s*(.+)$/gm;
    const lineOpts = [];
    let firstIdx = -1;
    let m;
    while ((m = lineRe.exec(raw)) !== null) {
      if (firstIdx < 0) firstIdx = m.index;
      lineOpts.push({ id: m[1], text: m[2].trim() });
    }
    if (lineOpts.length >= 2) {
      return { stem: raw.slice(0, firstIdx).trim(), options: lineOpts };
    }

    // 2) Плоский текст: «…ответов. 1) foo 2) bar»
    // Маркер: N) после начала/переноса/пунктуации/скобки/пробела-не-буквы.
    // Пропуск «(предложение 1)» — перед цифрой буква (после trim пробелов).
    const marks = [];
    const markRe = /(\d+)\)(?=\s|$)/g;
    while ((m = markRe.exec(raw)) !== null) {
      const pos = m.index;
      let k = pos - 1;
      while (k >= 0 && /[ \t]/.test(raw.charAt(k))) k--;
      const prev = k >= 0 ? raw.charAt(k) : "";
      // «(1) один…» — цифры вставки заданий 5/7, не варианты 1) 2) 3)
      if (prev === "(") continue;
      // буква / цифра перед N) → не вариант (предложение 1), год и т.п.)
      if (prev && /[A-Za-zА-Яа-яЁё0-9]/.test(prev)) continue;
      // внутри слова вроде «п1)» не бывает; отсекаем «№1)» только если нужно — оставляем
      const after = m.index + m[0].length;
      const textStart = after < raw.length && /\s/.test(raw.charAt(after)) ? after + 1 : after;
      marks.push({ id: m[1], pos: pos, textStart: textStart });
    }
    if (marks.length < 2 || marks[0].id !== "1") {
      return { stem: raw, options: [] };
    }
    // Требуем возрастающую нумерацию 1,2,3… (отсекает ложные совпадения)
    let seqOk = true;
    for (let i = 0; i < marks.length; i++) {
      if (Number(marks[i].id) !== i + 1) {
        seqOk = false;
        break;
      }
    }
    if (!seqOk) {
      // оставить только префикс 1..k пока идёт подряд
      const kept = [];
      for (let i = 0; i < marks.length; i++) {
        if (Number(marks[i].id) !== i + 1) break;
        kept.push(marks[i]);
      }
      if (kept.length < 2) return { stem: raw, options: [] };
      marks.length = 0;
      for (let i = 0; i < kept.length; i++) marks.push(kept[i]);
    }
    const options = [];
    for (let i = 0; i < marks.length; i++) {
      const end = i + 1 < marks.length ? marks[i + 1].pos : raw.length;
      options.push({
        id: marks[i].id,
        text: raw.slice(marks[i].textStart, end).trim(),
      });
    }
    return { stem: raw.slice(0, marks[0].pos).trim(), options: options };
  }

  function parseStemAndOptions(text) {
    return splitNumberedOptions(text);
  }

  /**
   * Статический HTML для учителя/экспорта: абзац-инструкция + строки «1) …».
   * Не использует formatMathText (тот схлопывает \\n в одну визуальную строку).
   */
  function formatProseTaskHtml(text) {
    const parsed = splitNumberedOptions(text);
    const parts = [];
    if (parsed.stem) {
      parts.push('<div class="oge-prose-stem">' + formatText(parsed.stem) + "</div>");
    }
    if (parsed.options.length) {
      parts.push(
        '<div class="oge-prose-options" role="list">' +
          parsed.options
            .map(function (o) {
              return (
                '<div class="oge-prose-opt" role="listitem">' +
                '<span class="oge-prose-opt-id">' +
                escapeHtml(o.id) +
                ")</span> " +
                '<span class="oge-prose-opt-text">' +
                formatText(o.text) +
                "</span></div>"
              );
            })
            .join("") +
          "</div>"
      );
    } else if (!parsed.stem && text) {
      return '<div class="oge-prose-stem">' + formatText(text) + "</div>";
    }
    return parts.join("");
  }

  /** Текст задания: ОГЭ-проза только для русского; math → KaTeX / formatMathText. */
  function formatTaskTextHtml(taskOrText) {
    const raw =
      taskOrText && typeof taskOrText === "object"
        ? taskText(taskOrText)
        : String(taskOrText || "");
    const asTask = taskOrText && typeof taskOrText === "object" ? taskOrText : null;
    if (asTask && subjectOf(asTask) === "math") {
      if (typeof global.formatMathText === "function") return global.formatMathText(raw);
      return formatText(raw);
    }
    // Проза 1) 2) 3) — только для подтверждённого ОГЭ русского
    if (asTask && isOgeRusTask(asTask)) {
      return formatProseTaskHtml(raw);
    }
    if (typeof global.formatMathText === "function") {
      // Сохраняем переносы: formatMathText их не превращает в <br>
      const src = normalizeNewlines(raw);
      if (/\n/.test(src) && !/\[\[|\\frac|\\sqrt|√/.test(src)) {
        return formatText(src);
      }
      return global.formatMathText(raw);
    }
    return formatText(raw);
  }

  function firstInstructionLine(stem) {
    const lines = normalizeNewlines(stem)
      .split(/\n+/)
      .map(function (l) {
        return l.trim();
      })
      .filter(Boolean);
    if (!lines.length) return "";
    const cleaned = lines.filter(function (l) {
      return !/^Тип\s+\d+/i.test(l);
    });
    const use = cleaned.length ? cleaned : lines;
    return use[0];
  }

  /** Инструкция vs тело: и при \\n, и когда всё в одной строке (старый кэш). */
  function splitInstructionAndBody(stem) {
    const raw = normalizeNewlines(stem).trim();
    if (!raw) return { instruction: "", body: "" };
    const lines = raw
      .split(/\n+/)
      .map(function (l) {
        return l.trim();
      })
      .filter(Boolean);
    if (lines.length >= 2) {
      const cleaned = lines.filter(function (l) {
        return !/^Тип\s+\d+/i.test(l);
      });
      const use = cleaned.length ? cleaned : lines;
      return { instruction: use[0], body: use.slice(1).join("\n").trim() };
    }
    const dig = raw.search(/\(\d+\)/);
    if (dig > 0) {
      const before = raw.slice(0, dig).trim();
      const m = before.match(/^(.*[.!?…])\s+/);
      if (m && m[1].length >= 12) {
        return {
          instruction: m[1].trim(),
          body: raw.slice(m[1].length).trim(),
        };
      }
      return { instruction: before, body: raw.slice(dig).trim() };
    }
    const cut = raw.search(/[.!?…]\s+(?=[«"(А-ЯA-Z])/);
    if (cut >= 12) {
      return {
        instruction: raw.slice(0, cut + 1).trim(),
        body: raw.slice(cut + 1).trim(),
      };
    }
    return { instruction: firstInstructionLine(raw), body: "" };
  }

  function stemWithoutMatchingTables(stem) {
    let s = normalizeNewlines(stem || "").trim();
    if (!s) return "";
    // Заголовки таблиц (с \\n и в «склеенном» тексте)
    let cut = s.search(
      /(?:\n|^)\s*(ПУНКТУАЦИОННЫЕ\s+ПРАВИЛА|ПРАВИЛА|ПРЕДЛОЖЕНИЯ)\s*(?:\n|:)/i
    );
    if (cut < 0) {
      cut = s.search(/(?:^|\s)(ПУНКТУАЦИОННЫЕ\s+ПРАВИЛА|ПРЕДЛОЖЕНИЯ)\s+(?=[АA1])/i);
    }
    // Блок А) Б) В) — если таблица уже в payload, не дублировать в stem
    if (cut < 0) {
      cut = s.search(/(?:^|\n)\s*[АA]\s*\)\s+/);
    }
    if (cut < 0) {
      cut = s.search(/\s[АA]\s*\)\s+\S/);
      if (cut > 40) {
        /* keep instruction before first А) */
      } else {
        cut = -1;
      }
    }
    if (cut >= 0) s = s.slice(0, cut).trim();
    s = s
      .replace(/\n?\s*Ответ запишите как три цифры[^\n]*/gi, "")
      .replace(/\n?\s*Запишите в ответ[^\n]*А\s*,?\s*Б\s*,?\s*В[^\n]*/gi, "")
      .trim();
    return s;
  }

  function stripLeadingMarker(text) {
    return String(text || "")
      .replace(/^\s*[А-ЯA-Zа-яa-z0-9]\s*[).：:]\s*/u, "")
      .replace(/^\s*[А-ЯA-Z]\s+(?=[А-ЯA-Zа-яa-z«"(])/u, "")
      .trim();
  }

  function isLetterId(id) {
    return /^[А-ЯA-Z]$/u.test(String(id || "").trim());
  }

  function isDigitId(id) {
    return /^\d+$/.test(String(id || "").trim());
  }

  function normalizeMatchSide(list, side) {
    const out = [];
    const raw = Array.isArray(list) ? list : [];
    raw.forEach(function (item, i) {
      let id = "";
      let text = "";
      if (item == null) return;
      if (typeof item === "string" || typeof item === "number") {
        text = String(item).trim();
        const m = text.match(/^([А-ЯA-Z0-9])\s*[).]\s*(.*)$/u);
        if (m) {
          id = m[1];
          text = m[2].trim();
        }
      } else {
        id = item.id != null ? String(item.id).trim() : "";
        text = item.text != null ? String(item.text) : "";
      }
      text = normalizeNewlines(text).trim();
      // Мусор вида одиночной «Б» / «В» без правила — не отдельная строка таблицы
      if (!text && isLetterId(id)) return;
      if (/^[А-ЯA-Z]$/u.test(text) && !id) return;
      if (/^[А-ЯA-Z]$/u.test(text) && isLetterId(id) && text === id) return;

      // Склеенный блок в одном item: «правило1\\nБ\\nправило2»
      const parts = text.split(/\n+/).map(function (l) {
        return l.trim();
      }).filter(Boolean);
      if (parts.length > 1 && parts.some(function (p) {
        return /^[А-ЯA-Z]$/u.test(p) || /^[А-ЯA-Z]\s*[).]/u.test(p);
      })) {
        let curId = id;
        let buf = [];
        function flush() {
          const t = buf.join(" ").trim();
          if (!t && !curId) return;
          if (/^[А-ЯA-Z]$/u.test(t)) return;
          out.push({
            id: curId || (side === "left" ? String.fromCharCode(1040 + out.length) : String(out.length + 1)),
            text: stripLeadingMarker(t),
          });
          buf = [];
        }
        parts.forEach(function (p) {
          const onlyLetter = /^([А-ЯA-Z])$/u.exec(p);
          const marked = /^([А-ЯA-Z0-9])\s*[).]\s*(.*)$/u.exec(p);
          if (onlyLetter) {
            flush();
            curId = onlyLetter[1];
            return;
          }
          if (marked && (!marked[2] || marked[2].length < 2)) {
            flush();
            curId = marked[1];
            return;
          }
          if (marked) {
            flush();
            curId = marked[1];
            buf.push(marked[2]);
            return;
          }
          buf.push(p);
        });
        flush();
        return;
      }

      if (!id) {
        id =
          side === "left"
            ? String.fromCharCode(1040 + out.length)
            : String(out.length + 1);
      }
      text = stripLeadingMarker(text);
      if (!text) return;
      // Не дублировать букву в тексте («А А) …» / «Б Между…»)
      if (isLetterId(id) && text.charAt(0) === id && /^[А-ЯA-Z]\s+/u.test(text)) {
        text = text.replace(/^[А-ЯA-Z]\s+/u, "").trim();
      }
      out.push({ id: id, text: text });
    });
    return out;
  }

  function parseMatchingFromStem(stem) {
    const raw = normalizeNewlines(stem || "");
    if (!raw) return { left: [], right: [] };
    const left = [];
    const right = [];
    const letterRe = /(?:^|\n)\s*([АБВГДЕЖЗИ])\s*\)\s*([^\n]+)/giu;
    let m;
    while ((m = letterRe.exec(raw)) !== null) {
      const text = stripLeadingMarker(m[2]);
      if (text && !/^[А-ЯA-Z]$/u.test(text)) left.push({ id: m[1].toUpperCase(), text: text });
    }
    const digitRe = /(?:^|\n)\s*(\d{1,2})\s*\)\s*([^\n]+)/g;
    while ((m = digitRe.exec(raw)) !== null) {
      const text = stripLeadingMarker(m[2]);
      if (text) right.push({ id: m[1], text: text });
    }
    return { left: left, right: right };
  }

  function matchingFromOptions(p) {
    const opts = optionsFromPayload(p);
    if (!opts || !opts.length) return null;
    const letterOpts = opts.filter(function (o) {
      return isLetterId(o.id);
    });
    const digitOpts = opts.filter(function (o) {
      return isDigitId(o.id);
    });
    if (letterOpts.length >= 2 && digitOpts.length >= 2) {
      return { left: letterOpts, right: digitOpts };
    }
    if (letterOpts.length >= 2 && digitOpts.length === 0) {
      return { left: letterOpts, right: [] };
    }
    return null;
  }

  function matchingOf(task) {
    const p = payloadOf(task) || {};
    let matching = p.matching && typeof p.matching === "object" ? p.matching : null;
    let left = matching && Array.isArray(matching.left) ? matching.left : [];
    let right = matching && Array.isArray(matching.right) ? matching.right : [];
    left = normalizeMatchSide(left, "left");
    right = normalizeMatchSide(right, "right");
    if (!left.length && !right.length) {
      const fromOpts = matchingFromOptions(p);
      if (fromOpts) {
        left = normalizeMatchSide(fromOpts.left, "left");
        right = normalizeMatchSide(fromOpts.right, "right");
      }
    }
    if (!left.length || !right.length) {
      const parsed = parseMatchingFromStem(taskText(task));
      if (!left.length) left = normalizeMatchSide(parsed.left, "left");
      if (!right.length) right = normalizeMatchSide(parsed.right, "right");
    }
    return { left: left, right: right };
  }

  function markSentenceNums(htmlOrText) {
    return formatPassageHtml(htmlOrText);
  }

  function markDigitInserts(text) {
    // Цифры вставки (5, 7) остаются в строке; переносы абзацев сохраняем
    const src = normalizeNewlines(text);
    const html = escapeHtml(src)
      .replace(/\((\d+)\)(\.{0,2})/g, '<span class="oge-digit-mark">($1)$2</span>');
    if (/\n\n/.test(html)) {
      return html
        .split(/\n\n+/)
        .map(function (p) {
          return '<p class="oge-fmt-p">' + p.replace(/\n/g, "<br>") + "</p>";
        })
        .join("");
    }
    return html.replace(/\n/g, "<br>");
  }

  function extractDigitIds(text) {
    const ids = [];
    const re = /\((\d+)\)/g;
    let m;
    while ((m = re.exec(String(text || ""))) !== null) {
      if (!ids.includes(m[1])) ids.push(m[1]);
    }
    return ids;
  }

  function splitReadingPassage(raw) {
    const text = String(raw || "").trim();
    if (!text) return { author: "", body: "", note: "" };
    const lines = text.split(/\n/);
    let author = "";
    let start = 0;
    for (let i = 0; i < lines.length; i++) {
      const t = lines[i].trim();
      if (!t) {
        if (author) {
          start = i + 1;
          break;
        }
        continue;
      }
      if (!author && !/^\(\d+\)/.test(t) && t.length < 120) {
        author = t;
        continue;
      }
      if (author) {
        start = i;
        break;
      }
      start = i;
      break;
    }
    let bodyLines = lines.slice(start);
    let note = "";
    for (let i = bodyLines.length - 1; i >= 0; i--) {
      const t = bodyLines[i].trim();
      if (!t) continue;
      if (!/\(\d+\)/.test(t) && t.length > 20) {
        note = t;
        bodyLines = bodyLines.slice(0, i);
      }
      break;
    }
    return {
      author,
      body: bodyLines.join("\n").trim(),
      note,
    };
  }

  var TTS_RATE_KEY = "edusense_tts_rate";
  var TTS_VOICE_KEY = "edusense_tts_voice_pref"; // male | female
  var TTS_RATES = [0.8, 1, 1.25];
  var _ttsSession = {
    speaking: false,
    paused: false,
    voiceURI: "",
    round: 0,
    text: "",
    onStatus: null,
  };

  function getTtsRate() {
    try {
      var r = Number(global.localStorage && localStorage.getItem(TTS_RATE_KEY));
      if (TTS_RATES.indexOf(r) >= 0) return r;
    } catch (_) {}
    return 1;
  }

  function setTtsRate(rate) {
    var r = Number(rate);
    if (TTS_RATES.indexOf(r) < 0) r = 1;
    try {
      if (global.localStorage) localStorage.setItem(TTS_RATE_KEY, String(r));
    } catch (_) {}
    return r;
  }

  function getVoicePref() {
    try {
      var p = String((global.localStorage && localStorage.getItem(TTS_VOICE_KEY)) || "");
      if (p === "male" || p === "female") return p;
    } catch (_) {}
    return "male";
  }

  function setVoicePref(pref) {
    var p = pref === "female" ? "female" : "male";
    try {
      if (global.localStorage) localStorage.setItem(TTS_VOICE_KEY, p);
    } catch (_) {}
    return p;
  }

  function listRuVoices() {
    if (typeof global.speechSynthesis === "undefined") return [];
    var voices = global.speechSynthesis.getVoices() || [];
    return voices.filter(function (v) {
      var lang = String((v && v.lang) || "");
      var name = String((v && v.name) || "");
      return /^ru(-|$)/i.test(lang) || /russian/i.test(name);
    });
  }

  function voiceScoreForPref(v, pref) {
    var n = String((v && v.name) || "") + " " + String((v && v.voiceURI) || "");
    var lang = String((v && v.lang) || "");
    var s = 0;
    if (/^ru(-|$)/i.test(lang) || /russian/i.test(n)) s += 20;
    if (/neural|online/i.test(n)) s += 50;
    if (/google|microsoft|edge|yandex/i.test(n)) s += 25;
    if (v && v.localService === false) s += 10;
    if (pref === "female") {
      if (/svetlana|irina|milena|katya|elena|anna|female|жен/i.test(n)) s += 120;
      if (/dmitry|pavel|male|муж/i.test(n)) s -= 80;
    } else {
      if (/dmitry|pavel|male|муж/i.test(n)) s += 120;
      if (/svetlana|irina|milena|katya|elena|anna|female|жен/i.test(n)) s -= 80;
    }
    return s;
  }

  function resolveVoice(pref) {
    var want = pref === "female" ? "female" : "male";
    var pool = listRuVoices();
    if (!pool.length && typeof global.speechSynthesis !== "undefined") {
      pool = global.speechSynthesis.getVoices() || [];
    }
    if (!pool.length) return null;
    pool = pool.slice().sort(function (a, b) {
      return voiceScoreForPref(b, want) - voiceScoreForPref(a, want);
    });
    return pool[0] || null;
  }

  function pickRussianVoice() {
    return resolveVoice(getVoicePref());
  }

  if (typeof global.speechSynthesis !== "undefined") {
    try {
      global.speechSynthesis.getVoices();
      global.speechSynthesis.addEventListener("voiceschanged", function () {
        global.speechSynthesis.getVoices();
      });
    } catch (_) {}
  }

  function ttsControlsHtml(num) {
    var cur = getTtsRate();
    var pref = getVoicePref();
    var labels = ["0.8×", "1.0×", "1.25×"];
    var rateBtns = TTS_RATES.map(function (r, i) {
      return (
        '<button type="button" class="oge-rus-speed-btn' +
        (r === cur ? " is-active" : "") +
        '" data-oge-tts-rate="' +
        r +
        '">' +
        labels[i] +
        "</button>"
      );
    });
    return (
      '<div class="oge-rus-tts-toolbar">' +
      '<div class="oge-rus-voice" role="group" aria-label="Голос">' +
      '<span class="oge-rus-speed-label">Голос</span>' +
      '<button type="button" class="oge-rus-voice-btn' +
      (pref === "male" ? " is-active" : "") +
      '" data-oge-tts-voice="male">Мужской</button>' +
      '<button type="button" class="oge-rus-voice-btn' +
      (pref === "female" ? " is-active" : "") +
      '" data-oge-tts-voice="female">Женский</button>' +
      "</div>" +
      '<div class="oge-rus-speed" role="group" aria-label="Скорость">' +
      '<span class="oge-rus-speed-label">Скорость</span>' +
      rateBtns.join("") +
      "</div>" +
      "</div>"
    );
  }

  function ttsRateHtml(num) {
    return ttsControlsHtml(num);
  }

  function applyPlaybackRate(root) {
    var rate = getTtsRate();
    var pref = getVoicePref();
    var scope = root || document;
    scope.querySelectorAll("audio.oge-rus-audio").forEach(function (el) {
      try {
        el.playbackRate = rate;
      } catch (_) {}
    });
    scope.querySelectorAll("[data-oge-tts-rate]").forEach(function (btn) {
      btn.classList.toggle("is-active", Number(btn.getAttribute("data-oge-tts-rate")) === rate);
    });
    scope.querySelectorAll("[data-oge-tts-voice]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-oge-tts-voice") === pref);
    });
    syncPauseButtons(scope);
  }

  function syncPauseButtons(root) {
    var scope = root || document;
    var playing = !!_ttsSession.speaking;
    var paused = !!_ttsSession.paused;
    scope.querySelectorAll("[data-oge-tts-pause]").forEach(function (btn) {
      btn.disabled = !playing;
      btn.textContent = paused ? "Продолжить" : "Пауза";
      btn.setAttribute("aria-pressed", paused ? "true" : "false");
    });
    scope.querySelectorAll("[data-oge-tts]").forEach(function (btn) {
      if (playing && !paused) btn.textContent = "Стоп";
      else btn.textContent = "Прослушать 2 раза";
    });
  }

  function stopTts(onStatus) {
    _ttsSession.speaking = false;
    _ttsSession.paused = false;
    _ttsSession.round = 0;
    _ttsSession.text = "";
    if (typeof global.speechSynthesis !== "undefined") {
      try {
        global.speechSynthesis.cancel();
      } catch (_) {}
    }
    if (onStatus) onStatus("Остановлено.");
    syncPauseButtons(document);
  }

  function toggleTtsPause(onStatus) {
    if (typeof global.speechSynthesis === "undefined") return;
    var synth = global.speechSynthesis;
    if (!_ttsSession.speaking) return;
    if (_ttsSession.paused) {
      try {
        synth.resume();
      } catch (_) {}
      _ttsSession.paused = false;
      if (onStatus) onStatus("Прослушивание " + _ttsSession.round + " из 2…");
    } else {
      try {
        synth.pause();
      } catch (_) {}
      _ttsSession.paused = true;
      if (onStatus) onStatus("Пауза. Нажмите «Продолжить».");
    }
    syncPauseButtons(document);
  }

  function speakTwice(text, onStatus) {
    if (!text || typeof global.speechSynthesis === "undefined") {
      if (onStatus) onStatus("Синтез речи недоступен в этом браузере.");
      return;
    }
    // Повторный клик по «Прослушать» во время чтения = стоп
    if (_ttsSession.speaking && !_ttsSession.paused) {
      stopTts(onStatus);
      return;
    }
    if (_ttsSession.speaking && _ttsSession.paused) {
      toggleTtsPause(onStatus);
      return;
    }

    const synth = global.speechSynthesis;
    try {
      synth.cancel();
    } catch (_) {}

    const rate = getTtsRate();
    const pref = getVoicePref();
    // Один голос на оба прохода — выбираем ДО старта и не меняем
    let lockedVoice = resolveVoice(pref);
    if (!lockedVoice) {
      const voicesNow = synth.getVoices() || [];
      if (!voicesNow.length) {
        setTimeout(function () {
          speakTwice(text, onStatus);
        }, 280);
        return;
      }
      lockedVoice = resolveVoice(pref);
    }

    _ttsSession.speaking = true;
    _ttsSession.paused = false;
    _ttsSession.text = text;
    _ttsSession.onStatus = onStatus;
    _ttsSession.voiceURI = lockedVoice ? lockedVoice.voiceURI || lockedVoice.name : "";
    syncPauseButtons(document);

    const utter = (round) => {
      if (!_ttsSession.speaking) return;
      _ttsSession.round = round;
      const u = new SpeechSynthesisUtterance(text);
      u.lang = (lockedVoice && lockedVoice.lang) || "ru-RU";
      u.rate = rate;
      if (lockedVoice) u.voice = lockedVoice;
      u.onstart = function () {
        _ttsSession.paused = false;
        if (onStatus) onStatus("Прослушивание " + round + " из 2…");
        syncPauseButtons(document);
      };
      u.onend = function () {
        if (!_ttsSession.speaking) return;
        if (round >= 2) {
          _ttsSession.speaking = false;
          _ttsSession.paused = false;
          if (onStatus) onStatus("Прослушивание завершено.");
          syncPauseButtons(document);
          return;
        }
        // Без паузы между 1 и 2 — сразу второй раз тем же голосом
        utter(2);
      };
      u.onerror = function () {
        _ttsSession.speaking = false;
        _ttsSession.paused = false;
        if (onStatus) onStatus("Ошибка воспроизведения.");
        syncPauseButtons(document);
      };
      synth.speak(u);
    };
    utter(1);
  }

  /** Проиграть <audio> два раза с паузой (как на экзамене). */
  function playAudioTwice(audioEl, onStatus, fallbackText) {
    if (!audioEl) {
      if (fallbackText) {
        speakTwice(fallbackText, onStatus);
        return;
      }
      if (onStatus) onStatus("Аудио не найдено.");
      return;
    }
    try {
      audioEl.pause();
    } catch (_) {}
    let round = 1;
    const cleanup = function () {
      audioEl.removeEventListener("ended", onEnded);
      audioEl.removeEventListener("error", onErr);
    };
    const useFallback = function (msg) {
      cleanup();
      if (fallbackText) {
        if (onStatus) onStatus(msg || "Запись недоступна — синтез речи.");
        speakTwice(fallbackText, onStatus);
        return;
      }
      if (onStatus) onStatus(msg || "Ошибка воспроизведения записи.");
    };
    const onErr = function () {
      const nxt = nextAudioSrc(audioEl);
      if (nxt) {
        try {
          audioEl.src = nxt;
          audioEl.load();
          audioEl.playbackRate = getTtsRate();
          audioEl.currentTime = 0;
          const p2 = audioEl.play();
          if (p2 && typeof p2.catch === "function") {
            p2.catch(function () {
              useFallback("Запись недоступна — включаю синтез речи.");
            });
          }
          return;
        } catch (_) {}
      }
      useFallback("Запись недоступна — включаю синтез речи.");
    };
    const onEnded = function () {
      if (round >= 2) {
        cleanup();
        if (onStatus) onStatus("Прослушивание завершено (2 раза).");
        return;
      }
      round = 2;
      if (onStatus) onStatus("Пауза… сейчас повтор");
      setTimeout(function () {
        if (onStatus) onStatus("Прослушивание 2 из 2…");
        try {
          audioEl.playbackRate = getTtsRate();
          audioEl.currentTime = 0;
          const p = audioEl.play();
          if (p && typeof p.catch === "function") {
            p.catch(function () {
              useFallback("Не удалось запустить повтор.");
            });
          }
        } catch (_) {
          useFallback("Не удалось запустить повтор.");
        }
      }, 200);
    };
    cleanup();
    audioEl.addEventListener("ended", onEnded);
    audioEl.addEventListener("error", onErr);
    if (onStatus) onStatus("Прослушивание 1 из 2…");
    try {
      audioEl.playbackRate = getTtsRate();
      audioEl.currentTime = 0;
      const p = audioEl.play();
      if (p && typeof p.catch === "function") {
        p.catch(function () {
          useFallback("Не удалось запустить аудио.");
        });
      }
    } catch (_) {
      useFallback("Не удалось запустить аудио.");
    }
  }

  function collectAudioCandidates(p, cid) {
    const out = [];
    const seen = {};
    function add(u) {
      const s = String(u || "").trim();
      if (!s || seen[s]) return;
      seen[s] = 1;
      out.push(s);
    }
    add(p.audio_url || p.audio);
    if (cid) {
      add("/audio/oge_rus/" + cid + ".mp3");
      add("/audio/oge_rus/" + cid + ".wav");
    }
    return out;
  }

  function nextAudioSrc(audioEl) {
    if (!audioEl) return "";
    const list = String(audioEl.getAttribute("data-oge-audio-srcs") || "")
      .split("|")
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
    const cur = String(audioEl.getAttribute("src") || audioEl.currentSrc || "");
    let idx = -1;
    for (let i = 0; i < list.length; i++) {
      if (cur === list[i] || cur.indexOf(list[i]) >= 0) {
        idx = i;
        break;
      }
    }
    const next = list[idx + 1];
    return next || "";
  }

  function bindAudioSrcFallback(audioEl) {
    if (!audioEl || audioEl.dataset.srcFallbackBound) return;
    audioEl.dataset.srcFallbackBound = "1";
    audioEl.addEventListener("error", function () {
      const nxt = nextAudioSrc(audioEl);
      if (!nxt) return;
      audioEl.src = nxt;
      try {
        audioEl.load();
      } catch (_) {}
    });
  }

  function renderRubricHint(p) {
    const r = p && p.rubric;
    if (!r || !Array.isArray(r.criteria) || !r.criteria.length) return "";
    const bits = r.criteria.map(function (c) {
      return String(c.title || c.id || "") + (c.max != null ? " (" + c.max + ")" : "");
    });
    const max = r.criteria.reduce(function (s, c) {
      return s + (Number(c.max) || 0);
    }, 0);
    return (
      '<p class="oge-rus-rubric-hint">Критерии: ' +
      escapeHtml(bits.join(" · ")) +
      (max ? " · макс. " + max : "") +
      ".</p>"
    );
  }

  function renderListeningBlock(task, opts) {
    const p = payloadOf(task) || {};
    const script = p.listening_text || "";
    const cid = String((task && task.context_id) || p.context_id || "").trim();
    const srcs = collectAudioCandidates(p, cid);
    const audioUrl = srcs[0] || "";
    const showTeacher = !!(opts && opts.teacher);
    const hide = p.hide_transcript_default !== false && !showTeacher;
    const num = task.num != null ? task.num : 1;
    const isPrint = !!(opts && opts.print);

    if (isPrint) {
      const transcript =
        showTeacher && opts.showKey && script
          ? '<div class="oge-rus-transcript-body">' +
            formatText(script) +
            "</div>" +
            (p.listening_author
              ? '<p class="oge-rus-author">' + escapeHtml(p.listening_author) + "</p>"
              : "")
          : "";
      return (
        '<div class="oge-rus-listen is-print" data-oge-listen="' +
        escapeHtml(num) +
        '"><p class="oge-rus-listen-hint">Задание 1 · сжатое изложение. На экзамене текст звучит дважды. Объём — не менее ' +
        essayMinWords(p, 70) +
        " слов.</p>" +
        (opts.showKey ? renderRubricHint(p) : "") +
        transcript +
        "</div>"
      );
    }

    let playerHtml = "";
    // Основная озвучка — нейроголос браузера; голос выбирается один раз и не меняется между 1 и 2.
    const ttsBtn =
      '<button type="button" class="oge-rus-play-twice oge-rus-tts" data-oge-tts="' +
      escapeHtml(num) +
      '" ' +
      (script ? "" : "disabled") +
      ">Прослушать 2 раза</button>";
    const pauseBtn =
      '<button type="button" class="oge-rus-pause-btn" data-oge-tts-pause="' +
      escapeHtml(num) +
      '" disabled>Пауза</button>';
    const mp3Btn = audioUrl
      ? '<button type="button" class="oge-rus-play-mp3" data-oge-play-twice="' +
        escapeHtml(num) +
        '">Запись MP3</button>'
      : "";
    playerHtml =
      '<div class="oge-rus-audio-player" data-oge-audio-player="' +
      escapeHtml(num) +
      '">' +
      (audioUrl
        ? '<div class="oge-rus-audio-bar" hidden>' +
          '<audio class="oge-rus-audio" preload="metadata" src="' +
          escapeHtml(audioUrl) +
          '" data-oge-audio-srcs="' +
          escapeHtml(srcs.join("|")) +
          '"></audio></div>'
        : "") +
      '<div class="oge-rus-audio-actions">' +
      ttsBtn +
      pauseBtn +
      mp3Btn +
      "</div>" +
      ttsControlsHtml(num) +
      '<span class="oge-rus-tts-status" data-oge-tts-status="' +
      escapeHtml(num) +
      '"></span>' +
      '<p class="oge-rus-audio-note">Выберите голос один раз — он останется на оба прослушивания. Можно поставить на паузу.</p>' +
      "</div>";

    if (!script && !audioUrl) {
      playerHtml =
        '<p class="oge-rus-listen-fallback"><strong>Текст для прослушивания не загружен.</strong></p>';
    }

    const transcript = script
      ? '<details class="oge-rus-transcript" ' +
        (hide ? "" : "open") +
        "><summary>" +
        (hide ? "Расшифровка записи (показать)" : "Расшифровка записи") +
        '</summary><div class="oge-rus-transcript-body">' +
        formatText(script) +
        "</div>" +
        (p.listening_author
          ? '<p class="oge-rus-author">' + escapeHtml(p.listening_author) + "</p>"
          : "") +
        "</details>"
      : "";

    return (
      '<div class="oge-rus-listen" data-oge-listen="' +
      escapeHtml(num) +
      '" data-oge-listen-text="' +
      escapeHtml(script) +
      '"><p class="oge-rus-listen-hint">Задание 1 · сжатое изложение. На экзамене текст звучит дважды. Объём — не менее ' +
      essayMinWords(p, 70) +
      " слов.</p>" +
      renderRubricHint(p) +
      '<div class="oge-rus-listen-controls">' +
      playerHtml +
      "</div>" +
      transcript +
      "</div>"
    );
  }

  function renderSharedBlock(kind, text, opts) {
    if (!text) return "";
    const options = opts || {};
    const collapsed = !!options.collapsed;
    const uid =
      "oge-shared-" +
      kind +
      "-" +
      String(options.uid != null ? options.uid : Math.random().toString(36).slice(2, 8));

    if (kind === "reading") {
      const parts = splitReadingPassage(text);
      return (
        '<aside class="oge-rus-shared" data-oge-shared="reading" data-oge-collapse-root="' +
        escapeHtml(uid) +
        '">' +
        '<div class="oge-rus-shared-head">' +
        '<h4 class="oge-rus-shared-title">Прочитайте текст и выполните задания 10–12</h4>' +
        (options.print
          ? ""
          : '<button type="button" class="oge-rus-collapse-btn" data-oge-collapse="' +
            escapeHtml(uid) +
            '" aria-expanded="' +
            (collapsed ? "false" : "true") +
            '">' +
            (collapsed ? "Развернуть" : "Свернуть") +
            "</button>") +
        "</div>" +
        (parts.author
          ? '<p class="oge-passage-author">' + escapeHtml(parts.author) + "</p>"
          : "") +
        '<div class="oge-rus-shared-body oge-passage-body" data-oge-collapse-body="' +
        escapeHtml(uid) +
        '"' +
        (collapsed ? ' hidden' : "") +
        ">" +
        formatPassageHtml(parts.body || text) +
        "</div>" +
        (parts.note
          ? '<p class="oge-passage-note">' + escapeHtml(parts.note) + "</p>"
          : "") +
        "</aside>"
      );
    }
    return (
      '<aside class="oge-rus-shared" data-oge-shared="grammar" data-oge-collapse-root="' +
      escapeHtml(uid) +
      '">' +
      '<div class="oge-rus-shared-head">' +
      '<h4 class="oge-rus-shared-title">Прочитайте текст и выполните задания 2–3</h4>' +
      (options.print
        ? ""
        : '<button type="button" class="oge-rus-collapse-btn" data-oge-collapse="' +
          escapeHtml(uid) +
          '" aria-expanded="' +
          (collapsed ? "false" : "true") +
          '">' +
          (collapsed ? "Развернуть" : "Свернуть") +
          "</button>") +
      "</div>" +
      '<div class="oge-rus-shared-body oge-passage-body" data-oge-collapse-body="' +
      escapeHtml(uid) +
      '"' +
      (collapsed ? " hidden" : "") +
      ">" +
      formatPassageHtml(text) +
      "</div></aside>"
    );
  }

  function findSharedText(list, key) {
    for (let i = 0; i < list.length; i++) {
      const p = payloadOf(list[i]) || {};
      if (p[key]) return String(p[key]);
    }
    return "";
  }

  function renderMatching(task) {
    const matching = matchingOf(task);
    const left = matching.left;
    const right = matching.right;
    if (!left.length && !right.length) return "";
    const leftHtml = left
      .map(function (item) {
        const id = String(item.id);
        const text = item.text || "";
        return (
          '<div class="oge-exam-match-item oge-rus-match-row" data-match-left="' +
          escapeHtml(id) +
          '">' +
          '<span class="oge-exam-match-letter" aria-hidden="true">' +
          escapeHtml(id) +
          ")</span>" +
          '<span class="oge-rus-match-left oge-exam-match-text">' +
          formatText(text) +
          "</span>" +
          '<input class="oge-exam-match-input oge-rus-match-input" type="text" inputmode="numeric" maxlength="1" autocomplete="off" data-oge-match="' +
          escapeHtml(id) +
          '" data-num="' +
          escapeHtml(task.num) +
          '" aria-label="Номер предложения для ' +
          escapeHtml(id) +
          '" /></div>'
        );
      })
      .join("");
    const rightHtml = right
      .map(function (item) {
        const id = String(item.id);
        const text = item.text || "";
        return (
          '<div class="oge-exam-match-item oge-rus-match-right" data-match-right="' +
          escapeHtml(id) +
          '">' +
          '<span class="oge-exam-match-right-id">' +
          escapeHtml(id) +
          ")</span>" +
          '<span class="oge-exam-match-text">' +
          formatText(text) +
          "</span></div>"
        );
      })
      .join("");
    return (
      '<div class="oge-exam-match oge-rus-matching" data-oge-matching="' +
      escapeHtml(task.num) +
      '">' +
      '<div class="kim-table-scroll">' +
      '<div class="oge-exam-match-table oge-rus-match-cols" role="group" aria-label="Соответствие правил и предложений">' +
      '<div class="oge-exam-match-col oge-exam-match-col--left">' +
      '<p class="oge-exam-match-head">Пунктуационные правила</p>' +
      leftHtml +
      "</div>" +
      '<div class="oge-exam-match-col oge-exam-match-col--right">' +
      '<p class="oge-exam-match-head">Предложения</p>' +
      rightHtml +
      "</div></div></div>" +
      '<p class="oge-exam-answer-hint oge-rus-match-hint">' +
      "Впишите номер предложения (1–5) для А, Б, В. В бланк уйдёт три цифры подряд (АБВ).</p></div>"
    );
  }

  function renderEssayChoice(task) {
    const p = payloadOf(task) || {};
    const opts = Array.isArray(p.essay_options) ? p.essay_options : [];
    if (!opts.length) return "";
    const name = "oge-essay-" + task.num;
    // Не дублируем текст чтения заранее — он уже над 10–12; подсказка без «превью»
    const readingHint =
      '<p class="oge-rus-essay-reading-hint">Сочинение пишется <strong>по прочитанному тексту</strong> (задания 10–12). При необходимости вернитесь к тексту выше.</p>';

    const radios = opts
      .map(function (opt, i) {
        const kind = String((opt && opt.type) || "13." + (i + 1));
        const title = String((opt && opt.title) || "");
        const statement = String((opt && opt.statement) || "");
        return (
          '<label class="oge-rus-essay-opt">' +
          '<span class="oge-rus-essay-opt-top">' +
          '<input type="radio" name="' +
          escapeHtml(name) +
          '" value="' +
          escapeHtml(kind) +
          '" data-oge-essay-opt="' +
          escapeHtml(task.num) +
          '" />' +
          '<span class="oge-rus-essay-opt-badge">' +
          escapeHtml(kind) +
          "</span>" +
          '<span class="oge-rus-essay-opt-label">' +
          escapeHtml(title || "Вариант сочинения") +
          "</span></span>" +
          '<div class="oge-rus-essay-stmt">' +
          formatText(statement) +
          "</div></label>"
        );
      })
      .join("");
    return (
      '<div class="oge-rus-essay" data-oge-essay="' +
      escapeHtml(task.num) +
      '">' +
      '<p class="oge-rus-essay-intro">Используя прочитанный текст, выполните <strong>ТОЛЬКО ОДНО</strong> из заданий: 13.1, 13.2 или 13.3. ' +
      "Перед написанием сочинения запишите номер выбранного задания: <strong>13.1</strong>, <strong>13.2</strong> или <strong>13.3</strong>. " +
      "Объём сочинения — <strong>не менее " +
      essayMinWords(p, 70) +
      " слов</strong>. " +
      "Если сочинение написано менее чем на " +
      essayMinWords(p, 70) +
      " слов, то такая работа не засчитывается и оценивается 0 баллов (критерий СК1). " +
      "Если сочинение представляет собой пересказанный или полностью переписанный исходный текст без каких бы то ни было комментариев, то такая работа оценивается 0 баллов.</p>" +
      readingHint +
      renderRubricHint(p) +
      '<p class="oge-rus-essay-hint">Выберите одно задание (13.1 / 13.2 / 13.3), затем напишите полный текст сочинения-рассуждения в поле ниже.</p>' +
      '<div class="oge-rus-essay-choices" role="radiogroup" aria-label="Варианты сочинения 13.1–13.3">' +
      radios +
      "</div></div>"
    );
  }

  function renderEssayAnswerPanel(task, answerState, opts) {
    // У учителя не показываем пустой мок поля ответа — только формулировки 13.x
    if (opts && opts.teacher) return "";
    const a = answerState || { mode: "text", text: "", photoDataUrl: "" };
    const isPhoto = a.mode === "photo";
    const num = task.num;
    return (
      '<div class="oge-open-answer answer-panel oge-essay-answer">' +
      '<div class="answer-tabs">' +
      '<button type="button" data-mode="text" data-num="' +
      num +
      '" class="' +
      (!isPhoto ? "is-active" : "") +
      '">Текст сочинения</button>' +
      '<button type="button" data-mode="photo" data-num="' +
      num +
      '" class="' +
      (isPhoto ? "is-active" : "") +
      '">Фото работы</button></div>' +
      (isPhoto
        ? '<div class="photo-box"><label><strong style="color:inherit">Загрузить фото</strong>' +
          '<div style="margin-top:6px;font-size:.85rem">Сфотографируйте сочинение в тетради</div>' +
          '<input type="file" accept="image/*" capture="environment" data-photo="' +
          num +
          '" /></label>' +
          (a.photoDataUrl
            ? '<img class="photo-preview" src="' +
              a.photoDataUrl +
              '" alt="Фото сочинения №' +
              num +
              '" />'
            : "") +
          "</div>"
        : '<textarea class="oge-essay-textarea" data-answer="' +
          num +
          '" rows="16" placeholder="Сначала выберите 13.1 / 13.2 / 13.3. Затем напишите сочинение-рассуждение (≥' +
          essayMinWords(payloadOf(task) || {}, 70) +
          ' слов)…">' +
          escapeHtml(a.text || "") +
          "</textarea>" +
          '<p class="oge-rus-essay-meta">Рекомендуемый объём: от ' +
          essayMinWords(payloadOf(task) || {}, 70) +
          " слов · аргументы — из прочитанного текста</p>") +
      "</div>"
    );
  }

  function renderMultiOptions(task, options, saved) {
    const num = task.num;
    const selected = new Set(
      String(saved || "")
        .replace(/\D/g, "")
        .split("")
        .filter(Boolean)
    );
    const items = options
      .map(function (o) {
        const id = String(o.id);
        const checked = selected.has(id) ? "checked" : "";
        return (
          '<label class="oge-exam-opt"><input type="checkbox" value="' +
          escapeHtml(id) +
          '" data-oge-multi="' +
          escapeHtml(num) +
          '" ' +
          checked +
          ' /><span class="oge-exam-opt-id">' +
          escapeHtml(id) +
          ')</span><span class="oge-exam-opt-text">' +
          formatText(o.text) +
          "</span></label>"
        );
      })
      .join("");
    return (
      '<div class="oge-exam-options" data-oge-multi-box="' +
      escapeHtml(num) +
      '">' +
      items +
      "</div>"
    );
  }

  function renderDigitPickers(task, digitIds, saved) {
    const num = task.num;
    const selected = new Set(
      String(saved || "")
        .replace(/\D/g, "")
        .split("")
        .filter(Boolean)
    );
    const items = digitIds
      .map(function (id) {
        const checked = selected.has(String(id)) ? "checked" : "";
        return (
          '<label class="oge-exam-digit"><input type="checkbox" value="' +
          escapeHtml(id) +
          '" data-oge-multi="' +
          escapeHtml(num) +
          '" ' +
          checked +
          " /><span>(" +
          escapeHtml(id) +
          ")</span></label>"
        );
      })
      .join("");
    return (
      '<div class="oge-exam-digits" data-oge-multi-box="' +
      escapeHtml(num) +
      '">' +
      items +
      '</div><p class="oge-exam-answer-hint">Отметьте цифры; в ответ уйдёт последовательность без пробелов.</p>'
    );
  }

  function renderAnswerLine(task, saved, conf) {
    conf = conf || {};
    const num = task.num;
    const val = escapeHtml(saved || "");
    if (conf.short) {
      return (
        '<div class="oge-exam-blank-wrap"><span class="oge-exam-blank-label">Ответ:</span>' +
        '<input class="oge-exam-blank" type="text" data-answer="' +
        escapeHtml(num) +
        '" data-oge-short="' +
        escapeHtml(num) +
        '" value="' +
        val +
        '" placeholder="' +
        escapeHtml(conf.placeholder || "…") +
        '" autocomplete="off" /></div>'
      );
    }
    return (
      '<div class="oge-exam-answer-line"><label for="oge-ans-' +
      escapeHtml(num) +
      '">Ответ:</label>' +
      '<input id="oge-ans-' +
      escapeHtml(num) +
      '" class="oge-exam-answer-input" type="text" inputmode="numeric" data-answer="' +
      escapeHtml(num) +
      '" value="' +
      val +
      '" placeholder="цифры" autocomplete="off" /></div>'
    );
  }

  function renderOpenAnswerPanel(task, answerState) {
    const a = answerState || { mode: "text", text: "", photoDataUrl: "" };
    const isPhoto = a.mode === "photo";
    return (
      '<div class="oge-open-answer answer-panel"><div class="answer-tabs">' +
      '<button type="button" data-mode="text" data-num="' +
      task.num +
      '" class="' +
      (!isPhoto ? "is-active" : "") +
      '">Ответ текстом</button>' +
      '<button type="button" data-mode="photo" data-num="' +
      task.num +
      '" class="' +
      (isPhoto ? "is-active" : "") +
      '">Фото решения</button></div>' +
      (isPhoto
        ? '<div class="photo-box"><label><strong style="color:inherit">Загрузить фото</strong>' +
          '<div style="margin-top:6px;font-size:.85rem">Сфотографируйте решение в тетради</div>' +
          '<input type="file" accept="image/*" capture="environment" data-photo="' +
          task.num +
          '" /></label>' +
          (a.photoDataUrl
            ? '<img class="photo-preview" src="' +
              a.photoDataUrl +
              '" alt="Фото решения №' +
              task.num +
              '" />'
            : "") +
          "</div>"
        : '<textarea data-answer="' +
          task.num +
          '" placeholder="Введите ответ…">' +
          escapeHtml(a.text || "") +
          "</textarea>") +
      "</div>"
    );
  }

  function renderTeacherKey(task) {
    const kim = kimTypeOf(task);
    const raw = String((task && task.answer) || "").trim();
    const hint = String((task && (task.solution || task.solution_hint)) || "").trim();
    const placeholder = !raw || /^развёрнут/i.test(raw);
    const open = kim === 1 || kim === 13;
    let ans = raw;
    if (kim === 4 && /^\d{3}$/.test(raw)) {
      ans = "А → " + raw.charAt(0) + " · Б → " + raw.charAt(1) + " · В → " + raw.charAt(2);
    }
    let body;
    if (open || placeholder) {
      body =
        "<p>Развёрнутый ответ · проверяет учитель по критериям ОГЭ (изложение / сочинение).</p>";
    } else {
      body = '<p class="oge-teacher-key-ans">' + escapeHtml(ans) + "</p>";
      if (hint && hint !== raw && hint !== ans) {
        body += '<p class="oge-teacher-key-hint">' + escapeHtml(hint) + "</p>";
      }
    }
    return (
      '<div class="oge-teacher-key" data-teacher-key="' +
      escapeHtml(task && task.num != null ? task.num : "") +
      '"><span class="oge-teacher-key-label">Ключ</span>' +
      body +
      "</div>"
    );
  }

  function withTeacherKey(html, task, options) {
    if (options && options.showKey) html += renderTeacherKey(task);
    return html;
  }

  function payloadImagesHtml(task) {
    const p = payloadOf(task) || {};
    const urls = Array.isArray(p.image_urls) ? p.image_urls : [];
    if (!urls.length) return "";
    const num = task && task.num != null ? task.num : "";
    return (
      '<div class="task-media" aria-label="Рисунок к заданию">' +
      urls
        .map(function (u) {
          const src = String(u || "").trim();
          if (!src || /^javascript:/i.test(src)) return "";
          if (typeof global.edusenseTaskImgHtml === "function") {
            return global.edusenseTaskImgHtml(src, num, "Рисунок");
          }
          return (
            '<img class="task-media-img" src="' +
            escapeHtml(src) +
            '" alt="Рисунок" loading="lazy" data-task-num="' +
            escapeHtml(num) +
            '" />'
          );
        })
        .filter(Boolean)
        .join("") +
      "</div>"
    );
  }

  function renderExamTaskBody(task, opts) {
    const options = opts || {};
    const p = payloadOf(task) || {};
    const kim = kimTypeOf(task);
    const saved = options.getAnswerText ? options.getAnswerText(task.num) : "";
    const text = taskText(task);
    const parsed = parseStemAndOptions(text);
    const stem = parsed.stem;
    const optsList = optionsFromPayload(p) || parsed.options;
    let html = payloadImagesHtml(task);

    if (kim === 1 || p.ui === "listening") {
      html += '<span class="oge-exam-num">' + escapeHtml(kim) + ".</span>";
      html +=
        '<span class="oge-exam-instruction">Сжатое изложение. Прослушайте текст и напишите сжатое изложение.</span>';
      html += renderListeningBlock(task, options);
      if (!options.teacher) {
        html += renderOpenAnswerPanel(
          task,
          options.getAnswerState && options.getAnswerState(task.num)
        );
      }
      return withTeacherKey(html, task, options);
    }

    if (kim === 13 || p.ui === "essay_choice" || p.essay_options) {
      html += '<span class="oge-exam-num">' + escapeHtml(kim) + ".</span>";
      html +=
        '<span class="oge-exam-instruction">Сочинение-рассуждение. Выполните только ОДНО из заданий 13.1–13.3.</span>';
      html += renderEssayChoice(task);
      const a = options.getAnswerState && options.getAnswerState(task.num);
      html += renderEssayAnswerPanel(
        task,
        a || { mode: "text", text: "", photoDataUrl: "" },
        options
      );
      return withTeacherKey(html, task, options);
    }

    const isMatching = kim === 4 || p.ui === "matching" || !!p.matching;
    const stemClean = isMatching ? stemWithoutMatchingTables(stem) : stem;
    const splitStem = splitInstructionAndBody(stemClean);
    const instruction =
      splitStem.instruction ||
      firstInstructionLine(stemClean) ||
      (task.topic ? String(task.topic) : "");

    html +=
      '<div class="oge-exam-head"><span class="oge-exam-num">' +
      escapeHtml(kim) +
      '.</span><span class="oge-exam-instruction">' +
      escapeHtml(instruction) +
      "</span></div>";

    if (isMatching) {
      // Не рендерим body stem с А/Б/В — только таблица соответствия
      html += renderMatching(task);
      if (!options.teacher) html += renderAnswerLine(task, saved);
      return withTeacherKey(html, task, options);
    }

    if (kim === 5 || kim === 7) {
      // Всегда от полного текста: парсер 1) 2) не должен резать «(1) (2) (3)»
      const splitFull = splitInstructionAndBody(taskText(task));
      let body = splitFull.body || splitStem.body;
      if (!body) {
        const fromMarks = extractDigitIds(taskText(task));
        if (fromMarks.length) body = taskText(task);
      }
      if (body) html += '<div class="oge-exam-stem">' + markDigitInserts(body) + "</div>";
      const digits = extractDigitIds(body || taskText(task));
      if (digits.length && !options.teacher) html += renderDigitPickers(task, digits, saved);
      if (!options.teacher) html += renderAnswerLine(task, saved);
      return withTeacherKey(html, task, options);
    }

    if (kim === 8 || kim === 9 || kim === 12) {
      const body = splitStem.body;
      if (body) html += '<div class="oge-exam-stem">' + formatText(body) + "</div>";
      if (!options.teacher) {
        const ph =
          kim === 12 ? "слово / словосочетание" : kim === 9 ? "словосочетание" : "слово";
        html += renderAnswerLine(task, saved, { short: true, placeholder: ph });
      }
      return withTeacherKey(html, task, options);
    }

    if (optsList.length) {
      html += renderMultiOptions(task, optsList, saved);
    } else if (splitStem.body) {
      html += '<div class="oge-exam-stem">' + formatText(splitStem.body) + "</div>";
    }
    if (!options.teacher) html += renderAnswerLine(task, saved);
    return withTeacherKey(html, task, options);
  }

  function renderExamTaskArticle(task, opts) {
    const kim = kimTypeOf(task);
    const open = kim === 1 || kim === 13;
    const body = renderExamTaskBody(task, opts);
    const extra = opts && opts.footerHtml ? opts.footerHtml : "";
    return (
      '<article class="oge-exam-task' +
      (open ? " is-open" : "") +
      '" data-num="' +
      escapeHtml(task.num) +
      '" data-kim="' +
      escapeHtml(kim) +
      '">' +
      body +
      extra +
      "</article>"
    );
  }

  function mapTasksWithShared(tasks, renderCard, opts) {
    const options = opts || {};
    const out = [];
    let grammarShown = false;
    let readingShown = false;
    const list = Array.isArray(tasks) ? tasks : [];
    const examMode = options.exam !== false && isOgeRusList(list);
    const grammarFallback = findSharedText(list, "grammar_text");
    const readingFallback = findSharedText(list, "reading_text");

    if (examMode) {
      if (!renderCard) {
        out.push(
          '<div class="oge-rus-exam" data-exam-ui="kim-v2"><div class="oge-rus-exam-sheet">'
        );
      }
      let bankLabel = "";
      let bankCode = "";
      for (let bi = 0; bi < list.length; bi++) {
        const bp = payloadOf(list[bi]) || {};
        if (bp.bank_label || bp.bank_code) {
          bankLabel = String(bp.bank_label || "").trim();
          bankCode = String(bp.bank_code || "").trim();
          break;
        }
      }
      const bannerTitle = bankLabel || "КИМ · задания 1–13";
      const bannerHint = options.print
        ? "Ответы записывайте в бланк. Изложение — после двукратного прослушивания."
        : bankLabel
        ? "Чтобы указать ошибку, напишите: " +
          (bankLabel.split(" · ")[0] || bankCode) +
          ", задание 11"
        : "Тестовая часть (2–12) — как в бланке. Изложение и сочинение — по порядку КИМ.";
      out.push(
        '<header class="oge-exam-banner"><p class="oge-exam-banner-kicker">ОГЭ · Русский язык' +
          (bankCode ? " · " + escapeHtml(bankCode) : "") +
          "</p>" +
          "<h2>" +
          escapeHtml(bannerTitle) +
          "</h2>" +
          "<p>" +
          escapeHtml(bannerHint) +
          "</p></header>"
      );
    }

    for (let ti = 0; ti < list.length; ti++) {
      const task = list[ti];
      const p = payloadOf(task) || {};
      const kim = kimTypeOf(task);
      const grammarText = p.grammar_text || (kim === 2 || kim === 3 ? grammarFallback : "");
      const readingText = p.reading_text || (kim >= 10 && kim <= 12 ? readingFallback : "");

      // Один блок текста перед парой 2–3 (как в КИМ / Решу ОГЭ)
      if (
        !grammarShown &&
        grammarText &&
        (p.show_shared === "grammar" || kim === 2 || kim === 3)
      ) {
        if (examMode && !renderCard && (kim === 2 || kim === 3)) {
          out.push('<p class="oge-section-label">Часть 1 · задания 2–9</p>');
        }
        out.push(
          renderSharedBlock("grammar", grammarText, {
            uid: "g-" + (task.num != null ? task.num : ti),
            collapsed: false,
            print: !!options.print,
          })
        );
        grammarShown = true;
      }
      if (
        !readingShown &&
        readingText &&
        (p.show_shared === "reading" || kim === 10)
      ) {
        if (examMode && !renderCard) {
          out.push('<p class="oge-section-label">Текст и задания 10–12</p>');
        }
        out.push(
          renderSharedBlock("reading", readingText, {
            uid: "r-" + (task.num != null ? task.num : ti),
            collapsed: false,
            print: !!options.print,
          })
        );
        readingShown = true;
      }

      if (examMode && typeof renderCard === "function") {
        let extras = "";
        const taskForBody =
          (kim === 13 || p.essay_options) && readingFallback
            ? Object.assign({}, task, {
                payload: Object.assign({}, p, {
                  reading_text: p.reading_text || readingFallback,
                }),
              })
            : task;
        if (options.examBody) {
          extras = renderExamTaskBody(
            taskForBody,
            Object.assign({}, options, { teacher: true })
          );
        } else {
          if (p.ui === "listening" || kim === 1) extras += renderListeningBlock(task, options);
          if (p.ui === "matching" || p.matching) extras += renderMatching(task);
          if (p.ui === "essay_choice" || p.essay_options) extras += renderEssayChoice(taskForBody);
        }
        out.push(renderCard(task, extras));
      } else if (examMode) {
        if (kim === 1) out.push('<p class="oge-section-label">Задание 1 · изложение</p>');
        if (kim === 13) out.push('<p class="oge-section-label">Задание 13 · сочинение</p>');
        const taskForBody =
          kim === 13 && readingFallback && !p.reading_text
            ? Object.assign({}, task, {
                payload: Object.assign({}, p, { reading_text: readingFallback }),
              })
            : task;
        out.push(renderExamTaskArticle(taskForBody, options));
      } else {
        let extras = "";
        if (p.ui === "listening" || kim === 1) extras += renderListeningBlock(task, options);
        if (p.ui === "matching" || p.matching) extras += renderMatching(task);
        if (p.ui === "essay_choice" || p.essay_options) {
          const essayTask = Object.assign({}, task, {
            payload: Object.assign({}, p, {
              reading_text: p.reading_text || readingFallback,
            }),
          });
          extras += renderEssayChoice(essayTask);
        }
        out.push(renderCard(task, extras));
      }
    }

    if (examMode && !renderCard) out.push("</div></div>");
    return out.join("");
  }

  function renderExamVariant(tasks, opts) {
    return mapTasksWithShared(tasks, null, Object.assign({}, opts || {}, { exam: true }));
  }

  function collectMatchingAnswer(root, num) {
    const box = root.querySelector('[data-oge-matching="' + num + '"]');
    if (!box) return null;
    const inputs = Array.from(box.querySelectorAll("[data-oge-match]"));
    return inputs.map(function (el) { return String(el.value || "").trim(); }).join("");
  }

  function collectMultiAnswer(root, num) {
    const box = root.querySelector('[data-oge-multi-box="' + num + '"]');
    if (!box) return null;
    const checked = Array.from(
      box.querySelectorAll('input[data-oge-multi="' + num + '"]:checked')
    );
    const digits = checked
      .map(function (el) { return String(el.value || "").trim(); })
      .filter(Boolean)
      .sort(function (a, b) { return Number(a) - Number(b); });
    return digits.join("");
  }

  function collectEssayPrefix(root, num) {
    const checked = root.querySelector('input[data-oge-essay-opt="' + num + '"]:checked');
    return checked ? String(checked.value) : "";
  }

  function syncAnswerField(root, num, value) {
    const ta = root.querySelector('[data-answer="' + num + '"]');
    if (ta) ta.value = value;
  }

  function bind(root, hooks) {
    if (!root) return;
    const onAnswer = hooks && typeof hooks.onAnswer === "function" ? hooks.onAnswer : null;
    const readOnly = !!(hooks && hooks.readOnly);

    root.querySelectorAll("[data-oge-collapse]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        const id = btn.getAttribute("data-oge-collapse");
        const body = root.querySelector('[data-oge-collapse-body="' + id + '"]');
        if (!body) return;
        const willHide = !body.hasAttribute("hidden");
        if (willHide) body.setAttribute("hidden", "");
        else body.removeAttribute("hidden");
        btn.setAttribute("aria-expanded", willHide ? "false" : "true");
        btn.textContent = willHide ? "Развернуть" : "Свернуть";
      });
    });

    root.querySelectorAll("[data-oge-play-twice]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        const num = btn.getAttribute("data-oge-play-twice");
        const host = root.querySelector('[data-oge-listen="' + num + '"]');
        const status = root.querySelector('[data-oge-tts-status="' + num + '"]');
        const audio = host && host.querySelector("audio.oge-rus-audio");
        const body = host && host.querySelector(".oge-rus-transcript-body");
        const text = body ? body.innerText || body.textContent || "" : "";
        playAudioTwice(
          audio,
          function (msg) {
            if (status) status.textContent = msg;
          },
          text
        );
      });
    });

    root.querySelectorAll("audio.oge-rus-audio").forEach(function (el) {
      bindAudioSrcFallback(el);
      try {
        el.playbackRate = getTtsRate();
      } catch (_) {}
    });

    root.querySelectorAll("[data-oge-tts-rate]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        setTtsRate(btn.getAttribute("data-oge-tts-rate"));
        applyPlaybackRate(root);
      });
    });

    root.querySelectorAll("[data-oge-tts-voice]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        setVoicePref(btn.getAttribute("data-oge-tts-voice"));
        applyPlaybackRate(root);
      });
    });

    root.querySelectorAll("[data-oge-tts-pause]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        const num = btn.getAttribute("data-oge-tts-pause");
        const status = root.querySelector('[data-oge-tts-status="' + num + '"]');
        toggleTtsPause(function (msg) {
          if (status) status.textContent = msg;
        });
      });
    });

    applyPlaybackRate(root);

    root.querySelectorAll("[data-oge-tts]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        const num = btn.getAttribute("data-oge-tts");
        const host = root.querySelector('[data-oge-listen="' + num + '"]');
        const status = root.querySelector('[data-oge-tts-status="' + num + '"]');
        const body = host && host.querySelector(".oge-rus-transcript-body");
        const fromBody = body ? body.innerText || body.textContent || "" : "";
        const fromAttr = host ? host.getAttribute("data-oge-listen-text") || "" : "";
        const text = String(fromBody || fromAttr || "").trim();
        speakTwice(text, function (msg) {
          if (status) status.textContent = msg;
        });
      });
    });

    root.querySelectorAll("[data-oge-match]").forEach(function (inp) {
      if (inp.dataset.bound) return;
      inp.dataset.bound = "1";
      inp.addEventListener("input", function () {
        const num = Number(inp.getAttribute("data-num"));
        const joined = collectMatchingAnswer(root, num);
        if (joined != null) {
          syncAnswerField(root, num, joined);
          if (onAnswer) onAnswer(num, joined);
        }
      });
    });

    root.querySelectorAll("[data-oge-multi]").forEach(function (inp) {
      if (inp.dataset.bound) return;
      inp.dataset.bound = "1";
      inp.addEventListener("change", function () {
        const num = Number(inp.getAttribute("data-oge-multi"));
        const joined = collectMultiAnswer(root, num);
        if (joined != null) {
          syncAnswerField(root, num, joined);
          if (onAnswer) onAnswer(num, joined);
        }
      });
    });

    root.querySelectorAll("[data-oge-essay-opt]").forEach(function (inp) {
      if (inp.dataset.bound) return;
      inp.dataset.bound = "1";
      inp.addEventListener("change", function () {
        const num = Number(inp.getAttribute("data-oge-essay-opt"));
        const kind = collectEssayPrefix(root, num);
        const ta = root.querySelector('[data-answer="' + num + '"]');
        const prev = ta ? ta.value : "";
        const body = String(prev).replace(/^\s*13\.[123]\s*[\n:—-]?\s*/i, "");
        const next = kind ? kind + "\n" + body : body;
        if (ta) ta.value = next;
        if (onAnswer) onAnswer(num, next);
      });
    });

    root.querySelectorAll("[data-oge-short], .oge-exam-answer-input").forEach(function (inp) {
      if (inp.dataset.boundShort) return;
      inp.dataset.boundShort = "1";
      inp.addEventListener("input", function () {
        if (readOnly) return;
        const num = Number(inp.getAttribute("data-answer") || inp.getAttribute("data-oge-short"));
        if (onAnswer) onAnswer(num, inp.value);
      });
    });

    if (readOnly) {
      root.querySelectorAll(
        "textarea[data-answer], input[data-answer], input[data-oge-match], input[data-oge-multi], input[data-oge-essay-opt], input[data-oge-short], .oge-exam-answer-input"
      ).forEach(function (el) {
        el.setAttribute("readonly", "readonly");
        el.setAttribute("disabled", "disabled");
      });
    }
  }

  global.OgeRusUI = {
    payloadOf: payloadOf,
    isOgeRusTask: isOgeRusTask,
    isOgeRusList: isOgeRusList,
    isOgeRussianExam: isOgeRussianExam,
    examModeBannerHtml: examModeBannerHtml,
    parseStemAndOptions: parseStemAndOptions,
    splitNumberedOptions: splitNumberedOptions,
    formatProseTaskHtml: formatProseTaskHtml,
    formatTaskTextHtml: formatTaskTextHtml,
    kimTypeOf: kimTypeOf,
    renderListeningBlock: renderListeningBlock,
    renderSharedBlock: renderSharedBlock,
    renderMatching: renderMatching,
    renderEssayChoice: renderEssayChoice,
    renderEssayAnswerPanel: renderEssayAnswerPanel,
    renderTeacherKey: renderTeacherKey,
    renderExamTaskArticle: renderExamTaskArticle,
    renderExamVariant: renderExamVariant,
    mapTasksWithShared: mapTasksWithShared,
    collectMatchingAnswer: collectMatchingAnswer,
    collectMultiAnswer: collectMultiAnswer,
    collectEssayPrefix: collectEssayPrefix,
    speakTwice: speakTwice,
    playAudioTwice: playAudioTwice,
    bind: bind,
  };
})(typeof window !== "undefined" ? window : globalThis);
