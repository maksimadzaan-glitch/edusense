# ТЗ: эталонные варианты (100% верность источнику, без AI-изобретений)

**Проект:** ege_tracker  
**Стек:** Python / FastAPI / Postgres / packs (`backend/universal/packs/`)  
**Скоуп сейчас:** только **ОГЭ математика** + **ОГЭ русский**. ЕГЭ — позже.  
**Цель документа:** зафиксировать режим `etalon`, при котором вариант = байт-в-байт верный импорт из легального источника (демо/открытый банк с правом использования / лицензированный комплект), **без** LLM, polish и hotlink-картинок.  
**Не делать в рамках этого ТЗ:** код, скрейпинг ФИПИ, публикацию «официальных КИМ ФИПИ» без лицензии.

---

## Оценка исходного ТЗ

### Что ок
- Жёсткая структура КИМ по слотам `1..N` (math 1–25, rus 1–13).
- Общие блоки контекста (план 1–5 / тексты изложения·грамматики·чтения).
- Локальные медиа + SVG (`figure_svg` / asset) вместо внешних URL.
- Отдельный импортёр без LLM; ключи — из отдельного файла ответов.
- Уже есть packs, `context_blocks`, `TaskPrototype`, `universal_tasks`, `adapt`, `variant_builder` — эталон строится **поверх**, не вместо.

### Что опасно
- **Право:** нельзя свободно скрейпить/редистрибутировать материалы ФИПИ. Импорт только из источника с явным правом (демоверсия для ознакомления — ограниченно; коммерческий банк — по лицензии; ручной ввод учителем своих текстов — ок).
- **Нет официального JSON API ФИПИ** — любой «парсер с сайта» = хрупкий + юридически рискованный путь. Не обещать автоподтягивание с fipi.ru.
- **Hotlink картинок** с чужих CDN умирает (CORS, 403, смена URL). В эталоне — только локальный кэш с checksum.
- **UI-честность:** нельзя писать «официальный КИМ ФИПИ», если нет лицензии. Лейбл: **«Эталонный вариант»** (+ provenance: год / код варианта / источник).
- Текущий пайплайн **ломает эталонность:** `polish_fipi_text`, `polish_answer_key`, `_maybe_vary_tasks` / `UNIVERSAL_VARY`, LLM-ветка в `variant_builder`, частичный rewrite в `adapt`. Для `etalon=true` всё это **обязано быть выключено**.

### Что нереалистично
- «100% как на бланке ФИПИ» без лицензированного контента и ручной приёмки.
- Полный автоимпорт с сайта ФИПИ «как у конкурентов».
- Один `.ts`-скрипт: у нас **Python** (`backend/scripts/…`).
- Обещать идентичность типографики PDF (шрифты бланка) — цель = **смысл + структура + медиа + ключи**, не пиксель-perfect бланк.

---

## Усиленное ТЗ (принять + дополнения)

### 1. Жёсткая структура КИМ
- Спека: `kim_specs/<exam>_<subject>_<year>.json` → список слотов `1..N` с обязательными полями: `task_number`, `part`, `answer_type` / механика, `max_score`, флаги `needs_passage` / `needs_media` / `matching`.
- Импорт **обязан** заполнить все слоты; reorder / skip / merge запрещены.
- Текст условия: **запрет** rephrase, truncate, «улучшения» формулировок, смены нумерации предложений `(1)(2)…`.
- Generate в режиме `mode=etalon`: только выбор уже импортированного эталонного `context_id` / `variant_code` целиком; не сборка «по кускам из банка подтипов».

### 2. Медиа
- В задании/блоке: `payload.media[]` и/или `image_urls[]` (относительные пути в паке).
- Рендер: медиа **перед** текстом вопроса (как в КИМ: рисунок/таблица → формулировка).
- Математика: сохранить текущий `figure_svg` / `figure_kind`+asset; эталонные чертежи — либо inline SVG (safe), либо файл в `assets/`.
- Asset pipeline: скачать **или** положить вручную в  
  `packs/oge_math/assets/…` / `packs/oge_rus/assets/…`  
  с записью checksum (sha256) в provenance/manifest. **Никогда** не полагаться только на внешний hotlink.
- Аудио изложения (rus №1): как сейчас — локальный файл / TTS-fallback; официальные записи ФИПИ в репозиторий **не** класть без права.

### 3. Вёрстка «как в ФИПИ»
- Passage-блоки с нумерацией `(1) (2) …` — сохранять переносы и номера; UI не склеивать в абзац.
- Matching: сетка **А–Б–В** × **1–5** (`payload.matching.left/right` или эквивалент уже используемый в `oge_rus`); ответ — конкатенация цифр в порядке букв.
- Shared-тексты: listening ≠ grammar ≠ reading (уже правило пака `oge_rus`) — в эталоне жёстко.

### 4. Импортёр `import_fipi_variant.py` (Python)
Путь: `backend/scripts/import_fipi_variant.py`.

| Правило | Значение |
|--------|----------|
| LLM | запрещён |
| `polish_fipi_text` / `polish_answer_key` | не вызывать |
| AI vary | off, игнорировать env |
| Вход | JSON эталона (+ отдельный keys-файл) |
| Выход | `context_blocks` / prototypes / optional `universal_tasks` + provenance |
| Идемпотентность | upsert по стабильному id / `context_id` |

Ключи: `correct_answer` / `template_answer` **только** из официального keys-файла (или секции `keys` того же комплекта), **не** из LLM и не «угадыванием».

---

## Дополнения (обязательные)

### A. `provenance` (на context / variant)
```json
{
  "source": "demo2026|licensed_bank|manual_teacher",
  "year": 2026,
  "variant_code": "oge_math_demo_01",
  "kim_spec_id": "oge_math_2026",
  "content_hash": "sha256:…",
  "imported_at": "ISO-8601"
}
```
`content_hash` — от канонического JSON заданий+медиа-метаданных (без `imported_at`).

### B. Флаг `etalon: true`
- На `context_block` и/или записи варианта.
- Generate: при `mode=etalon` выбираются **только** сущности с `etalon=true`; иначе — текущий банк/шаблоны (как сейчас).
- UI: бейдж **«Эталонный вариант»**; не «официальный КИМ ФИПИ» без лицензии в provenance.

### C. Kill mutate path
При `etalon=true` на всём пути до ученика:
- `variant_builder`: без LLM, без `_maybe_vary_tasks`;
- `adapt` / `bank`: **не** вызывать `polish_fipi_text` на statement; не переписывать topic/text;
- `correct_answer` не «полировать» до потери эталонной формы (допустима только документированная нормализация сравнения ответа ученика, не мутация ключа в БД).

### D. Golden tests
- После импорта: dump → reimport → тот же `content_hash`.
- Фикстура: минимальный math + rus эталон в `tests/` или `packs/.../fixtures/`.
- Регресс: при `etalon=true` вызов polish/vary = fail теста (mock/spy).

### E. Human acceptance checklist (до `published`)
Статус черновика → `published` только после ручной галочки:

1. Все слоты спеки заполнены, порядок `1..N`.
2. Тексты сверены с источником (выборочно + спорные номера).
3. Медиа на месте, checksum совпал, превью до вопроса.
4. Passage `(1)(2)…` и matching-сетка отображаются корректно.
5. Ключи сверены с keys-файлом; part2 — критерии, не выдуманный «ответ».
6. Provenance заполнен; UI-лейбл честный.
7. Generate `mode=etalon` отдаёт этот вариант без изменений текста.

### F. Скоуп
| Сейчас | Позже |
|--------|--------|
| OGE math, OGE russian | EGE предметы |

### G. Схема import JSON (согласована с Task / prototype)

Минимальный каркас файла импорта:

```json
{
  "version": 1,
  "etalon": true,
  "kim_spec_id": "oge_math_2026",
  "exam_code": "OGE",
  "subject_code": "math",
  "variant_code": "oge_math_demo_01",
  "provenance": {
    "source": "demo2026",
    "year": 2026,
    "variant_code": "oge_math_demo_01",
    "kim_spec_id": "oge_math_2026",
    "content_hash": "",
    "imported_at": null
  },
  "context": {
    "context_id": "etalon_oge_math_demo_01",
    "title": "Эталон · ОГЭ математика · demo",
    "description_text": "…",
    "etalon": true
  },
  "tasks": [
    {
      "task_number": 1,
      "part": 1,
      "type": "SHORT_VALUE",
      "statement": "…дословно…",
      "payload": {
        "media": [
          {
            "kind": "image",
            "path": "assets/etalon/demo_01/q01.png",
            "sha256": "…",
            "alt": "Рисунок к заданию 1"
          }
        ],
        "image_urls": ["assets/etalon/demo_01/q01.png"],
        "matching": null
      },
      "figure_svg": null,
      "figure_kind": "asset",
      "correct_answer": "",
      "max_score": 1,
      "topic": "…",
      "context_id": "etalon_oge_math_demo_01"
    }
  ],
  "keys_file": "keys/oge_math_demo_01.keys.json"
}
```

**Keys-файл** (отдельно):

```json
{
  "variant_code": "oge_math_demo_01",
  "answers": {
    "1": "12",
    "2": "3"
  }
}
```

Маппинг в модели:
- `TaskPrototype`: `template_text` ← `statement`, `template_answer` ← keys, `figure_svg` / `figure_params` / `context_id`, флаг эталона в JSON params или отдельной колонке/поле context.
- `Task` (player): `statement`, `payload`, `correct_answer`, `type`, `task_number`, …
- Импортёр пишет provenance в context_block (поле верхнего уровня или `figure_params.provenance`).

Для **oge_rus** в `payload` допускаются уже принятые ключи: `grammar_text`, `reading_text`, `listening_text`, `matching`, `kim_type`, `ui` — без перефразирования.

---

## Критерий «готово» (приёмка режима)

1. Скрипт `import_fipi_variant.py` поднимает 1 math + 1 rus эталон из фикстур без сети к LLM.
2. `mode=etalon` generate → тексты = импорт (hash совпал).
3. Polish/vary на эталоне не выполняются (тест).
4. Картинки только из `packs/.../assets`, checksum проверен.
5. UI показывает «Эталонный вариант» + год/код; нет ложного «официальный КИМ ФИПИ».
6. Checklist пройден → статус `published`.

---

## Вне скоупа (явно)

- Автоскрейп fipi.ru / зеркал.
- ЕГЭ-предметы.
- Пиксель-perfect PDF бланка.
- Выкладка чужих аудио/PDF в git без лицензии.
- Переписывание существующих «тренировочных» паков под эталон (они остаются режимом bank/template).

---

## Реализация (кратко)

См. [`ETALON_README.md`](./ETALON_README.md).

- Импортёр: `python -m backend.scripts.import_fipi_variant <etalon.json> [--golden]`
- Спеки слотов: `kim_specs/oge_math_2026.json`, `kim_specs/oge_rus_2026.json`
- Фикстуры: `oge_rus/fixtures/etalon/`, `oge_math/fixtures/etalon/`
- Generate: `mode=etalon` или авто-предпочтение `figure_params.etalon=true`; vary off
- UI: лейбл «Эталонный вариант»; `payload.image_urls` перед текстом вопроса
