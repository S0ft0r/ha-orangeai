"""Интеграция Лоджия — Умные шторы."""

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import Platform
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)

from .const import DOMAIN, ENTITY_GROUP
from .manager import LoggiaManager

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS: list[Platform] = [
    Platform.COVER,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.TIME,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Загрузка интеграции и запуск менеджера."""
    manager = LoggiaManager(hass, entry)
    await manager.async_init_translations()
    _LOGGER.info("%s", manager.tr_log("log_setup_entry", title=entry.title))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    if not hass.data[DOMAIN].get("_frontend_registered"):
        js_file = Path(__file__).parent / "frontend" / f"{DOMAIN}-icons.js"
        if js_file.is_file() and getattr(hass, "http", None) is not None:
            url_path = f"/{DOMAIN}_static/{DOMAIN}-icons.js"
            try:
                if hasattr(hass.http, "async_register_static_paths"):
                    await hass.http.async_register_static_paths(
                        [StaticPathConfig(url_path, str(js_file), cache_headers=False)]
                    )
                elif hasattr(hass.http, "register_static_path"):
                    hass.http.register_static_path(
                        url_path, str(js_file), cache_headers=False
                    )
                ver = int(js_file.stat().st_mtime)
                add_extra_js_url(hass, f"{url_path}?v={ver}")
                hass.data[DOMAIN]["_frontend_registered"] = True
            except Exception as err:
                _LOGGER.warning("Failed to register %s custom icons: %s", DOMAIN, err)

    dev_reg = dr.async_get(hass)
    main_device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, **manager.device_info
    )
    manager.main_device_id = main_device.id

    group_devices: dict[str, str] = {}
    for group in manager.active_groups:
        sub_device = dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            **manager.device_info_for_group(group),
        )
        if main_device.area_id and sub_device.area_id is None:
            sub_device = (
                dev_reg.async_update_device(
                    sub_device.id, area_id=main_device.area_id
                )
                or sub_device
            )
        group_devices[group] = sub_device.id

    @callback
    def _async_on_device_registry_updated(event) -> None:
        """Автоматически наследовать Пространство (area_id) основного устройства для подустройств без пространства."""
        if event.data.get("action") != "update":
            return
        if event.data.get("device_id") != manager.main_device_id:
            return
        if "area_id" not in event.data.get("changes", {}):
            return
        updated_main = dev_reg.async_get(manager.main_device_id)
        if not updated_main or not updated_main.area_id:
            return
        for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
            if dev.id != manager.main_device_id and dev.area_id is None:
                dev_reg.async_update_device(dev.id, area_id=updated_main.area_id)

    entry.async_on_unload(
        hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED, _async_on_device_registry_updated
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _sync_entity_devices(hass, entry, manager, group_devices)
    _remove_stale_devices(dev_reg, entry, manager)
    await manager.async_start()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка интеграции и отписка от событий."""
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        manager: LoggiaManager = hass.data[DOMAIN].pop(entry.entry_id)
        await manager.async_stop_manager()
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Перезагрузка при изменении опций."""
    manager: LoggiaManager | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if manager and manager.consume_ignore_options_update():
        return
    await hass.config_entries.async_reload(entry.entry_id)


@callback
def _sync_entity_devices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    manager: LoggiaManager,
    group_devices: dict[str, str],
) -> None:
    """Перепривязать активные сущности к целевым подустройствам и удалить сущности выключенных режимов."""
    ent_reg = er.async_get(hass)
    prefix = f"{entry.entry_id}_"
    for ent_entry in list(er.async_entries_for_config_entry(ent_reg, entry.entry_id)):
        uid = ent_entry.unique_id or ""
        if not uid.startswith(prefix):
            continue
        key = uid[len(prefix) :]
        if (
            key in ENTITY_GROUP
            or key
            in (
                "yandex_volume",
                "low_battery_threshold",
                "watering_status",
                "phytolamp_status",
                "status",
                "next_action",
            )
        ) and key not in manager.config_entities:
            ent_reg.async_remove(ent_entry.entity_id)
            continue
        group = ENTITY_GROUP.get(key)
        if group is None:
            target_device_id = manager.main_device_id
        else:
            target_device_id = group_devices.get(group, manager.main_device_id)

        if target_device_id and ent_entry.device_id != target_device_id:
            ent_reg.async_update_entity(ent_entry.entity_id, device_id=target_device_id)
        ent_obj = manager.config_entities.get(key)
        expected_tk = getattr(ent_obj, "translation_key", None)
        if expected_tk and ent_entry.translation_key != expected_tk:
            ent_reg.async_update_entity(
                ent_entry.entity_id, translation_key=expected_tk
            )


@callback
def _remove_stale_devices(dev_reg: dr.DeviceRegistry, entry: ConfigEntry, manager) -> None:
    """Удаляет подустройства выключенных режимов."""
    active = {(DOMAIN, entry.entry_id)} | {
        (DOMAIN, f"{entry.entry_id}_{group}") for group in manager.active_groups
    }
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        if not device.identifiers & active:
            dev_reg.async_remove_device(device.id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Разрешить удаление подустройств, но не основного устройства."""
    return (DOMAIN, entry.entry_id) not in device.identifiers
