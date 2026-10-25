# Домашняя оранжерея (Home Orangery)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-0.1.26-blue.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8.0%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Manufacturer](https://img.shields.io/badge/manufacturer-OrangeAI-purple.svg)](https://github.com/S0ft0r/ha-orangeai)
[![Author](https://img.shields.io/badge/author-%40S0ft0r-orange.svg)](https://github.com/S0ft0r)

🌐 **Язык:** **🇷🇺 Русский** | [🇬🇧 English](README.en.md)

> **Версия:** 0.1.26  
> **Производитель:** `OrangeAI` · **Автор:** [Softor (@S0ft0r)](https://github.com/S0ft0r)  
> Для сообщества: [тема на 4PDA](https://4pda.to/forum/index.php?showtopic=871505&view=findpost&p=143572987)

Интеграция для Home Assistant, которая объединяет управление шторами, подсветкой растений и многозонным поливом в оранжерее, зимнем саду, гроубоксе или на лоджии. Можно включить все модули или только нужные.

## Основные возможности

- **Шторы и жалюзи:** расписание, управление группой приводов, защита от прямого солнца с учётом положения солнца, погоды и освещённости.
- **Подсветка растений:** отдельный график или работа по основным настройкам оранжереи.
- **Многозонный полив:** независимые утренние и вечерние циклы, датчики влажности, ручной запуск и диагностика; общая Lovelace-карточка доступна в полном и кратком режимах.

## Требования

- Home Assistant `2026.8.0` или новее.
- Для модулей нужны соответствующие сущности: привода `cover.*`, светильники или реле `light.*` / `switch.*`, клапаны или насосы `switch.*`.

## Установка и настройка

### Через HACS

[![Открыть репозиторий «Домашняя оранжерея» в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=S0ft0r&repository=ha-orangeai&category=integration)

Плашка открывает страницу репозитория в HACS. Если репозиторий там не появился, добавьте `https://github.com/S0ft0r/ha-orangeai` через меню HACS → **Custom repositories**, выбрав категорию **Integration**. Затем откройте интеграцию в HACS, нажмите **Скачать** и перезапустите Home Assistant.

### Добавить и настроить интеграцию

[![Запустить настройку «Домашней оранжереи» в Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orry)

Нажмите плашку после установки, чтобы открыть мастер настройки. Также интеграцию можно добавить через **Настройки → Устройства и службы → Добавить интеграцию → Домашняя оранжерея**.

### Вручную

Скопируйте `custom_components/orry` в `config/custom_components/orry/` и перезапустите Home Assistant; затем запустите настройку плашкой выше или через **Настройки → Устройства и службы → Добавить интеграцию**.

После установки или обновления выполните жёсткую перезагрузку страницы со сбросом кэша. Это необходимо для загрузки иконок `orry:*` и карточки.

## Lovelace-карточка

`custom:orry-card` поддерживает `mode: full` (с вкладками) и `mode: summary` (только шапка и сводные плитки). В обоих режимах одинаковы сводные показатели и строка состояния. Укажите сенсор **«Далее»** главного устройства нужной конфигурации; остальные связанные сущности карточка найдёт автоматически. В Storage ресурс регистрируется автоматически, в YAML-режиме JS-модуль загружается интеграцией.

```yaml
type: custom:orry-card
mode: full  # или summary
entity: sensor.orangery_next_action  # замените на ID сенсора «Далее» вашей конфигурации
default_tab: watering
drive_indicator: position
show_position_percent: true
title: Домашняя оранжерея
```

`default_tab`: `blinds` (по умолчанию), `phytolamp` или `watering`; `title` задаёт собственный заголовок. `drive_indicator`: `position`, `battery` или `none` (без полосы; если параметр не задан, полосы нет). `show_position_percent` независимо управляет процентом положения и по умолчанию равен `true`. Необязательный `switch_icon` задаёт иконку Home Assistant вместо стандартного переключателя (например, `mdi:power`); если параметр не задан, остаётся штатный переключатель. Иконки приводов `orry:blind-0/25/50/75/100` показывают текущее положение шторы. Строки приводов включают чекбоксы защиты от солнца и рабочего режима; изменения сразу передаются интеграции. Отключённые строки штрихуются, кроме чекбокса включения. Открыть [интерактивный конструктор карточки](https://html-preview.github.io/?url=https://github.com/S0ft0r/ha-orangeai/blob/main/docs/orry-builder.html) или изучить [полную документацию](docs/DOCUMENTATION.md#кастомная-карточка-lovelace).

## Полная документация

- [Полное руководство на русском](docs/DOCUMENTATION.md)
- [Full documentation in English](docs/DOCUMENTATION.en.md)
- [История изменений](CHANGELOG.md) · [English changelog](CHANGELOG.en.md)
- [Сообщить об ошибке или предложить улучшение](https://github.com/S0ft0r/ha-orangeai/issues)
