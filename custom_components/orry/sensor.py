"""Сенсоры состояния и диагностики Лоджии."""

import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    DOMAIN,
    MODE_BLINDS,
    MODE_SUN_PROTECT,
    MODE_PHYTOLAMP,
    MODE_WATERING,
    WATERING_MODE_OFF,
    DEFAULT_WATERING_ENABLED,
    DEFAULT_WATERING_SKIP_NEXT,
    DEFAULT_WATERING_MORNING_TIME,
    DEFAULT_WATERING_EVENING_TIME,
    pos_to_blind_step,
)
from .manager import LoggiaManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Установка сенсоров состояния (на основном устройстве) и диагностики (на профильных подустройствах)."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        # Основное устройство: сводные состояния всех модулей («Шторы», «Подсветка», «Полив») и «Далее»
        LoggiaStatusSensor(manager),
        LoggiaPhytolampStatusSensor(manager),
        LoggiaWateringStatusSensor(manager),
        LoggiaNextActionSensor(manager),
    ]

    if manager.has_mode(MODE_BLINDS):
        entities.extend(
            [
                # Подустройство «Привода»: диагностика приводов штор
                LoggiaOpenCountSensor(manager),
                LoggiaClosedCountSensor(manager),
                LoggiaErrorCountSensor(manager),
                LoggiaBatterySensor(manager),
            ]
        )

    if manager.has_mode(MODE_PHYTOLAMP):
        entities.extend(
            [
                # Подустройство «Подсветка»: диагностика светильников/реле
                LoggiaPhytolampOnCountSensor(manager),
                LoggiaPhytolampOffCountSensor(manager),
                LoggiaPhytolampErrorCountSensor(manager),
            ]
        )

    if manager.has_mode(MODE_WATERING):
        entities.extend(
            [
                # Подустройство «Полив»: диагностика полива и датчиков влажности
                LoggiaWateringActiveCountSensor(manager),
                LoggiaWateringErrorCountSensor(manager),
            ]
        )
        if LoggiaWateringBatterySensor.should_create(hass, manager):
            entities.append(LoggiaWateringBatterySensor(manager))
        else:
            ent_reg = er.async_get(hass)
            old_bat_ent_id = ent_reg.async_get_entity_id(
                "sensor", DOMAIN, f"{manager.entry.entry_id}_watering_battery"
            )
            if old_bat_ent_id:
                ent_reg.async_remove(old_bat_ent_id)

    async_add_entities(entities)


class LoggiaBaseSensor(SensorEntity):
    """Базовый класс для сенсоров Лоджии с автоматической привязкой к целевому устройству."""

    _attr_has_entity_name = True

    def __init__(self, manager: LoggiaManager, key: str):
        self.manager = manager
        self._key = key
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = manager.device_info_for(key)
        manager.config_entities[key] = self


class LoggiaStatusSensor(LoggiaBaseSensor):
    """Текстовый сенсор сводного состояния штор (открыты >= 50%, закрыты < 50%) с состоянием каждой шторы в атрибутах."""

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "status")
        self._failed_blinds: list[str] = []
        self._blinds_positions: dict[str, str] = {}
        self._debounce_unsub = None
        manager.set_status_sensor(self)

    @property
    def icon(self) -> str:
        """Динамическая кастомная иконка сводного состояния штор."""
        if not self.manager.has_mode(MODE_BLINDS) or not self.manager.blinds:
            return "orry:blind-0"
        step = pos_to_blind_step(self.manager._get_average_position(), 100)
        if self.manager.has_mode(MODE_SUN_PROTECT) and getattr(self.manager, "_is_sun_protecting", False):
            return f"orry:blind-sun-{step}"
        return f"orry:blind-{step}"

    def _compute_status_and_attributes(self) -> tuple[str, dict[str, str]]:
        if not self.manager.has_mode(MODE_BLINDS):
            return (
                self.manager.tr_sensor_state("status", "not_configured"),
                {},
            )
        all_blinds = self.manager.all_blinds
        excluded = self.manager.excluded_blinds
        active_blinds = [b for b in all_blinds if b not in excluded]
        total = len(active_blinds)

        up_limit = self.manager.get_up_limit()
        down_limit = self.manager.get_down_limit()
        tolerance = 5

        positions_map: dict[str, str] = {}
        open_count = 0
        closed_count = 0

        unknown_txt = self.manager.tr_sensor_state("status", "unknown")
        excl_txt = self.manager.tr_sensor_state("status", "excluded_suffix")

        for blind in all_blinds:
            st = self.hass.states.get(blind) if self.hass else None
            name = (st.name if st and st.name else blind)
            if name in positions_map:
                name = f"{name} ({blind})"

            pos = st.attributes.get("current_position") if st else None
            try:
                p_val = int(pos) if pos is not None else None
            except (TypeError, ValueError):
                p_val = None

            pos_str = f"{p_val}%" if p_val is not None else unknown_txt
            if blind in excluded:
                positions_map[name] = f"{pos_str} ({excl_txt})"
                continue

            positions_map[name] = pos_str
            if p_val is not None:
                if abs(p_val - up_limit) <= tolerance:
                    open_count += 1
                if abs(p_val - down_limit) <= tolerance:
                    closed_count += 1

        if total == 0:
            return (
                self.manager.tr_sensor_state("status", "no_active"),
                positions_map,
            )

        if open_count >= closed_count:
            if open_count == total:
                return (
                    self.manager.tr_sensor_state("status", "all_open"),
                    positions_map,
                )
            return (
                self.manager.tr_sensor_state(
                    "status",
                    "all_open_except",
                    count=total - open_count,
                ),
                positions_map,
            )
        else:
            if closed_count == total:
                return (
                    self.manager.tr_sensor_state("status", "all_closed"),
                    positions_map,
                )
            return (
                self.manager.tr_sensor_state(
                    "status",
                    "all_closed_except",
                    count=total - closed_count,
                ),
                positions_map,
            )

    @property
    def extra_state_attributes(self) -> dict:
        """Положение каждой шторы и список штор, не выполнивших последнее действие."""
        if not self.manager.has_mode(MODE_BLINDS):
            return {}
        attrs = dict(self._blinds_positions)
        attrs["failed_blinds"] = list(self._failed_blinds)
        return attrs

    @callback
    def set_failed_blinds(self, failed_blinds: list[str] | None = None) -> None:
        """Обновить список несработавших штор и пересчитать статус."""
        self._failed_blinds = list(failed_blinds or [])
        self.async_refresh_status()

    @callback
    def async_refresh_status(self, event=None) -> None:
        """Пересчитать текстовое состояние и атрибуты сенсора сразу."""
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None
        state_text, positions_map = self._compute_status_and_attributes()
        self._attr_native_value = state_text
        self._blinds_positions = positions_map
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def _async_debounced_state_change(self, event=None) -> None:
        """Отложенное обновление статуса (1.5 сек), чтобы не спамить в журнал во время движения штор."""
        if self._debounce_unsub:
            self._debounce_unsub()

        @callback
        def _fire(_now) -> None:
            self._debounce_unsub = None
            self.manager.recheck_failed_blinds()
            self.async_refresh_status()

        self._debounce_unsub = async_call_later(self.hass, 1.5, _fire)

    async def async_added_to_hass(self):
        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, self._async_debounced_state_change
                )
            )
        self.async_refresh_status()

    async def async_will_remove_from_hass(self) -> None:
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None


class LoggiaNextActionSensor(LoggiaBaseSensor):
    """Сенсор следующего автоматического действия по всем активным модулям."""

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "next_action")
        self._action_attrs: dict[str, str] = {}
        manager.set_next_action_sensor(self)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Следующее действие по каждому из трёх модулей (без указания названия модуля)."""
        return dict(self._action_attrs)

    def update_state(
        self, state_text: str, action_attrs: dict[str, str] | None = None
    ) -> None:
        self._attr_native_value = state_text
        if action_attrs is not None:
            self._action_attrs = dict(action_attrs)
        if self.hass is not None:
            self.async_write_ha_state()


class LoggiaPhytolampStatusSensor(LoggiaBaseSensor):
    """Сенсор сводного состояния подсветки растений («Подсветка») на основном устройстве Лоджии."""

    _attr_icon = "orry:phytolamp"

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "phytolamp_status")
        self._lamps_state_map: dict[str, str] = {}

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Состояние и идентификаторы устройств подсветки для интерфейсов."""
        if not self.manager.has_mode(MODE_PHYTOLAMP):
            return {}

        attributes: dict[str, object] = dict(self._lamps_state_map)
        lamps: list[dict[str, object]] = []
        used_names: set[str] = set()
        on_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_on")
        off_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_off")
        unknown_lbl = self.manager.tr_sensor_state("status", "unknown")

        for lamp_id in self.manager.phytolamps:
            state = self.hass.states.get(lamp_id) if self.hass else None
            name = state.name if (state and state.name) else lamp_id
            if name in used_names:
                name = f"{name} ({lamp_id})"
            used_names.add(name)
            available = bool(
                state and state.state not in ("unknown", "unavailable", "")
            )
            lamps.append(
                {
                    "entity_id": lamp_id,
                    "name": name,
                    "state": (
                        on_lbl
                        if state and state.state == "on"
                        else off_lbl
                        if available
                        else unknown_lbl
                    ),
                    "is_on": state.state == "on" if available and state else None,
                    "available": available,
                }
            )

        attributes["orry_phytolamps"] = lamps
        return attributes

    @callback
    def async_refresh_status(self, event=None) -> None:
        """Пересчитать текстовое состояние и атрибуты подсветки."""
        if event is not None and hasattr(event, "data"):
            ent_id = event.data.get("entity_id")
            new_st = event.data.get("new_state")
            if ent_id:
                self.manager.on_phytolamp_state_changed(
                    ent_id, new_st.state if new_st else None
                )
        if not self.manager.has_mode(MODE_PHYTOLAMP) or not self.manager.phytolamps:
            self._attr_native_value = self.manager.tr_sensor_state(
                "phytolamp_status", "not_configured"
            )
            self._lamps_state_map = {}
            if self.hass is not None:
                self.async_write_ha_state()
            return

        lamps = self.manager.phytolamps
        total = len(lamps)
        on_count = 0
        lamps_map: dict[str, str] = {}

        on_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_on")
        off_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_off")
        unknown_lbl = self.manager.tr_sensor_state("status", "unknown")

        for lamp_id in lamps:
            st = self.hass.states.get(lamp_id) if self.hass else None
            name = st.name if (st and st.name) else lamp_id
            if name in lamps_map:
                name = f"{name} ({lamp_id})"

            if not st or st.state in ("unknown", "unavailable", ""):
                lamps_map[name] = unknown_lbl
            elif st.state == "on":
                on_count += 1
                lamps_map[name] = on_lbl
            else:
                lamps_map[name] = off_lbl

        self._lamps_state_map = lamps_map
        if on_count == 0:
            self._attr_native_value = self.manager.tr_sensor_state(
                "phytolamp_status", "off"
            )
        elif on_count == total:
            self._attr_native_value = self.manager.tr_sensor_state(
                "phytolamp_status", "on"
            )
        else:
            self._attr_native_value = self.manager.tr_sensor_state(
                "phytolamp_status",
                "phytolamp_on_partial",
                on=on_count,
                total=total,
            )

        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if self.manager.has_mode(MODE_PHYTOLAMP) and self.manager.phytolamps:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    self.manager.phytolamps,
                    self.async_refresh_status,
                )
            )
        self.async_refresh_status()


class LoggiaOpenCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества открытых штор (>= 50%) на подустройстве «Привода»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "orry:blind-100"

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "open_count")
        self._open_blinds: dict[str, str] = {}
        self._debounce_unsub = None

    @property
    def extra_state_attributes(self) -> dict:
        """Список открытых штор с их текущим положением."""
        return dict(self._open_blinds)

    @callback
    def async_refresh_count(self, event=None):
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None
        count = 0
        open_map: dict[str, str] = {}
        for blind in self.manager.blinds:
            st = self.hass.states.get(blind) if self.hass else None
            name = (st.name if st and st.name else blind)
            pos = st.attributes.get("current_position") if st else None
            if pos is not None:
                try:
                    p_val = int(pos)
                    if p_val >= 50:
                        count += 1
                        open_map[name] = f"{p_val}%"
                except (TypeError, ValueError):
                    pass
        self._open_blinds = open_map
        self._attr_native_value = count
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def _async_debounced_state_change(self, event=None) -> None:
        if self._debounce_unsub:
            self._debounce_unsub()

        @callback
        def _fire(_now) -> None:
            self._debounce_unsub = None
            self.async_refresh_count()

        self._debounce_unsub = async_call_later(self.hass, 1.5, _fire)

    async def async_added_to_hass(self):
        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, self._async_debounced_state_change
                )
            )
        self.async_refresh_count()

    async def async_will_remove_from_hass(self) -> None:
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None


class LoggiaClosedCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества закрытых штор (< 50%) на подустройстве «Привода»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "orry:blind-0"

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "closed_count")
        self._closed_blinds: dict[str, str] = {}
        self._debounce_unsub = None

    @property
    def extra_state_attributes(self) -> dict:
        """Список закрытых штор с их текущим положением."""
        return dict(self._closed_blinds)

    @callback
    def async_refresh_count(self, event=None):
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None
        count = 0
        closed_map: dict[str, str] = {}
        for blind in self.manager.blinds:
            st = self.hass.states.get(blind) if self.hass else None
            name = (st.name if st and st.name else blind)
            pos = st.attributes.get("current_position") if st else None
            if pos is not None:
                try:
                    p_val = int(pos)
                    if p_val < 50:
                        count += 1
                        closed_map[name] = f"{p_val}%"
                except (TypeError, ValueError):
                    pass
        self._closed_blinds = closed_map
        self._attr_native_value = count
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def _async_debounced_state_change(self, event=None) -> None:
        if self._debounce_unsub:
            self._debounce_unsub()

        @callback
        def _fire(_now) -> None:
            self._debounce_unsub = None
            self.async_refresh_count()

        self._debounce_unsub = async_call_later(self.hass, 1.5, _fire)

    async def async_added_to_hass(self):
        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, self._async_debounced_state_change
                )
            )
        self.async_refresh_count()

    async def async_will_remove_from_hass(self) -> None:
        if self._debounce_unsub:
            self._debounce_unsub()
            self._debounce_unsub = None


class LoggiaErrorCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества штор, не достигших целевой позиции при последнем действии, на подустройстве «Привода»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "error_count")
        self._attr_native_value = 0
        self._failed_blinds: list[str] = []
        self._target_position: int | None = None
        manager.set_error_sensor(self)

    @property
    def extra_state_attributes(self) -> dict:
        """Список несработавших штор и целевая позиция последней команды."""
        attrs = {"failed_blinds": list(self._failed_blinds)}
        if self._target_position is not None:
            attrs["target_position"] = f"{self._target_position}%"
        return attrs

    def set_errors(
        self,
        count: int,
        failed_blinds: list[str] | None = None,
        target_position: int | None = None,
    ) -> None:
        """Установить текущее количество несработавших приводов и детали в атрибутах."""
        self._attr_native_value = int(count)
        if failed_blinds is not None:
            self._failed_blinds = list(failed_blinds)
        if target_position is not None:
            self._target_position = target_position
        if self.hass is not None:
            self.async_write_ha_state()


class LoggiaBatterySensor(LoggiaBaseSensor):
    """Диагностический сенсор минимального уровня заряда АКБ приводов штор на подустройстве «Привода»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "battery")
        self._batteries_map: dict[str, str] = {}
        self._tracked_entities: set[str] = set()
        self._unsub_track = None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Уровень заряда аккумулятора каждого привода шторы."""
        return dict(self._batteries_map)

    def _find_battery_sensor_for_blind(self, blind_id: str) -> str | None:
        """Найти связанный сенсор заряда батареи для привода шторы через реестр устройств/сущностей."""
        if not self.hass:
            return None
        ent_reg = er.async_get(self.hass)
        cover_entry = ent_reg.async_get(blind_id)
        if cover_entry and cover_entry.device_id:
            for entry in er.async_entries_for_device(
                ent_reg, cover_entry.device_id, include_disabled_entities=False
            ):
                if entry.domain != "sensor":
                    continue
                if (
                    entry.device_class == SensorDeviceClass.BATTERY
                    or entry.original_device_class == SensorDeviceClass.BATTERY
                ):
                    return entry.entity_id
                st = self.hass.states.get(entry.entity_id)
                if st and st.attributes.get("device_class") == SensorDeviceClass.BATTERY:
                    return entry.entity_id
                if entry.entity_id.endswith("_battery"):
                    return entry.entity_id

        obj_id = blind_id.split(".", 1)[-1]
        for cand in (f"sensor.{obj_id}_battery", f"sensor.{obj_id}_battery_level"):
            if self.hass.states.get(cand) is not None:
                return cand
        return None

    def _read_blind_battery(self, blind_id: str) -> tuple[int | None, bool, str | None]:
        """Прочитать заряд батареи привода (возвращает: процент, есть_ли_источник_батареи, entity_id_сенсора)."""
        bat_sensor_id = self._find_battery_sensor_for_blind(blind_id)
        has_source = bat_sensor_id is not None

        if bat_sensor_id and self.hass:
            bat_state = self.hass.states.get(bat_sensor_id)
            if bat_state and bat_state.state not in ("unknown", "unavailable", ""):
                try:
                    val = max(0, min(100, int(round(float(bat_state.state)))))
                    return val, True, bat_sensor_id
                except (TypeError, ValueError):
                    pass

        if self.hass:
            cover_state = self.hass.states.get(blind_id)
            if cover_state:
                for attr_key in ("battery", "battery_level"):
                    if attr_key in cover_state.attributes:
                        has_source = True
                        raw = cover_state.attributes.get(attr_key)
                        if raw is not None:
                            try:
                                val = max(0, min(100, int(round(float(raw)))))
                                return val, True, bat_sensor_id
                            except (TypeError, ValueError):
                                pass

        return None, has_source, bat_sensor_id

    @callback
    def async_refresh_battery(self, event=None) -> None:
        """Пересчитать минимальный уровень заряда и атрибуты по всем приводам."""
        all_blinds = self.manager.all_blinds
        excluded = self.manager.excluded_blinds
        unknown_txt = self.manager.tr_sensor_state("status", "unknown")
        excl_txt = self.manager.tr_sensor_state("status", "excluded_suffix")

        batteries_map: dict[str, str] = {}
        active_values: list[int] = []
        all_values: list[int] = []
        discovered_sensors: set[str] = set()
        levels_by_entity: dict[str, tuple[str, int]] = {}

        for blind in all_blinds:
            st = self.hass.states.get(blind) if self.hass else None
            name = st.name if st and st.name else blind
            if name in batteries_map:
                name = f"{name} ({blind})"

            val, has_source, bat_sensor_id = self._read_blind_battery(blind)
            if bat_sensor_id:
                discovered_sensors.add(bat_sensor_id)

            if val is not None:
                all_values.append(val)
                if blind in excluded:
                    batteries_map[name] = f"{val}% ({excl_txt})"
                else:
                    batteries_map[name] = f"{val}%"
                    active_values.append(val)
                    levels_by_entity[blind] = (name, val)
            elif has_source:
                if blind in excluded:
                    batteries_map[name] = f"{unknown_txt} ({excl_txt})"
                else:
                    batteries_map[name] = unknown_txt

        self._batteries_map = batteries_map
        self.manager.report_battery_levels(levels_by_entity)
        if active_values:
            self._attr_native_value = min(active_values)
        elif all_values:
            self._attr_native_value = min(all_values)
        else:
            self._attr_native_value = None

        target_track = set(all_blinds) | discovered_sensors
        if self.hass and target_track != self._tracked_entities:
            if self._unsub_track:
                self._unsub_track()
                self._unsub_track = None
            self._tracked_entities = target_track
            if target_track:
                self._unsub_track = async_track_state_change_event(
                    self.hass, list(target_track), self.async_refresh_battery
                )

        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_refresh_battery()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_track:
            self._unsub_track()
            self._unsub_track = None
        self._tracked_entities.clear()


class LoggiaWateringStatusSensor(LoggiaBaseSensor):
    """Сенсор сводного состояния полива растений на основном устройстве Лоджии."""

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "watering_status")
        self._active_valve: str | None = None

    @property
    def icon(self) -> str:
        """Кастомная иконка сводного состояния полива (без -off на основном устройстве)."""
        if (
            self.manager.has_mode(MODE_WATERING)
            and self.manager.watering_valves
            and self.manager.get_bool("watering_enabled", DEFAULT_WATERING_ENABLED)
            and not self._active_valve
            and self.manager.get_bool("watering_skip_next", DEFAULT_WATERING_SKIP_NEXT)
        ):
            return "orry:watering-pause"
        return "orry:watering"

    @callback
    def set_active_valve(self, valve_id: str | None) -> None:
        """Установить текущий поливаемый клапан (или None по окончании полива)."""
        self._active_valve = valve_id
        self.async_refresh_status()

    @callback
    def async_refresh_status(self) -> None:
        """Пересчитать текстовое состояние полива."""
        if not self.manager.has_mode(MODE_WATERING) or not self.manager.watering_valves:
            self._attr_native_value = self.manager.tr_sensor_state(
                "watering_status", "not_configured"
            )
            if self.hass is not None:
                self.async_write_ha_state()
            return
        if not self.manager.get_bool("watering_enabled", DEFAULT_WATERING_ENABLED):
            self._attr_native_value = self.manager.tr_sensor_state(
                "watering_status", "disabled"
            )
        elif self._active_valve:
            st = self.hass.states.get(self._active_valve) if self.hass else None
            name = st.name if (st and st.name) else self._active_valve
            self._attr_native_value = self.manager.tr_sensor_state(
                "watering_status",
                "watering_now",
                name=name,
            )
        elif self.manager.get_bool("watering_skip_next", DEFAULT_WATERING_SKIP_NEXT):
            self._attr_native_value = self.manager.tr_sensor_state(
                "watering_status",
                "skip_next",
            )
        else:
            excl_morning = self.manager.excluded_watering_morning
            excl_evening = self.manager.excluded_watering_evening
            has_morning = False
            has_evening = False
            for v in self.manager.watering_valves:
                cfg = self.manager.get_watering_zone_config(v)
                if (
                    v not in excl_morning
                    and cfg.get("m_mode") != WATERING_MODE_OFF
                    and int(cfg.get("m_duration", 0)) > 0
                ):
                    has_morning = True
                if (
                    v not in excl_evening
                    and cfg.get("e_mode") != WATERING_MODE_OFF
                    and int(cfg.get("e_duration", 0)) > 0
                ):
                    has_evening = True

            if not has_morning and not has_evening:
                self._attr_native_value = self.manager.tr_sensor_state(
                    "watering_status", "no_active_zones"
                )
            else:
                m_str = self.manager.get_time_str(
                    "watering_morning_time", DEFAULT_WATERING_MORNING_TIME
                )[:5]
                e_str = self.manager.get_time_str(
                    "watering_evening_time", DEFAULT_WATERING_EVENING_TIME
                )[:5]
                times = []
                if has_morning:
                    times.append(m_str)
                if has_evening:
                    times.append(e_str)
                self._attr_native_value = self.manager.tr_sensor_state(
                    "watering_status",
                    "scheduled",
                    times=", ".join(times),
                )

        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        """Сводка и структурированные настройки направлений полива."""
        if not self.manager.has_mode(MODE_WATERING) or not self.manager.watering_valves:
            return {}
        zones_summary: dict[str, object] = {}
        zones: list[dict[str, object]] = []
        excl_morning = self.manager.excluded_watering_morning
        excl_evening = self.manager.excluded_watering_evening
        m_lbl = self.manager.tr_entity_state("select", "watering_zone", "morning_short")
        e_lbl = self.manager.tr_entity_state("select", "watering_zone", "evening_short")
        sec_lbl = self.manager.tr_entity_state("select", "watering_zone", "unit_sec")
        excl_txt = self.manager.tr_sensor_state("status", "excluded_suffix")
        for v in self.manager.watering_valves:
            st = self.hass.states.get(v) if self.hass else None
            name = st.name if (st and st.name) else v
            cfg = self.manager.get_watering_zone_config(v)
            m_mode_key = str(cfg.get("m_mode", WATERING_MODE_OFF))
            e_mode_key = str(cfg.get("e_mode", WATERING_MODE_OFF))
            m_mode_txt = (
                excl_txt
                if v in excl_morning
                else self.manager.tr_entity_state(
                    "select", "watering_morning_mode", m_mode_key, m_mode_key
                )
            )
            e_mode_txt = (
                excl_txt
                if v in excl_evening
                else self.manager.tr_entity_state(
                    "select", "watering_morning_mode", e_mode_key, e_mode_key
                )
            )
            try:
                morning_duration = int(cfg.get("m_duration", 0) or 0)
            except (TypeError, ValueError):
                morning_duration = 0
            try:
                evening_duration = int(cfg.get("e_duration", 0) or 0)
            except (TypeError, ValueError):
                evening_duration = 0
            zones_summary[name] = (
                f"{m_lbl}: {m_mode_txt} ({morning_duration}{sec_lbl}) | "
                f"{e_lbl}: {e_mode_txt} ({evening_duration}{sec_lbl})"
            )
            zones.append(
                {
                    "entity_id": v,
                    "name": name,
                    "morning_mode": m_mode_txt,
                    "morning_duration": morning_duration,
                    "evening_mode": e_mode_txt,
                    "evening_duration": evening_duration,
                    "morning_excluded": v in excl_morning,
                    "evening_excluded": v in excl_evening,
                    "state": st.state if st else None,
                }
            )

        zones_summary["orry_watering_zones"] = zones
        return zones_summary

    async def async_added_to_hass(self) -> None:
        self.async_refresh_status()


class LoggiaWateringActiveCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества активных направлений полива на подустройстве «Полив»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "watering_active_count")

    @callback
    def async_refresh_count(self) -> None:
        """Пересчитать количество активных направлений полива."""
        excl_morning = self.manager.excluded_watering_morning
        excl_evening = self.manager.excluded_watering_evening
        count = 0
        for v in self.manager.watering_valves:
            cfg = self.manager.get_watering_zone_config(v)
            m_on = (
                v not in excl_morning
                and cfg.get("m_mode") != WATERING_MODE_OFF
                and int(cfg.get("m_duration", 0)) > 0
            )
            e_on = (
                v not in excl_evening
                and cfg.get("e_mode") != WATERING_MODE_OFF
                and int(cfg.get("e_duration", 0)) > 0
            )
            if m_on or e_on:
                count += 1
        self._attr_native_value = count
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        """Общее число направлений полива."""
        return {"total_zones": len(self.manager.watering_valves)}

    async def async_added_to_hass(self) -> None:
        self.async_refresh_count()


class LoggiaPhytolampOnCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества включённых светильников/реле на подустройстве «Подсветка»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "orry:phytolamp"

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "phytolamp_on_count")
        self._on_lamps: dict[str, str] = {}

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Список включённых светильников подсветки."""
        return dict(self._on_lamps)

    @callback
    def async_refresh_status(self, event=None) -> None:
        count = 0
        on_map: dict[str, str] = {}
        on_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_on")
        for lamp_id in self.manager.phytolamps:
            st = self.hass.states.get(lamp_id) if self.hass else None
            if st and st.state == "on":
                count += 1
                name = st.name if st.name else lamp_id
                if name in on_map:
                    name = f"{name} ({lamp_id})"
                on_map[name] = on_lbl
        self._on_lamps = on_map
        self._attr_native_value = count
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if self.manager.phytolamps:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    self.manager.phytolamps,
                    self.async_refresh_status,
                )
            )
        self.async_refresh_status()


class LoggiaPhytolampOffCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества выключенных светильников/реле на подустройстве «Подсветка»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "orry:phytolamp-off"

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "phytolamp_off_count")
        self._off_lamps: dict[str, str] = {}

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Список выключенных светильников подсветки."""
        return dict(self._off_lamps)

    @callback
    def async_refresh_status(self, event=None) -> None:
        count = 0
        off_map: dict[str, str] = {}
        off_lbl = self.manager.tr_sensor_state("phytolamp_status", "lamp_off")
        unknown_lbl = self.manager.tr_sensor_state("status", "unknown")
        for lamp_id in self.manager.phytolamps:
            st = self.hass.states.get(lamp_id) if self.hass else None
            if not st or st.state != "on":
                count += 1
                name = st.name if (st and st.name) else lamp_id
                if name in off_map:
                    name = f"{name} ({lamp_id})"
                off_map[name] = (
                    unknown_lbl
                    if (not st or st.state in ("unknown", "unavailable", ""))
                    else off_lbl
                )
        self._off_lamps = off_map
        self._attr_native_value = count
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if self.manager.phytolamps:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    self.manager.phytolamps,
                    self.async_refresh_status,
                )
            )
        self.async_refresh_status()


class LoggiaPhytolampErrorCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор количества светильников/реле, не поменявших состояние при команде, на подустройстве «Подсветка»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "phytolamp_error_count")
        self._attr_native_value = 0
        self._failed_names: list[str] = []

    @property
    def extra_state_attributes(self) -> dict:
        if self._failed_names:
            return {"failed_lamps": list(self._failed_names)}
        return {}

    @callback
    def async_refresh_status(self, event=None) -> None:
        failed_ids = self.manager.failed_phytolamps
        names: list[str] = []
        for lamp_id in failed_ids:
            st = self.hass.states.get(lamp_id) if self.hass else None
            names.append(st.name if (st and st.name) else lamp_id)
        self._failed_names = names
        self._attr_native_value = len(failed_ids)
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_refresh_status()


class LoggiaWateringErrorCountSensor(LoggiaBaseSensor):
    """Диагностический сенсор общего числа ошибок полива (клапаны + датчики влажности) на подустройстве «Полив»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "watering_error_count")
        self._attr_native_value = 0
        self._valve_errors_count: int = 0
        self._sensor_errors_count: int = 0
        self._failed_valve_names: list[str] = []
        self._failed_sensor_names: list[str] = []

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {
            "valve_errors": self._valve_errors_count,
            "sensor_errors": self._sensor_errors_count,
        }
        if self._failed_valve_names:
            attrs["failed_valves"] = list(self._failed_valve_names)
        if self._failed_sensor_names:
            attrs["failed_sensors"] = list(self._failed_sensor_names)
        return attrs

    @callback
    def _on_entity_event(self, event=None) -> None:
        if event is not None and hasattr(event, "data"):
            ent_id = event.data.get("entity_id")
            new_st = event.data.get("new_state")
            if ent_id:
                self.manager.on_watering_entity_state_changed(
                    ent_id, new_st.state if new_st else None
                )
        self.async_refresh_errors()

    @callback
    def async_refresh_errors(self, event=None) -> None:
        failed_valves = self.manager.watering_valve_errors
        failed_sensors = self.manager.watering_sensor_errors

        v_names: list[str] = []
        for v_id in failed_valves:
            st = self.hass.states.get(v_id) if self.hass else None
            v_names.append(st.name if (st and st.name) else v_id)

        s_names: list[str] = []
        for s_id in failed_sensors:
            st = self.hass.states.get(s_id) if self.hass else None
            s_names.append(st.name if (st and st.name) else s_id)

        self._valve_errors_count = len(failed_valves)
        self._sensor_errors_count = len(failed_sensors)
        self._failed_valve_names = v_names
        self._failed_sensor_names = s_names
        self._attr_native_value = self._valve_errors_count + self._sensor_errors_count
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        tracked = list(
            dict.fromkeys(
                [
                    *self.manager.watering_valves,
                    *self.manager.watering_moisture_map.values(),
                ]
            )
        )
        if tracked:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, tracked, self._on_entity_event
                )
            )
        self.async_refresh_errors()


class LoggiaWateringBatterySensor(LoggiaBaseSensor):
    """Диагностический сенсор уровня заряда АКБ датчиков влажности почвы и беспроводных клапанов полива на подустройстве «Полив»."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, manager: LoggiaManager):
        super().__init__(manager, "watering_battery")
        self._batteries_map: dict[str, str] = {}
        self._tracked_entities: set[str] = set()
        self._unsub_track = None

    @staticmethod
    def _find_battery_sensor_for_entity(
        hass: HomeAssistant | None, target_id: str
    ) -> str | None:
        """Найти связанный сенсор заряда батареи для датчика влажности или клапана через реестр устройств/сущностей."""
        if not hass:
            return None
        ent_reg = er.async_get(hass)
        m_entry = ent_reg.async_get(target_id)
        if m_entry and m_entry.device_id:
            for entry in er.async_entries_for_device(
                ent_reg, m_entry.device_id, include_disabled_entities=False
            ):
                if entry.domain != "sensor" or entry.entity_id == target_id:
                    continue
                if (
                    entry.device_class == SensorDeviceClass.BATTERY
                    or entry.original_device_class == SensorDeviceClass.BATTERY
                ):
                    return entry.entity_id
                st = hass.states.get(entry.entity_id)
                if st and st.attributes.get("device_class") == SensorDeviceClass.BATTERY:
                    return entry.entity_id
                if entry.entity_id.endswith("_battery"):
                    return entry.entity_id

        obj_id = target_id.split(".", 1)[-1]
        for suffix in ("_soil_moisture", "_moisture", "_humidity", "_valve", "_switch"):
            if obj_id.endswith(suffix):
                base_id = obj_id[: -len(suffix)]
                for cand in (
                    f"sensor.{base_id}_battery",
                    f"sensor.{base_id}_battery_level",
                ):
                    if hass.states.get(cand) is not None:
                        return cand
        for cand in (f"sensor.{obj_id}_battery", f"sensor.{obj_id}_battery_level"):
            if hass.states.get(cand) is not None:
                return cand
        return None

    @classmethod
    def _entity_has_battery_source(
        cls, hass: HomeAssistant | None, target_id: str
    ) -> bool:
        """Проверить, есть ли у сущности (датчика почвы или клапана) батарейный сенсор или атрибут."""
        if not hass:
            return False
        if cls._find_battery_sensor_for_entity(hass, target_id) is not None:
            return True
        st = hass.states.get(target_id)
        if st:
            for attr_key in ("battery", "battery_level"):
                if attr_key in st.attributes:
                    return True
        return False

    @classmethod
    def should_create(cls, hass: HomeAssistant, manager: LoggiaManager) -> bool:
        """Создавать сенсор заряда только если выбраны датчики почвы или хотя бы один клапан имеет батарею."""
        if bool(manager.get_setting("watering_use_moisture", False)):
            if any(s for s in manager.watering_moisture_map.values() if s):
                return True
        for v_id in manager.watering_valves:
            if cls._entity_has_battery_source(hass, v_id):
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Уровень заряда аккумулятора каждого подключённого датчика влажности почвы и клапана с АКБ."""
        return dict(self._batteries_map)

    def _find_battery_sensor_for_moisture(self, moisture_id: str) -> str | None:
        """Совместимый метод поиска батарейного сенсора для датчика влажности или клапана."""
        return self._find_battery_sensor_for_entity(self.hass, moisture_id)

    def _read_moisture_battery(
        self, moisture_id: str
    ) -> tuple[int | None, bool, str | None]:
        """Прочитать заряд батареи датчика влажности или клапана (процент, есть_ли_источник_батареи, entity_id_сенсора)."""
        bat_sensor_id = self._find_battery_sensor_for_moisture(moisture_id)
        has_source = bat_sensor_id is not None

        if bat_sensor_id and self.hass:
            bat_state = self.hass.states.get(bat_sensor_id)
            if bat_state and bat_state.state not in ("unknown", "unavailable", ""):
                try:
                    val = max(0, min(100, int(round(float(bat_state.state)))))
                    return val, True, bat_sensor_id
                except (TypeError, ValueError):
                    pass

        if self.hass:
            m_state = self.hass.states.get(moisture_id)
            if m_state:
                for attr_key in ("battery", "battery_level"):
                    if attr_key in m_state.attributes:
                        has_source = True
                        raw = m_state.attributes.get(attr_key)
                        if raw is not None:
                            try:
                                val = max(0, min(100, int(round(float(raw)))))
                                return val, True, bat_sensor_id
                            except (TypeError, ValueError):
                                pass

        return None, has_source, bat_sensor_id

    @callback
    def async_refresh_battery(self, event=None) -> None:
        """Пересчитать минимальный уровень заряда и атрибуты по датчикам влажности почвы и клапанам с АКБ."""
        use_moisture = bool(self.manager.get_setting("watering_use_moisture", False))
        moisture_sensors = (
            list(
                dict.fromkeys(
                    s for s in self.manager.watering_moisture_map.values() if s
                )
            )
            if use_moisture
            else []
        )
        candidates = list(
            dict.fromkeys([*moisture_sensors, *self.manager.watering_valves])
        )
        unknown_txt = self.manager.tr_sensor_state("status", "unknown")

        batteries_map: dict[str, str] = {}
        values: list[int] = []
        discovered_sensors: set[str] = set()
        levels_by_entity: dict[str, tuple[str, int]] = {}

        for m_id in candidates:
            st = self.hass.states.get(m_id) if self.hass else None
            name = st.name if (st and st.name) else m_id
            if name in batteries_map:
                name = f"{name} ({m_id})"

            val, has_source, bat_sensor_id = self._read_moisture_battery(m_id)
            if bat_sensor_id:
                discovered_sensors.add(bat_sensor_id)

            if val is not None:
                values.append(val)
                batteries_map[name] = f"{val}%"
                levels_by_entity[m_id] = (name, val)
            elif has_source or m_id in moisture_sensors:
                batteries_map[name] = unknown_txt

        self._batteries_map = batteries_map
        self.manager.report_battery_levels(levels_by_entity)
        self._attr_native_value = min(values) if values else None

        target_track = set(candidates) | discovered_sensors
        if self.hass and target_track != self._tracked_entities:
            if self._unsub_track:
                self._unsub_track()
                self._unsub_track = None
            self._tracked_entities = target_track
            if target_track:
                self._unsub_track = async_track_state_change_event(
                    self.hass, list(target_track), self.async_refresh_battery
                )

        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_refresh_battery()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_track:
            self._unsub_track()
            self._unsub_track = None
        self._tracked_entities.clear()

