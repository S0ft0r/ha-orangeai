"""Кнопки действий (Button) интеграции Лоджия."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODE_BLINDS, MODE_WATERING
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Создание кнопок выполнения действий для подустройств «Привода» и «Полив»."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []
    if manager.has_mode(MODE_BLINDS):
        entities.append(LoggiaExecuteActionButton(manager))
    if manager.has_mode(MODE_WATERING):
        entities.append(LoggiaWateringExecuteButton(manager))
    if entities:
        async_add_entities(entities)


class LoggiaExecuteActionButton(ButtonEntity):
    """Кнопка выполнения выбранного ручного действия для активных приводов."""

    _attr_has_entity_name = True
    _attr_translation_key = "execute_action"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "execute_action"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"
        manager.config_entities[self._key] = self

    async def async_press(self) -> None:
        """Выполнить выбранное в списке действие и сбросить выбор на 'Остановить'."""
        await self.manager.async_execute_manual_action()


class LoggiaWateringExecuteButton(ButtonEntity):
    """Кнопка дозированного ручного запуска (30 сек) и экстренной остановки полива."""

    _attr_has_entity_name = True
    _attr_translation_key = "watering_execute"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "watering_execute"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"
        manager.config_entities[self._key] = self

    @property
    def icon(self) -> str:
        """Иконка как у кнопки выполнения в «Приводах» (с переключением на стоп во время полива)."""
        if self.manager.is_watering_active:
            return "mdi:stop-circle-outline"
        return "mdi:play-circle-outline"

    async def async_press(self) -> None:
        """Запустить дозированный полив (30 сек) выбранного направления или остановить активный полив."""
        await self.manager.async_toggle_manual_watering()
