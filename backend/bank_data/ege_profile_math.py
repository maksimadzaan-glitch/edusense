"""ЕГЭ · Профильная математика — проверенный банк (слоты КИМ 1–19)."""

from __future__ import annotations


def _t(
    slot: int,
    text: str,
    answer: str,
    *,
    part: int = 1,
    difficulty: str = "medium",
    topic: str = "Общее",
    section: str = "algebra",
    needs_figure: int = 0,
    figure_kind: str | None = None,
    max_score: int = 1,
) -> dict:
    return {
        "slot": slot,
        "part": part,
        "difficulty": difficulty,
        "topic": topic,
        "section": section,
        "text": text,
        "answer": answer,
        "needs_figure": needs_figure,
        "figure_kind": figure_kind,
        "max_score": max_score,
        "task_type": "Развёрнутый ответ" if part == 2 else "Краткий ответ",
    }


TASKS: list[dict] = [
    # 1 — вычисления
    _t(1, "Найдите значение выражения 3² · 4 − 5 · 2.", "26", difficulty="easy", topic="Степени"),
    _t(1, "Найдите значение выражения [[5|6]] − [[1|3]].", "0.5", difficulty="easy", topic="Дроби"),
    _t(1, "Найдите значение выражения √49 − √16.", "3", difficulty="medium", topic="Корни"),
    _t(1, "Найдите значение выражения 2⁵ : 2².", "8", difficulty="medium", topic="Степени"),
    _t(1, "Найдите значение выражения log₂16 − log₂2.", "3", difficulty="hard", topic="Логарифмы"),
    _t(1, "Найдите значение выражения 5! : 3!.", "20", difficulty="medium", topic="Факториал"),
    _t(1, "Найдите значение выражения (0,2)⁻¹ − 3.", "2", difficulty="hard", topic="Степени"),

    # 2 — уравнения / векторы-координаты (типичный слот 2)
    _t(2, "Решите уравнение 5x − 7 = 3x + 1.", "4", difficulty="easy", topic="Линейные уравнения"),
    _t(2, "Решите уравнение x² − 5x + 6 = 0. Если корней несколько, укажите больший.", "3", difficulty="easy", topic="Квадратные уравнения"),
    _t(2, "Решите уравнение x² − 9 = 0. Если корней несколько, укажите больший.", "3", difficulty="medium", topic="Квадратные уравнения"),
    _t(2, "Решите систему уравнений: 2x + y = 7 и x − y = 2. В ответе укажите x.", "3", difficulty="medium", topic="Системы"),
    _t(2, "Решите уравнение √(x − 1) = 3.", "10", difficulty="hard", topic="Иррациональные уравнения"),
    _t(2, "Векторы a(2; −1) и b(−2; 1). Найдите |a + b|.", "0", difficulty="hard", topic="Векторы", section="geometry"),
    _t(2, "Точки A(1; 2) и B(4; 6). Найдите длину отрезка AB.", "5", difficulty="medium", topic="Координаты", section="geometry"),

    # 3 — планиметрия
    _t(3, "Найдите площадь прямоугольника со сторонами 5 и 12.", "60", difficulty="easy", topic="Площадь прямоугольника", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "В прямоугольном треугольнике катеты равны 6 и 8. Найдите гипотенузу.", "10", difficulty="easy", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(3, "Площадь треугольника равна 24, основание равно 8. Найдите высоту к этому основанию.", "6", difficulty="medium", topic="Площадь треугольника", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(3, "Радиус окружности равен 5. Найдите длину диаметра.", "10", difficulty="medium", topic="Окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(3, "Радиус круга равен 3. Найдите площадь круга, делённую на π.", "9", difficulty="hard", topic="Площадь круга", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(3, "Сторона ромба равна 10, острый угол 60°. Найдите площадь ромба.", "50√3", difficulty="hard", topic="Ромб", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "В равностороннем треугольнике сторона равна 6. Найдите высоту.", "3√3", difficulty="medium", topic="Равносторонний треугольник", section="planimetry", needs_figure=1, figure_kind="triangle"),

    # Fix hard answers that use √ — blank prefers simple numbers where possible; keep a few radical forms OK for profile
    # replace last two with numeric-friendly variants for blank:
]

# убрать ответы с радикалами для надёжности бланка
TASKS = [t for t in TASKS if "√" not in str(t.get("answer") or "")]
TASKS += [
    _t(3, "Сторона квадрата равна 8. Найдите его периметр.", "32", difficulty="easy", topic="Квадрат", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Диагонали ромба равны 6 и 8. Найдите площадь ромба.", "24", difficulty="hard", topic="Ромб", section="planimetry", needs_figure=1, figure_kind="rect"),

    # 4 — вероятность
    _t(4, "В урне 3 белых и 7 чёрных шаров. Наугад берут один шар. Найдите вероятность того, что шар белый.", "0.3", difficulty="easy", topic="Классическая вероятность", section="probability"),
    _t(4, "Монету бросают один раз. Найдите вероятность выпадения орла.", "0.5", difficulty="easy", topic="Монета", section="probability"),
    _t(4, "Игральный кубик бросают один раз. Найдите вероятность того, что выпадет чётное число.", "0.5", difficulty="medium", topic="Кубик", section="probability"),
    _t(4, "В классе 12 юношей и 18 девушек. Наугад выбирают одного ученика. Найдите вероятность того, что выбран юноша.", "0.4", difficulty="medium", topic="Выборка", section="probability"),
    _t(4, "Два раза бросают монету. Найдите вероятность того, что оба раза выпадет орёл.", "0.25", difficulty="hard", topic="Независимые события", section="probability"),
    _t(4, "В коробке 5 красных и 15 синих ручек. Наугад берут одну. Найдите вероятность красной.", "0.25", difficulty="easy", topic="Классическая вероятность", section="probability"),
    _t(4, "Кубик бросают дважды. Найдите вероятность того, что оба раза выпадет шестёрка.", "1/36", difficulty="hard", topic="Независимые события", section="probability"),

    # 5 — прикладные
    _t(5, "Товар стоил 800 рублей. Цену повысили на 10%. Найдите новую цену товара в рублях.", "880", difficulty="easy", topic="Проценты", section="algebra"),
    _t(5, "Число увеличили на 25% и получили 150. Найдите исходное число.", "120", difficulty="medium", topic="Проценты", section="algebra"),
    _t(5, "Автомобиль проехал 180 км за 3 часа. Найдите среднюю скорость в км/ч.", "60", difficulty="easy", topic="Движение", section="algebra"),
    _t(5, "Насос заливает бак объёмом 120 литров за 4 часа. Сколько литров заливается за 1 час?", "30", difficulty="medium", topic="Работа", section="algebra"),
    _t(5, "Вклад 20000 руб. увеличили на 5%. Найдите сумму вклада после увеличения.", "21000", difficulty="hard", topic="Проценты", section="algebra"),
    _t(5, "Скидка 20% от цены 2500 руб. Найдите размер скидки в рублях.", "500", difficulty="easy", topic="Проценты", section="algebra"),
    _t(5, "Два мастера красят забор за 6 часов. Сколько часов нужно одному мастеру (вдвое медленнее паре)?", "12", difficulty="hard", topic="Работа", section="algebra"),

    # 6 — стереометрия
    _t(6, "Прямоугольный параллелепипед имеет измерения 3, 4 и 5. Найдите объём.", "60", difficulty="easy", topic="Объём параллелепипеда", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(6, "Прямоугольный параллелепипед имеет измерения 3, 4 и 5. Найдите площадь поверхности.", "94", difficulty="medium", topic="Площадь поверхности", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(6, "Ребро куба равно 4. Найдите объём куба.", "64", difficulty="easy", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(6, "Прямоугольный параллелепипед 2×3×6. Найдите длину пространственной диагонали.", "7", difficulty="hard", topic="Диагональ", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(6, "Площадь основания прямой призмы равна 12, высота равна 5. Найдите объём призмы.", "60", difficulty="medium", topic="Призма", section="stereometry"),
    _t(6, "Ребро куба равно 6. Найдите площадь полной поверхности.", "216", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(6, "Цилиндр: радиус 3, высота 4. Найдите объём, делённый на π.", "36", difficulty="hard", topic="Цилиндр", section="stereometry"),

    # 7 — функции / графики
    _t(7, "Найдите значение функции f(x) = 2x − 5 при x = 4.", "3", difficulty="easy", topic="Линейная функция", section="functions", needs_figure=1, figure_kind="graph_linear"),
    _t(7, "Найдите значение функции f(x) = x² − 3x при x = 5.", "10", difficulty="medium", topic="Квадратичная функция", section="functions", needs_figure=1, figure_kind="graph_parabola"),
    _t(7, "Найдите нуль функции f(x) = 3x − 12.", "4", difficulty="easy", topic="Нуль функции", section="functions"),
    _t(7, "Найдите наименьшее значение функции f(x) = x² − 4x + 7 на множестве всех действительных x.", "3", difficulty="hard", topic="Экстремум", section="functions", needs_figure=1, figure_kind="graph_parabola"),
    _t(7, "Дана функция y = k/x. При x = 2 значение y равно 3. Найдите k.", "6", difficulty="medium", topic="Гипербола", section="functions", needs_figure=1, figure_kind="graph_hyperbola"),
    _t(7, "Найдите f(−2) для f(x) = x² − x.", "6", difficulty="easy", topic="Квадратичная функция", section="functions"),
    _t(7, "Прямая y = 2x + b проходит через точку (1; 5). Найдите b.", "3", difficulty="medium", topic="Линейная функция", section="functions", needs_figure=1, figure_kind="graph_linear"),

    # 8 — производная
    _t(8, "Найдите производную функции f(x) = 5x − 2. В ответе укажите значение f'(x).", "5", difficulty="easy", topic="Производная", section="analysis"),
    _t(8, "Найдите производную функции f(x) = x². В ответе укажите f'(3).", "6", difficulty="medium", topic="Производная в точке", section="analysis"),
    _t(8, "Найдите производную функции f(x) = 3x² − 4x + 1. В ответе укажите f'(1).", "2", difficulty="medium", topic="Производная многочлена", section="analysis"),
    _t(8, "Касательная к графику функции y = x² в точке x₀ = 1 имеет угловой коэффициент, равный…", "2", difficulty="hard", topic="Касательная", section="analysis", needs_figure=1, figure_kind="graph_parabola"),
    _t(8, "Найдите f'(x) для f(x) = 7. В ответе укажите значение производной.", "0", difficulty="easy", topic="Производная константы", section="analysis"),
    _t(8, "Найдите f'(2) для f(x) = x³.", "12", difficulty="hard", topic="Производная степени", section="analysis"),
    _t(8, "Найдите f'(0) для f(x) = e^x. В ответе укажите значение.", "1", difficulty="hard", topic="Производная экспоненты", section="analysis"),

    # 9 — прикладные / числа
    _t(9, "Найдите НОД чисел 24 и 18.", "6", difficulty="easy", topic="НОД", section="algebra"),
    _t(9, "Найдите НОК чисел 6 и 8.", "24", difficulty="medium", topic="НОК", section="algebra"),
    _t(9, "Сколько процентов составляет число 15 от числа 60?", "25", difficulty="easy", topic="Проценты", section="algebra"),
    _t(9, "Среднее арифметическое чисел 4, 8 и 12 равно…", "8", difficulty="medium", topic="Среднее", section="algebra"),
    _t(9, "Найдите сумму первых пяти членов арифметической прогрессии 2, 5, 8, …", "40", difficulty="hard", topic="Прогрессии", section="algebra"),
    _t(9, "Найдите 5-й член геометрической прогрессии 2, 6, 18, …", "162", difficulty="hard", topic="Прогрессии", section="algebra"),
    _t(9, "Сколько делителей имеет число 12?", "6", difficulty="medium", topic="Делители", section="algebra"),

    # 10 — планиметрия сложнее
    _t(10, "В равнобедренном треугольнике основание равно 10, боковая сторона равна 13. Найдите площадь, если высота к основанию равна 12.", "60", difficulty="medium", topic="Равнобедренный треугольник", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(10, "Стороны прямоугольника 9 и 12. Найдите длину диагонали.", "15", difficulty="easy", topic="Диагональ прямоугольника", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(10, "В прямоугольном треугольнике гипотенуза равна 10, один катет равен 6. Найдите второй катет.", "8", difficulty="medium", topic="Пифагор", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(10, "Площадь квадрата равна 49. Найдите длину его стороны.", "7", difficulty="easy", topic="Квадрат", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(10, "Окружность вписана в квадрат со стороной 6. Найдите диаметр окружности.", "6", difficulty="hard", topic="Вписанная окружность", section="planimetry", needs_figure=1, figure_kind="circle"),
    _t(10, "В треугольнике стороны 5, 12, 13. Найдите площадь.", "30", difficulty="medium", topic="Площадь треугольника", section="planimetry", needs_figure=1, figure_kind="triangle"),
    _t(10, "Хорда длиной 8 удалена от центра на 3. Найдите радиус окружности.", "5", difficulty="hard", topic="Хорда", section="planimetry", needs_figure=1, figure_kind="circle"),

    # 11 — стереометрия / сечения
    _t(11, "Объём куба равен 27. Найдите длину ребра куба.", "3", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Площадь полной поверхности куба равна 54. Найдите длину ребра.", "3", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Прямоугольный параллелепипед 3×4×5. Найдите площадь грани 3×4.", "12", difficulty="easy", topic="Грань", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Высота цилиндра 5, радиус основания 2. Найдите объём, делённый на π.", "20", difficulty="hard", topic="Цилиндр", section="stereometry"),
    _t(11, "Площадь боковой поверхности куба с ребром 5 равна… (только боковая, без оснований).", "100", difficulty="medium", topic="Куб", section="stereometry", needs_figure=1, figure_kind="box3d"),
    _t(11, "Объём шара равен 36π. Найдите радиус шара.", "3", difficulty="hard", topic="Шар", section="stereometry"),
    _t(11, "Пирамида: площадь основания 20, высота 6. Найдите объём.", "40", difficulty="medium", topic="Пирамида", section="stereometry"),

    # 12 — краткий / переход к part2
    _t(12, "Решите уравнение x² − 4x − 5 = 0. В ответе укажите сумму корней.", "4", part=1, difficulty="medium", topic="Квадратное уравнение", section="algebra"),
    _t(12, "Найдите произведение корней уравнения x² − 7x + 10 = 0.", "10", part=1, difficulty="medium", topic="Квадратное уравнение", section="algebra"),
    _t(12, "Решите неравенство x² − 5x + 6 < 0. В ответе укажите длину промежутка решения.", "1", part=1, difficulty="hard", topic="Неравенства", section="algebra", needs_figure=1, figure_kind="numberline"),
    _t(12, "Найдите область определения функции y = √(x − 3). В ответе укажите наименьшее целое число из области определения.", "3", part=1, difficulty="hard", topic="Область определения", section="functions", needs_figure=1, figure_kind="numberline"),
    _t(12, "Исследуйте функцию f(x) = x² − 6x + 5: найдите координату x вершины параболы.", "3", part=1, difficulty="medium", topic="Парабола", section="functions", needs_figure=1, figure_kind="graph_parabola"),
    _t(12, "Решите систему: x + y = 5 и x − y = 1. В ответе укажите произведение x·y.", "6", part=1, difficulty="easy", topic="Системы", section="algebra"),

    # 13–19 — часть 2 (развёрнутый ответ, короткий ключ для учителя)
    _t(13, "Решите уравнение x² − 4x − 5 = 0. В ответе укажите сумму корней.", "4", part=2, difficulty="medium", topic="Уравнение", section="algebra", max_score=2),
    _t(13, "Решите уравнение 2x² − 5x − 3 = 0. В ответе укажите больший корень.", "3", part=2, difficulty="medium", topic="Уравнение", section="algebra", max_score=2),
    _t(13, "Решите уравнение |x − 2| = 5. В ответе укажите сумму решений.", "4", part=2, difficulty="hard", topic="Модуль", section="algebra", max_score=2),
    _t(13, "Решите уравнение log₂(x − 1) = 3.", "9", part=2, difficulty="hard", topic="Логарифмы", section="algebra", max_score=2),

    _t(14, "Решите неравенство x² − 5x + 6 ≤ 0. В ответе укажите длину промежутка решения.", "1", part=2, difficulty="medium", topic="Неравенства", section="algebra", max_score=2, needs_figure=1, figure_kind="numberline"),
    _t(14, "Решите неравенство (x − 1)(x − 4) > 0. В ответе укажите наименьшее целое число, не входящее в решение и большее 0.", "2", part=2, difficulty="hard", topic="Неравенства", section="algebra", max_score=2),
    _t(14, "Решите неравенство |x| < 3. В ответе укажите длину промежутка решения.", "6", part=2, difficulty="easy", topic="Модуль", section="algebra", max_score=2, needs_figure=1, figure_kind="numberline"),
    _t(14, "Решите неравенство 2x − 7 ≥ 3. В ответе укажите наименьшее целое решение.", "5", part=2, difficulty="easy", topic="Неравенства", section="algebra", max_score=2),

    _t(15, "В треугольнике ABC угол C = 90°, AC = 6, BC = 8. Найдите AB.", "10", part=2, difficulty="easy", topic="Планиметрия", section="planimetry", max_score=2, needs_figure=1, figure_kind="triangle"),
    _t(15, "В треугольнике стороны 7, 24, 25. Найдите площадь.", "84", part=2, difficulty="medium", topic="Планиметрия", section="planimetry", max_score=2, needs_figure=1, figure_kind="triangle"),
    _t(15, "Около квадрата со стороной 4 описана окружность. Найдите квадрат длины её диаметра.", "32", part=2, difficulty="hard", topic="Планиметрия", section="planimetry", max_score=2, needs_figure=1, figure_kind="circle"),
    _t(15, "В прямоугольнике диагональ 13, одна сторона 5. Найдите площадь.", "60", part=2, difficulty="medium", topic="Планиметрия", section="planimetry", max_score=2, needs_figure=1, figure_kind="rect"),

    _t(16, "Прямоугольный параллелепипед 2×3×6. Найдите площадь полной поверхности.", "72", part=2, difficulty="medium", topic="Стереометрия", section="stereometry", max_score=2, needs_figure=1, figure_kind="box3d"),
    _t(16, "Куб с ребром 5. Найдите квадрат длины пространственной диагонали.", "75", part=2, difficulty="hard", topic="Стереометрия", section="stereometry", max_score=2, needs_figure=1, figure_kind="box3d"),
    _t(16, "Цилиндр: радиус 4, высота 3. Найдите площадь боковой поверхности, делённую на π.", "24", part=2, difficulty="medium", topic="Цилиндр", section="stereometry", max_score=2),
    _t(16, "Пирамида: основание — квадрат со стороной 6, высота 4. Найдите объём.", "48", part=2, difficulty="easy", topic="Пирамида", section="stereometry", max_score=2),

    _t(17, "Найдите наименьшее значение функции f(x) = x² − 6x + 10.", "1", part=2, difficulty="medium", topic="Параметр / экстремум", section="analysis", max_score=2, needs_figure=1, figure_kind="graph_parabola"),
    _t(17, "При каких a уравнение x² − ax + 1 = 0 имеет два различных корня? В ответе укажите наименьшее целое a > 2.", "3", part=2, difficulty="hard", topic="Параметр", section="algebra", max_score=2),
    _t(17, "Найдите точку максимума функции f(x) = −x² + 4x − 1. Укажите x.", "2", part=2, difficulty="medium", topic="Экстремум", section="analysis", max_score=2),
    _t(17, "Найдите f'(x) в точке x = 1 для f(x) = x³ − 3x. Укажите значение.", "0", part=2, difficulty="easy", topic="Производная", section="analysis", max_score=2),

    _t(18, "Решите систему: x + 2y = 8 и 3x − y = 3. В ответе укажите x.", "2", part=2, difficulty="medium", topic="Системы", section="algebra", max_score=2),
    _t(18, "Решите систему: x² + y² = 25 и y = 3. В ответе укажите наибольший x.", "4", part=2, difficulty="hard", topic="Системы", section="algebra", max_score=2),
    _t(18, "Найдите все пары (x; y): x − y = 1 и xy = 12. В ответе укажите сумму x + y для пары с большим x.", "7", part=2, difficulty="hard", topic="Системы", section="algebra", max_score=2),
    _t(18, "Решите систему: 2x + y = 10 и x − y = 2. В ответе укажите y.", "2", part=2, difficulty="medium", topic="Системы", section="algebra", max_score=2),

    _t(19, "Экономическая задача: вклад 100000 руб. под 10% годовых. Найдите сумму через 1 год.", "110000", part=2, difficulty="easy", topic="Экономика", section="algebra", max_score=2),
    _t(19, "Кредит 200000 руб. под 5% годовых. Найдите сумму долга через год без погашений.", "210000", part=2, difficulty="easy", topic="Экономика", section="algebra", max_score=2),
    _t(19, "Товар подорожал на 20%, затем подешевел на 20%. Исходная цена 1000. Найдите итоговую цену.", "960", part=2, difficulty="medium", topic="Проценты", section="algebra", max_score=2),
    _t(19, "Зарплата 40000. Повысили на 15%. Найдите новую зарплату.", "46000", part=2, difficulty="easy", topic="Проценты", section="algebra", max_score=2),
]
