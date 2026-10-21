"""Обобщённые сущности штор (Cover) интеграции Лоджия на подустройстве «Привода»."""

from typing import Any

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, MODE_BLINDS, MODE_SUN_PROTECT, pos_to_blind_step
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Создание обобщённых сущностей штор на подустройстве «Привода»."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]

    if not manager.has_mode(MODE_BLINDS):
        return

    entities: list[CoverEntity] = [LoggiaGroupCover(manager, "blinds")]
    if manager.has_mode(MODE_SUN_PROTECT):
        entities.append(LoggiaGroupCover(manager, "sun_blinds"))

    async_add_entities(entities)


class LoggiaGroupCover(CoverEntity):
    """Обобщённая сущность управления группой штор (все активные или защита от солнца)."""

    _attr_has_entity_name = True
    _attr_device_class = CoverDeviceClass.SHADE
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, manager: LoggiaManager, key: str) -> None:
        self.manager = manager
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_device_info = manager.device_info_for(key)
        manager.config_entities[key] = self

    @property
    def _target_blinds(self) -> list[str]:
        """Список активных (не исключённых) приводов для этой сущности."""
        if self._key == "sun_blinds":
            return self.manager.protect_blinds
        return self.manager.blinds

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _async_on_blind_change(event) -> None:
            self.async_write_ha_state()

        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, _async_on_blind_change
                )
            )

    @property
    def current_cover_position(self) -> int | None:
        """Среднее положение всех активных приводов в группе."""
        positions: list[int] = []
        for blind in self._target_blinds:
            st = self.hass.states.get(blind) if self.hass else None
            pos = st.attributes.get(ATTR_CURRENT_POSITION) if st else None
            try:
                if pos is not None:
                    positions.append(int(pos))
            except (TypeError, ValueError):
                pass
        if not positions:
            return None
        return int(round(sum(positions) / len(positions)))

    @property
    def is_closed(self) -> bool | None:
        """Шторы считаются закрытыми, если средняя позиция меньше 50% или у нижнего лимита."""
        pos = self.current_cover_position
        if pos is None:
            return None
        down_limit = self.manager.get_down_limit()
        return pos < 50 or abs(pos - down_limit) <= 5

    @property
    def icon(self) -> str:
        """Динамическая кастомная иконка по положению штор (0, 25, 50, 75, 100%)."""
        pos = self.current_cover_position
        if self._key == "sun_blinds":
            if pos is None:
                return "orry:blind-sun"
            return f"orry:blind-sun-{pos_to_blind_step(pos, 0)}"
        return f"orry:blind-{pos_to_blind_step(pos, 100)}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Список активных штор и их индивидуальные позиции."""
        targets = self._target_blinds
        attrs: dict[str, Any] = {
            "active_blinds": list(targets),
            "excluded_blinds": list(self.manager.excluded_blinds),
        }
        for blind in targets:
            st = self.hass.states.get(blind) if self.hass else None
            name = (st.name if st and st.name else blind)
            pos = st.attributes.get(ATTR_CURRENT_POSITION) if st else None
            attrs[name] = f"{pos}%" if pos is not None else "—"
        return attrs

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Открыть шторы группы до верхнего лимита."""
        await self.manager.async_set_position(
            self.manager.get_up_limit(), self._target_blinds
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Закрыть шторы группы до нижнего лимита."""
        await self.manager.async_set_position(
            self.manager.get_down_limit(), self._target_blinds
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Остановить движение штор группы."""
        await self.manager.async_stop(self._target_blinds)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Установить позицию штор группы с учётом верхнего и нижнего лимитов."""
        raw_pos = int(kwargs.get(ATTR_POSITION, 0))
        up_limit = self.manager.get_up_limit()
        down_limit = self.manager.get_down_limit()
        low = min(down_limit, up_limit)
        high = max(down_limit, up_limit)
        clamped_pos = max(low, min(high, raw_pos))
        await self.manager.async_set_position(clamped_pos, self._target_blinds)
