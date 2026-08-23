# Отчёт sandbox QA — 2026-08-11

**Итог: PASS=34 FAIL=0**

База: `http://127.0.0.1:8010` (uvicorn перезапущен с текущим кодом).  
PostgreSQL для `/api/ai/generate`: **доступен**.  
Класс: `EDU-8053`, работа: `EDU-7139`.

Исправлений продукта не потребовалось — все пункты матрицы зелёные.  
`?v=` не бампили (фронт не меняли). Коммитов нет.

---

## A. Core pages — PASS

| Проверка | Статус |
|----------|--------|
| GET `/teacher`, `/student`, `/student/join`, `/student/dashboard` | PASS (200) |
| Static JS/CSS с `?v=115` / `math.js?v=34` | PASS (200) |

## B. Teacher class + generate — PASS

| Проверка | Статус | Детали |
|----------|--------|--------|
| Create class | PASS | `EDU-8053` |
| POST `/api/ai/generate` ОГЭ математика | PASS | **25** реальных заданий, без stub «Эталонное задание», `exam_ui=None` |
| Math без oge_rus chrome | PASS | нет `oge_rus` / `ui=oge_rus` |
| POST generate ОГЭ русский | PASS | **13** заданий, `exam_ui=oge_rus_kim` |
| Rus structure | PASS | 13/13 со структурой |

## C. Publish → student → submit → teacher — PASS

| Шаг | Статус |
|-----|--------|
| Publish assignment | PASS (`EDU-7139`, 25 q) |
| POST `/api/student/join` по коду работы | PASS |
| GET `/api/student/tasks` → active | PASS |
| GET assignment без ключей ответов | PASS (stripped) |
| POST submit | PASS (score=5.0, `ai_reviewed`) |
| GET submissions → ученик виден учителю | PASS |
| Join по коду класса → active в списке | PASS |

## D. Teacher menu APIs — PASS

| API | Статус |
|-----|--------|
| GET `/api/assignments/by-class/{code}` | PASS |
| GET/PUT `/api/classes/{code}/roster` | PASS |
| GET `/api/classes/{code}/students` | PASS |
| GET `/api/classes/{code}/analytics` | PASS (200) |

## E. Regressions — PASS

| Проверка | Статус |
|----------|--------|
| Закрытый `accepting_submissions` → submit 403 | PASS |
| Join на закрытую работу → `closed: true` | PASS |
| Русский №4 matching: `payload.matching.left/right` | PASS (left=3, right=5) |
| Нет stub math etalon в default generate | PASS |

---

## Замечания

- Скрипт прогона: `backend/scripts/_sandbox_qa.py` (вспомогательный, не часть продукта).
- UI smoke (браузер): страницы `/teacher` и `/student` отдаются сервером; полный клик-флоу не требуется — API-цепочка publish→join→submit подтверждена.
- Wave student-work (таймер / progress / autosave / upsert / post-submit): см. секцию ниже. `?v=116` (student). Коммитов нет.

---

## Wave: student-work features — 2026-08-11 19:57 UTC

**Итог: PASS=37 FAIL=0** (после рестарта uvicorn с новым кодом).

Base: `http://127.0.0.1:8010` · Class: `EDU-3214` · Assignment: `EDU-2611` · pg=OK

### Что вошло
1. **Таймер** — countdown на экране работы; после 0: ответы locked, сдача разрешена (комментарий в `student.js`).
2. **Прогресс** — «Отвечено N из M».
3. **Autosave** — localStorage ключ `CODE::name`, restore при продолжении.
4. **Upsert** — повторный submit тем же ФИО → 200, одна строка у учителя.
5. **Post-submit** — score/max, «на проверке» для part2, кнопки в кабинет / разбор.
6. Уже сданная работа при открытии → экран «уже сдано» (+ опционально «Открыть снова»).
7. `accepting_submissions=false` и дедлайн — submit/join 403; фронт тоже блокирует.

### Smoke highlights
| Статус | Проверка | Детали |
|--------|----------|--------|
| PASS | timer_minutes present | timer=45 |
| PASS | submit answers | score=5.0 id=14 |
| PASS | second submit upserts | status=200 id=14 score=4.0 |
| PASS | teacher sees one row per student | score=4.0 |
| PASS | tasks APIs after submit | in completed, not active |
| PASS | submit closed -> 403 | Приём работ закрыт |
| PASS | static student ?v=116 | OK |

*(Промежуточный прогон 19:55 UTC с FAIL=2 — устаревший процесс на :8010 без upsert; не актуален.)*

---

## Wave: student-work features — 2026-08-11 21:09 UTC

Base: `http://127.0.0.1:8010` · Class: `EDU-0429` · Assignment: `EDU-4951`
**PASS=46 FAIL=0** · pg=OK

### Features verified
- Static assets `?v=117`
- Beta badge in landing HTML + teacher/student JS
- Analytics Russian topic labels + remediation gate
- Timer field on publish/GET (`timer_minutes`)
- Submit + second submit upsert (200) + one teacher row per student
- Student tasks APIs after submit (completed / not active)
- Accepting closed / join closed regressions

| Статус | Проверка | Детали |
|--------|----------|--------|
| PASS | GET /teacher | 1491 bytes |
| PASS | GET /student | 1493 bytes |
| PASS | GET /student/join | 1493 bytes |
| PASS | GET /student/dashboard | 1493 bytes |
| PASS | static /css/teacher.css?v=117 | 78463 bytes |
| PASS | static /css/student.css?v=117 | 34623 bytes |
| PASS | static /css/oge_rus_exam.css?v=117 | 21921 bytes |
| PASS | static /css/styles.css?v=117 | 19089 bytes |
| PASS | static /js/teacher.js?v=117 | 165416 bytes |
| PASS | static /js/student.js?v=117 | 68577 bytes |
| PASS | static /js/oge_rus_ui.js?v=117 | 61792 bytes |
| PASS | static /js/math.js?v=34 | 10545 bytes |
| PASS | landing beta badge | HTML |
| PASS | teacher beta badge | JS |
| PASS | student beta badge | JS |
| PASS | create class | code=EDU-0429 id=13 |
| PASS | generate OGE math | 25 tasks, exam_ui=None |
| PASS | math no oge_rus chrome | clean |
| PASS | generate OGE russian | 13 tasks, exam_ui=oge_rus_kim |
| PASS | rus has structure | 13/13 |
| PASS | publish assignment | code=EDU-4951 q=25 |
| PASS | student join assignment | class=EDU-0429 |
| PASS | student tasks active | active=1 |
| PASS | no answer keys on public GET | 25 questions stripped |
| PASS | timer_minutes present | timer=45 |
| PASS | submit answers | score=5.0 status=ai_reviewed id=16 |
| PASS | second submit upserts | status=200 id=16 score=4.0 |
| PASS | teacher sees one row per student | score=4.0 status=ai_reviewed |
| PASS | tasks APIs after submit | in completed, not active |
| PASS | join with class code | 200 |
| PASS | class-code join lists active | n=1 |
| PASS | assignments by-class | n=1 |
| PASS | GET roster | /api/classes/EDU-0429/roster |
| PASS | PUT roster | n=2 |
| PASS | GET students | /api/classes/EDU-0429/students n=2 |
| PASS | GET analytics | /api/classes/EDU-0429/analytics |
| PASS | analytics topics Russian | heat=25 |
| PASS | analytics trend no smoke titles | points=1 |
| PASS | remediation gate fields | ready=False hint=Ждём сдачи всех из списка: сдано 1 из 2 (нет: Сидоров QA) |
| PASS | remediation gated until all submitted | ready=false |
| PASS | analytics summary_lines | Сдали 1 из 2 (50.0%). |
| PASS | close accepting | status=closed |
| PASS | submit closed -> 403 | Приём работ закрыт |
| PASS | join closed shows closed | {'message': 'Приём ответов закрыт', 'closed': True, 'title': 'QA Sandbox Assignment', 'subject': 'Математика', 'code': ' |
| PASS | rus task4 matching/structure | type=Тип 4 keys=['oge_rus', 'kim_type', 'ui', 'image_urls', 'matching', 'media', 'image_paths', 'etalon', 'provenance'] |
| PASS | no stub math etalon | clean |

---

## Wave: student-work features — 2026-08-12 06:16 UTC

Base: `http://127.0.0.1:8010` · Class: `EDU-0987` · Assignment: `EDU-2899`
**PASS=46 FAIL=0** · pg=OK

### Features verified
- Static assets `?v=118`
- Beta badge in landing HTML + teacher/student JS
- Analytics Russian topic labels + remediation gate
- Timer field on publish/GET (`timer_minutes`)
- Submit + second submit upsert (200) + one teacher row per student
- Student tasks APIs after submit (completed / not active)
- Accepting closed / join closed regressions

| Статус | Проверка | Детали |
|--------|----------|--------|
| PASS | GET /teacher | 1622 bytes |
| PASS | GET /student | 1624 bytes |
| PASS | GET /student/join | 1624 bytes |
| PASS | GET /student/dashboard | 1624 bytes |
| PASS | static /css/teacher.css?v=118 | 81396 bytes |
| PASS | static /css/student.css?v=118 | 37568 bytes |
| PASS | static /css/oge_rus_exam.css?v=118 | 21921 bytes |
| PASS | static /css/styles.css?v=118 | 19089 bytes |
| PASS | static /js/teacher.js?v=118 | 179027 bytes |
| PASS | static /js/student.js?v=118 | 75177 bytes |
| PASS | static /js/oge_rus_ui.js?v=118 | 61792 bytes |
| PASS | static /js/math.js?v=34 | 10545 bytes |
| PASS | landing beta badge | HTML |
| PASS | teacher beta badge | JS |
| PASS | student beta badge | JS |
| PASS | create class | code=EDU-0987 id=15 |
| PASS | generate OGE math | 25 tasks, exam_ui=None |
| PASS | math no oge_rus chrome | clean |
| PASS | generate OGE russian | 13 tasks, exam_ui=oge_rus_kim |
| PASS | rus has structure | 13/13 |
| PASS | publish assignment | code=EDU-2899 q=25 |
| PASS | student join assignment | class=EDU-0987 |
| PASS | student tasks active | active=1 |
| PASS | no answer keys on public GET | 25 questions stripped |
| PASS | timer_minutes present | timer=45 |
| PASS | submit answers | score=5.0 status=ai_reviewed id=21 |
| PASS | second submit upserts | status=200 id=21 score=4.0 |
| PASS | teacher sees one row per student | score=4.0 status=ai_reviewed |
| PASS | tasks APIs after submit | in completed, not active |
| PASS | join with class code | 200 |
| PASS | class-code join lists active | n=1 |
| PASS | assignments by-class | n=1 |
| PASS | GET roster | /api/classes/EDU-0987/roster |
| PASS | PUT roster | n=2 |
| PASS | GET students | /api/classes/EDU-0987/students n=2 |
| PASS | GET analytics | /api/classes/EDU-0987/analytics |
| PASS | analytics topics Russian | heat=25 |
| PASS | analytics trend no smoke titles | points=1 |
| PASS | remediation gate fields | ready=False hint=Ждём сдачи всех из списка: сдано 1 из 2 (нет: Сидоров QA) |
| PASS | remediation gated until all submitted | ready=false |
| PASS | analytics summary_lines | Сдали 1 из 2 (50.0%). |
| PASS | close accepting | status=closed |
| PASS | submit closed -> 403 | Приём работ закрыт |
| PASS | join closed shows closed | {'message': 'Приём ответов закрыт', 'closed': True, 'title': 'QA Sandbox Assignment', 'subject': 'Математика', 'code': ' |
| PASS | rus task4 matching/structure | type=Тип 4 keys=['oge_rus', 'kim_type', 'ui', 'image_urls', 'matching', 'media', 'image_paths', 'etalon', 'provenance'] |
| PASS | no stub math etalon | clean |

