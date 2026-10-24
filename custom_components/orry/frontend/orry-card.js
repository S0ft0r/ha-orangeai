/*
 * Full Lovelace card for the Orry Home Orangery integration.
 * The layout follows the header + KPI tiles + tabbed content pattern of dnevnik2-card.
 */

const CARD_TYPE = "orry-card";
const CARD_VERSION = "0.1.24";
const DOMAIN = "orry";

const ENTITY_KEYS = [
  "next_action",
  "status",
  "phytolamp_status",
  "watering_status",
  "blinds",
  "sun_blinds",
  "excluded_blinds",
  "blinds_for_protect",
  "battery",
  "open_count",
  "closed_count",
  "error_count",
  "phytolamp_on_count",
  "phytolamp_off_count",
  "phytolamp_error_count",
  "watering_active_count",
  "watering_error_count",
  "watering_battery",
  "watering_enabled",
  "watering_skip_next",
  "watering_execute",
  "watering_zone",
  "watering_morning_time",
  "watering_evening_time",
  "watering_morning_mode",
  "watering_evening_mode",
  "watering_morning_duration",
  "watering_evening_duration",
];

const DEVICE_GROUPS = [
  "drives",
  "schedule",
  "sun",
  "illuminance",
  "phytolamp",
  "watering",
  "control",
];

// Последний резервный поиск по видимому имени нужен для HA-клиентов,
// которые не передают unique_id/translation_key в hass.entities.
const ENTITY_FALLBACK_RULES = {
  next_action: {
    domain: "sensor",
    group: "main",
    labels: ["далее", "next", "next action", "dalee"],
  },
  status: {
    domain: "sensor",
    group: "main",
    labels: ["шторы", "blinds", "shtory"],
  },
  phytolamp_status: {
    domain: "sensor",
    group: "main",
    labels: ["подсветка", "lighting", "plant lighting", "phytolamp", "podsvetka"],
  },
  watering_status: {
    domain: "sensor",
    group: "main",
    labels: ["полив", "watering", "irrigation", "poliv"],
  },
  blinds: {
    domain: "cover",
    group: "drives",
    labels: ["шторы", "жалюзи", "blinds", "shtory"],
  },
  sun_blinds: {
    domain: "cover",
    group: "drives",
    labels: ["шторы защиты от солнца", "sun protection blinds", "shtory zashchity ot solntsa"],
  },
  excluded_blinds: {
    domain: "select",
    group: "drives",
    labels: ["используемые привода", "used drives", "ispolzuemye privoda"],
  },
  blinds_for_protect: {
    domain: "select",
    group: "drives",
    labels: ["привода защиты от солнца", "drives for sun protection", "privoda zashchity ot solntsa"],
  },
  battery: {
    domain: "sensor",
    group: "drives",
    labels: ["уровень заряда", "battery", "uroven zaryada"],
  },
  open_count: {
    domain: "sensor",
    group: "drives",
    labels: ["открыто", "open", "otkryto"],
  },
  closed_count: {
    domain: "sensor",
    group: "drives",
    labels: ["закрыто", "closed", "zakryto"],
  },
  error_count: {
    domain: "sensor",
    group: "drives",
    labels: ["ошибки", "errors", "oshibki"],
  },
  phytolamp_on_count: {
    domain: "sensor",
    group: "phytolamp",
    labels: ["включено", "on", "vklucheno"],
  },
  phytolamp_off_count: {
    domain: "sensor",
    group: "phytolamp",
    labels: ["выключено", "off", "vyklucheno"],
  },
  phytolamp_error_count: {
    domain: "sensor",
    group: "phytolamp",
    labels: ["ошибки", "errors", "oshibki"],
  },
  watering_active_count: {
    domain: "sensor",
    group: "watering",
    labels: ["активно направлений", "active zones", "aktivno napravleniy"],
  },
  watering_error_count: {
    domain: "sensor",
    group: "watering",
    labels: ["ошибки", "errors", "oshibki"],
  },
  watering_battery: {
    domain: "sensor",
    group: "watering",
    labels: ["уровень заряда", "battery", "uroven zaryada"],
  },
  watering_enabled: {
    domain: "switch",
    group: "watering",
    labels: ["автополив", "automatic watering", "auto watering", "avtopoliv"],
  },
  watering_skip_next: {
    domain: "switch",
    group: "watering",
    labels: ["пропустить следующий полив", "skip next watering", "propustit sleduyushchiy poliv"],
  },
  watering_execute: {
    domain: "button",
    group: "watering",
    labels: ["выполнить", "execute", "run watering", "vypolnit"],
  },
  watering_zone: {
    domain: "select",
    group: "watering",
    labels: ["направление полива", "watering zone", "napravlenie poliva"],
  },
  watering_morning_time: {
    domain: "time",
    group: "schedule",
    labels: ["полив утренний", "утренний полив", "morning watering", "watering morning"],
  },
  watering_evening_time: {
    domain: "time",
    group: "schedule",
    labels: ["полив вечерний", "вечерний полив", "evening watering", "watering evening"],
  },
  watering_morning_mode: {
    domain: "select",
    group: "watering",
    labels: ["режим полива утро", "watering mode morning", "morning watering mode"],
  },
  watering_evening_mode: {
    domain: "select",
    group: "watering",
    labels: ["режим полива вечер", "watering mode evening", "evening watering mode"],
  },
  watering_morning_duration: {
    domain: "number",
    group: "watering",
    labels: ["длительность полива утро", "watering duration morning", "morning watering duration"],
  },
  watering_evening_duration: {
    domain: "number",
    group: "watering",
    labels: ["длительность полива вечер", "watering duration evening", "evening watering duration"],
  },
};

const TEXT = {
  ru: {
    title: "Оранжерея",
    moduleBlinds: "Шторы",
    moduleLighting: "Подсветка",
    moduleWatering: "Полив",
    subtitle: "Модули оранжереи",
    nextAction: "Далее",
    noActions: "Нет запланированных действий",
    chooseSensor: "Выберите сенсор «Далее» на основном устройстве Orry в настройках карточки.",
    sensorNotFound: "Выбранный сенсор не найден. Проверьте настройки карточки.",
    noModules: "Не найдены активные модули Orry для выбранной оранжереи.",
    averagePosition: "Среднее положение",
    lightingOn: "Включена",
    lightingOff: "Выключена",
    lightingUnavailable: "Нет данных о светильниках",
    scheduled: "По расписанию",
    groupControl: "Сводное управление",
    allBlinds: "Все активные шторы",
    drivePositions: "Положение приводов",
    updatedNow: "Текущее состояние",
    sunProtection: "Защита от солнца",
    driveEnabled: "Привод включён в работу",
    open: "Открыть",
    stop: "Стоп",
    close: "Закрыть",
    activeDrives: "активных",
    excluded: "исключено",
    errors: "ошибок",
    noDriveData: "Нет данных о положениях приводов",
    unavailable: "Недоступно",
    on: "Включено",
    off: "Выключено",
    lightingSummary: "Состояние подсветки",
    devices: "устройств",
    wateringSchedule: "Расписание полива",
    autoWatering: "Автополив",
    skipNext: "Пропустить следующий полив",
    morning: "Утро",
    evening: "Вечер",
    zones: "направлений",
    noZones: "Нет настроенных направлений полива",
    manualWatering: "Ручной полив",
    wateringZone: "Направление полива",
    selectZone: "Выберите направление",
    runWatering: "Выполнить 30 с",
    stopWatering: "Остановить полив",
    wateringNow: "Поливается",
    notSelected: "Не выбрано",
    status: "Состояние",
    active: "Активно",
    diagnostics: "Диагностика",
    configureHint: "Откройте меню карточки и выберите сенсор «Далее» от нужной интеграции Orry.",
  },
  en: {
    title: "Orangery",
    moduleBlinds: "Blinds",
    moduleLighting: "Lighting",
    moduleWatering: "Watering",
    subtitle: "Orangery modules",
    nextAction: "Next",
    noActions: "No scheduled actions",
    chooseSensor: "Select the “Next” sensor from the Orry main device in the card settings.",
    sensorNotFound: "The selected sensor was not found. Check the card settings.",
    noModules: "No active Orry modules were found for the selected orangery.",
    averagePosition: "Average position",
    lightingOn: "On",
    lightingOff: "Off",
    lightingUnavailable: "No light data available",
    scheduled: "Scheduled",
    groupControl: "Group control",
    allBlinds: "All active blinds",
    drivePositions: "Drive positions",
    updatedNow: "Current state",
    sunProtection: "Sun protection",
    driveEnabled: "Drive enabled for operation",
    open: "Open",
    stop: "Stop",
    close: "Close",
    activeDrives: "active",
    excluded: "excluded",
    errors: "errors",
    noDriveData: "No drive position data",
    unavailable: "Unavailable",
    on: "On",
    off: "Off",
    lightingSummary: "Lighting status",
    devices: "devices",
    wateringSchedule: "Watering schedule",
    autoWatering: "Auto watering",
    skipNext: "Skip next watering",
    morning: "Morning",
    evening: "Evening",
    zones: "zones",
    noZones: "No watering zones configured",
    manualWatering: "Manual watering",
    wateringZone: "Watering zone",
    selectZone: "Select a zone",
    runWatering: "Run for 30 s",
    stopWatering: "Stop watering",
    wateringNow: "Watering",
    notSelected: "Not selected",
    status: "Status",
    active: "Active",
    diagnostics: "Diagnostics",
    configureHint: "Open the card menu and select the “Next” sensor from the desired Orry integration.",
  },
};

const ICONS = {
  greenhouse:
    "<path d='M3 20.5h18M5.5 20.5V9l6.5-5 6.5 5v11.5M9 20.5v-6h6v6M8 10.5h.01M12 10.5h.01M16 10.5h.01'/>",
  next: "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
  blinds: "<path d='M4 4h16M5 5v14M9 5v12M13 5v10M17 5v8M20 5v14M4 20h16'/>",
  light:
    "<path d='M9 18h6M10 22h4M8.5 14.5a6 6 0 1 1 7 0c-.8.6-1.3 1.4-1.4 2.5h-4.2c-.1-1.1-.6-1.9-1.4-2.5Z'/><path d='M12 2v2M4.9 4.9l1.4 1.4M19.1 4.9l-1.4 1.4'/>",
  water:
    "<path d='M12 3C9 7.3 6 10.3 6 14a6 6 0 0 0 12 0c0-3.7-3-6.7-6-11Z'/><path d='M9.5 15.5a2.5 2.5 0 0 0 2.5 2.5'/>",
  open: "<path d='M12 19V5M6 11l6-6 6 6'/>",
  close: "<path d='M12 5v14M6 13l6 6 6-6'/>",
  pause: "<rect x='6' y='5' width='4' height='14' rx='1'/><rect x='14' y='5' width='4' height='14' rx='1'/>",
  clock: "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
  drop: "<path d='M12 3C9 7.3 6 10.3 6 14a6 6 0 0 0 12 0c0-3.7-3-6.7-6-11Z'/>",
  play: "<path d='m8 5 11 7-11 7V5Z' fill='currentColor' stroke='none'/>",
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`;
}

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function haIcon(iconName) {
  const safeName = String(iconName || "").trim();
  return safeName
    ? `<ha-icon icon="${escapeHtml(safeName)}" aria-hidden="true"></ha-icon>`
    : "";
}

function languageFor(hass) {
  const language = hass?.locale?.language || hass?.language || "ru";
  return String(language).toLowerCase().startsWith("en") ? "en" : "ru";
}

function isUnavailable(value) {
  const state = String(value ?? "").trim().toLowerCase();
  return !state || state === "unknown" || state === "unavailable";
}

function isNotConfigured(value) {
  const state = String(value ?? "").trim().toLowerCase();
  return (
    isUnavailable(state) ||
    state.includes("не настро") ||
    state.includes("not configured") ||
    state.includes("not set")
  );
}

function normalizeEntityText(value) {
  return String(value || "")
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[_-]+/g, " ")
    .replace(/[^a-z0-9\u0400-\u04ff]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function labelIsPresent(text, label) {
  const normalizedLabel = normalizeEntityText(label);
  return Boolean(
    normalizedLabel &&
      (` ${text} `.includes(` ${normalizedLabel} `) || text === normalizedLabel)
  );
}

function entityKeyFromDisplayName(entityId, meta = {}, state = null, device = null) {
  const domain = String(entityId || "").split(".")[0];
  const objectId = String(entityId || "").split(".").pop().replace(/[_-]+/g, " ");
  const displayName = normalizeEntityText(
    [meta.name, meta.original_name, state?.attributes?.friendly_name, objectId]
      .filter(Boolean)
      .join(" ")
  );
  if (!displayName) return "";

  const group = deviceGroupFromDevice(device);
  for (const [key, rule] of Object.entries(ENTITY_FALLBACK_RULES)) {
    if (domain !== rule.domain || group !== rule.group) continue;
    if (rule.labels.some((label) => labelIsPresent(displayName, label))) {
      return key;
    }
  }
  return "";
}

function entityKeyMatchesScope(key, entityId, device) {
  const rule = ENTITY_FALLBACK_RULES[key];
  if (!rule || String(entityId || "").split(".")[0] !== rule.domain) return false;
  const group = deviceGroupFromDevice(device);
  if (group === null) return !["battery", "error_count"].includes(key);
  return group === rule.group;
}

function entityKey(entityId, meta = {}, entryId = "", state = null, device = null) {
  const translated = String(meta.translation_key || "").trim();
  if (translated) return translated;

  const uniqueId = String(meta.unique_id || "");
  if (entryId && uniqueId.startsWith(`${entryId}_`)) {
    return uniqueId.slice(entryId.length + 1);
  }

  const candidates = [...ENTITY_KEYS].sort((a, b) => b.length - a.length);
  for (const key of candidates) {
    const idMatches = entityId.endsWith(`_${key}`) || entityId === key;
    const uniqueIdMatches = uniqueId.endsWith(`_${key}`) || uniqueId === key;
    if (uniqueIdMatches) return key;
    if (idMatches && entityKeyMatchesScope(key, entityId, device)) return key;
  }
  return entityKeyFromDisplayName(entityId, meta, state, device);
}

function listDeviceIdentifiers(device) {
  if (!device) return [];
  const identifiers = device.identifiers;
  if (Array.isArray(identifiers)) {
    return identifiers
      .map((item) => {
        if (Array.isArray(item) && item.length >= 2) {
          return [String(item[0]), String(item[1])];
        }
        if (item && typeof item === "object") {
          return [String(item.domain || ""), String(item.identifier || item.id || "")];
        }
        return null;
      })
      .filter(Boolean);
  }
  if (identifiers && typeof identifiers === "object") {
    return Object.entries(identifiers).map(([domain, identifier]) => [
      String(domain),
      String(identifier),
    ]);
  }
  return [];
}

function entryIdFromDevice(device) {
  for (const [domain, identifier] of listDeviceIdentifiers(device)) {
    if (domain !== DOMAIN || !identifier) continue;
    for (const group of DEVICE_GROUPS) {
      const suffix = `_${group}`;
      if (identifier.endsWith(suffix)) return identifier.slice(0, -suffix.length);
    }
    return identifier;
  }
  return "";
}

function deviceGroupFromDevice(device) {
  for (const [domain, identifier] of listDeviceIdentifiers(device)) {
    if (domain !== DOMAIN || !identifier) continue;
    for (const group of DEVICE_GROUPS) {
      if (identifier.endsWith(`_${group}`)) return group;
    }
    return "main";
  }
  return null;
}

function findDefaultAnchor(hass) {
  if (!hass?.states) return "";
  const sensorIds = Object.keys(hass.states).filter((id) => id.startsWith("sensor."));
  for (const id of sensorIds) {
    const meta = hass.entities?.[id] || {};
    const state = hass.states[id];
    const device = meta.device_id ? hass.devices?.[meta.device_id] : null;
    const entryId = entryIdFromDevice(device);
    const key = entityKey(id, meta, entryId, state, device);
    const name = normalizeEntityText(
      [
        meta.name,
        meta.original_name,
        state?.attributes?.friendly_name,
        id.split(".").pop().replace(/[_-]+/g, " "),
      ]
        .filter(Boolean)
        .join(" ")
    );
    const looksLikeOrry =
      meta.platform === DOMAIN ||
      Boolean(entryId) ||
      String(meta.unique_id || "").includes("_next_action") ||
      id.endsWith("_next_action");
    if (
      looksLikeOrry &&
      (key === "next_action" ||
        String(meta.unique_id || "").endsWith("_next_action") ||
        id.endsWith("_next_action") ||
        labelIsPresent(name, "далее") ||
        labelIsPresent(name, "next action") ||
        labelIsPresent(name, "next") ||
        labelIsPresent(name, "dalee"))
    ) {
      return id;
    }
  }
  return "";
}

const CARD_STYLES = `
  :host {
    display: block;
    --orry-chip-bg: rgba(127, 127, 127, 0.10);
    --orry-tile-bg: rgba(127, 127, 127, 0.06);
    --orry-row-hover: rgba(127, 127, 127, 0.05);
  }
  * { box-sizing: border-box; }
  ha-card {
    overflow: hidden;
    color: var(--primary-text-color);
    background: var(--ha-card-background, var(--card-background-color, #fff));
  }
  button, select, input { font: inherit; }
  .clickable { cursor: pointer; }
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 14px 16px 10px;
  }
  .header-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
  .header-icon {
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: rgba(3, 169, 244, 0.16);
    color: var(--primary-color, #03a9f4);
  }
  .header-icon svg { width: 23px; height: 23px; }
  .header-titles { min-width: 0; }
  .header-title {
    overflow: hidden;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.25;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .header-subtitle { margin-top: 2px; color: var(--secondary-text-color); font-size: 12px; }
  .next-pill {
    max-width: calc(100% - 36px);
    min-width: 0;
    flex: 0 1 auto;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 9px;
    border: 1px solid rgba(3, 169, 244, 0.23);
    border-radius: 999px;
    background: rgba(3, 169, 244, 0.08);
    color: var(--primary-color, #03a9f4);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }
  .next-pill svg { width: 15px; height: 15px; flex: 0 0 15px; }
  .next-pill span { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(var(--module-count, 3), minmax(0, 1fr));
    gap: 8px;
    padding: 2px 16px 14px;
  }
  .kpi-tile {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 4px;
    padding: 8px 10px;
    border: 1px solid var(--divider-color, rgba(127,127,127,.16));
    border-radius: 10px;
    background: var(--orry-tile-bg);
  }
  .kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 5px; color: var(--secondary-text-color); font-size: 11px; }
  .kpi-top svg { width: 15px; height: 15px; flex: 0 0 15px; }
  .kpi-main { min-height: 18px; overflow: hidden; font-size: 13px; font-weight: 700; white-space: nowrap; text-overflow: ellipsis; }
  .kpi-sub { overflow: hidden; color: var(--secondary-text-color); font-size: 10px; white-space: nowrap; text-overflow: ellipsis; }

  .tabs-bar {
    display: grid;
    grid-template-columns: repeat(var(--module-count, 3), minmax(0, 1fr));
    border-top: 1px solid var(--divider-color, rgba(127,127,127,.18));
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.18));
    background: var(--orry-tile-bg);
  }
  .tab-btn {
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 6px 8px;
    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--secondary-text-color);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }
  .tab-btn svg { width: 16px; height: 16px; flex: 0 0 16px; }
  .tab-btn.active {
    border-bottom-color: var(--primary-color, #03a9f4);
    background: rgba(3, 169, 244, 0.06);
    color: var(--primary-color, #03a9f4);
  }
  .tab-badge {
    min-width: 18px;
    padding: 1px 5px;
    border-radius: 999px;
    background: var(--orry-chip-bg);
    color: var(--primary-text-color);
    font-size: 10px;
    text-align: center;
  }
  .tab-btn.active .tab-badge { background: var(--primary-color, #03a9f4); color: #fff; }

  .subbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 16px;
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.16));
    color: var(--secondary-text-color);
    font-size: 11px;
    flex-wrap: wrap;
  }
  .subbar strong { color: var(--primary-text-color); font-weight: 600; }
  .content { padding: 12px 16px 15px; }
  .control-card {
    padding: 10px 12px 11px;
    border: 1px solid var(--divider-color, rgba(127,127,127,.16));
    border-radius: 10px;
    background: var(--orry-tile-bg);
  }
  .control-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  .control-title { font-size: 13px; font-weight: 600; }
  .position-value { color: var(--primary-color, #03a9f4); font-size: 16px; font-weight: 700; }
  .position-slider { width: 100%; margin: 12px 0 10px; accent-color: var(--primary-color, #03a9f4); }
  .action-row { display: flex; gap: 7px; }
  .action-btn {
    min-height: 32px;
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    border: 1px solid var(--divider-color, rgba(127,127,127,.2));
    border-radius: 7px;
    background: var(--ha-card-background, var(--card-background-color, #fff));
    color: var(--primary-text-color);
    font-size: 11px;
    cursor: pointer;
  }
  .action-btn svg { width: 14px; height: 14px; color: var(--secondary-text-color); }
  .action-btn:disabled, .toggle:disabled, .switch-icon-button:disabled, .watering-select:disabled { cursor: default; opacity: .45; }
  .section-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin: 13px 1px 6px;
    color: var(--secondary-text-color);
    font-size: 10px;
    font-weight: 600;
  }
  .entity-list { display: flex; flex-direction: column; }
  .drive-list {
    --drive-check-width: 30px;
    --drive-column-gap: 7px;
    display: flex;
    flex-direction: column;
    margin-top: 13px;
  }
  .drive-list-heading, .drive-row {
    display: grid;
    grid-template-columns: 28px minmax(0, 1fr) var(--drive-check-width) var(--drive-check-width);
    align-items: center;
    column-gap: var(--drive-column-gap);
  }
  .drive-list-heading {
    min-height: 28px;
    padding: 0 2px 4px;
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.12));
  }
  .drive-column-icon { display: flex; align-items: center; justify-content: center; color: var(--secondary-text-color); }
  .drive-column-icon ha-icon { width: 17px; height: 17px; --mdc-icon-size: 17px; }
  .sun-column-icon { color: var(--state-icon-color, #fdd835); }
  .drive-row {
    min-height: 48px;
    position: relative;
    isolation: isolate;
    padding: 6px 2px;
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.12));
  }
  .drive-row:last-child { border-bottom: 0; }
  .drive-row[data-more-info] { cursor: pointer; }
  .drive-row[data-more-info]:hover { background: var(--orry-row-hover); }
  .drive-row > * { min-width: 0; position: relative; z-index: 1; }
  .drive-row-icon.entity-icon { width: 28px; height: 28px; }
  .drive-main { min-width: 0; }
  .drive-main-top { min-width: 0; display: flex; align-items: center; gap: 7px; }
  .drive-main-top .entity-name { min-width: 0; flex: 1; }
  .drive-position { flex: 0 0 auto; color: var(--primary-color, #03a9f4); font-size: 11px; font-weight: 700; white-space: nowrap; }
  .drive-main .mini-track { margin-top: 4px; }
  .drive-checkbox-cell { min-height: 30px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  .drive-checkbox { width: 15px; height: 15px; margin: 0; accent-color: var(--primary-color, #03a9f4); cursor: pointer; }
  .drive-checkbox:disabled { cursor: default; opacity: .55; }
  .drive-checkbox:focus-visible { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; }
  .drive-row.is-disabled::before {
    content: "";
    position: absolute;
    z-index: 0;
    top: 0;
    right: calc(var(--drive-check-width) + var(--drive-column-gap));
    bottom: 0;
    left: -2px;
    border-radius: 5px;
    background: repeating-linear-gradient(-45deg, transparent 0 5px, rgba(127,127,127,.13) 5px 7px);
    pointer-events: none;
  }
  .drive-row.is-disabled > :not(.drive-work-cell) { opacity: .42; }
  .drive-row.is-disabled > .drive-work-cell { opacity: 1; }
  .entity-row {
    min-height: 44px;
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto;
    align-items: center;
    gap: 9px;
    padding: 6px 2px;
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.12));
  }
  .entity-row:last-child { border-bottom: 0; }
  .entity-row[data-more-info] { cursor: pointer; }
  .entity-row[data-more-info]:hover { background: var(--orry-row-hover); }
  .entity-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(3, 169, 244, 0.08);
    color: var(--primary-color, #03a9f4);
  }
  .entity-icon.entity-state-icon.is-on { color: var(--state-icon-color, #fdd835); background: rgba(253, 216, 53, .12); }
  .entity-icon.entity-state-icon.is-off { color: var(--secondary-text-color); background: var(--orry-chip-bg); }
  .entity-icon svg, .entity-icon ha-icon { width: 16px; height: 16px; --mdc-icon-size: 16px; }
  .entity-name { overflow: hidden; font-size: 12px; font-weight: 500; white-space: nowrap; text-overflow: ellipsis; }
  .entity-state { margin-top: 2px; color: var(--secondary-text-color); font-size: 10px; }
  .entity-value { color: var(--primary-text-color); font-size: 12px; font-weight: 600; white-space: nowrap; }
  .mini-track { width: 100%; height: 4px; margin-top: 5px; overflow: hidden; border-radius: 999px; background: var(--orry-chip-bg); }
  .mini-fill { height: 100%; border-radius: inherit; background: var(--primary-color, #03a9f4); }
  .mini-fill.drive-battery-green { background: #4caf50; }
  .mini-fill.drive-battery-yellow { background: #fdd835; }
  .mini-fill.drive-battery-orange { background: #ff9800; }
  .mini-fill.drive-battery-red { background: #f44336; }
  .empty-inline { padding: 14px 4px; color: var(--secondary-text-color); font-size: 12px; text-align: center; }
  .panel { display: none; }
  .panel.active { display: block; }
  .toggle-row {
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 7px 2px;
    border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.12));
  }
  .toggle-row:last-child { border-bottom: 0; }
  .toggle-label { font-size: 12px; font-weight: 500; }
  .toggle-sub { margin-top: 2px; color: var(--secondary-text-color); font-size: 10px; }
  .toggle-main { min-width: 0; display: flex; align-items: center; gap: 9px; }
  .switch-icon-button {
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    border: 0;
    border-radius: 50%;
    background: transparent;
    color: var(--secondary-text-color);
    cursor: pointer;
    transition: color .15s ease, background .15s ease;
  }
  .switch-icon-button:hover { background: var(--orry-row-hover); }
  .switch-icon-button.on { color: var(--state-icon-color, #fdd835); }
  .switch-icon-button ha-icon { width: 20px; height: 20px; --mdc-icon-size: 20px; }
  .switch-icon-button:focus-visible, .toggle:focus-visible { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; }
  .toggle {
    width: 36px;
    height: 21px;
    flex: 0 0 36px;
    padding: 2px;
    border: 0;
    border-radius: 999px;
    background: rgba(127,127,127,.32);
    cursor: pointer;
    transition: background .15s ease;
  }
  .toggle span {
    width: 17px;
    height: 17px;
    display: block;
    border-radius: 50%;
    background: #fff;
    box-shadow: 0 1px 2px rgba(0,0,0,.24);
    transition: transform .15s ease;
  }
  .toggle.on { background: var(--primary-color, #03a9f4); }
  .toggle.on span { transform: translateX(15px); }
  .schedule-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 10px 0 3px; }
  .schedule-tile { padding: 8px 10px; border: 1px solid var(--divider-color, rgba(127,127,127,.16)); border-radius: 9px; background: var(--orry-tile-bg); }
  .schedule-title { color: var(--secondary-text-color); font-size: 10px; }
  .schedule-value { margin-top: 4px; font-size: 12px; font-weight: 600; }
  .watering-select-row { display: flex; align-items: center; gap: 8px; margin-top: 12px; }
  .watering-select {
    min-width: 0;
    flex: 1;
    height: 34px;
    padding: 0 8px;
    border: 1px solid var(--divider-color, rgba(127,127,127,.2));
    border-radius: 7px;
    background: var(--ha-card-background, var(--card-background-color, #fff));
    color: var(--primary-text-color);
    font-size: 11px;
  }
  .execute-btn {
    min-height: 34px;
    padding: 0 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    border: 0;
    border-radius: 7px;
    background: var(--primary-color, #03a9f4);
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }
  .execute-btn svg { width: 14px; height: 14px; }
  .execute-btn:disabled { cursor: default; opacity: .45; }
  .zone-row { padding: 8px 2px; border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.12)); }
  .zone-row:last-child { border-bottom: 0; }
  .zone-info { color: var(--secondary-text-color); font-size: 10px; line-height: 1.45; }
  .empty-box { padding: 20px 16px; color: var(--secondary-text-color); text-align: center; font-size: 13px; }
  @media (max-width: 420px) {
    .header { padding-left: 12px; padding-right: 12px; }
    .kpi-grid { padding-left: 12px; padding-right: 12px; }
    .kpi-grid.module-count-1 { grid-template-columns: 1fr; }
    .kpi-grid.module-count-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .kpi-grid.module-count-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .kpi-grid.module-count-3 .kpi-tile:last-child { grid-column: span 2; }
    .content { padding-left: 12px; padding-right: 12px; }
    .subbar { padding-left: 12px; padding-right: 12px; }
    .tab-btn { gap: 4px; padding-left: 3px; padding-right: 3px; font-size: 11px; }
    .next-pill { max-width: calc(100% - 36px); font-size: 10px; }
    .action-btn { font-size: 10px; }
  }
  @media (max-width: 380px) {
    .drive-list { --drive-check-width: 25px; --drive-column-gap: 5px; }
    .drive-list-heading, .drive-row { grid-template-columns: 24px minmax(0, 1fr) var(--drive-check-width) var(--drive-check-width); }
    .drive-row-icon.entity-icon { width: 24px; height: 24px; }
    .drive-position { font-size: 10px; }
  }
`;

class OrryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._bundle = null;
    this._activeTab = "blinds";
    this._userSwitchedTab = false;
    this._lastRenderSig = "";
  }

  static getStubConfig(hass) {
    return {
      entity: findDefaultAnchor(hass),
      default_tab: "blinds",
      drive_indicator: "position",
      show_position_percent: true,
    };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {
              domain: "sensor",
              integration: DOMAIN,
            },
          },
        },
        {
          name: "default_tab",
          default: "blinds",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "blinds", label: "Шторы" },
                { value: "phytolamp", label: "Подсветка" },
                { value: "watering", label: "Полив" },
              ],
            },
          },
        },
        { name: "title", selector: { text: {} } },
        { name: "switch_icon", selector: { icon: {} } },
        {
          name: "drive_indicator",
          default: "position",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "position", label: "Положение шторы" },
                { value: "battery", label: "Заряд батареи" },
                { value: "none", label: "Без индикатора" },
              ],
            },
          },
        },
        {
          name: "show_position_percent",
          default: true,
          selector: { boolean: {} },
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "entity":
            return "Основной сенсор «Далее»";
          case "default_tab":
            return "Вкладка по умолчанию";
          case "title":
            return "Свой заголовок (необязательно)";
          case "switch_icon":
            return "Иконка вместо переключателя (необязательно)";
          case "drive_indicator":
            return "Индикатор приводов штор";
          case "show_position_percent":
            return "Показывать процент положения штор";
          default:
            return schema.name;
        }
      },
      computeHelper: (schema) => {
        if (schema.name === "entity") {
          return "Выберите сенсор «Далее» с основного устройства. Карточка найдёт остальные сущности этой конфигурации Orry автоматически.";
        }
        if (schema.name === "drive_indicator") {
          return "Выберите одну полосу: положение шторы, заряд батареи или отсутствие полосы.";
        }
        if (schema.name === "switch_icon") {
          return "Если не задана, отображается стандартный переключатель; если задана — указанная иконка вместо него.";
        }
        if (schema.name === "show_position_percent") {
          return "Показ процента положения не зависит от выбранной полосы и всегда относится к положению шторы.";
        }
        return undefined;
      },
    };
  }

  setConfig(config) {
    if (!config) throw new Error("A card configuration is required");
    this._config = {
      default_tab: "blinds",
      show_position_percent: true,
      ...config,
    };
    if (!this._userSwitchedTab) {
      this._activeTab = this._config.default_tab || "blinds";
    }
    this._bundle = this._hass ? this._resolveEntities() : null;
    this._lastRenderSig = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._bundle = this._resolveEntities();
    const watched = this._watchedEntityIds(this._bundle);
    const signature = JSON.stringify({
      config: this._config,
      tab: this._activeTab,
      language: languageFor(hass),
      states: watched.map((entityId) => {
        const state = hass?.states?.[entityId];
        return [
          entityId,
          state?.state || "",
          state?.last_updated || "",
          state?.attributes || {},
        ];
      }),
    });
    if (signature !== this._lastRenderSig) {
      this._lastRenderSig = signature;
      this._render();
    }
  }

  getCardSize() {
    return 8;
  }

  _resolveEntities() {
    const hass = this._hass;
    const anchorId =
      this._config?.entity || findDefaultAnchor(hass) || "";
    const ids = Object.fromEntries(ENTITY_KEYS.map((key) => [key, ""]));
    if (!hass || !hass.states || !anchorId) {
      return { anchorId, entryId: "", mainDeviceId: "", ids, states: {}, mainDevice: null };
    }

    const anchorMeta = hass.entities?.[anchorId] || {};
    const anchorDeviceId = anchorMeta.device_id || "";
    const anchorDevice = anchorDeviceId ? hass.devices?.[anchorDeviceId] : null;
    const entryId =
      String(anchorMeta.config_entry_id || "") ||
      entryIdFromDevice(anchorDevice) ||
      this._entryIdFromUnique(anchorMeta.unique_id || "");

    let mainDeviceId = anchorDeviceId;
    let currentDevice = anchorDevice;
    const visited = new Set();
    while (currentDevice?.via_device_id && !visited.has(currentDevice.via_device_id)) {
      visited.add(currentDevice.via_device_id);
      mainDeviceId = currentDevice.via_device_id;
      currentDevice = hass.devices?.[mainDeviceId];
    }
    if (entryId && (!currentDevice || currentDevice === anchorDevice)) {
      for (const [deviceId, device] of Object.entries(hass.devices || {})) {
        if (
          listDeviceIdentifiers(device).some(
            ([domain, identifier]) => domain === DOMAIN && identifier === entryId
          )
        ) {
          mainDeviceId = deviceId;
          currentDevice = device;
          break;
        }
      }
    }

    const relatedDeviceIds = new Set();
    if (anchorDeviceId) relatedDeviceIds.add(anchorDeviceId);
    if (mainDeviceId) relatedDeviceIds.add(mainDeviceId);

    for (const [deviceId, device] of Object.entries(hass.devices || {})) {
      const belongsByIdentifier = entryId
        ? listDeviceIdentifiers(device).some(
            ([domain, identifier]) =>
              domain === DOMAIN &&
              (identifier === entryId || identifier.startsWith(`${entryId}_`))
          )
        : false;
      const configEntries = Array.isArray(device.config_entries)
        ? device.config_entries
        : [];
      const belongsByEntry = entryId
        ? configEntries.some((item) => {
            const id = typeof item === "string" ? item : item?.entry_id || item?.id;
            return String(id || "") === entryId;
          })
        : false;
      const belongsByParent = mainDeviceId && device.via_device_id === mainDeviceId;
      if (belongsByIdentifier || belongsByEntry || belongsByParent) {
        relatedDeviceIds.add(deviceId);
      }
    }

    const candidates = [];
    for (const [entityId, meta] of Object.entries(hass.entities || {})) {
      if (!meta) continue;
      const uniqueId = String(meta.unique_id || "");
      const sameEntry = Boolean(entryId && uniqueId.startsWith(`${entryId}_`));
      const sameDevice = Boolean(meta.device_id && relatedDeviceIds.has(meta.device_id));
      if (meta.platform && meta.platform !== DOMAIN) continue;
      if (!sameEntry && !sameDevice) continue;
      candidates.push([entityId, meta]);
    }

    // Keep an explicitly selected anchor even on frontend builds that omit entity registry metadata.
    if (!candidates.some(([entityId]) => entityId === anchorId)) {
      candidates.push([anchorId, anchorMeta]);
    }

    for (const [entityId, meta] of candidates) {
      const device = meta.device_id ? hass.devices?.[meta.device_id] : null;
      const key = entityKey(
        entityId,
        meta,
        entryId,
        hass.states[entityId],
        device
      );
      if (Object.prototype.hasOwnProperty.call(ids, key) && !ids[key]) {
        ids[key] = entityId;
      }
    }

    const states = {};
    for (const [key, entityId] of Object.entries(ids)) {
      states[key] = entityId ? hass.states[entityId] || null : null;
    }

    let mainDevice = mainDeviceId ? hass.devices?.[mainDeviceId] : null;
    if (!mainDevice && anchorDevice) mainDevice = anchorDevice;

    return { anchorId, entryId, mainDeviceId, mainDevice, ids, states };
  }

  _entryIdFromUnique(uniqueId) {
    const value = String(uniqueId || "");
    const knownKeys = [...ENTITY_KEYS].sort((a, b) => b.length - a.length);
    for (const key of knownKeys) {
      const suffix = `_${key}`;
      if (value.endsWith(suffix)) return value.slice(0, -suffix.length);
    }
    const split = value.indexOf("_");
    return split > 0 ? value.slice(0, split) : "";
  }

  _watchedEntityIds(bundle) {
    const watched = new Set(Object.values(bundle?.ids || {}).filter(Boolean));
    const coverState = bundle?.states?.blinds;
    const coverAttrs = coverState?.attributes || {};
    for (const entityId of coverAttrs.all_blinds || []) watched.add(entityId);
    for (const entityId of coverAttrs.active_blinds || []) watched.add(entityId);
    const lightAttrs = bundle?.states?.phytolamp_status?.attributes || {};
    const configuredLights = lightAttrs.orry_phytolamps || lightAttrs.phytolamps;
    if (Array.isArray(configuredLights)) {
      for (const item of configuredLights) {
        if (item?.entity_id) watched.add(item.entity_id);
      }
    }
    const wateringAttrs = bundle?.states?.watering_status?.attributes || {};
    const configuredZones = wateringAttrs.orry_watering_zones || wateringAttrs.watering_zones;
    if (Array.isArray(configuredZones)) {
      for (const item of configuredZones) {
        if (item?.entity_id) watched.add(item.entity_id);
      }
    }
    return [...watched];
  }

  _text(key) {
    const lang = languageFor(this._hass);
    return TEXT[lang]?.[key] || TEXT.ru[key] || key;
  }

  _state(bundle, key) {
    const entityId = bundle?.ids?.[key];
    return entityId ? this._hass?.states?.[entityId] || null : null;
  }

  _entityName(entityId) {
    const state = this._hass?.states?.[entityId];
    const meta = this._hass?.entities?.[entityId];
    return (
      state?.attributes?.friendly_name ||
      meta?.name ||
      meta?.original_name ||
      entityId ||
      ""
    );
  }

  _lights(bundle) {
    const attrs = this._state(bundle, "phytolamp_status")?.attributes || {};
    const details = attrs.orry_phytolamps || attrs.phytolamps;
    if (Array.isArray(details)) {
      return details.map((item) => ({ ...item }));
    }
    return Object.entries(attrs)
      .filter(([key, value]) => typeof value === "string" && !key.startsWith("_"))
      .map(([name, state]) => ({ name, state, entity_id: "", is_on: null }));
  }

  _wateringZones(bundle) {
    const attrs = this._state(bundle, "watering_status")?.attributes || {};
    const configuredZones = attrs.orry_watering_zones || attrs.watering_zones;
    if (Array.isArray(configuredZones)) {
      return configuredZones.map((item) => ({ ...item }));
    }
    return Object.entries(attrs)
      .filter(([key, value]) => typeof value === "string" && !["icon", "friendly_name"].includes(key))
      .map(([name, summary]) => ({ name, summary }));
  }

  _modules(bundle) {
    const modules = [];
    if (bundle.ids.blinds) {
      modules.push({ key: "blinds", title: this._text("moduleBlinds"), icon: "blinds" });
    }

    const phytolampState = this._state(bundle, "phytolamp_status");
    if (
      this._lights(bundle).length > 0 ||
      (phytolampState && !isNotConfigured(phytolampState.state))
    ) {
      modules.push({ key: "phytolamp", title: this._text("moduleLighting"), icon: "light" });
    }

    const wateringState = this._state(bundle, "watering_status");
    if (
      bundle.ids.watering_enabled ||
      bundle.ids.watering_skip_next ||
      bundle.ids.watering_execute ||
      (wateringState && !isNotConfigured(wateringState.state))
    ) {
      modules.push({ key: "watering", title: this._text("moduleWatering"), icon: "water" });
    }
    return modules;
  }

  _displayState(state, fallback = "—") {
    if (!state || isUnavailable(state.state)) return fallback;
    return String(state.state);
  }

  _position(state) {
    const raw = state?.attributes?.current_position;
    if (raw === null || raw === undefined || raw === "") return null;
    const number = Number(raw);
    return Number.isFinite(number) ? Math.max(0, Math.min(100, Math.round(number))) : null;
  }

  _percentValue(raw) {
    if (raw === null || raw === undefined || raw === "") return null;
    const match = String(raw).match(/-?\d+(?:[.,]\d+)?/);
    if (!match) return null;
    const value = Number(match[0].replace(",", "."));
    return Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value))) : null;
  }

  _blindBatteryPercent(bundle, entityId, state) {
    for (const key of ["battery", "battery_level"]) {
      const direct = this._percentValue(state?.attributes?.[key]);
      if (direct !== null) return direct;
    }

    const batteryAttributes = this._state(bundle, "battery")?.attributes || {};
    const friendlyName = state?.attributes?.friendly_name || this._entityName(entityId);
    const candidates = [
      friendlyName,
      `${friendlyName} (${entityId})`,
      entityId,
      entityId?.split(".").pop(),
    ].filter(Boolean);
    for (const candidate of candidates) {
      const value = this._percentValue(batteryAttributes[candidate]);
      if (value !== null) return value;
    }

    const normalizedCandidates = new Set(candidates.map((value) => String(value).trim().toLowerCase()));
    for (const [name, value] of Object.entries(batteryAttributes)) {
      if (normalizedCandidates.has(String(name).trim().toLowerCase())) {
        const percent = this._percentValue(value);
        if (percent !== null) return percent;
      }
    }
    return null;
  }

  _render() {
    if (!this.shadowRoot) return;
    const bundle = this._bundle || this._resolveEntities();
    const t = (key) => this._text(key);

    if (!this._hass || !bundle.anchorId) {
      this.shadowRoot.innerHTML = `
        <style>${CARD_STYLES}</style>
        <ha-card><div class="empty-box">${escapeHtml(t("chooseSensor"))}</div></ha-card>
      `;
      return;
    }

    if (!this._hass.states?.[bundle.anchorId]) {
      this.shadowRoot.innerHTML = `
        <style>${CARD_STYLES}</style>
        <ha-card><div class="empty-box">${escapeHtml(t("sensorNotFound"))}</div></ha-card>
      `;
      return;
    }

    const modules = this._modules(bundle);
    if (!modules.length) {
      this.shadowRoot.innerHTML = `
        <style>${CARD_STYLES}</style>
        <ha-card><div class="empty-box">${escapeHtml(t("noModules"))}</div></ha-card>
      `;
      return;
    }

    if (!modules.some((module) => module.key === this._activeTab)) {
      const requested = this._config.default_tab;
      this._activeTab = modules.some((module) => module.key === requested)
        ? requested
        : modules[0].key;
    }

    const title =
      this._config.title ||
      bundle.mainDevice?.name_by_user ||
      bundle.mainDevice?.name ||
      t("title");
    const subtitle = modules.map((module) => module.title).join(" · ");
    const nextState = this._state(bundle, "next_action");
    const nextText = this._displayState(nextState, t("noActions"));

    this.shadowRoot.innerHTML = `
      <style>${CARD_STYLES}</style>
      <ha-card>
        <div class="header">
          <div class="header-left">
            <div class="header-icon">${icon("greenhouse")}</div>
            <div class="header-titles">
              <div class="header-title">${escapeHtml(title)}</div>
              <div class="header-subtitle">${escapeHtml(subtitle || t("subtitle"))}</div>
            </div>
          </div>
          <div class="next-pill clickable" data-more-info="${escapeHtml(bundle.ids.next_action || bundle.anchorId)}" title="${escapeHtml(nextText)}">
            ${icon("next")}<span><b>${escapeHtml(t("nextAction"))}:</b> ${escapeHtml(nextText)}</span>
          </div>
        </div>

        <div class="kpi-grid module-count-${modules.length}" style="--module-count:${modules.length}">
          ${modules.map((module) => this._renderKpi(module, bundle)).join("")}
        </div>

        <div class="tabs-bar" style="--module-count:${modules.length}">
          ${modules.map((module) => this._renderTab(module, bundle)).join("")}
        </div>

        ${modules
          .map((module) => {
            const body =
              module.key === "blinds"
                ? this._renderBlindsPanel(bundle)
                : module.key === "phytolamp"
                  ? this._renderLightingPanel(bundle)
                  : this._renderWateringPanel(bundle);
            return `<section class="panel ${module.key === this._activeTab ? "active" : ""}" data-panel="${module.key}">${body}</section>`;
          })
          .join("")}
      </ha-card>
    `;
    this._bindEvents(bundle);
  }

  _renderKpi(module, bundle) {
    const t = (key) => this._text(key);
    let value = "—";
    let sub = "";
    let entityId = "";

    if (module.key === "blinds") {
      const cover = this._state(bundle, "blinds");
      const position = this._position(cover);
      const status = this._state(bundle, "status");
      value = position === null ? this._displayState(status) : `${position}%`;
      sub = position === null ? t("averagePosition") : t("averagePosition");
      entityId = bundle.ids.blinds || bundle.ids.status;
    } else if (module.key === "phytolamp") {
      const status = this._state(bundle, "phytolamp_status");
      const lights = this._lights(bundle);
      const onCount = lights.filter((item) => this._lightIsOn(item)).length;
      value = this._displayState(status);
      sub = lights.length
        ? `${onCount} / ${lights.length} ${t("devices")}`
        : t("lightingSummary");
      entityId = bundle.ids.phytolamp_status;
    } else {
      const status = this._state(bundle, "watering_status");
      const zones = this._wateringZones(bundle);
      value = this._displayState(status);
      sub = zones.length ? `${zones.length} ${t("zones")}` : t("wateringSchedule");
      entityId = bundle.ids.watering_status;
    }

    return `
      <div class="kpi-tile clickable" data-more-info="${escapeHtml(entityId)}">
        <div class="kpi-top"><span>${escapeHtml(module.title)}</span>${icon(module.icon)}</div>
        <div class="kpi-main" title="${escapeHtml(value)}">${escapeHtml(value)}</div>
        <div class="kpi-sub" title="${escapeHtml(sub)}">${escapeHtml(sub)}</div>
      </div>
    `;
  }

  _renderTab(module, bundle) {
    let count = 0;
    if (module.key === "blinds") {
      count = this._allBlindIds(bundle).length;
    } else if (module.key === "phytolamp") {
      count = this._lights(bundle).length;
    } else {
      count = this._wateringZones(bundle).length;
    }
    return `
      <button class="tab-btn ${module.key === this._activeTab ? "active" : ""}" data-action="switch-tab" data-tab="${module.key}">
        ${icon(module.icon)}<span>${escapeHtml(module.title)}</span>${count ? `<span class="tab-badge">${count}</span>` : ""}
      </button>
    `;
  }

  _activeBlindIds(bundle) {
    const selectAttrs = this._state(bundle, "excluded_blinds")?.attributes || {};
    const coverAttrs = this._state(bundle, "blinds")?.attributes || {};
    const active = Array.isArray(selectAttrs.active_blinds)
      ? selectAttrs.active_blinds
      : coverAttrs.active_blinds;
    if (Array.isArray(active)) return active.filter((id) => typeof id === "string");
    return [];
  }

  _allBlindIds(bundle) {
    const coverAttrs = this._state(bundle, "blinds")?.attributes || {};
    const workAttrs = this._state(bundle, "excluded_blinds")?.attributes || {};
    const sunAttrs = this._state(bundle, "blinds_for_protect")?.attributes || {};
    const all = Array.isArray(coverAttrs.all_blinds)
      ? coverAttrs.all_blinds
      : Array.isArray(workAttrs.all_blinds)
        ? workAttrs.all_blinds
        : Array.isArray(sunAttrs.all_blinds)
          ? sunAttrs.all_blinds
          : null;
    if (all) return [...new Set(all.filter((id) => typeof id === "string"))];

    const fallback = [
      ...(Array.isArray(coverAttrs.active_blinds) ? coverAttrs.active_blinds : []),
      ...(Array.isArray(coverAttrs.excluded_blinds) ? coverAttrs.excluded_blinds : []),
      ...(Array.isArray(workAttrs.active_blinds) ? workAttrs.active_blinds : []),
      ...(Array.isArray(workAttrs.excluded_blinds) ? workAttrs.excluded_blinds : []),
    ];
    return [...new Set(fallback.filter((id) => typeof id === "string"))];
  }

  _blindIcon(entityId, state, position) {
    const metaIcon = this._hass?.entities?.[entityId]?.icon;
    const entityIcon = metaIcon || state?.attributes?.icon;
    if (entityIcon) return haIcon(entityIcon);
    if (position !== null) {
      const step = Math.max(0, Math.min(100, Math.round(position / 25) * 25));
      return haIcon(`orry:blind-${step}`) || icon("blinds");
    }
    return icon("blinds");
  }

  _renderBlindsPanel(bundle) {
    const t = (key) => this._text(key);
    const coverId = bundle.ids.blinds;
    const cover = this._state(bundle, "blinds");
    const pos = this._position(cover);
    const allBlinds = this._allBlindIds(bundle);
    const activeIds = new Set(this._activeBlindIds(bundle));
    const workSelectId = bundle.ids.excluded_blinds || "";
    const workSelect = this._state(bundle, "excluded_blinds");
    const workAttrs = workSelect?.attributes || {};
    const sunSelectId = bundle.ids.blinds_for_protect || "";
    const sunSelect = this._state(bundle, "blinds_for_protect");
    const sunAttrs = sunSelect?.attributes || {};
    const sunCoverAttrs = this._state(bundle, "sun_blinds")?.attributes || {};
    const sunSelected = new Set(
      Array.isArray(sunAttrs.selected_blinds)
        ? sunAttrs.selected_blinds
        : Array.isArray(sunCoverAttrs.active_blinds)
          ? sunCoverAttrs.active_blinds
          : []
    );
    const workOptions = workAttrs.option_by_blind || {};
    const sunOptions = sunAttrs.option_by_blind || {};
    const excluded = allBlinds.filter((entityId) => !activeIds.has(entityId));
    const openCount = this._displayState(this._state(bundle, "open_count"), "0");
    const errors = this._displayState(this._state(bundle, "error_count"), "0");
    const summary = `${openCount} ${t("activeDrives")} · ${errors} ${t("errors")}`;
    const coverAvailable = Boolean(coverId && cover && !isUnavailable(cover.state));

    const indicatorMode = ["position", "battery"].includes(this._config?.drive_indicator)
      ? this._config.drive_indicator
      : "none";
    const showPositionPercent = this._config?.show_position_percent !== false;
    const rows = allBlinds
      .map((entityId) => {
        const state = this._hass.states?.[entityId];
        const position = this._position(state);
        const battery = this._blindBatteryPercent(bundle, entityId, state);
        const name = this._entityName(entityId);
        const isWorking = activeIds.has(entityId);
        const sunOption = sunOptions[entityId] || "";
        const workOption = workOptions[entityId] || "";
        let indicator = "";

        if (indicatorMode === "position" && position !== null) {
          indicator = `<div class="mini-track" aria-label="${position}%"><div class="mini-fill" style="width:${position}%"></div></div>`;
        } else if (indicatorMode === "battery" && battery !== null) {
          const colorClass = battery >= 45
            ? "drive-battery-green"
            : battery >= 35
              ? "drive-battery-yellow"
              : battery >= 15
                ? "drive-battery-orange"
                : "drive-battery-red";
          indicator = `<div class="mini-track" aria-label="${battery}%"><div class="mini-fill ${colorClass}" style="width:${battery}%"></div></div>`;
        }

        const positionText = position === null
          ? "—"
          : showPositionPercent
            ? `${position}%`
            : "";
        const rowClass = `drive-row clickable${isWorking ? "" : " is-disabled"}`;
        const sunChecked = sunSelected.has(entityId);
        const sunAvailable = Boolean(sunSelectId && sunOption);
        const workAvailable = Boolean(workSelectId && workOption);
        return `
          <div class="${rowClass}" data-more-info="${escapeHtml(entityId)}">
            <div class="entity-icon drive-row-icon">${this._blindIcon(entityId, state, position)}</div>
            <div class="drive-main">
              <div class="drive-main-top">
                <div class="entity-name" title="${escapeHtml(name)}">${escapeHtml(name)}</div>
                <span class="drive-position">${escapeHtml(positionText)}</span>
              </div>
              ${indicator}
            </div>
            <label class="drive-checkbox-cell drive-sun-cell" title="${escapeHtml(t("sunProtection"))}">
              <input class="drive-checkbox" type="checkbox" data-action="drive-sun-toggle" data-entity="${escapeHtml(sunSelectId)}" data-option="${escapeHtml(sunOption)}" aria-label="${escapeHtml(`${name}: ${t("sunProtection")}`)}" ${sunChecked ? "checked" : ""} ${sunAvailable ? "" : "disabled"}>
            </label>
            <label class="drive-checkbox-cell drive-work-cell" title="${escapeHtml(t("driveEnabled"))}">
              <input class="drive-checkbox" type="checkbox" data-action="drive-work-toggle" data-entity="${escapeHtml(workSelectId)}" data-option="${escapeHtml(workOption)}" aria-label="${escapeHtml(`${name}: ${t("driveEnabled")}`)}" ${isWorking ? "checked" : ""} ${workAvailable ? "" : "disabled"}>
            </label>
          </div>
        `;
      })
      .join("");

    return `
      <div class="subbar"><span><strong>${escapeHtml(t("groupControl"))}</strong></span><span>${escapeHtml(summary)}${excluded.length ? ` · ${excluded.length} ${escapeHtml(t("excluded"))}` : ""}</span></div>
      <div class="content">
        <div class="control-card">
          <div class="control-heading"><span class="control-title">${escapeHtml(t("allBlinds"))}</span><span class="position-value">${pos === null ? "—" : `${pos}%`}</span></div>
          <input class="position-slider" type="range" min="0" max="100" step="1" value="${pos === null ? 0 : pos}" data-action="set-position" data-entity="${escapeHtml(coverId)}" aria-label="${escapeHtml(t("averagePosition"))}" ${!coverAvailable || pos === null ? "disabled" : ""}>
          <div class="action-row">
            <button class="action-btn" data-action="cover-service" data-service="open_cover" data-entity="${escapeHtml(coverId)}" ${!coverAvailable ? "disabled" : ""}>${icon("open")}<span>${escapeHtml(t("open"))}</span></button>
            <button class="action-btn" data-action="cover-service" data-service="stop_cover" data-entity="${escapeHtml(coverId)}" ${!coverAvailable ? "disabled" : ""}>${icon("pause")}<span>${escapeHtml(t("stop"))}</span></button>
            <button class="action-btn" data-action="cover-service" data-service="close_cover" data-entity="${escapeHtml(coverId)}" ${!coverAvailable ? "disabled" : ""}>${icon("close")}<span>${escapeHtml(t("close"))}</span></button>
          </div>
        </div>
        <div class="drive-list">
          <div class="drive-list-heading" aria-label="${escapeHtml(t("drivePositions"))}">
            <span></span><span></span>
            <span class="drive-column-icon sun-column-icon" title="${escapeHtml(t("sunProtection"))}">${haIcon("mdi:white-balance-sunny")}</span>
            <span class="drive-column-icon" title="${escapeHtml(t("driveEnabled"))}">${haIcon("mdi:power")}</span>
          </div>
          ${rows || `<div class="empty-inline">${escapeHtml(t("noDriveData"))}</div>`}
        </div>
      </div>
    `;
  }

  _lightIsOn(item) {
    const state = item?.entity_id ? this._hass?.states?.[item.entity_id] : null;
    if (state?.state === "on") return true;
    if (state?.state === "off") return false;
    return item?.is_on === true;
  }

  _lightIsAvailable(item) {
    const state = item?.entity_id ? this._hass?.states?.[item.entity_id] : null;
    if (state) return !isUnavailable(state.state);
    return item?.available !== false && item?.is_on !== null;
  }

  _renderSwitchControl(action, entityId, label, isOn, disabled) {
    const iconName = String(this._config?.switch_icon || "").trim();
    const className = iconName ? "switch-icon-button" : "toggle";
    const content = iconName ? haIcon(iconName) : "<span></span>";
    const title = iconName ? ` title="${escapeHtml(iconName)}"` : "";
    return `<button class="${className} ${isOn ? "on" : ""}" data-action="${escapeHtml(action)}" data-entity="${escapeHtml(entityId)}" aria-pressed="${isOn}" aria-label="${escapeHtml(label)}"${title} ${disabled ? "disabled" : ""}>${content}</button>`;
  }

  _renderLightingPanel(bundle) {
    const t = (key) => this._text(key);
    const status = this._state(bundle, "phytolamp_status");
    const lights = this._lights(bundle);
    const onCount = lights.filter((item) => this._lightIsOn(item)).length;
    const rows = lights
      .map((item) => {
        const entityId = item.entity_id || "";
        const state = entityId ? this._hass.states?.[entityId] : null;
        const isOn = this._lightIsOn(item);
        const available = this._lightIsAvailable(item);
        const stateText =
          item.state ||
          (state?.state === "on" ? t("lightingOn") : state?.state === "off" ? t("lightingOff") : t("unavailable"));
        const safeName = item.name || (entityId ? this._entityName(entityId) : t("moduleLighting"));
        const entityIcon = item.icon || state?.attributes?.icon;
        const leadingIcon = haIcon(entityIcon) || icon("light");
        return `
          <div class="toggle-row ${entityId ? "clickable" : ""}" ${entityId ? `data-more-info="${escapeHtml(entityId)}"` : ""}>
            <div class="toggle-main">
              <div class="entity-icon entity-state-icon ${isOn ? "is-on" : "is-off"}">${leadingIcon}</div>
              <div><div class="toggle-label">${escapeHtml(safeName)}</div><div class="toggle-sub">${escapeHtml(stateText)}</div></div>
            </div>
            ${entityId ? this._renderSwitchControl("toggle-light", entityId, safeName, isOn, !available) : ""}
          </div>
        `;
      })
      .join("");
    const summary = this._displayState(status, t("lightingUnavailable"));
    const trailing = lights.length
      ? `${onCount} / ${lights.length} ${t("devices")}`
      : summary;

    return `
      <div class="subbar"><span><strong>${escapeHtml(t("lightingSummary"))}</strong></span><span>${escapeHtml(trailing)}</span></div>
      <div class="content">
        ${rows || `<div class="empty-inline">${escapeHtml(summary)}</div>`}
      </div>
    `;
  }

  _renderToggleRow(label, subtitle, entityId, state) {
    const on = state?.state === "on";
    const unavailable = !state || isUnavailable(state.state);
    const entityIcon = haIcon(state?.attributes?.icon);
    return `
      <div class="toggle-row">
        <div class="toggle-main">
          ${entityIcon ? `<div class="entity-icon entity-state-icon ${on ? "is-on" : "is-off"}">${entityIcon}</div>` : ""}
          <div><div class="toggle-label">${escapeHtml(label)}</div><div class="toggle-sub">${escapeHtml(subtitle || (on ? this._text("on") : this._text("off")))}</div></div>
        </div>
        ${this._renderSwitchControl("toggle-switch", entityId, label, on, unavailable)}
      </div>
    `;
  }

  _timeValue(bundle, key) {
    const state = this._state(bundle, key);
    if (!state || isUnavailable(state.state)) return "—";
    const match = String(state.state).match(/\b\d{1,2}:\d{2}/);
    return match ? match[0] : String(state.state);
  }

  _renderWateringPanel(bundle) {
    const t = (key) => this._text(key);
    const status = this._state(bundle, "watering_status");
    const zones = this._wateringZones(bundle);
    const activeCountState = this._state(bundle, "watering_active_count");
    const activeCount = this._displayState(activeCountState, String(zones.length));
    const zoneSelect = this._state(bundle, "watering_zone");
    const executeId = bundle.ids.watering_execute;
    const options = Array.isArray(zoneSelect?.attributes?.options)
      ? zoneSelect.attributes.options
      : [];
    const selected = zoneSelect?.state || "";
    const stopOption = options[0] || "";
    const statusText = String(status?.state || "").toLowerCase();
    const wateringNow =
      statusText.startsWith("полив:") || statusText.startsWith("watering:");
    const canExecute = Boolean(
      executeId && (wateringNow || (selected && selected !== stopOption))
    );

    const zoneRows = zones
      .map((zone) => {
        const morning = `${zone.morning_mode || "—"} (${zone.morning_duration ?? "—"} ${languageFor(this._hass) === "ru" ? "с" : "s"})`;
        const evening = `${zone.evening_mode || "—"} (${zone.evening_duration ?? "—"} ${languageFor(this._hass) === "ru" ? "с" : "s"})`;
        const summary = zone.summary || `${t("morning")}: ${morning} · ${t("evening")}: ${evening}`;
        const name = zone.name || (zone.entity_id ? this._entityName(zone.entity_id) : "");
        const entityId = zone.entity_id || "";
        return `
          <div class="zone-row ${entityId ? "clickable" : ""}" ${entityId ? `data-more-info="${escapeHtml(entityId)}"` : ""}>
            <div class="entity-name">${escapeHtml(name)}</div>
            <div class="zone-info">${escapeHtml(summary)}</div>
          </div>
        `;
      })
      .join("");

    const selectorHtml = zoneSelect
      ? `
        <div class="section-label"><span>${escapeHtml(t("manualWatering"))}</span></div>
        <div class="watering-select-row">
          <select class="watering-select" data-action="watering-zone" data-entity="${escapeHtml(bundle.ids.watering_zone)}" aria-label="${escapeHtml(t("wateringZone"))}">
            ${options
              .map((option) => `<option value="${escapeHtml(option)}" ${option === selected ? "selected" : ""}>${escapeHtml(option)}</option>`)
              .join("")}
          </select>
          <button class="execute-btn" data-action="watering-execute" data-entity="${escapeHtml(executeId)}" ${!canExecute ? "disabled" : ""}>${icon(wateringNow ? "pause" : "play")}<span>${escapeHtml(t(wateringNow ? "stopWatering" : "runWatering"))}</span></button>
        </div>
      `
      : "";

    return `
      <div class="subbar"><span><strong>${escapeHtml(t("wateringSchedule"))}</strong></span><span>${escapeHtml(activeCount)} ${escapeHtml(t("zones"))} · ${escapeHtml(this._displayState(status, t("unavailable")))}</span></div>
      <div class="content">
        ${bundle.ids.watering_enabled ? this._renderToggleRow(t("autoWatering"), this._displayState(status, ""), bundle.ids.watering_enabled, this._state(bundle, "watering_enabled")) : ""}
        ${bundle.ids.watering_skip_next ? this._renderToggleRow(t("skipNext"), "", bundle.ids.watering_skip_next, this._state(bundle, "watering_skip_next")) : ""}
        <div class="schedule-grid">
          <div class="schedule-tile"><div class="schedule-title">${escapeHtml(t("morning"))}</div><div class="schedule-value">${escapeHtml(this._timeValue(bundle, "watering_morning_time"))}</div></div>
          <div class="schedule-tile"><div class="schedule-title">${escapeHtml(t("evening"))}</div><div class="schedule-value">${escapeHtml(this._timeValue(bundle, "watering_evening_time"))}</div></div>
        </div>
        <div class="section-label"><span>${escapeHtml(t("wateringSchedule"))}</span><span>${zones.length} ${escapeHtml(t("zones"))}</span></div>
        <div class="entity-list">${zoneRows || `<div class="empty-inline">${escapeHtml(t("noZones"))}</div>`}</div>
        ${selectorHtml}
      </div>
    `;
  }

  _bindEvents(bundle) {
    const root = this.shadowRoot;
    if (!root) return;

    root.querySelectorAll("[data-action='switch-tab']").forEach((button) => {
      button.addEventListener("click", () => {
        this._userSwitchedTab = true;
        this._activeTab = button.getAttribute("data-tab") || "blinds";
        this._lastRenderSig = "";
        this._render();
      });
    });

    root.querySelectorAll("[data-action='cover-service']").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entityId = button.getAttribute("data-entity");
        const service = button.getAttribute("data-service");
        if (entityId && service) this._callService("cover", service, { entity_id: entityId });
      });
    });

    root.querySelectorAll("[data-action='set-position']").forEach((slider) => {
      slider.addEventListener("change", () => {
        const entityId = slider.getAttribute("data-entity");
        const position = Number(slider.value);
        if (entityId && Number.isFinite(position)) {
          this._callService("cover", "set_cover_position", {
            entity_id: entityId,
            position,
          });
        }
      });
    });

    root.querySelectorAll("[data-action='toggle-light'], [data-action='toggle-switch']").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entityId = button.getAttribute("data-entity");
        const state = this._hass?.states?.[entityId];
        if (!entityId || !state || isUnavailable(state.state)) return;
        const domain = entityId.split(".")[0];
        if (!["light", "switch"].includes(domain)) return;
        const service = state.state === "on" ? "turn_off" : "turn_on";
        this._callService(domain, service, { entity_id: entityId });
      });
    });

    root.querySelectorAll("[data-action='watering-zone']").forEach((select) => {
      select.addEventListener("change", () => {
        const entityId = select.getAttribute("data-entity");
        if (entityId && select.value) {
          this._callService("select", "select_option", {
            entity_id: entityId,
            option: select.value,
          });
        }
      });
    });

    root.querySelectorAll("[data-action='watering-execute']").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entityId = button.getAttribute("data-entity");
        if (entityId) this._callService("button", "press", { entity_id: entityId });
      });
    });

    root.querySelectorAll(".drive-checkbox-cell").forEach((cell) => {
      cell.addEventListener("click", (event) => event.stopPropagation());
    });
    root.querySelectorAll("[data-action='drive-sun-toggle'], [data-action='drive-work-toggle']").forEach((input) => {
      input.addEventListener("click", (event) => event.stopPropagation());
      input.addEventListener("change", () => {
        const entityId = input.getAttribute("data-entity");
        const option = input.getAttribute("data-option");
        if (entityId && option && !input.disabled) {
          this._callService("select", "select_option", { entity_id: entityId, option });
        }
      });
    });

    root.querySelectorAll("[data-more-info]").forEach((element) => {
      element.addEventListener("click", (event) => {
        if (event.target?.closest?.("[data-action]")) return;
        const entityId = element.getAttribute("data-more-info");
        if (!entityId) return;
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId },
            bubbles: true,
            composed: true,
          })
        );
      });
    });
  }

  _callService(domain, service, data) {
    if (!this._hass?.callService) return;
    try {
      const result = this._hass.callService(domain, service, data);
      if (result?.catch) {
        result.catch((error) => console.error(`Orry card: ${domain}.${service} failed`, error));
      }
    } catch (error) {
      console.error(`Orry card: ${domain}.${service} failed`, error);
    }
  }
}

function registerOrryCard() {
  const registry =
    typeof window !== "undefined" && window.customElements
      ? window.customElements
      : typeof customElements !== "undefined"
        ? customElements
        : null;
  if (!registry) return false;

  // Home Assistant 2026.9+ can swap in a scoped registry after app-shell modules load.
  if (typeof document !== "undefined" && !registry.get("home-assistant")) return false;
  if (registry.get(CARD_TYPE)) return true;

  try {
    registry.define(CARD_TYPE, OrryCard);
  } catch (error) {
    if (registry.get(CARD_TYPE)) return true;
    try {
      const ScopedOrryCard = class extends OrryCard {};
      registry.define(CARD_TYPE, ScopedOrryCard);
    } catch (fallbackError) {
      console.error("Unable to register custom:orry-card", error, fallbackError);
      return false;
    }
  }
  return true;
}

if (!registerOrryCard() && typeof window !== "undefined") {
  let attempts = 0;
  const timer = window.setInterval(() => {
    attempts += 1;
    if (registerOrryCard() || attempts >= 600) window.clearInterval(timer);
  }, 50);
}

if (typeof window !== "undefined") {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((item) => item.type === CARD_TYPE)) {
    window.customCards.push({
      type: CARD_TYPE,
      name: "Домашняя оранжерея — Полная карточка",
      description: "Сводка штор, подсветки и полива с вкладками и управлением.",
      preview: true,
      documentationURL: "https://github.com/S0ft0r/ha-orangeai",
    });
  }
}
