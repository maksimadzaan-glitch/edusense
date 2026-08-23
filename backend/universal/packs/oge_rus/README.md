# Pack: ОГЭ Русский язык (`oge_rus`)

Цельные варианты КИМ **типы 1–13**:
- 1 — сжатое изложение (`listening_text` + аудио/TTS)
- 2–3 — грамматика по короткому `grammar_text`
- 4 — соответствие (matching)
- 5–9 — пунктуация / орфография / формы / словосочетание
- 10–12 — задания к длинному `reading_text`
- 13 — сочинение 13.1 / 13.2 / 13.3

**Важно:** listening ≠ grammar ≠ reading — тексты не склеивать.

**Правило generate:** один полный `context_id` со слотами 1–13 (vary=False, без перемешивания). Неполные `var_01`… / `var_a` в generate не попадают.

## Seed

```powershell
python -m backend.scripts.import_oge_rus_variants --json backend/universal/packs/oge_rus/imports/oge_rus_variants_full.json
```

Полный пак: `imports/oge_rus_variants_full.json` (эталон структуры: `imports/oge_rus_var_kim.json`)
