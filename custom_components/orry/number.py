"""Настройки (числовые ползунки) Лоджии."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import PERCENTAGE, UnitOfTime, DEGREE, LIGHT_LUX, UnitOfSpeed 

from .const import (
    DOMAIN,
    MODE_BLINDS,
    MODE_WATERING,
    DEFAULT_UP_LIMIT, DEFAULT_DOWN_LIMIT,
    DEFAULT_SUN_AZIMUTH, DEFAULT_SUN_ELEVATION,
    DEFAULT_MIN_ILLUMINANCE, DEFAULT_MAX_ILLUMINANCE,
    DEFAULT_REPEAT, DEFAULT_REPEAT_DELAY, DEFAULT_MOVEMENT_TIME,
    DEFAULT_SLIDER_STEP, DEFAULT_SLIDER_FAST_SPEED, DEFAULT_YANDEX_VOLUME,
    DEFAULT_WATERING_SOIL_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
)
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Создание числовых настроек в зависимости от режимов."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]

    configs = [
        # ── ОСНОВНОЕ УСТРОЙСТВО (Общий порог низкого заряда батарей) ──
        (
            "low_battery_threshold",
            5,
            50,
            1,
            PERCENTAGE,
            None,
            DEFAULT_LOW_BATTERY_THRESHOLD,
        ),
    ]

    # ── ПРИВОДА (На подустройстве «Привода» при включённом модуле штор) ──
    if manager.has_mode(MODE_BLINDS):
        configs.extend([
            ("up_limit", 0, 100, 1, PERCENTAGE, "orry:blind-limit-up", DEFAULT_UP_LIMIT),
            ("down_limit", 0, 100, 1, PERCENTAGE, "orry:blind-limit-down", DEFAULT_DOWN_LIMIT),
            ("repeat_for", 1, 5, 1, None, "orry:blind-repeat", DEFAULT_REPEAT),
            ("delay_for_repeat", 1, 10, 1, UnitOfTime.SECONDS, "orry:repeat-pause", DEFAULT_REPEAT_DELAY),
            ("movement_time", 5, 120, 1, UnitOfTime.SECONDS, "orry:blind-speed", DEFAULT_MOVEMENT_TIME),
        ])

    # ── СОЛНЦЕ И ОСВЕЩЁННОСТЬ (Для защиты от солнца) ──
    if manager.needs_sun_subdevice:
        configs.extend([
            ("sun_azimuth", 0, 359, 1, DEGREE, None, DEFAULT_SUN_AZIMUTH),
            ("sun_elevation", 0, 90, 1, DEGREE, None, DEFAULT_SUN_ELEVATION),
        ])
    if manager.needs_illuminance_subdevice:
        configs.extend([
            ("min_illuminance", 0, 100000, 100, LIGHT_LUX, None, DEFAULT_MIN_ILLUMINANCE),
            ("max_illuminance", 0, 100000, 100, LIGHT_LUX, None, DEFAULT_MAX_ILLUMINANCE),
        ])

    # ── ПОДСВЕТКА РАСТЕНИЙ (Собственные настройки на подустройстве «Подсветка») ──
    if manager.needs_phytolamp_subdevice:
        if bool(manager.get_setting("phytolamp_use_sun", False)):
            configs.extend([
                ("phytolamp_sun_azimuth", 0, 359, 1, DEGREE, None, DEFAULT_SUN_AZIMUTH),
                ("phytolamp_sun_elevation", 0, 90, 1, DEGREE, None, DEFAULT_SUN_ELEVATION),
            ])
        if bool(manager.get_setting("phytolamp_use_illuminance", False)):
            configs.extend([
                ("phytolamp_min_illuminance", 0, 100000, 100, LIGHT_LUX, None, DEFAULT_MIN_ILLUMINANCE),
                ("phytolamp_max_illuminance", 0, 100000, 100, LIGHT_LUX, None, DEFAULT_MAX_ILLUMINANCE),
            ])

    # ── ПОЛИВ РАСТЕНИЙ (Подустройство «Полив») ──
    entities: list[NumberEntity] = []
    if manager.has_mode(MODE_WATERING):
        if bool(manager.get_setting("watering_use_moisture", False)):
            configs.append(
                ("watering_soil_threshold", 1, 100, 1, PERCENTAGE, "orry:watering-percent", DEFAULT_WATERING_SOIL_THRESHOLD)
            )
        entities.extend([
            LoggiaWateringDurationNumber(manager, "watering_morning_duration", "m_duration", "orry:sunrise-timer"),
            LoggiaWateringDurationNumber(manager, "watering_evening_duration", "e_duration", "orry:sunset-timer"),
        ])

    # ── СЛАЙДЕР ──
    if manager.has_mode(MODE_BLINDS) and manager.has_mode("slider"):
        configs.extend([
            ("slider_step", 1, 50, 1, PERCENTAGE, None, DEFAULT_SLIDER_STEP),
            ("slider_fast_speed", 10, 300, 5, UnitOfSpeed.MILLIMETERS_PER_SECOND, None, DEFAULT_SLIDER_FAST_SPEED),
        ])

    # ── ЯНДЕКС (Громкость временно отключена по решению архитектуры) ──
    # if manager.has_mode("yandex"):
    #     configs.append(
    #         ("yandex_volume", 10, 100, 10, PERCENTAGE, None, DEFAULT_YANDEX_VOLUME)
    #     )

    entities.extend([LoggiaConfigNumber(manager, *c) for c in configs])
    async_add_entities(entities)

class LoggiaConfigNumber(NumberEntity, RestoreEntity):
    """Класс для числового ползунка настройки."""

    _attr_entity_category = EntityCategory.CONFIG  # Помещает в блок "Настройки" карточки устройства
    _attr_has_entity_name = True

    def __init__(self, manager: LoggiaManager, key, min_v, max_v, step, unit, icon, default):
        self.manager = manager
        # self._attr_device_info = {
        #     "identifiers": {(DOMAIN, manager.entry.entry_id)},
        #     "name": manager.entry.title,
        #     "manufacturer": "Softor",
        #     "model": "Smart loggia",
        # }
        self._attr_device_info = manager.device_info_for(key)

        self._key = key
        
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step
        if unit is not None:
            self._attr_native_unit_of_measurement = unit
        if icon is not None:
            self._attr_icon = icon        
        # self._attr_native_unit_of_measurement = unit
        # self._attr_icon = icon
        self._attr_mode = NumberMode.BOX #if step == 1 and max_v <= 10 else NumberMode.SLIDER

        self._default = default
        
        # Регистрируем себя в менеджере!
        manager.config_entities[key] = self

    async def async_added_to_hass(self):
        """Восстанавливаем состояние после перезагрузки HA."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        
        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                self._attr_native_value = self._default
        else:
            # Если это первый запуск, пытаемся взять из старых настроек OptionsFlow или ставим дефолт
            self._attr_native_value = float(self.manager.get_setting(self._key, self._default))

        self.async_write_ha_state()
        if self._key in ("up_limit", "down_limit"):
            self._refresh_limit_dependents()
        if self._key == "low_battery_threshold":
            self.manager.recheck_battery_thresholds()

    async def async_set_native_value(self, value: float) -> None:
        """Пользователь передвинул ползунок в интерфейсе."""
        self._attr_native_value = value
        self.async_write_ha_state()
        if self._key in ("up_limit", "down_limit"):
            self._refresh_limit_dependents()
        if self._key == "low_battery_threshold":
            self.manager.recheck_battery_thresholds()
        if self._key == "watering_soil_threshold":
            self.manager._refresh_watering_zone_dependents()
        if self._key in ("sun_azimuth", "sun_elevation", "min_illuminance", "max_illuminance"):
            self.hass.async_create_task(self.manager._evaluate_sun_protection())
        if self._key in (
            "phytolamp_sun_azimuth",
            "phytolamp_sun_elevation",
            "phytolamp_min_illuminance",
            "phytolamp_max_illuminance",
        ):
            self.hass.async_create_task(self.manager._evaluate_phytolamp_custom())

    def _refresh_limit_dependents(self) -> None:
        """Обновить селектор ручных действий и все сенсоры, зависящие от верхнего/нижнего лимита."""
        action_ent = self.manager.config_entities.get("manual_action")
        if action_ent and hasattr(action_ent, "async_refresh_options"):
            action_ent.async_refresh_options()
        for sensor_key in ("open_count", "closed_count"):
            sensor_ent = self.manager.config_entities.get(sensor_key)
            if sensor_ent and hasattr(sensor_ent, "async_refresh_count"):
                sensor_ent.async_refresh_count()
        status_ent = self.manager.config_entities.get("status")
        if status_ent and hasattr(status_ent, "async_refresh_status"):
            status_ent.async_refresh_status()


class LoggiaWateringDurationNumber(NumberEntity):
    """Числовая настройка длительности полива для выбранного направления (утро / вечер)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 600
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_mode = NumberMode.BOX

    def __init__(self, manager: LoggiaManager, key: str, field_name: str, icon: str | None = None) -> None:
        self.manager = manager
        self._key = key
        self._field_name = field_name
        self._attr_device_info = manager.device_info_for(key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
        if icon is not None:
            self._attr_icon = icon
        manager.config_entities[key] = self

    @property
    def native_value(self) -> float:
        """Длительность работы текущего выбранного направления полива."""
        cfg = self.manager.get_watering_zone_config()
        return float(cfg.get(self._field_name, 30))

    async def async_set_native_value(self, value: float) -> None:
        """Сохранить новую длительность работы для выбранного направления (или всех направлений)."""
        self.manager.update_watering_zone_setting(self._field_name, int(value))

    @callback
    def async_refresh_from_manager(self) -> None:
        """Обновить отображаемое значение при переключении направления."""
        if self.hass is not None:
            self.async_write_ha_state()

