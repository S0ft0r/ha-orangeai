"""Константы интеграции Домашняя оранжерея (Orry)."""

DOMAIN = "orry"


def pos_to_blind_step(pos: int | float | None, default: int = 100) -> int:
    """Округлить процент открытия шторы (0..100) до ближайшего шага иконки (0, 25, 50, 75, 100)."""
    if pos is None:
        return default
    try:
        val = max(0.0, min(100.0, float(pos)))
    except (TypeError, ValueError):
        return default
    return int(round(val / 25.0)) * 25

# ── Модули и режимы работы ──
MODE_BLINDS = "blinds"
MODE_SUN_PROTECT = "sun_protect"
MODE_PHYTOLAMP = "phytolamp"
MODE_WATERING = "watering"
MODE_SLIDER = "slider"
MODE_YANDEX = "yandex"
MODE_LOGGING = "logging"

# ── Режимы работы устройства (слайдера) ──
SLIDER_MODE_FULL = "full"
SLIDER_MODE_STEP = "step"
SLIDER_MODE_PROPORTIONAL = "proportional"

# ── Значения по умолчанию ──
DEFAULT_SUN_SENSOR = "sun.sun"
DEFAULT_USE_FORECAST = False
DEFAULT_USE_ILLUMINANCE = False

DEFAULT_OPEN_AT_SUNRISE = True
DEFAULT_OPEN_TIME_WORKDAY = "06:10:00"
DEFAULT_OPEN_TIME_WEEKEND = "07:10:00"

DEFAULT_CLOSE_AT_SUNSET = True
DEFAULT_CLOSE_TIME = "21:00:00"

# ── Рабочий цикл и государственные праздники ──
DEFAULT_SPLIT_WEEKEND_SCHEDULE = True
DEFAULT_WORK_DAYS = 5
DEFAULT_OFF_DAYS = 2
DEFAULT_CYCLE_START_DATE = "2026-01-05"  # Понедельник
DEFAULT_USE_HOLIDAYS = True

# Встроенный офлайн-резерв производственного календаря РФ (2026–2027 + ст. 112 ТК РФ)
RU_FIXED_HOLIDAYS_MD: set[tuple[int, int]] = {
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (2, 23),
    (3, 8),
    (5, 1),
    (5, 9),
    (6, 12),
    (11, 4),
}

RU_HOLIDAYS_FALLBACK: set[str] = {
    # 2026 (Постановление Правительства РФ от 24.09.2025 № 1466)
    "2026-01-01",
    "2026-01-02",
    "2026-01-03",
    "2026-01-04",
    "2026-01-05",
    "2026-01-06",
    "2026-01-07",
    "2026-01-08",
    "2026-01-09",
    "2026-02-23",
    "2026-03-08",
    "2026-03-09",
    "2026-05-01",
    "2026-05-09",
    "2026-05-11",
    "2026-06-12",
    "2026-11-04",
    "2026-12-31",
    # 2027 (Постановление Правительства РФ от 17.09.2026 № 1187)
    "2027-01-01",
    "2027-01-02",
    "2027-01-03",
    "2027-01-04",
    "2027-01-05",
    "2027-01-06",
    "2027-01-07",
    "2027-01-08",
    "2027-02-22",
    "2027-02-23",
    "2027-03-08",
    "2027-05-01",
    "2027-05-03",
    "2027-05-09",
    "2027-05-10",
    "2027-06-12",
    "2027-06-14",
    "2027-11-04",
    "2027-11-05",
    "2027-12-31",
}

RU_WORKING_WEEKENDS_FALLBACK: set[str] = {
    "2027-02-20",
}

DEFAULT_SUN_AZIMUTH = 0
DEFAULT_SUN_ELEVATION = 0
DEFAULT_UP_LIMIT = 100
DEFAULT_DOWN_LIMIT = 0
DEFAULT_MIN_ILLUMINANCE = 0
DEFAULT_MAX_ILLUMINANCE = 0
DEFAULT_ILLUMINANCE_DELAY = "00:02:00"
DEFAULT_REPEAT = 2
DEFAULT_REPEAT_DELAY = 1
DEFAULT_MOVEMENT_TIME = 30
DEFAULT_FORECASTS = ["sunny", "partlycloudy"]

# Голосовое управление (Яндекс / Assist / Универсальное)
VOICE_ENGINE_YANDEX = "yandex"
VOICE_ENGINE_ASSIST = "assist"
VOICE_ENGINE_CUSTOM = "custom"
DEFAULT_VOICE_ENGINE = VOICE_ENGINE_YANDEX
DEFAULT_VOICE_EVENT = "yandex_intent"

DEFAULT_YANDEX_VOLUME = 30
# DEFAULT_YANDEX_INTENT_OPEN = "Открой шторы; Подними шторы; Открыть шторы"
# DEFAULT_YANDEX_INTENT_CLOSE = "Закрой шторы; Опусти шторы; Закрыть шторы"
# DEFAULT_YANDEX_INTENT_POSITION = "Положение штор"
# DEFAULT_YANDEX_INTENT_STATUS = "Состояние штор; Что со шторами"
DEFAULT_YANDEX_INTENT_OPEN = ""
DEFAULT_YANDEX_INTENT_CLOSE = ""
DEFAULT_YANDEX_INTENT_POSITION = ""
DEFAULT_YANDEX_INTENT_STATUS = ""

# Слайдер / Выключатель
DEFAULT_BASIC_TOPIC = "zigbee2mqtt/+/action"
DEFAULT_PAYLOAD_UP = "slider_up"
DEFAULT_PAYLOAD_DOWN = "slider_down"
DEFAULT_PAYLOAD_STOP = "single_wireless"
DEFAULT_SLIDER_MODE = SLIDER_MODE_PROPORTIONAL
DEFAULT_SLIDER_STEP = 10
DEFAULT_SLIDER_FAST_SPEED = 45
DEFAULT_SLIDER_FAST_TIME_MS = 350

# Подсветка растений (Фитолампа)
DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS = True
DEFAULT_PHYTOLAMP_USE_SUN = False
DEFAULT_PHYTOLAMP_USE_FORECAST = False
DEFAULT_PHYTOLAMP_USE_ILLUMINANCE = False
DEFAULT_PHYTOLAMP_ON_WORKDAY = "06:10:00"
DEFAULT_PHYTOLAMP_ON_WEEKEND = "07:10:00"
DEFAULT_PHYTOLAMP_OFF_TIME = "21:00:00"

# Полив растений (Оросительная система)
WATERING_MODE_OFF = "off"
WATERING_MODE_DAILY = "daily"
WATERING_MODE_EVERY_OTHER_DAY = "every_other_day"
WATERING_MODE_EVERY_TWO_DAYS = "every_two_days"
WATERING_MODE_BY_SENSOR = "by_sensor"

WATERING_MODES = [
    WATERING_MODE_OFF,
    WATERING_MODE_DAILY,
    WATERING_MODE_EVERY_OTHER_DAY,
    WATERING_MODE_EVERY_TWO_DAYS,
    WATERING_MODE_BY_SENSOR,
]

DEFAULT_WATERING_ENABLED = True
DEFAULT_WATERING_SKIP_NEXT = False
DEFAULT_WATERING_USE_MOISTURE = False
DEFAULT_WATERING_MORNING_TIME = "08:00:00"
DEFAULT_WATERING_EVENING_TIME = "20:00:00"
DEFAULT_WATERING_SOIL_THRESHOLD = 50
DEFAULT_WATERING_MORNING_MODE = WATERING_MODE_DAILY
DEFAULT_WATERING_MORNING_DURATION = 30
DEFAULT_WATERING_EVENING_MODE = WATERING_MODE_OFF
DEFAULT_WATERING_EVENING_DURATION = 30
DEFAULT_WATERING_MANUAL_DURATION = 30
DEFAULT_WATERING_SAFETY_MARGIN = 10

# Контроль разряда батарей приводов, клапанов и датчиков
DEFAULT_LOW_BATTERY_THRESHOLD = 15
DEFAULT_LOW_BATTERY_RECOVERY = 20

WATERING_ZONE_ALL = "__all__"
WATERING_PREFIX_ALL = "↺\u00a0\u00a0"
WATERING_PREFIX_ACTIVE = "✓\ufe0e\u00a0\u00a0"
WATERING_PREFIX_OFF = "✕\ufe0e\u00a0\u00a0"

# Ручные действия и префиксы для подустройства «Привода»
ACTION_STOP = "stop"
ACTION_OPEN = "open"
ACTION_CLOSE = "close"
ACTION_POS_10 = "pos_10"
ACTION_POS_20 = "pos_20"
ACTION_POS_30 = "pos_30"
ACTION_POS_40 = "pos_40"
ACTION_POS_50 = "pos_50"
ACTION_POS_60 = "pos_60"
ACTION_POS_70 = "pos_70"
ACTION_POS_80 = "pos_80"
ACTION_POS_90 = "pos_90"

MANUAL_POSITION_ACTIONS: dict[str, int] = {
    ACTION_POS_10: 10,
    ACTION_POS_20: 20,
    ACTION_POS_30: 30,
    ACTION_POS_40: 40,
    ACTION_POS_50: 50,
    ACTION_POS_60: 60,
    ACTION_POS_70: 70,
    ACTION_POS_80: 80,
    ACTION_POS_90: 90,
}

MANUAL_ACTIONS = [
    ACTION_STOP,
    ACTION_OPEN,
    ACTION_CLOSE,
    *MANUAL_POSITION_ACTIONS.keys(),
]

DRIVE_PREFIX_ACTIVE = "✓\ufe0e\u00a0\u00a0"
DRIVE_PREFIX_EXCLUDED = "✕\ufe0e\u00a0\u00a0"
DRIVE_PREFIX_ENABLE_ALL = "↺\u00a0\u00a0"

ENTITY_GROUP: dict[str, str] = {
    # привода (управление, настройки и диагностика штор)
    "blinds": "drives",
    "sun_blinds": "drives",
    "up_limit": "drives",
    "down_limit": "drives",
    "repeat_for": "drives",
    "delay_for_repeat": "drives",
    "movement_time": "drives",
    "excluded_blinds": "drives",
    "manual_action": "drives",
    "execute_action": "drives",
    "open_count": "drives",
    "closed_count": "drives",
    "error_count": "drives",
    "battery": "drives",
    # расписание
    "open_at_sunrise": "schedule",
    "close_at_sunset": "schedule",
    "up_time_workday": "schedule",
    "up_time_weekend": "schedule",
    "down_time": "schedule",
    "phytolamp_on_time_workday": "schedule",
    "phytolamp_on_time_weekend": "schedule",
    "phytolamp_off_time": "schedule",
    "watering_morning_time": "schedule",
    "watering_evening_time": "schedule",
    # солнце
    "sun_azimuth": "sun",
    "sun_elevation": "sun",
    # освещённость
    "min_illuminance": "illuminance",
    "max_illuminance": "illuminance",
    "illuminance_delay": "illuminance",
    # подсветка растений
    "phytolamp_sun_azimuth": "phytolamp",
    "phytolamp_sun_elevation": "phytolamp",
    "phytolamp_min_illuminance": "phytolamp",
    "phytolamp_max_illuminance": "phytolamp",
    "phytolamp_illuminance_delay": "phytolamp",
    "phytolamp_on_count": "phytolamp",
    "phytolamp_off_count": "phytolamp",
    "phytolamp_error_count": "phytolamp",
    # полив растений
    "watering_enabled": "watering",
    "watering_skip_next": "watering",
    "watering_soil_threshold": "watering",
    "watering_zone": "watering",
    "watering_execute": "watering",
    "watering_morning_zones": "watering",
    "watering_evening_zones": "watering",
    "watering_morning_mode": "watering",
    "watering_morning_duration": "watering",
    "watering_evening_mode": "watering",
    "watering_evening_duration": "watering",
    "watering_active_count": "watering",
    "watering_error_count": "watering",
    "watering_battery": "watering",
    # управление (пульт / слайдер)
    "slider_step": "control",
    "slider_fast_speed": "control",
    "slider_mode": "control",
    # "yandex_volume": "control",
}
