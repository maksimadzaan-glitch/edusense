# Pack: ОГЭ Математика (`oge_math`)

Filesystem-пак заданий ОГЭ по математике. **Runtime store — PostgreSQL** (`context_blocks` + `task_prototypes`). Generate не читает JSON напрямую.

## Структура

```
oge_math/
  pack_info.json       # метаданные КИМ (31 первичный балл, части)
  topics.json          # темы → номера заданий
  context_blocks/      # связные блоки для слотов 1–5
  assets/figures/part2/ # SVG-чертежи к решению (23–25)
  tasks/part1|part2/   # тонкие индексы + figure samples
  variants/            # опциональные снимки вариантов
  README.md
  TZ_NEEDED.md         # адаптированное ТЗ + gaps
  TZ_PART2_FIGURES.md  # чертежи части 2 (MVP vs later)
```

## Context blocks (слоты 1–5)

В реальном КИМ задания 1–5 опираются на **один** общий текст/план. При `generate_variant(math, OGE)`:

1. выбирается случайный `context_id` с полным набором шаблонов 1–5;
2. слоты 1–5 заполняются прототипами **этого** блока (общий `figure_kind` / `figure_params`);
3. слоты 6–25 — как раньше: случайный прототип на номер из PG.

Сейчас в паке 3 блока: `dacha_sosnovoe`, `apartment_2room`, `tires_factory`.

## Формулы

Предпочтительны школьный unicode и `[[a|b]]` + существующий math.js. LaTeX в тексте допускается, но **не** требуется переписывать банк в LaTeX-only.

## Нормализация ответов (часть 1)

```python
from backend.universal.answer_normalize import normalize_answer, answers_equal

normalize_answer(" 3,5 ")  # "3.5"
answers_equal("−2", "-2")  # True
```

Проверка: `python -m backend.universal.answer_normalize`

Используется при автопроверке сдачи (`/api/assignments/.../submit`).

## Seed

```powershell
# 1) базовые прототипы 1–25 (в т.ч. слоты 6–25; figure_kind части 2)
python -m backend.scripts.seed_all_subjects

# 2) context blocks + связанные prototypes 1–5
python -m backend.scripts.seed_oge_math_pack

# после правок context_blocks/*.json (планы, названия) — обязательно сброс старых ctx:* строк:
python -m backend.scripts.seed_oge_math_pack --reset-contexts
```

После смены `figure_params` / `prototype_title` в JSON нужен re-seed (шаг 2 с `--reset-contexts`), иначе в PG останутся старые `ctx:apt` и дробные комнаты. После сида перезапустите API.

## Чертежи части 2 (23–25)

См. `TZ_PART2_FIGURES.md`. Sample SVG: `assets/figures/part2/`. Подтипы 23a/24a/25a в `math_oge.json` с `figure_kind: "asset"` + `figure_data`.

```powershell
python -m backend.scripts.validate_oge_part2_figures
python -m backend.scripts.seed_all_subjects
```

Статика: `/packs/oge_math/assets/figures/part2/q23_sample_main.svg`  
При generate SVG **встраивается** в `solution_figure_svg` (учительский ключ / lightbox).

## Generate (без AI-вариации)

```powershell
$env:UNIVERSAL_VARY="0"
python -m backend.universal_variant_builder --subject math --exam OGE
```

В прогрессе должно появиться `context_blocks: <id>`. У заданий 1–5 — одинаковый план (`figure_svg`), если у блока есть `figure_params.rooms`.

## Что ещё нужно от методиста

См. `TZ_NEEDED.md`: точные планы с бланков, panels для №11, сетки №18, критерии части 2.
