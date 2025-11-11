export function formatLATime(iso) {
    if (!iso) return "TBA";
    const d = new Date(iso); // API returns UTC; we'll *display* LA wall-clock
    return new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Los_Angeles",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  }
  
  // returns an ISO string for (event start - 60 min) in UTC, but we display LA time
  export function oneHourBeforeISO(iso) {
    if (!iso) return null;
    const d = new Date(iso);           // UTC instant
    d.setUTCMinutes(d.getUTCMinutes() - 60);
    return d.toISOString();
  }
  