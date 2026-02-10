export function formatLATime(iso) {
  if (!iso) return "TBA";
  const d = new Date(iso); // API returns UTC; we'll *display* LA wall-clock
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export function formatLADate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(d);
}

export function formatLADateTime(iso) {
  if (!iso) return "TBA";
  const d = new Date(iso);
  const dateStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(d);
  const timeStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    hour: "numeric",
    minute: "2-digit",
  }).format(d);
  return `${dateStr} at ${timeStr}`;
}

// returns an ISO string for (event start - 60 min) in UTC, but we display LA time
export function oneHourBeforeISO(iso) {
  if (!iso) return null;
  const d = new Date(iso);           // UTC instant
  d.setUTCMinutes(d.getUTCMinutes() - 60);
  return d.toISOString();
}