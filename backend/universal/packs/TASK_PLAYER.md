# Universal Task Player

Аддетивный слой заданий с фиксированными механиками ответа. Не заменяет `task_prototypes` / паки `oge_math` и `oge_rus`.

## Механики (`type`)

| type | UI | Формат `correct_answer` | Автопроверка |
|------|----|-------------------------|--------------|
| `CHOICE_SINGLE` | radio | id варианта (`"2"`) | normalize + equality |
| `CHOICE_MULTI` | checkboxes | цифры/ids без пробелов (`"12"`) | те же цифры в любом порядке |
| `MATCHING` | input на каждый left | конкатенация ответов (`"213"`) | normalize + equality |
| `SHORT_VALUE` | text input | строка (`"60"`) | normalize + equality |
| `FREE_RESPONSE` | textarea | обычно пусто | нет (`ok: null`) |

`normalize_answer`: trim, схлопывание пробелов, lower (кроме сценариев, где автопроверки нет).

## Payload (JSON)

- **CHOICE_***: `{ "options": [ { "id": "1", "text": "…" }, … ] }`
- **MATCHING**: `{ "left": […], "right": […] }` с полями `id` / `text`
- **SHORT_VALUE / FREE_RESPONSE**: произвольные подсказки (`unit`, `min_words`, …)

## Импорт

```bash
python -m backend.scripts.import_tasks backend/universal/packs/tasks_template.json
python -m backend.scripts.import_tasks path/to.json --dry-run
```

Upsert по `id`. Нужен `POSTGRES_URL`. При старте API вызываются `create_all` + `ensure_pg_columns` для таблицы `universal_tasks`.

Или API: `POST /api/tasks/import` с телом `{ "tasks": [ … ] }`.

## API

- `GET /api/tasks?subject=MATH&exam_type=OGE` — список (без ключей)
- `GET /api/tasks/{id}` — одно задание
- `POST /api/tasks/check` — `{ "task_id", "answer" }` → `{ ok, score, max_score }`

## Frontend

`frontend/js/task_renderer.js`: `renderTask(task, container, { onChange })`, `collectAnswer(container, type)`.

Демо: `/task-demo`.
