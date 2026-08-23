"""ЕГЭ · Базовая математика — банк по слотам полного КИМ 1–21 (≥2–3 варианта на слот)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    # 1 — арифметика
    _t(1, "Вычислите: 15 + 27 − 8.", "34", difficulty="easy", topic="Арифметика"),
    _t(1, "Вычислите: 12 · 5.", "60", difficulty="easy", topic="Арифметика"),
    _t(1, "Вычислите: 96 : 8 + 7.", "19", difficulty="easy", topic="Арифметика"),
    _t(1, "Вычислите: 3² + 4².", "25", difficulty="medium", topic="Степени"),
    _t(1, "Вычислите: √81 − √16.", "5", difficulty="medium", topic="Корни"),
    _t(1, "Вычислите: [[3|4]] + [[1|4]].", "1", difficulty="easy", topic="Дроби"),

    # 2 — проценты / быт
    _t(2, "Найдите 20% от числа 150.", "30", difficulty="easy", topic="Проценты"),
    _t(2, "Товар стоил 400 руб., скидка 10%. Найдите цену со скидкой.", "360", difficulty="medium", topic="Проценты"),
    _t(2, "Число 80 увеличили на 25%. Найдите результат.", "100", difficulty="easy", topic="Проценты"),
    _t(2, "Скидка 15% от 2000 руб. Найдите размер скидки в рублях.", "300", difficulty="medium", topic="Проценты"),
    _t(2, "Зарплата 30000. Повысили на 10%. Найдите новую зарплату.", "33000", difficulty="easy", topic="Проценты"),
    _t(2, "Товар подорожал с 500 до 600 руб. На сколько процентов выросла цена?", "20", difficulty="hard", topic="Проценты"),

    # 3 — геометрия плоскости
    _t(3, "Площадь квадрата со стороной 7 равна…", "49", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Периметр прямоугольника со сторонами 3 и 8 равен…", "22", difficulty="easy", topic="Периметр", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Катеты 6 и 8. Найдите гипотенузу.", "10", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(3, "Сторона квадрата 5. Найдите периметр.", "20", difficulty="easy", topic="Периметр", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Площадь прямоугольника 4×9 равна…", "36", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Радиус окружности 4. Найдите диаметр.", "8", difficulty="medium", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),

    # 4 — вероятность
    _t(4, "Монету бросают один раз. Вероятность орла равна…", "0.5", difficulty="easy", topic="Вероятность", section="probability"),
    _t(4, "В мешке 2 красных и 3 синих карандаша. Вероятность вынуть красный равна…", "0.4", difficulty="medium", topic="Вероятность", section="probability"),
    _t(4, "Кубик бросают один раз. Вероятность выпадения 6 равна…", "1/6", difficulty="easy", topic="Кубик", section="probability"),
    _t(4, "В урне 5 белых и 5 чёрных шаров. Вероятность белого равна…", "0.5", difficulty="easy", topic="Вероятность", section="probability"),
    _t(4, "В классе 10 мальчиков и 15 девочек. Вероятность выбрать девочку равна…", "0.6", difficulty="medium", topic="Выборка", section="probability"),
    _t(4, "Два раза бросают монету. Вероятность двух орлов равна…", "0.25", difficulty="hard", topic="Вероятность", section="probability"),

    # 5 — среднее / степени / текстовые
    _t(5, "Среднее арифметическое 10 и 20 равно…", "15", difficulty="easy", topic="Среднее"),
    _t(5, "Найдите значение 2³.", "8", difficulty="easy", topic="Степени"),
    _t(5, "Среднее арифметическое 5, 7 и 9 равно…", "7", difficulty="easy", topic="Среднее"),
    _t(5, "Найдите 3⁴.", "81", difficulty="medium", topic="Степени"),
    _t(5, "Автомобиль ехал 2 часа со скоростью 60 км/ч. Какой путь он проехал?", "120", difficulty="easy", topic="Движение"),
    _t(5, "Найдите НОД чисел 12 и 18.", "6", difficulty="medium", topic="НОД"),

    # 6 — графики / функции
    _t(6, "На графике y = x отмечена точка при x = 3. Найдите y.", "3", difficulty="easy", topic="График", section="functions", needs_figure=1, figure_kind="graph_linear"),
    _t(6, "Найдите f(2) для f(x) = 5x − 1.", "9", difficulty="medium", topic="Функция", section="functions"),
    _t(6, "Найдите f(0) для f(x) = 4x + 7.", "7", difficulty="easy", topic="Функция", section="functions"),
    _t(6, "Найдите f(3) для f(x) = x².", "9", difficulty="easy", topic="Функция", section="functions", needs_figure=1, figure_kind="graph_parabola"),
    _t(6, "Прямая y = x + 2. Найдите y при x = 5.", "7", difficulty="easy", topic="График", section="functions", needs_figure=1, figure_kind="graph_linear"),
    _t(6, "Найдите нуль функции f(x) = 2x − 10.", "5", difficulty="medium", topic="Нуль функции", section="functions"),

    # 7 — уравнения
    _t(7, "Решите уравнение 3x − 9 = 0.", "3", difficulty="easy", topic="Уравнения"),
    _t(7, "Решите уравнение 2x + 5 = 17.", "6", difficulty="easy", topic="Уравнения"),
    _t(7, "Решите уравнение x² = 49. Укажите положительный корень.", "7", difficulty="medium", topic="Уравнения"),
    _t(7, "Решите уравнение x² − 5x + 6 = 0. Укажите больший корень.", "3", difficulty="medium", topic="Квадратные"),

    # 8 — неравенства
    _t(8, "Решите неравенство x > 3. Укажите наименьшее целое решение.", "4", difficulty="easy", topic="Неравенства", needs_figure=1, figure_kind="numberline"),
    _t(8, "Решите неравенство 2x − 4 ≤ 6. Укажите наибольшее целое решение.", "5", difficulty="medium", topic="Неравенства"),
    _t(8, "Решите неравенство x² < 9. Укажите длину промежутка решения.", "6", difficulty="hard", topic="Неравенства", needs_figure=1, figure_kind="numberline"),

    # 9 — треугольники / Пифагор
    _t(9, "Катеты 9 и 12. Найдите гипотенузу.", "15", difficulty="easy", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(9, "Гипотенуза 13, катет 5. Найдите второй катет.", "12", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(9, "Площадь прямоугольного треугольника с катетами 6 и 8 равна…", "24", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="triangle"),

    # 10 — окружность / многоугольники
    _t(10, "Радиус окружности 6. Найдите длину диаметра.", "12", difficulty="easy", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(10, "Сторона правильного шестиугольника 4. Найдите периметр.", "24", difficulty="medium", topic="Многоугольник", section="planimetry"),
    _t(10, "Площадь круга равна 25π. Найдите радиус.", "5", difficulty="medium", topic="Круг", section="planimetry", needs_figure=1, figure_kind="circle"),

    # 11 — стереометрия
    _t(11, "Ребро куба 4. Найдите объём.", "64", difficulty="easy", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Параллелепипед 2×3×5. Найдите объём.", "30", difficulty="easy", topic="Параллелепипед", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Ребро куба 3. Найдите площадь полной поверхности.", "54", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),

    # 12 — проценты / вклад
    _t(12, "Вклад 10000 руб. увеличили на 8%. Найдите новую сумму.", "10800", difficulty="easy", topic="Проценты"),
    _t(12, "Цена 2500 руб., скидка 12%. Найдите цену со скидкой.", "2200", difficulty="medium", topic="Проценты"),
    _t(12, "Число уменьшили на 10% и получили 90. Найдите исходное число.", "100", difficulty="hard", topic="Проценты"),

    # 13 — таблицы / данные
    _t(13, "В таблице: 12, 15, 18, 21. Найдите среднее арифметическое.", "16.5", difficulty="medium", topic="Статистика"),
    _t(13, "Оценки: 3, 4, 5, 4, 4. Найдите медиану.", "4", difficulty="easy", topic="Статистика"),
    _t(13, "Сумма чисел 8, 12 и 16 равна… Найдите среднее.", "12", difficulty="easy", topic="Среднее"),

    # 14 — движение / работа
    _t(14, "Пешеход шёл 4 часа со скоростью 5 км/ч. Какой путь?", "20", difficulty="easy", topic="Движение"),
    _t(14, "Поезд проехал 240 км за 3 часа. Найдите скорость в км/ч.", "80", difficulty="easy", topic="Движение"),
    _t(14, "Два крана наполняют бассейн за 6 часов. Сколько часов нужно одному (в 2 раза медленнее пары)?", "12", difficulty="hard", topic="Работа"),

    # 15 — логика / выбор
    _t(15, "Сколько простых чисел среди 2, 3, 4, 5, 6, 7?", "4", difficulty="medium", topic="Логика"),
    _t(15, "Найдите наименьшее двузначное число, кратное 7.", "14", difficulty="easy", topic="Числа"),
    _t(15, "Сколько делителей у числа 18?", "6", difficulty="medium", topic="Делители"),

    # 16 — координаты
    _t(16, "Точки A(0; 0) и B(3; 4). Найдите длину AB.", "5", difficulty="medium", topic="Координаты", section="geometry"),
    _t(16, "Вектор a(3; 4). Найдите |a|.", "5", difficulty="easy", topic="Векторы", section="geometry"),
    _t(16, "Точка M(2; −1). Найдите сумму координат.", "1", difficulty="easy", topic="Координаты", section="geometry"),

    # 17 — выражения
    _t(17, "Упростите и найдите значение: 2(x + 3) при x = 4.", "14", difficulty="easy", topic="Выражения"),
    _t(17, "Найдите значение (a + b)² при a = 2, b = 3.", "25", difficulty="medium", topic="Выражения"),
    _t(17, "Вычислите: [[2|3]] · 6.", "4", difficulty="easy", topic="Дроби"),

    # 18 — практическая геометрия
    _t(18, "Комната 5×6 м. Найдите площадь пола в м².", "30", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(18, "Участок 12 м на 8 м. Найдите периметр в метрах.", "40", difficulty="easy", topic="Периметр", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(18, "Квадратный участок со стороной 10 м. Найдите площадь.", "100", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),

    # 19 — вероятность / комбинаторика
    _t(19, "В лотерее 10 билетов, 2 выигрышных. Вероятность выигрышного равна…", "0.2", difficulty="easy", topic="Вероятность", section="probability"),
    _t(19, "Сколько двузначных чисел можно составить из цифр 1 и 2 (цифры могут повторяться)?", "4", difficulty="medium", topic="Комбинаторика"),
    _t(19, "Кубик бросают один раз. Вероятность числа больше 4 равна…", "1/3", difficulty="medium", topic="Кубик", section="probability"),

    # 20 — функции
    _t(20, "Найдите f(−3) для f(x) = 2x + 1.", "−5", difficulty="easy", topic="Функция", section="functions"),
    _t(20, "Найдите нуль функции f(x) = x − 8.", "8", difficulty="easy", topic="Нуль функции", section="functions"),
    _t(20, "Найдите f(4) для f(x) = x² − 5x.", "−4", difficulty="medium", topic="Функция", section="functions", needs_figure=1, figure_kind="graph_parabola"),

    # 21 — итоговая прикладная
    _t(21, "Товар стоил 1200 руб. Скидка 25%, затем наценка 10% на новую цену. Найдите итоговую цену.", "990", difficulty="hard", topic="Проценты"),
    _t(21, "Смешали 2 л воды и 3 л сока. Какова доля сока в смеси (в виде десятичной дроби)?", "0.6", difficulty="medium", topic="Доли"),
    _t(21, "Билет 800 руб., студенческая скидка 50%. Сколько заплатит студент?", "400", difficulty="easy", topic="Проценты"),
]
