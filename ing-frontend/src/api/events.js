import { apiGet } from "./client";

export const getTodayEvents = () => apiGet("/events/today");
export const getUpcomingEvents = (limit = 100, offset = 0) =>
  apiGet("/events/upcoming", { limit, offset });

export const getWeekEvents = (weekOffset = 0, limit = 200, skip = 0) =>
  apiGet("/events/week", { week_offset: weekOffset, limit, skip });
