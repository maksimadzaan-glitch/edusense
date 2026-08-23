"""ОГЭ · Математика — банк по слотам полного КИМ 1–25 (≥2 варианта на слот)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    # 1 — вычисления
    _t(1, "Вычислите: (−3)² − 4 · 2.", "1", difficulty="easy", topic="Вычисления"),
    _t(1, "Найдите значение [[2|5]] + [[3|5]].", "1", difficulty="easy", topic="Дроби"),
    _t(1, "Вычислите: 2³ · 3 − 10.", "14", difficulty="easy", topic="Вычисления"),
    _t(1, "Вычислите: √64 + √36.", "14", difficulty="medium", topic="Корни"),
    _t(1, "Вычислите: [[7|8]] − [[3|8]].", "0.5", difficulty="medium", topic="Дроби"),
    _t(1, "Вычислите: 5! : 4!.", "5", difficulty="hard", topic="Факториал"),

    # 2 — уравнения
    _t(2, "Решите уравнение 2x + 5 = 17.", "6", difficulty="easy", topic="Уравнения"),
    _t(2, "Решите уравнение x² = 49. Укажите положительный корень.", "7", difficulty="medium", topic="Уравнения"),
    _t(2, "Решите уравнение 3x − 9 = 0.", "3", difficulty="easy", topic="Уравнения"),
    _t(2, "Решите уравнение x² − 5x + 6 = 0. Укажите больший корень.", "3", difficulty="medium", topic="Квадратные уравнения"),
    _t(2, "Решите уравнение √(x + 3) = 4.", "13", difficulty="hard", topic="Иррациональные"),
    _t(2, "Решите уравнение |x| = 5. Укажите положительный корень.", "5", difficulty="medium", topic="Модуль"),

    # 3 — планиметрия
    _t(3, "Площадь прямоугольника 4×9 равна…", "36", difficulty="easy", topic="Планиметрия", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Катеты 5 и 12. Найдите гипотенузу.", "13", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(3, "Сторона квадрата 6. Найдите площадь.", "36", difficulty="easy", topic="Квадрат", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Периметр равностороннего треугольника со стороной 5 равен…", "15", difficulty="easy", topic="Треугольник", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(3, "Радиус окружности 7. Найдите диаметр.", "14", difficulty="easy", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(3, "В прямоугольном треугольнике катеты 9 и 12. Найдите гипотенузу.", "15", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),

    # 4 — вероятность
    _t(4, "В урне 4 белых и 6 чёрных шаров. Вероятность белого равна…", "0.4", difficulty="easy", topic="Вероятность", section="probability"),
    _t(4, "Монету бросают один раз. Вероятность решки равна…", "0.5", difficulty="easy", topic="Монета", section="probability"),
    _t(4, "Кубик бросают один раз. Вероятность чётного числа равна…", "0.5", difficulty="medium", topic="Кубик", section="probability"),
    _t(4, "В коробке 3 красных и 7 синих шаров. Вероятность красного равна…", "0.3", difficulty="easy", topic="Вероятность", section="probability"),
    _t(4, "Два раза бросают монету. Вероятность двух решек равна…", "0.25", difficulty="hard", topic="Вероятность", section="probability"),
    _t(4, "В классе 8 юношей и 12 девушек. Вероятность выбрать юношу равна…", "0.4", difficulty="medium", topic="Выборка", section="probability"),

    # 5 — проценты / текстовые
    _t(5, "Найдите 15% от 200.", "30", difficulty="easy", topic="Проценты"),
    _t(5, "Товар стоил 500 руб., скидка 20%. Найдите цену со скидкой.", "400", difficulty="medium", topic="Проценты"),
    _t(5, "Число 60 увеличили на 50%. Найдите результат.", "90", difficulty="easy", topic="Проценты"),
    _t(5, "Автомобиль проехал 150 км за 3 часа. Найдите скорость в км/ч.", "50", difficulty="easy", topic="Движение"),
    _t(5, "Найдите 12% от 250.", "30", difficulty="medium", topic="Проценты"),
    _t(5, "Скидка 25% от 800 руб. Найдите размер скидки.", "200", difficulty="easy", topic="Проценты"),

    # 6 — функции / графики
    _t(6, "f(x) = 3x + 1. Найдите f(4).", "13", difficulty="easy", topic="Функции", section="functions"),
    _t(6, "f(x) = x² − 1. Найдите f(3).", "8", difficulty="easy", topic="Функции", section="functions", needs_figure=1, figure_kind="graph_parabola"),
    _t(6, "Найдите нуль функции f(x) = 5x − 20.", "4", difficulty="medium", topic="Нуль функции", section="functions"),
    _t(6, "f(x) = 2x − 7. Найдите f(5).", "3", difficulty="easy", topic="Функции", section="functions", needs_figure=1, figure_kind="graph_linear"),
    _t(6, "Дана y = k/x. При x = 4 значение y = 2. Найдите k.", "8", difficulty="medium", topic="Гипербола", section="functions", needs_figure=1, figure_kind="graph_hyperbola"),
    _t(6, "Найдите f(−1) для f(x) = x² + 3x.", "−2", difficulty="hard", topic="Функции", section="functions"),

    # 7 — геометрия / площади
    _t(7, "Площадь треугольника с основанием 10 и высотой 6 равна…", "30", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(7, "Площадь ромба с диагоналями 6 и 8 равна…", "24", difficulty="medium", topic="Ромб", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(7, "Сторона квадрата 9. Найдите площадь.", "81", difficulty="easy", topic="Квадрат", section="planimetry", needs_figure=1, figure_kind="rect"),

    # 8 — числа / прогрессии
    _t(8, "Найдите НОД чисел 24 и 36.", "12", difficulty="easy", topic="НОД"),
    _t(8, "Найдите 5-й член арифметической прогрессии 3, 7, 11, …", "19", difficulty="medium", topic="Прогрессии"),
    _t(8, "Найдите НОК чисел 4 и 6.", "12", difficulty="medium", topic="НОК"),

    # 9 — алгебраические выражения
    _t(9, "Упростите: 2a + 3a при a = 4. Найдите значение.", "20", difficulty="easy", topic="Выражения"),
    _t(9, "Найдите значение (x − 2)(x + 2) при x = 5.", "21", difficulty="medium", topic="Выражения"),
    _t(9, "Вычислите: 3² · 2³.", "72", difficulty="easy", topic="Степени"),

    # 10 — неравенства
    _t(10, "Решите неравенство x − 5 < 0. Укажите наибольшее целое решение.", "4", difficulty="easy", topic="Неравенства", needs_figure=1, figure_kind="numberline"),
    _t(10, "Решите неравенство 3x ≥ 12. Укажите наименьшее целое решение.", "4", difficulty="easy", topic="Неравенства"),
    _t(10, "Решите неравенство |x| ≤ 2. Укажите длину промежутка решения.", "4", difficulty="medium", topic="Модуль", needs_figure=1, figure_kind="numberline"),

    # 11 — треугольники
    _t(11, "Катеты 8 и 15. Найдите гипотенузу.", "17", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(11, "В равнобедренном треугольнике основание 10, боковая сторона 13. Высота к основанию равна 12. Найдите площадь.", "60", difficulty="medium", topic="Треугольник", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(11, "Периметр равностороннего треугольника 18. Найдите сторону.", "6", difficulty="easy", topic="Треугольник", section="planimetry", needs_figure=1, figure_kind="triangle"),

    # 12 — окружность
    _t(12, "Радиус 5. Найдите длину диаметра.", "10", difficulty="easy", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(12, "Диаметр 14. Найдите радиус.", "7", difficulty="easy", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(12, "Площадь круга 49π. Найдите радиус.", "7", difficulty="medium", topic="Круг", section="planimetry", needs_figure=1, figure_kind="circle"),

    # 13 — стереометрия
    _t(13, "Объём куба с ребром 3 равен…", "27", difficulty="medium", topic="Стереометрия", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(13, "Ребро куба 5. Найдите площадь полной поверхности.", "150", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(13, "Параллелепипед 2×3×4. Найдите объём.", "24", difficulty="easy", topic="Параллелепипед", section="stereometry", needs_figure=1, figure_kind="box3d"),

    # 14 — координаты / график
    _t(14, "Точки A(1; 2) и B(4; 6). Найдите длину AB.", "5", difficulty="medium", topic="Координаты", section="geometry"),
    _t(14, "Прямая y = 2x − 1. Найдите y при x = 3.", "5", difficulty="easy", topic="График", section="functions", needs_figure=1, figure_kind="graph_linear"),
    _t(14, "Вектор a(6; 8). Найдите |a|.", "10", difficulty="easy", topic="Векторы", section="geometry"),

    # 15 — текстовая
    _t(15, "Два рабочих за 5 дней зарабатывают вместе 10000 руб. Сколько зарабатывает один в день, если они получают поровну?", "1000", difficulty="medium", topic="Текстовая"),
    _t(15, "Книга стоила 400 руб. Подорожала на 15%. Найдите новую цену.", "460", difficulty="easy", topic="Проценты"),
    _t(15, "Смешали 3 кг по 40 руб. и 2 кг по 60 руб. Найдите среднюю цену за 1 кг.", "48", difficulty="hard", topic="Смеси"),

    # 16 — вероятность / статистика
    _t(16, "Оценки: 2, 3, 4, 5, 5. Найдите среднее арифметическое.", "3.8", difficulty="medium", topic="Статистика"),
    _t(16, "В урне 1 белый и 4 чёрных. Вероятность белого равна…", "0.2", difficulty="easy", topic="Вероятность", section="probability"),
    _t(16, "Кубик бросают дважды. Вероятность двух шестёрок равна…", "1/36", difficulty="hard", topic="Вероятность", section="probability"),

    # 17 — практическая геометрия
    _t(17, "Комната 4×5 м. Найдите площадь в м².", "20", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(17, "Забор вокруг квадратного участка со стороной 15 м. Найдите длину забора.", "60", difficulty="easy", topic="Периметр", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(17, "Треугольный участок: основание 12, высота 5. Найдите площадь.", "30", difficulty="medium", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="triangle"),

    # 18 — системы (краткий)
    _t(18, "Решите систему: x + y = 10 и x − y = 2. Укажите x.", "6", difficulty="medium", topic="Системы"),
    _t(18, "Решите систему: 2x + y = 7 и x − y = 2. Укажите y.", "1", difficulty="easy", topic="Системы"),
    _t(18, "Решите систему: x + 2y = 8 и 3x − y = 3. Укажите x.", "2", difficulty="hard", topic="Системы"),

    # 19 — итог части 1
    _t(19, "Найдите значение выражения 2⁵ − 3².", "23", difficulty="medium", topic="Вычисления"),
    _t(19, "Сколько процентов составляет 18 от 72?", "25", difficulty="easy", topic="Проценты"),
    _t(19, "Среднее арифметическое 6, 9 и 15 равно…", "10", difficulty="easy", topic="Среднее"),

    # 20–25 — часть 2
    _t(20, "Решите уравнение x² − 5x + 4 = 0. Укажите меньший корень.", "1", part=2, difficulty="medium", topic="Уравнения", max_score=2),
    _t(20, "Решите систему: x + y = 10 и x − y = 2. Укажите x.", "6", part=2, difficulty="medium", topic="Системы", max_score=2),
    _t(20, "Решите уравнение 2x² − 5x − 3 = 0. Укажите больший корень.", "3", part=2, difficulty="hard", topic="Уравнения", max_score=2),

    _t(21, "Решите неравенство x² − 4 < 0. Укажите длину промежутка решения.", "4", part=2, difficulty="medium", topic="Неравенства", max_score=2),
    _t(21, "Решите неравенство (x − 1)(x − 5) ≤ 0. Укажите длину промежутка решения.", "4", part=2, difficulty="hard", topic="Неравенства", max_score=2),
    _t(21, "Решите неравенство 2x − 7 ≥ 3. Укажите наименьшее целое решение.", "5", part=2, difficulty="easy", topic="Неравенства", max_score=2),

    _t(22, "Товар стоил 2000 руб. Подорожал на 10%, затем подешевел на 10%. Найдите итоговую цену.", "1980", part=2, difficulty="medium", topic="Экономика", max_score=2),
    _t(22, "Вклад 50000 под 8% годовых. Найдите сумму через 1 год.", "54000", part=2, difficulty="easy", topic="Экономика", max_score=2),
    _t(22, "Зарплата 35000. Повысили на 20%. Найдите новую зарплату.", "42000", part=2, difficulty="easy", topic="Проценты", max_score=2),

    _t(23, "В треугольнике катеты 6 и 8. Найдите гипотенузу. Обоснуйте.", "10", part=2, difficulty="easy", topic="Пифагор", section="planimetry", max_score=2, needs_figure=1, figure_kind="triangle"),
    _t(23, "В треугольнике стороны 5, 12, 13. Найдите площадь.", "30", part=2, difficulty="medium", topic="Планиметрия", section="planimetry", max_score=2, needs_figure=1, figure_kind="triangle"),
    _t(23, "Диагонали ромба 10 и 24. Найдите площадь.", "120", part=2, difficulty="medium", topic="Ромб", section="planimetry", max_score=2),

    _t(24, "Куб с ребром 4. Найдите объём.", "64", part=2, difficulty="easy", topic="Стереометрия", section="stereometry", max_score=2),
    _t(24, "Параллелепипед 3×4×5. Найдите площадь полной поверхности.", "94", part=2, difficulty="medium", topic="Стереометрия", section="stereometry", max_score=2),
    _t(24, "Цилиндр: радиус 3, высота 4. Найдите объём, делённый на π.", "36", part=2, difficulty="hard", topic="Цилиндр", section="stereometry", max_score=2),

    _t(25, "Найдите наименьшее значение f(x) = x² − 6x + 10.", "1", part=2, difficulty="medium", topic="Функции", section="analysis", max_score=2),
    _t(25, "При каких целых a > 0 уравнение x² − ax + 4 = 0 имеет два различных корня? Укажите наименьшее такое a.", "5", part=2, difficulty="hard", topic="Параметр", max_score=2),
    _t(25, "Найдите точку минимума f(x) = x² − 4x + 1. Укажите x.", "2", part=2, difficulty="medium", topic="Экстремум", section="analysis", max_score=2),
]
