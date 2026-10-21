"""Диагностика интеграции Домашняя оранжерея (кнопка «Скачать диагностику» в Home Assistant)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN
from .manager import LoggiaManager

TO_REDACT = {"latitude", "longitude", "unique_id"}


def _serialize_state(hass: HomeAssistant, entity_id: str | None) -> dict[str, Any] | None:
    """Сериализовать текущее состояние и атрибуты сущности Home Assistant."""
    if not entity_id:
        return None
    st = hass.states.get(entity_id)
    if st is None:
        return {"entity_id": entity_id, "state": "missing"}
    return {
        "entity_id": entity_id,
        "name": st.name,
        "state": st.state,
        "attributes": async_redact_data(dict(st.attributes), TO_REDACT),
        "last_changed": st.last_changed.isoformat() if st.last_changed else None,
        "last_updated": st.last_updated.isoformat() if st.last_updated else None,
    }


def _build_common_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, manager: LoggiaManager | None
) -> dict[str, Any]:
    """Собрать полную диагностическую сводку по интеграции и внешним устройствам."""
    data: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": getattr(entry, "minor_version", 1),
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
    }
    if manager is None:
        return data

    # Состояния собственных сущностей интеграции
    own_entities: dict[str, Any] = {}
    for key, ent in manager.config_entities.items():
        ent_id = getattr(ent, "entity_id", None)
        own_entities[key] = _serialize_state(hass, ent_id) if ent_id else {
            "native_value": getattr(ent, "native_value", None),
        }

    # Состояния подключённого внешнего оборудования и датчиков
    external_sensors: dict[str, Any] = {}
    for sensor_key in (
        "sun_sensor",
        "forecast_sensor",
        "illuminance_sensor",
        "phytolamp_forecast_sensor",
        "phytolamp_illuminance_sensor",
    ):
        s_id = manager.get_setting(sensor_key)
        if s_id:
            external_sensors[sensor_key] = _serialize_state(hass, s_id)

    moisture_map = manager.watering_moisture_map
    moisture_states = {
        valve_id: _serialize_state(hass, sensor_id)
        for valve_id, sensor_id in moisture_map.items()
        if sensor_id
    }

    data["runtime"] = {
        "modes": manager.modes,
        "active_groups": sorted(manager.active_groups),
        "excluded_blinds": sorted(manager.excluded_blinds),
        "excluded_watering_morning": sorted(manager.excluded_watering_morning),
        "excluded_watering_evening": sorted(manager.excluded_watering_evening),
        "is_sun_protecting": manager._is_sun_protecting,
        "is_phytolamp_sun_off": manager._is_phytolamp_sun_off,
        "last_target_position": manager._last_target_position,
        "schedule_flags": {
            "split_weekend_schedule": manager.split_weekend_schedule,
            "is_weekend_today": manager._is_weekend_day(),
            "last_day_opened": manager._last_day_opened,
            "last_day_closed": manager._last_day_closed,
            "last_day_phytolamp_on": manager._last_day_phytolamp_on,
            "last_day_phytolamp_off": manager._last_day_phytolamp_off,
            "last_day_watering_morning": manager._last_day_watering_morning,
            "last_day_watering_evening": manager._last_day_watering_evening,
        },
        "errors": {
            "failed_blinds": list(manager._failed_blind_ids),
            "failed_phytolamps": manager.failed_phytolamps,
            "watering_valve_errors": manager.watering_valve_errors,
            "watering_sensor_errors": manager.watering_sensor_errors,
            "low_battery_devices": {k: {"name": v[0], "battery": v[1]} for k, v in manager._low_battery_devices.items()},
        },
        "watering_zones_config": dict(manager._watering_zones_config),
    }
    data["integration_entities"] = own_entities
    data["external_entities"] = {
        "blinds": [_serialize_state(hass, b) for b in manager.all_blinds],
        "protect_blinds": [_serialize_state(hass, b) for b in manager.protect_blinds],
        "phytolamps": [_serialize_state(hass, l_id) for l_id in manager.phytolamps],
        "watering_valves": [
            _serialize_state(hass, v_id) for v_id in manager.watering_valves
        ],
        "watering_moisture_sensors": moisture_states,
        "environment_sensors": external_sensors,
    }
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Вернуть диагностические данные для всей записи конфигурации (ConfigEntry)."""
    manager: LoggiaManager | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    return _build_common_diagnostics(hass, entry, manager)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> dict[str, Any]:
    """Вернуть диагностические данные для конкретного устройства или подустройства."""
    manager: LoggiaManager | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    diag = _build_common_diagnostics(hass, entry, manager)

    ent_reg = er.async_get(hass)
    device_entities = [
        _serialize_state(hass, ent_entry.entity_id)
        for ent_entry in er.async_entries_for_device(
            ent_reg, device.id, include_disabled_entities=True
        )
    ]

    diag["device"] = {
        "name": device.name,
        "name_by_user": device.name_by_user,
        "model": device.model,
        "manufacturer": device.manufacturer,
        "area_id": device.area_id,
        "entities": device_entities,
    }
    return diag
