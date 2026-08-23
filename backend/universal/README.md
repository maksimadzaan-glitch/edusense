# Universal PostgreSQL test generation

Отдельный контур сборки полных вариантов КИМ через PostgreSQL-**шаблоны** + опциональную лёгкую LLM-вариацию.

**Teacher `/api/ai/generate` = только Postgres.** SQLite (`edusense.db`) остаётся для пользователей, классов, заданий и сдач — **не** как банк заданий для сборки варианта.

**AI** здесь не «история продукта», а опциональный плюс: чуть изменить числа/формулировки (`vary=true` / чекбокс в UI). По умолчанию вариация **выкл.** — мгновенный вариант из шаблонов.

## Идея

1. В PG лежат готовые `template_text` / `template_answer` (+ `template_solution` для части 2).
2. На каждый `task_number` случайно выбирается прототип.
3. Вариант собирается мгновенно из шаблонов.
4. LLM (опционально) лишь слегка меняет числа/формулировки батчами ≤6.
5. При сбое вариации возвращается исходный шаблон.
6. Нет шаблонов для предмета/экзамена → явная ошибка 404/422 (без fallback на SQLite и без полной LLM-генерации КИМ).

Полная генерация 25 заданий одним мега-промптом **не используется**.



## Стек



- Sync SQLAlchemy 2 + **psycopg v3** (`postgresql+psycopg://...`)

- Почему не asyncpg: основной API EduSense уже sync (`Session` + `Depends(get_db)`); отдельный async-движок усложнил бы стек без выигрыша для сида/выборки прототипов.



## Env



В корневом `.env`:



```env

POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal



# LLM — нужен только если включена вариация (vary=true в API или UNIVERSAL_VARY/BANK_VARY для CLI)

AI_PROVIDER=gigachat

# или deepseek / openai

DEEPSEEK_API_KEY=

OPENAI_API_KEY=

OPENAI_BASE_URL=https://api.openai.com/v1

OPENAI_MODEL=gpt-4o-mini



# выключить вариацию в CLI (если флаг vary не передан в generate_variant)
UNIVERSAL_VARY=0
# или: BANK_VARY=0

```



Допускаются и формы `postgresql://...` / `postgres://...` / `postgresql+asyncpg://...` — они нормализуются к `postgresql+psycopg://`.



Если `POSTGRES_URL` нет — `POST /api/universal/generate` отвечает **503**.



## Таблицы



- `subjects` — код/название предмета (`math`, `russian`, …)

- `exam_types` — `OGE`, `EGE`, `VPR_8`, …

- `task_prototypes` — слоты КИМ:

  - `prompt_instruction` — короткая подсказка для вариации

  - `template_text` / `template_answer` / `template_solution` — готовый шаблон



Создание без Alembic: `init_pg_tables()` вызывает `create_all` и `ensure_pg_columns()`  

(`ALTER TABLE … ADD COLUMN IF NOT EXISTS` для уже существующей БД).



## Спеки JSON



Каталог: `backend/universal/specs/*.json`



```json

{

  "subject_code": "math",

  "subject_name": "Математика",

  "exam_code": "OGE",

  "exam_name": "ОГЭ",

  "prototypes": [

    {

      "task_number": 1,

      "part": 1,

      "prototype_title": "Вычисления · ex1",

      "prompt_instruction": "Измени числа и формулировку условия, сохрани тип задания и корректный ответ.",

      "template_text": "Вычислите: (−3)² − 4 · 2.",

      "template_answer": "1"

    }

  ]

}

```



Математика (OGE / EGE профиль / EGE база) собирается из `backend/bank_data/*_math.py`:



```bash

python -m backend.scripts._write_universal_specs

```



## Seed

После pull (если раньше сидили instruction-only прототипы) нужен reset:

```bash
pip install -r requirements.txt
python -m backend.scripts.seed_all_subjects --reset
```

Для ОГЭ математики дополнительно загрузите context blocks (слоты 1–5 с общим планом):

```bash
python -m backend.scripts.seed_oge_math_pack
```

См. `backend/universal/packs/oge_math/README.md`.

Без `--reset` upsert обновит совпадающие по `(subject, exam, task_number, title)` строки,  
но старые instruction-only titles останутся — для чистого перехода предпочтителен `--reset`.



Ориентиры длин:



| Предмет | OGE | EGE |

|---------|-----|-----|

| math | 1–25 (шаблоны) | 1–19 профиль (шаблоны); база → `math_base` 1–21 |

| russian | 1–26 (расш.) | 1–27 |

| physics | 1–25 | 1–25 |

| social | 1–24 | 1–24 |

| biology / history | stub | stub |



Предметы без `template_*`: одиночная LLM-генерация задания как last resort (не мега-промпт).



## Generate



Быстрый тест без LLM (только шаблоны):



```powershell

$env:UNIVERSAL_VARY="0"

python -m backend.universal_variant_builder --subject math --exam OGE

```



С вариацией в CLI (если env не задан, `generate_variant` без `vary=` включает вариацию; teacher API передаёт `vary` явно, default `false`):



```bash

python -m backend.universal_variant_builder --subject math --exam OGE

```



CLI печатает прогресс, например: `собрано из шаблонов: 25; вариация: off`.



API:



```bash

curl -X POST http://127.0.0.1:8000/api/universal/generate ^

  -H "Content-Type: application/json" ^

  -d "{\"subject_code\":\"math\",\"exam_code\":\"OGE\"}"

```



Ответ (схема):



```json

{

  "subject_code": "math",

  "exam_code": "OGE",

  "tasks": [

    {

      "task_number": 1,

      "part": 1,

      "prototype_title": "...",

      "text": "...",

      "answer": "...",

      "solution": null

    }

  ]

}

```



Для `part=2` поле `solution` обязательно непустое.


