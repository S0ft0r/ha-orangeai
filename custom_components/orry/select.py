"""Выпадающие списки (Select) интеграции Лоджия."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.translation import async_get_translations

from .const import (
    DOMAIN,
    MODE_BLINDS,
    MODE_SUN_PROTECT,
    MODE_WATERING,
    ACTION_STOP,
    ACTION_OPEN,
    ACTION_CLOSE,
    MANUAL_POSITION_ACTIONS,
    DRIVE_PREFIX_ACTIVE,
    DRIVE_PREFIX_EXCLUDED,
    DRIVE_PREFIX_ENABLE_ALL,
    WATERING_MODE_OFF,
    WATERING_MODE_DAILY,
    WATERING_MODE_EVERY_OTHER_DAY,
    WATERING_MODE_EVERY_TWO_DAYS,
    WATERING_MODE_BY_SENSOR,
    WATERING_MODES,
    WATERING_ZONE_ALL,
    WATERING_PREFIX_ALL,
    WATERING_PREFIX_ACTIVE,
    WATERING_PREFIX_OFF,
    pos_to_blind_step,
)
from .manager import LoggiaManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Создание выпадающих списков для подустройств «Привода» и «Полив»."""
    manager: LoggiaManager = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = []
    if manager.has_mode(MODE_BLINDS):
        entities.extend(
            [
                LoggiaManualActionSelect(manager),
                LoggiaExcludedBlindsSelect(manager),
            ]
        )
        if manager.has_mode(MODE_SUN_PROTECT):
            entities.append(LoggiaSunBlindsSelect(manager))

    if manager.has_mode(MODE_WATERING):
        entities.extend(
            [
                LoggiaWateringZoneSelect(manager),
                LoggiaWateringZonesActivitySelect(
                    manager, "watering_morning_zones", "morning"
                ),
                LoggiaWateringZonesActivitySelect(
                    manager, "watering_evening_zones", "evening"
                ),
                LoggiaWateringModeSelect(manager, "watering_morning_mode", "m_mode", "orry:watering-sunrise"),
                LoggiaWateringModeSelect(manager, "watering_evening_mode", "e_mode", "orry:watering-sunset"),
            ]
        )

    async_add_entities(entities)


class LoggiaManualActionSelect(SelectEntity):
    """Выбор ручного действия для приводов (по умолчанию — Остановить)."""

    _attr_has_entity_name = True
    _attr_translation_key = "manual_action"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "manual_action"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"
        self._attr_current_option = ACTION_STOP
        manager.config_entities[self._key] = self

    def _get_valid_options(self) -> list[str]:
        """Сформировать список действий с учётом текущих верхнего и нижнего лимитов."""
        down_limit = self.manager.get_down_limit()
        up_limit = self.manager.get_up_limit()
        low = min(down_limit, up_limit)
        high = max(down_limit, up_limit)

        opts = [ACTION_STOP, ACTION_OPEN, ACTION_CLOSE]
        for action_key, pct in MANUAL_POSITION_ACTIONS.items():
            if low <= pct <= high:
                opts.append(action_key)
        return opts

    @property
    def options(self) -> list[str]:
        """Динамический список доступных действий (без пунктов, выпадающих за лимиты)."""
        return self._get_valid_options()

    @property
    def current_option(self) -> str | None:
        """Текущее выбранное действие (с автосбросом на 'Остановить', если вышло за лимиты)."""
        valid = self._get_valid_options()
        if self._attr_current_option not in valid:
            self._attr_current_option = ACTION_STOP
        return self._attr_current_option

    @property
    def icon(self) -> str:
        """Динамическая иконка выбранного действия штор."""
        opt = self.current_option
        if opt == ACTION_OPEN:
            return "orry:blind-100"
        if opt == ACTION_CLOSE:
            return "orry:blind-0"
        if opt in MANUAL_POSITION_ACTIONS:
            return f"orry:blind-{pos_to_blind_step(MANUAL_POSITION_ACTIONS[opt], 50)}"
        return "orry:blind-50"

    async def async_select_option(self, option: str) -> None:
        """Выбрать действие из списка."""
        if option in self._get_valid_options():
            self._attr_current_option = option
            self.async_write_ha_state()

    @callback
    def async_refresh_options(self) -> None:
        """Обновить доступные пункты при изменении лимитов."""
        valid = self._get_valid_options()
        if self._attr_current_option not in valid:
            self._attr_current_option = ACTION_STOP
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def reset_to_stop(self) -> None:
        """Сбросить выбранное действие обратно на 'Остановить' после нажатия кнопки."""
        self._attr_current_option = ACTION_STOP
        if self.hass is not None:
            self.async_write_ha_state()


class LoggiaExcludedBlindsSelect(SelectEntity, RestoreEntity):
    """Умный выпадающий список для включения/исключения отдельных приводов из работы."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_translation_key = "excluded_blinds"
    _attr_icon = "orry:blind-pause"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "excluded_blinds"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"

        raw_excluded = manager.get_setting("excluded_blinds", []) or []
        all_set = set(manager.all_blinds)
        self.excluded_set: set[str] = {b for b in raw_excluded if b in all_set}
        self._option_to_blind: dict[str, str] = {}
        self._last_options_snapshot: list[str] = []

        # Локализованные тексты из translations/<lang>.json
        self._txt_enable_all: str = manager.tr_entity_state(
            "select", "excluded_blinds", "enable_all"
        )
        self._txt_all_active: str = manager.tr_entity_state(
            "select", "excluded_blinds", "all_active"
        )
        self._txt_excluded: str = manager.tr_entity_state(
            "select", "excluded_blinds", "excluded"
        )

        manager.config_entities[self._key] = self

    @property
    def _enable_all_label(self) -> str:
        """Склеить префикс из const.py и локализованную фразу из translations/*.json."""
        return f"{DRIVE_PREFIX_ENABLE_ALL} {self._txt_enable_all}".strip()

    async def async_added_to_hass(self) -> None:
        """Восстановить список исключённых приводов и загрузить переводы из translations/*.json."""
        await super().async_added_to_hass()

        # Подгружаем фразы из translations/<lang>.json
        try:
            lang = self.hass.config.language or "ru"
            translations = await async_get_translations(
                self.hass, lang, "entity", [DOMAIN]
            )
            prefix = f"component.{DOMAIN}.entity.select.excluded_blinds.state."
            self._txt_enable_all = translations.get(
                f"{prefix}enable_all", self._txt_enable_all
            )
            self._txt_all_active = translations.get(
                f"{prefix}all_active", self._txt_all_active
            )
            self._txt_excluded = translations.get(
                f"{prefix}excluded", self._txt_excluded
            )
        except Exception:
            pass

        last_state = await self.async_get_last_state()
        if last_state and "excluded_blinds" in last_state.attributes:
            restored = last_state.attributes.get("excluded_blinds") or []
            all_set = set(self.manager.all_blinds)
            self.excluded_set = {b for b in restored if b in all_set}
            self.manager.set_excluded_blinds(self.excluded_set)

        @callback
        def _async_on_blind_state_change(event) -> None:
            new_opts = self._rebuild_options()
            if new_opts != self._last_options_snapshot:
                self._last_options_snapshot = list(new_opts)
                self.async_write_ha_state()

        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, _async_on_blind_state_change
                )
            )
        self._last_options_snapshot = self._rebuild_options()
        self.async_write_ha_state()

    def _blind_label(self, blind_id: str, used_names: set[str]) -> str:
        """Получить читаемое имя привода для выпадающего списка."""
        st = self.manager.hass.states.get(blind_id) if self.manager.hass else None
        base_name = st.name if (st and st.name) else blind_id
        prefix = DRIVE_PREFIX_EXCLUDED if blind_id in self.excluded_set else DRIVE_PREFIX_ACTIVE
        label = f"{prefix} {base_name}".strip()
        if label in used_names:
            label = f"{prefix} {base_name} ({blind_id})".strip()
        used_names.add(label)
        return label

    def _summary_label(self) -> str:
        """Сводная строка статуса (отображается как текущее значение в закрытом списке)."""
        total = len(self.manager.all_blinds)
        excl_count = len(self.excluded_set)
        if excl_count == 0:
            return f"{self._txt_all_active} ({total})"
        return f"{self._txt_excluded}: {excl_count} / {total}"

    def _rebuild_options(self) -> list[str]:
        """Пересобрать пункты выпадающего списка."""
        self._option_to_blind.clear()
        used_names: set[str] = set()
        opts = [self._summary_label()]
        if self.excluded_set:
            opts.append(self._enable_all_label)
        for blind_id in self.manager.all_blinds:
            lbl = self._blind_label(blind_id, used_names)
            self._option_to_blind[lbl] = blind_id
            opts.append(lbl)
        return opts

    @property
    def options(self) -> list[str]:
        """Список доступных пунктов меню."""
        return self._rebuild_options()

    @property
    def current_option(self) -> str | None:
        """Текущее отображаемое значение — всегда актуальная сводка."""
        return self._summary_label()

    @property
    def extra_state_attributes(self) -> dict:
        """Списки приводов и соответствие entity_id к пунктам select для UI карточки."""
        all_blinds = self.manager.all_blinds
        self._rebuild_options()
        return {
            "all_blinds": list(all_blinds),
            "excluded_blinds": [blind for blind in all_blinds if blind in self.excluded_set],
            "active_blinds": [blind for blind in all_blinds if blind not in self.excluded_set],
            "option_by_blind": {
                blind_id: option for option, blind_id in self._option_to_blind.items()
            },
        }

    async def async_select_option(self, option: str) -> None:
        """Переключить статус выбранного привода (Активен ↔ Исключён)."""
        self._rebuild_options()
        changed = False

        if option == self._enable_all_label:
            if self.excluded_set:
                self.excluded_set.clear()
                changed = True
        elif option in self._option_to_blind:
            blind_id = self._option_to_blind[option]
            if blind_id in self.excluded_set:
                self.excluded_set.remove(blind_id)
            else:
                self.excluded_set.add(blind_id)
            changed = True

        if changed:
            self.manager.set_excluded_blinds(self.excluded_set)

        self.async_write_ha_state()


class LoggiaSunBlindsSelect(SelectEntity):
    """Live-настройка приводов, участвующих в защите от прямого солнца."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_translation_key = "blinds_for_protect"
    _attr_icon = "orry:blind-sun"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "blinds_for_protect"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"
        self._option_to_blind: dict[str, str] = {}
        self._last_options_snapshot: list[str] = []
        self._txt_all_selected = manager.tr_entity_state(
            "select", self._key, "all_selected"
        )
        self._txt_selected = manager.tr_entity_state(
            "select", self._key, "selected"
        )
        self._txt_enable_all = manager.tr_entity_state(
            "select", self._key, "enable_all"
        )
        manager.config_entities[self._key] = self

    @property
    def _enable_all_label(self) -> str:
        return f"{DRIVE_PREFIX_ENABLE_ALL} {self._txt_enable_all}".strip()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        try:
            lang = self.hass.config.language or "ru"
            translations = await async_get_translations(
                self.hass, lang, "entity", [DOMAIN]
            )
            prefix = f"component.{DOMAIN}.entity.select.{self._key}.state."
            self._txt_all_selected = translations.get(
                f"{prefix}all_selected", self._txt_all_selected
            )
            self._txt_selected = translations.get(
                f"{prefix}selected", self._txt_selected
            )
            self._txt_enable_all = translations.get(
                f"{prefix}enable_all", self._txt_enable_all
            )
        except Exception:
            pass

        @callback
        def _async_on_blind_state_change(_event) -> None:
            new_options = self._rebuild_options()
            if new_options != self._last_options_snapshot:
                self._last_options_snapshot = list(new_options)
                self.async_write_ha_state()

        if self.manager.all_blinds:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self.manager.all_blinds, _async_on_blind_state_change
                )
            )
        self._last_options_snapshot = self._rebuild_options()
        self.async_write_ha_state()

    def _blind_label(self, blind_id: str, used_names: set[str]) -> str:
        st = self.manager.hass.states.get(blind_id) if self.manager.hass else None
        base_name = st.name if st and st.name else blind_id
        selected = blind_id in self.manager.blinds_for_protect
        state_prefix = DRIVE_PREFIX_ACTIVE if selected else DRIVE_PREFIX_EXCLUDED
        label = f"{state_prefix} {base_name}".strip()
        if label in used_names:
            label = f"{state_prefix} {base_name} ({blind_id})".strip()
        used_names.add(label)
        return label

    def _summary_label(self) -> str:
        total = len(self.manager.all_blinds)
        selected_count = len(self.manager.blinds_for_protect)
        if selected_count == total:
            return f"{self._txt_all_selected} ({total})"
        return f"{self._txt_selected}: {selected_count} / {total}"

    def _rebuild_options(self) -> list[str]:
        self._option_to_blind.clear()
        used_names: set[str] = set()
        all_blinds = self.manager.all_blinds
        selected = self.manager.blinds_for_protect
        options = [self._summary_label()]
        if len(selected) < len(all_blinds):
            options.append(self._enable_all_label)
        for blind_id in all_blinds:
            label = self._blind_label(blind_id, used_names)
            self._option_to_blind[label] = blind_id
            options.append(label)
        return options

    @property
    def options(self) -> list[str]:
        return self._rebuild_options()

    @property
    def current_option(self) -> str | None:
        return self._summary_label()

    @property
    def extra_state_attributes(self) -> dict:
        self._rebuild_options()
        all_blinds = self.manager.all_blinds
        selected = self.manager.blinds_for_protect
        return {
            "all_blinds": list(all_blinds),
            "selected_blinds": [blind for blind in all_blinds if blind in selected],
            "option_by_blind": {
                blind_id: option for option, blind_id in self._option_to_blind.items()
            },
        }

    async def async_select_option(self, option: str) -> None:
        self._rebuild_options()
        selected = set(self.manager.blinds_for_protect)
        if option == self._enable_all_label:
            selected = set(self.manager.all_blinds)
        elif option in self._option_to_blind:
            blind_id = self._option_to_blind[option]
            if blind_id in selected:
                selected.remove(blind_id)
            else:
                selected.add(blind_id)
        else:
            return
        await self.manager.async_set_blinds_for_protect(selected)
        self.async_write_ha_state()


class LoggiaWateringZoneSelect(SelectEntity):
    """Выбор направления полива в блоке «Управление» (по умолчанию — «Остановить», с автовозвратом)."""

    _attr_has_entity_name = True
    _attr_translation_key = "watering_zone"

    def __init__(self, manager: LoggiaManager) -> None:
        self.manager = manager
        self._key = "watering_zone"
        self._attr_device_info = manager.device_info_for(self._key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{self._key}"

        self._option_to_zone: dict[str, str] = {}
        self._zone_to_option: dict[str, str] = {}
        self._last_options_snapshot: list[str] = []

        self._txt_stop: str = manager.tr_entity_state(
            "select", "watering_zone", ACTION_STOP
        )

        manager.config_entities[self._key] = self

    async def async_added_to_hass(self) -> None:
        """Загрузить локализованный пункт «Остановить» и подписаться на переименование клапанов."""
        await super().async_added_to_hass()

        try:
            lang = self.hass.config.language or "ru"
            translations = await async_get_translations(
                self.hass, lang, "entity", [DOMAIN]
            )
            stop_key = f"component.{DOMAIN}.entity.select.watering_zone.state.{ACTION_STOP}"
            fallback_key = f"component.{DOMAIN}.entity.select.manual_action.state.{ACTION_STOP}"
            if stop_key in translations:
                self._txt_stop = translations[stop_key]
            elif fallback_key in translations:
                self._txt_stop = translations[fallback_key]
        except Exception:
            pass

        tracked_entities = list(self.manager.watering_valves)

        @callback
        def _async_on_tracked_change(_event) -> None:
            new_opts = self._rebuild_options()
            if new_opts != self._last_options_snapshot:
                self._last_options_snapshot = list(new_opts)
                self.async_write_ha_state()

        if tracked_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, tracked_entities, _async_on_tracked_change
                )
            )

        self._last_options_snapshot = self._rebuild_options()
        self.async_write_ha_state()

    def _format_valve_label(self, valve_id: str, used_labels: set[str]) -> str:
        """Получить чистое читаемое имя клапана для выпадающего списка."""
        st = self.manager.hass.states.get(valve_id) if self.manager.hass else None
        base_name = (st.name if (st and st.name) else valve_id).strip()
        label = base_name
        if label in used_labels or label == self._txt_stop:
            label = f"{base_name} ({valve_id})".strip()
        used_labels.add(label)
        return label

    def _rebuild_options(self) -> list[str]:
        """Пересобрать список: «Остановить» + список всех клапанов."""
        self._option_to_zone.clear()
        self._zone_to_option.clear()
        used_labels: set[str] = {self._txt_stop}

        self._option_to_zone[self._txt_stop] = ACTION_STOP
        self._zone_to_option[ACTION_STOP] = self._txt_stop
        self._zone_to_option[WATERING_ZONE_ALL] = self._txt_stop
        opts = [self._txt_stop]

        for valve_id in self.manager.watering_valves:
            lbl = self._format_valve_label(valve_id, used_labels)
            self._option_to_zone[lbl] = valve_id
            self._zone_to_option[valve_id] = lbl
            opts.append(lbl)
        return opts

    @property
    def options(self) -> list[str]:
        """Пункты выпадающего списка направлений."""
        return self._rebuild_options()

    @property
    def current_option(self) -> str | None:
        """Текущий выбранный пункт списка (по умолчанию — «Остановить»)."""
        opts = self._rebuild_options()
        sel_zone = self.manager.selected_watering_zone
        if sel_zone in self._zone_to_option:
            return self._zone_to_option[sel_zone]
        return opts[0] if opts else None

    @property
    def extra_state_attributes(self) -> dict:
        """Атрибуты со сводной матрицей всех направлений и датчиков влажности."""
        zones_attr = {}
        moisture_map = self.manager.watering_moisture_map
        for v in self.manager.watering_valves:
            cfg = self.manager.get_watering_zone_config(v)
            zones_attr[v] = {
                **cfg,
                "moisture_sensor": moisture_map.get(v),
            }
        return {
            "selected_zone": self.manager.selected_watering_zone,
            "zones": zones_attr,
        }

    async def async_select_option(self, option: str) -> None:
        """Выбрать направление полива или «Остановить»."""
        self._rebuild_options()
        zone_id = self._option_to_zone.get(option, ACTION_STOP)
        self.manager.set_selected_watering_zone(zone_id)
        self.async_write_ha_state()

    @callback
    def reset_to_stop(self) -> None:
        """Вернуть выбранный пункт обратно на «Остановить» после нажатия кнопки."""
        self.manager.set_selected_watering_zone(ACTION_STOP)
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def async_refresh_options(self) -> None:
        """Обновить список направлений."""
        self._last_options_snapshot = self._rebuild_options()
        if self.hass is not None:
            self.async_write_ha_state()


class LoggiaWateringZonesActivitySelect(SelectEntity, RestoreEntity):
    """Умный выпадающий список для включения/исключения отдельных направлений из утреннего или вечернего полива."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, manager: LoggiaManager, key: str, period: str) -> None:
        self.manager = manager
        self._key = key
        self._period = period
        self._option_key = f"excluded_watering_{period}"
        self._attr_device_info = manager.device_info_for(key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key

        raw_excluded = manager.get_setting(self._option_key, []) or []
        all_set = set(manager.watering_valves)
        self.excluded_set: set[str] = {v for v in raw_excluded if v in all_set}
        self._option_to_valve: dict[str, str] = {}
        self._last_options_snapshot: list[str] = []

        self._txt_enable_all: str = manager.tr_entity_state(
            "select", key, "enable_all"
        )
        self._txt_all_active: str = manager.tr_entity_state(
            "select", key, "all_active"
        )
        self._txt_excluded: str = manager.tr_entity_state(
            "select", key, "excluded"
        )

        manager.config_entities[key] = self

    @property
    def _enable_all_label(self) -> str:
        """Склеить префикс из const.py и локализованную фразу включения всех направлений."""
        return f"{DRIVE_PREFIX_ENABLE_ALL} {self._txt_enable_all}".strip()

    async def async_added_to_hass(self) -> None:
        """Восстановить список исключённых направлений и загрузить переводы из translations/*.json."""
        await super().async_added_to_hass()

        try:
            lang = self.hass.config.language or "ru"
            translations = await async_get_translations(
                self.hass, lang, "entity", [DOMAIN]
            )
            prefix = f"component.{DOMAIN}.entity.select.{self._key}.state."
            self._txt_enable_all = translations.get(
                f"{prefix}enable_all", self._txt_enable_all
            )
            self._txt_all_active = translations.get(
                f"{prefix}all_active", self._txt_all_active
            )
            self._txt_excluded = translations.get(
                f"{prefix}excluded", self._txt_excluded
            )
        except Exception:
            pass

        last_state = await self.async_get_last_state()
        if last_state and "excluded_zones" in last_state.attributes:
            restored = last_state.attributes.get("excluded_zones") or []
            all_set = set(self.manager.watering_valves)
            self.excluded_set = {v for v in restored if v in all_set}
            self.manager.set_excluded_watering_zones(self._period, self.excluded_set)

        @callback
        def _async_on_valve_state_change(_event) -> None:
            new_opts = self._rebuild_options()
            if new_opts != self._last_options_snapshot:
                self._last_options_snapshot = list(new_opts)
                self.async_write_ha_state()

        if self.manager.watering_valves:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    self.manager.watering_valves,
                    _async_on_valve_state_change,
                )
            )
        self._last_options_snapshot = self._rebuild_options()
        self.async_write_ha_state()

    def _valve_label(self, valve_id: str, used_names: set[str]) -> str:
        """Получить читаемое имя направления для выпадающего списка."""
        st = self.manager.hass.states.get(valve_id) if self.manager.hass else None
        base_name = st.name if (st and st.name) else valve_id
        prefix = (
            DRIVE_PREFIX_EXCLUDED
            if valve_id in self.excluded_set
            else DRIVE_PREFIX_ACTIVE
        )
        label = f"{prefix} {base_name}".strip()
        if label in used_names:
            label = f"{prefix} {base_name} ({valve_id})".strip()
        used_names.add(label)
        return label

    def _summary_label(self) -> str:
        """Сводная строка статуса (отображается как текущее значение в закрытом списке)."""
        total = len(self.manager.watering_valves)
        excl_count = len(self.excluded_set)
        if excl_count == 0:
            return f"{self._txt_all_active} ({total})"
        return f"{self._txt_excluded}: {excl_count} / {total}"

    def _rebuild_options(self) -> list[str]:
        """Пересобрать пункты выпадающего списка."""
        self._option_to_valve.clear()
        used_names: set[str] = set()
        opts = [self._summary_label()]
        if self.excluded_set:
            opts.append(self._enable_all_label)
        for valve_id in self.manager.watering_valves:
            lbl = self._valve_label(valve_id, used_names)
            self._option_to_valve[lbl] = valve_id
            opts.append(lbl)
        return opts

    @property
    def options(self) -> list[str]:
        """Список доступных пунктов меню."""
        return self._rebuild_options()

    @property
    def current_option(self) -> str | None:
        """Текущее отображаемое значение — всегда актуальная сводка."""
        return self._summary_label()

    @property
    def extra_state_attributes(self) -> dict:
        """Атрибуты со списками исключённых и активных направлений для периода."""
        all_v = self.manager.watering_valves
        return {
            "excluded_zones": [v for v in all_v if v in self.excluded_set],
            "active_zones": [v for v in all_v if v not in self.excluded_set],
        }

    async def async_select_option(self, option: str) -> None:
        """Переключить статус выбранного направления (Активно ↔ Исключено)."""
        self._rebuild_options()
        changed = False

        if option == self._enable_all_label:
            if self.excluded_set:
                self.excluded_set.clear()
                changed = True
        elif option in self._option_to_valve:
            valve_id = self._option_to_valve[option]
            if valve_id in self.excluded_set:
                self.excluded_set.remove(valve_id)
            else:
                self.excluded_set.add(valve_id)
            changed = True

        if changed:
            self.manager.set_excluded_watering_zones(self._period, self.excluded_set)

        self.async_write_ha_state()


class LoggiaWateringModeSelect(SelectEntity):
    """Выпадающий список выбора режима полива (утро / вечер) для выбранного направления."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_options = WATERING_MODES

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
    def current_option(self) -> str | None:
        """Режим полива текущего выбранного направления."""
        cfg = self.manager.get_watering_zone_config()
        val = str(cfg.get(self._field_name, WATERING_MODE_OFF))
        return val if val in WATERING_MODES else WATERING_MODE_OFF

    async def async_select_option(self, option: str) -> None:
        """Изменить режим полива для выбранного направления (или сразу всех направлений)."""
        if option in WATERING_MODES:
            self.manager.update_watering_zone_setting(self._field_name, option)

    @callback
    def async_refresh_from_manager(self) -> None:
        """Обновить отображаемый режим при переключении направления."""
        if self.hass is not None:
            self.async_write_ha_state()

