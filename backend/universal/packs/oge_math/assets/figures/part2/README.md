# Чертежи части 2 (слоты 23–25)

Статичные SVG в стиле бланка ФИПИ (чёрный/белый). Runtime при generate **встраивает** SVG в вопрос (`figure_svg` / `solution_figure_svg`), чтобы teacher lightbox работал без отдельного fetch.

## Файлы

| Файл | Слот / sample | Содержание |
|------|---------------|------------|
| `q23_sample_main.svg` | 23a | Равнобедренная трапеция + вписанная окружность |
| `q24_sample_main.svg` | 24a | Параллелограмм ABCD, E — середина AB |
| `q25_sample_main.svg` | 25a | Две окружности + общая внешняя касательная |

## URL

- Относительно пака: `assets/figures/part2/q23_sample_main.svg`
- HTTP (static mount): `/packs/oge_math/assets/figures/part2/q23_sample_main.svg`

## Правила

- Классы: `geo-fig fipi-fig`
- Обязателен `viewBox`
- Без `<script>`, внешних URL, анимаций
- Доп. построения (пунктир blue/orange) — только на будущих step-SVG, не в main condition

Валидация: `python -m backend.scripts.validate_oge_part2_figures`
