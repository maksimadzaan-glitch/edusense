/**
 * Пересчёт первичных баллов ОГЭ → оценка 2–5 (математика / русский).
 * Зеркало backend/services/grade_calculator.py
 */
(function (global) {
  "use strict";

  const MATH_MAX = 31;
  const RUS_MAX = 33;
  const LIT_MAX = 8;
  const GEO_NUMS = [15, 16, 17, 18, 19, 23, 24, 25];
  const GEO_DEFAULT_MAX = { 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 23: 2, 24: 2, 25: 2 };
  const MATH_MODULES = [
    { id: "practice", label: "Практика 1–5", nums: [1, 2, 3, 4, 5] },
    { id: "algebra", label: "Алгебра", nums: [6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 21, 22] },
    { id: "geometry", label: "Геометрия", nums: GEO_NUMS },
  ];
  const RUS_MODULES = [
    { id: "izlozhenie", label: "Изложение", nums: [1] },
    { id: "test", label: "Тест", nums: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] },
    { id: "sochinenie", label: "Сочинение", nums: [13] },
  ];
  const LIT_KEYS = { gk1: 1, gk2: 1, gk3: 1, gk4: 1, fk1: 1, literacy: 1 };

  function normalizeSubject(raw) {
    const s = String(raw || "")
      .toLowerCase()
      .replace(/ё/g, "е")
      .trim();
    if (!s) return "math";
    if (s === "math" || s === "mathematics" || s === "math_base" || s.indexOf("матем") >= 0) {
      return "math";
    }
    if (s === "russian" || s === "rus" || s === "ru" || s.indexOf("русск") >= 0 || s.indexOf("russian") >= 0) {
      return "russian";
    }
    return s;
  }

  function maxPrimary(subject) {
    return normalizeSubject(subject) === "russian" ? RUS_MAX : MATH_MAX;
  }

  function markFromScale(score, subject) {
    const p = Math.round(Number(score) || 0);
    if (normalizeSubject(subject) === "russian") {
      if (p <= 14) return "2";
      if (p <= 22) return "3";
      if (p <= 28) return "4";
      return "5";
    }
    if (p <= 7) return "2";
    if (p <= 14) return "3";
    if (p <= 21) return "4";
    return "5";
  }

  function asNum(value, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function isPending(item) {
    const status = String((item && item.status) || "").toLowerCase();
    return status.indexOf("pending") >= 0 || status === "ai_pending" || status === "manual_pending";
  }

  function itemMax(item, fallback) {
    if (!item) return fallback;
    if (item.max_score != null) return Math.max(0, asNum(item.max_score, fallback));
    if (item.maxScore != null) return Math.max(0, asNum(item.maxScore, fallback));
    return fallback;
  }

  function itemEarned(item) {
    if (!item || isPending(item)) return 0;
    if (item.earned != null) return Math.max(0, asNum(item.earned, 0));
    if (String(item.status || "").toLowerCase() === "correct") return itemMax(item, 1);
    return 0;
  }

  function sumLiteracy(blob) {
    if (blob == null) return null;
    if (typeof blob === "number") return blob;
    if (typeof blob !== "object") return null;
    let total = 0;
    let found = false;
    Object.keys(blob).forEach((key) => {
      const lk = String(key).toLowerCase();
      if (LIT_KEYS[lk] || lk.indexOf("gk") === 0 || lk.indexOf("fk") === 0) {
        const val = blob[key];
        total += asNum(val && typeof val === "object" ? val.earned ?? val.score : val, 0);
        found = true;
      }
    });
    return found ? total : null;
  }

  function extractLiteracy(review, items) {
    if (review && review.literacy_score != null) return asNum(review.literacy_score, 0);
    const fromReview =
      sumLiteracy(review && review.literacy) ??
      sumLiteracy(review && (review.criteria || review.rubric_scores));
    if (fromReview != null) return fromReview;
    let total = 0;
    let found = false;
    (items || []).forEach((item) => {
      if (!item) return;
      if (item.literacy_earned != null) {
        total += asNum(item.literacy_earned, 0);
        found = true;
        return;
      }
      const got = sumLiteracy(item.literacy || item.criteria || item.rubric_scores);
      if (got != null) {
        total += got;
        found = true;
      }
    });
    return found ? total : null;
  }

  function moduleBlock(byNum, spec, defaultMax) {
    let earned = 0;
    let max = 0;
    let pending = false;
    let present = false;
    spec.nums.forEach((n) => {
      const item = byNum.get(n);
      const fallback = defaultMax && defaultMax[n] != null ? defaultMax[n] : 1;
      if (item) {
        present = true;
        earned += itemEarned(item);
        max += itemMax(item, fallback);
        if (isPending(item)) pending = true;
      } else if (defaultMax && defaultMax[n] != null) {
        max += fallback;
      }
    });
    if (!present && !max) {
      max = spec.nums.reduce((s, n) => s + ((defaultMax && defaultMax[n]) || 1), 0);
    }
    return {
      id: spec.id,
      label: spec.label,
      earned: Math.round(earned),
      max: Math.round(max),
      pending,
      present,
    };
  }

  function calculate(opts) {
    const o = opts || {};
    const kind = normalizeSubject(o.subject);
    const cap = maxPrimary(kind);
    const rawItems = Array.isArray(o.items) ? o.items.filter((it) => it && typeof it === "object") : [];
    const byNum = new Map();
    rawItems.forEach((it) => {
      const n = Number(it.num);
      if (n) byNum.set(n, it);
    });

    let primary;
    if (o.teacherScore != null && o.teacherScore !== "") primary = Math.round(asNum(o.teacherScore, 0));
    else if (o.score != null && o.score !== "") primary = Math.round(asNum(o.score, 0));
    else primary = Math.round(rawItems.reduce((s, it) => s + itemEarned(it), 0));
    primary = Math.max(0, Math.min(primary, cap));

    let lit = o.literacyScore != null && o.literacyScore !== "" ? asNum(o.literacyScore, 0) : extractLiteracy(o.review, rawItems);
    const litUnknown = lit == null;
    const litI = lit == null ? null : Math.round(lit);

    let scale = markFromScale(primary, kind);
    let grade = scale;
    let failedGeometry = false;
    let failedLiteracy = false;
    let geoPending = false;
    let geoScore = null;
    let geoMax = 11;
    const modules = [];
    let geometryTag = null;
    let literacyTag = null;

    if (kind === "math") {
      MATH_MODULES.forEach((spec) => {
        modules.push(moduleBlock(byNum, spec, spec.id === "geometry" ? GEO_DEFAULT_MAX : null));
      });
      const geo = modules.find((m) => m.id === "geometry");
      if (geo) {
        geoScore = geo.earned;
        geoMax = geo.max || geoMax;
        geoPending = !!geo.pending;
      }
      if (primary >= 8 && geo && geo.present && geoScore != null && geoScore < 2 && !geoPending) {
        failedGeometry = true;
        grade = "2";
      }
      if (geo && geo.present) {
        if (geoPending) geometryTag = `⏳ Геометрия на проверке (${geoScore}/${geoMax})`;
        else if (geoScore != null && geoScore >= 2) geometryTag = `✓ Геометрия сдана (${geoScore}/${geoMax})`;
        else if (geoScore != null) geometryTag = `⚠️ Завал Геометрии (${geoScore}/${geoMax})`;
      }
    } else {
      RUS_MODULES.forEach((spec) => modules.push(moduleBlock(byNum, spec)));
      modules.push({
        id: "literacy",
        label: "Грамотность",
        earned: litI != null ? litI : 0,
        max: LIT_MAX,
        pending: litUnknown,
      });
      if (!litUnknown && (scale === "4" || scale === "5")) {
        const need = scale === "5" ? 6 : 4;
        if ((litI || 0) < need) {
          failedLiteracy = true;
          grade = scale === "5" ? "4" : "3";
        }
      }
      if (litUnknown) literacyTag = "Грамотность не выставлена";
      else if (failedLiteracy) literacyTag = `⚠️ Не хватило грамотности (${litI}/${LIT_MAX})`;
      else literacyTag = `✓ Грамотность (${litI}/${LIT_MAX})`;
    }

    return {
      subject: kind,
      score: primary,
      max_score: cap,
      grade: String(grade),
      scale_grade: String(scale),
      failed_geometry: failedGeometry,
      failed_literacy: failedLiteracy,
      geometry_score: geoScore,
      geometry_max: kind === "math" ? geoMax : null,
      geometry_pending: geoPending,
      literacy_score: litI,
      literacy_max: kind === "russian" ? LIT_MAX : null,
      literacy_unknown: kind === "russian" ? litUnknown : false,
      modules,
      geometry_tag: geometryTag,
      literacy_tag: literacyTag,
    };
  }

  function fromReview(subject, review, extra) {
    const r = review || {};
    const x = extra || {};
    return calculate({
      subject,
      items: Array.isArray(r.items) ? r.items : [],
      score: x.score,
      teacherScore: x.teacherScore,
      literacyScore: x.literacyScore,
      review: r,
    });
  }

  global.OgeGrade = {
    calculate,
    fromReview,
    normalizeSubject,
    maxPrimary,
    markFromScale,
    MATH_MAX,
    RUS_MAX,
    LIT_MAX,
  };
})(typeof window !== "undefined" ? window : globalThis);
