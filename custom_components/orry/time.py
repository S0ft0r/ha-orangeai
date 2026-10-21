"""Настройки времени Лоджии."""

from datetime import time
from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    MODE_BLINDS,
    MODE_PHYTOLAMP,
    MODE_WATERING,
    DEFAULT_OPEN_TIME_WORKDAY, DEFAULT_OPEN_TIME_WEEKEND, DEFAULT_CLOSE_TIME,
    DEFAULT_ILLUMINANCE_DELAY,
    DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
    DEFAULT_PHYTOLAMP_ON_WORKDAY, DEFAULT_PHYTOLAMP_ON_WEEKEND, DEFAULT_PHYTOLAMP_OFF_TIME,
    DEFAULT_WATERING_MORNING_TIME, DEFAULT_WATERING_EVENING_TIME,
)
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]
    
    configs = []
    if manager.has_mode(MODE_BLINDS):
        configs.append(("up_time_workday", None, DEFAULT_OPEN_TIME_WORKDAY))
        if manager.split_weekend_schedule:
            configs.append(("up_time_weekend", None, DEFAULT_OPEN_TIME_WEEKEND))
        configs.append(("down_time", None, DEFAULT_CLOSE_TIME))

    # Если задействован датчик освещённости (в защите от солнца или подсветке)
    if manager.needs_illuminance_subdevice:
        configs.append(("illuminance_delay", None, DEFAULT_ILLUMINANCE_DELAY))

    # Если включен режим подсветки растений с собственными настройками (не основные настройки интеграции)
    if manager.needs_phytolamp_subdevice:
        configs.append(("phytolamp_on_time_workday", "orry:phytolamp-on-clock", DEFAULT_PHYTOLAMP_ON_WORKDAY))
        if manager.split_weekend_schedule:
            configs.append(("phytolamp_on_time_weekend", "orry:phytolamp-on-clock-weekend", DEFAULT_PHYTOLAMP_ON_WEEKEND))
        configs.append(("phytolamp_off_time", "orry:phytolamp-clock", DEFAULT_PHYTOLAMP_OFF_TIME))
        if bool(manager.get_setting("phytolamp_use_illuminance", False)):
            configs.append(("phytolamp_illuminance_delay", None, DEFAULT_ILLUMINANCE_DELAY))

    # Если включен режим полива растений
    if manager.has_mode(MODE_WATERING):
        configs.extend([
            ("watering_morning_time", "orry:watering-clock-morning", DEFAULT_WATERING_MORNING_TIME),
            ("watering_evening_time", "orry:watering-clock-evening", DEFAULT_WATERING_EVENING_TIME),
        ])

    async_add_entities([LoggiaConfigTime(manager, *c) for c in configs])


class LoggiaConfigTime(TimeEntity, RestoreEntity):
    """Класс для ввода времени."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, manager: LoggiaManager, key, icon, default):
        self.manager = manager
        self._attr_device_info = manager.device_info_for(key)

        self._key = key
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        if key == "up_time_workday" and not manager.split_weekend_schedule:
            self._attr_translation_key = "up_time_daily"
        elif key == "phytolamp_on_time_workday" and not manager.split_weekend_schedule:
            self._attr_translation_key = "phytolamp_on_time_daily"
        else:
            self._attr_translation_key = key
        if icon is not None:
            self._attr_icon = icon        
        self._default_str = default
        manager.config_entities[key] = self

    @property
    def icon(self) -> str | None:
        """Кастомная иконка времени открытия/закрытия штор (с лампочкой при привязке подсветки к основному расписанию)."""
        if self._key in ("up_time_workday", "up_time_weekend", "down_time"):
            light_linked = self.manager.has_mode(MODE_PHYTOLAMP) and bool(
                self.manager.get_setting(
                    "phytolamp_use_main_settings",
                    DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                )
            )
            suffix = "-light" if light_linked else ""
            if self._key == "up_time_workday":
                return f"orry:blind-open-clock{suffix}"
            if self._key == "up_time_weekend":
                return f"orry:blind-open-clock-weekend{suffix}"
            return f"orry:blind-clock{suffix}"
        return getattr(self, "_attr_icon", None)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        
        # Пытаемся восстановить
        val_str = None
        if last_state and last_state.state not in ("unknown", "unavailable"):
            val_str = last_state.state
        else:
            # Иначе берем из первоначального WIZARD (ConfigFlow)
            val_str = self.manager.get_setting(self._key, self._default_str)
            
        try:
            parts = [int(x) for x in str(val_str).split(":")]
            self._attr_native_value = time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)
        except Exception:
            self._attr_native_value = time(0, 0)
            
        self.async_write_ha_state()
        self.manager.recalculate_schedule_flags()

    async def async_set_value(self, value: time) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
        self.manager.recalculate_schedule_flags()
