"""Менеджер автоматизации Лоджия."""

import asyncio
import json
import logging
from datetime import date, datetime, time, timedelta

from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
    async_track_state_change_event,
)
from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, ENTITY_GROUP,
    MODE_BLINDS, MODE_SLIDER, MODE_SUN_PROTECT, MODE_PHYTOLAMP, MODE_WATERING, MODE_YANDEX, MODE_LOGGING,
    ACTION_STOP, ACTION_OPEN, ACTION_CLOSE, MANUAL_POSITION_ACTIONS,
    DEFAULT_UP_LIMIT, DEFAULT_DOWN_LIMIT,
    DEFAULT_REPEAT, DEFAULT_REPEAT_DELAY, DEFAULT_MOVEMENT_TIME,
    DEFAULT_BASIC_TOPIC, DEFAULT_PAYLOAD_UP, DEFAULT_PAYLOAD_DOWN, DEFAULT_PAYLOAD_STOP,
    DEFAULT_YANDEX_VOLUME, DEFAULT_YANDEX_INTENT_OPEN, DEFAULT_YANDEX_INTENT_CLOSE,
    DEFAULT_YANDEX_INTENT_POSITION, DEFAULT_YANDEX_INTENT_STATUS,
    VOICE_ENGINE_YANDEX, DEFAULT_VOICE_ENGINE, DEFAULT_VOICE_EVENT,
    SLIDER_MODE_FULL, SLIDER_MODE_STEP, SLIDER_MODE_PROPORTIONAL,
    DEFAULT_SLIDER_MODE, DEFAULT_SLIDER_STEP, DEFAULT_SLIDER_FAST_SPEED, DEFAULT_SLIDER_FAST_TIME_MS,
    DEFAULT_OPEN_AT_SUNRISE, DEFAULT_OPEN_TIME_WORKDAY, DEFAULT_OPEN_TIME_WEEKEND,
    DEFAULT_CLOSE_AT_SUNSET, DEFAULT_CLOSE_TIME,
    DEFAULT_SPLIT_WEEKEND_SCHEDULE,
    DEFAULT_WORK_DAYS, DEFAULT_OFF_DAYS, DEFAULT_CYCLE_START_DATE, DEFAULT_USE_HOLIDAYS,
    RU_FIXED_HOLIDAYS_MD, RU_HOLIDAYS_FALLBACK, RU_WORKING_WEEKENDS_FALLBACK,
    DEFAULT_SUN_SENSOR, DEFAULT_SUN_AZIMUTH, DEFAULT_SUN_ELEVATION,
    DEFAULT_FORECASTS, DEFAULT_MIN_ILLUMINANCE, DEFAULT_MAX_ILLUMINANCE,
    DEFAULT_ILLUMINANCE_DELAY,
    DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
    DEFAULT_PHYTOLAMP_ON_WORKDAY, DEFAULT_PHYTOLAMP_ON_WEEKEND, DEFAULT_PHYTOLAMP_OFF_TIME,
    WATERING_MODE_OFF, WATERING_MODE_DAILY, WATERING_MODE_EVERY_OTHER_DAY,
    WATERING_MODE_EVERY_TWO_DAYS, WATERING_MODE_BY_SENSOR, WATERING_MODES,
    WATERING_ZONE_ALL,
    DEFAULT_WATERING_ENABLED, DEFAULT_WATERING_SKIP_NEXT,
    DEFAULT_WATERING_USE_MOISTURE,
    DEFAULT_WATERING_MORNING_TIME, DEFAULT_WATERING_EVENING_TIME,
    DEFAULT_WATERING_SOIL_THRESHOLD,
    DEFAULT_WATERING_MORNING_MODE, DEFAULT_WATERING_MORNING_DURATION,
    DEFAULT_WATERING_EVENING_MODE, DEFAULT_WATERING_EVENING_DURATION,
    DEFAULT_WATERING_MANUAL_DURATION, DEFAULT_WATERING_SAFETY_MARGIN,
    DEFAULT_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_RECOVERY,
)

_LOGGER = logging.getLogger(__name__)


class LoggiaManager:
    """Класс управления шторами лоджии."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.main_device_id: str | None = None
        self._unsub_listeners: list = []

        # Настройки
        self.config_entities = {}
        self._device_translations: dict[str, str] = {}
        self._entity_translations: dict[str, str] = {}
        self._common_translations: dict[str, str] = {}

        # Сенсоры
        self._status_sensor = None
        self._next_action_sensor = None
        self._error_sensor = None

        # Внутренние состояния
        self._last_day_opened: int = -1
        self._last_day_closed: int = -1
        self._last_day_phytolamp_on: int = -1
        self._last_day_phytolamp_off: int = -1
        self._last_day_watering_morning: int = -1
        self._last_day_watering_evening: int = -1
        self._is_sun_protecting: bool = False
        self._is_phytolamp_sun_off: bool = False
        self._sun_protect_unsub = None
        self._phytolamp_lux_unsub = None
        self._phytolamp_delay_unsub = None
        self._phytolamp_verify_unsub = None
        self._verify_task: asyncio.Task | None = None
        self._watering_task: asyncio.Task | None = None
        self._valve_safety_timers: dict[str, callable] = {}
        self._command_seq: int = 0
        self._last_target_position: int | None = None
        self._failed_blind_ids: list[str] = []
        self._failed_phytolamps: set[str] = set()
        self._phytolamp_expected_state: str | None = None
        self._failed_watering_valves: set[str] = set()
        self._failed_watering_sensors: set[str] = set()
        self._all_battery_levels: dict[str, tuple[str, int]] = {}
        self._low_battery_devices: dict[str, tuple[str, int]] = {}
        self._low_battery_notified: set[str] = set()
        self._ignore_next_options_update: bool = False
        self._selected_watering_zone: str = ACTION_STOP
        self._watering_zones_config: dict[str, dict] = self._init_watering_zones_config()
        self._holidays_cache: dict[tuple[str, int], tuple[set[date], set[date]]] = {}

    def consume_ignore_options_update(self) -> bool:
        """Проверка и сброс флага пропуска перезагрузки при обновлении options из UI сущности."""
        if self._ignore_next_options_update:
            self._ignore_next_options_update = False
            return True
        return False

    def set_status_sensor(self, sensor):
        self._status_sensor = sensor

    def set_next_action_sensor(self, sensor):
        self._next_action_sensor = sensor
        self.update_next_action_text()

    def set_error_sensor(self, sensor):
        self._error_sensor = sensor

    # ────────────────────────────────────────────────────────────
    #  Настройки и устройства
    # ────────────────────────────────────────────────────────────

    def _device_model_name(self, group_key: str) -> str:
        """Получить локализованное название устройства из translations/*.json для поля model."""
        tr_key = f"component.{DOMAIN}.device.{group_key}.name"
        template = self._device_translations.get(tr_key)
        if template:
            try:
                return template.format(title=self.entry.title)
            except Exception:
                return template
        return (
            self.entry.title
            if group_key == "loggia"
            else f"{self.entry.title}: {group_key}"
        )

    def tr_entity_state(
        self,
        platform: str,
        entity_key: str,
        state_key: str,
        default: str = "",
        **kwargs,
    ) -> str:
        """Получить локализованную фразу состояния сущности (или общей секции common) из translations/*.json."""
        full_key = f"component.{DOMAIN}.entity.{platform}.{entity_key}.state.{state_key}"
        common_key = f"component.{DOMAIN}.common.{state_key}"
        template = self._entity_translations.get(full_key)
        if template is None:
            template = self._common_translations.get(common_key, default)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template

    def tr_sensor_state(
        self, sensor_key: str, state_key: str, default: str = "", **kwargs
    ) -> str:
        """Получить локализованную фразу состояния сенсора из translations/*.json."""
        return self.tr_entity_state("sensor", sensor_key, state_key, default, **kwargs)

    def tr_log(self, log_key: str, default: str = "", **kwargs) -> str:
        """Получить локализованную фразу лога из секции common в translations/*.json."""
        common_key = f"component.{DOMAIN}.common.{log_key}"
        template = self._common_translations.get(common_key, default)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template

    @property
    def device_info(self) -> DeviceInfo:
        """Основное устройство."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            translation_key="loggia",
            translation_placeholders={"title": self.entry.title},
            manufacturer="OrangeAI",
            model=self._device_model_name("loggia"),
            entry_type=DeviceEntryType.SERVICE,
        )

    def device_info_for_group(self, group: str | None) -> DeviceInfo:
        """Получить DeviceInfo для указанной группы подустройства (или основного устройства, если group=None)."""
        if group is None:
            return self.device_info
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry.entry_id}_{group}")},
            translation_key=group,
            translation_placeholders={"title": self.entry.title},
            manufacturer="OrangeAI",
            model=self._device_model_name(group),
            entry_type=DeviceEntryType.SERVICE,
            via_device_id=self.main_device_id,
        )

    def device_info_for(self, key: str) -> DeviceInfo:
        """Устройство, к которому относится объект с данным ключом."""
        group = ENTITY_GROUP.get(key)
        return self.device_info_for_group(group)

    @property
    def needs_phytolamp_subdevice(self) -> bool:
        """Нужно ли подустройство собственных настроек подсветки."""
        return self.has_mode(MODE_PHYTOLAMP) and (
            not self.has_mode(MODE_BLINDS)
            or not bool(
                self.get_setting(
                    "phytolamp_use_main_settings",
                    DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                )
            )
        )

    @property
    def needs_sun_subdevice(self) -> bool:
        """Нужно ли подустройство защиты от солнца (углы азимута и высоты)."""
        return self.has_mode(MODE_BLINDS) and self.has_mode(MODE_SUN_PROTECT)

    @property
    def needs_illuminance_subdevice(self) -> bool:
        """Нужно ли подустройство освещённости для защиты от солнца."""
        return (
            self.has_mode(MODE_BLINDS)
            and self.has_mode(MODE_SUN_PROTECT)
            and bool(self.get_setting("use_illuminance", False))
        )

    @property
    def active_groups(self) -> set[str]:
        """Подустройства, которые должны существовать при текущих режимах."""
        groups: set[str] = set()
        if (
            self.has_mode(MODE_BLINDS)
            or self.has_mode(MODE_PHYTOLAMP)
            or self.has_mode(MODE_WATERING)
        ):
            groups.add("schedule")
        if self.has_mode(MODE_BLINDS):
            groups.add("drives")
            if self.needs_sun_subdevice:
                groups.add("sun")
            if self.needs_illuminance_subdevice:
                groups.add("illuminance")
            if self.has_mode(MODE_SLIDER):  # or self.has_mode(MODE_YANDEX)
                groups.add("control")
        if self.has_mode(MODE_PHYTOLAMP):
            groups.add("phytolamp")
        if self.has_mode(MODE_WATERING):
            groups.add("watering")
        return groups

    def get_setting(self, key, default=None):
        if key in self.entry.options:
            val = self.entry.options[key]
            if val is not None and val != "":
                return val
        val = self.entry.data.get(key, default)
        return val if val != "" else default

    def get_number(self, key: str, default: float) -> float:
        """Получить значение из нативного ползунка интеграции."""
        if key in self.config_entities:
            val = self.config_entities[key].native_value
            if val is not None:
                return float(val)
        raw = self.get_setting(key, default)
        try:
            return float(raw) if raw is not None else float(default)
        except (TypeError, ValueError):
            return float(default)

    def get_time_str(self, key: str, default: str) -> str:
        """Получить время (HH:MM:SS) из нативного элемента time."""
        if key in self.config_entities:
            val = self.config_entities[key].native_value
            if val is not None:
                return val.strftime("%H:%M:%S")
        return str(self.get_setting(key, default))

    def get_bool(self, key: str, default: bool) -> bool:
        """Получить булево значение из нативного переключателя switch."""
        if key in self.config_entities:
            val = getattr(self.config_entities[key], "is_on", None)
            if val is not None:
                return bool(val)
        return bool(self.get_setting(key, default))

    @property
    def modes(self) -> list:
        raw_modes = list(self.get_setting("modes", []) or [])
        if not self.get_setting("_modular_v2", False) and self.get_setting("blinds"):
            if MODE_BLINDS not in raw_modes:
                raw_modes.insert(0, MODE_BLINDS)
        return raw_modes

    def has_mode(self, mode: str) -> bool:
        """Проверка, активен ли режим."""
        return mode in self.modes

    @property
    def all_blinds(self) -> list[str]:
        """Полный список всех выбранных в интеграции приводов штор (включая временно исключённые)."""
        return list(self.get_setting("blinds", []) or [])

    @property
    def excluded_blinds(self) -> set[str]:
        """Приоритетный список приводов, полностью исключённых из работы."""
        if "excluded_blinds" in self.config_entities:
            ent = self.config_entities["excluded_blinds"]
            if hasattr(ent, "excluded_set"):
                return set(ent.excluded_set)
        raw = self.get_setting("excluded_blinds", []) or []
        all_set = set(self.all_blinds)
        return {b for b in raw if b in all_set}

    def set_excluded_blinds(self, excluded: list[str] | set[str]) -> None:
        """Сохранить обновлённый список исключённых приводов в options без перезагрузки интеграции."""
        clean_list = [b for b in self.all_blinds if b in excluded]
        if list(self.entry.options.get("excluded_blinds", [])) != clean_list:
            new_options = dict(self.entry.options)
            new_options["excluded_blinds"] = clean_list
            self._ignore_next_options_update = True
            self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        for sensor_key in ("open_count", "closed_count"):
            sensor_ent = self.config_entities.get(sensor_key)
            if sensor_ent and hasattr(sensor_ent, "async_refresh_count"):
                sensor_ent.async_refresh_count()
        bat_ent = self.config_entities.get("battery")
        if bat_ent and hasattr(bat_ent, "async_refresh_battery"):
            bat_ent.async_refresh_battery()
        for cover_key in ("blinds", "sun_blinds"):
            cover_ent = self.config_entities.get(cover_key)
            if cover_ent:
                cover_ent.async_write_ha_state()
        self.recheck_failed_blinds()
        self._sync_repair_issues()
        if self._status_sensor:
            self._status_sensor.async_refresh_status()

    @property
    def blinds(self) -> list[str]:
        """Активные привода штор (за вычетом приоритетного списка исключённых)."""
        excluded = self.excluded_blinds
        return [b for b in self.all_blinds if b not in excluded]

    @property
    def protect_blinds(self) -> list[str]:
        """Пересечение выбранных штор защиты с активными основными шторами (п. 5 ТЗ)."""
        active_blinds = self.blinds
        specified = self.get_setting("blinds_for_protect", [])
        if not specified:
            return active_blinds
        return [b for b in specified if b in active_blinds]

    def get_up_limit(self) -> int:
        """Верхний предел из нативного ползунка интеграции."""
        return int(self.get_number("up_limit", DEFAULT_UP_LIMIT))

    def get_down_limit(self) -> int:
        """Нижний предел из нативного ползунка интеграции."""
        return int(self.get_number("down_limit", DEFAULT_DOWN_LIMIT))

    def _get_average_position(self) -> int:
        positions = []
        for blind in self.blinds:
            st = self.hass.states.get(blind)
            if st and st.attributes.get(ATTR_CURRENT_POSITION) is not None:
                try:
                    positions.append(int(st.attributes[ATTR_CURRENT_POSITION]))
                except (TypeError, ValueError):
                    continue
        return int(sum(positions) / len(positions)) if positions else 50

    # ────────────────────────────────────────────────────────────
    #  Команды шторам
    # ────────────────────────────────────────────────────────────

    async def async_set_position(self, position: int, blinds_target: list | None = None):
        excluded = self.excluded_blinds
        target_blinds = [
            b for b in (blinds_target if blinds_target is not None else self.blinds)
            if b not in excluded
        ]
        if not target_blinds:
            return

        position = max(0, min(100, int(position)))
        self._last_target_position = position
        repeat_count = int(self.get_number("repeat_for", DEFAULT_REPEAT))
        repeat_delay = int(self.get_number("delay_for_repeat", DEFAULT_REPEAT_DELAY))
        tolerance = repeat_count

        # Фильтруем шторы, которые уже находятся в целевой позиции (в пределах допуска)
        blinds_to_move = []
        for blind in target_blinds:
            st = self.hass.states.get(blind)
            cur = st.attributes.get(ATTR_CURRENT_POSITION) if st else None
            try:
                if cur is None or abs(int(cur) - position) > tolerance:
                    blinds_to_move.append(blind)
            except (TypeError, ValueError):
                blinds_to_move.append(blind)

        if not blinds_to_move:
            _LOGGER.debug(
                "%s",
                self.tr_log(
                    "log_already_at_pos",
                    position=position,
                    tolerance=tolerance,
                ),
            )
            self._failed_blind_ids = []
            if self._error_sensor:
                self._error_sensor.set_errors(0, [], position)
            if self._status_sensor:
                self._status_sensor.set_failed_blinds([])
            return

        _LOGGER.info(
            "%s",
            self.tr_log("log_set_pos", position=position, blinds=blinds_to_move),
        )

        self._command_seq += 1
        my_seq = self._command_seq

        if self._verify_task and not self._verify_task.done():
            self._verify_task.cancel()

        for i in range(repeat_count):
            if self._command_seq != my_seq:
                return
            calc_pos = max(0, min(100, position - (repeat_count - 1 - i)))
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {"entity_id": blinds_to_move, ATTR_POSITION: calc_pos},
                blocking=True,
            )
            if i < repeat_count - 1:
                await asyncio.sleep(repeat_delay)

        if self._command_seq != my_seq:
            return

        movement_time = int(self.get_number("movement_time", DEFAULT_MOVEMENT_TIME))
        direction = "up" if position >= 50 else "down"
        self._verify_task = self.entry.async_create_background_task(
            self.hass,
            self._async_verify_movement(blinds_to_move, position, movement_time, direction, my_seq),
            "loggia_verify_movement",
        )

    async def async_stop(self, blinds_target: list | None = None):
        self._command_seq += 1
        if self._verify_task and not self._verify_task.done():
            self._verify_task.cancel()
        excluded = self.excluded_blinds
        target_blinds = [
            b for b in (blinds_target if blinds_target is not None else self.blinds)
            if b not in excluded
        ]
        if not target_blinds:
            return
        _LOGGER.info("%s", self.tr_log("log_stop", blinds=target_blinds))
        repeat_count = int(self.get_number("repeat_for", DEFAULT_REPEAT))
        for _ in range(repeat_count):
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_STOP_COVER,
                {"entity_id": target_blinds},
                blocking=True,
            )

    async def async_execute_manual_action(self) -> None:
        """Выполнить выбранное в списке ручное действие для активных приводов и вернуть выбор на 'Остановить'."""
        action_ent = self.config_entities.get("manual_action")
        action = (
            action_ent.current_option
            if action_ent and action_ent.current_option
            else ACTION_STOP
        )
        up_limit = self.get_up_limit()
        down_limit = self.get_down_limit()
        low = min(down_limit, up_limit)
        high = max(down_limit, up_limit)

        if action == ACTION_STOP:
            await self.async_stop()
        elif action == ACTION_OPEN:
            await self.async_set_position(up_limit)
        elif action == ACTION_CLOSE:
            await self.async_set_position(down_limit)
        elif action in MANUAL_POSITION_ACTIONS:
            target_pct = MANUAL_POSITION_ACTIONS[action]
            if low <= target_pct <= high:
                await self.async_set_position(target_pct)
            else:
                _LOGGER.warning(
                    "%s",
                    self.tr_log(
                        "log_out_of_limits",
                        target=target_pct,
                        low=low,
                        high=high,
                    ),
                )

        if action_ent and hasattr(action_ent, "reset_to_stop"):
            action_ent.reset_to_stop()

    # ────────────────────────────────────────────────────────────
    #  Проверка доезда + ошибки
    # ────────────────────────────────────────────────────────────

    async def _async_verify_movement(
        self,
        blinds_list: list,
        target_position: int,
        delay_seconds: int,
        direction: str = "down",
        cmd_seq: int | None = None,
    ):
        await asyncio.sleep(delay_seconds)
        if cmd_seq is not None and self._command_seq != cmd_seq:
            return

        repeat_tol = int(self.get_number("repeat_for", DEFAULT_REPEAT))
        excluded = self.excluded_blinds
        active_targets = [b for b in blinds_list if b not in excluded]
        if not active_targets:
            return

        # Опрос реального физического положения каждого привода (как в оригинальном проекте dev.covers.yaml):
        # микро-шаг +/- repeat_for и через 500 мс stop_cover заставляют привод прислать реальный current_position
        nudge_pos = max(
            0,
            min(
                100,
                target_position + (-repeat_tol if direction == "up" else repeat_tol),
            ),
        )
        for blind in active_targets:
            if cmd_seq is not None and self._command_seq != cmd_seq:
                return
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {"entity_id": blind, ATTR_POSITION: nudge_pos},
                blocking=True,
            )
            await asyncio.sleep(0.5)
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_STOP_COVER,
                {"entity_id": blind},
                blocking=True,
            )

        await asyncio.sleep(2)
        if cmd_seq is not None and self._command_seq != cmd_seq:
            return

        failed = []
        failed_ids = []
        tolerance = max(5, repeat_tol)
        excluded = self.excluded_blinds

        # Проверяем только те привода из целевого списка, которые не отключены
        for blind in blinds_list:
            if blind in excluded:
                continue
            state = self.hass.states.get(blind)
            if not state:
                failed.append(blind)
                failed_ids.append(blind)
                continue
            cur = state.attributes.get(ATTR_CURRENT_POSITION)
            try:
                cur_val = int(cur) if cur is not None else None
            except (TypeError, ValueError):
                cur_val = None
            if cur_val is None or abs(cur_val - target_position) > tolerance:
                failed.append(state.name or blind)
                failed_ids.append(blind)

        self._failed_blind_ids = failed_ids
        if self._error_sensor:
            self._error_sensor.set_errors(len(failed), failed, target_position)
        if self._status_sensor:
            self._status_sensor.set_failed_blinds(failed)
        self._sync_repair_issues()

        if failed:
            await self._async_handle_error(failed, target_position, direction)

    @callback
    def recheck_failed_blinds(self) -> None:
        """Убрать из списка ошибок привода, которые доехали до цели или были переведены в нужную сторону (открыты >=50% / закрыты <50%)."""
        if not self._failed_blind_ids or self._last_target_position is None:
            return

        tolerance = max(5, int(self.get_number("repeat_for", DEFAULT_REPEAT)))
        excluded = self.excluded_blinds
        still_failed_ids = []
        still_failed_names = []
        target = self._last_target_position

        for blind in self._failed_blind_ids:
            if blind in excluded:
                continue
            state = self.hass.states.get(blind)
            if not state:
                still_failed_ids.append(blind)
                still_failed_names.append(blind)
                continue
            cur = state.attributes.get(ATTR_CURRENT_POSITION)
            try:
                cur_val = int(cur) if cur is not None else None
            except (TypeError, ValueError):
                cur_val = None

            if cur_val is None:
                still_failed_ids.append(blind)
                still_failed_names.append(state.name or blind)
                continue

            reached_exact = abs(cur_val - target) <= tolerance
            reached_side = (target >= 50 and cur_val >= 50) or (target < 50 and cur_val < 50)
            if not (reached_exact or reached_side):
                still_failed_ids.append(blind)
                still_failed_names.append(state.name or blind)

        if len(still_failed_ids) != len(self._failed_blind_ids):
            self._failed_blind_ids = still_failed_ids
            if self._error_sensor:
                self._error_sensor.set_errors(len(still_failed_names), still_failed_names, target)
            if self._status_sensor:
                self._status_sensor.set_failed_blinds(still_failed_names)
            self._sync_repair_issues()

    @callback
    def _sync_repair_issues(self) -> None:
        """Создать или автоматически закрыть предупреждения в Home Assistant Repairs (Настройки -> Система -> Ремонт)."""
        if not self.hass:
            return
        eid = self.entry.entry_id

        # 1. Привода штор
        excluded = self.excluded_blinds
        active_failed_blinds = [
            b for b in self._failed_blind_ids if b not in excluded
        ]
        if active_failed_blinds and self.has_mode(MODE_BLINDS):
            names = []
            for b in active_failed_blinds:
                st = self.hass.states.get(b)
                names.append(st.name if (st and st.name) else b)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"blinds_error_{eid}",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="blinds_error",
                translation_placeholders={
                    "title": self.entry.title,
                    "devices": ", ".join(names),
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, f"blinds_error_{eid}")

        # 2. Подсветка растений
        failed_lamps = self.failed_phytolamps if self.has_mode(MODE_PHYTOLAMP) else []
        if failed_lamps:
            names = []
            for l_id in failed_lamps:
                st = self.hass.states.get(l_id)
                names.append(st.name if (st and st.name) else l_id)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"phytolamp_error_{eid}",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="phytolamp_error",
                translation_placeholders={
                    "title": self.entry.title,
                    "devices": ", ".join(names),
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, f"phytolamp_error_{eid}")

        # 3. Полив растений (клапаны + датчики влажности)
        if self.has_mode(MODE_WATERING):
            w_failed = list(
                dict.fromkeys(
                    [*self.watering_valve_errors, *self.watering_sensor_errors]
                )
            )
        else:
            w_failed = []
        if w_failed:
            names = []
            for ent_id in w_failed:
                st = self.hass.states.get(ent_id)
                names.append(st.name if (st and st.name) else ent_id)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"watering_error_{eid}",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="watering_error",
                translation_placeholders={
                    "title": self.entry.title,
                    "devices": ", ".join(names),
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, f"watering_error_{eid}")

        # 4. Низкий заряд батарей (< порога low_battery_threshold)
        if self._low_battery_devices:
            bat_items = [
                f"{name} ({pct}%)"
                for name, pct in self._low_battery_devices.values()
            ]
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"low_battery_{eid}",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="low_battery",
                translation_placeholders={
                    "title": self.entry.title,
                    "threshold": str(self.low_battery_threshold),
                    "devices": ", ".join(bat_items),
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, f"low_battery_{eid}")

    async def _async_dispatch_alert(
        self,
        message: str,
        tts_message: str | None = None,
        logbook_name: str | None = None,
        notify_title: str | None = None,
        allow_night_tts: bool = True,
    ) -> None:
        """Отправить уведомление об ошибке в Logbook, Push и на голосовые колонки (если включён MODE_LOGGING)."""
        if not self.has_mode(MODE_LOGGING):
            return

        players = self.get_setting("yandex_media_player", []) or []
        if players:
            can_speak = True
            if not allow_night_tts:
                now_hour = dt_util.now().hour
                can_speak = 9 <= now_hour < 21
            if can_speak:
                await self._async_speak(tts_message or message, players)

        lb_name = logbook_name or self.tr_sensor_state("error_count", "logbook_name")
        title_str = notify_title or self.tr_sensor_state("error_count", "notify_title")

        _LOGGER.error("%s", self.tr_log("log_error_prefix", message=message))

        await self.hass.services.async_call(
            "logbook", "log", {"name": lb_name, "message": message}
        )

        for target in self.get_setting("notify_target", []) or []:
            parts = target.split(".")
            if len(parts) == 2:
                try:
                    if parts[0] == "notify" and self.hass.states.get(target) is not None:
                        await self.hass.services.async_call(
                            "notify",
                            "send_message",
                            {
                                "entity_id": target,
                                "title": title_str,
                                "message": message,
                            },
                        )
                    else:
                        await self.hass.services.async_call(
                            parts[0],
                            parts[1],
                            {"title": title_str, "message": message},
                        )
                except Exception as err:
                    _LOGGER.error(
                        "%s",
                        self.tr_log(
                            "log_notify_error", target=target, error=err
                        ),
                    )

    async def _async_handle_error(
        self, failed_blinds: list, target_position: int, direction: str = "down"
    ):
        if not self.has_mode(MODE_LOGGING):
            return

        blinds_str = ", ".join(failed_blinds)
        count = len(failed_blinds)

        if count == 1:
            tts_key = "tts_single_open" if direction == "up" else "tts_single_close"
            tts_message = self.tr_sensor_state(
                "error_count", tts_key, blinds=blinds_str
            )
        else:
            tts_key = "tts_multi_open" if direction == "up" else "tts_multi_close"
            tts_message = self.tr_sensor_state(
                "error_count", tts_key, count=count, blinds=blinds_str
            )

        log_key = "log_open" if direction == "up" else "log_close"
        message = self.tr_sensor_state(
            "error_count",
            log_key,
            target=target_position,
            blinds=blinds_str,
        )
        await self._async_dispatch_alert(
            message=message,
            tts_message=tts_message,
            logbook_name=self.tr_sensor_state("error_count", "logbook_name"),
            notify_title=self.tr_sensor_state("error_count", "notify_title"),
            allow_night_tts=True,
        )

    async def _async_handle_phytolamp_error(
        self, failed_lamp_ids: list[str], turn_on: bool
    ) -> None:
        """Отправить уведомление о несработавших реле/светильниках подсветки."""
        if not self.has_mode(MODE_LOGGING) or not failed_lamp_ids:
            return
        names = []
        for l_id in failed_lamp_ids:
            st = self.hass.states.get(l_id)
            names.append(st.name if (st and st.name) else l_id)
        devices_str = ", ".join(names)
        msg_key = "log_phytolamp_fail_on" if turn_on else "log_phytolamp_fail_off"
        tts_key = "tts_phytolamp_fail_on" if turn_on else "tts_phytolamp_fail_off"
        message = self.tr_log(msg_key, devices=devices_str)
        tts_message = self.tr_log(tts_key, devices=devices_str)
        await self._async_dispatch_alert(
            message=message,
            tts_message=tts_message,
            logbook_name=self.tr_log("logbook_name_phytolamp"),
            notify_title=self.tr_log("notify_title_phytolamp"),
            allow_night_tts=True,
        )

    async def _async_handle_watering_valve_error(
        self, failed_valve_ids: list[str], is_cutoff: bool = False
    ) -> None:
        """Отправить уведомление об ошибке клапана полива или срабатывании защиты от перелива."""
        if not self.has_mode(MODE_LOGGING) or not failed_valve_ids:
            return
        names = []
        for v_id in failed_valve_ids:
            st = self.hass.states.get(v_id)
            names.append(st.name if (st and st.name) else v_id)
        devices_str = ", ".join(names)
        msg_key = "log_watering_cutoff_alert" if is_cutoff else "log_watering_valve_fail"
        tts_key = "tts_watering_cutoff_alert" if is_cutoff else "tts_watering_valve_fail"
        message = self.tr_log(msg_key, devices=devices_str)
        tts_message = self.tr_log(tts_key, devices=devices_str)
        await self._async_dispatch_alert(
            message=message,
            tts_message=tts_message,
            logbook_name=self.tr_log("logbook_name_watering"),
            notify_title=self.tr_log("notify_title_watering"),
            allow_night_tts=True,
        )

    async def _async_handle_watering_sensor_error(
        self, failed_sensor_ids: list[str]
    ) -> None:
        """Отправить уведомление о недоступности датчика влажности почвы."""
        if not self.has_mode(MODE_LOGGING) or not failed_sensor_ids:
            return
        names = []
        for s_id in failed_sensor_ids:
            st = self.hass.states.get(s_id)
            names.append(st.name if (st and st.name) else s_id)
        devices_str = ", ".join(names)
        message = self.tr_log("log_watering_sensor_fail", devices=devices_str)
        tts_message = self.tr_log("tts_watering_sensor_fail", devices=devices_str)
        await self._async_dispatch_alert(
            message=message,
            tts_message=tts_message,
            logbook_name=self.tr_log("logbook_name_watering"),
            notify_title=self.tr_log("notify_title_watering"),
            allow_night_tts=False,
        )

    @property
    def low_battery_threshold(self) -> int:
        """Порог предупреждения о низком заряде батареи (%)."""
        return max(
            5,
            min(
                50,
                int(
                    self.get_number(
                        "low_battery_threshold", DEFAULT_LOW_BATTERY_THRESHOLD
                    )
                ),
            ),
        )

    @callback
    def recheck_battery_thresholds(self) -> None:
        """Пересчитать список разряженных батарей при изменении порога на основном устройстве."""
        if self._all_battery_levels:
            self.report_battery_levels(dict(self._all_battery_levels))

    @callback
    def report_battery_levels(
        self, levels_by_entity: dict[str, tuple[str, int]]
    ) -> None:
        """Обновить контроль низкого заряда АКБ (< порога с гистерезисом восстановления +5%) и отправить разовое оповещение."""
        self._all_battery_levels.update(levels_by_entity)
        threshold = self.low_battery_threshold
        recovery = min(100, threshold + 5)
        newly_low: list[tuple[str, int]] = []
        changed = False

        for ent_id, (name, pct) in self._all_battery_levels.items():
            if pct < threshold:
                prev = self._low_battery_devices.get(ent_id)
                if prev != (name, pct):
                    self._low_battery_devices[ent_id] = (name, pct)
                    changed = True
                if ent_id not in self._low_battery_notified:
                    self._low_battery_notified.add(ent_id)
                    newly_low.append((name, pct))
            elif pct >= recovery or (ent_id in levels_by_entity and pct >= threshold and self._low_battery_devices.get(ent_id, (None, 0))[1] >= threshold):
                if ent_id in self._low_battery_devices:
                    self._low_battery_devices.pop(ent_id, None)
                    changed = True
                self._low_battery_notified.discard(ent_id)

        # Если порог был понижен пользователем и ранее записанный процент теперь >= нового порога, снимаем предупреждение
        for ent_id in list(self._low_battery_devices.keys()):
            if self._low_battery_devices[ent_id][1] >= threshold:
                self._low_battery_devices.pop(ent_id, None)
                self._low_battery_notified.discard(ent_id)
                changed = True

        if changed:
            self._sync_repair_issues()

        if newly_low and self.has_mode(MODE_LOGGING):
            items_str = ", ".join(f"{n} ({p}%)" for n, p in newly_low)
            message = self.tr_log(
                "log_low_battery", threshold=threshold, devices=items_str
            )
            tts_message = self.tr_log("tts_low_battery", devices=items_str)
            self.entry.async_create_background_task(
                self.hass,
                self._async_dispatch_alert(
                    message=message,
                    tts_message=tts_message,
                    logbook_name=self.tr_log("logbook_name_battery"),
                    notify_title=self.tr_log("notify_title_battery"),
                    allow_night_tts=False,
                ),
                "loggia_low_battery_alert",
            )

    # ────────────────────────────────────────────────────────────
    #  БЛОК 1: Логика времени и Сенсор следующего действия (п. 1.1, 1.2 ТЗ)
    # ────────────────────────────────────────────────────────────

    def _parse_time(self, time_str: str) -> time:
        try:
            parts = [int(x) for x in str(time_str).split(":")]
            return time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)
        except Exception:
            return time(0, 0)

    @staticmethod
    def _ceil_to_minute(dt_val: datetime) -> time:
        """Округлить локальное время события солнца в большую сторону до минуты (если есть секунды)."""
        local_dt = dt_util.as_local(dt_val)
        if local_dt.second > 0 or local_dt.microsecond > 0:
            local_dt = local_dt + timedelta(minutes=1)
        return local_dt.time().replace(second=0, microsecond=0)

    def _get_sun_event_time(self, attr_name: str, now: datetime | None = None) -> time | None:
        """Получить локальное время сегодняшнего рассвета (next_rising) или заката (next_setting)."""
        if now is None:
            now = dt_util.now()
        try:
            astral_event = "sunrise" if attr_name == "next_rising" else "sunset"
            astral_dt = get_astral_event_date(self.hass, astral_event, now.date())
            if isinstance(astral_dt, datetime):
                return self._ceil_to_minute(astral_dt)
        except Exception:
            pass

        sun_sensor = self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)
        sun_state = self.hass.states.get(sun_sensor)
        if not sun_state:
            return None
        raw = sun_state.attributes.get(attr_name)
        if not raw:
            return None
        dt_val = dt_util.parse_datetime(str(raw)) if isinstance(raw, str) else raw
        if isinstance(dt_val, datetime):
            return self._ceil_to_minute(dt_val)
        return None

    @property
    def phytolamps(self) -> list[str]:
        """Список выбранных устройств управления подсветкой (switch / light)."""
        raw = self.get_setting("phytolamp", []) or []
        if isinstance(raw, str):
            return [raw] if raw else []
        return [e for e in raw if e]

    @property
    def phytolamp_illuminance_sensor(self) -> str | None:
        """Сенсор освещённости для подсветки (если не выбран — используется основной illuminance_sensor)."""
        return self.get_setting("phytolamp_illuminance_sensor") or self.get_setting("illuminance_sensor")

    @property
    def failed_phytolamps(self) -> list[str]:
        """Активные светильники подсветки, не переключившиеся при последней команде."""
        active = set(self.phytolamps)
        return [e for e in self.phytolamps if e in self._failed_phytolamps and e in active]

    @callback
    def _refresh_phytolamp_sensors(self) -> None:
        """Обновить диагностические сенсоры подсветки (Включено / Выключено / Ошибки) и основной статус."""
        for key in (
            "phytolamp_status",
            "phytolamp_on_count",
            "phytolamp_off_count",
            "phytolamp_error_count",
        ):
            ent = self.config_entities.get(key)
            if ent and hasattr(ent, "async_refresh_status"):
                ent.async_refresh_status()
        self._sync_repair_issues()

    @callback
    def on_phytolamp_state_changed(self, entity_id: str, new_state_str: str | None) -> None:
        """Сбросить ошибку светильника, если он перешёл в ожидаемое рабочее состояние."""
        if entity_id in self._failed_phytolamps and new_state_str in ("on", "off"):
            if (
                self._phytolamp_expected_state is None
                or new_state_str == self._phytolamp_expected_state
            ):
                self._failed_phytolamps.discard(entity_id)
                err_ent = self.config_entities.get("phytolamp_error_count")
                if err_ent and hasattr(err_ent, "async_refresh_status"):
                    err_ent.async_refresh_status()
                self._sync_repair_issues()

    async def async_set_phytolamp(self, turn_on: bool) -> None:
        """Включить или выключить устройства подсветки растений с проверкой переключения."""
        if not self.has_mode(MODE_PHYTOLAMP):
            return
        lamps = self.phytolamps
        if not lamps:
            return
        expected = "on" if turn_on else "off"
        self._phytolamp_expected_state = expected
        service = "turn_on" if turn_on else "turn_off"
        _LOGGER.info(
            "%s",
            self.tr_log(
                "log_phytolamp_on" if turn_on else "log_phytolamp_off",
                lamps=lamps,
            ),
        )
        if self._phytolamp_verify_unsub is not None:
            self._phytolamp_verify_unsub()
            self._phytolamp_verify_unsub = None

        call_failed = False
        try:
            await self.hass.services.async_call(
                "homeassistant",
                service,
                {"entity_id": lamps},
                blocking=True,
            )
        except Exception as err:
            call_failed = True
            _LOGGER.error(
                "%s",
                self.tr_log("log_phytolamp_error", service=service, error=err),
            )

        @callback
        def _verify_phytolamps(_now=None) -> None:
            self._phytolamp_verify_unsub = None
            prev_failed = set(self._failed_phytolamps)
            failed: set[str] = set()
            for lamp_id in self.phytolamps:
                st = self.hass.states.get(lamp_id)
                if not st or st.state != expected:
                    failed.add(lamp_id)
            self._failed_phytolamps = failed
            self._refresh_phytolamp_sensors()
            newly_failed = [
                lid for lid in self.phytolamps if lid in failed and lid not in prev_failed
            ]
            if newly_failed and self.has_mode(MODE_LOGGING):
                self.entry.async_create_background_task(
                    self.hass,
                    self._async_handle_phytolamp_error(newly_failed, turn_on),
                    "loggia_phytolamp_error_alert",
                )

        if call_failed:
            _verify_phytolamps()
        else:
            self._phytolamp_verify_unsub = async_call_later(
                self.hass, 3.0, _verify_phytolamps
            )

    @callback
    def _schedule_phytolamp_with_movement_delay(self, turn_on: bool) -> None:
        """Запланировать включение/выключение подсветки с задержкой полного хода штор (movement_time)."""
        if self._phytolamp_delay_unsub is not None:
            self._phytolamp_delay_unsub()
            self._phytolamp_delay_unsub = None

        delay_sec = max(0, int(self.get_number("movement_time", DEFAULT_MOVEMENT_TIME)))
        _LOGGER.info(
            "%s",
            self.tr_log(
                "log_phytolamp_delay_on" if turn_on else "log_phytolamp_delay_off",
                delay=delay_sec,
            ),
        )

        async def _async_delayed_phytolamp(_now) -> None:
            self._phytolamp_delay_unsub = None
            if turn_on:
                if self._is_within_phytolamp_time_bounds() and not self._is_sun_protecting:
                    await self.async_set_phytolamp(True)
            else:
                await self.async_set_phytolamp(False)

        if delay_sec > 0:
            self._phytolamp_delay_unsub = async_call_later(
                self.hass, delay_sec, _async_delayed_phytolamp
            )
        else:
            self.entry.async_create_background_task(
                self.hass,
                _async_delayed_phytolamp(None),
                "loggia_phytolamp_delay",
            )

    def _get_year_holidays(
        self, country: str, year: int
    ) -> tuple[set[date], set[date]]:
        """Получить множества (праздничные_выходные, рабочие_выходные) для страны и года (с кэшированием)."""
        cache_key = (country.upper(), year)
        if cache_key in self._holidays_cache:
            return self._holidays_cache[cache_key]

        holiday_dates: set[date] = set()
        workday_weekends: set[date] = set()

        try:
            import holidays as py_holidays  # type: ignore

            cal = py_holidays.country_holidays(country.upper(), years=[year])
            holiday_dates.update(cal.keys())
            if hasattr(py_holidays, "WORKDAY"):
                try:
                    w_cal = py_holidays.country_holidays(
                        country.upper(),
                        years=[year],
                        categories=(py_holidays.WORKDAY,),
                    )
                    workday_weekends.update(w_cal.keys())
                except Exception:
                    pass
        except Exception:
            pass

        if country.upper() == "RU":
            prefix = f"{year}-"
            matched_year = False
            for iso_str in RU_HOLIDAYS_FALLBACK:
                if iso_str.startswith(prefix):
                    matched_year = True
                    try:
                        holiday_dates.add(date.fromisoformat(iso_str))
                    except ValueError:
                        pass
            for iso_str in RU_WORKING_WEEKENDS_FALLBACK:
                if iso_str.startswith(prefix):
                    try:
                        workday_weekends.add(date.fromisoformat(iso_str))
                    except ValueError:
                        pass
            if not matched_year and not holiday_dates:
                for m, d in RU_FIXED_HOLIDAYS_MD:
                    try:
                        holiday_dates.add(date(year, m, d))
                    except ValueError:
                        pass

        self._holidays_cache[cache_key] = (holiday_dates, workday_weekends)
        return holiday_dates, workday_weekends

    @property
    def split_weekend_schedule(self) -> bool:
        """Разделять ли расписание на будни и выходные."""
        return bool(
            self.get_setting("split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE)
        )

    def _is_weekend_day(self, now: datetime | date | None = None) -> bool:
        """Определить, действует ли в указанную дату расписание выходного дня (универсальный цикл N/M + госпраздники)."""
        if not self.split_weekend_schedule:
            return False

        if now is None:
            now = dt_util.now()
        target_date = now.date() if isinstance(now, datetime) else now

        work_days = max(0, int(self.get_number("work_days", DEFAULT_WORK_DAYS)))
        off_days = max(0, int(self.get_number("off_days", DEFAULT_OFF_DAYS)))
        if work_days <= 0 and off_days > 0:
            return True
        if off_days <= 0 and work_days > 0 and not self.get_bool("use_holidays", DEFAULT_USE_HOLIDAYS):
            return False

        raw_start = str(
            self.get_setting("cycle_start_date", DEFAULT_CYCLE_START_DATE)
            or DEFAULT_CYCLE_START_DATE
        ).strip()
        try:
            anchor_date = date.fromisoformat(raw_start[:10])
        except ValueError:
            anchor_date = date(2026, 1, 5)

        if self.get_bool("use_holidays", DEFAULT_USE_HOLIDAYS):
            country = str(getattr(self.hass.config, "country", None) or "RU").upper()
            holiday_dates, workday_weekends = self._get_year_holidays(
                country, target_date.year
            )
            if target_date in holiday_dates:
                return True
            if (
                work_days == 5
                and off_days == 2
                and anchor_date.weekday() == 0
                and target_date in workday_weekends
            ):
                return False

        total_cycle = work_days + off_days
        if total_cycle <= 0 or off_days <= 0:
            return False
        if work_days <= 0:
            return True

        day_index = (target_date - anchor_date).days % total_cycle
        return day_index >= work_days

    def _get_phytolamp_on_time(self, now: datetime) -> time:
        """Точное утреннее время включения подсветки (основное или собственное)."""
        is_weekend = self._is_weekend_day(now)
        if bool(
            self.get_setting(
                "phytolamp_use_main_settings",
                DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
            )
        ):
            return self._get_up_limit_time(now)
        return self._parse_time(
            self.get_time_str(
                "phytolamp_on_time_weekend" if is_weekend else "phytolamp_on_time_workday",
                DEFAULT_PHYTOLAMP_ON_WEEKEND if is_weekend else DEFAULT_PHYTOLAMP_ON_WORKDAY,
            )
        )

    def _get_phytolamp_off_time(self) -> time:
        """Точное вечернее время выключения подсветки (основное или собственное)."""
        if bool(
            self.get_setting(
                "phytolamp_use_main_settings",
                DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
            )
        ):
            return self._get_down_limit_time()
        return self._parse_time(
            self.get_time_str("phytolamp_off_time", DEFAULT_PHYTOLAMP_OFF_TIME)
        )

    def _is_within_phytolamp_time_bounds(self, now: datetime | None = None) -> bool:
        """Проверка: находимся ли мы внутри дневного окна работы подсветки."""
        if now is None:
            now = dt_util.now()
        if self._last_day_phytolamp_off == now.day:
            return False
        current_time = now.time()
        on_time = self._get_phytolamp_on_time(now)
        off_time = self._get_phytolamp_off_time()
        return on_time <= current_time < off_time

    def _get_up_limit_time(self, now: datetime) -> time:
        is_weekend = self._is_weekend_day(now)
        return self._parse_time(
            self.get_time_str(
                "up_time_weekend" if is_weekend else "up_time_workday",
                DEFAULT_OPEN_TIME_WEEKEND if is_weekend else DEFAULT_OPEN_TIME_WORKDAY,
            )
        )

    def _get_down_limit_time(self) -> time:
        return self._parse_time(self.get_time_str("down_time", DEFAULT_CLOSE_TIME))

    def _get_effective_open_time(self, now: datetime) -> time:
        """Эффективное время открытия сегодня: max(sunrise, up_limit_time) при включённом рассвете."""
        up_limit_time = self._get_up_limit_time(now)
        if self.get_bool("open_at_sunrise", DEFAULT_OPEN_AT_SUNRISE):
            rising = self._get_sun_event_time("next_rising", now)
            if rising and rising > up_limit_time:
                return rising
        return up_limit_time

    def _get_effective_close_time(self, now: datetime) -> time:
        """Эффективное время закрытия сегодня: min(sunset, down_limit_time) при включённом закате."""
        down_limit_time = self._get_down_limit_time()
        if self.get_bool("close_at_sunset", DEFAULT_CLOSE_AT_SUNSET):
            setting = self._get_sun_event_time("next_setting", now)
            if setting and setting < down_limit_time:
                return setting
        return down_limit_time

    def _is_within_time_bounds(self, now: datetime) -> bool:
        """Проверка: находимся ли мы внутри дневного окна работы автоматики (п. 1.2 ТЗ)."""
        if self._last_day_closed == now.day:
            return False

        current_time = now.time()
        effective_open = self._get_effective_open_time(now)
        effective_close = self._get_effective_close_time(now)

        return effective_open <= current_time < effective_close

    def update_next_action_text(self, now: datetime | None = None) -> None:
        """Обновить текстовый сенсор следующего действия по всем активным модулям и его атрибуты."""
        if not self._next_action_sensor:
            return
        if now is None:
            now = dt_util.now()

        candidates: list[tuple[datetime, int, str]] = []
        attrs: dict[str, str] = {}

        # ── 1. Шторы (blind_action) ──
        if self.has_mode(MODE_BLINDS) and self.all_blinds:
            effective_open = self._get_effective_open_time(now)
            effective_close = self._get_effective_close_time(now)

            if (
                self._last_day_closed != now.day
                and now.time() < effective_close
                and (self._last_day_opened == now.day or now.time() >= effective_open)
            ):
                dt_blind = now.replace(
                    hour=effective_close.hour,
                    minute=effective_close.minute,
                    second=0,
                    microsecond=0,
                )
                b_time_str = effective_close.strftime("%H:%M")
                blind_action = self.tr_sensor_state(
                    "next_action", "short_will_close", time=b_time_str
                )
                blind_full = self.tr_sensor_state(
                    "next_action", "will_close", time=b_time_str
                )
            else:
                if self._last_day_opened != now.day and now.time() < effective_open:
                    dt_blind = now.replace(
                        hour=effective_open.hour,
                        minute=effective_open.minute,
                        second=0,
                        microsecond=0,
                    )
                else:
                    tomorrow = now + timedelta(days=1)
                    open_tom = self._get_effective_open_time(tomorrow)
                    dt_blind = tomorrow.replace(
                        hour=open_tom.hour,
                        minute=open_tom.minute,
                        second=0,
                        microsecond=0,
                    )
                b_time_str = dt_blind.strftime("%H:%M")
                blind_action = self.tr_sensor_state(
                    "next_action", "short_will_open", time=b_time_str
                )
                blind_full = self.tr_sensor_state(
                    "next_action", "will_open", time=b_time_str
                )
            attrs["blind_action"] = blind_action
            candidates.append((dt_blind, 1, blind_full))

        # ── 2. Подсветка растений (light_action) ──
        if self.has_mode(MODE_PHYTOLAMP) and self.phytolamps:
            phytolamp_on = self._get_phytolamp_on_time(now)
            phytolamp_off = self._get_phytolamp_off_time()

            if (
                self._last_day_phytolamp_off != now.day
                and now.time() < phytolamp_off
                and (
                    self._last_day_phytolamp_on == now.day
                    or now.time() >= phytolamp_on
                )
            ):
                dt_light = now.replace(
                    hour=phytolamp_off.hour,
                    minute=phytolamp_off.minute,
                    second=0,
                    microsecond=0,
                )
                l_time_str = phytolamp_off.strftime("%H:%M")
                light_action = self.tr_sensor_state(
                    "next_action", "short_light_will_off", time=l_time_str
                )
                light_full = self.tr_sensor_state(
                    "next_action", "light_will_off", time=l_time_str
                )
            else:
                if (
                    self._last_day_phytolamp_on != now.day
                    and now.time() < phytolamp_on
                ):
                    dt_light = now.replace(
                        hour=phytolamp_on.hour,
                        minute=phytolamp_on.minute,
                        second=0,
                        microsecond=0,
                    )
                else:
                    tomorrow = now + timedelta(days=1)
                    on_tom = self._get_phytolamp_on_time(tomorrow)
                    dt_light = tomorrow.replace(
                        hour=on_tom.hour,
                        minute=on_tom.minute,
                        second=0,
                        microsecond=0,
                    )
                l_time_str = dt_light.strftime("%H:%M")
                light_action = self.tr_sensor_state(
                    "next_action", "short_light_will_on", time=l_time_str
                )
                light_full = self.tr_sensor_state(
                    "next_action", "light_will_on", time=l_time_str
                )
            attrs["light_action"] = light_action
            candidates.append((dt_light, 2, light_full))

        # ── 3. Полив растений (watering_action) ──
        if self.has_mode(MODE_WATERING) and self.watering_valves:
            if not self.get_bool("watering_enabled", DEFAULT_WATERING_ENABLED):
                watering_action = self.tr_sensor_state("watering_status", "disabled")
            elif self.get_bool("watering_skip_next", DEFAULT_WATERING_SKIP_NEXT):
                watering_action = self.tr_sensor_state("watering_status", "skip_next")
            else:
                excl_morning = self.excluded_watering_morning
                excl_evening = self.excluded_watering_evening
                has_morning = False
                has_evening = False
                for v in self.watering_valves:
                    cfg = self.get_watering_zone_config(v)
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
                    watering_action = self.tr_sensor_state(
                        "watering_status", "no_active_zones"
                    )
                else:
                    m_time = self._parse_time(
                        self.get_time_str(
                            "watering_morning_time", DEFAULT_WATERING_MORNING_TIME
                        )
                    )
                    e_time = self._parse_time(
                        self.get_time_str(
                            "watering_evening_time", DEFAULT_WATERING_EVENING_TIME
                        )
                    )
                    w_slots: list[datetime] = []
                    if has_morning:
                        if (
                            self._last_day_watering_morning != now.day
                            and now.time() < m_time
                        ):
                            w_slots.append(
                                now.replace(
                                    hour=m_time.hour,
                                    minute=m_time.minute,
                                    second=0,
                                    microsecond=0,
                                )
                            )
                        else:
                            w_slots.append(
                                (now + timedelta(days=1)).replace(
                                    hour=m_time.hour,
                                    minute=m_time.minute,
                                    second=0,
                                    microsecond=0,
                                )
                            )
                    if has_evening:
                        if (
                            self._last_day_watering_evening != now.day
                            and now.time() < e_time
                        ):
                            w_slots.append(
                                now.replace(
                                    hour=e_time.hour,
                                    minute=e_time.minute,
                                    second=0,
                                    microsecond=0,
                                )
                            )
                        else:
                            w_slots.append(
                                (now + timedelta(days=1)).replace(
                                    hour=e_time.hour,
                                    minute=e_time.minute,
                                    second=0,
                                    microsecond=0,
                                )
                            )
                    dt_watering = min(w_slots)
                    w_time_str = dt_watering.strftime("%H:%M")
                    watering_action = self.tr_sensor_state(
                        "next_action", "short_watering_will_on", time=w_time_str
                    )
                    watering_full = self.tr_sensor_state(
                        "next_action", "watering_will_on", time=w_time_str
                    )
                    candidates.append((dt_watering, 3, watering_full))
            attrs["watering_action"] = watering_action

        if candidates:
            candidates.sort(key=lambda item: (item[0], item[1]))
            action_str = candidates[0][2]
        else:
            action_str = self.tr_sensor_state("next_action", "no_actions")

        self._next_action_sensor.update_state(action_str, attrs)

    def recalculate_schedule_flags(self, now: datetime | None = None) -> None:
        """Пересчитать флаги открытия/закрытия текущего дня при старте и при изменении расписания в UI."""
        if now is None:
            now = dt_util.now()
        current_time = now.time()
        effective_open = self._get_effective_open_time(now)
        effective_close = self._get_effective_close_time(now)

        if current_time >= effective_open:
            self._last_day_opened = now.day
        else:
            self._last_day_opened = -1

        if current_time >= effective_close:
            self._last_day_closed = now.day
        else:
            self._last_day_closed = -1

        if self.has_mode(MODE_PHYTOLAMP):
            phytolamp_on = self._get_phytolamp_on_time(now)
            phytolamp_off = self._get_phytolamp_off_time()
            if current_time >= phytolamp_on:
                self._last_day_phytolamp_on = now.day
            else:
                self._last_day_phytolamp_on = -1
            if current_time >= phytolamp_off:
                self._last_day_phytolamp_off = now.day
            else:
                self._last_day_phytolamp_off = -1

        if self.has_mode(MODE_WATERING):
            m_time = self._parse_time(
                self.get_time_str("watering_morning_time", DEFAULT_WATERING_MORNING_TIME)
            )
            e_time = self._parse_time(
                self.get_time_str("watering_evening_time", DEFAULT_WATERING_EVENING_TIME)
            )
            self._last_day_watering_morning = now.day if current_time >= m_time else -1
            self._last_day_watering_evening = now.day if current_time >= e_time else -1
            self._refresh_watering_sensors()

        self.update_next_action_text(now)

    async def _setup_time_listeners(self):
        self.recalculate_schedule_flags()

        @callback
        def _check_schedule(now: datetime | None = None):
            if now is None:
                now = dt_util.now()
            else:
                now = dt_util.as_local(now)
            current_time = now.time()

            effective_open = self._get_effective_open_time(now)
            effective_close = self._get_effective_close_time(now)

            # ── 1. Утреннее открытие и 2. Вечернее закрытие штор (п. 1.1 и 1.2 ТЗ) ──
            if self.has_mode(MODE_BLINDS) and self.blinds:
                if self._last_day_opened != now.day:
                    if effective_open <= current_time < effective_close:
                        self._last_day_opened = now.day
                        _LOGGER.info(
                            "%s",
                            self.tr_log(
                                "log_schedule_open",
                                time=effective_open.strftime("%H:%M"),
                            ),
                        )
                        self.hass.async_create_task(self.async_set_position(self.get_up_limit()))

                if self._last_day_closed != now.day:
                    if current_time >= effective_close:
                        self._last_day_closed = now.day
                        self._is_sun_protecting = False
                        _LOGGER.info(
                            "%s",
                            self.tr_log(
                                "log_schedule_close",
                                time=effective_close.strftime("%H:%M"),
                            ),
                        )
                        self.hass.async_create_task(self.async_set_position(self.get_down_limit()))

            # ── 3. Расписание подсветки растений (точно заданное время) ──
            if self.has_mode(MODE_PHYTOLAMP) and self.phytolamps:
                phytolamp_on = self._get_phytolamp_on_time(now)
                phytolamp_off = self._get_phytolamp_off_time()
                use_main = bool(
                    self.get_setting(
                        "phytolamp_use_main_settings",
                        DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                    )
                )

                if self._last_day_phytolamp_on != now.day:
                    if phytolamp_on <= current_time < phytolamp_off:
                        self._last_day_phytolamp_on = now.day
                        sun_blocks = (
                            (self.has_mode(MODE_SUN_PROTECT) and self._is_sun_protecting)
                            if use_main
                            else self._is_phytolamp_sun_off
                        )
                        if not sun_blocks:
                            _LOGGER.info(
                                "%s",
                                self.tr_log(
                                    "log_schedule_phytolamp_on",
                                    time=phytolamp_on.strftime("%H:%M"),
                                ),
                            )
                            self.hass.async_create_task(self.async_set_phytolamp(True))

                if self._last_day_phytolamp_off != now.day:
                    if current_time >= phytolamp_off:
                        self._last_day_phytolamp_off = now.day
                        self._is_phytolamp_sun_off = False
                        if self._phytolamp_delay_unsub is not None:
                            self._phytolamp_delay_unsub()
                            self._phytolamp_delay_unsub = None
                        _LOGGER.info(
                            "%s",
                            self.tr_log(
                                "log_schedule_phytolamp_off",
                                time=phytolamp_off.strftime("%H:%M"),
                            ),
                        )
                        self.hass.async_create_task(self.async_set_phytolamp(False))

            # ── 3.1. Расписание полива растений (утро и вечер) ──
            if self.has_mode(MODE_WATERING) and self.watering_valves:
                m_time = self._parse_time(
                    self.get_time_str(
                        "watering_morning_time", DEFAULT_WATERING_MORNING_TIME
                    )
                )
                e_time = self._parse_time(
                    self.get_time_str(
                        "watering_evening_time", DEFAULT_WATERING_EVENING_TIME
                    )
                )
                if self._last_day_watering_morning != now.day and current_time >= m_time:
                    self._last_day_watering_morning = now.day
                    if (
                        current_time.hour == m_time.hour
                        and current_time.minute == m_time.minute
                    ):
                        self._start_watering_cycle("morning")

                if self._last_day_watering_evening != now.day and current_time >= e_time:
                    self._last_day_watering_evening = now.day
                    if (
                        current_time.hour == e_time.hour
                        and current_time.minute == e_time.minute
                    ):
                        self._start_watering_cycle("evening")

            # ── 4. Обновление текстового сенсора следующего действия ──
            self.update_next_action_text(now)

        unsub_time = async_track_time_change(self.hass, _check_schedule, second=0)
        self._unsub_listeners.append(unsub_time)

        # Также слушаем смену состояния sun.sun (рассвет/закат), чтобы реагировать без задержки до следующей минуты
        sun_sensor = self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)

        @callback
        def _on_sun_state_change(event: Event):
            old_state = event.data.get("old_state")
            new_state = event.data.get("new_state")
            if old_state and new_state and old_state.state != new_state.state:
                _check_schedule()

        unsub_sun = async_track_state_change_event(self.hass, [sun_sensor], _on_sun_state_change)
        self._unsub_listeners.append(unsub_sun)
        self.update_next_action_text()

    # ────────────────────────────────────────────────────────────
    #  БЛОК 2: Защита от солнца, Погода, Освещенность (п. 2.1.1 — 2.1.4 ТЗ)
    # ────────────────────────────────────────────────────────────

    async def _evaluate_sun_protection(self):
        """Вычисление состояния защиты от солнца с приоритетом освещённости."""
        now = dt_util.now()

        # Защита работает только в разрешённом дневном окне (условия п. 1.2 ТЗ)
        if not self._is_within_time_bounds(now):
            if self._is_sun_protecting:
                self._is_sun_protecting = False
            return

        sun_sensor = self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)
        sun_state = self.hass.states.get(sun_sensor)

        if not sun_state or sun_state.state != "above_horizon":
            target_protection = False
        else:
            # 2.1.1 Базовые условия по азимуту и высоте солнца
            cur_azimuth = float(sun_state.attributes.get("azimuth", 0))
            cur_elevation = float(sun_state.attributes.get("elevation", 0))

            thr_azimuth = self.get_number("sun_azimuth", DEFAULT_SUN_AZIMUTH)
            thr_elevation = self.get_number("sun_elevation", DEFAULT_SUN_ELEVATION)

            sun_in_sector = (cur_azimuth >= thr_azimuth) and (cur_elevation >= thr_elevation)

            if not sun_in_sector:
                # При выходе солнца из сектора (снижении за установленную высоту) — шторы открываются
                target_protection = False
            else:
                use_forecast = bool(self.get_setting("use_forecast", False))
                use_illuminance = bool(self.get_setting("use_illuminance", False))

                weather_allows = True
                if use_forecast:
                    weather_sensor = self.get_setting("forecast_sensor")
                    if weather_sensor:
                        w_state = self.hass.states.get(weather_sensor)
                        forecasts = self.get_setting("forecasts", DEFAULT_FORECASTS)
                        if w_state and w_state.state not in forecasts:
                            weather_allows = False

                lux_state_decision = None
                if use_illuminance:
                    lux_sensor = self.get_setting("illuminance_sensor")
                    if lux_sensor:
                        l_state = self.hass.states.get(lux_sensor)
                        if l_state and l_state.state not in ("unknown", "unavailable"):
                            try:
                                cur_lux = float(l_state.state)
                                max_lux = self.get_number("max_illuminance", DEFAULT_MAX_ILLUMINANCE)
                                min_lux = self.get_number("min_illuminance", DEFAULT_MIN_ILLUMINANCE)

                                if cur_lux >= max_lux:
                                    lux_state_decision = True
                                elif cur_lux <= min_lux:
                                    lux_state_decision = False
                            except ValueError:
                                pass

                # ── 2.1.1 – 2.1.4 Логика выбора с приоритетом освещённости ──
                if use_illuminance:
                    if lux_state_decision is not None:
                        # Чёткое решение от датчика освещённости (>= max_lux или <= min_lux)
                        target_protection = lux_state_decision
                    else:
                        # Между min_lux и max_lux сохраняем текущее состояние (гистерезис)
                        target_protection = self._is_sun_protecting
                elif use_forecast:
                    target_protection = weather_allows
                else:
                    target_protection = True

        if target_protection == self._is_sun_protecting:
            return

        self._is_sun_protecting = target_protection

        use_main_phytolamp = self.has_mode(MODE_PHYTOLAMP) and bool(
            self.get_setting(
                "phytolamp_use_main_settings",
                DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
            )
        )

        if target_protection:
            _LOGGER.info("%s", self.tr_log("log_sun_protect_on"))
            await self.async_set_position(self.get_down_limit(), self.protect_blinds)
            if use_main_phytolamp:
                self._schedule_phytolamp_with_movement_delay(turn_on=False)
        else:
            _LOGGER.info("%s", self.tr_log("log_sun_protect_off"))
            await self.async_set_position(self.get_up_limit(), self.protect_blinds)
            if use_main_phytolamp and self._is_within_phytolamp_time_bounds(now):
                self._schedule_phytolamp_with_movement_delay(turn_on=True)

    async def _setup_sun_protect_listeners(self):
        immediate_entities = [self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)]
        if self.get_setting("use_forecast") and self.get_setting("forecast_sensor"):
            immediate_entities.append(self.get_setting("forecast_sensor"))

        @callback
        def async_handle_sun_or_weather_change(event: Event):
            self.hass.async_create_task(self._evaluate_sun_protection())

        unsub_immediate = async_track_state_change_event(
            self.hass, immediate_entities, async_handle_sun_or_weather_change
        )
        self._unsub_listeners.append(unsub_immediate)

        # Для датчика освещённости применяется антидребезг (illuminance_delay)
        if self.get_setting("use_illuminance") and self.get_setting("illuminance_sensor"):
            lux_sensor = self.get_setting("illuminance_sensor")

            @callback
            def async_handle_illuminance_change(event: Event):
                if self._sun_protect_unsub is not None:
                    self._sun_protect_unsub()
                    self._sun_protect_unsub = None

                delay_str = self.get_time_str("illuminance_delay", DEFAULT_ILLUMINANCE_DELAY)
                parsed_delay = self._parse_time(delay_str)
                delay_sec = parsed_delay.hour * 3600 + parsed_delay.minute * 60 + parsed_delay.second

                async def _async_delayed_eval(_now):
                    self._sun_protect_unsub = None
                    await self._evaluate_sun_protection()

                if delay_sec > 0:
                    self._sun_protect_unsub = async_call_later(
                        self.hass, delay_sec, _async_delayed_eval
                    )
                else:
                    self.entry.async_create_background_task(
                        self.hass,
                        self._evaluate_sun_protection(),
                        "loggia_sun_protect_eval",
                    )

            unsub_lux = async_track_state_change_event(
                self.hass, [lux_sensor], async_handle_illuminance_change
            )
            self._unsub_listeners.append(unsub_lux)

    # ────────────────────────────────────────────────────────────
    #  БЛОК 2.1: Собственная логика подсветки растений (при своих настройках)
    # ────────────────────────────────────────────────────────────

    async def _evaluate_phytolamp_custom(self) -> None:
        """Вычисление состояния подсветки растений по её собственным углам солнца, погоде и освещённости."""
        if not self.needs_phytolamp_subdevice:
            return
        now = dt_util.now()
        if not self._is_within_phytolamp_time_bounds(now):
            if self._is_phytolamp_sun_off:
                self._is_phytolamp_sun_off = False
            return

        use_sun = bool(self.get_setting("phytolamp_use_sun", False))
        use_forecast = bool(self.get_setting("phytolamp_use_forecast", False))
        use_illuminance = bool(self.get_setting("phytolamp_use_illuminance", False))
        if not (use_sun or use_forecast or use_illuminance):
            return

        sun_sensor = self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)
        sun_state = self.hass.states.get(sun_sensor)

        if not sun_state or sun_state.state != "above_horizon":
            # Солнце за горизонтом, но мы внутри дневного окна работы подсветки -> подсветка должна гореть
            target_sun_enough = False
        else:
            sun_in_sector = True
            if use_sun:
                cur_azimuth = float(sun_state.attributes.get("azimuth", 0))
                cur_elevation = float(sun_state.attributes.get("elevation", 0))
                thr_azimuth = self.get_number("phytolamp_sun_azimuth", DEFAULT_SUN_AZIMUTH)
                thr_elevation = self.get_number("phytolamp_sun_elevation", DEFAULT_SUN_ELEVATION)
                sun_in_sector = (cur_azimuth >= thr_azimuth) and (cur_elevation >= thr_elevation)

            if not sun_in_sector:
                target_sun_enough = False
            else:
                weather_allows = True
                if use_forecast:
                    weather_sensor = self.get_setting("phytolamp_forecast_sensor") or self.get_setting("forecast_sensor")
                    if weather_sensor:
                        w_state = self.hass.states.get(weather_sensor)
                        forecasts = self.get_setting("phytolamp_forecasts", DEFAULT_FORECASTS)
                        if w_state and w_state.state not in forecasts:
                            weather_allows = False

                lux_state_decision = None
                if use_illuminance:
                    lux_sensor = self.phytolamp_illuminance_sensor
                    if lux_sensor:
                        l_state = self.hass.states.get(lux_sensor)
                        if l_state and l_state.state not in ("unknown", "unavailable"):
                            try:
                                cur_lux = float(l_state.state)
                                max_lux = self.get_number("phytolamp_max_illuminance", DEFAULT_MAX_ILLUMINANCE)
                                min_lux = self.get_number("phytolamp_min_illuminance", DEFAULT_MIN_ILLUMINANCE)
                                if cur_lux >= max_lux:
                                    lux_state_decision = True
                                elif cur_lux <= min_lux:
                                    lux_state_decision = False
                            except ValueError:
                                pass

                if use_illuminance:
                    if lux_state_decision is not None:
                        target_sun_enough = lux_state_decision
                    else:
                        target_sun_enough = self._is_phytolamp_sun_off
                elif use_forecast:
                    target_sun_enough = weather_allows
                else:
                    target_sun_enough = True

        if target_sun_enough == self._is_phytolamp_sun_off:
            return

        self._is_phytolamp_sun_off = target_sun_enough

        if target_sun_enough:
            _LOGGER.info("%s", self.tr_log("log_phytolamp_custom_off"))
            await self.async_set_phytolamp(False)
        else:
            _LOGGER.info("%s", self.tr_log("log_phytolamp_custom_on"))
            await self.async_set_phytolamp(True)

    async def _setup_phytolamp_custom_listeners(self) -> None:
        """Подписка на датчики солнца, погоды и освещённости для собственных настроек подсветки."""
        if not self.needs_phytolamp_subdevice:
            return
        use_sun = bool(self.get_setting("phytolamp_use_sun", False))
        use_forecast = bool(self.get_setting("phytolamp_use_forecast", False))
        use_illuminance = bool(self.get_setting("phytolamp_use_illuminance", False))
        if not (use_sun or use_forecast or use_illuminance):
            return

        immediate_entities = [self.get_setting("sun_sensor", DEFAULT_SUN_SENSOR)]
        if use_forecast:
            weather_sensor = self.get_setting("phytolamp_forecast_sensor") or self.get_setting("forecast_sensor")
            if weather_sensor and weather_sensor not in immediate_entities:
                immediate_entities.append(weather_sensor)

        @callback
        def async_handle_phytolamp_sun_or_weather(event: Event):
            self.hass.async_create_task(self._evaluate_phytolamp_custom())

        unsub_imm = async_track_state_change_event(
            self.hass, immediate_entities, async_handle_phytolamp_sun_or_weather
        )
        self._unsub_listeners.append(unsub_imm)

        if use_illuminance and self.phytolamp_illuminance_sensor:
            lux_sensor = self.phytolamp_illuminance_sensor

            @callback
            def async_handle_phytolamp_lux_change(event: Event):
                if self._phytolamp_lux_unsub is not None:
                    self._phytolamp_lux_unsub()
                    self._phytolamp_lux_unsub = None

                delay_str = self.get_time_str("phytolamp_illuminance_delay", DEFAULT_ILLUMINANCE_DELAY)
                parsed_delay = self._parse_time(delay_str)
                delay_sec = parsed_delay.hour * 3600 + parsed_delay.minute * 60 + parsed_delay.second

                async def _async_delayed_phytolamp_eval(_now):
                    self._phytolamp_lux_unsub = None
                    await self._evaluate_phytolamp_custom()

                if delay_sec > 0:
                    self._phytolamp_lux_unsub = async_call_later(
                        self.hass, delay_sec, _async_delayed_phytolamp_eval
                    )
                else:
                    self.entry.async_create_background_task(
                        self.hass,
                        self._evaluate_phytolamp_custom(),
                        "loggia_phytolamp_custom_eval",
                    )

            unsub_lux = async_track_state_change_event(
                self.hass, [lux_sensor], async_handle_phytolamp_lux_change
            )
            self._unsub_listeners.append(unsub_lux)

    # ────────────────────────────────────────────────────────────
    #  БЛОК 4: Универсальное голосовое управление (Яндекс / Assist / TTS)
    # ────────────────────────────────────────────────────────────

    async def _async_speak(
        self, tts_msg: str, target_players: list[str] | str | None = None
    ) -> None:
        """Озвучить сообщение через Яндекс.Станцию или стандартный движок TTS Home Assistant."""
        raw_players = target_players or self.get_setting("yandex_media_player", []) or []
        if isinstance(raw_players, str):
            players = [raw_players] if raw_players else []
        else:
            players = [p for p in raw_players if p]
        if not players:
            _LOGGER.warning(
                "%s", self.tr_log("log_tts_no_player", message=tts_msg)
            )
            return

        # volume = int(self.get_number("yandex_volume", DEFAULT_YANDEX_VOLUME)) / 100.0
        voice_engine = self.get_setting("voice_engine", DEFAULT_VOICE_ENGINE)
        tts_entity = self.get_setting("tts_entity")

        try:
            # Если выбран стандартный TTS Home Assistant (Assist / Custom) и указан движок tts.*
            if voice_engine != VOICE_ENGINE_YANDEX and tts_entity:
                # await self.hass.services.async_call(
                #     "media_player",
                #     "volume_set",
                #     {"entity_id": players, "volume_level": volume},
                # )
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": tts_entity,
                        "media_player_entity_id": players,
                        "message": tts_msg,
                    },
                )
                return

            # Режим по умолчанию (Яндекс.Станция — media_content_type: text)
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": players,
                    "media_content_id": tts_msg,
                    "media_content_type": "text",
                    # "extra": {"volume_level": volume},
                },
            )
        except Exception as err:
            _LOGGER.error(
                "%s",
                self.tr_log("log_tts_error", players=players, error=err),
            )

    def _build_position_tts_message(self) -> str:
        """Сформировать голосовое сообщение о положении каждой шторы (с переводом из translations/*.json)."""
        items = []
        for blind in self.blinds:
            st = self.hass.states.get(blind)
            name = st.name if st and st.name else blind
            pos = st.attributes.get(ATTR_CURRENT_POSITION) if st else None
            if pos is None:
                items.append(
                    self.tr_sensor_state(
                        "status",
                        "tts_pos_unknown",
                        name=name,
                    )
                )
            else:
                try:
                    p_val = int(pos)
                    if p_val == 0:
                        items.append(
                            self.tr_sensor_state(
                                "status",
                                "tts_pos_closed",
                                name=name,
                            )
                        )
                    elif p_val == 100:
                        items.append(
                            self.tr_sensor_state(
                                "status",
                                "tts_pos_open",
                                name=name,
                            )
                        )
                    else:
                        items.append(
                            self.tr_sensor_state(
                                "status",
                                "tts_pos_pct",
                                name=name,
                                pos=p_val,
                            )
                        )
                except (TypeError, ValueError):
                    items.append(
                        self.tr_sensor_state(
                            "status",
                            "tts_pos_unknown",
                            name=name,
                        )
                    )
        return (
            ". ".join(items)
            if items
            else self.tr_sensor_state("status", "tts_no_blinds")
        )

    def _format_except_blinds(self, count: int) -> str:
        """Получить локализованное числительное ('одной шторы', 'двух штор' / 'one blind', 'two blinds') из translations/*.json."""
        if 1 <= count <= 10:
            return self.tr_sensor_state(
                "status", f"except_{count}", count=count
            )
        return self.tr_sensor_state(
            "status", "except_many", count=count
        )

    def _build_status_tts_message(self) -> str:
        """Сформировать сводное голосовое сообщение о состоянии штор (с переводом из translations/*.json)."""
        if not self.blinds:
            return self.tr_sensor_state("status", "tts_no_blinds")
        up_limit = self.get_up_limit()
        down_limit = self.get_down_limit()
        tolerance = 5

        open_count = 0
        closed_count = 0

        for blind in self.blinds:
            st = self.hass.states.get(blind)
            pos = st.attributes.get(ATTR_CURRENT_POSITION) if st else None
            try:
                p_val = int(pos) if pos is not None else -999
            except (TypeError, ValueError):
                p_val = -999

            if abs(p_val - up_limit) <= tolerance:
                open_count += 1
            if abs(p_val - down_limit) <= tolerance:
                closed_count += 1

        total = len(self.blinds)
        if open_count >= closed_count:
            if open_count == total:
                return self.tr_sensor_state("status", "tts_all_open")
            except_str = self._format_except_blinds(total - open_count)
            return self.tr_sensor_state(
                "status",
                "tts_all_open_except",
                except_text=except_str,
            )
        else:
            if closed_count == total:
                return self.tr_sensor_state("status", "tts_all_closed")
            except_str = self._format_except_blinds(total - closed_count)
            return self.tr_sensor_state(
                "status",
                "tts_all_closed_except",
                except_text=except_str,
            )

    async def _setup_yandex_listeners(self):
        @callback
        def async_handle_voice_event(event: Event):
            intent_data = event.data or {}
            raw_text = (
                intent_data.get("text")
                or intent_data.get("command")
                or intent_data.get("phrase")
                or intent_data.get("utterance")
                or ""
            )
            text = str(raw_text).strip().rstrip(".!?, ").lower()
            if not text:
                return

            speaker_id = intent_data.get("entity_id") or intent_data.get("media_player")

            raw_players = self.get_setting("yandex_media_player", []) or []
            if isinstance(raw_players, str):
                media_players = [raw_players] if raw_players else []
            else:
                media_players = [p for p in raw_players if p]

            # Если в событии пришла конкретная колонка из списка — отвечаем на неё;
            # иначе отвечаем на выбранные в настройках колонки (или на speaker_id, если список в настройках пуст)
            if speaker_id and isinstance(speaker_id, str) and speaker_id.startswith("media_player."):
                if media_players and speaker_id in media_players:
                    target_speaker = [speaker_id]
                elif not media_players:
                    target_speaker = [speaker_id]
                else:
                    target_speaker = media_players
            else:
                target_speaker = media_players

            def _parse_phrases(setting_key: str, default_val: str) -> list[str]:
                raw_val = self.get_setting(setting_key, default_val) or default_val
                return [
                    p.strip().rstrip(".!?, ").lower()
                    for p in str(raw_val).split(";")
                    if p.strip()
                ]

            open_phrases = _parse_phrases(
                "yandex_intent_open",
                self.tr_sensor_state("status", "intent_open_default", DEFAULT_YANDEX_INTENT_OPEN),
            )
            close_phrases = _parse_phrases(
                "yandex_intent_close",
                self.tr_sensor_state("status", "intent_close_default", DEFAULT_YANDEX_INTENT_CLOSE),
            )
            pos_phrases = _parse_phrases(
                "yandex_intent_position",
                self.tr_sensor_state("status", "intent_position_default", DEFAULT_YANDEX_INTENT_POSITION),
            )
            status_phrases = _parse_phrases(
                "yandex_intent_status",
                self.tr_sensor_state("status", "intent_status_default", DEFAULT_YANDEX_INTENT_STATUS),
            )

            _LOGGER.info(
                "%s",
                self.tr_log(
                    "log_voice_event",
                    event=event.event_type,
                    text=text,
                    target=target_speaker,
                ),
            )

            if text in open_phrases:
                self.hass.async_create_task(self.async_set_position(self.get_up_limit()))
            elif text in close_phrases:
                self.hass.async_create_task(self.async_set_position(self.get_down_limit()))
            elif text in pos_phrases:
                self.hass.async_create_task(
                    self._async_speak(self._build_position_tts_message(), target_speaker)
                )
            elif text in status_phrases:
                self.hass.async_create_task(
                    self._async_speak(self._build_status_tts_message(), target_speaker)
                )

        # Всегда слушаем yandex_intent + кастомное событие (если задано другое)
        events_to_listen = {DEFAULT_VOICE_EVENT}
        custom_event = str(self.get_setting("voice_event", DEFAULT_VOICE_EVENT)).strip()
        if custom_event:
            events_to_listen.add(custom_event)

        for evt_name in events_to_listen:
            unsub = self.hass.bus.async_listen(evt_name, async_handle_voice_event)
            self._unsub_listeners.append(unsub)

    # ────────────────────────────────────────────────────────────
    #  БЛОК 3: Математика слайдера
    # ────────────────────────────────────────────────────────────

    def _is_fast_swipe(self, speed: float | None, time_delta_ms: float | None) -> bool:
        fast_speed = float(self.get_number("slider_fast_speed", DEFAULT_SLIDER_FAST_SPEED))
        fast_time = float(self.get_number("slider_fast_time_ms", DEFAULT_SLIDER_FAST_TIME_MS))
        if speed is not None:
            return abs(speed) >= fast_speed
        if time_delta_ms is not None:
            return time_delta_ms <= fast_time
        return False

    def _calculate_target_position(
        self, direction: str, displacement: float | None = None, speed: float | None = None, time_delta_ms: float | None = None
    ) -> int:
        slider_mode = self.get_setting("slider_mode", DEFAULT_SLIDER_MODE)
        up_limit = self.get_up_limit()
        down_limit = self.get_down_limit()
        avg_pos = self._get_average_position()
        step = int(self.get_number("slider_step", DEFAULT_SLIDER_STEP))

        if slider_mode == SLIDER_MODE_FULL:
            return up_limit if direction == "up" else down_limit

        if slider_mode == SLIDER_MODE_STEP:
            new_pos = avg_pos + step if direction == "up" else avg_pos - step
            return max(down_limit, min(up_limit, new_pos))

        if self._is_fast_swipe(speed, time_delta_ms):
            return up_limit if direction == "up" else down_limit

        if displacement is not None:
            new_pos = avg_pos + int(round(displacement))
            return max(down_limit, min(up_limit, new_pos))

        new_pos = avg_pos + step if direction == "up" else avg_pos - step
        return max(down_limit, min(up_limit, new_pos))

    def _handle_slider_action(
        self, action_cmd: str, displacement: float | None = None, speed: float | None = None, time_delta_ms: float | None = None
    ):
        payload_up = str(self.get_setting("payload_up", DEFAULT_PAYLOAD_UP))
        payload_down = str(self.get_setting("payload_down", DEFAULT_PAYLOAD_DOWN))
        payload_stop = str(self.get_setting("payload_stop", DEFAULT_PAYLOAD_STOP))

        if action_cmd == payload_stop or action_cmd == "stop":
            self.hass.async_create_task(self.async_stop())
            return
        direction = None
        if action_cmd == payload_up or (displacement is not None and displacement > 0):
            direction = "up"
        elif action_cmd == payload_down or (displacement is not None and displacement < 0):
            direction = "down"

        if direction is None:
            return

        target = self._calculate_target_position(direction, displacement, speed, time_delta_ms)
        _LOGGER.info(
            "%s",
            self.tr_log(
                "log_slider_action",
                action=action_cmd,
                displacement=displacement,
                speed=speed,
                time_ms=time_delta_ms,
                target=target,
            ),
        )
        self.hass.async_create_task(self.async_set_position(target))

    async def _setup_slider_listeners(self):
        slider_device = self.get_setting("slider_device")
        if not slider_device:
            return

        payload_up = str(self.get_setting("payload_up", DEFAULT_PAYLOAD_UP))
        payload_down = str(self.get_setting("payload_down", DEFAULT_PAYLOAD_DOWN))
        payload_stop = str(self.get_setting("payload_stop", DEFAULT_PAYLOAD_STOP))
        basic_topic = str(self.get_setting("basic_topic", DEFAULT_BASIC_TOPIC) or DEFAULT_BASIC_TOPIC).strip()

        dev_reg = dr.async_get(self.hass)
        device_entry = dev_reg.async_get(slider_device)
        device_names = set()
        if device_entry:
            if device_entry.name:
                device_names.add(device_entry.name)
            if device_entry.name_by_user:
                device_names.add(device_entry.name_by_user)

        @callback
        def async_handle_zha_event(event: Event):
            if event.data.get("device_id") != slider_device:
                return
            cmd = str(event.data.get("command") or event.data.get("args") or "")
            if payload_up in cmd:
                self._handle_slider_action(payload_up)
            elif payload_down in cmd:
                self._handle_slider_action(payload_down)
            elif payload_stop in cmd:
                self._handle_slider_action(payload_stop)

        self._unsub_listeners.append(self.hass.bus.async_listen("zha_event", async_handle_zha_event))

        if "mqtt" in self.hass.config.components:
            try:
                import time as _time
                from homeassistant.components import mqtt
                from homeassistant.helpers.event import async_call_later

                last_json_ts = 0.0
                pending_plain_unsub = None

                @callback
                def async_handle_mqtt_msg(msg):
                    nonlocal last_json_ts, pending_plain_unsub
                    if getattr(msg, "retain", False):
                        return
                    # Если в топике используется wildcard '+', проверяем принадлежность выбранному устройству
                    if "+" in basic_topic and device_names:
                        topic_parts = msg.topic.split("/")
                        if len(topic_parts) >= 2 and topic_parts[1] not in device_names:
                            return

                    raw = str(
                        msg.payload.decode("utf-8", errors="ignore")
                        if isinstance(msg.payload, bytes)
                        else msg.payload
                    ).strip()
                    if not raw:
                        return

                    if raw.startswith("{"):
                        try:
                            data = json.loads(raw)
                        except Exception:
                            return
                        action_cmd = str(data.get("action") or "").strip()
                        if not action_cmd:
                            return
                        displacement = (
                            float(data["action_slide_relative_displacement"])
                            if data.get("action_slide_relative_displacement") is not None
                            else None
                        )
                        speed = (
                            float(data["action_slide_speed"])
                            if data.get("action_slide_speed") is not None
                            else None
                        )
                        time_delta_ms = None
                        for key in ("action_slide_time_delta", "action_slide_time", "action_time"):
                            if data.get(key) is not None:
                                time_delta_ms = float(data[key])
                                break

                        last_json_ts = _time.monotonic()
                        if pending_plain_unsub is not None:
                            pending_plain_unsub()
                            pending_plain_unsub = None

                        self._handle_slider_action(action_cmd, displacement, speed, time_delta_ms)
                        return

                    # Плоское сообщение из топика .../action (без JSON-параметров свайпа):
                    # если только что пришёл JSON из базового топика устройства, игнорируем дубль
                    if _time.monotonic() - last_json_ts < 0.5:
                        return

                    if pending_plain_unsub is not None:
                        pending_plain_unsub()

                    @callback
                    def _fire_plain(_now):
                        nonlocal pending_plain_unsub
                        pending_plain_unsub = None
                        if _time.monotonic() - last_json_ts < 0.5:
                            return
                        self._handle_slider_action(raw)

                    pending_plain_unsub = async_call_later(self.hass, 0.1, _fire_plain)

                topics_to_sub = {basic_topic}
                if basic_topic.endswith("/action"):
                    topics_to_sub.add(basic_topic[: -len("/action")])

                for topic in topics_to_sub:
                    unsub = await mqtt.async_subscribe(self.hass, topic, async_handle_mqtt_msg)
                    self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.error(
                    "%s", self.tr_log("log_mqtt_error", error=err)
                )

    # ────────────────────────────────────────────────────────────
    #  Жизненный цикл
    # ────────────────────────────────────────────────────────────

    async def async_init_translations(self) -> None:
        """Загрузка переводов названий устройств, состояний и общих фраз из translations/*.json."""
        try:
            lang = self.hass.config.language or "ru"
            self._device_translations = await async_get_translations(
                self.hass, lang, "device", [DOMAIN]
            )
            self._entity_translations = await async_get_translations(
                self.hass, lang, "entity", [DOMAIN]
            )
            self._common_translations = await async_get_translations(
                self.hass, lang, "common", [DOMAIN]
            )
        except Exception:
            self._device_translations = {}
            self._entity_translations = {}
            self._common_translations = {}

    async def async_start(self):
        if not self._device_translations:
            await self.async_init_translations()

        _LOGGER.info(
            "%s", self.tr_log("log_manager_start", modes=self.modes)
        )

        # 1. Расписание
        await self._setup_time_listeners()

        # 2. Защита от солнца
        if self.has_mode(MODE_BLINDS) and MODE_SUN_PROTECT in self.modes:
            await self._setup_sun_protect_listeners()

        # 2.1. Собственные настройки подсветки растений
        if self.needs_phytolamp_subdevice:
            await self._setup_phytolamp_custom_listeners()

        # 3. Слайдер
        if self.has_mode(MODE_BLINDS) and MODE_SLIDER in self.modes:
            await self._setup_slider_listeners()

        # 3.1. Защита от перелива: если при старте какие-то клапаны уже открыты — взводим таймеры
        if self.has_mode(MODE_WATERING):
            for v_id in self.watering_valves:
                st = self.hass.states.get(v_id)
                if st and st.state == "on":
                    self._arm_valve_safety_timer(v_id)

        # 4. Яндекс (голосовые интенты отключены, управление через групповые cover)
        # if MODE_YANDEX in self.modes:
        #     await self._setup_yandex_listeners()

    async def async_stop_manager(self):
        _LOGGER.info("%s", self.tr_log("log_manager_stop"))
        if self._sun_protect_unsub is not None:
            self._sun_protect_unsub()
            self._sun_protect_unsub = None
        if self._phytolamp_lux_unsub is not None:
            self._phytolamp_lux_unsub()
            self._phytolamp_lux_unsub = None
        if self._phytolamp_delay_unsub is not None:
            self._phytolamp_delay_unsub()
            self._phytolamp_delay_unsub = None
        if self._phytolamp_verify_unsub is not None:
            self._phytolamp_verify_unsub()
            self._phytolamp_verify_unsub = None
        if self._verify_task:
            self._verify_task.cancel()
        if self._watering_task:
            self._watering_task.cancel()
        self._cancel_all_valve_safety_timers()
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
        eid = self.entry.entry_id
        for prefix in ("blinds_error", "phytolamp_error", "watering_error"):
            ir.async_delete_issue(self.hass, DOMAIN, f"{prefix}_{eid}")

    # ────────────────────────────────────────────────────────────
    #  БЛОК 4: Полив растений (Оросительная система)
    # ────────────────────────────────────────────────────────────

    @property
    def watering_valves(self) -> list[str]:
        """Список выбранных клапанов / насосов полива."""
        raw = self.get_setting("watering_valves", []) or []
        if isinstance(raw, str):
            return [raw] if raw else []
        return [v for v in raw if v]

    @property
    def watering_moisture_map(self) -> dict[str, str]:
        """Сопоставление клапан -> датчик влажности почвы."""
        raw = self.get_setting("watering_moisture_map", {}) or {}
        return dict(raw) if isinstance(raw, dict) else {}

    def _init_watering_zones_config(self) -> dict[str, dict]:
        """Инициализировать словарь индивидуальных настроек для каждого клапана полива."""
        valves = self.watering_valves
        raw_cfg = self.get_setting("watering_zones_config", {}) or {}
        old_map = dict(raw_cfg) if isinstance(raw_cfg, dict) else {}
        def_m_mode = str(
            self.get_setting("watering_default_morning_mode", DEFAULT_WATERING_MORNING_MODE)
        )
        def_m_dur = int(
            self.get_setting(
                "watering_default_morning_duration", DEFAULT_WATERING_MORNING_DURATION
            )
        )
        def_e_mode = str(
            self.get_setting("watering_default_evening_mode", DEFAULT_WATERING_EVENING_MODE)
        )
        def_e_dur = int(
            self.get_setting(
                "watering_default_evening_duration", DEFAULT_WATERING_EVENING_DURATION
            )
        )
        result: dict[str, dict] = {}
        for v in valves:
            prev = old_map.get(v) if isinstance(old_map.get(v), dict) else {}
            m_m = str(prev.get("m_mode", def_m_mode))
            if m_m not in WATERING_MODES:
                m_m = def_m_mode
            e_m = str(prev.get("e_mode", def_e_mode))
            if e_m not in WATERING_MODES:
                e_m = def_e_mode
            try:
                m_d = max(0, min(600, int(prev.get("m_duration", def_m_dur))))
            except (TypeError, ValueError):
                m_d = def_m_dur
            try:
                e_d = max(0, min(600, int(prev.get("e_duration", def_e_dur))))
            except (TypeError, ValueError):
                e_d = def_e_dur
            result[v] = {
                "m_mode": m_m,
                "m_duration": m_d,
                "e_mode": e_m,
                "e_duration": e_d,
            }
        return result

    @property
    def excluded_watering_morning(self) -> set[str]:
        """Множество клапанов, исключённых из утреннего полива по расписанию."""
        all_v = set(self.watering_valves)
        ent = self.config_entities.get("watering_morning_zones")
        if ent and hasattr(ent, "excluded_set"):
            return {v for v in ent.excluded_set if v in all_v}
        raw = self.get_setting("excluded_watering_morning", []) or []
        return {v for v in raw if v in all_v}

    @property
    def excluded_watering_evening(self) -> set[str]:
        """Множество клапанов, исключённых из вечернего полива по расписанию."""
        all_v = set(self.watering_valves)
        ent = self.config_entities.get("watering_evening_zones")
        if ent and hasattr(ent, "excluded_set"):
            return {v for v in ent.excluded_set if v in all_v}
        raw = self.get_setting("excluded_watering_evening", []) or []
        return {v for v in raw if v in all_v}

    @callback
    def set_excluded_watering_zones(
        self, period: str, excluded_ids: set[str] | list[str]
    ) -> None:
        """Обновить список исключённых направлений для утреннего или вечернего полива."""
        if period not in ("morning", "evening"):
            return
        option_key = f"excluded_watering_{period}"
        all_v = self.watering_valves
        clean_set = {v for v in excluded_ids if v in all_v}
        clean_list = [v for v in all_v if v in clean_set]

        if list(self.entry.options.get(option_key, [])) != clean_list:
            new_options = dict(self.entry.options)
            new_options[option_key] = clean_list
            self._ignore_next_options_update = True
            self.hass.config_entries.async_update_entry(self.entry, options=new_options)

        self._refresh_watering_sensors()

    @property
    def selected_watering_zone(self) -> str:
        """Текущий выбранный в селекторе клапан (по умолчанию — ACTION_STOP «Остановить»)."""
        valves = self.watering_valves
        if self._selected_watering_zone in valves:
            return self._selected_watering_zone
        self._selected_watering_zone = ACTION_STOP
        return ACTION_STOP

    @callback
    def set_selected_watering_zone(self, zone_id: str) -> None:
        """Выбрать направление для ручного полива (или вернуть на «Остановить»)."""
        valves = self.watering_valves
        if zone_id in (ACTION_STOP, WATERING_ZONE_ALL) or zone_id in valves:
            self._selected_watering_zone = (
                ACTION_STOP if zone_id == WATERING_ZONE_ALL else zone_id
            )
            zone_ent = self.config_entities.get("watering_zone")
            if zone_ent and hasattr(zone_ent, "async_refresh_options"):
                zone_ent.async_refresh_options()

    def get_watering_zone_config(self, zone_id: str | None = None) -> dict:
        """Получить настройки расписания полива (единые для всех направлений)."""
        valves = self.watering_valves
        for v in valves:
            if v not in self._watering_zones_config:
                self._watering_zones_config = self._init_watering_zones_config()
                break
        target = zone_id if (zone_id is not None and zone_id in valves) else (valves[0] if valves else "")
        if target in self._watering_zones_config:
            return dict(self._watering_zones_config[target])
        return {
            "m_mode": DEFAULT_WATERING_MORNING_MODE,
            "m_duration": DEFAULT_WATERING_MORNING_DURATION,
            "e_mode": DEFAULT_WATERING_EVENING_MODE,
            "e_duration": DEFAULT_WATERING_EVENING_DURATION,
        }

    @callback
    def update_watering_zone_setting(self, field: str, value) -> None:
        """Обновить общую настройку расписания (режим или время работы) сразу для всех направлений."""
        valves = self.watering_valves
        for v in valves:
            if v not in self._watering_zones_config:
                self._watering_zones_config = self._init_watering_zones_config()
                break

        if not valves:
            return

        for v in valves:
            self._watering_zones_config.setdefault(
                v,
                {
                    "m_mode": DEFAULT_WATERING_MORNING_MODE,
                    "m_duration": DEFAULT_WATERING_MORNING_DURATION,
                    "e_mode": DEFAULT_WATERING_EVENING_MODE,
                    "e_duration": DEFAULT_WATERING_EVENING_DURATION,
                },
            )[field] = value

        # Сохраняем матрицу зон в options без перезагрузки интеграции
        new_options = dict(self.entry.options)
        new_options["watering_zones_config"] = {
            k: dict(val) for k, val in self._watering_zones_config.items()
        }
        self._ignore_next_options_update = True
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

        self._refresh_watering_zone_dependents()

    @property
    def watering_valve_errors(self) -> list[str]:
        """Список клапанов полива с ошибками (не включились/не выключились по команде или недоступны)."""
        result: list[str] = []
        for v in self.watering_valves:
            st = self.hass.states.get(v)
            is_unavail = st is not None and st.state == "unavailable"
            if v in self._failed_watering_valves or is_unavail:
                result.append(v)
        return result

    @property
    def watering_sensor_errors(self) -> list[str]:
        """Список датчиков влажности почвы с ошибками (недоступны или вернули некорректное значение)."""
        if not bool(
            self.get_setting("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE)
        ):
            return []
        result: list[str] = []
        seen: set[str] = set()
        moisture_map = self.watering_moisture_map
        for v in self.watering_valves:
            s_id = moisture_map.get(v)
            if not s_id or s_id in seen:
                continue
            seen.add(s_id)
            st = self.hass.states.get(s_id)
            is_bad = False
            if st is not None:
                if st.state in ("unavailable", "unknown"):
                    is_bad = True
                else:
                    try:
                        float(st.state)
                    except (TypeError, ValueError):
                        is_bad = True
            if is_bad or s_id in self._failed_watering_sensors:
                result.append(s_id)
        return result

    def _get_valve_safety_timeout(
        self, valve_id: str, planned_duration: int | None = None
    ) -> int:
        """Рассчитать защитный таймаут от перелива для клапана (макс. длительность зоны + запас)."""
        if planned_duration is not None and planned_duration > 0:
            base_sec = int(planned_duration)
        else:
            z_cfg = self.get_watering_zone_config(valve_id)
            m_dur = int(z_cfg.get("m_duration", DEFAULT_WATERING_MORNING_DURATION) or 0)
            e_dur = int(z_cfg.get("e_duration", DEFAULT_WATERING_EVENING_DURATION) or 0)
            base_sec = max(m_dur, e_dur, DEFAULT_WATERING_MANUAL_DURATION)
        return max(1, base_sec) + DEFAULT_WATERING_SAFETY_MARGIN

    @callback
    def _cancel_valve_safety_timer(self, valve_id: str) -> None:
        """Отменить защитный таймер перелива для указанного клапана."""
        unsub = self._valve_safety_timers.pop(valve_id, None)
        if unsub is not None:
            unsub()

    @callback
    def _cancel_all_valve_safety_timers(self) -> None:
        """Отменить все активные защитные таймеры перелива."""
        for valve_id in list(self._valve_safety_timers.keys()):
            self._cancel_valve_safety_timer(valve_id)

    @callback
    def _arm_valve_safety_timer(
        self, valve_id: str, planned_duration: int | None = None
    ) -> None:
        """Взвести сторожевой таймер защиты от перелива для открытого клапана."""
        self._cancel_valve_safety_timer(valve_id)
        timeout_sec = self._get_valve_safety_timeout(valve_id, planned_duration)

        async def _async_on_safety_timeout(_now) -> None:
            self._valve_safety_timers.pop(valve_id, None)
            st = self.hass.states.get(valve_id)
            if st is None or st.state != "off":
                _LOGGER.warning(
                    "%s",
                    self.tr_log(
                        "log_watering_safety_cutoff",
                        valve=valve_id,
                        timeout=timeout_sec,
                    ),
                )
                try:
                    await self.hass.services.async_call(
                        "homeassistant",
                        "turn_off",
                        {"entity_id": valve_id},
                        blocking=True,
                    )
                except Exception as err:
                    self._failed_watering_valves.add(valve_id)
                    _LOGGER.error(
                        "%s",
                        self.tr_log(
                            "log_watering_valve_off_error",
                            valve=valve_id,
                            error=err,
                        ),
                    )
                await asyncio.sleep(min(3.0, max(0.5, timeout_sec * 0.1)))
                st_after = self.hass.states.get(valve_id)
                if not st_after or st_after.state != "off":
                    self._failed_watering_valves.add(valve_id)
                self._refresh_watering_sensors()
                if self.has_mode(MODE_LOGGING):
                    await self._async_handle_watering_valve_error(
                        [valve_id], is_cutoff=True
                    )

        self._valve_safety_timers[valve_id] = async_call_later(
            self.hass, float(timeout_sec), _async_on_safety_timeout
        )

    @property
    def is_watering_active(self) -> bool:
        """Проверка: идёт ли сейчас цикл полива или открыт ли хотя бы один клапан."""
        if self._watering_task and not self._watering_task.done():
            return True
        for v_id in self.watering_valves:
            st = self.hass.states.get(v_id)
            if st and st.state == "on":
                return True
        return False

    async def async_stop_watering(self) -> None:
        """Экстренная остановка активного полива и закрытие всех клапанов."""
        _LOGGER.info("%s", self.tr_log("log_watering_manual_stop"))
        if self._watering_task and not self._watering_task.done():
            self._watering_task.cancel()
            try:
                await self._watering_task
            except (asyncio.CancelledError, Exception):
                pass
        self._watering_task = None
        self._cancel_all_valve_safety_timers()

        w_status = self.config_entities.get("watering_status")
        if w_status and hasattr(w_status, "set_active_valve"):
            w_status.set_active_valve(None)

        newly_failed_valves: list[str] = []
        for valve_id in self.watering_valves:
            st = self.hass.states.get(valve_id)
            if st is None or st.state != "off":
                try:
                    await self.hass.services.async_call(
                        "homeassistant",
                        "turn_off",
                        {"entity_id": valve_id},
                        blocking=True,
                    )
                except Exception as err:
                    if valve_id not in self._failed_watering_valves:
                        newly_failed_valves.append(valve_id)
                    self._failed_watering_valves.add(valve_id)
                    _LOGGER.error(
                        "%s",
                        self.tr_log(
                            "log_watering_valve_off_error",
                            valve=valve_id,
                            error=err,
                        ),
                    )
        self._refresh_watering_sensors()
        if newly_failed_valves and self.has_mode(MODE_LOGGING):
            await self._async_handle_watering_valve_error(newly_failed_valves)

    async def async_toggle_manual_watering(
        self, duration: int = DEFAULT_WATERING_MANUAL_DURATION
    ) -> None:
        """Выполнить выбранное в селекте «Направление полива» действие и обязательно вернуть выбор на «Остановить»."""
        if not self.has_mode(MODE_WATERING) or not self.watering_valves:
            return

        zone_ent = self.config_entities.get("watering_zone")
        selected = self.selected_watering_zone
        valves = self.watering_valves

        if zone_ent and hasattr(zone_ent, "reset_to_stop"):
            zone_ent.reset_to_stop()
        else:
            self._selected_watering_zone = ACTION_STOP

        if selected == ACTION_STOP or selected not in valves:
            await self.async_stop_watering()
            return

        if self.is_watering_active:
            await self.async_stop_watering()

        targets = [selected]
        self._watering_task = self.entry.async_create_background_task(
            self.hass,
            self.async_run_manual_watering(targets, int(duration)),
            "loggia_watering_manual",
        )

    async def _async_operate_valve_for_duration(
        self, valve_id: str, duration: int, mode_label: str
    ) -> None:
        """Открыть клапан на заданное время с проверкой включения, защитой от перелива и гарантированным закрытием."""
        _LOGGER.info(
            "%s",
            self.tr_log(
                "log_watering_valve_on",
                valve=valve_id,
                duration=duration,
                mode=mode_label,
            ),
        )
        w_status = self.config_entities.get("watering_status")
        valve_st_before = self.hass.states.get(valve_id)
        was_unavail = (
            valve_st_before is None
            or valve_st_before.state in ("unavailable", "unknown")
        )
        turn_on_ok = False
        self._arm_valve_safety_timer(valve_id, duration)
        try:
            if w_status and hasattr(w_status, "set_active_valve"):
                w_status.set_active_valve(valve_id)
            await self.hass.services.async_call(
                "homeassistant",
                "turn_on",
                {"entity_id": valve_id},
                blocking=True,
            )
            check_wait = min(3.0, max(0.5, duration * 0.5))
            await asyncio.sleep(check_wait)
            valve_st_after = self.hass.states.get(valve_id)
            if (
                not valve_st_after
                or valve_st_after.state in ("unavailable", "unknown")
                or valve_st_after.state != "on"
            ):
                was_already_failed = valve_id in self._failed_watering_valves
                self._failed_watering_valves.add(valve_id)
                self._refresh_watering_sensors()
                if not was_already_failed and self.has_mode(MODE_LOGGING):
                    await self._async_handle_watering_valve_error([valve_id])
            else:
                turn_on_ok = True
                self._failed_watering_valves.discard(valve_id)
                self._refresh_watering_sensors()
            remaining = max(0.0, duration - check_wait)
            if remaining > 0:
                await asyncio.sleep(remaining)
        except asyncio.CancelledError:
            _LOGGER.warning(
                "%s",
                self.tr_log("log_watering_cancelled", valve=valve_id),
            )
            raise
        except Exception as err:
            self._failed_watering_valves.add(valve_id)
            self._refresh_watering_sensors()
            _LOGGER.error(
                "%s",
                self.tr_log(
                    "log_watering_valve_off_error",
                    valve=valve_id,
                    error=err,
                ),
            )
        finally:
            self._cancel_valve_safety_timer(valve_id)
            if w_status and hasattr(w_status, "set_active_valve"):
                w_status.set_active_valve(None)
            try:
                await self.hass.services.async_call(
                    "homeassistant",
                    "turn_off",
                    {"entity_id": valve_id},
                    blocking=True,
                )
                if was_unavail and not turn_on_ok:
                    self._failed_watering_valves.add(valve_id)
            except Exception as err:
                self._failed_watering_valves.add(valve_id)
                _LOGGER.error(
                    "%s",
                    self.tr_log(
                        "log_watering_valve_off_error",
                        valve=valve_id,
                        error=err,
                    ),
                )
            self._refresh_watering_sensors()

    async def async_run_manual_watering(
        self, target_valves: list[str], duration: int = DEFAULT_WATERING_MANUAL_DURATION
    ) -> None:
        """Дозированный ручной полив выбранного направления (или всех по очереди)."""
        if not self.has_mode(MODE_WATERING) or not target_valves or duration <= 0:
            return
        _LOGGER.info(
            "%s",
            self.tr_log(
                "log_watering_manual_start",
                count=len(target_valves),
                duration=duration,
            ),
        )
        for valve_id in target_valves:
            await self._async_operate_valve_for_duration(valve_id, duration, "manual")

    @callback
    def on_watering_entity_state_changed(self, entity_id: str, new_state_str: str | None) -> None:
        """Актуализировать списки ошибок клапанов и датчиков и контролировать защиту от перелива."""
        changed = False
        if entity_id in self.watering_valves:
            if new_state_str == "on":
                if entity_id not in self._valve_safety_timers:
                    self._arm_valve_safety_timer(entity_id)
            elif new_state_str == "off":
                self._cancel_valve_safety_timer(entity_id)
        if entity_id in self._failed_watering_valves and new_state_str in ("on", "off"):
            # Если сейчас не идёт цикл полива и клапан штатно в off (или включился вручную), снимаем ошибку
            if not (self._watering_task and not self._watering_task.done()):
                self._failed_watering_valves.discard(entity_id)
                changed = True
        if entity_id in self._failed_watering_sensors and new_state_str not in (
            None,
            "unavailable",
            "unknown",
            "",
            "none",
        ):
            try:
                float(new_state_str)
                self._failed_watering_sensors.discard(entity_id)
                changed = True
            except (TypeError, ValueError):
                pass
        if changed:
            err_ent = self.config_entities.get("watering_error_count")
            if err_ent and hasattr(err_ent, "async_refresh_errors"):
                err_ent.async_refresh_errors()
        self._sync_repair_issues()

    @callback
    def _refresh_watering_sensors(self) -> None:
        """Обновить сенсор состояния полива на основном устройстве и диагностику полива."""
        w_status = self.config_entities.get("watering_status")
        if w_status and hasattr(w_status, "async_refresh_status"):
            w_status.async_refresh_status()
        w_count = self.config_entities.get("watering_active_count")
        if w_count and hasattr(w_count, "async_refresh_count"):
            w_count.async_refresh_count()
        w_err = self.config_entities.get("watering_error_count")
        if w_err and hasattr(w_err, "async_refresh_errors"):
            w_err.async_refresh_errors()
        w_bat = self.config_entities.get("watering_battery")
        if w_bat and hasattr(w_bat, "async_refresh_battery"):
            w_bat.async_refresh_battery()
        w_btn = self.config_entities.get("watering_execute")
        if w_btn and getattr(w_btn, "hass", None) is not None:
            w_btn.async_write_ha_state()
        self.update_next_action_text()
        self._sync_repair_issues()

    @callback
    def _refresh_watering_zone_dependents(self) -> None:
        """Обновить селектор направления и связанные ползунки/списки при переключении направления."""
        zone_ent = self.config_entities.get("watering_zone")
        if zone_ent and hasattr(zone_ent, "async_refresh_options"):
            zone_ent.async_refresh_options()
        for key in (
            "watering_morning_mode",
            "watering_evening_mode",
            "watering_morning_duration",
            "watering_evening_duration",
        ):
            ent = self.config_entities.get(key)
            if ent and hasattr(ent, "async_refresh_from_manager"):
                ent.async_refresh_from_manager()
        self._refresh_watering_sensors()

    @callback
    def _start_watering_cycle(self, period: str) -> None:
        """Запустить утренний или вечерний цикл полива в фоне."""
        if self._watering_task and not self._watering_task.done():
            _LOGGER.warning(
                "%s",
                self.tr_log("log_watering_already_running", period=period),
            )
            return
        self._watering_task = self.entry.async_create_background_task(
            self.hass,
            self.async_run_watering_cycle(period),
            f"loggia_watering_{period}",
        )

    async def async_run_watering_cycle(self, period: str) -> None:
        """Последовательный цикл полива по всем активным направлениям (dev.watering4.yaml)."""
        if not self.has_mode(MODE_WATERING):
            return
        if not self.get_bool("watering_enabled", DEFAULT_WATERING_ENABLED):
            _LOGGER.info(
                "%s",
                self.tr_log("log_watering_disabled", period=period),
            )
            return

        if self.get_bool("watering_skip_next", DEFAULT_WATERING_SKIP_NEXT):
            _LOGGER.info(
                "%s",
                self.tr_log("log_watering_skip_next", period=period),
            )
            skip_ent = self.config_entities.get("watering_skip_next")
            if skip_ent and hasattr(skip_ent, "async_turn_off"):
                await skip_ent.async_turn_off()
            return

        valves = self.watering_valves
        if not valves:
            return

        use_moisture = bool(
            self.get_setting("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE)
        )
        moisture_map = self.watering_moisture_map if use_moisture else {}
        soil_threshold = self.get_number(
            "watering_soil_threshold", DEFAULT_WATERING_SOIL_THRESHOLD
        )
        day_num = int(dt_util.now().timestamp() // 86400)

        _LOGGER.info(
            "%s",
            self.tr_log("log_watering_start", period=period, count=len(valves)),
        )

        excluded_for_period = (
            self.excluded_watering_morning
            if period == "morning"
            else self.excluded_watering_evening
        )

        for valve_id in valves:
            if valve_id in excluded_for_period:
                continue
            z_cfg = self.get_watering_zone_config(valve_id)
            mode = z_cfg["m_mode"] if period == "morning" else z_cfg["e_mode"]
            duration = int(
                z_cfg["m_duration"] if period == "morning" else z_cfg["e_duration"]
            )

            if mode == WATERING_MODE_OFF or duration <= 0:
                continue

            if mode == WATERING_MODE_DAILY:
                is_day_match = True
            elif mode == WATERING_MODE_EVERY_OTHER_DAY:
                is_day_match = (day_num % 2) == 0
            elif mode == WATERING_MODE_EVERY_TWO_DAYS:
                is_day_match = (day_num % 3) == 0
            elif mode == WATERING_MODE_BY_SENSOR:
                is_day_match = True
            else:
                is_day_match = False

            if not is_day_match:
                continue

            sensor_id = moisture_map.get(valve_id) if use_moisture else None
            if mode == WATERING_MODE_BY_SENSOR and not sensor_id:
                _LOGGER.debug(
                    "%s",
                    self.tr_log("log_watering_no_sensor", valve=valve_id),
                )
                continue

            if sensor_id:
                st = self.hass.states.get(sensor_id)
                moisture_val: float | None = None
                if st and st.state not in ("unknown", "unavailable", "", "none"):
                    try:
                        moisture_val = float(st.state)
                    except (TypeError, ValueError):
                        moisture_val = None

                if moisture_val is None:
                    was_sensor_failed = sensor_id in self._failed_watering_sensors
                    self._failed_watering_sensors.add(sensor_id)
                    self._refresh_watering_sensors()
                    if not was_sensor_failed and self.has_mode(MODE_LOGGING):
                        await self._async_handle_watering_sensor_error([sensor_id])
                else:
                    self._failed_watering_sensors.discard(sensor_id)

                if mode == WATERING_MODE_BY_SENSOR and moisture_val is None:
                    _LOGGER.debug(
                        "%s",
                        self.tr_log(
                            "log_watering_sensor_unavail",
                            sensor=sensor_id,
                            valve=valve_id,
                        ),
                    )
                    continue

                if moisture_val is not None and moisture_val >= soil_threshold:
                    _LOGGER.info(
                        "%s",
                        self.tr_log(
                            "log_watering_moisture_skip",
                            valve=valve_id,
                            moisture=moisture_val,
                            threshold=soil_threshold,
                        ),
                    )
                    continue

            await self._async_operate_valve_for_duration(valve_id, duration, mode)

