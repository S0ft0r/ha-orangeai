# Home Orangery — Modular Blind, Plant Lighting & Watering Controller for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-0.1.26.1-blue.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8.0%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Manufacturer](https://img.shields.io/badge/manufacturer-OrangeAI-purple.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Author](https://img.shields.io/badge/author-%40S0ft0r-orange.svg)](https://github.com/S0ft0r)

🌐 **Language:** [🇷🇺 Полная документация на русском (DOCUMENTATION.md)](DOCUMENTATION.md) | **🇬🇧 English**

[Short README overview](../README.en.md) · [Open the interactive Lovelace YAML builder](https://html-preview.github.io/?url=https://github.com/S0ft0r/ha-orangeai/blob/main/docs/orry-builder.html)

> **Version:** 0.1.26.1  
> **Manufacturer:** `OrangeAI`  
> **Author:** [Softor (@S0ft0r)](https://github.com/S0ft0r)

A modular custom integration for **Home Assistant** providing comprehensive automated and manual control of **roller blinds & shades**, **plant grow lighting**, and **multi-zone plant watering** in a home orangery, winter garden, grow box, or green loggia. Enable all three modules together or use any of them independently. Features universal work/weekend cyclical scheduling (`5/2`, `2/2`, `N/M` with national public holidays or single daily mode) and sunrise/sunset tracking, direct sunlight protection by solar azimuth & elevation, stepped insolation by weather & illuminance, cross-module "Notification only" (`logging`) mode, battery monitoring with configurable low-battery threshold (`low_battery_threshold`), and a bundled set of 40 custom vector icons (`orry:*`).

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Custom Lovelace Card](#custom-lovelace-card)
4. [Key Features](#key-features)
5. [Integration Devices](#integration-devices)
6. [How Configuration Works: Initial Setup, Reconfiguration & Device Cards](#how-configuration-works-initial-setup-reconfiguration--device-cards)
7. [Mapping Table: Setup Fields ↔ Device Card Controls](#mapping-table-setup-fields--device-card-controls)
8. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
9. [Using the Device Cards](#using-the-device-cards)
10. [Automation Logic](#automation-logic)
11. [Disclaimer](#disclaimer)

---

## Requirements

| Component | Requirement | Description |
|---|---|---|
| **Home Assistant** | Required | Version `2026.8.0` or newer |
| **Blind drives** | When "Blind control" module is enabled | One or more position-capable blind drives (`cover.*`, 0–100%) |
| **Plant lights / relays** | When "Plant lighting" module is enabled | Switches (`switch.*`) or lights (`light.*`) for plant lighting |
| **Watering valves / pumps** | When "Plant watering" module is enabled | One or more switches (`switch.*`) controlling irrigation valves or pumps |
| **Soil moisture sensors** | Optional | Per-zone soil moisture sensors (`sensor.*`) for watering zones |
| **Sun** | Defaults to `sun.sun` | Built-in Sun integration used for sunrise/sunset times and solar angles |
| **Illuminance sensor** | Optional | Illuminance sensor in lux (`lx`) for sun protection and/or plant lighting |
| **Weather forecast** | Optional | Weather entity (`weather.*`) for filtering sun protection and plant lighting |
| **Remote / Switch** | Optional | Physical switch with built-in slider (e.g. **Aqara Z1 Pro**) or rotary knob (MQTT / ZHA) |
| **Smart speakers** | Optional | Speakers (**Yandex Station** or any TTS media player) for voice announcements on drive errors |

---

## Installation

### Method 1. Via HACS (Recommended)

[![Open your Home Assistant instance and open the Home Orangery repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=S0ft0r&repository=ha-orangeai&category=integration)

The badge opens the repository page in HACS. If the repository is not listed, open the HACS menu → **Custom repositories**, enter `https://github.com/S0ft0r/ha-orangeai`, choose **Integration**, and select **Add**.

1. On the integration page in HACS, select **Download**.
2. Restart Home Assistant.
3. **Reload your browser with cache clearing** (`Ctrl + F5` / `Shift + F5` on Windows/Linux or `Cmd + Shift + R` on macOS), or completely restart the browser.
   > ⚠️ **Important for custom icons (`orry:*`) and the custom card:** the integration registers its vector icon bundle (`orry-icons.js`) and `custom:orry-card` (`orry-card.js`) in the Home Assistant frontend. If you do not perform a hard refresh with cache clearing after installing or updating the integration, the browser will keep using its cached frontend shell: **empty spaces** may appear instead of icons, and the card may report that `orry-card` was not found.
   > - **In the Home Assistant Companion mobile app:** go to *Settings → Companion App → Debugging → Reset frontend cache* (or force-close and reopen the app).

After installation, use the official badge to start setup, or go to **Settings → Devices & Services → Add Integration** and select **Home Orangery**:

[![Open your Home Assistant instance and start setting up Home Orangery](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orry)

### Method 2. Manual Installation

1. Download the release archive `orry.zip` and extract its `orry` folder into `config/custom_components/`, so the resulting path is `config/custom_components/orry/`. If you downloaded the source repository archive, copy `custom_components/orry` into `config/custom_components/` instead.
2. Restart Home Assistant.
3. **Reload your browser with cache clearing** (`Ctrl + F5` / `Cmd + Shift + R`) or reset the frontend cache in the Home Assistant Companion app so the `orry:*` icons and `custom:orry-card` load.
4. Use the setup badge in the installation section above, or go to **Settings → Devices & Services → Add Integration → Home Orangery**.

---

## Custom Lovelace Card

The integration includes a Home Assistant-style `custom:orry-card` with `mode: full` and `mode: summary`. Both modes share the same header, header state line, and summary tiles for the enabled **Blinds**, **Lighting**, and **Watering** modules. Tiles show live counters (blinds: total / active / errors; lighting: total / on; watering: configured / active), the blind-position slider, and available lighting and auto-watering toggles. Each tile shows its next event from the **Next** sensor attributes (`blind_action`, `light_action`, and `watering_action`); the separate “Next” pill on the right side of the header has been removed. Full mode additionally shows detailed tabs for configured lights, auto-watering, schedule information, and manual dosed watering; summary mode shows only the header and KPI tiles. Visible tiles and tabs are determined automatically by enabled modules. After the first verified integration action, the subtitle uses the **Next** sensor's `last_action` attribute (localized text with local time); until then it falls back to enabled module names. `last_action_at` contains the event's ISO timestamp. The last action survives schedule refreshes and is restored after a Home Assistant restart; builder demo history is never used. Set `scroll_text: true` to scroll overflowing event lines in the mini-cards; it defaults to `false`. The header's `last_action` subtitle still scrolls automatically when it overflows. Detailed panels—including the watering panel—are unchanged.

The blinds tile includes a position slider for the active group and `total / active / errors` counters; there is no separate aggregate blind-control panel. In full mode, the drive list includes every configured drive, including those excluded from automation. The **Sun protection** checkbox is connected to the `blinds_for_protect` select entity, which is created when the sun-protection module is enabled and can be changed live without reloading the integration. If protection is already active, newly selected drives are closed immediately and deselected drives are opened. The **In work** checkbox updates the existing `excluded_blinds` select. Excluded rows are dimmed and hatched except for the final work-checkbox cell. The position/battery indicator uses the available row width; the numeric position can be toggled independently. Position-aware drive icons use `orry:blind-0/25/50/75/100` without blue tile backgrounds. The sun-protection and work columns use the Orry icons `orry:blind-sun` and `orry:blind-pause`. No separate “Drives” heading is shown. The card always uses the Home Assistant theme.

- In Lovelace **Storage** mode the card resource is registered automatically; in YAML mode the integration loads the JS module through the frontend. Do not add the resource manually.
- In the visual editor, select the main device's **Next** sensor for the desired Orry configuration. The card discovers related entities on the main device and its sub-devices.
- Use the matching **Next** sensor for each Orry configuration. If Home Assistant has multiple orangery configurations, set `entity` explicitly on each card to bind it to the correct one; other related entities are discovered automatically.

### Configure the card directly in YAML

In a YAML dashboard, add the card as an item in the `cards:` list of the desired view. This example shows a view with the watering tab selected initially:

```yaml
views:
  - title: Orangery
    path: orangery
    cards:
      - type: custom:orry-card
        mode: full
        entity: sensor.orangery_next_action
        default_tab: watering
        drive_indicator: position
        show_position_percent: true
        scroll_text: true
        title: Home Orangery
```

The `entity` value above is an example. Replace `sensor.orangery_next_action` with the actual entity ID of the **Next** sensor on the main device for the desired Orry configuration (find it under **Settings → Devices & services → Entities**). If editing only one card's YAML in Home Assistant, paste the card configuration starting at `type:` without the `views:` or `cards:` wrapper. When editing an existing YAML dashboard, add the card to its existing `cards:` list rather than creating a second root-level `views:` block.

| Option | Required? | Allowed values and purpose |
| :--- | :--- | :--- |
| `type` | Yes | Always `custom:orry-card`. |
| `mode` | No; defaults to `full` | `full` shows summary tiles and detailed tabs; `summary` keeps the same header, state line, and tiles without tabs. |
| `entity` | Required in the visual editor; recommended in YAML | Entity ID of the main device's **Next** sensor for the selected configuration. With one configuration the card can try to find it automatically; with multiple configurations, set `entity` explicitly on each card. |
| `default_tab` | No; defaults to `blinds` | Initial tab in `full` mode: `blinds`, `phytolamp` (lighting), or `watering`. If that module is disabled, the first available tab opens; ignored in `summary`. |
| `drive_indicator` | No; if omitted, no bar is shown | Applies to the detailed drive list in `full` mode: `position` shows a blue shutter-position bar; `battery` shows a battery bar (green at 45%+, yellow 35–44%, orange 15–34%, red below 15%); `none` hides the bar. |
| `show_position_percent` | No; defaults to `true` | In `full` mode, shows the numeric shutter position in the detailed list independently of the bar mode; it always represents shutter position, not battery charge. |
| `scroll_text` | No; defaults to `false` | Enables marquee scrolling for overflowing event lines in the mini-cards. When disabled, long text is truncated with an ellipsis. The header's `last_action` state line continues to scroll automatically when it overflows. |
| `title` | No | Custom card title. If omitted, the main Orry device name is used. |
| `switch_icon` | No | In `full` mode, a Home Assistant icon (for example, `mdi:power`) replaces the standard toggle in the detailed lighting and watering controls. If omitted, the standard toggle is shown. |

Disabled modules are hidden automatically: each card shows only its active KPI tiles and, in `full` mode, the corresponding tabs.

## Key Features

- **Lovelace card (`custom:orry-card`)**: `full` mode with detailed tabs and `summary` mode with the same KPI tiles but no tabs; shared header and state line across modes.
- **Modular Architecture**:
  - The first setup screen lets you pick only the orangery modules you need: **Enable blind control**, **Enable plant lighting**, and **Enable plant watering** (at least one module is required), plus a separate global toggle **Enable error logging**.
  - Each module creates only its own sub-devices and entities; disabling a module automatically removes its unused sub-devices and entities.
- **Organized Device Cards & No Duplication During Reconfiguration**:
  - Everyday settings (travel limits, command repeats, schedule times, solar angles, lux thresholds, remote parameters, plant lighting times, watering modes and durations) live directly on dedicated device cards.
  - During reconfiguration (**Configure** button), already configured modules are skipped by default unless **Edit previously configured functions** is turned on, and parameters already exposed as entities on device cards are never asked again.
- **Flexible Blind Drive Management & Voice Assistant Support**:
  - Grouped cover entities **Blinds** (all active drives) and **Sun protection blinds** on the **Drives** sub-device can be added to dashboards or exposed to any voice assistant (Yandex Alice, Apple Siri, Home Assistant Assist) with full travel limits, retries, and excluded-drive filtering.
  - Temporarily exclude individual drives from operation (`✓` / `✕`) right from the **Used drives** dropdown on the **Drives** device card.
  - Trigger manual actions (*Stop*, *Open fully*, *Close fully*, *Open to 10% ... 90%*) with automatic filtering that hides percentages outside your configured travel limits.
- **Accurate Sun & Time Scheduling, Sun Protection & Plant Lighting**:
  - Morning opening at sunrise (with separate weekday/weekend "not earlier than" limits) and evening closing at sunset (with a "not later than" limit), rounding non-zero sunrise/sunset seconds up to the next full minute.
  - Automatically closes selected blinds when the sun enters the configured azimuth & elevation window, filtered by weather and illuminance.
  - Plant lighting can follow main integration settings (inverse sun protection logic delayed by full blind travel time) or run on custom schedule, sun, weather, and illuminance rules.
- **Multi-Zone Plant Watering**:
  - A single compact **Orangery: watering** sub-device card manages any number of valves/pumps: selecting a specific direction (or **↺ All zones (bulk)**) immediately loads and edits its morning and evening mode (*Off*, *Daily*, *Every other day*, *Every two days*, *By sensor*) and duration (`0–600 s`).
  - Sequential valve execution during morning and evening cycles, one-time skip of the next watering cycle with auto-reset, and per-zone soil moisture threshold checks.
- **Reliable Command Delivery & Diagnostics**:
  - Configurable command repeats with micro-step positioning and physical position polling after full travel time, error counting, Logbook entries, push notifications, and voice alerts.

---

## Integration Devices

After setup, the integration creates **1 main device** and up to **4 sub-devices** depending on the enabled modules. Disabling a module automatically removes its unused sub-device.

| # | Device Name | When Created | Controls & Sensors Inside |
|---|---|---|---|
| 1 | **`<Orangery Name>`** *(Main Device)* | **Always** | Module status sensors (**Next**, **Blinds**, **Lighting**, **Watering**), aggregated battery status across all devices (**Battery level**), and configurable **Low battery alert threshold** (`5–50%`, default `15%`) |
| 2 | **`<Name>: blinds & shades`** (`drives`) | When **Enable blind control** is enabled | Grouped cover (**Blinds**), **Operating mode** (*Automatic*, *Forced closing*, *Manual*, *Notification only*), **Sun protection mode**, per-drive exclusion (**Used drives**), manual control (**Select action**), settings (**Up limit**, **Down limit**, **Repeat count**, **Repeat delay**, **Full travel time**), and diagnostics (**Open**, **Closed**, **Errors**, **Battery level**) |
| 3 | **`<Name>: schedule`** (`schedule`) | When any scheduled module is enabled | Unified schedule card for all active modules with clear prefixes: **Blinds: open at sunrise**, **Blinds: close at sunset**, **Blinds: open on weekdays / weekends** (or single **Blinds: open at**), **Blinds: close at**, **Lighting: turn on on weekdays / weekends** (or **Lighting: turn on at**), **Lighting: turn off at**, **Watering: morning watering**, **Watering: evening watering** |
| 4 | **`<Name>: grow light`** (`phytolamp`) | When **Enable plant lighting** is enabled | **Lighting mode** (*Automatic*, *Scheduled*, *Manual*, *Notification only*), **Use main settings** toggle, and diagnostics (**On**, **Off**, **Errors**) |
| 5 | **`<Name>: watering`** (`watering`) | When **Enable plant watering** is enabled | **Auto watering** and **Skip next watering** switches, **Watering mode (morning / evening)**, **Zones for morning watering** and **Zones for evening watering** selectors, **Watering duration (morning / evening)**, **Delay after sunrise / before sunset**, **Air humidity scaling**, manual 30-second dosed run (**Watering zone** + **Execute** button), and diagnostics (**Active zones**, **Errors**, **Battery level**) |

---

## How Configuration Works: Initial Setup, Reconfiguration & Device Cards

To keep the interface clean and intuitive, settings are organized into three groups:

1. **Initial Setup (when adding the integration)**:
   - On the first screen, you select the desired orangery modules (*Enable blind control*, *Enable plant lighting*, *Enable plant watering*) and optionally turn on the global **Enable error logging** switch.
   - On the subsequent screens, you select your hardware (blind drives, plant lights, watering valves, external sensors, remote controller, speakers) and provide **initial values** for schedules, travel limits, repeats, solar angles, illuminance thresholds, and default watering presets.
   - Once initial setup completes, the integration creates the corresponding devices and places all everyday controls onto their device cards.

2. **Reconfiguration (clicking "Configure" on the integration page)**:
   - The first screen shows your active modules, the **Enable error logging** toggle, and the **Edit previously configured functions** switch (default **OFF**):
     - When **Edit previously configured functions** is **OFF**, the wizard only opens setup screens for newly enabled modules, skipping all screens of already configured modules.
     - When **Edit previously configured functions** is **ON**, the wizard walks through equipment and sensor selection screens of existing modules (for example, to add a new blind drive, watering valve, or change a weather sensor).
   - Any setting that **already exists on a device card** is **automatically hidden** during reconfiguration so settings are never duplicated:
     - **Travel limits**, **Schedule & Sun**, and **Repeats & Timings** screens, as well as initial watering presets, are only shown when the corresponding sub-device is created for the first time; afterwards they are always adjusted on the **Drives**, **Schedule**, and **Watering** device cards.
     - **Solar angles**, **Illuminance thresholds/delay**, **Remote step/swipe speed**, and **Custom plant lighting settings** only appear during reconfiguration if you are enabling that feature for the very first time.

3. **Device Card-Only Controls**:
   - Temporary exclusion of individual drives (**Used drives**), manual blind positioning (**Action** + **Execute**), and per-zone watering configuration (**Watering zone**) live directly on the **Drives** and **Watering** device cards.

---

## Mapping Table: Setup Fields ↔ Device Card Controls

### 1. Module Selection, Drives & Blind Schedule

| Initial Setup Field | Wizard Screen | Behavior During Reconfiguration ("Configure") | Device Card | Control on Device Card |
|---|---|---|---|---|
| **Orangery modules** (*Blinds*, *Plant lighting*, *Plant watering*) | Module selection | **Always available** *(at least one module required)* | General integration setting | Enables/disables modules and their sub-devices |
| **Enable error logging** | Module selection | **Always available** *(separate global toggle)* | General integration setting | Enables Logbook logging, push notifications, and TTS error alerts |
| **Edit previously configured functions** | Reconfiguration only | Default **OFF** *(skips already configured modules)* | Reconfiguration wizard | Opens equipment/sensor screens for already active modules |
| **Blind drives** | Blind control | Available on first activation of blind control or when *Edit previously configured functions* is ON | Blind module setting | Defines the list of all controlled blinds |
| **Additional blind features** (*Direct sun protection*, *Remote / switch*) | Blind control | Available when configuring the blind module | Blind module setting | Enables sun protection and physical remote control |
| **Upper / Lower travel limit** | Travel limits | **Hidden** once `Orangery: drives` exists | `Orangery: drives` | **Up limit** and **Down limit** (`0–100%`) |
| **Repeat count / Delay / Full travel time** | Repeats and timings | **Hidden** once `Orangery: drives` exists | `Orangery: drives` | **Repeat count**, **Repeat delay**, **Full travel time** |
| *(Not in setup wizard)* | — | **Device card only** | `Orangery: drives` | Grouped cover entities **Blinds** and **Sun protection blinds** |
| *(Not in setup wizard)* | — | **Device card only** | `Orangery: drives` | **Used drives** dropdown (`✓` / `✕` / `↺`) |
| *(Not in setup wizard)* | — | **Device card only** | `Orangery: drives` | **Action** dropdown & **Execute** button |
| **Open at sunrise / Close at sunset / Weekday, weekend & close times** | Schedule and sun | **Hidden** once `Orangery: schedule` exists | `Orangery: schedule` | **Blinds: open at sunrise**, **Blinds: close at sunset** switches and **Blinds: open on weekdays**, **Blinds: open on weekends**, **Blinds: close at** time fields |
| **Consecutive workdays / Consecutive days off / First workday of cycle / Use weekend schedule on public holidays** | Schedule and sun *(or Custom plant lighting settings)* | **Available during reconfiguration** *(wizard only)* | Shared schedule setting | Defines the work/off cycle (`5/2` from Monday by default, `2/2`, `3/3`, `1/3`, etc.) and official public holiday handling for the Home Assistant country |

### 2. Direct Sun Protection, Weather & Illuminance

| Initial Setup Field | Wizard Screen | Behavior During Reconfiguration ("Configure") | Device Card | Control on Device Card |
|---|---|---|---|---|
| **Sun sensor** | Direct sun protection | Available when configuring sun protection | Internal binding | Used for sunrise, sunset, and solar angles |
| **Blinds for protection** | Direct sun protection | Available when configuring sun protection | Internal binding | Selects which blinds close during sun protection |
| **Additional conditions** (*Consider weather forecast*, *Consider illuminance level*) | Direct sun protection | Available when configuring sun protection | Internal binding | Enables weather filtering and creates the Illuminance device |
| **Sun azimuth / Sun elevation** | Direct sun protection (angles) | **Shown only on first activation** *(until `Orangery: sun protection` is created)* | `Orangery: sun protection` | **Azimuth** (`0–359°`) and **Elevation angle** (`0–90°`) |
| **Weather sensor / Weather conditions** | Weather forecast | Available when configuring weather filtering | Internal binding | Selected weather entity and conditions (*Sunny*, *Partly cloudy*, *Cloudy*, *Fog*) |
| **Illuminance sensor** | Illuminance | Available when configuring illuminance | Internal binding | Selected lux sensor |
| **Lower threshold / Upper threshold / Spike delay** | Illuminance | **Shown only on first activation** *(until `Orangery: illuminance` is created)* | `Orangery: illuminance` | **Lower threshold**, **Upper threshold** (`0–100000 lx`), and **Delay** |

### 3. Plant Lighting

| Initial Setup Field | Wizard Screen | Behavior During Reconfiguration ("Configure") | Device Card | Control on Device Card |
|---|---|---|---|---|
| **Plant lighting switches / lights** | Plant lighting | Available when configuring plant lighting | Internal binding | Selected phytolamp switches or lights |
| **Use main integration settings** | Plant lighting *(shown only when blind control is enabled)* | Available when configuring plant lighting | Internal binding | When enabled, lighting uses main schedule & sensors; when unchecked (or blind control is off), creates **`Orangery: plant lighting`** |
| **Additional conditions** (*Consider sun position*, *illuminance*, *weather*) | Custom plant lighting settings | Available when custom settings are used | Internal binding | Enables custom sun, illuminance, and weather rules for lighting |
| **Turn on lighting on weekdays / weekends / Turn off at** | Custom plant lighting settings | **Shown only on first creation** of `Orangery: plant lighting` | `Orangery: plant lighting` | **Turn on on weekdays**, **Turn on on weekends**, **Turn off at** time fields |
| **Sun azimuth / Sun elevation** | Plant lighting — Sun position | **Shown only on first activation** *(seeded from sun protection during initial setup)* | `Orangery: plant lighting` | **Sun azimuth** and **Sun elevation angle** |
| **Illuminance sensor / Lower & Upper thresholds / Delay** | Plant lighting — Illuminance | Sensor available during setup; thresholds & delay **on first activation** | `Orangery: plant lighting` | **Lower illuminance threshold**, **Upper illuminance threshold**, **Illuminance delay** |

### 4. Plant Watering

| Initial Setup Field | Wizard Screen | Behavior During Reconfiguration ("Configure") | Device Card | Control on Device Card |
|---|---|---|---|---|
| **Watering valves / pumps** | Plant watering | Available when configuring plant watering | Internal binding | Defines the list of watering zones (valves/pumps) |
| **Use soil moisture sensors** | Plant watering | Available when configuring plant watering | Internal binding | Opens per-valve moisture sensor mapping screen and creates soil threshold control |
| **Morning / Evening watering time** | Plant watering | **Shown only on first activation** *(until `Orangery: watering` is created)* | `Orangery: watering` | **Morning watering** and **Evening watering** time fields |
| **Default mode & duration (morning / evening)** | Plant watering | **Shown only on first activation** *(seeds initial template for all selected valves)* | `Orangery: watering` | **Watering zone** selector + **Watering mode (morning / evening)** and **Watering duration (morning / evening)** |
| **Skip watering if moisture is above** | Watering — Soil moisture sensors | **Shown only on first activation** of moisture sensors | `Orangery: watering` | **Soil moisture threshold** (`1–100%`) |
| **Per-valve soil moisture sensors** | Watering — Soil moisture sensors | Available when configuring soil moisture sensors | Internal binding | Optional soil moisture sensor for each watering zone |
| *(Not in setup wizard)* | — | **Device card only** | `Orangery: watering` | **Auto watering** and **Skip next watering** switches |

### 5. Remote Control & Error Logging

| Initial Setup Field | Wizard Screen | Behavior During Reconfiguration ("Configure") | Device Card | Control on Device Card |
|---|---|---|---|---|
| **Device (MQTT / ZHA)** | Control device | Available when configuring remote control | Internal binding | Selected physical switch / slider |
| **Device operating mode** | Control device | **Shown only on first activation** *(adjusted on device card afterwards)* | `Orangery: control` | **Device operating mode** (*Full travel*, *Fixed step*, *Proportional*) |
| **Position step / Fast swipe threshold** | Control device | **Shown only on first activation** *(adjusted on device card afterwards)* | `Orangery: control` | **Step size** (`1–50%`) and **Swipe speed** (`10–300 mm/s`) |
| **Base MQTT topic / Up, Down, Stop messages** | Device command setup | Available when configuring remote control *(topic shown only for MQTT devices)* | Internal binding | MQTT action topic (defaults to `zigbee2mqtt/+/action`) and gesture payloads |
| **Push notification targets / Media players / Speaker TTS mode / TTS engine** | Error logging and notifications | Available when configuring error logging | Internal binding | Notification services and speaker TTS settings for drive errors |

### 6. Status & Diagnostic Indicators Across Devices

Summary state sensors are placed on the **main `Orangery` device**, while diagnostic counters are placed in the **Diagnostics** section of their respective sub-devices:

| Control | Device | Card Section | Description |
|---|---|---|---|
| **Next** | `Orangery` *(Main)* | Sensors | Nearest scheduled action across all active modules (*Blinds will open at HH:MM*, *Blinds will close at HH:MM*, *Lighting will turn on at HH:MM*, *Lighting will turn off at HH:MM*, or *Watering will start at HH:MM*), with per-module `blind_action`, `light_action`, and `watering_action` attributes created only for enabled modules. After verified commands it also exposes `last_action` (text plus local time) and `last_action_at` (ISO timestamp) |
| **Blinds** | `Orangery` *(Main)* | Sensors | Summary text of active blinds (*All fully open*, *All fully open except N*, *All fully closed*, *All fully closed except N*, *No active blinds*, or *Not configured*). Updates with a **1.5-second debounce** and exposes individual blind positions and `failed_blinds` in its attributes |
| **Lighting** | `Orangery` *(Main)* | Sensors | Summary status of plant lighting (*On*, *Off*, *On (N of M)*, or *Not configured*) with individual lamp states in attributes |
| **Watering** | `Orangery` *(Main)* | Sensors | Current irrigation state: *Scheduled (08:00, 20:00)*, *Watering: [Valve Name]*, *Skip next watering*, *No active zones*, *Disabled*, or *Not configured*. Attributes include a live summary of all zones |
| **Open** | `Orangery: drives` | Diagnostics | Number of active (non-excluded) blinds at position `>= 50%` |
| **Closed** | `Orangery: drives` | Diagnostics | Number of active (non-excluded) blinds at position `< 50%` |
| **Errors** | `Orangery: drives` | Diagnostics | Number of active target blinds that failed the last command (resets to `0` automatically when delayed blinds finish arriving) |
| **Battery level** | `Orangery: drives` | Diagnostics | Minimum battery percentage (`%`) across active blind drives, with per-drive battery levels listed in its attributes |
| **On** | `Orangery: plant lighting` | Diagnostics | Number of plant lighting switches/lights currently turned on (with per-lamp list in attributes) |
| **Off** | `Orangery: plant lighting` | Diagnostics | Number of plant lighting switches/lights currently turned off (with per-lamp list in attributes) |
| **Errors** | `Orangery: plant lighting` | Diagnostics | Number of switches/lights that failed to change state on the last command (`failed_lamps` in attributes) |
| **Active zones** | `Orangery: watering` | Diagnostics | Number of watering zones with an active morning or evening schedule (`> 0 s`, with `total_zones` in attributes) |
| **Errors** | `Orangery: watering` | Diagnostics | Total count of watering errors (valves + soil moisture sensors), with `valve_errors`, `sensor_errors`, `failed_valves`, and `failed_sensors` in attributes |
| **Battery level** | `Orangery: watering` | Diagnostics | Minimum battery percentage (`%`) across connected soil moisture sensors, with per-sensor battery levels in attributes |

In addition, the integration supports native Home Assistant system features:
- **Download Diagnostics (`diagnostics.py`)** — click *Download diagnostics* in the three-dot menu of any integration device to export a complete JSON snapshot of configuration and live entity states (with sensitive fields automatically redacted);
- **Home Assistant Repairs (`issue_registry`)** — automatically raises a warning under *Settings → System → Repairs* if blind drives, plant lights, watering valves, or soil moisture sensors fail or go offline, and clears the issue automatically once they recover.

---

## Step-by-Step Setup Guide

1. **Step 1 — Select Orangery Modules**: Check one or more modules (*Enable blind control*, *Enable plant lighting*, *Enable plant watering*), toggle **Enable error logging** if desired, and (during reconfiguration) toggle **Edit previously configured functions** if you want to modify already configured modules.
2. **Step 2 — Blind Control**: Select your blind drives and optional blind features (*Enable direct sun protection*, *Use remote control / switch*). During initial setup, configure **Travel limits**, **Schedule and sun**, and **Repeats and timings**.
3. **Step 3 — Direct Sun Protection, Solar Angles, Weather & Illuminance**: Select the sun sensor, optional subset of blinds for sun protection, solar angles (`0–359°` azimuth, `0–90°` elevation), weather conditions, and illuminance sensor/thresholds.
4. **Step 4 — Remote Control**: Select an MQTT or ZHA controller, operating mode (*Full travel*, *Fixed step*, *Proportional*), and action payloads (MQTT topic is shown only for MQTT devices).
5. **Step 5 — Plant Lighting**: Select plant lighting switches/lights and (when blind control is enabled) whether to use main integration settings or custom plant lighting settings.
6. **Step 6 — Plant Watering & Soil Moisture Sensors**: Select watering valves/pumps, optional soil moisture sensor support, initial schedule/presets, and per-valve moisture sensors.
7. **Step 7 — Error Logging & Notifications**: Select push notification targets and optional smart speakers / TTS engine for voice error alerts.

---

## Using the Device Cards

### "Orangery: drives" Card

1. **Grouped Cover Entities ("Blinds" and "Sun protection blinds"):**
   - **Blinds** (`cover.<orangery>_blinds`) controls all active (non-excluded) blind drives, and **Sun protection blinds** (`cover.<orangery>_sun_blinds`) controls active sun-facing drives when sun protection is enabled.
   - Expose these entities to any voice assistant (Yandex Alice, Apple Siri, Home Assistant Assist) or dashboard to control all active blinds with travel limits, retries, and travel verification.
2. **Drive Activity (temporary drive exclusion):**
   - When closed, the dropdown displays **`All active (5)`** or **`Excluded: 1 / 5`**.
   - Open the dropdown to toggle any drive (`✓` ↔ `✕`) without reloading the integration, or select **`↺ Enable all drives`** at the top of the list to restore all drives at once.
3. **Manual Control ("Action" + "Execute" button):**
   - Select *Stop* (default), *Open fully*, *Close fully*, or any 10% step (*Open to 10%* .. *Open to 90%*, automatically filtered by `[Down limit .. Up limit]`), then press **Execute**. The selector automatically resets to **Stop**.

### "Orangery: watering" Card

1. **Independent Morning & Evening Zone Multi-Selects:**
   - **Zones for morning watering** and **Zones for evening watering** allow independent per-valve toggling (`✓` ↔ `✕`) for morning and evening irrigation cycles (displaying **`All enabled (N)`** or **`Excluded: X / N`** when closed).
   - **Watering mode (morning / evening)** and **Watering duration (morning / evening)** (`5–600 s`) configure the trigger mode and base duration of each cycle.
2. **Manual 30-Second Dosed Watering ("Watering zone" + "Execute" button):**
   - **Watering zone** defaults to **`Stop`**.
   - Select any valve and press **Execute** to run a **30-second** manual dosed watering cycle on that valve (pressing **Execute** again while active stops watering immediately), and the selector automatically resets to **`Stop`**.
3. **Master Switches:**
   - **Auto watering** enables or disables scheduled watering cycles (turning it off also stops any active watering).
   - **Skip next watering** skips the next scheduled morning or evening cycle once and automatically resets to `OFF`.

---

## Automation Logic

- **Morning & Evening Blind Schedule**:
  - Morning opening runs at the later of sunrise (rounded up to the next full minute) and the configured weekday/weekend opening time when *Open at sunrise* is enabled, or strictly at the configured time when disabled.
  - Evening closing runs at the earlier of sunset (rounded up to the next full minute) and the configured closing time when *Close at sunset* is enabled, or strictly at the configured time when disabled.
- **Direct Sun Protection**:
  - Active during daytime (between morning opening and evening closing) while the sun is above the horizon and solar azimuth & elevation exceed the configured thresholds.
  - When both weather and illuminance filtering are enabled, the illuminance sensor takes priority whenever lux crosses the upper or lower threshold (after the configured delay).
- **Plant Watering (Irrigation System)**:
  - Triggered at **Morning watering** and **Evening watering** times when **Auto watering** is `ON`.
  - If **Skip next watering** is `ON`, the cycle is skipped and the skip switch is automatically turned `OFF`.
  - Otherwise, each configured valve is processed sequentially one by one: checks the active day mode (*Daily*, *Every other day*, *Every two days*, *By sensor*), skips watering if an attached soil moisture sensor reads `>= Soil moisture threshold`, turns the valve `ON` for its configured duration, and guarantees turning the valve `OFF` in a `finally` block even if interrupted.

---

## Disclaimer

This software is provided "AS IS", without warranty of any kind. Always verify your travel limits and timing parameters with your physical blind drives and irrigation equipment before unattended operation.
