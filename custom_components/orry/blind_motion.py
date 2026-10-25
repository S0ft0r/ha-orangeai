"""Чистые функции для безопасных команд положения штор."""


def normalize_position_limits(down_limit: int, up_limit: int) -> tuple[int, int]:
    """Вернуть упорядоченные пределы положения в диапазоне 0–100%."""
    down = max(0, min(100, int(down_limit)))
    up = max(0, min(100, int(up_limit)))
    return min(down, up), max(down, up)


def clamp_cover_position(position: int, lower_limit: int, upper_limit: int) -> int:
    """Ограничить целевое положение допустимыми пределами штор."""
    low, high = normalize_position_limits(lower_limit, upper_limit)
    return max(low, min(high, max(0, min(100, int(position)))))


def build_position_sequence(
    target: int,
    repeat_count: int,
    direction: str,
    lower_limit: int,
    upper_limit: int,
) -> list[int]:
    """Сформировать безопасные повторы; последний элемент всегда равен точной цели.

    Для движения вверх промежуточные команды подходят к цели снизу,
    для движения вниз — сверху. Каждая команда отдельно ограничивается
    настроенными пределами, поэтому диагностический шаг не выходит за них.
    """
    low, high = normalize_position_limits(lower_limit, upper_limit)
    exact_target = clamp_cover_position(target, low, high)
    count = max(1, int(repeat_count))
    movement = str(direction).lower()

    positions: list[int] = []
    for index in range(count):
        offset = count - index - 1
        if movement == "up":
            command = exact_target - offset
        elif movement == "down":
            command = exact_target + offset
        else:
            command = exact_target
        positions.append(clamp_cover_position(command, low, high))
    return positions


def diagnostic_position(
    target: int,
    offset: int,
    direction: str,
    lower_limit: int,
    upper_limit: int,
) -> int:
    """Вернуть безопасную позицию диагностического микрошага."""
    low, high = normalize_position_limits(lower_limit, upper_limit)
    exact_target = clamp_cover_position(target, low, high)
    distance = max(0, int(offset))
    movement = str(direction).lower()

    if movement == "up":
        command = exact_target - distance
    elif movement == "down":
        command = exact_target + distance
    else:
        command = exact_target
    return clamp_cover_position(command, low, high)
