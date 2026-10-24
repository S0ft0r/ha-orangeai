# Changelog

🌐 **Language / Язык:** [🇷🇺 Русский](CHANGELOG.md) | **🇬🇧 English**

All notable changes to the **Home Orangery** (`orry`) integration for Home Assistant are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.24.1] — 2026-10-24

### Fixed
- **Restored the “In work” checkboxes:** the `excluded_blinds` select now initializes from saved config-entry options, without overwriting settings from restored entity state or performing redundant state writes at startup.
- **Added a fallback to resolve select options by drive entity ID/name** when Home Assistant frontend metadata omits `option_by_blind`.
- The card continues to use the Home Assistant theme only; no manual theme toggle or local persistence is included.

---

## [0.1.24] — 2026-10-24

### Added
- **Ported the approved drive list into `custom:orry-card`:** each drive shows a position-aware icon, one position/battery/no-bar indicator, an independently configurable position percentage, and compact sun-protection/work checkboxes. No separate “Drives” heading is added.
- **Drive checkboxes are connected to the integration:** the work checkbox uses `excluded_blinds`; the new live `blinds_for_protect` select persists sun-protection choices without reloading and applies changes immediately during active protection.
- **Excluded drive rows are dimmed and hatched,** while the final “In work” checkbox cell remains bright and unhatched. The indicator fills the available row width. The card uses the Home Assistant theme.

---

## [0.1.23] — 2026-10-24

### Added
- **Optional `switch_icon` card setting:** the selected Home Assistant icon replaces the standard toggle; when omitted, the standard toggle is shown.
- **Blind-drive indicator options (`drive_indicator`, `show_position_percent`)**: choose a shutter-position bar, a battery bar, or no bar; the position percentage is controlled independently.
- **Interactive Orry Lovelace YAML builder** with a Next-sensor field, default-tab and indicator selectors, position-percent toggle, optional title and switch icon, and copyable card-level YAML.

---

## [0.1.22] — 2026-10-24

### Added
- **Full Lovelace card `custom:orry-card`:** header, summary tiles for enabled modules, and tabs for Blinds, Lighting, and Watering; related entities are discovered automatically from the selected Orry configuration.
- **Card controls:** grouped blind control, configured light toggles, auto-watering and skip-cycle switches, schedule summary, and manual dosed watering.
- **Automatic frontend resource registration** in Lovelace Storage mode and deferred custom-element registration for current Home Assistant frontends.

### Fixed
- Card entity discovery now also works when frontend metadata omits `unique_id` / `translation_key`: it falls back to display names and sub-device groups, including localized entity IDs.
- Frontend resource URLs include hashes of both the JS asset and loader, so the stale app-shell URL changes even when file timestamps match.

---

## [0.1.21] — 2026-10-21

### Changed
- **Split schedule setup into two compact screens without scrolling (`ConfigFlow` & `OptionsFlow`):**
  - The **"Schedule and sun"** (`time`) screen now contains only the *Open at sunrise* / *Close at sunset* toggles and opening/closing time fields.
  - Work/weekend cycle parameters (*Consecutive workdays*, *Consecutive days off*, *First workday of cycle*) and the *Use weekend schedule on public holidays* toggle have been moved to a dedicated **"Work week"** (`work_week`) screen shown when weekday/weekend schedule separation is enabled.
- **Russian display name in integration search & HACS:** set `"name": "Домашняя оранжерея"` in `manifest.json` and `hacs.json` so the integration is searchable in Russian in Home Assistant's "Select brand" dialog and in HACS.

---

## [0.1.20] — 2026-10-21

### Added
- **Initial public release of the "Home Orangery" (`orry`) integration:**
  - Hierarchical modular architecture for managing a home orangery, winter garden, grow box, or smart loggia:
    - **Main Device (`<Name>`)** — unified overview of blinds, grow lights, and watering status, next scheduled action sensor (`next_action`), aggregated battery status across all configured devices (`battery`), and configurable low battery alert threshold (`low_battery_threshold`, `5–50%`, default `15%`).
    - **Subdevice "Blinds & Shades" (`drives`)** — group `cover` entity, direct sun protection by solar azimuth & elevation, stepped insolation or fixed closing position, drive exclusion selector (`excluded_blinds`), command repeat (`repeat_commands`) for sleeping Zigbee motors, and drive battery monitoring.
    - **Subdevice "Grow Light" (`phytolamp`)** — supplemental plant lighting linked to the blinds schedule (`phytolamp_use_main_settings`, factoring in blind travel delay during sun protection) or running on an independent schedule and insolation curve.
    - **Subdevice "Watering" (`watering`)** — morning and evening automatic irrigation schedules (by clock or relative to sunrise/sunset), independent valve multi-selects for morning (`watering_morning_zones`) and evening (`watering_evening_zones`) watering, duration controls, air humidity scaling, manual `30 sec` dosed watering (`watering_zone` + `watering_execute`), and hardware safety watchdog (`auto_watchdog`).
    - **Unified Subdevice "Schedule" (`schedule`)** — all time settings and sunrise/sunset toggles across enabled modules with clear module prefixes (`Blinds: …`, `Lighting: …`, `Watering: …`).
  - **Universal Work/Weekend Schedule (5/2, 2/2, N/M + Public Holidays or Single Daily Schedule):**
    - Toggle **"Split schedule into workdays and weekends"** (`split_weekend_schedule`) in the setup wizard and `OptionsFlow` (`Configure`).
    - Support for arbitrary cyclical schedules (`work_days` workdays followed by `off_days` days off starting from `cycle_start_date`) and automatic national holiday and working-day transfer detection (`use_holidays`, powered by `holidays` and the Home Assistant country setting).
  - **Cross-module "Notification only" (`logging`) mode & low-battery alerts** — dispatches detailed notifications via selected `notify.*` services or `persistent_notification` both when a module is set to `Notification only` and when any drive or valve battery drops below `low_battery_threshold`.
  - **Bundled 40 custom vector icons (`orry:*`) & automatic multi-line entity name wrapping (`frontend/orry-icons.js`):**
    - Zero-configuration registration of `window.customIcons["orry"]` without third-party HACS plugins.
    - Automatic multi-line wrapping of long `orry` entity names inside Lovelace cards instead of single-line ellipsis truncation (`...`).
  - Full bilingual localization (`translations/ru.json` and `translations/en.json`), redacted diagnostics (`diagnostics.py`), and live reconfiguration (`OptionsFlow`).
