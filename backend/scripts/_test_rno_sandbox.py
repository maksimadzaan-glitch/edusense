"""Песочница: мутатор ОГЭ + генератор РНО (без записи в боевую БД).

  py -3 -m backend.scripts._test_rno_sandbox
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from backend.services.grade_calculator import item_failed, part_scores_from_items
from backend.services.math_mutator import (
    apply_mutator_logic_to_question,
    fill_math_templates,
    generate_math_task,
)
from backend.services.rno_generator import (
    collect_failed_task_ids,
    generate_rno,
    mutate_question_unique,
    rno_title,
)

SPEC = (
    Path(__file__).resolve().parents[1]
    / "universal"
    / "specs"
    / "math_oge_mutator.json"
)


def _load_protos() -> list[dict]:
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    return [p for p in (data.get("prototypes") or []) if isinstance(p, dict)]


def _proto_to_question(proto: dict) -> dict:
    num = int(proto.get("task_number") or 0)
    fp = proto.get("figure_params") if isinstance(proto.get("figure_params"), dict) else {}
    text = str(proto.get("template_text") or "")
    return {
        "num": num,
        "part": int(proto.get("part") or (2 if num >= 20 else 1)),
        "type": "Развёрнутый ответ" if num >= 20 else "Краткий ответ",
        "topic": str(proto.get("prototype_title") or f"№{num}"),
        "text": text,
        "answer": str(proto.get("template_answer") or ""),
        "max_score": 2 if num >= 20 else 1,
        "figure_kind": proto.get("figure_kind"),
        "figure_params": copy.deepcopy(fp),
        "payload": {
            "subtype_code": fp.get("subtype_code"),
            "mutator_logic": fp.get("mutator_logic"),
            "mutator_template": text,
            "explanation_template": fp.get("explanation_template")
            or proto.get("template_solution"),
        },
    }


def _one_proto_per_slot(protos: list[dict]) -> list[dict]:
    by_slot: dict[int, dict] = {}
    for p in protos:
        num = int(p.get("task_number") or 0)
        fp = p.get("figure_params") if isinstance(p.get("figure_params"), dict) else {}
        if not num or not isinstance(fp.get("mutator_logic"), dict):
            continue
        by_slot.setdefault(num, p)
    return [by_slot[n] for n in sorted(by_slot)]


def _check(errors: list[str], cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def test_collect_failed() -> list[str]:
    errors: list[str] = []
    items = [
        {"num": 3, "earned": 0, "max_score": 1, "status": "wrong"},
        {"num": 4, "earned": 1, "max_score": 1, "status": "correct"},
        {"num": 5, "earned": 0, "max_score": 2, "status": "pending"},
        {"num": 8, "earned": 0, "max_score": 1, "status": "empty"},
        {"num": 20, "earned": 1, "max_score": 2, "status": "wrong"},
    ]
    got = collect_failed_task_ids(items=items)
    _check(errors, got == [3, 8, 20], f"failed ids {got}, expected [3, 8, 20]")
    _check(errors, not item_failed(items[1]), "correct full score must not fail")
    _check(errors, not item_failed(items[2]), "pending must not fail")
    heatmap = [
        {"num": 6, "wrong_count": 4, "empty_count": 1, "success_pct": 20},
        {"num": 7, "wrong_count": 0, "empty_count": 0, "success_pct": 100},
        {"num": 9, "wrong_count": 2, "empty_count": 0, "success_pct": 40},
        {"num": 1, "wrong_count": 0, "empty_count": 0, "correct_count": 0, "pending_count": 0},
        {"num": 20, "wrong_count": 0, "empty_count": 0, "pending_count": 5, "success_pct": None},
    ]
    heat_failed = collect_failed_task_ids(heatmap=heatmap)
    _check(errors, 6 in heat_failed and 9 in heat_failed, f"heatmap misses {heat_failed}")
    _check(errors, 7 not in heat_failed, f"100% slot leaked: {heat_failed}")
    _check(errors, 1 not in heat_failed, f"empty heatmap row leaked: {heat_failed}")
    _check(errors, 20 not in heat_failed, f"pending-only heatmap leaked: {heat_failed}")
    p1, p2 = part_scores_from_items(
        "math",
        [
            {"num": 1, "part": 1, "earned": 1, "max_score": 1, "status": "correct"},
            {"num": 20, "part": 2, "earned": 2, "max_score": 2, "status": "correct"},
        ],
    )
    _check(errors, (p1, p2) == (1, 2), f"part scores {(p1, p2)}")
    _check(
        errors,
        rno_title("КИМ 12 апреля").startswith("Работа над ошибками:"),
        "title prefix",
    )
    return errors


def test_mutator_core(protos: list[dict]) -> list[str]:
    errors: list[str] = []
    tz = {
        "template": "Найдите больший корень уравнения: x² + {b}x + {c} = 0",
        "mutator_logic": {
            "variables": {
                "x1": "random_int(-10, 10)",
                "x2": "random_int(-10, 10, exclude=[x1])",
            },
            "computed": {
                "b": "-(x1 + x2)",
                "c": "x1 * x2",
                "answer": "max(x1, x2)",
            },
        },
    }
    one = generate_math_task(tz, random.Random(20260818))
    vals = one["values"]
    _check(
        errors,
        int(vals["b"]) == -(int(vals["x1"]) + int(vals["x2"])),
        f"quadratic b {vals}",
    )
    _check(
        errors,
        str(one["answer"]) == str(max(int(vals["x1"]), int(vals["x2"]))),
        f"quadratic answer {one['answer']} {vals}",
    )

    filled = 0
    unique_pairs = 0
    for proto in _one_proto_per_slot(protos):
        q = _proto_to_question(proto)
        a = copy.deepcopy(q)
        b = copy.deepcopy(q)
        ok_a = apply_mutator_logic_to_question(a, random.Random(11))
        ok_b = apply_mutator_logic_to_question(b, random.Random(99))
        if not ok_a:
            errors.append(f"mutator failed slot #{q['num']}")
            continue
        filled += 1
        if "{" in str(a.get("text") or ""):
            errors.append(f"#{q['num']} leftover placeholder: {a['text']}")
        if not str(a.get("answer") or "").strip():
            errors.append(f"#{q['num']} empty answer after mutator")
        if ok_b and (a["text"] != b["text"] or a["answer"] != b["answer"]):
            unique_pairs += 1
    _check(errors, filled >= 10, f"filled only {filled} mutator slots")
    _check(errors, unique_pairs >= 6, f"too few unique pairs ({unique_pairs})")
    print(f"  mutator slots filled={filled} unique_pairs={unique_pairs}")
    return errors


def test_generate_rno(protos: list[dict]) -> list[str]:
    errors: list[str] = []
    questions = [_proto_to_question(p) for p in _one_proto_per_slot(protos) if int(p.get("task_number") or 0) <= 19]
    questions.append(
        {
            "num": 23,
            "part": 2,
            "type": "Развёрнутый ответ",
            "topic": "Геометрия",
            "text": "В треугольнике ABC угол C = 90°, AC = 6, BC = 8. Найдите AB.",
            "answer": "10",
            "max_score": 2,
            "payload": {},
        }
    )
    fill_math_templates(questions, random.Random(7), enabled=True)
    snapshot = {int(q["num"]): (str(q.get("text") or ""), str(q.get("answer") or "")) for q in questions}

    failed = [6, 8, 9, 10, 14, 23]
    result = generate_rno(
        questions,
        failed,
        subject="Математика",
        source_title="Песочница КИМ",
        seed=4242,
    )
    _check(
        errors,
        result["title"] == "Работа над ошибками: Песочница КИМ",
        f"title {result['title']!r}",
    )
    nums = result["failed_nums"]
    _check(errors, set(nums) == set(failed) & set(snapshot), f"RNO nums {nums}")
    _check(errors, all(int(q["num"]) in failed for q in result["questions"]), "kept source KIM nums")
    plot_src = [{"num": n, "text": f"plot {n}", "answer": str(n), "payload": {}} for n in range(1, 6)]
    plot_rno = generate_rno(plot_src, [3], subject="Математика", source_title="plot", seed=11)
    _check(
        errors,
        plot_rno["failed_nums"] == [3],
        f"RNO must not expand 1–5, got {plot_rno['failed_nums']}",
    )

    changed = 0
    for q in result["questions"]:
        num = int(q["num"])
        src_text, src_ans = snapshot[num]
        if str(q.get("text") or "") != src_text or str(q.get("answer") or "") != src_ans:
            changed += 1
        pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        _check(errors, bool(pl.get("rno")), f"#{num} missing rno flag")
        if num < 20 and "{" in str(q.get("text") or ""):
            errors.append(f"RNO #{num} leftover placeholder")
    _check(errors, changed >= 4, f"RNO changed only {changed} tasks")

    for num, (text, ans) in snapshot.items():
        src = next(q for q in questions if int(q["num"]) == num)
        if str(src.get("text") or "") != text or str(src.get("answer") or "") != ans:
            errors.append(f"source #{num} mutated in place")

    other = generate_rno(
        questions,
        failed,
        subject="Математика",
        source_title="Песочница КИМ",
        seed=7777,
    )
    differ = 0
    by_a = {int(q["num"]): q for q in result["questions"]}
    by_b = {int(q["num"]): q for q in other["questions"]}
    for num in failed:
        if num not in by_a or num not in by_b:
            continue
        if by_a[num].get("text") != by_b[num].get("text") or by_a[num].get("answer") != by_b[num].get("answer"):
            differ += 1
    _check(errors, differ >= 3, f"two RNO seeds too similar (differ={differ})")

    q23 = by_a.get(23)
    if q23 and q23.get("text") != snapshot[23][0]:
        errors.append("part 2 geometry text was rewritten")

    print(f"  rno tasks={len(result['questions'])} changed={changed} seed_differ={differ} mutated_count={result['mutated_count']}")
    return errors


def test_mutate_unique_inplace() -> list[str]:
    errors: list[str] = []
    q = {
        "num": 6,
        "part": 1,
        "text": "Найдите значение выражения: ([[1|{a}]] + [[1|{b}]]) · {prod}.",
        "answer": "7",
        "payload": {
            "subtype_code": "math_oge_q06_frac_add",
            "mutator_logic": {
                "variables": {
                    "a": "random_choice([2, 3, 4, 5, 6])",
                    "b": "random_choice([2, 3, 4, 5, 6], exclude=[a])",
                },
                "computed": {"prod": "a * b", "answer": "a + b"},
            },
            "mutator_template": "Найдите значение выражения: ([[1|{a}]] + [[1|{b}]]) · {prod}.",
        },
    }
    apply_mutator_logic_to_question(q, random.Random(1))
    before = (q["text"], q["answer"])
    ok = mutate_question_unique(q, seed=888, math_mode=True)
    after = (q["text"], q["answer"])
    _check(errors, ok, "mutate_question_unique returned False")
    _check(errors, after != before, f"unique mutate did not change values {before} -> {after}")
    _check(errors, "{" not in str(q["text"]), f"placeholder left {q['text']}")
    print(f"  unique: {before[1]!r} -> {after[1]!r}")
    return errors


def test_api_sandbox(questions: list[dict], failed: list[int]) -> list[str]:
    errors: list[str] = []
    try:
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.database import Base, get_db
        from backend.main import app
        from backend.models import Assignment, EduClass, Submission, Teacher
    except Exception as exc:
        errors.append(f"api sandbox import failed: {exc}")
        return errors

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        db = TestingSession()
        teacher = Teacher(name="Песочница", email="sandbox-rno@edusense.local")
        db.add(teacher)
        db.flush()
        classroom = EduClass(
            teacher_id=teacher.id,
            name="9А песочница",
            code="RNOBOX",
            subject="Математика",
            target_exam="oge",
        )
        db.add(classroom)
        db.flush()
        assignment = Assignment(
            class_id=classroom.id,
            title="КИМ песочница",
            code="RNOKIM1",
            questions_json=json.dumps(questions, ensure_ascii=False),
            grading_mode="ai_assist",
            status="active",
        )
        db.add(assignment)
        db.flush()
        items = []
        for q in questions:
            num = int(q.get("num") or 0)
            mx = int(q.get("max_score") or 1)
            failed_here = num in failed
            items.append(
                {
                    "num": num,
                    "max_score": mx,
                    "earned": 0 if failed_here else mx,
                    "status": "wrong" if failed_here else "correct",
                    "part": int(q.get("part") or 1),
                }
            )
        db.add(
            Submission(
                assignment_id=assignment.id,
                student_name="Иванов Иван",
                score=2,
                status="ai_reviewed",
                answers_json="{}",
                ai_review_json=json.dumps({"items": items, "max_score": 31}, ensure_ascii=False),
            )
        )
        db.commit()
        db.close()

        client = TestClient(app)
        empty = client.post("/api/classes/MISSING/analytics/rno", json={"max_tasks": 10})
        _check(errors, empty.status_code in (404, 400), f"missing class status {empty.status_code}")

        resp = client.post(
            "/api/classes/RNOBOX/analytics/rno",
            json={"assignment_code": "RNOKIM1", "max_tasks": 25},
        )
        if resp.status_code != 200:
            errors.append(f"POST /analytics/rno -> {resp.status_code} {resp.text[:400]}")
            return errors
        body = resp.json()
        _check(
            errors,
            str(body.get("title") or "").startswith("Работа над ошибками:"),
            f"api title {body.get('title')!r}",
        )
        api_nums = [int(q.get("num") or 0) for q in (body.get("questions") or [])]
        _check(errors, set(failed) <= set(api_nums), f"api nums {api_nums} missing {failed}")
        _check(errors, set(api_nums) <= set(failed), f"api leaked extra nums {api_nums} beyond {failed}")
        _check(errors, len(body.get("questions") or []) >= 3, "api returned too few questions")
        src_map = {int(q["num"]): (str(q.get("text") or ""), str(q.get("answer") or "")) for q in questions}
        changed = 0
        for q in body.get("questions") or []:
            num = int(q.get("num") or 0)
            if num not in src_map:
                continue
            if (str(q.get("text") or ""), str(q.get("answer") or "")) != src_map[num]:
                changed += 1
        _check(errors, changed >= 3, f"api RNO too similar to source (changed={changed})")
        print(
            f"  api title={body.get('title')!r} questions={len(body.get('questions') or [])} "
            f"mutated={body.get('mutated_count')} nums={body.get('failed_nums')}"
        )
    except Exception as exc:
        errors.append(f"api sandbox crashed: {exc}")
    finally:
        app.dependency_overrides.pop(get_db, None)
    return errors


def main() -> int:
    errors: list[str] = []
    print("== collect_failed / title / parts ==")
    errors.extend(test_collect_failed())

    print("== mutator core (math_oge_mutator.json) ==")
    protos = _load_protos()
    if len(protos) < 10:
        errors.append(f"prototypes too few: {len(protos)}")
    else:
        print(f"  prototypes in spec: {len(protos)}")
    errors.extend(test_mutator_core(protos))

    print("== mutate_question_unique ==")
    errors.extend(test_mutate_unique_inplace())

    print("== generate_rno ==")
    errors.extend(test_generate_rno(protos))

    print("== API sandbox (in-memory sqlite) ==")
    questions = [
        _proto_to_question(p)
        for p in _one_proto_per_slot(protos)
        if int(p.get("task_number") or 0) in {6, 8, 9, 10, 14, 17}
    ]
    fill_math_templates(questions, random.Random(3), enabled=True)
    errors.extend(test_api_sandbox(questions, [6, 8, 9, 10]))

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
