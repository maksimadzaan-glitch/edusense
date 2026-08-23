# ТЗ (адаптированное): pack ОГЭ математика → EduSense

Версия под **существующую** архитектуру: Postgres `task_prototypes` + PG-only generate + optional AI vary.  
Исходное «чистое» filesystem-ТЗ (только JSON-паки, LaTeX-everywhere, полный трекинг) **не** копируется буквально.

---

## 1. Что реализовано

| Слой | Статус |
|------|--------|
| Pack FS `backend/universal/packs/oge_math/` | **есть**: pack_info, topics, context_blocks×3, tasks indexes, variants stub |
| Loader → PG | `backend/universal/packs/loader.py` + `python -m backend.scripts.seed_oge_math_pack` |
| Таблица `context_blocks` | **есть** (context_id, title, description_text, figure_*, exam/subject) |
| `task_prototypes.context_id` | **есть** (+ answer_type, max_score, acceptable_answers) |
| Generate 1–5 | один случайный context_block; общий figure на слотах |
| Generate 6–25 | как раньше — random prototype per slot из PG |
| Answer normalize | `backend/universal/answer_normalize.py` + wire в submit part1 |
| AI vary | **по умолчанию off** в teacher UI; CLI — env `UNIVERSAL_VARY` |
| math_oge.json | остаётся источником слотов 6–25 (+ legacy 1–5 без context) |

### Context blocks в паке

| context_id | Тема | Figure |
|------------|------|--------|
| `dacha_sosnovoe` | Дача / план участка | `plan` + rooms |
| `apartment_2room` | Квартира | `plan` + rooms |
| `tires_factory` | Шины / таблицы | без рисунка (данные в тексте) |

---

## 2. Адаптации относительно «пользовательского» ТЗ

| Было в их ТЗ | Как у нас |
|--------------|-----------|
| Pack как единственный runtime | Pack = **source of truth для сида**; runtime = **Postgres** |
| Variant generator читает JSON | `generate_variant` читает **только PG** |
| LaTeX-only банк | School unicode + `[[a|b]]`; LaTeX не ломаем, не форсируем rewrite |
| Полный scoring/scale tracking | Stub: max_score на прототипе; шкала 31 в pack_info |
| LLM grading part 2 | **Не делаем** сейчас (criteria stub ok) |
| Отдельный variants/ engine | variants/ — опциональный снимок; генерация через CLI/API |

---

## 3. Быстрый цикл

```powershell
python -m backend.scripts.seed_all_subjects
python -m backend.scripts.seed_oge_math_pack
$env:UNIVERSAL_VARY="0"
python -m backend.universal_variant_builder --subject math --exam OGE
python -m backend.universal.answer_normalize
```

После обновления пака — снова `seed_oge_math_pack` (или `--reset-contexts`) и restart API.

---

## 4. Gaps / что прислать (приоритет)

Сохраняем практические JSON-схемы из предыдущего TZ_NEEDED.

### P0 — Более «КИМ-ные» планы 1–5

Нужны раскладки с реальных бланков (номера объектов = ответ). Формат:

```json
{
  "context_id": "dacha_from_blank_01",
  "title": "…",
  "description_text": "общий текст к заданиям 1–5…",
  "figure_kind": "plan",
  "figure_params": {
    "title": "план участка",
    "width": 10,
    "height": 8,
    "gate": { "side": "bottom", "at": 5, "width": 1.5 },
    "rooms": [
      { "id": "3", "label": "Дом", "x": 3.5, "y": 0.5, "w": 4, "h": 3 }
    ]
  },
  "exam_code": "OGE",
  "subject_code": "math",
  "tasks": [
    {
      "task_number": 1,
      "part": 1,
      "prototype_title": "План участка · сопоставление объектов",
      "template_text": "…",
      "correct_answer": "3412",
      "acceptable_answers": ["3412"],
      "answer_type": "digits",
      "max_score": 1
    }
  ]
}
```

Положите файл в `context_blocks/` и запустите seed.

### P1 — Задание 11 (три панели А/Б/В)

```json
{
  "figure_kind": "graph_parabola",
  "figure_params": {
    "panels": [
      { "id": "A", "type": "parabola", "a": 1, "c": 1 },
      { "id": "B", "type": "parabola", "a": -1, "c": 1 },
      { "id": "C", "type": "parabola", "a": 1, "c": -1 }
    ]
  }
}
```

Рендер `panels` ещё не обязателен — можно прислать данные заранее.

### P2 — Задание 13 (4 варианта прямой)

Сейчас показывается верный интервал. Для копии бланка — 4 SVG/описания.

### P3 — Задание 18 (точные фигуры на сетке)

```json
{
  "figure_kind": "grid",
  "figure_params": {
    "cols": 10,
    "rows": 8,
    "polygons": [[[1, 1], [8, 1], [6, 4], [3, 4]]],
    "angle": { "vertex": [1, 1], "p1": [1, 5], "p2": [6, 1] }
  }
}
```

Координаты в **клетках**, начало внизу слева.

### P4 — Часть 2 (20–25)

Тексты + эталонные решения уже частично в `math_oge.json`.  
Критерии баллов / LLM-grading — **out of scope** этого этапа (можно прислать rubric JSON впрок).

### P5 — Трекинг прогресса по темам

`topics.json` есть как карта. Дашборд/статистика по topic_id — позже.

---

## 5. figure_kind (как в системе)

| Значение | Назначение |
|----------|------------|
| `plan` | План участка / квартиры (`rooms`) |
| `numberline` | Числовая прямая |
| `grid` | Клетчатая бумага |
| `graph_linear` / `graph_parabola` / `graph_hyperbola` / `graph_cubic` | Графики |
| `triangle` / `rect` / `circle` / `box3d` | Простая геометрия |

Без `figure_params.rooms` для plan **не** рисуем фейк-планы.

---

## 6. Не делать сейчас

- Полный LLM grading части 2  
- Force LaTeX rewrite всего банка  
- Ломать PG-only generate / vary-off default  
- Commit без явной просьбы
