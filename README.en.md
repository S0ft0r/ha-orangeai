# Home Orangery — Home Assistant Integration

[![Home Assistant Marketplace](https://img.shields.io/badge/Home%20Assistant-Marketplace-41BDF5.svg)](https://www.home-assistant.io/blog/2026/11/04/release-202611/#welcome-to-the-marketplace)
[![Version](https://img.shields.io/badge/version-0.1.27-blue.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8.0%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Manufacturer](https://img.shields.io/badge/manufacturer-OrangeAI-purple.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Author](https://img.shields.io/badge/author-%40S0ft0r-orange.svg)](https://github.com/S0ft0r)

🌐 **Language:** [🇷🇺 Русский](README.md) | **🇬🇧 English**

> **Version:** 0.1.27  
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

### Home Assistant Core 2026.11.0 and newer — built-in Marketplace (recommended)

Open **Settings → Marketplace**. The first time you open it, read and accept the notice about community projects. Search for **Home Orangery** or `orry`. If the integration is not yet shown in the main catalog, select **Add from link** and enter `https://github.com/S0ft0r/ha-orangeai`. Adding a custom repository requires GitHub device sign-in; you do not enter your GitHub password in Home Assistant.

Select **Install**. Marketplace installs the integration and opens its setup flow without restarting Home Assistant. A restart is still required after an integration update.

### If you already installed the integration through HACS

On the first start after upgrading Home Assistant to `2026.11.0`, existing installations and custom repositories migrate to Marketplace automatically. Do not install the integration a second time; verify it under **Settings → Marketplace**. The separate HACS integration cannot be installed on Home Assistant `2026.11.0` or newer.

### Home Assistant Core 2026.8.0–2026.10.x

The integration still supports Home Assistant `2026.8.0` and newer, but the built-in Marketplace is available starting with Core `2026.11.0`. On Core `2026.8.0–2026.10.x`, add `https://github.com/S0ft0r/ha-orangeai` to HACS as a custom **Integration** repository, download the integration, and restart Home Assistant. HACS cannot be installed on Core `2026.11.0` or newer.

### Setup and manual installation

[![Open your Home Assistant instance and start setting up Home Orangery](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orry)

After installation, start setup with this badge or go to **Settings → Devices & services → Add integration → Home Orangery**.

For manual installation, copy `custom_components/orry` into `config/custom_components/orry/` and restart Home Assistant, then start the setup flow. After installing for the first time or updating, hard-refresh the browser with cache clearing if the `orry:*` icons or card do not appear.

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

`default_tab` accepts `blinds` (default), `phytolamp`, or `watering`; `title` is optional. `drive_indicator` accepts `position`, `battery`, or `none`; if omitted, no bar is shown. `show_position_percent` independently controls the shutter-position percentage and defaults to `true`. Optional `switch_icon` displays a Home Assistant icon instead of the standard toggle (for example, `mdi:power`); if omitted, the standard toggle remains. Drive rows include sun-protection and work checkboxes connected to the integration; excluded rows are hatched except for the work checkbox. Drive icons `orry:blind-0/25/50/75/100` indicate the current shutter position. No separate “Drives” heading is added. Open the [interactive card builder](https://html-preview.github.io/?url=https://github.com/S0ft0r/ha-orangeai/blob/main/docs/orry-builder.en.html) or see the [full documentation](docs/DOCUMENTATION.en.md#custom-lovelace-card) for YAML dashboard details.

## Full documentation

- [Полное руководство на русском](docs/DOCUMENTATION.md)
- [Full documentation in English](docs/DOCUMENTATION.en.md)
- [Changelog](CHANGELOG.en.md) · [История изменений на русском](CHANGELOG.md)
- [Report an issue or request an improvement](https://github.com/S0ft0r/ha-orangeai/issues)
