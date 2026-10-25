# Home Orangery — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-0.1.26-blue.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8.0%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Manufacturer](https://img.shields.io/badge/manufacturer-OrangeAI-purple.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Author](https://img.shields.io/badge/author-%40S0ft0r-orange.svg)](https://github.com/S0ft0r)

🌐 **Language:** [🇷🇺 Русский](README.md) | **🇬🇧 English**

> **Version:** 0.1.26  
> **Manufacturer:** `OrangeAI` · **Author:** [Softor (@S0ft0r)](https://github.com/S0ft0r)

A Home Assistant integration that brings together roller blinds, plant lighting, and multi-zone watering for an orangery, winter garden, grow box, or green loggia. Enable all modules or only the ones you need.

## Key features

- **Blinds and shades:** schedules, grouped drive control, and direct-sun protection based on solar position, weather, and illuminance.
- **Plant lighting:** use a dedicated schedule or follow the orangery's main settings.
- **Multi-zone watering:** independent morning and evening cycles, soil-moisture sensors, manual operation, and diagnostics; one Lovelace card offers full and summary modes for enabled modules.

## Requirements

- Home Assistant `2026.8.0` or newer.
- Module entities: blind drives (`cover.*`), lights or relays (`light.*` / `switch.*`), and watering valves or pumps (`switch.*`).

## Installation and setup

### Via HACS

[![Open your Home Assistant instance and open the Home Orangery repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=S0ft0r&repository=ha-orangeai&category=integration)

The badge opens the repository page in HACS. If it does not appear there, add `https://github.com/S0ft0r/ha-orangeai` from the HACS **Custom repositories** menu as an **Integration**. Then open the integration in HACS, select **Download**, and restart Home Assistant.

### Add and configure the integration

[![Open your Home Assistant instance and start setting up Home Orangery](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orry)

Use this badge after installation to open the setup flow. Alternatively, go to **Settings → Devices & services → Add integration → Home Orangery**.

### Manual installation

Copy `custom_components/orry` into `config/custom_components/orry/` and restart Home Assistant. Then start setup using the badge above or **Settings → Devices & services → Add integration**.

After installation or an update, hard-refresh the browser with cache clearing so the `orry:*` icons and card are loaded.

## Lovelace card

`custom:orry-card` supports `mode: full` (detailed tabs) and `mode: summary` (header and KPI tiles only). Both modes share the same summary indicators and state line. Set the **Next** sensor on the main device of the desired configuration; related entities are discovered automatically. In Storage mode the resource is registered automatically; in YAML mode the integration loads the JS module.

```yaml
type: custom:orry-card
mode: full  # or summary
entity: sensor.orangery_next_action  # replace with your configuration's Next sensor ID
default_tab: watering
drive_indicator: position
show_position_percent: true
title: Home Orangery
```

`default_tab` accepts `blinds` (default), `phytolamp`, or `watering`; `title` is optional. `drive_indicator` accepts `position`, `battery`, or `none`; if omitted, no bar is shown. `show_position_percent` independently controls the shutter-position percentage and defaults to `true`. Optional `switch_icon` displays a Home Assistant icon instead of the standard toggle (for example, `mdi:power`); if omitted, the standard toggle remains. Drive rows include sun-protection and work checkboxes connected to the integration; excluded rows are hatched except for the work checkbox. Drive icons `orry:blind-0/25/50/75/100` indicate the current shutter position. No separate “Drives” heading is added. Open the [interactive card builder](https://html-preview.github.io/?url=https://github.com/S0ft0r/ha-orangeai/blob/main/docs/orry-builder.html) or see the [full documentation](docs/DOCUMENTATION.en.md#custom-lovelace-card) for YAML dashboard details.

## Full documentation

- [Полное руководство на русском](docs/DOCUMENTATION.md)
- [Full documentation in English](docs/DOCUMENTATION.en.md)
- [Changelog](CHANGELOG.en.md) · [История изменений на русском](CHANGELOG.md)
- [Report an issue or request an improvement](https://github.com/S0ft0r/ha-orangeai/issues)
