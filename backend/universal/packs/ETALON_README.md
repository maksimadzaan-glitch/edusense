# Эталонные варианты (режим `etalon`)

См. полное ТЗ: [`TZ_FIPI_ETALON.md`](./TZ_FIPI_ETALON.md).

## Скоуп

- ОГЭ математика — 25 слотов (`kim_specs/oge_math_2026.json`)
- ОГЭ русский — 13 слотов (`kim_specs/oge_rus_2026.json`)

## Импорт

```bash
# собрать demo-фикстуры (из oge_rus_var_kim + math demo)
python -m backend.scripts.import_fipi_variant --build-fixtures

# импорт в Postgres + golden check
python -m backend.scripts.import_fipi_variant backend/universal/packs/oge_rus/fixtures/etalon/oge_rus_var_kim.etalon.json --golden
python -m backend.scripts.import_fipi_variant backend/universal/packs/oge_math/fixtures/etalon/oge_math_demo_01.etalon.json --golden
```

Без LLM, без `polish_fipi_text` / vary. Ключи — только из `keys_file`.

## Схема JSON (кратко)

| Поле | Назначение |
|------|------------|
| `etalon: true` | флаг комплекта |
| `kim_spec_id` | id спеки слотов |
| `variant_code` | стабильный код варианта |
| `context` | `context_id`, title, description, `etalon` |
| `tasks[]` | слоты `1..N`, `statement` дословно, `payload.image_urls` / `matching` / тексты |
| `keys_file` | `{ "answers": { "1": "...", ... } }` |
| `provenance` | source, year, variant_code, kim_spec_id, content_hash, imported_at |

## Generate

- Если в PG есть контексты с `figure_params.etalon=true` — generate **предпочитает** их (vary принудительно off).
- `mode=etalon` (API) — только эталон; ошибка, если эталонов нет.
- Adapt не полирует statement/options для эталона.
- UI-лейбл: **«Эталонный вариант»** (не «официальный КИМ ФИПИ» без лицензии).

## Фикстуры

- `oge_rus/fixtures/etalon/oge_rus_var_kim.etalon.json` — конвертация `imports/oge_rus_var_kim.json`
- `oge_math/fixtures/etalon/oge_math_demo_01.etalon.json` — демо 1–25 + `assets/etalon/demo_01/q01.svg`
