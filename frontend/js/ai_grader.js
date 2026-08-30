/**
 * API-клиент ИИ-проверки Части 2 (спека: lib/aiGrader.ts).
 * Vanilla JS — gradePart2Task POST /api/v1/grade-part2.
 */
(function (global) {
  "use strict";

  var FIPI_PART2 = {
    20: {
      title: "№20 · уравнение / выражение",
      criteria: [
        "2 балла: верное решение с обоснованием; ОДЗ указана и учтена, если есть дробь, корень, логарифм; получен верный ответ.",
        "1 балл: верный метод, но вычислительная ошибка ИЛИ потерян посторонний корень / не указаны ограничения (например x ≠ 3), при этом идея верна.",
        "0 баллов: решение не по задаче, только ответ без шагов, или грубая ошибка в методе.",
      ],
    },
    21: {
      title: "№21 · текстовая задача",
      criteria: [
        "2 балла: верная математическая модель и верный ответ с пояснением.",
        "1 балл: верная модель (уравнение/система), ошибка в вычислениях или не доведён ответ.",
        "0 баллов: неверная модель или решение отсутствует.",
      ],
    },
    22: {
      title: "№22 · функция / график / исследование",
      criteria: [
        "2 балла: верные шаги и ответ, область определения учтена.",
        "1 балл: верный ход с вычислительной ошибкой или неполнотой ОДЗ.",
        "0 баллов: ход не соответствует условию.",
      ],
    },
    23: {
      title: "№23 · геометрия (вычисление)",
      criteria: [
        "2 балла: верное решение с опорой на свойства фигур, верный ответ.",
        "1 балл: верный геометрический ход, ошибка в вычислении или неполное обоснование.",
        "0 баллов: неверная конфигурация или нет решения.",
      ],
    },
    24: {
      title: "№24 · геометрия (доказательство / вычисление)",
      criteria: [
        "2 балла: доказательство или вычисление с полным обоснованием.",
        "1 балл: идея верна, пропущено обоснование ключевого шага или арифметическая ошибка.",
        "0 баллов: доказательство не проведено / ход неверен.",
      ],
    },
    25: {
      title: "№25 · геометрия повышенной сложности",
      criteria: [
        "2 балла: полное обоснованное решение и верный ответ.",
        "1 балл: существенное продвижение (верная идея), решение не доведено или с ошибкой в конце.",
        "0 баллов: нет продвижения по задаче.",
      ],
    },
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fipiRubricFor(taskNum, extra) {
    var spec = FIPI_PART2[Number(taskNum)] || {
      title: "Часть 2 · развёрнутый ответ",
      criteria: [
        "2 балла: верное обоснованное решение и ответ.",
        "1 балл: верный ход с недочётом (ОДЗ, вычисление, обоснование).",
        "0 баллов: решение неверно или отсутствует.",
      ],
    };
    var lines = [spec.title, "Максимум: 2 балла."].concat(spec.criteria);
    var extraS = String(extra || "").trim();
    if (extraS) {
      lines.push("Дополнительно от учителя / варианта:");
      lines.push(extraS);
    }
    return lines.join("\n");
  }

  function highlightFipiReason(text) {
    var escaped = escapeHtml(text || "");
    return escaped.replace(
      /(ОДЗ|знаменател\w*|ограничен\w*|посторонн\w*\s+корн\w*|не указан\w*|x\s*(?:!=|≠|<>)\s*[\d.\-]+)/gi,
      '<mark class="p2-mark">$1</mark>'
    );
  }

    function clampInt(raw, lo, hi) {
      var n = Number(raw);
      if (!Number.isFinite(n)) return lo;
      return Math.max(lo, Math.min(hi, Math.round(n)));
    }

    function clampScore(raw) {
      return clampInt(raw, 0, 2);
    }

    function authJsonHeaders(extra) {
      var base = { "Content-Type": "application/json" };
      if (global.EduSenseAuth && global.EduSenseAuth.authHeaders) {
        return global.EduSenseAuth.authHeaders(Object.assign(base, extra || {}));
      }
      return Object.assign(base, extra || {});
    }

    async function gradePart2Task(taskData) {
      var data = taskData || {};
      var body = {
        taskText: data.taskText || data.task_text || "",
        studentAnswer: data.studentAnswer || data.student_answer || "",
        correctSolution: data.correctSolution || data.correct_solution || "",
        fipiRubric: data.fipiRubric || data.fipi_rubric || "",
      };
      var num = data.taskNum != null ? data.taskNum : data.task_num;
      if (num != null && num !== "") body.taskNum = Number(num);
      var photo = data.photoDataUrl || data.photo_data_url || "";
      if (photo) body.photoDataUrl = String(photo);
      var response;
      try {
        response = await fetch("/api/v1/grade-part2", {
          method: "POST",
          headers: authJsonHeaders(),
          body: JSON.stringify(body),
        });
      } catch (_) {
        throw new Error("Не удалось подключиться к серверу.");
      }
      var payload = null;
      try {
        payload = await response.json();
      } catch (_) {}
      if (!response.ok) {
        var detail = (payload && payload.detail) || "Ошибка " + response.status;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return {
        score: clampScore(payload && payload.score),
        fipi_reason: String((payload && payload.fipi_reason) || ""),
        student_feedback: String((payload && payload.student_feedback) || ""),
        source: String((payload && payload.source) || "llm"),
        model_solution: String((payload && payload.model_solution) || ""),
      };
    }

    async function gradeRusTask(taskData) {
      var data = taskData || {};
      var kind = String(data.kind || "").toLowerCase() === "sochinenie" ? "sochinenie" : "izlozhenie";
      var body = {
        kind: kind,
        taskText: data.taskText || data.task_text || "",
        studentAnswer: data.studentAnswer || data.student_answer || "",
        sourceText: data.sourceText || data.source_text || "",
      };
      var photo = data.photoDataUrl || data.photo_data_url || "";
      if (photo) body.photoDataUrl = String(photo);
      var response;
      try {
        response = await fetch("/api/v1/grade-rus", {
          method: "POST",
          headers: authJsonHeaders(),
          body: JSON.stringify(body),
        });
      } catch (_) {
        throw new Error("Не удалось подключиться к серверу.");
      }
      var payload = null;
      try {
        payload = await response.json();
      } catch (_) {}
      if (!response.ok) {
        var detail = (payload && payload.detail) || "Ошибка " + response.status;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      var maxScore = clampInt(payload && payload.max_score, 1, 7);
      var criteria = payload && payload.criteria && typeof payload.criteria === "object" ? payload.criteria : {};
      return {
        score: clampInt(payload && payload.score, 0, maxScore),
        max_score: maxScore,
        fipi_reason: String((payload && payload.fipi_reason) || ""),
        student_feedback: String((payload && payload.student_feedback) || ""),
        source: String((payload && payload.source) || "llm"),
        criteria: criteria,
      };
    }

  async function writeMathSolution(taskData) {
    var data = taskData || {};
    var body = {
      taskText: data.taskText || data.task_text || "",
      correctSolution: data.correctSolution || data.correct_solution || "",
    };
    var num = data.taskNum != null ? data.taskNum : data.task_num;
    if (num != null && num !== "") body.taskNum = Number(num);
    var photo = data.photoDataUrl || data.photo_data_url || "";
    if (photo) body.photoDataUrl = String(photo);
    var response;
    try {
      response = await fetch("/api/v1/math-solution", {
        method: "POST",
        headers: authJsonHeaders(),
        body: JSON.stringify(body),
      });
    } catch (_) {
      throw new Error("Не удалось подключиться к серверу.");
    }
    var payload = null;
    try {
      payload = await response.json();
    } catch (_) {}
    if (!response.ok) {
      var detail = (payload && payload.detail) || "Ошибка " + response.status;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return {
      solution: String((payload && payload.solution) || ""),
      answer: String((payload && payload.answer) || ""),
      source: String((payload && payload.source) || "llm"),
    };
  }

    var api = {
      gradePart2Task: gradePart2Task,
      gradeRusTask: gradeRusTask,
      writeMathSolution: writeMathSolution,
      fipiRubricFor: fipiRubricFor,
      highlightFipiReason: highlightFipiReason,
    };

    global.AiGrader = api;
    global.gradePart2Task = gradePart2Task;
    global.gradeRusTask = gradeRusTask;
    global.writeMathSolution = writeMathSolution;
})(typeof window !== "undefined" ? window : this);
