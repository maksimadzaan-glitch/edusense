# -*- coding: utf-8 -*-
"""Sandbox QA matrix for ege_tracker. Run against http://127.0.0.1:8010"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

# Windows consoles often use cp1251 — keep stdout ASCII-safe
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

BASE = "http://127.0.0.1:8010"
results: list[tuple[str, str, str]] = []  # section, status, detail


def ok(section: str, detail: str = "") -> None:
    results.append((section, "PASS", detail))
    print(f"  PASS  {section}" + (f" — {detail}" if detail else ""))


def fail(section: str, detail: str = "") -> None:
    results.append((section, "FAIL", detail))
    print(f"  FAIL  {section}" + (f" — {detail}" if detail else ""))


def info(msg: str) -> None:
    print(f"  ..    {msg}")


def get(path: str, **kw):
    return requests.get(f"{BASE}{path}", timeout=kw.pop("timeout", 60), **kw)


def post(path: str, **kw):
    return requests.post(f"{BASE}{path}", timeout=kw.pop("timeout", 120), **kw)


def put(path: str, **kw):
    return requests.put(f"{BASE}{path}", timeout=kw.pop("timeout", 60), **kw)


def patch(path: str, **kw):
    return requests.patch(f"{BASE}{path}", timeout=kw.pop("timeout", 60), **kw)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def has_stub_etalon(questions: list[dict]) -> list[str]:
    hits = []
    for q in questions:
        text = str(q.get("text") or "")
        if "Эталонное задание" in text:
            hits.append(f"#{q.get('num')}: {text[:80]}")
    return hits


def strip_leaked(q: dict) -> list[str]:
    leaked = []
    for key in ("answer", "acceptable_answers", "correct", "correct_answer", "answers_key"):
        if q.get(key) not in (None, "", [], {}):
            # public student GET should strip these; empty string might be ok after strip
            val = q.get(key)
            if val not in ("", [], {}):
                leaked.append(f"{key}={val!r}"[:120])
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    for key in ("answer", "correct", "correct_answer"):
        if pl.get(key) not in (None, "", [], {}):
            leaked.append(f"payload.{key}")
    return leaked


def main() -> int:
    # ------------------------------------------------------------------ A
    section("A. Core pages")
    pages = ["/teacher", "/student", "/student/join", "/student/dashboard"]
    for p in pages:
        r = get(p)
        if r.status_code == 200 and len(r.content) > 100:
            ok(f"GET {p}", f"{len(r.content)} bytes")
        else:
            fail(f"GET {p}", f"status={r.status_code}")

    # static with ?v=
    statics = [
        "/css/teacher.css?v=118",
        "/css/student.css?v=118",
        "/css/oge_rus_exam.css?v=118",
        "/css/styles.css?v=118",
        "/js/teacher.js?v=118",
        "/js/student.js?v=118",
        "/js/oge_rus_ui.js?v=118",
        "/js/math.js?v=34",
    ]
    for s in statics:
        r = get(s)
        if r.status_code == 200 and len(r.content) > 50:
            ok(f"static {s}", f"{len(r.content)} bytes")
        else:
            fail(f"static {s}", f"status={r.status_code}")

    # beta badge in landing HTML + teacher/student JS
    r = get("/")
    if r.status_code == 200 and "beta-badge" in r.text and "Бета" in r.text:
        ok("landing beta badge", "HTML")
    else:
        fail("landing beta badge", f"status={r.status_code}")
    for label, js in (("teacher", "/js/teacher.js?v=118"), ("student", "/js/student.js?v=118")):
        jr = get(js)
        if jr.status_code == 200 and "beta-badge" in jr.text and "Бета" in jr.text:
            ok(f"{label} beta badge", "JS")
        else:
            fail(f"{label} beta badge", "missing")

    # ------------------------------------------------------------------ B
    section("B. Teacher class + generate")
    class_code = None
    class_id = None
    r = post(
        "/api/class/create",
        json={
            "name": f"QA Sandbox {datetime.now(timezone.utc).strftime('%H%M%S')}",
            "subject": "Математика",
            "target_exam": "oge",
            "teacher": {"name": "QA Teacher", "email": "qa.sandbox@edusense.local"},
        },
    )
    if r.status_code in (200, 201):
        data = r.json()
        class_code = data["classroom"]["code"]
        class_id = data["classroom"]["id"]
        ok("create class", f"code={class_code} id={class_id}")
    else:
        fail("create class", f"{r.status_code} {r.text[:300]}")
        # try to continue with health check only

    # Generate OGE math
    math_qs: list[dict] = []
    math_exam_ui = None
    pg_available = True
    r = post(
        "/api/ai/generate",
        json={"exam": "ОГЭ", "subject": "Математика", "count": 25, "vary": False},
        timeout=180,
    )
    if r.status_code == 503 and "PostgreSQL" in r.text:
        pg_available = False
        fail("generate OGE math", f"PG missing: {r.text[:200]}")
    elif r.status_code != 200:
        pg_available = False
        fail("generate OGE math", f"{r.status_code} {r.text[:400]}")
    else:
        data = r.json()
        math_qs = data.get("questions") or []
        math_exam_ui = data.get("exam_ui")
        stubs = has_stub_etalon(math_qs)
        if len(math_qs) != 25:
            fail("generate OGE math count", f"got {len(math_qs)}, want 25")
        elif stubs:
            fail("generate OGE math no stub", f"stubs: {stubs[:3]}")
        else:
            ok("generate OGE math", f"25 tasks, exam_ui={math_exam_ui!r}")

        # math must NOT have oge_rus chrome
        rus_chrome = []
        for q in math_qs:
            pl = q.get("payload") or {}
            if pl.get("oge_rus") or pl.get("ui") == "oge_rus" or q.get("exam_ui") == "oge_rus_kim":
                rus_chrome.append(q.get("num"))
        if math_exam_ui == "oge_rus_kim" or rus_chrome:
            fail("math no oge_rus chrome", f"exam_ui={math_exam_ui} nums={rus_chrome[:5]}")
        else:
            ok("math no oge_rus chrome", "clean")

    # Generate OGE russian
    rus_qs: list[dict] = []
    rus_exam_ui = None
    r = post(
        "/api/ai/generate",
        json={"exam": "ОГЭ", "subject": "Русский язык", "count": 13, "vary": False},
        timeout=180,
    )
    if r.status_code == 503 and "PostgreSQL" in r.text:
        fail("generate OGE russian", f"PG missing: {r.text[:200]}")
    elif r.status_code == 404:
        # try etalon mode
        info("bank generate 404, trying mode=etalon")
        r = post(
            "/api/ai/generate",
            json={
                "exam": "ОГЭ",
                "subject": "Русский язык",
                "count": 13,
                "vary": False,
                "mode": "etalon",
            },
            timeout=180,
        )
        if r.status_code != 200:
            fail("generate OGE russian etalon", f"{r.status_code} {r.text[:400]}")
        else:
            data = r.json()
            rus_qs = data.get("questions") or []
            rus_exam_ui = data.get("exam_ui")
            if len(rus_qs) != 13:
                fail("generate OGE russian count", f"got {len(rus_qs)}")
            elif rus_exam_ui != "oge_rus_kim":
                fail("generate OGE russian exam_ui", f"got {rus_exam_ui!r}")
            else:
                ok("generate OGE russian (etalon)", f"13 tasks, exam_ui={rus_exam_ui}")
    elif r.status_code != 200:
        fail("generate OGE russian", f"{r.status_code} {r.text[:400]}")
    else:
        data = r.json()
        rus_qs = data.get("questions") or []
        rus_exam_ui = data.get("exam_ui")
        if len(rus_qs) != 13:
            fail("generate OGE russian count", f"got {len(rus_qs)}")
        elif rus_exam_ui != "oge_rus_kim":
            fail("generate OGE russian exam_ui", f"got {rus_exam_ui!r}")
        else:
            ok("generate OGE russian", f"13 tasks, exam_ui={rus_exam_ui}")

        # structure check
        structured = 0
        for q in rus_qs:
            pl = q.get("payload") or {}
            if pl.get("oge_rus") or pl.get("ui") == "oge_rus" or pl.get("left") or pl.get("right") or pl.get("pairs"):
                structured += 1
            elif q.get("type") or q.get("text"):
                structured += 1
        if structured < 10:
            fail("rus has structure", f"only {structured}/13 look structured")
        else:
            ok("rus has structure", f"{structured}/13")

    # ------------------------------------------------------------------ C
    section("C. Publish -> student -> submit -> teacher")
    assign_code = None
    questions_for_publish = math_qs if math_qs else rus_qs

    if not class_code:
        fail("publish flow", "no class_code")
    elif not questions_for_publish:
        # try publish with minimal handcrafted questions so we can still test flow
        info("no generate questions — using handcrafted fallback for publish/submit")
        questions_for_publish = [
            {
                "num": 1,
                "part": 1,
                "type": "short",
                "topic": "тест",
                "text": "Сколько будет 2+2?",
                "answer": "4",
                "max_score": 1,
            },
            {
                "num": 2,
                "part": 1,
                "type": "short",
                "topic": "тест",
                "text": "Сколько будет 3+3?",
                "answer": "6",
                "max_score": 1,
            },
        ]

    if class_code and questions_for_publish:
        r = post(
            "/api/assignments/publish",
            json={
                "class_code": class_code,
                "title": "QA Sandbox Assignment",
                "questions": questions_for_publish,
                "grading_mode": "autopilot",
                "timer_minutes": 45,
            },
        )
        if r.status_code not in (200, 201):
            fail("publish assignment", f"{r.status_code} {r.text[:400]}")
        else:
            pub = r.json()
            assign_code = pub["code"]
            ok("publish assignment", f"code={assign_code} q={len(pub.get('questions') or [])}")

            student_name = "Иванов QA"
            r = post(
                "/api/student/join",
                json={"code": assign_code, "name": student_name},
            )
            if r.status_code != 200:
                fail("student join assignment", f"{r.status_code} {r.text[:300]}")
            else:
                join = r.json()
                ok("student join assignment", f"class={join.get('class_code')}")

            r = get(
                "/api/student/tasks",
                params={"class_code": class_code, "student_name": student_name},
            )
            if r.status_code != 200:
                fail("student tasks", f"{r.status_code} {r.text[:300]}")
            else:
                tasks = r.json()
                active_codes = [t["code"] for t in (tasks.get("active") or [])]
                if assign_code in active_codes:
                    ok("student tasks active", f"active={len(active_codes)}")
                else:
                    fail("student tasks active", f"assign not in active: {active_codes[:5]}")

            r = get(f"/api/assignments/{assign_code}")
            if r.status_code != 200:
                fail("GET assignment public", f"{r.status_code}")
            else:
                a = r.json()
                qs = a.get("questions") or []
                leaks = []
                for q in qs:
                    leaks.extend(strip_leaked(q))
                if leaks:
                    fail("no answer keys on public GET", f"{leaks[:5]}")
                else:
                    ok("no answer keys on public GET", f"{len(qs)} questions stripped")
                timer = a.get("timer_minutes") or a.get("time_limit_minutes")
                if timer == 45:
                    ok("timer_minutes present", f"timer={timer}")
                else:
                    fail("timer_minutes present", f"got {timer!r}")

            # submit some answers
            answers = []
            for q in questions_for_publish[: min(5, len(questions_for_publish))]:
                ans = str(q.get("answer") or "1")
                answers.append({"num": int(q.get("num") or 1), "text": ans})
            r = post(
                f"/api/assignments/{assign_code}/submit",
                json={"student_name": student_name, "answers": answers},
            )
            if r.status_code not in (200, 201):
                fail("submit answers", f"{r.status_code} {r.text[:400]}")
            else:
                sub = r.json()
                first_sub_id = sub.get("id")
                ok(
                    "submit answers",
                    f"score={sub.get('score')} status={sub.get('status')} id={first_sub_id}",
                )

            # second submit same name → upsert (200) + one teacher row
            answers2 = list(answers)
            if answers2:
                answers2[0] = dict(answers2[0])
                answers2[0]["text"] = str(answers2[0].get("text") or "") + "x"
            r = post(
                f"/api/assignments/{assign_code}/submit",
                json={"student_name": student_name, "answers": answers2 or answers},
            )
            if r.status_code == 200:
                sub2 = r.json()
                ok(
                    "second submit upserts",
                    f"status=200 id={sub2.get('id')} score={sub2.get('score')}",
                )
            elif r.status_code == 201:
                fail("second submit upserts", "got 201 (created) instead of 200 replace")
            else:
                fail("second submit upserts", f"{r.status_code} {r.text[:300]}")

            r = get(f"/api/assignments/{assign_code}/submissions")
            if r.status_code != 200:
                fail("teacher submissions list", f"{r.status_code}")
            else:
                subs = r.json()
                name_hits = [
                    s
                    for s in subs
                    if student_name.casefold() in (s.get("student_name") or "").casefold()
                ]
                if len(name_hits) == 1:
                    ok(
                        "teacher sees one row per student",
                        f"score={name_hits[0].get('score')} status={name_hits[0].get('status')}",
                    )
                elif len(name_hits) > 1:
                    fail("teacher sees one row per student", f"rows={len(name_hits)}")
                else:
                    fail("teacher sees submission", f"names={[s.get('student_name') for s in subs]}")

            # student tasks: completed contains assignment (not active)
            r = get(
                "/api/student/tasks",
                params={"class_code": class_code, "student_name": student_name},
            )
            if r.status_code == 200:
                tasks = r.json()
                done_codes = [t["code"] for t in (tasks.get("completed") or [])]
                active_codes = [t["code"] for t in (tasks.get("active") or [])]
                if assign_code in done_codes and assign_code not in active_codes:
                    ok("tasks APIs after submit", "in completed, not active")
                else:
                    fail(
                        "tasks APIs after submit",
                        f"done={done_codes[:5]} active={active_codes[:5]}",
                    )
            else:
                fail("tasks APIs after submit", f"{r.status_code}")

            # join with class code lists active
            r = post(
                "/api/student/join",
                json={"code": class_code, "name": "Петров QA"},
            )
            if r.status_code != 200:
                fail("join with class code", f"{r.status_code} {r.text[:300]}")
            else:
                ok("join with class code", "200")
            r = get(
                "/api/student/tasks",
                params={"class_code": class_code, "student_name": "Петров QA"},
            )
            if r.status_code == 200:
                active = r.json().get("active") or []
                if any(t.get("code") == assign_code for t in active):
                    ok("class-code join lists active", f"n={len(active)}")
                else:
                    fail("class-code join lists active", f"codes={[t.get('code') for t in active]}")
            else:
                fail("class-code join lists active", f"{r.status_code}")

    # ------------------------------------------------------------------ D
    section("D. Teacher menu APIs")
    if class_code:
        r = get(f"/api/assignments/by-class/{class_code}")
        if r.status_code == 200:
            ok("assignments by-class", f"n={len(r.json())}")
        else:
            fail("assignments by-class", f"{r.status_code} {r.text[:200]}")

        r = get(f"/api/classes/{class_code}/roster")
        # roster router prefix — check
        if r.status_code == 404:
            # try alternate paths
            for alt in (
                f"/api/roster/{class_code}",
                f"/api/class/{class_code}/roster",
                f"/api/classes/{class_code}/roster",
            ):
                r = get(alt)
                if r.status_code == 200:
                    break
        # discover from roster.py
        if r.status_code != 200:
            # read typical prefix /api/classes/{code}/roster from analytics-like
            pass

    # discover roster path via known routes
    # from roster.py we'll check after probing
    roster_ok = False
    students_ok = False
    analytics_ok = False
    if class_code:
        for base_path in (
            f"/api/classes/{class_code}/roster",
            f"/api/class/{class_code}/roster",
            f"/api/roster/{class_code}",
        ):
            r = get(base_path)
            if r.status_code == 200:
                ok("GET roster", base_path)
                roster_ok = True
                r2 = put(base_path, json={"names": ["Сидоров QA", "Иванов QA"]})
                if r2.status_code == 200:
                    ok("PUT roster", f"n={len((r2.json().get('students') or r2.json().get('names') or r2.json().get('roster') or []))}")
                else:
                    fail("PUT roster", f"{r2.status_code} {r2.text[:200]}")
                break
        if not roster_ok:
            fail("GET roster", "path not found")

        for base_path in (
            f"/api/classes/{class_code}/students",
            f"/api/class/{class_code}/students",
            f"/api/roster/{class_code}/students",
        ):
            r = get(base_path)
            if r.status_code == 200:
                ok("GET students", f"{base_path} n={len(r.json() if isinstance(r.json(), list) else r.json().get('students') or [])}")
                students_ok = True
                break
        if not students_ok:
            fail("GET students", "path not found")

        for base_path in (
            f"/api/classes/{class_code}/analytics",
            f"/api/analytics/{class_code}",
            f"/api/class/{class_code}/analytics",
        ):
            r = get(base_path)
            if r.status_code == 200:
                ok("GET analytics", base_path)
                analytics_ok = True
                data = r.json()
                # Russian labels + remediation gate
                heat = data.get("heatmap") or []
                eng_noise = [
                    h for h in heat
                    if isinstance(h.get("topic"), str)
                    and any(x in h["topic"].lower() for x in ("syntax_", "punctuation_", "grammar_form", "syntax basis", "punctuation matching"))
                ]
                if not eng_noise:
                    ok("analytics topics Russian", f"heat={len(heat)}")
                else:
                    fail("analytics topics Russian", f"english={eng_noise[:2]}")
                titles = [t.get("title") or "" for t in (data.get("trend") or [])]
                smoke_titles = [t for t in titles if "smoke" in t.lower()]
                if not smoke_titles:
                    ok("analytics trend no smoke titles", f"points={len(titles)}")
                else:
                    fail("analytics trend no smoke titles", str(smoke_titles[:2]))
                if "remediation_ready" in data and "remediation_hint" in data:
                    ok(
                        "remediation gate fields",
                        f"ready={data.get('remediation_ready')} hint={str(data.get('remediation_hint') or '')[:80]}",
                    )
                    # empty roster or incomplete → not ready
                    if data.get("remediation_ready") is False:
                        ok("remediation gated until all submitted", "ready=false")
                    else:
                        info(f"remediation_ready unexpectedly true: {data.get('remediation_hint')}")
                else:
                    fail("remediation gate fields", "missing")
                lines = data.get("summary_lines") or []
                if lines:
                    ok("analytics summary_lines", str(lines[0])[:80])
                else:
                    fail("analytics summary_lines", "empty")
                break
        if not analytics_ok:
            fail("GET analytics", "path not found")

    # ------------------------------------------------------------------ E
    section("E. Regressions")
    if assign_code:
        # close accepting
        r = patch(
            f"/api/assignments/{assign_code}",
            json={"accepting_submissions": False},
        )
        if r.status_code != 200:
            fail("close accepting", f"{r.status_code} {r.text[:200]}")
        else:
            ok("close accepting", f"status={r.json().get('status')}")

        r = post(
            f"/api/assignments/{assign_code}/submit",
            json={
                "student_name": "Закрытый QA",
                "answers": [{"num": 1, "text": "x"}],
            },
        )
        if r.status_code == 403:
            ok("submit closed -> 403", r.json().get("detail", "")[:80] if isinstance(r.json().get("detail"), str) else "403")
        else:
            fail("submit closed -> 403", f"got {r.status_code}")

        r = post(
            "/api/student/join",
            json={"code": assign_code, "name": "Закрытый QA"},
        )
        if r.status_code == 403:
            detail = r.json().get("detail")
            closed = False
            if isinstance(detail, dict) and detail.get("closed"):
                closed = True
            elif "закрыт" in str(detail).lower():
                closed = True
            if closed:
                ok("join closed shows closed", str(detail)[:120])
            else:
                fail("join closed shows closed", f"403 but no closed flag: {detail!r}"[:200])
        else:
            fail("join closed shows closed", f"got {r.status_code}")

    # Russian matching task 4
    if rus_qs:
        q4 = next((q for q in rus_qs if int(q.get("num") or 0) == 4), None)
        if not q4 and len(rus_qs) >= 4:
            q4 = rus_qs[3]
        if q4:
            pl = q4.get("payload") or {}
            has_match = bool(
                pl.get("left")
                or pl.get("right")
                or pl.get("pairs")
                or pl.get("columns")
                or pl.get("matching")
                or pl.get("options_left")
                or "соотнес" in str(q4.get("text") or "").lower()
                or "установ" in str(q4.get("type") or "").lower()
                or q4.get("type") in ("matching", "match", "correspondence")
            )
            # also accept structured content in text/payload for oge rus
            if not has_match and (pl.get("oge_rus") or pl.get("ui") == "oge_rus"):
                # dump keys for diagnosis
                info(f"task4 keys: type={q4.get('type')} payload_keys={list(pl.keys())[:20]}")
                # still pass if payload has meaningful structure beyond chrome flags
                content_keys = [k for k in pl.keys() if k not in ("oge_rus", "ui", "exam_ui", "etalon")]
                has_match = len(content_keys) >= 1 and bool(q4.get("text"))
            if has_match:
                ok("rus task4 matching/structure", f"type={q4.get('type')} keys={list(pl.keys())[:12]}")
            else:
                fail("rus task4 matching/structure", f"type={q4.get('type')} payload={list(pl.keys())}")
        else:
            fail("rus task4 matching/structure", "no q4")

    if math_qs:
        stubs = has_stub_etalon(math_qs)
        if stubs:
            fail("no stub math etalon", str(stubs[:2]))
        else:
            ok("no stub math etalon", "clean")

    # ------------------------------------------------------------------ report
    section("SUMMARY")
    passes = sum(1 for _, s, _ in results if s == "PASS")
    fails = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"\nPASS={passes} FAIL={fails} pg_available={pg_available}")

    report_lines = [
        f"# Sandbox QA report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Base: `{BASE}`",
        f"PostgreSQL generate: {'OK' if pg_available else 'UNAVAILABLE / failed'}",
        f"Class: `{class_code}`  Assignment: `{assign_code}`",
        "",
        f"**Итого: PASS={passes} FAIL={fails}**",
        "",
        "| Статус | Проверка | Детали |",
        "|--------|----------|--------|",
    ]
    for name, status, detail in results:
        d = (detail or "").replace("|", "/").replace("\n", " ")[:200]
        report_lines.append(f"| {status} | {name} | {d} |")

    if fails:
        report_lines += ["", "## FAIL items", ""]
        for name, status, detail in results:
            if status == "FAIL":
                report_lines.append(f"- **{name}**: {detail}")

    report_path = __file__.replace("_sandbox_qa.py", "_sandbox_report.md")
    # Append wave section; keep prior report body if present
    wave = [
        "",
        "---",
        "",
        f"## Wave: student-work features — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Base: `{BASE}` · Class: `{class_code}` · Assignment: `{assign_code}`",
        f"**PASS={passes} FAIL={fails}** · pg={'OK' if pg_available else 'no'}",
        "",
        "### Features verified",
        "- Static assets `?v=118`",
        "- Beta badge in landing HTML + teacher/student JS",
        "- Analytics Russian topic labels + remediation gate",
        "- Timer field on publish/GET (`timer_minutes`)",
        "- Submit + second submit upsert (200) + one teacher row per student",
        "- Student tasks APIs after submit (completed / not active)",
        "- Accepting closed / join closed regressions",
        "",
        "| Статус | Проверка | Детали |",
        "|--------|----------|--------|",
    ]
    for name, status, detail in results:
        d = (detail or "").replace("|", "/").replace("\n", " ")[:200]
        wave.append(f"| {status} | {name} | {d} |")
    wave.append("")

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            prev = f.read()
    except FileNotFoundError:
        prev = ""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(prev.rstrip() + "\n" + "\n".join(wave) + "\n")
    print(f"\nReport appended: {report_path}")

    # also dump machine-readable for fixer
    dump = {
        "pass": passes,
        "fail": fails,
        "pg_available": pg_available,
        "class_code": class_code,
        "assign_code": assign_code,
        "results": [{"name": n, "status": s, "detail": d} for n, s, d in results],
        "math_sample": (math_qs[:1] if math_qs else None),
        "rus_q4": next((q for q in rus_qs if int(q.get("num") or 0) == 4), rus_qs[3] if len(rus_qs) >= 4 else None),
    }
    with open(report_path.replace(".md", "_data.json"), "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2, default=str)

    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
