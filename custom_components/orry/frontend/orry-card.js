/*
 * Full Lovelace card for the Orry Home Orangery integration.
 * The layout follows the header + KPI tiles + tabbed content pattern of dnevnik2-card.
 */

const CARD_TYPE = "orry-card";
const CARD_VERSION = "0.1.26.1";
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
    averageActiveBlinds: "Среднее положение активных штор",
    activeBlinds: "Активных штор",
    setBlindPosition: "Установить положение активных штор",
    totalDevices: "Всего устройств",
    enabledDevices: "Включено",
    configuredZones: "Настроено направлений",
    activeZones: "активно",
    turnLightingOn: "Включить подсветку",
    turnLightingOff: "Выключить подсветку",
    lightingOn: "Включена",
    lightingOff: "Выключена",
    lightingUnavailable: "Нет данных о светильниках",
    scheduled: "По расписанию",
    drivePositions: "Положение приводов",
    updatedNow: "Текущее состояние",
    sunProtection: "Защита от солнца",
    driveEnabled: "Привод включён в работу",
    errors: "Ошибок",
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
    averageActiveBlinds: "Average active blinds position",
    activeBlinds: "Active blinds",
    setBlindPosition: "Set active blinds position",
    totalDevices: "Total devices",
    enabledDevices: "On",
    configuredZones: "Configured zones",
    activeZones: "active",
    turnLightingOn: "Turn lighting on",
    turnLightingOff: "Turn lighting off",
    lightingOn: "On",
    lightingOff: "Off",
    lightingUnavailable: "No light data available",
    scheduled: "Scheduled",
    drivePositions: "Drive positions",
    updatedNow: "Current state",
    sunProtection: "Sun protection",
    driveEnabled: "Drive enabled for operation",
    errors: "Errors",
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
    "<path d='M3.5 20.5h17M5.5 20.5V9l6.5-5 6.5 5v11.5M9 20.5v-6h6v6M8 10.5h.01M12 10.5h.01M16 10.5h.01'/><path d='M12 8.5c-1.7-2.1-4.3-1.4-4.3.5 0 1.7 2.2 2.2 4.3 3.8 2.1-1.6 4.3-2.1 4.3-3.8 0-1.9-2.6-2.6-4.3-.5Z'/>",
  next: "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
  light:
    "<path d='M9 18h6M10 22h4M8.5 14.5a6 6 0 1 1 7 0c-.8.6-1.3 1.4-1.4 2.5h-4.2c-.1-1.1-.6-1.9-1.4-2.5Z'/><path d='M12 2v2M4.9 4.9l1.4 1.4M19.1 4.9l-1.4 1.4'/>",
  water:
    "<path d='M12 3C9 7.3 6 10.3 6 14a6 6 0 0 0 12 0c0-3.7-3-6.7-6-11Z'/><path d='M9.5 15.5a2.5 2.5 0 0 0 2.5 2.5'/>",
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
    gap: 10px;
    padding: 14px 16px 10px;
  }
  .header-left { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1 1 auto; }
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
  .header-titles { min-width: 0; flex: 1 1 auto; }
  .header-title {
    overflow: hidden;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.25;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .header-subtitle {
    min-width: 0;
    margin-top: 2px;
    overflow: hidden;
    color: var(--secondary-text-color);
    font-size: 12px;
    white-space: nowrap;
  }
  .header-subtitle-track { display: inline-flex; align-items: center; width: max-content; white-space: nowrap; }
  .header-subtitle-copy { display: inline-block; flex: 0 0 auto; white-space: nowrap; }
  .header-subtitle-clone { display: none; }
  .header-subtitle.is-scrolling .header-subtitle-clone { display: inline-block; }
  .header-subtitle.is-scrolling .header-subtitle-track {
    gap: 28px;
    animation: subtitle-marquee var(--subtitle-duration, 12s) linear infinite;
    will-change: transform;
  }
  .header-subtitle.is-scrolling:hover .header-subtitle-track,
  .header-subtitle.is-scrolling:focus-within .header-subtitle-track { animation-play-state: paused; }
  @keyframes subtitle-marquee { to { transform: translateX(var(--subtitle-distance, -280px)); } }
  @media (prefers-reduced-motion: reduce) {
    .header-subtitle.is-scrolling .header-subtitle-track { animation: none; will-change: auto; }
    .header-subtitle.is-scrolling .header-subtitle-clone { display: none; }
  }
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
  .kpi-main { min-height: 22px; display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; }
  .kpi-sub { overflow: hidden; color: var(--secondary-text-color); font-size: 10px; white-space: nowrap; text-overflow: ellipsis; }
  .kpi-main.blinds-kpi-main { display: block; min-height: 20px; overflow: visible; }
  .device-count-pill {
    min-height: 20px;
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 3px 8px;
    border: 1px solid rgba(3, 169, 244, .23);
    border-radius: 999px;
    color: var(--primary-color, #147aa5);
    background: rgba(3, 169, 244, .09);
    font-size: 10px;
    line-height: 1;
    font-weight: 700;
    white-space: nowrap;
  }
  .blinds-summary-range {
    position: relative;
    width: 100%;
    height: 4px;
    margin: 7px 2px;
    border-radius: 999px;
    background: var(--orry-chip-bg);
  }
  .blinds-range-fill { width: 50%; height: 100%; border-radius: inherit; background: var(--primary-color, #03a9f4); }
  .blinds-range-thumb {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 14px;
    height: 14px;
    border: 2px solid var(--ha-card-background, var(--card-background-color, #fff));
    border-radius: 50%;
    background: var(--primary-color, #03a9f4);
    box-shadow: 0 1px 3px rgba(0,0,0,.25);
    transform: translate(-50%, -50%);
    pointer-events: none;
  }
  .blinds-summary-range-input {
    position: absolute;
    z-index: 2;
    top: 50%;
    left: -10px;
    width: calc(100% + 20px);
    height: 20px;
    margin: 0;
    padding: 0;
    transform: translateY(-50%);
    opacity: 0;
    border: 0;
    background: transparent;
    -webkit-appearance: none;
    appearance: none;
    cursor: pointer;
  }
  .blinds-summary-range-input::-webkit-slider-runnable-track { height: 20px; background: transparent; }
  .blinds-summary-range-input::-webkit-slider-thumb { width: 20px; height: 20px; margin: 0; border: 0; border-radius: 50%; background: transparent; box-shadow: none; -webkit-appearance: none; }
  .blinds-summary-range-input::-moz-range-track { height: 20px; border: 0; background: transparent; }
  .blinds-summary-range-input::-moz-range-thumb { width: 20px; height: 20px; border: 0; border-radius: 50%; background: transparent; box-shadow: none; }
  .blinds-summary-range:focus-within .blinds-range-thumb { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; }
  .blinds-summary-range-input:disabled { cursor: default; }
  .kpi-footer { min-width: 0; width: 100%; }
  .kpi-next-event {
    min-width: 0;
    width: 100%;
    display: block;
    overflow: hidden;
    color: var(--secondary-text-color);
    font-size: 10px;
    line-height: 1.25;
    white-space: nowrap;
  }
  .kpi-next-event-track { width: 100%; display: block; overflow: hidden; white-space: nowrap; }
  .kpi-next-event-copy { width: 100%; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .kpi-next-event-clone { display: none; }
  .kpi-next-event.is-scrolling .kpi-next-event-track {
    width: max-content;
    display: inline-flex;
    align-items: center;
    gap: 28px;
    overflow: visible;
    animation: event-marquee var(--event-duration, 12s) linear infinite;
    will-change: transform;
  }
  .kpi-next-event.is-scrolling .kpi-next-event-copy { width: auto; flex: 0 0 auto; display: inline-block; overflow: visible; text-overflow: clip; }
  .kpi-next-event.is-scrolling .kpi-next-event-clone { display: inline-block; }
  .kpi-next-event.is-scrolling:hover .kpi-next-event-track,
  .kpi-next-event.is-scrolling:focus-within .kpi-next-event-track { animation-play-state: paused; }
  @keyframes event-marquee { to { transform: translateX(var(--event-distance, -280px)); } }
  @media (prefers-reduced-motion: reduce) {
    .kpi-next-event.is-scrolling .kpi-next-event-track { width: 100%; display: block; animation: none; will-change: auto; }
    .kpi-next-event.is-scrolling .kpi-next-event-copy { width: 100%; display: block; overflow: hidden; text-overflow: ellipsis; }
    .kpi-next-event.is-scrolling .kpi-next-event-clone { display: none; }
  }
  .lighting-kpi-main, .watering-kpi-main { justify-content: flex-start; gap: 8px; }
  .lighting-kpi-button, .watering-kpi-button {
    width: 22px;
    height: 22px;
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    padding: 0;
    border: 0;
    border-radius: 50%;
    background: transparent;
    color: var(--state-icon-color, var(--secondary-text-color));
    cursor: pointer;
  }
  .lighting-kpi-button.is-on { color: var(--state-active-color, #fdd835); }
  .watering-kpi-button.is-on { color: var(--primary-color, #03a9f4); }
  .lighting-kpi-button:hover, .watering-kpi-button:hover { background: var(--orry-row-hover); }
  .lighting-kpi-button:focus-visible, .watering-kpi-button:focus-visible { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 1px; }
  .lighting-kpi-button ha-icon, .watering-kpi-button ha-icon { width: 17px; height: 17px; --mdc-icon-size: 17px; }
  .lighting-kpi-button:disabled, .watering-kpi-button:disabled { cursor: default; opacity: .45; }

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
  .tab-btn svg, .tab-btn ha-icon { width: 16px; height: 16px; flex: 0 0 16px; --mdc-icon-size: 16px; }
  .tab-btn.active {
    border-bottom-color: var(--primary-color, #03a9f4);
    background: rgba(3, 169, 244, 0.06);
    color: var(--primary-color, #03a9f4);
  }
  ha-card.summary-mode .kpi-grid { grid-template-columns: repeat(var(--module-count, 3), minmax(0, 1fr)); }
  ha-card.summary-mode .tabs-bar, ha-card.summary-mode .panel { display: none; }

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
  .toggle:disabled, .switch-icon-button:disabled, .watering-select:disabled { cursor: default; opacity: .45; }
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
  .sun-column-icon { color: var(--secondary-text-color); }
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
  .drive-row-icon.entity-icon {
    width: 28px;
    height: 28px;
    border-radius: 0;
    background: transparent;
    color: var(--primary-color, #03a9f4);
  }
  .drive-main { min-width: 0; }
  .drive-main-top { min-width: 0; display: flex; align-items: center; gap: 7px; }
  .drive-main-top .entity-name { min-width: 0; flex: 1; }
  .drive-position { flex: 0 0 auto; color: var(--primary-color, #03a9f4); font-size: 11px; font-weight: 700; white-space: nowrap; }
  .drive-main .mini-track { margin-top: 4px; }
  .drive-checkbox-cell { min-height: 30px; position: relative; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  .drive-checkbox {
    position: absolute;
    z-index: 2;
    inset: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    opacity: 0;
    cursor: pointer;
  }
  .drive-checkbox-visual { width: 19px; height: 19px; display: flex; align-items: center; justify-content: center; color: var(--state-icon-color, var(--secondary-text-color)); pointer-events: none; }
  .drive-checkbox:checked + .drive-checkbox-visual { color: var(--state-active-color, var(--primary-color, #03a9f4)); }
  .drive-checkbox-visual ha-icon { width: 19px; height: 19px; --mdc-icon-size: 19px; }
  .drive-checkbox-visual .checkbox-marked { display: none; }
  .drive-checkbox:checked + .drive-checkbox-visual .checkbox-empty { display: none; }
  .drive-checkbox:checked + .drive-checkbox-visual .checkbox-marked { display: inline-flex; }
  .drive-checkbox:focus-visible + .drive-checkbox-visual { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; border-radius: 3px; }
  .drive-checkbox:disabled { cursor: default; }
  .drive-checkbox:disabled + .drive-checkbox-visual { opacity: .55; }
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
    .kpi-grid.module-count-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .kpi-grid.module-count-3 .kpi-tile:last-child { grid-column: auto; }
    .kpi-tile { padding: 7px 6px; }
    .kpi-top { gap: 3px; font-size: 9px; }
    .kpi-top .device-count-pill { min-height: 18px; padding: 2px 4px; font-size: 8px; }
    .kpi-main { font-size: 12px; }
    .kpi-sub { font-size: 9px; }
    .device-count-pill { padding: 2px 4px; font-size: 8px; }
    .kpi-next-event { font-size: 9px; }
    .content { padding-left: 12px; padding-right: 12px; }
    .subbar { padding-left: 12px; padding-right: 12px; }
    .tab-btn { gap: 4px; padding-left: 3px; padding-right: 3px; font-size: 11px; }
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
    this._marqueeObserver = null;
  }

  disconnectedCallback() {
    this._marqueeObserver?.disconnect();
    this._marqueeObserver = null;
  }

  static getStubConfig(hass) {
    return {
      mode: "full",
      entity: findDefaultAnchor(hass),
      default_tab: "blinds",
      drive_indicator: "position",
      show_position_percent: true,
      scroll_text: false,
    };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "mode",
          default: "full",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "full", label: "Полная" },
                { value: "summary", label: "Краткая" },
              ],
            },
          },
        },
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
        {
          name: "scroll_text",
          default: false,
          selector: { boolean: {} },
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "mode":
            return "Режим карточки";
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
          case "scroll_text":
            return "Прокручивать длинные события";
          default:
            return schema.name;
        }
      },
      computeHelper: (schema) => {
        if (schema.name === "mode") {
          return "Полная — вкладки и подробное управление; краткая — те же сводные плитки без вкладок.";
        }
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
        if (schema.name === "scroll_text") {
          return "Если включено, длинные события в мини-карточках будут прокручиваться вместо обрезания.";
        }
        return undefined;
      },
    };
  }

  setConfig(config) {
    if (!config) throw new Error("A card configuration is required");
    this._config = {
      mode: "full",
      default_tab: "blinds",
      show_position_percent: true,
      scroll_text: false,
      ...config,
    };
    this._config.mode = this._config.mode === "summary" ? "summary" : "full";
    this._config.scroll_text = this._config.scroll_text === true;
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
    return this._config?.mode === "summary" ? 4 : 8;
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
      modules.push({ key: "blinds", title: this._text("moduleBlinds") });
    }

    const phytolampState = this._state(bundle, "phytolamp_status");
    if (
      this._lights(bundle).length > 0 ||
      (phytolampState && !isNotConfigured(phytolampState.state))
    ) {
      modules.push({ key: "phytolamp", title: this._text("moduleLighting") });
    }

    const wateringState = this._state(bundle, "watering_status");
    if (
      bundle.ids.watering_enabled ||
      bundle.ids.watering_skip_next ||
      bundle.ids.watering_execute ||
      (wateringState && !isNotConfigured(wateringState.state))
    ) {
      modules.push({ key: "watering", title: this._text("moduleWatering") });
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

  _blindSelectOption(selectState, entityId, name, isSelected) {
    const attrs = selectState?.attributes || {};
    const direct = attrs.option_by_blind?.[entityId];
    if (typeof direct === "string" && direct) return direct;
    const options = Array.isArray(attrs.options) ? attrs.options.map(String) : [];
    if (!options.length) return "";

    const marker = isSelected ? "\u2713\ufe0e\u00a0\u00a0" : "\u2715\ufe0e\u00a0\u00a0";
    const matches = options.filter((option) =>
      option.includes(entityId) || (name && option.includes(name))
    );
    return matches.find((option) => option.startsWith(marker)) || matches[0] || "";
  }

  _syncTextMarquees() {
    this._marqueeObserver?.disconnect();
    this._marqueeObserver = null;
    const subtitle = this.shadowRoot?.querySelector(".header-subtitle");
    const eventLines = [...(this.shadowRoot?.querySelectorAll(".kpi-next-event") || [])];
    const elements = [subtitle, ...eventLines].filter(Boolean);
    if (!elements.length) return;

    const update = () => {
      for (const element of elements) {
        if (!element.isConnected) continue;
        const isSubtitle = element === subtitle;
        const copy = element.querySelector(
          isSubtitle ? ".header-subtitle-copy" : ".kpi-next-event-copy:not(.kpi-next-event-clone)"
        );
        const clone = element.querySelector(
          isSubtitle ? ".header-subtitle-clone" : ".kpi-next-event-clone"
        );
        const text = copy?.textContent || "";
        element.title = text;
        element.setAttribute("aria-label", text);
        const textWidth = isSubtitle
          ? copy?.getBoundingClientRect().width || 0
          : copy?.scrollWidth || 0;
        const shouldScroll =
          textWidth > element.clientWidth + 1 &&
          (isSubtitle || this._config.scroll_text === true);
        element.classList.toggle("is-scrolling", shouldScroll);
        if (!shouldScroll) {
          if (clone) clone.textContent = "";
          element.style.removeProperty(isSubtitle ? "--subtitle-distance" : "--event-distance");
          element.style.removeProperty(isSubtitle ? "--subtitle-duration" : "--event-duration");
          continue;
        }

        const distance = textWidth + 28;
        if (clone) clone.textContent = text;
        element.style.setProperty(
          isSubtitle ? "--subtitle-distance" : "--event-distance",
          `${-distance}px`
        );
        element.style.setProperty(
          isSubtitle ? "--subtitle-duration" : "--event-duration",
          `${Math.max(8, distance / 30)}s`
        );
      }
    };

    if (typeof ResizeObserver !== "undefined") {
      this._marqueeObserver = new ResizeObserver(update);
      elements.forEach((element) => this._marqueeObserver.observe(element));
    }
    const schedule = typeof requestAnimationFrame === "function"
      ? requestAnimationFrame
      : (callback) => setTimeout(callback, 0);
    schedule(update);
  }

  _blindAveragePosition(bundle) {
    const positions = [...new Set(this._activeBlindIds(bundle))]
      .map((entityId) => this._position(this._hass?.states?.[entityId]))
      .filter((position) => position !== null);
    if (positions.length) {
      return Math.round(positions.reduce((sum, position) => sum + position, 0) / positions.length);
    }
    return this._position(this._state(bundle, "blinds"));
  }

  _render() {
    if (!this.shadowRoot) return;
    this._marqueeObserver?.disconnect();
    this._marqueeObserver = null;
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

    const mode = this._config?.mode === "summary" ? "summary" : "full";
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
    const nextState = this._state(bundle, "next_action");
    const lastAction = nextState?.attributes?.last_action;
    const subtitle =
      typeof lastAction === "string" && lastAction.trim()
        ? lastAction.trim()
        : modules.map((module) => module.title).join(" · ");
    const detailedPanels = mode === "full"
      ? `
        <div class="tabs-bar" style="--module-count:${modules.length}">
          ${modules.map((module) => this._renderTab(module)).join("")}
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
      `
      : "";

    this.shadowRoot.innerHTML = `
      <style>${CARD_STYLES}</style>
      <ha-card class="${mode === "summary" ? "summary-mode" : "full-mode"}">
        <div class="header">
          <div class="header-left">
            <div class="header-icon">${icon("greenhouse")}</div>
            <div class="header-titles">
              <div class="header-title">${escapeHtml(title)}</div>
              <div class="header-subtitle" title="${escapeHtml(subtitle)}" aria-label="${escapeHtml(subtitle)}">
                <span class="header-subtitle-track">
                  <span class="header-subtitle-copy">${escapeHtml(subtitle || t("subtitle"))}</span>
                  <span class="header-subtitle-copy header-subtitle-clone" aria-hidden="true"></span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="kpi-grid module-count-${modules.length}" style="--module-count:${modules.length}">
          ${modules.map((module) => this._renderKpi(module, bundle)).join("")}
        </div>

        ${detailedPanels}
      </ha-card>
    `;
    this._bindEvents(bundle);
    this._syncTextMarquees();
  }

  _renderKpiEvent(text) {
    const safeText = escapeHtml(text);
    return `
      <div class="kpi-footer">
        <div class="kpi-next-event" title="${safeText}" aria-label="${safeText}">
          <span class="kpi-next-event-track">
            <span class="kpi-next-event-copy">${safeText}</span>
            <span class="kpi-next-event-copy kpi-next-event-clone" aria-hidden="true"></span>
          </span>
        </div>
      </div>
    `;
  }

  _renderKpi(module, bundle) {
    const t = (key) => this._text(key);
    const entityId = bundle.ids[module.key === "blinds" ? "blinds" : `${module.key}_status`] || "";
    const infoEntityId = entityId || bundle.anchorId;
    const nextAttributes = this._state(bundle, "next_action")?.attributes || {};
    const eventFor = (attribute) => {
      const value = nextAttributes[attribute];
      return typeof value === "string" && value.trim() ? value.trim() : t("noActions");
    };

    if (module.key === "blinds") {
      const cover = this._state(bundle, "blinds");
      const coverId = bundle.ids.blinds || "";
      const activeIds = [...new Set(this._activeBlindIds(bundle))];
      const allCount = this._allBlindIds(bundle).length;
      const activeCount = activeIds.length;
      const position = this._blindAveragePosition(bundle);
      const errors = this._displayState(this._state(bundle, "error_count"), "0");
      const positionText = position === null ? "—" : `${position}%`;
      const positionLabel = `${t("averageActiveBlinds")}: ${positionText}`;
      const totalLabel = `${t("totalDevices")}: ${allCount}`;
      const activeLabel = `${t("activeBlinds")}: ${activeCount}`;
      const errorLabel = `${t("errors")}: ${errors}`;
      const accessibleCounts = languageFor(this._hass) === "en"
        ? `${allCount} devices, ${activeCount} active blinds, ${errors} errors`
        : `${allCount} устройств, ${activeCount} активных штор, ${errors} ошибок`;
      const coverAvailable = Boolean(
        coverId && cover && !isUnavailable(cover.state) && activeCount > 0 && position !== null
      );
      const value = position === null ? 0 : position;
      return `
        <div class="kpi-tile clickable" data-more-info="${escapeHtml(infoEntityId)}">
          <div class="kpi-top">
            <span>${escapeHtml(module.title)}</span>
            <span class="device-count-pill blinds-kpi-counts" role="group" aria-label="${escapeHtml(accessibleCounts)}" title="${escapeHtml(accessibleCounts)}">
              <span title="${escapeHtml(totalLabel)}">${allCount}</span><span aria-hidden="true"> / </span>
              <span title="${escapeHtml(activeLabel)}">${activeCount}</span><span aria-hidden="true"> / </span>
              <span title="${escapeHtml(errorLabel)}">${escapeHtml(errors)}</span>
            </span>
          </div>
          <div class="kpi-main blinds-kpi-main">
            <div class="blinds-summary-range">
              <div class="blinds-range-fill" style="width:${value}%"></div>
              <div class="blinds-range-thumb" style="left:${value}%"></div>
              <input class="blinds-summary-range-input" type="range" min="0" max="100" step="1" value="${value}" data-action="set-position" data-entity="${escapeHtml(coverId)}" aria-label="${escapeHtml(t("setBlindPosition"))}" aria-valuetext="${escapeHtml(positionText)}" title="${escapeHtml(positionLabel)}" ${coverAvailable ? "" : "disabled"}>
            </div>
          </div>
          ${this._renderKpiEvent(eventFor("blind_action"))}
        </div>
      `;
    }

    if (module.key === "phytolamp") {
      const lights = this._lights(bundle);
      const onCount = lights.filter((item) => this._lightIsOn(item)).length;
      const actionableLights = lights.filter((item) => {
        const lightId = String(item?.entity_id || "");
        return lightId && ["light", "switch"].includes(lightId.split(".")[0]) && this._lightIsAvailable(item);
      });
      const anyOn = onCount > 0;
      const countLabel = `${t("totalDevices")}: ${lights.length}, ${t("enabledDevices")}: ${onCount}`;
      const buttonLabel = t(anyOn ? "turnLightingOff" : "turnLightingOn");
      const pressed = onCount === 0 ? "false" : onCount === lights.length ? "true" : "mixed";
      return `
        <div class="kpi-tile clickable" data-more-info="${escapeHtml(infoEntityId)}">
          <div class="kpi-top">
            <span>${escapeHtml(module.title)}</span>
            <span class="device-count-pill" role="img" aria-label="${escapeHtml(countLabel)}" title="${escapeHtml(countLabel)}">${lights.length} / ${onCount}</span>
          </div>
          <div class="kpi-main lighting-kpi-main">
            <button class="lighting-kpi-button ${anyOn ? "is-on" : ""}" type="button" data-action="toggle-kpi-lights" aria-label="${escapeHtml(buttonLabel)}" aria-pressed="${pressed}" title="${escapeHtml(buttonLabel)}" ${actionableLights.length ? "" : "disabled"}>${haIcon("mdi:lightbulb-outline")}</button>
          </div>
          ${this._renderKpiEvent(eventFor("light_action"))}
        </div>
      `;
    }

    const zones = this._wateringZones(bundle);
    const activeCountState = this._state(bundle, "watering_active_count");
    const activeCount = this._displayState(activeCountState, String(zones.length));
    const totalZonesRaw = activeCountState?.attributes?.total_zones;
    const parsedTotalZones = totalZonesRaw === null || totalZonesRaw === undefined || totalZonesRaw === ""
      ? Number.NaN
      : Number(totalZonesRaw);
    const totalZones = Number.isFinite(parsedTotalZones)
      ? Math.max(0, Math.trunc(parsedTotalZones))
      : zones.length;
    const countLabel = `${t("configuredZones")}: ${totalZones}, ${t("activeZones")}: ${activeCount}`;
    const wateringSwitchId = bundle.ids.watering_enabled || "";
    const wateringSwitch = this._state(bundle, "watering_enabled");
    const wateringOn = wateringSwitch?.state === "on";
    const wateringAvailable = Boolean(
      wateringSwitchId && wateringSwitch && !isUnavailable(wateringSwitch.state)
    );
    const buttonLabel = `${t("autoWatering")}: ${t(wateringOn ? "on" : "off")}`;
    return `
      <div class="kpi-tile clickable" data-more-info="${escapeHtml(infoEntityId)}">
        <div class="kpi-top">
          <span>${escapeHtml(module.title)}</span>
          <span class="device-count-pill" role="img" aria-label="${escapeHtml(countLabel)}" title="${escapeHtml(countLabel)}">${totalZones} / ${escapeHtml(activeCount)}</span>
        </div>
        <div class="kpi-main watering-kpi-main">
          <button class="watering-kpi-button ${wateringOn ? "is-on" : ""}" type="button" data-action="toggle-switch" data-entity="${escapeHtml(wateringSwitchId)}" aria-label="${escapeHtml(buttonLabel)}" aria-pressed="${wateringOn}" title="${escapeHtml(buttonLabel)}" ${wateringAvailable ? "" : "disabled"}>${haIcon("mdi:watering-can")}</button>
        </div>
        ${this._renderKpiEvent(eventFor("watering_action"))}
      </div>
    `;
  }

  _renderTab(module) {
    const icons = {
      blinds: "orry:blind-50",
      phytolamp: "orry:phytolamp",
      watering: "orry:watering",
    };
    return `
      <button class="tab-btn ${module.key === this._activeTab ? "active" : ""}" data-action="switch-tab" data-tab="${module.key}">
        ${haIcon(icons[module.key])}<span>${escapeHtml(module.title)}</span>
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
    const step = position === null
      ? 50
      : Math.max(0, Math.min(100, Math.round(position / 25) * 25));
    return haIcon(`orry:blind-${step}`);
  }

  _renderBlindsPanel(bundle) {
    const t = (key) => this._text(key);
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
        const sunChecked = sunSelected.has(entityId);
        const sunOption = sunOptions[entityId] || this._blindSelectOption(
          sunSelect, entityId, name, sunChecked
        );
        const workOption = workOptions[entityId] || this._blindSelectOption(
          workSelect, entityId, name, isWorking
        );
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
              <span class="drive-checkbox-visual" aria-hidden="true"><span class="checkbox-empty">${haIcon("mdi:checkbox-blank-outline")}</span><span class="checkbox-marked">${haIcon("mdi:checkbox-marked-outline")}</span></span>
            </label>
            <label class="drive-checkbox-cell drive-work-cell" title="${escapeHtml(t("driveEnabled"))}">
              <input class="drive-checkbox" type="checkbox" data-action="drive-work-toggle" data-entity="${escapeHtml(workSelectId)}" data-option="${escapeHtml(workOption)}" aria-label="${escapeHtml(`${name}: ${t("driveEnabled")}`)}" ${isWorking ? "checked" : ""} ${workAvailable ? "" : "disabled"}>
              <span class="drive-checkbox-visual" aria-hidden="true"><span class="checkbox-empty">${haIcon("mdi:checkbox-blank-outline")}</span><span class="checkbox-marked">${haIcon("mdi:checkbox-marked-outline")}</span></span>
            </label>
          </div>
        `;
      })
      .join("");

    return `
      <div class="content">
        <div class="drive-list">
          <div class="drive-list-heading" aria-label="${escapeHtml(t("drivePositions"))}">
            <span></span><span></span>
            <span class="drive-column-icon sun-column-icon" title="${escapeHtml(t("sunProtection"))}">${haIcon("orry:blind-sun")}</span>
            <span class="drive-column-icon work-column-icon" title="${escapeHtml(t("driveEnabled"))}">${haIcon("orry:blind-pause")}</span>
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

    root.querySelectorAll("[data-action='set-position']").forEach((slider) => {
      slider.addEventListener("input", () => {
        const position = Math.max(0, Math.min(100, Math.round(Number(slider.value) || 0)));
        const range = slider.closest(".blinds-summary-range");
        const fill = range?.querySelector(".blinds-range-fill");
        const thumb = range?.querySelector(".blinds-range-thumb");
        if (fill) fill.style.width = `${position}%`;
        if (thumb) thumb.style.left = `${position}%`;
        slider.setAttribute("aria-valuetext", `${position}%`);
      });
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

    root.querySelectorAll("[data-action='toggle-kpi-lights']").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const lights = this._lights(bundle);
        const targetOn = !lights.some((item) => this._lightIsOn(item));
        for (const item of lights) {
          const entityId = String(item?.entity_id || "");
          const domain = entityId.split(".")[0];
          if (!entityId || !["light", "switch"].includes(domain) || !this._lightIsAvailable(item)) continue;
          if (this._lightIsOn(item) === targetOn) continue;
          this._callService(domain, targetOn ? "turn_on" : "turn_off", { entity_id: entityId });
        }
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
      name: "Домашняя оранжерея — Карточка Orry",
      description: "Полный и краткий режимы; сводка штор, подсветки и полива.",
      preview: true,
      documentationURL: "https://github.com/S0ft0r/ha-orangeai",
    });
  }
}
