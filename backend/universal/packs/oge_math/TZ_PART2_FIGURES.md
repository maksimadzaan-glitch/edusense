# ТЗ: чертежи части 2 ОГЭ math (20–25) — адаптировано под EduSense

Цель: чертежи для слотов **23–25** (решение), редкий чертёж у **22**, **нет** у **20–21**. Runtime — Postgres-прототипы + `figures.py` + teacher lightbox. Сырой AI-SVG без `fipi-fig`/`geo-fig` UI отбрасывает.

---

## MVP сейчас vs позже

| Сейчас (MVP) | Позже |
|--------------|--------|
| Статичные SVG в `assets/figures/part2/` | GeoGebra / интерактив |
| `figure_data` + embed SVG при generate | Dark-mode dual assets |
| Teacher lightbox + «Чертёж к решению» | AI-grading по чертежу |
| Валидация: файл есть, нет `<script`, viewBox/geo-fig | Полный SVGO pipeline |
| `steps[]` хранятся в JSON, без UI | Пошаговый интерактивный рендер |
| 2–3 sample-подтипа (23a / 24a / 25a) | Полный банк чертежей КИМ |

---

## 1. Какие слоты

| № | Рисунок | Правило |
|---|---------|---------|
| **20** | **НЕТ** | Алгебра. `figure_kind: null`, без `figure_data` |
| **21** | **НЕТ** | Текстовые задачи |
| **22** | **Редко** | Только явный `graph_*` в условии; иначе `null` |
| **23** | **ДА** (решение) | Планиметрия на вычисление — sample SVG / `triangle`/`circle`/`rect` |
| **24** | **ДА** (решение) | Доказательство — схема с буквами |
| **25** | **ДА** (решение) | Сложная планиметрия — sample SVG / raw asset |

Авто-детект для 20–25 **выключен**. Без явного `figure_kind` / `figure_data.main_figure_url` рисунка не будет.

---

## 2. Стиль ФИПИ

- Чёрные тонкие линии на **белом** (`#111` / `#fff`)
- Плоский 2D; без теней, градиентов, 3D
- Подписи: Times / serif, вершины A,B,C…
- SVG: `viewBox="0 0 W H"`, классы `geo-fig fipi-fig`
- Доп. построения (позже): пунктир blue/orange только на **шагах решения**, не в условии КИМ
- Без `<script>`, внешних URL, фильтров, анимаций

---

## 3. Схема, которая работает сегодня

### Поля прототипа (PG `task_prototypes`)

| Поле | Тип | Описание |
|------|-----|----------|
| `figure_kind` | string\|null | `triangle`/`rect`/`circle`/`grid`/… или `asset` для pack-SVG |
| `figure_params` | JSON text\|null | параметры процедурного генератора |
| `figure_data` | JSON text\|null | **расширение ТЗ** (см. ниже) |
| `figure_svg` | text\|null | предзагруженный / inline SVG (условие) |

### `figure_data` (MVP)

```json
{
  "has_condition_figure": false,
  "has_solution_figure": true,
  "figure_type": "trapezoid",
  "main_figure_url": "assets/figures/part2/q23_sample_main.svg",
  "steps": [
    { "id": 1, "caption": "провести высоты", "figure_url": null }
  ]
}
```

| Поле | Описание |
|------|----------|
| `has_condition_figure` | показывать в условии (`figure_svg`) |
| `has_solution_figure` | показывать у учителя как «Чертёж к решению» |
| `figure_type` | метка (trapezoid / chords / parallelogram / …) |
| `main_figure_url` | путь относительно пака `oge_math/` |
| `steps` | задел под пошаговые чертежи (UI позже) |

### На выходе generate (`QuestionOut`)

| Поле | Когда |
|------|--------|
| `figure_kind` + `figure_svg` | чертёж **условия** (lightbox в карточке) |
| `solution_figure_svg` | чертёж **к решению** (ключ учителя); ученику не отдаётся |

Правило MVP: у 23–25 обычно `has_condition_figure: false` → SVG уходит в `solution_figure_svg`. Если оба флага true — один и тот же asset может попасть в оба поля.

### Процедурный путь (как раньше)

```json
{
  "figure_kind": "triangle",
  "figure_params": {
    "labels": { "A": "A", "B": "B", "C": "C" },
    "sides": { "AB": "10", "BC": "6", "CA": "8" }
  }
}
```

`figures.py` рисует SVG из kind+params. Для сложной геометрии предпочтителен pack-asset (`figure_kind: "asset"` + `figure_data`).

---

## 4. Файлы и URL

```
packs/oge_math/assets/figures/part2/
  README.md
  q23_sample_main.svg
  q24_sample_main.svg
  q25_sample_main.svg
```

- Статика: `/packs/oge_math/assets/figures/part2/q23_sample_main.svg`
- При generate предпочтительно **embed** содержимого SVG в `figure_svg` / `solution_figure_svg` (lightbox без отдельного fetch)

Пример JSON: `tasks/part2/task_23_sample.json`

---

## 5. Примеры (MVP samples)

**23a** — трапеция + вписанная окружность → `q23_sample_main.svg`  
**24a** — параллелограмм, E середина AB → `q24_sample_main.svg`  
**25a** — две окружности + касательная → `q25_sample_main.svg`

В `math_oge.json` у этих подтипов: `figure_kind: "asset"` + `figure_data`.

---

## 6. Валидация

```powershell
python -m backend.scripts.validate_oge_part2_figures
```

Проверки: файл по `main_figure_url` существует; нет `<script`; есть `viewBox` и класс `geo-fig` или `fipi-fig`.

---

## 7. Seed / тест

```powershell
python -m backend.scripts.seed_all_subjects
# (опционально) python -m backend.scripts.seed_oge_math_pack
$env:UNIVERSAL_VARY="0"
# generate math/OGE → у №23–25 в ключе учителя должен быть «Чертёж к решению»
```

---

## 8. Что прислать исследователю (полный банк — позже)

JSON-массив с `task_number`, `subtype_code`, `figure_kind` / `figure_data` (+ опционально raw SVG).  
Тексты условий не дублировать целиком — достаточно `subtype_code` + figure fields.
