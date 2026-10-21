"""Переключатели настроек Лоджии."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    MODE_BLINDS,
    MODE_WATERING,
    DEFAULT_OPEN_AT_SUNRISE,
    DEFAULT_CLOSE_AT_SUNSET,
    DEFAULT_WATERING_ENABLED,
    DEFAULT_WATERING_SKIP_NEXT,
)
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Создание переключателей настроек."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]

    configs = []
    if manager.has_mode(MODE_BLINDS):
        configs.extend([
            ("open_at_sunrise", "orry:blind-sunrise", DEFAULT_OPEN_AT_SUNRISE),
            ("close_at_sunset", "orry:blind-sunset", DEFAULT_CLOSE_AT_SUNSET),
        ])

    if manager.has_mode(MODE_WATERING):
        configs.extend([
            ("watering_enabled", None, DEFAULT_WATERING_ENABLED),
            ("watering_skip_next", "orry:watering-pause", DEFAULT_WATERING_SKIP_NEXT),
        ])

    async_add_entities([LoggiaConfigSwitch(manager, *c) for c in configs])


class LoggiaConfigSwitch(SwitchEntity, RestoreEntity):
    """Переключатель настройки расписания."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(
        self, manager: LoggiaManager, key: str, icon: str | None, default: bool
    ) -> None:
        self.manager = manager
        self._attr_device_info = manager.device_info_for(key)
        self._key = key
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
        if icon is not None:
            self._attr_icon = icon
        self._default = default
        manager.config_entities[key] = self

    @property
    def icon(self) -> str | None:
        """Динамическая иконка для переключателя автополива."""
        if self._key == "watering_enabled":
            return "orry:watering" if self.is_on else "orry:watering-off"
        return getattr(self, "_attr_icon", None)

    async def async_added_to_hass(self) -> None:
        """Восстановление состояния после перезагрузки HA."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()

        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._attr_is_on = last_state.state == STATE_ON
        else:
            self._attr_is_on = bool(
                self.manager.get_setting(self._key, self._default)
            )

        self.async_write_ha_state()
        self.manager.recalculate_schedule_flags()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Включение переключателя."""
        self._attr_is_on = True
        self.async_write_ha_state()
        self.manager.recalculate_schedule_flags()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Выключение переключателя."""
        self._attr_is_on = False
        self.async_write_ha_state()
        self.manager.recalculate_schedule_flags()
