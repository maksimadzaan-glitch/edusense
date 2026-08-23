# ТЗ: 5 предметов ОГЭ + 5 ЕГЭ (коротко)

Цель: набить паки → потом другие функции продукта.  
Формат ответа нейросети: **только JSON** (как `oge_math_finish`), без кода.

Общая схема задачи:
```json
{
  "task_number": 1,
  "part": 1,
  "prototype_title": "…",
  "template_text": "…",
  "template_answer": "…",
  "template_solution": null,
  "difficulty": "easy|medium|hard",
  "answer_type": "number|string|sequence|detailed",
  "max_score": 1,
  "acceptable_answers": [],
  "figure_kind": null,
  "figure_params": null,
  "context_id": null
}
```
Формулы: школьный вид / `[[a|b]]`, без сырого `\begin`.  
Минимум на предмет: **полный КИМ**, ≥**3** подтипа на номер (ветвистые — 4+), 5 успешных сборок.

---

## ОГЭ

| # | subject_code | exam | Слоты | Особый акцент |
|---|--------------|------|------:|---------------|
| 1 | `math` | OGE | 25 | **Эталон — уже идёт** |
| 2 | `russian` | OGE | 9 | сжа, нормы; мало картинок |
| 3 | `informatics` | OGE | 15 | логика/коды; ответы проверяемые |
| 4 | `social` | OGE | 24 | термины, выборы; ч.2 критерии |
| 5 | `physics` | OGE | 25 | формулы, единицы; схемы по необходимости |

## ЕГЭ

| # | subject_code | exam | Слоты | Особый акцент |
|---|--------------|------|------:|---------------|
| 1 | `math` | EGE | 19 | профиль; геометрия/графики |
| 2 | `russian` | EGE | 27 | орфоэпия→сочинение; критерии ч.2 |
| 3 | `informatics` | EGE | 27 | исполняемые ответы где можно |
| 4 | `social` | EGE | 25 | задания с текстом/графиком |
| 5 | `physics` | EGE | 26 | расчёт + качественные |

`exam_code` в JSON: `OGE` / `EGE`. База ЕГЭ math — отдельно позже (`math_base`).

---

## Порядок работ
1. Добить **OGE math** до приёмки (оставшиеся context_blocks + SVG 23–25).  
2. Параллельно штамповать JSON: **OGE russian → informatics → social → physics**.  
3. Потом **EGE math → russian → informatics → social → physics**.  
4. Стоп по контенту → функции: раздача класса, проверка, аналитика.

## Промпт нейросети (копипаст)
> Сделай контент-пак для {OGE|EGE} · {предмет} по спецификации ФИПИ {год}.  
> Верни JSON: pack_info, context_blocks (если есть связки), tasks[] на все номера КИМ, ≥3 подтипа на номер где уместно.  
> Поля как в ege_tracker (template_text/answer/solution или statement/correct_answer — один стиль на весь файл).  
> Чертежи: SVG в figure_data.svg_content только где нужны в реальном КИМ.  
> Код не пиши.

Папки паков: `backend/universal/packs/{exam}_{subject}/` (пример: `oge_russian`, `ege_physics`).
