# Changelog

🌐 **Language / Язык:** [🇷🇺 Русский](CHANGELOG.md) | **🇬🇧 English**

All notable changes to the **Home Orangery** (`orry`) integration for Home Assistant are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
