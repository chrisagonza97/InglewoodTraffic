import { useQuery } from "@tanstack/react-query";
import { getTodayEvents, getUpcomingEvents, getWeekEvents } from "../api/events";

export function useTodayEvents() {
  return useQuery({
    queryKey: ["events", "today"],
    queryFn: getTodayEvents,
    staleTime: 60_000,
    retry: 1,
  });
}

export function useUpcomingEvents(limit = 100) {
  return useQuery({
    queryKey: ["events", "upcoming", limit],
    queryFn: () => getUpcomingEvents(limit),
    staleTime: 300_000,
    retry: 1,
  });
}

export function useWeekEvents(weekOffset = 0, limit = 200) {
  return useQuery({
    queryKey: ["events", "week", weekOffset, limit],
    queryFn: () => getWeekEvents(weekOffset, limit),
    staleTime: 120_000,
    retry: 1,
  });
}
