"""Config Flow и Options Flow для интеграции Лоджия."""

from datetime import timedelta
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    MODE_BLINDS, MODE_SUN_PROTECT, MODE_PHYTOLAMP, MODE_WATERING, MODE_SLIDER, MODE_YANDEX, MODE_LOGGING,
    DEFAULT_SUN_SENSOR, DEFAULT_USE_FORECAST, DEFAULT_USE_ILLUMINANCE,
    DEFAULT_OPEN_AT_SUNRISE, DEFAULT_OPEN_TIME_WORKDAY, DEFAULT_OPEN_TIME_WEEKEND,
    DEFAULT_CLOSE_AT_SUNSET, DEFAULT_CLOSE_TIME,
    DEFAULT_SPLIT_WEEKEND_SCHEDULE,
    DEFAULT_WORK_DAYS, DEFAULT_OFF_DAYS, DEFAULT_USE_HOLIDAYS,
    DEFAULT_SUN_AZIMUTH, DEFAULT_SUN_ELEVATION,
    DEFAULT_UP_LIMIT, DEFAULT_DOWN_LIMIT, DEFAULT_MIN_ILLUMINANCE,
    DEFAULT_MAX_ILLUMINANCE, DEFAULT_ILLUMINANCE_DELAY, DEFAULT_REPEAT,
    DEFAULT_REPEAT_DELAY, DEFAULT_MOVEMENT_TIME, DEFAULT_FORECASTS,
    DEFAULT_YANDEX_VOLUME, DEFAULT_YANDEX_INTENT_OPEN, DEFAULT_YANDEX_INTENT_CLOSE,
    DEFAULT_YANDEX_INTENT_POSITION, DEFAULT_YANDEX_INTENT_STATUS,
    VOICE_ENGINE_YANDEX, VOICE_ENGINE_ASSIST, VOICE_ENGINE_CUSTOM,
    DEFAULT_VOICE_ENGINE, DEFAULT_VOICE_EVENT,
    DEFAULT_BASIC_TOPIC, DEFAULT_PAYLOAD_UP, DEFAULT_PAYLOAD_DOWN, DEFAULT_PAYLOAD_STOP,
    SLIDER_MODE_FULL, SLIDER_MODE_STEP, SLIDER_MODE_PROPORTIONAL,
    DEFAULT_SLIDER_MODE, DEFAULT_SLIDER_STEP, DEFAULT_SLIDER_FAST_SPEED,
    DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
    DEFAULT_PHYTOLAMP_USE_SUN, DEFAULT_PHYTOLAMP_USE_FORECAST,
    DEFAULT_PHYTOLAMP_USE_ILLUMINANCE,
    DEFAULT_PHYTOLAMP_ON_WORKDAY, DEFAULT_PHYTOLAMP_ON_WEEKEND, DEFAULT_PHYTOLAMP_OFF_TIME,
    WATERING_MODES,
    DEFAULT_WATERING_USE_MOISTURE,
    DEFAULT_WATERING_MORNING_TIME, DEFAULT_WATERING_EVENING_TIME,
    DEFAULT_WATERING_SOIL_THRESHOLD,
    DEFAULT_WATERING_MORNING_MODE, DEFAULT_WATERING_MORNING_DURATION,
    DEFAULT_WATERING_EVENING_MODE, DEFAULT_WATERING_EVENING_DURATION,
    DEFAULT_LOW_BATTERY_THRESHOLD,
)


def _default_monday_iso() -> str:
    """Понедельник текущей недели в формате YYYY-MM-DD."""
    today = dt_util.now().date()
    return (today - timedelta(days=today.weekday())).isoformat()


def _add_cycle_schedule_fields(schema: dict, get_val) -> None:
    """Добавить поля рабочего цикла (N рабочих / M выходных / опорная дата) и учёта госпраздников."""
    schema[
        vol.Optional(
            "work_days",
            default=max(1, int(get_val("work_days", DEFAULT_WORK_DAYS) or DEFAULT_WORK_DAYS)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=31,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )
    schema[
        vol.Optional(
            "off_days",
            default=max(1, int(get_val("off_days", DEFAULT_OFF_DAYS) or DEFAULT_OFF_DAYS)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=31,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )
    schema[
        vol.Optional(
            "cycle_start_date",
            default=get_val("cycle_start_date") or _default_monday_iso(),
        )
    ] = selector.DateSelector()
    schema[
        vol.Optional(
            "use_holidays",
            default=get_val("use_holidays", DEFAULT_USE_HOLIDAYS),
        )
    ] = selector.BooleanSelector()


def _add_entity_selector(
    schema_dict: dict,
    key: str,
    domain,
    current_value=None,
    multiple: bool = False,
    device_class=None,
    required: bool = False,
    include_entities: list[str] | None = None,
):
    config_kwargs = {"domain": domain, "multiple": multiple}
    if device_class:
        config_kwargs["device_class"] = device_class
    if include_entities:
        config_kwargs["include_entities"] = include_entities
    sel = selector.EntitySelector(selector.EntitySelectorConfig(**config_kwargs))
    vol_class = vol.Required if required else vol.Optional
    val = current_value
    if include_entities and isinstance(val, list):
        val = [v for v in val if v in include_entities]
    if isinstance(val, list):
        val = val if multiple else (val[0] if val else None)
    if val == "":
        val = None
    if val:
        schema_dict[vol_class(key, default=val)] = sel
    else:
        schema_dict[vol_class(key)] = sel


def _add_device_selector(
    schema_dict: dict,
    key: str,
    entity_filters: list,
    current_value=None,
    required: bool = False,
):
    sel = selector.DeviceSelector(
        selector.DeviceSelectorConfig(entity=entity_filters, multiple=False)
    )
    vol_class = vol.Required if required else vol.Optional
    val = current_value
    if isinstance(val, list):
        val = val[0] if val else None
    if val == "":
        val = None
    if val:
        schema_dict[vol_class(key, default=val)] = sel
    else:
        schema_dict[vol_class(key)] = sel


def _sun_protect_extras_default(get_val) -> list[str]:
    """Собрать текущие чекбоксы защиты от солнца."""
    extras: list[str] = []
    if get_val("use_forecast", DEFAULT_USE_FORECAST):
        extras.append("use_forecast")
    if get_val("use_illuminance", DEFAULT_USE_ILLUMINANCE):
        extras.append("use_illuminance")
    return extras


def _apply_sun_protect_extras(user_input: dict) -> dict:
    """Преобразовать multi-select в boolean-флаги."""
    extras = user_input.pop("sun_protect_extras", []) or []
    user_input["use_forecast"] = "use_forecast" in extras
    user_input["use_illuminance"] = "use_illuminance" in extras
    return user_input


def _phytolamp_extras_default(get_val) -> list[str]:
    """Собрать текущие чекбоксы подсветки растений."""
    extras: list[str] = []
    if get_val("phytolamp_use_sun", DEFAULT_PHYTOLAMP_USE_SUN):
        extras.append("phytolamp_use_sun")
    if get_val("phytolamp_use_illuminance", DEFAULT_PHYTOLAMP_USE_ILLUMINANCE):
        extras.append("phytolamp_use_illuminance")
    if get_val("phytolamp_use_forecast", DEFAULT_PHYTOLAMP_USE_FORECAST):
        extras.append("phytolamp_use_forecast")
    return extras


def _apply_phytolamp_extras(user_input: dict) -> dict:
    """Преобразовать multi-select подсветки растений в boolean-флаги."""
    extras = user_input.pop("phytolamp_extras", []) or []
    user_input["phytolamp_use_sun"] = "phytolamp_use_sun" in extras
    user_input["phytolamp_use_illuminance"] = "phytolamp_use_illuminance" in extras
    user_input["phytolamp_use_forecast"] = "phytolamp_use_forecast" in extras
    return user_input


def _valve_field_label(hass, valve_id: str, used_labels: set[str]) -> str:
    """Сформировать понятную подпись поля для привязки датчика влажности к клапану."""
    st = hass.states.get(valve_id) if hass else None
    name = st.name if (st and st.name) else valve_id
    label = f"{name} ({valve_id})" if name != valve_id else valve_id
    if label in used_labels:
        label = f"{label} [{len(used_labels) + 1}]"
    used_labels.add(label)
    return label


def _sync_watering_zones_config(
    valves: list[str],
    existing_cfg: dict | None,
    m_mode: str,
    m_duration: int,
    e_mode: str,
    e_duration: int,
    overwrite_all: bool = False,
) -> dict[str, dict]:
    """Создать или актуализировать словарь настроек зон полива по списку клапанов."""
    old_map = dict(existing_cfg) if isinstance(existing_cfg, dict) else {}
    new_map: dict[str, dict] = {}
    for valve_id in valves:
        if not overwrite_all and valve_id in old_map and isinstance(old_map[valve_id], dict):
            prev = old_map[valve_id]
            new_map[valve_id] = {
                "m_mode": str(prev.get("m_mode", m_mode)),
                "m_duration": int(prev.get("m_duration", m_duration)),
                "e_mode": str(prev.get("e_mode", e_mode)),
                "e_duration": int(prev.get("e_duration", e_duration)),
            }
        else:
            new_map[valve_id] = {
                "m_mode": str(m_mode),
                "m_duration": int(m_duration),
                "e_mode": str(e_mode),
                "e_duration": int(e_duration),
            }
    return new_map


class LoggiaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data: dict = {}
        self._steps_queue: list[str] = []
        self._completed_steps: set[str] = set()

    def _get_val(self, key, default=None):
        return self._data.get(key, default)

    def _is_mqtt_device(self, device_id: str) -> bool:
        if not device_id:
            return False
        registry = dr.async_get(self.hass)
        device = registry.async_get(device_id)
        if device:
            for identifier in device.identifiers:
                if identifier[0] == "mqtt":
                    return True
        return False

    def _build_steps_queue(self) -> list[str]:
        modes = self._data.get("modes", []) or []
        queue = []
        if MODE_BLINDS in modes:
            queue.append("blinds")
        if MODE_PHYTOLAMP in modes:
            queue.append("phytolamp")
        if MODE_WATERING in modes:
            queue.append("watering")
        if MODE_LOGGING in modes:
            queue.append("logging")
        return queue

    async def _async_get_default_title(self) -> str:
        """Получить локализованное название экземпляра по умолчанию из translations/*.json."""
        fallback = "Orangery"
        try:
            lang = (self.hass.config.language if self.hass else "ru") or "ru"
            tr = await async_get_translations(self.hass, lang, "entity", [DOMAIN])
            return tr.get(
                f"component.{DOMAIN}.entity.sensor.status.state.default_title",
                fallback,
            )
        except Exception:
            return fallback

    async def _async_next_step(self):
        if not self._steps_queue:
            default_title = await self._async_get_default_title()
            custom_title = str(self._data.pop("instance_name", "") or "").strip()
            title = custom_title if custom_title else default_title
            return self.async_create_entry(
                title=title,
                data={
                    "_modular_v2": True,
                    "modes": self._data.pop("modes", []),
                    "blinds": self._data.pop("blinds", []),
                    "sun_sensor": self._data.pop("sun_sensor", DEFAULT_SUN_SENSOR) or DEFAULT_SUN_SENSOR,
                },
                options=self._data,
            )
        next_step = self._steps_queue.pop(0)
        self._completed_steps.add(next_step)
        return await getattr(self, f"async_step_{next_step}")()

    async def async_step_user(self, user_input=None):
        errors = {}
        allowed_modules = [
            MODE_BLINDS,
            MODE_PHYTOLAMP,
            MODE_WATERING,
        ]
        default_title = await self._async_get_default_title()
        if user_input is not None:
            raw_title = str(user_input.get("instance_name") or "").strip()
            self._data["instance_name"] = raw_title or default_title
            selected_modules = [
                m for m in (user_input.get("modes") or []) if m in allowed_modules
            ]
            if not selected_modules:
                errors["modes"] = "no_modules"
            else:
                enable_logging = bool(user_input.get("enable_logging", False))
                modes = list(selected_modules)
                if enable_logging:
                    modes.append(MODE_LOGGING)
                self._data["_modular_v2"] = True
                self._data["modes"] = modes
                self._steps_queue = self._build_steps_queue()
                return await self._async_next_step()

        current_title = str(self._get_val("instance_name", default_title) or default_title)
        current_modes = self._get_val("modes", [MODE_BLINDS]) or [MODE_BLINDS]
        default_modules = [m for m in current_modes if m in allowed_modules]
        if not default_modules:
            default_modules = [MODE_BLINDS]
        default_logging = MODE_LOGGING in current_modes

        schema = {
            vol.Optional("instance_name", default=current_title): selector.TextSelector(),
            vol.Optional("modes", default=default_modules): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=allowed_modules,
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                    translation_key="modes",
                )
            ),
            vol.Optional("enable_logging", default=default_logging): selector.BooleanSelector(),
        }
        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_blinds(self, user_input=None):
        errors = {}
        blinds_submodes = [MODE_SUN_PROTECT, MODE_SLIDER]
        if user_input is not None:
            if not user_input.get("blinds"):
                errors["blinds"] = "no_blinds"
            else:
                selected_sub = [
                    m for m in (user_input.pop("blinds_modes", []) or []) if m in blinds_submodes
                ]
                base_modes = [
                    m for m in (self._data.get("modes", []) or []) if m not in blinds_submodes
                ]
                self._data["modes"] = base_modes + selected_sub
                self._data.update(user_input)

                inject_steps = []
                if MODE_SUN_PROTECT in selected_sub:
                    inject_steps.append("sun_protect")
                if MODE_SLIDER in selected_sub:
                    inject_steps.append("device")
                    inject_steps.append("device_payloads")
                inject_steps.extend(["limits", "time", "repeats"])

                self._steps_queue = inject_steps + self._steps_queue
                return await self._async_next_step()

        default_sub = [
            m for m in (self._get_val("modes", []) or []) if m in blinds_submodes
        ]
        schema = {}
        _add_entity_selector(
            schema, "blinds", "cover", self._get_val("blinds"), multiple=True, required=True
        )
        schema[vol.Optional("blinds_modes", default=default_sub)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=blinds_submodes,
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="blinds_modes",
            )
        )
        schema[
            vol.Optional(
                "split_weekend_schedule",
                default=self._get_val(
                    "split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE
                ),
            )
        ] = selector.BooleanSelector()
        return self.async_show_form(
            step_id="blinds", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_sun_protect(self, user_input=None):
        if user_input is not None:
            user_input.setdefault("blinds_for_protect", [])
            user_input = _apply_sun_protect_extras(user_input)
            self._data.update(user_input)

            inject_steps = ["sun_protect_angles"]
            if user_input.get("use_forecast"):
                inject_steps.append("weather")
            if user_input.get("use_illuminance"):
                inject_steps.append("illuminance")

            self._steps_queue = inject_steps + self._steps_queue
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "sun_sensor", "sun", self._get_val("sun_sensor", DEFAULT_SUN_SENSOR))
        _add_entity_selector(
            schema,
            "blinds_for_protect",
            "cover",
            self._get_val("blinds_for_protect"),
            multiple=True,
            include_entities=self._get_val("blinds", []),
        )
        schema[vol.Optional(
            "sun_protect_extras",
            default=_sun_protect_extras_default(self._get_val),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["use_forecast", "use_illuminance"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="sun_protect_extras",
            )
        )
        return self.async_show_form(step_id="sun_protect", data_schema=vol.Schema(schema))

    async def async_step_phytolamp(self, user_input=None):
        errors = {}
        has_blinds_module = MODE_BLINDS in (self._data.get("modes", []) or [])
        if user_input is not None:
            if not user_input.get("phytolamp"):
                errors["phytolamp"] = "no_phytolamp"
            else:
                use_main = (
                    bool(
                        user_input.get(
                            "phytolamp_use_main_settings",
                            DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                        )
                    )
                    if has_blinds_module
                    else False
                )
                user_input["phytolamp_use_main_settings"] = use_main
                self._data.update(user_input)

                if not use_main:
                    self._steps_queue = ["phytolamp_settings"] + self._steps_queue
                else:
                    self._data["phytolamp_use_sun"] = False
                    self._data["phytolamp_use_illuminance"] = False
                    self._data["phytolamp_use_forecast"] = False
                return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema, "phytolamp", ["switch", "light"],
            self._get_val("phytolamp"), multiple=True, required=True,
        )
        if has_blinds_module:
            schema[
                vol.Optional(
                    "phytolamp_use_main_settings",
                    default=self._get_val(
                        "phytolamp_use_main_settings",
                        DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                    ),
                )
            ] = selector.BooleanSelector()
        else:
            schema[
                vol.Optional(
                    "split_weekend_schedule",
                    default=self._get_val(
                        "split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE
                    ),
                )
            ] = selector.BooleanSelector()
        return self.async_show_form(step_id="phytolamp", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_phytolamp_settings(self, user_input=None):
        if user_input is not None:
            if "phytolamp_on_time_daily" in user_input:
                user_input["phytolamp_on_time_workday"] = user_input.pop("phytolamp_on_time_daily")
            user_input = _apply_phytolamp_extras(user_input)
            self._data.update(user_input)

            inject_steps = []
            if user_input.get("phytolamp_use_sun"):
                inject_steps.append("phytolamp_sun")
            if user_input.get("phytolamp_use_forecast"):
                inject_steps.append("phytolamp_weather")
            if user_input.get("phytolamp_use_illuminance"):
                inject_steps.append("phytolamp_illuminance")

            self._steps_queue = inject_steps + self._steps_queue
            return await self._async_next_step()

        split = bool(self._get_val("split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE))
        schema = {}
        if MODE_SUN_PROTECT not in self._get_val("modes", []):
            _add_entity_selector(schema, "sun_sensor", "sun", self._get_val("sun_sensor", DEFAULT_SUN_SENSOR))
        schema[vol.Optional(
            "phytolamp_extras",
            default=_phytolamp_extras_default(self._get_val),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    "phytolamp_use_sun",
                    "phytolamp_use_illuminance",
                    "phytolamp_use_forecast",
                ],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="phytolamp_extras",
            )
        )
        if split:
            schema[vol.Optional("phytolamp_on_time_workday", default=self._get_val("phytolamp_on_time_workday", DEFAULT_PHYTOLAMP_ON_WORKDAY))] = selector.TimeSelector()
            schema[vol.Optional("phytolamp_on_time_weekend", default=self._get_val("phytolamp_on_time_weekend", DEFAULT_PHYTOLAMP_ON_WEEKEND))] = selector.TimeSelector()
        else:
            schema[vol.Optional("phytolamp_on_time_daily", default=self._get_val("phytolamp_on_time_workday", DEFAULT_PHYTOLAMP_ON_WORKDAY))] = selector.TimeSelector()
        schema[vol.Optional("phytolamp_off_time", default=self._get_val("phytolamp_off_time", DEFAULT_PHYTOLAMP_OFF_TIME))] = selector.TimeSelector()
        if split and MODE_BLINDS not in (self._data.get("modes", []) or []):
            _add_cycle_schedule_fields(schema, self._get_val)
        return self.async_show_form(step_id="phytolamp_settings", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_sun(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        def_az = self._get_val("phytolamp_sun_azimuth", self._get_val("sun_azimuth", DEFAULT_SUN_AZIMUTH))
        def_el = self._get_val("phytolamp_sun_elevation", self._get_val("sun_elevation", DEFAULT_SUN_ELEVATION))
        schema = {
            vol.Optional("phytolamp_sun_azimuth", default=def_az): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=359, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
            ),
            vol.Optional("phytolamp_sun_elevation", default=def_el): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
            ),
        }
        return self.async_show_form(step_id="phytolamp_sun", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_weather(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        def_sensor = self._get_val("phytolamp_forecast_sensor", self._get_val("forecast_sensor"))
        def_forecasts = self._get_val("phytolamp_forecasts", self._get_val("forecasts", DEFAULT_FORECASTS))
        _add_entity_selector(schema, "phytolamp_forecast_sensor", "weather", def_sensor, required=True)
        schema[vol.Optional("phytolamp_forecasts", default=def_forecasts)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["sunny", "partlycloudy", "cloudy", "fog"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="forecasts",
            )
        )
        return self.async_show_form(step_id="phytolamp_weather", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_illuminance(self, user_input=None):
        if user_input is not None:
            if not user_input.get("phytolamp_illuminance_sensor") and self._get_val("illuminance_sensor"):
                user_input["phytolamp_illuminance_sensor"] = self._get_val("illuminance_sensor")
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        main_lux_sensor = self._get_val("illuminance_sensor")
        def_sensor = self._get_val("phytolamp_illuminance_sensor", main_lux_sensor)
        def_min = self._get_val("phytolamp_min_illuminance", self._get_val("min_illuminance", DEFAULT_MIN_ILLUMINANCE))
        def_max = self._get_val("phytolamp_max_illuminance", self._get_val("max_illuminance", DEFAULT_MAX_ILLUMINANCE))
        def_delay = self._get_val("phytolamp_illuminance_delay", self._get_val("illuminance_delay", DEFAULT_ILLUMINANCE_DELAY))
        _add_entity_selector(
            schema, "phytolamp_illuminance_sensor", "sensor",
            def_sensor,
            device_class="illuminance", required=not bool(main_lux_sensor),
        )
        schema[vol.Optional("phytolamp_min_illuminance", default=def_min)] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Optional("phytolamp_max_illuminance", default=def_max)] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Optional("phytolamp_illuminance_delay", default=def_delay)] = selector.TimeSelector()
        return self.async_show_form(step_id="phytolamp_illuminance", data_schema=vol.Schema(schema))

    async def async_step_watering(self, user_input=None):
        errors = {}
        if user_input is not None:
            valves = user_input.get("watering_valves") or []
            if not valves:
                errors["watering_valves"] = "no_watering_valves"
            else:
                use_moisture = bool(
                    user_input.get("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE)
                )
                user_input["watering_use_moisture"] = use_moisture
                m_mode = user_input.get(
                    "watering_default_morning_mode", DEFAULT_WATERING_MORNING_MODE
                )
                m_dur = int(
                    user_input.get(
                        "watering_default_morning_duration",
                        DEFAULT_WATERING_MORNING_DURATION,
                    )
                )
                e_mode = user_input.get(
                    "watering_default_evening_mode", DEFAULT_WATERING_EVENING_MODE
                )
                e_dur = int(
                    user_input.get(
                        "watering_default_evening_duration",
                        DEFAULT_WATERING_EVENING_DURATION,
                    )
                )
                user_input["watering_zones_config"] = _sync_watering_zones_config(
                    valves,
                    self._get_val("watering_zones_config"),
                    m_mode,
                    m_dur,
                    e_mode,
                    e_dur,
                    overwrite_all=True,
                )
                self._data.update(user_input)
                if use_moisture:
                    self._steps_queue = ["watering_moisture"] + self._steps_queue
                return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema,
            "watering_valves",
            "switch",
            self._get_val("watering_valves"),
            multiple=True,
            required=True,
        )
        schema[
            vol.Optional(
                "watering_use_moisture",
                default=self._get_val("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE),
            )
        ] = selector.BooleanSelector()
        schema[
            vol.Optional(
                "watering_morning_time",
                default=self._get_val("watering_morning_time", DEFAULT_WATERING_MORNING_TIME),
            )
        ] = selector.TimeSelector()
        schema[
            vol.Optional(
                "watering_evening_time",
                default=self._get_val("watering_evening_time", DEFAULT_WATERING_EVENING_TIME),
            )
        ] = selector.TimeSelector()
        schema[
            vol.Optional(
                "watering_default_morning_mode",
                default=self._get_val(
                    "watering_default_morning_mode", DEFAULT_WATERING_MORNING_MODE
                ),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=WATERING_MODES,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="watering_mode",
            )
        )
        schema[
            vol.Optional(
                "watering_default_morning_duration",
                default=self._get_val(
                    "watering_default_morning_duration",
                    DEFAULT_WATERING_MORNING_DURATION,
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=600,
                step=1,
                unit_of_measurement="s",
                mode=selector.NumberSelectorMode.BOX,
            )
        )
        schema[
            vol.Optional(
                "watering_default_evening_mode",
                default=self._get_val(
                    "watering_default_evening_mode", DEFAULT_WATERING_EVENING_MODE
                ),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=WATERING_MODES,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="watering_mode",
            )
        )
        schema[
            vol.Optional(
                "watering_default_evening_duration",
                default=self._get_val(
                    "watering_default_evening_duration",
                    DEFAULT_WATERING_EVENING_DURATION,
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=600,
                step=1,
                unit_of_measurement="s",
                mode=selector.NumberSelectorMode.BOX,
            )
        )
        return self.async_show_form(
            step_id="watering", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_watering_moisture(self, user_input=None):
        valves: list[str] = list(self._get_val("watering_valves", []) or [])
        current_map: dict = dict(self._get_val("watering_moisture_map", {}) or {})
        used_labels: set[str] = set()
        label_to_valve: dict[str, str] = {}
        for v in valves:
            lbl = _valve_field_label(self.hass, v, used_labels)
            label_to_valve[lbl] = v

        if user_input is not None:
            if "watering_soil_threshold" in user_input:
                self._data["watering_soil_threshold"] = user_input["watering_soil_threshold"]
            new_map: dict[str, str] = {}
            for lbl, v in label_to_valve.items():
                sensor_id = user_input.get(lbl)
                if sensor_id:
                    new_map[v] = sensor_id
            self._data["watering_moisture_map"] = new_map
            return await self._async_next_step()

        schema: dict = {
            vol.Optional(
                "watering_soil_threshold",
                default=self._get_val(
                    "watering_soil_threshold", DEFAULT_WATERING_SOIL_THRESHOLD
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            )
        }
        for lbl, v in label_to_valve.items():
            _add_entity_selector(
                schema,
                lbl,
                "sensor",
                current_map.get(v),
                multiple=False,
                device_class=["moisture", "humidity"],
                required=False,
            )
        return self.async_show_form(
            step_id="watering_moisture", data_schema=vol.Schema(schema)
        )

    async def async_step_sun_protect_angles(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        schema[vol.Optional("sun_azimuth", default=self._get_val("sun_azimuth", DEFAULT_SUN_AZIMUTH))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=359, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
        )
#        _add_entity_selector(schema, "sun_azimuth_sensor", ["sensor", "input_number"], self._get_val("sun_azimuth_sensor"))
        schema[vol.Optional("sun_elevation", default=self._get_val("sun_elevation", DEFAULT_SUN_ELEVATION))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
        )
#        _add_entity_selector(schema, "sun_elevation_sensor", ["sensor", "input_number"], self._get_val("sun_elevation_sensor"))
        return self.async_show_form(step_id="sun_protect_angles", data_schema=vol.Schema(schema))

    async def async_step_weather(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "forecast_sensor", "weather", self._get_val("forecast_sensor"), required=True)
        schema[vol.Optional("forecasts", default=self._get_val("forecasts", DEFAULT_FORECASTS))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["sunny", "partlycloudy", "cloudy", "fog"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="forecasts",
            )
        )
        return self.async_show_form(step_id="weather", data_schema=vol.Schema(schema))

    async def async_step_illuminance(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema, "illuminance_sensor", "sensor",
            self._get_val("illuminance_sensor"),
            device_class="illuminance", required=True,
        )
        schema[vol.Optional("min_illuminance", default=self._get_val("min_illuminance", DEFAULT_MIN_ILLUMINANCE))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Optional("max_illuminance", default=self._get_val("max_illuminance", DEFAULT_MAX_ILLUMINANCE))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Optional("illuminance_delay", default=self._get_val("illuminance_delay", DEFAULT_ILLUMINANCE_DELAY))] = selector.TimeSelector()
        return self.async_show_form(step_id="illuminance", data_schema=vol.Schema(schema))

    async def async_step_yandex(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        is_ru = str(getattr(self.hass.config, "language", "ru") or "ru").lower().startswith("ru")
        def_open = DEFAULT_YANDEX_INTENT_OPEN if is_ru else ""
        def_close = DEFAULT_YANDEX_INTENT_CLOSE if is_ru else ""
        def_pos = DEFAULT_YANDEX_INTENT_POSITION if is_ru else ""
        def_status = DEFAULT_YANDEX_INTENT_STATUS if is_ru else ""

        schema = {
            vol.Optional(
                "voice_engine",
                default=self._get_val("voice_engine", DEFAULT_VOICE_ENGINE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[VOICE_ENGINE_YANDEX, VOICE_ENGINE_ASSIST, VOICE_ENGINE_CUSTOM],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="voice_engine",
                )
            ),
            vol.Optional("yandex_intent_open", default=self._get_val("yandex_intent_open", def_open)): selector.TextSelector(),
            vol.Optional("yandex_intent_close", default=self._get_val("yandex_intent_close", def_close)): selector.TextSelector(),
            vol.Optional("yandex_intent_position", default=self._get_val("yandex_intent_position", def_pos)): selector.TextSelector(),
            vol.Optional("yandex_intent_status", default=self._get_val("yandex_intent_status", def_status)): selector.TextSelector(),
        }
        _add_entity_selector(schema, "yandex_media_player", "media_player", self._get_val("yandex_media_player"), multiple=True)
        _add_entity_selector(schema, "tts_entity", "tts", self._get_val("tts_entity"), multiple=False)
        schema[vol.Optional("voice_event", default=self._get_val("voice_event", DEFAULT_VOICE_EVENT))] = selector.TextSelector()
        schema[vol.Optional("yandex_volume", default=self._get_val("yandex_volume", DEFAULT_YANDEX_VOLUME))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=100, step=10, mode=selector.NumberSelectorMode.SLIDER)
        )
        return self.async_show_form(step_id="yandex", data_schema=vol.Schema(schema))

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        filters = [
            selector.EntityFilterSelectorConfig(integration="mqtt"),
            selector.EntityFilterSelectorConfig(integration="zha"),
        ]
        _add_device_selector(schema, "slider_device", filters, self._get_val("slider_device"), required=True)
        schema[vol.Optional("slider_mode", default=self._get_val("slider_mode", DEFAULT_SLIDER_MODE))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[SLIDER_MODE_FULL, SLIDER_MODE_STEP, SLIDER_MODE_PROPORTIONAL],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="slider_mode",
            )
        )
        schema[vol.Optional("slider_step", default=self._get_val("slider_step", DEFAULT_SLIDER_STEP))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=50, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Optional("slider_fast_speed", default=self._get_val("slider_fast_speed", DEFAULT_SLIDER_FAST_SPEED))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=300, step=5, unit_of_measurement="mm/s", mode=selector.NumberSelectorMode.BOX)
        )
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_device_payloads(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        if self._is_mqtt_device(self._data.get("slider_device")):
            schema[vol.Optional("basic_topic", default=self._get_val("basic_topic", DEFAULT_BASIC_TOPIC))] = selector.TextSelector()
        schema[vol.Optional("payload_up", default=self._get_val("payload_up", DEFAULT_PAYLOAD_UP))] = selector.TextSelector()
        schema[vol.Optional("payload_down", default=self._get_val("payload_down", DEFAULT_PAYLOAD_DOWN))] = selector.TextSelector()
        schema[vol.Optional("payload_stop", default=self._get_val("payload_stop", DEFAULT_PAYLOAD_STOP))] = selector.TextSelector()
        return self.async_show_form(step_id="device_payloads", data_schema=vol.Schema(schema))

    async def async_step_limits(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        schema[vol.Optional("up_limit", default=self._get_val("up_limit", DEFAULT_UP_LIMIT))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
        )
#        _add_entity_selector(schema, "up_limit_sensor", ["sensor", "input_number"], self._get_val("up_limit_sensor"))
        schema[vol.Optional("down_limit", default=self._get_val("down_limit", DEFAULT_DOWN_LIMIT))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
        )
#        _add_entity_selector(schema, "down_limit_sensor", ["sensor", "input_number"], self._get_val("down_limit_sensor"))
        return self.async_show_form(step_id="limits", data_schema=vol.Schema(schema))

    async def async_step_time(self, user_input=None):
        if user_input is not None:
            if "up_time_daily" in user_input:
                user_input["up_time_workday"] = user_input.pop("up_time_daily")
            self._data.update(user_input)
            return await self._async_next_step()

        split = bool(self._get_val("split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE))
        schema = {
            vol.Optional("open_at_sunrise", default=self._get_val("open_at_sunrise", DEFAULT_OPEN_AT_SUNRISE)): selector.BooleanSelector(),
        }
        if split:
            schema[vol.Optional("up_time_workday", default=self._get_val("up_time_workday", DEFAULT_OPEN_TIME_WORKDAY))] = selector.TimeSelector()
            schema[vol.Optional("up_time_weekend", default=self._get_val("up_time_weekend", DEFAULT_OPEN_TIME_WEEKEND))] = selector.TimeSelector()
        else:
            schema[vol.Optional("up_time_daily", default=self._get_val("up_time_workday", DEFAULT_OPEN_TIME_WORKDAY))] = selector.TimeSelector()
        schema[vol.Optional("close_at_sunset", default=self._get_val("close_at_sunset", DEFAULT_CLOSE_AT_SUNSET))] = selector.BooleanSelector()
        schema[vol.Optional("down_time", default=self._get_val("down_time", DEFAULT_CLOSE_TIME))] = selector.TimeSelector()
        if split:
            _add_cycle_schedule_fields(schema, self._get_val)
        return self.async_show_form(step_id="time", data_schema=vol.Schema(schema))

    async def async_step_repeats(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {
            vol.Optional("repeat_for", default=self._get_val("repeat_for", DEFAULT_REPEAT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=5, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional("delay_for_repeat", default=self._get_val("delay_for_repeat", DEFAULT_REPEAT_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=10, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional("movement_time", default=self._get_val("movement_time", DEFAULT_MOVEMENT_TIME)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=120, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
            ),
        }
        return self.async_show_form(step_id="repeats", data_schema=vol.Schema(schema))

    async def async_step_logging(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "notify_target", "notify", self._get_val("notify_target"), multiple=True)
        _add_entity_selector(schema, "yandex_media_player", "media_player", self._get_val("yandex_media_player"), multiple=True)
        schema[
            vol.Optional(
                "voice_engine",
                default=self._get_val("voice_engine", DEFAULT_VOICE_ENGINE),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[VOICE_ENGINE_YANDEX, VOICE_ENGINE_ASSIST],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="voice_engine",
            )
        )
        _add_entity_selector(schema, "tts_entity", "tts", self._get_val("tts_entity"), multiple=False)
        schema[
            vol.Optional(
                "low_battery_threshold",
                default=self._get_val(
                    "low_battery_threshold", DEFAULT_LOW_BATTERY_THRESHOLD
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5,
                max=50,
                step=1,
                unit_of_measurement="%",
                mode=selector.NumberSelectorMode.SLIDER,
            )
        )
        # schema[vol.Optional("yandex_volume", default=self._get_val("yandex_volume", DEFAULT_YANDEX_VOLUME))] = selector.NumberSelector(
        #     selector.NumberSelectorConfig(min=10, max=100, step=10, mode=selector.NumberSelectorMode.SLIDER)
        # )
        return self.async_show_form(step_id="logging", data_schema=vol.Schema(schema))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LoggiaOptionsFlow(config_entry)


class LoggiaOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self._config_entry = config_entry
        self._options = dict(config_entry.options)
        for k, v in config_entry.data.items():
            if k not in self._options:
                self._options[k] = v

        raw_modes = list(self._options.get("modes", []) or [])
        if not self._options.get("_modular_v2") and self._options.get("blinds"):
            if MODE_BLINDS not in raw_modes:
                raw_modes.insert(0, MODE_BLINDS)
            self._options["modes"] = raw_modes

        self._initial_modes: set[str] = set(raw_modes)
        self._edit_existing: bool = False
        self._steps_queue: list[str] = []
        self._completed_steps: set[str] = set()

    def _get_val(self, key, default=None):
        return self._options.get(key, default)

    def _has_subdevice(self, group: str) -> bool:
        """Проверяет, существует ли уже подустройство данной группы."""
        registry = dr.async_get(self.hass)
        target_identifier = (DOMAIN, f"{self._config_entry.entry_id}_{group}")
        for device in dr.async_entries_for_config_entry(
            registry, self._config_entry.entry_id
        ):
            if target_identifier in device.identifiers:
                return True
        return False

    def _has_entity(self, platform: str, key: str) -> bool:
        """Проверяет, существует ли уже сущность с данным ключом."""
        registry = er.async_get(self.hass)
        return (
            registry.async_get_entity_id(
                platform, DOMAIN, f"{self._config_entry.entry_id}_{key}"
            )
            is not None
        )

    def _is_mqtt_device(self, device_id: str) -> bool:
        if not device_id:
            return False
        registry = dr.async_get(self.hass)
        device = registry.async_get(device_id)
        if device:
            for identifier in device.identifiers:
                if identifier[0] == "mqtt":
                    return True
        return False

    def _build_steps_queue(self, edit_existing: bool = False) -> list[str]:
        modes = self._options.get("modes", []) or []
        target_modes = (
            modes
            if edit_existing
            else [m for m in modes if m not in self._initial_modes]
        )
        queue = []
        if MODE_BLINDS in target_modes:
            queue.append("blinds")
        if MODE_PHYTOLAMP in target_modes:
            queue.append("phytolamp")
        if MODE_WATERING in target_modes:
            queue.append("watering")
        if MODE_LOGGING in target_modes:
            queue.append("logging")
        return queue

    async def _async_next_step(self):
        if not self._steps_queue:
            return self.async_create_entry(title="", data=self._options)
        next_step = self._steps_queue.pop(0)
        self._completed_steps.add(next_step)
        return await getattr(self, f"async_step_{next_step}")()

    async def async_step_init(self, user_input=None):
        errors = {}
        allowed_modules = [
            MODE_BLINDS,
            MODE_PHYTOLAMP,
            MODE_WATERING,
        ]
        blinds_submodes = [MODE_SUN_PROTECT, MODE_SLIDER]
        current_modes = list(self._get_val("modes", []) or [])

        if user_input is not None:
            selected_modules = [
                m for m in (user_input.get("modes") or []) if m in allowed_modules
            ]
            if not selected_modules:
                errors["modes"] = "no_modules"
            else:
                edit_existing = bool(user_input.get("edit_existing_modes", False))
                enable_logging = bool(user_input.get("enable_logging", False))
                self._edit_existing = edit_existing

                new_modes = list(selected_modules)
                if MODE_BLINDS in selected_modules:
                    for sub in blinds_submodes:
                        if sub in current_modes and sub not in new_modes:
                            new_modes.append(sub)
                if enable_logging:
                    new_modes.append(MODE_LOGGING)

                self._options["_modular_v2"] = True
                self._options["modes"] = new_modes
                self._steps_queue = self._build_steps_queue(edit_existing=edit_existing)
                return await self._async_next_step()

        default_modules = [m for m in current_modes if m in allowed_modules]
        default_logging = MODE_LOGGING in current_modes

        schema = {
            vol.Optional("modes", default=default_modules): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=allowed_modules,
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                    translation_key="modes",
                )
            ),
            vol.Optional("enable_logging", default=default_logging): selector.BooleanSelector(),
            vol.Optional("edit_existing_modes", default=False): selector.BooleanSelector(),
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_blinds(self, user_input=None):
        errors = {}
        blinds_submodes = [MODE_SUN_PROTECT, MODE_SLIDER]
        if user_input is not None:
            if not user_input.get("blinds"):
                errors["blinds"] = "no_blinds"
            else:
                selected_sub = [
                    m for m in (user_input.pop("blinds_modes", []) or []) if m in blinds_submodes
                ]
                selected_blinds = set(user_input.get("blinds", []))
                if "excluded_blinds" in self._options:
                    self._options["excluded_blinds"] = [
                        b for b in self._options["excluded_blinds"] if b in selected_blinds
                    ]
                base_modes = [
                    m for m in (self._options.get("modes", []) or []) if m not in blinds_submodes
                ]
                self._options["modes"] = base_modes + selected_sub
                self._options.update(user_input)

                inject_steps = []
                if MODE_SUN_PROTECT in selected_sub and (
                    self._edit_existing or MODE_SUN_PROTECT not in self._initial_modes
                ):
                    inject_steps.append("sun_protect")
                if MODE_SLIDER in selected_sub and (
                    self._edit_existing or MODE_SLIDER not in self._initial_modes
                ):
                    inject_steps.append("device")
                    inject_steps.append("device_payloads")
                if not self._has_subdevice("drives"):
                    inject_steps.extend(["limits", "time", "repeats"])
                elif bool(
                    self._options.get(
                        "split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE
                    )
                ):
                    inject_steps.append("time")

                self._steps_queue = inject_steps + self._steps_queue
                return await self._async_next_step()

        default_sub = [
            m for m in (self._get_val("modes", []) or []) if m in blinds_submodes
        ]
        schema = {}
        _add_entity_selector(
            schema, "blinds", "cover", self._get_val("blinds"), multiple=True, required=True
        )
        schema[vol.Optional("blinds_modes", default=default_sub)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=blinds_submodes,
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="blinds_modes",
            )
        )
        schema[
            vol.Optional(
                "split_weekend_schedule",
                default=self._get_val(
                    "split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE
                ),
            )
        ] = selector.BooleanSelector()
        return self.async_show_form(
            step_id="blinds", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_sun_protect(self, user_input=None):
        if user_input is not None:
            user_input.setdefault("blinds_for_protect", [])
            user_input = _apply_sun_protect_extras(user_input)
            self._options.update(user_input)

            inject_steps = []
            if not self._has_subdevice("sun"):
                inject_steps.append("sun_protect_angles")
            if user_input.get("use_forecast"):
                inject_steps.append("weather")
            if user_input.get("use_illuminance"):
                inject_steps.append("illuminance")

            self._steps_queue = inject_steps + self._steps_queue
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "sun_sensor", "sun", self._get_val("sun_sensor", DEFAULT_SUN_SENSOR))
        _add_entity_selector(
            schema,
            "blinds_for_protect",
            "cover",
            self._get_val("blinds_for_protect"),
            multiple=True,
            include_entities=self._get_val("blinds", []),
        )
        schema[vol.Optional(
            "sun_protect_extras",
            default=_sun_protect_extras_default(self._get_val),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["use_forecast", "use_illuminance"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="sun_protect_extras",
            )
        )
        return self.async_show_form(step_id="sun_protect", data_schema=vol.Schema(schema))

    async def async_step_phytolamp(self, user_input=None):
        errors = {}
        has_blinds_module = MODE_BLINDS in (self._options.get("modes", []) or [])
        if user_input is not None:
            if not user_input.get("phytolamp"):
                errors["phytolamp"] = "no_phytolamp"
            else:
                use_main = (
                    bool(
                        user_input.get(
                            "phytolamp_use_main_settings",
                            DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                        )
                    )
                    if has_blinds_module
                    else False
                )
                user_input["phytolamp_use_main_settings"] = use_main
                self._options.update(user_input)

                if not use_main:
                    self._steps_queue = ["phytolamp_settings"] + self._steps_queue
                else:
                    self._options["phytolamp_use_sun"] = False
                    self._options["phytolamp_use_illuminance"] = False
                    self._options["phytolamp_use_forecast"] = False
                return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema, "phytolamp", ["switch", "light"],
            self._get_val("phytolamp"), multiple=True, required=True,
        )
        if has_blinds_module:
            schema[
                vol.Optional(
                    "phytolamp_use_main_settings",
                    default=self._get_val(
                        "phytolamp_use_main_settings",
                        DEFAULT_PHYTOLAMP_USE_MAIN_SETTINGS,
                    ),
                )
            ] = selector.BooleanSelector()
        else:
            schema[
                vol.Optional(
                    "split_weekend_schedule",
                    default=self._get_val(
                        "split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE
                    ),
                )
            ] = selector.BooleanSelector()
        return self.async_show_form(step_id="phytolamp", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_phytolamp_settings(self, user_input=None):
        if user_input is not None:
            if "phytolamp_on_time_daily" in user_input:
                user_input["phytolamp_on_time_workday"] = user_input.pop("phytolamp_on_time_daily")
            user_input = _apply_phytolamp_extras(user_input)
            self._options.update(user_input)

            inject_steps = []
            if (
                user_input.get("phytolamp_use_sun")
                and not self._has_entity("number", "phytolamp_sun_azimuth")
            ):
                inject_steps.append("phytolamp_sun")
            if user_input.get("phytolamp_use_forecast"):
                inject_steps.append("phytolamp_weather")
            if user_input.get("phytolamp_use_illuminance"):
                inject_steps.append("phytolamp_illuminance")

            self._steps_queue = inject_steps + self._steps_queue
            return await self._async_next_step()

        split = bool(self._get_val("split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE))
        schema = {}
        if MODE_SUN_PROTECT not in self._get_val("modes", []):
            _add_entity_selector(schema, "sun_sensor", "sun", self._get_val("sun_sensor", DEFAULT_SUN_SENSOR))
        schema[vol.Optional(
            "phytolamp_extras",
            default=_phytolamp_extras_default(self._get_val),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    "phytolamp_use_sun",
                    "phytolamp_use_illuminance",
                    "phytolamp_use_forecast",
                ],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="phytolamp_extras",
            )
        )
        if not self._has_entity("time", "phytolamp_on_time_workday"):
            if split:
                schema[vol.Optional("phytolamp_on_time_workday", default=self._get_val("phytolamp_on_time_workday", DEFAULT_PHYTOLAMP_ON_WORKDAY))] = selector.TimeSelector()
                schema[vol.Optional("phytolamp_on_time_weekend", default=self._get_val("phytolamp_on_time_weekend", DEFAULT_PHYTOLAMP_ON_WEEKEND))] = selector.TimeSelector()
            else:
                schema[vol.Optional("phytolamp_on_time_daily", default=self._get_val("phytolamp_on_time_workday", DEFAULT_PHYTOLAMP_ON_WORKDAY))] = selector.TimeSelector()
            schema[vol.Optional("phytolamp_off_time", default=self._get_val("phytolamp_off_time", DEFAULT_PHYTOLAMP_OFF_TIME))] = selector.TimeSelector()
        elif split and not self._has_entity("time", "phytolamp_on_time_weekend"):
            schema[vol.Optional("phytolamp_on_time_weekend", default=self._get_val("phytolamp_on_time_weekend", DEFAULT_PHYTOLAMP_ON_WEEKEND))] = selector.TimeSelector()
        if split and MODE_BLINDS not in (self._options.get("modes", []) or []):
            _add_cycle_schedule_fields(schema, self._get_val)
        return self.async_show_form(step_id="phytolamp_settings", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_sun(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        def_az = self._get_val("phytolamp_sun_azimuth", DEFAULT_SUN_AZIMUTH)
        def_el = self._get_val("phytolamp_sun_elevation", DEFAULT_SUN_ELEVATION)
        schema = {
            vol.Optional("phytolamp_sun_azimuth", default=def_az): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=359, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
            ),
            vol.Optional("phytolamp_sun_elevation", default=def_el): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
            ),
        }
        return self.async_show_form(step_id="phytolamp_sun", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_weather(self, user_input=None):
        if user_input is not None:
            if not user_input.get("phytolamp_forecast_sensor") and self._get_val("forecast_sensor"):
                user_input["phytolamp_forecast_sensor"] = self._get_val("forecast_sensor")
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        main_forecast = self._get_val("forecast_sensor")
        def_sensor = self._get_val("phytolamp_forecast_sensor", main_forecast)
        def_forecasts = self._get_val("phytolamp_forecasts", DEFAULT_FORECASTS)
        _add_entity_selector(schema, "phytolamp_forecast_sensor", "weather", def_sensor, required=not bool(main_forecast))
        schema[vol.Optional("phytolamp_forecasts", default=def_forecasts)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["sunny", "partlycloudy", "cloudy", "fog"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="forecasts",
            )
        )
        return self.async_show_form(step_id="phytolamp_weather", data_schema=vol.Schema(schema))

    async def async_step_phytolamp_illuminance(self, user_input=None):
        if user_input is not None:
            if not user_input.get("phytolamp_illuminance_sensor") and self._get_val("illuminance_sensor"):
                user_input["phytolamp_illuminance_sensor"] = self._get_val("illuminance_sensor")
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        main_lux_sensor = self._get_val("illuminance_sensor")
        def_sensor = self._get_val("phytolamp_illuminance_sensor", main_lux_sensor)
        def_min = self._get_val("phytolamp_min_illuminance", DEFAULT_MIN_ILLUMINANCE)
        def_max = self._get_val("phytolamp_max_illuminance", DEFAULT_MAX_ILLUMINANCE)
        def_delay = self._get_val("phytolamp_illuminance_delay", DEFAULT_ILLUMINANCE_DELAY)
        _add_entity_selector(
            schema, "phytolamp_illuminance_sensor", "sensor",
            def_sensor,
            device_class="illuminance", required=not bool(main_lux_sensor),
        )
        if not self._has_entity("number", "phytolamp_min_illuminance"):
            schema[vol.Optional("phytolamp_min_illuminance", default=def_min)] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
            )
            schema[vol.Optional("phytolamp_max_illuminance", default=def_max)] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
            )
            schema[vol.Optional("phytolamp_illuminance_delay", default=def_delay)] = selector.TimeSelector()
        return self.async_show_form(step_id="phytolamp_illuminance", data_schema=vol.Schema(schema))

    async def async_step_watering(self, user_input=None):
        errors = {}
        has_watering_subdevice = self._has_subdevice("watering")
        if user_input is not None:
            valves = user_input.get("watering_valves") or []
            if not valves:
                errors["watering_valves"] = "no_watering_valves"
            else:
                use_moisture = bool(
                    user_input.get("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE)
                )
                user_input["watering_use_moisture"] = use_moisture
                m_mode = user_input.get(
                    "watering_default_morning_mode",
                    self._get_val(
                        "watering_default_morning_mode", DEFAULT_WATERING_MORNING_MODE
                    ),
                )
                m_dur = int(
                    user_input.get(
                        "watering_default_morning_duration",
                        self._get_val(
                            "watering_default_morning_duration",
                            DEFAULT_WATERING_MORNING_DURATION,
                        ),
                    )
                )
                e_mode = user_input.get(
                    "watering_default_evening_mode",
                    self._get_val(
                        "watering_default_evening_mode", DEFAULT_WATERING_EVENING_MODE
                    ),
                )
                e_dur = int(
                    user_input.get(
                        "watering_default_evening_duration",
                        self._get_val(
                            "watering_default_evening_duration",
                            DEFAULT_WATERING_EVENING_DURATION,
                        ),
                    )
                )
                user_input["watering_zones_config"] = _sync_watering_zones_config(
                    valves,
                    self._get_val("watering_zones_config"),
                    m_mode,
                    m_dur,
                    e_mode,
                    e_dur,
                    overwrite_all=not has_watering_subdevice,
                )
                self._options.update(user_input)
                if use_moisture:
                    self._steps_queue = ["watering_moisture"] + self._steps_queue
                return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema,
            "watering_valves",
            "switch",
            self._get_val("watering_valves"),
            multiple=True,
            required=True,
        )
        schema[
            vol.Optional(
                "watering_use_moisture",
                default=self._get_val("watering_use_moisture", DEFAULT_WATERING_USE_MOISTURE),
            )
        ] = selector.BooleanSelector()

        if not has_watering_subdevice:
            schema[
                vol.Optional(
                    "watering_morning_time",
                    default=self._get_val(
                        "watering_morning_time", DEFAULT_WATERING_MORNING_TIME
                    ),
                )
            ] = selector.TimeSelector()
            schema[
                vol.Optional(
                    "watering_evening_time",
                    default=self._get_val(
                        "watering_evening_time", DEFAULT_WATERING_EVENING_TIME
                    ),
                )
            ] = selector.TimeSelector()
            schema[
                vol.Optional(
                    "watering_default_morning_mode",
                    default=self._get_val(
                        "watering_default_morning_mode", DEFAULT_WATERING_MORNING_MODE
                    ),
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=WATERING_MODES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="watering_mode",
                )
            )
            schema[
                vol.Optional(
                    "watering_default_morning_duration",
                    default=self._get_val(
                        "watering_default_morning_duration",
                        DEFAULT_WATERING_MORNING_DURATION,
                    ),
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=600,
                    step=1,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            )
            schema[
                vol.Optional(
                    "watering_default_evening_mode",
                    default=self._get_val(
                        "watering_default_evening_mode", DEFAULT_WATERING_EVENING_MODE
                    ),
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=WATERING_MODES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="watering_mode",
                )
            )
            schema[
                vol.Optional(
                    "watering_default_evening_duration",
                    default=self._get_val(
                        "watering_default_evening_duration",
                        DEFAULT_WATERING_EVENING_DURATION,
                    ),
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=600,
                    step=1,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            )

        return self.async_show_form(
            step_id="watering", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_watering_moisture(self, user_input=None):
        valves: list[str] = list(self._get_val("watering_valves", []) or [])
        current_map: dict = dict(self._get_val("watering_moisture_map", {}) or {})
        used_labels: set[str] = set()
        label_to_valve: dict[str, str] = {}
        for v in valves:
            lbl = _valve_field_label(self.hass, v, used_labels)
            label_to_valve[lbl] = v

        if user_input is not None:
            if "watering_soil_threshold" in user_input:
                self._options["watering_soil_threshold"] = user_input[
                    "watering_soil_threshold"
                ]
            new_map: dict[str, str] = {}
            for lbl, v in label_to_valve.items():
                sensor_id = user_input.get(lbl)
                if sensor_id:
                    new_map[v] = sensor_id
            self._options["watering_moisture_map"] = new_map
            return await self._async_next_step()

        schema: dict = {}
        if not self._has_entity("number", "watering_soil_threshold"):
            schema[
                vol.Optional(
                    "watering_soil_threshold",
                    default=self._get_val(
                        "watering_soil_threshold", DEFAULT_WATERING_SOIL_THRESHOLD
                    ),
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            )

        for lbl, v in label_to_valve.items():
            _add_entity_selector(
                schema,
                lbl,
                "sensor",
                current_map.get(v),
                multiple=False,
                device_class=["moisture", "humidity"],
                required=False,
            )
        return self.async_show_form(
            step_id="watering_moisture", data_schema=vol.Schema(schema)
        )

    async def async_step_sun_protect_angles(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        schema[vol.Optional("sun_azimuth", default=self._get_val("sun_azimuth", DEFAULT_SUN_AZIMUTH))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=359, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
        )
        schema[vol.Optional("sun_elevation", default=self._get_val("sun_elevation", DEFAULT_SUN_ELEVATION))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°", mode=selector.NumberSelectorMode.SLIDER)
        )
        return self.async_show_form(step_id="sun_protect_angles", data_schema=vol.Schema(schema))

    async def async_step_weather(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "forecast_sensor", "weather", self._get_val("forecast_sensor"), required=True)
        schema[vol.Optional("forecasts", default=self._get_val("forecasts", DEFAULT_FORECASTS))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["sunny", "partlycloudy", "cloudy", "fog"],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="forecasts",
            )
        )
        return self.async_show_form(step_id="weather", data_schema=vol.Schema(schema))

    async def async_step_illuminance(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(
            schema, "illuminance_sensor", "sensor",
            self._get_val("illuminance_sensor"),
            device_class="illuminance", required=True,
        )
        if not self._has_subdevice("illuminance"):
            schema[vol.Optional("min_illuminance", default=self._get_val("min_illuminance", DEFAULT_MIN_ILLUMINANCE))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
            )
            schema[vol.Optional("max_illuminance", default=self._get_val("max_illuminance", DEFAULT_MAX_ILLUMINANCE))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100000, step=100, unit_of_measurement="lx", mode=selector.NumberSelectorMode.BOX)
            )
            schema[vol.Optional("illuminance_delay", default=self._get_val("illuminance_delay", DEFAULT_ILLUMINANCE_DELAY))] = selector.TimeSelector()
        return self.async_show_form(step_id="illuminance", data_schema=vol.Schema(schema))

    async def async_step_yandex(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        is_ru = str(getattr(self.hass.config, "language", "ru") or "ru").lower().startswith("ru")
        def_open = DEFAULT_YANDEX_INTENT_OPEN if is_ru else ""
        def_close = DEFAULT_YANDEX_INTENT_CLOSE if is_ru else ""
        def_pos = DEFAULT_YANDEX_INTENT_POSITION if is_ru else ""
        def_status = DEFAULT_YANDEX_INTENT_STATUS if is_ru else ""

        schema = {
            vol.Optional(
                "voice_engine",
                default=self._get_val("voice_engine", DEFAULT_VOICE_ENGINE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[VOICE_ENGINE_YANDEX, VOICE_ENGINE_ASSIST, VOICE_ENGINE_CUSTOM],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="voice_engine",
                )
            ),
            vol.Optional("yandex_intent_open", default=self._get_val("yandex_intent_open", def_open)): selector.TextSelector(),
            vol.Optional("yandex_intent_close", default=self._get_val("yandex_intent_close", def_close)): selector.TextSelector(),
            vol.Optional("yandex_intent_position", default=self._get_val("yandex_intent_position", def_pos)): selector.TextSelector(),
            vol.Optional("yandex_intent_status", default=self._get_val("yandex_intent_status", def_status)): selector.TextSelector(),
        }
        _add_entity_selector(schema, "yandex_media_player", "media_player", self._get_val("yandex_media_player"), multiple=True)
        _add_entity_selector(schema, "tts_entity", "tts", self._get_val("tts_entity"), multiple=False)
        schema[vol.Optional("voice_event", default=self._get_val("voice_event", DEFAULT_VOICE_EVENT))] = selector.TextSelector()
        if not self._has_entity("number", "yandex_volume"):
            schema[vol.Optional("yandex_volume", default=self._get_val("yandex_volume", DEFAULT_YANDEX_VOLUME))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=100, step=10, mode=selector.NumberSelectorMode.SLIDER)
            )
        return self.async_show_form(step_id="yandex", data_schema=vol.Schema(schema))

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        filters = [
            selector.EntityFilterSelectorConfig(integration="mqtt"),
            selector.EntityFilterSelectorConfig(integration="zha"),
        ]
        _add_device_selector(schema, "slider_device", filters, self._get_val("slider_device"), required=True)
        schema[vol.Optional("slider_mode", default=self._get_val("slider_mode", DEFAULT_SLIDER_MODE))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[SLIDER_MODE_FULL, SLIDER_MODE_STEP, SLIDER_MODE_PROPORTIONAL],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="slider_mode",
            )
        )
        if not self._has_entity("number", "slider_step"):
            schema[vol.Optional("slider_step", default=self._get_val("slider_step", DEFAULT_SLIDER_STEP))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
            )
            schema[vol.Optional("slider_fast_speed", default=self._get_val("slider_fast_speed", DEFAULT_SLIDER_FAST_SPEED))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=300, step=5, unit_of_measurement="mm/s", mode=selector.NumberSelectorMode.BOX)
            )
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_device_payloads(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        if self._is_mqtt_device(self._options.get("slider_device")):
            schema[vol.Optional("basic_topic", default=self._get_val("basic_topic", DEFAULT_BASIC_TOPIC))] = selector.TextSelector()
        schema[vol.Optional("payload_up", default=self._get_val("payload_up", DEFAULT_PAYLOAD_UP))] = selector.TextSelector()
        schema[vol.Optional("payload_down", default=self._get_val("payload_down", DEFAULT_PAYLOAD_DOWN))] = selector.TextSelector()
        schema[vol.Optional("payload_stop", default=self._get_val("payload_stop", DEFAULT_PAYLOAD_STOP))] = selector.TextSelector()
        return self.async_show_form(step_id="device_payloads", data_schema=vol.Schema(schema))

    async def async_step_limits(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {
            vol.Optional("up_limit", default=self._get_val("up_limit", DEFAULT_UP_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
            ),
            vol.Optional("down_limit", default=self._get_val("down_limit", DEFAULT_DOWN_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
            ),
        }
        return self.async_show_form(step_id="limits", data_schema=vol.Schema(schema))

    async def async_step_time(self, user_input=None):
        if user_input is not None:
            if "up_time_daily" in user_input:
                user_input["up_time_workday"] = user_input.pop("up_time_daily")
            self._options.update(user_input)
            return await self._async_next_step()

        split = bool(self._get_val("split_weekend_schedule", DEFAULT_SPLIT_WEEKEND_SCHEDULE))
        schema = {}
        if not self._has_entity("time", "up_time_workday"):
            schema[vol.Optional("open_at_sunrise", default=self._get_val("open_at_sunrise", DEFAULT_OPEN_AT_SUNRISE))] = selector.BooleanSelector()
            if split:
                schema[vol.Optional("up_time_workday", default=self._get_val("up_time_workday", DEFAULT_OPEN_TIME_WORKDAY))] = selector.TimeSelector()
                schema[vol.Optional("up_time_weekend", default=self._get_val("up_time_weekend", DEFAULT_OPEN_TIME_WEEKEND))] = selector.TimeSelector()
            else:
                schema[vol.Optional("up_time_daily", default=self._get_val("up_time_workday", DEFAULT_OPEN_TIME_WORKDAY))] = selector.TimeSelector()
            schema[vol.Optional("close_at_sunset", default=self._get_val("close_at_sunset", DEFAULT_CLOSE_AT_SUNSET))] = selector.BooleanSelector()
            schema[vol.Optional("down_time", default=self._get_val("down_time", DEFAULT_CLOSE_TIME))] = selector.TimeSelector()
        elif split and not self._has_entity("time", "up_time_weekend"):
            schema[vol.Optional("up_time_weekend", default=self._get_val("up_time_weekend", DEFAULT_OPEN_TIME_WEEKEND))] = selector.TimeSelector()
        if split:
            _add_cycle_schedule_fields(schema, self._get_val)
        return self.async_show_form(step_id="time", data_schema=vol.Schema(schema))

    async def async_step_repeats(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {
            vol.Optional("repeat_for", default=self._get_val("repeat_for", DEFAULT_REPEAT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=5, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional("delay_for_repeat", default=self._get_val("delay_for_repeat", DEFAULT_REPEAT_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=10, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional("movement_time", default=self._get_val("movement_time", DEFAULT_MOVEMENT_TIME)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=120, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
            ),
        }
        return self.async_show_form(step_id="repeats", data_schema=vol.Schema(schema))

    async def async_step_logging(self, user_input=None):
        if user_input is not None:
            self._options.update(user_input)
            return await self._async_next_step()

        schema = {}
        _add_entity_selector(schema, "notify_target", "notify", self._get_val("notify_target"), multiple=True)
        _add_entity_selector(schema, "yandex_media_player", "media_player", self._get_val("yandex_media_player"), multiple=True)
        schema[
            vol.Optional(
                "voice_engine",
                default=self._get_val("voice_engine", DEFAULT_VOICE_ENGINE),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[VOICE_ENGINE_YANDEX, VOICE_ENGINE_ASSIST],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="voice_engine",
            )
        )
        _add_entity_selector(schema, "tts_entity", "tts", self._get_val("tts_entity"), multiple=False)
        if not self._has_entity("number", "low_battery_threshold"):
            schema[
                vol.Optional(
                    "low_battery_threshold",
                    default=self._get_val(
                        "low_battery_threshold", DEFAULT_LOW_BATTERY_THRESHOLD
                    ),
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=50,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            )
        # if not self._has_entity("number", "yandex_volume"):
        #     schema[vol.Optional("yandex_volume", default=self._get_val("yandex_volume", DEFAULT_YANDEX_VOLUME))] = selector.NumberSelector(
        #         selector.NumberSelectorConfig(min=10, max=100, step=10, mode=selector.NumberSelectorMode.SLIDER)
        #     )
        return self.async_show_form(step_id="logging", data_schema=vol.Schema(schema))
