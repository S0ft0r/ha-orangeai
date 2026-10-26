"""Интеграция Лоджия — Умные шторы."""

import hashlib
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA, MODE_STORAGE
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


async def _async_upsert_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Добавить или обновить JS-модуль в ресурсах Lovelace в режиме Storage."""
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if getattr(lovelace_data, "resource_mode", None) != MODE_STORAGE:
        return False

    resources = getattr(lovelace_data, "resources", None)
    methods = (
        "async_get_info",
        "async_items",
        "async_create_item",
        "async_update_item",
        "async_delete_item",
    )
    if resources is None or not all(hasattr(resources, method) for method in methods):
        return False

    await resources.async_get_info()
    base_url = url.split("?", 1)[0]
    matches = [
        item
        for item in resources.async_items()
        if str(item.get("url", "")).split("?", 1)[0] == base_url
    ]
    if not matches:
        await resources.async_create_item({"url": url, "res_type": "module"})
        return True

    primary = matches[0]
    updates: dict[str, str] = {}
    if primary.get("url") != url:
        updates["url"] = url
    if primary.get("type") != "module":
        updates["res_type"] = "module"
    if updates:
        await resources.async_update_item(primary["id"], updates)

    for duplicate in matches[1:]:
        await resources.async_delete_item(duplicate["id"])
    return True


def _collect_frontend_asset_metadata(
    js_assets: list[tuple[Path, str]],
) -> list[tuple[Path, str, str]]:
    """Собрать существующие JS-файлы и их версии вне event loop.

    Проверки путей, чтение файлов и stat() блокирующие, поэтому функция
    вызывается через hass.async_add_executor_job().
    """
    existing_assets: list[tuple[Path, str, str]] = []
    for path, url in js_assets:
        try:
            if not path.is_file():
                continue
            mtime = int(path.stat().st_mtime)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        except OSError as err:
            _LOGGER.debug("Skipping unavailable frontend asset %s: %s", path, err)
            continue
        existing_assets.append((path, url, f"{mtime}-{digest}"))

    if not existing_assets:
        return []

    loader_revision = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:8]
    return [
        (path, url, f"{asset_revision}-{loader_revision}")
        for path, url, asset_revision in existing_assets
    ]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Загрузка интеграции и запуск менеджера."""
    manager = LoggiaManager(hass, entry)
    await manager.async_init_translations()
    _LOGGER.info("%s", manager.tr_log("log_setup_entry", title=entry.title))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    frontend_dir = Path(__file__).parent / "frontend"
    js_assets = [
        (frontend_dir / f"{DOMAIN}-icons.js", f"/{DOMAIN}_static/{DOMAIN}-icons.js"),
        (frontend_dir / f"{DOMAIN}-card.js", f"/{DOMAIN}_static/{DOMAIN}-card.js"),
    ]
    if getattr(hass, "http", None) is not None:
        try:
            frontend_assets = await hass.async_add_executor_job(
                _collect_frontend_asset_metadata, js_assets
            )
            existing_assets = [
                (path, url) for path, url, _version in frontend_assets
            ]
            registered_paths = hass.data[DOMAIN].setdefault(
                "_frontend_registered_paths", set()
            )
            if not isinstance(registered_paths, set):
                registered_paths = set(registered_paths)
                hass.data[DOMAIN]["_frontend_registered_paths"] = registered_paths
            if hass.data[DOMAIN].get("_frontend_registered") and not registered_paths:
                # Старый флаг означал, что ранее был зарегистрирован только модуль иконок.
                registered_paths.add(f"/{DOMAIN}_static/{DOMAIN}-icons.js")

            new_assets = [
                (path, url)
                for path, url in existing_assets
                if url not in registered_paths
            ]
            if new_assets:
                if hasattr(hass.http, "async_register_static_paths"):
                    await hass.http.async_register_static_paths(
                        [
                            StaticPathConfig(url, str(path), cache_headers=False)
                            for path, url in new_assets
                        ]
                    )
                    registered_paths.update(url for _, url in new_assets)
                elif hasattr(hass.http, "register_static_path"):
                    for path, url in new_assets:
                        hass.http.register_static_path(
                            url, str(path), cache_headers=False
                        )
                        registered_paths.add(url)
                hass.data[DOMAIN]["_frontend_registered"] = bool(registered_paths)

            versions: dict[str, str] = hass.data[DOMAIN].setdefault(
                "_frontend_versions", {}
            )
            # Версии рассчитаны в executor вместе с проверкой наличия файлов.
            lovelace_data = hass.data.get(LOVELACE_DATA)
            storage_resource_mode = (
                getattr(lovelace_data, "resource_mode", None) == MODE_STORAGE
            )
            for _path, url_path, version in frontend_assets:
                previous_version = versions.get(url_path)
                module_url = f"{url_path}?v={version}"
                is_icon_asset = url_path == f"/{DOMAIN}_static/{DOMAIN}-icons.js"

                if storage_resource_mode:
                    if previous_version is not None and previous_version != version:
                        remove_extra_js_url(
                            hass, f"{url_path}?v={previous_version}"
                        )
                    # Entity icons are used outside Lovelace too (for example, in
                    # integration and entity panels), so register the icon pack
                    # as a frontend-wide module as well as a dashboard resource.
                    if is_icon_asset and previous_version != version:
                        add_extra_js_url(hass, module_url)
                    try:
                        resource_registered = await _async_upsert_lovelace_resource(
                            hass, module_url
                        )
                    except Exception as err:
                        _LOGGER.warning(
                            "Failed to register %s as a Lovelace resource: %s",
                            url_path,
                            err,
                        )
                        resource_registered = False
                    if not resource_registered:
                        _LOGGER.warning(
                            "Lovelace storage resources are unavailable; "
                            "falling back to frontend module loading for %s",
                            url_path,
                        )
                        if not is_icon_asset or previous_version == version:
                            add_extra_js_url(hass, module_url)
                elif previous_version != version:
                    if previous_version is not None:
                        remove_extra_js_url(
                            hass, f"{url_path}?v={previous_version}"
                        )
                    add_extra_js_url(hass, module_url)

                versions[url_path] = version
        except Exception as err:
            _LOGGER.warning(
                "Failed to register %s frontend assets: %s", DOMAIN, err
            )

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
