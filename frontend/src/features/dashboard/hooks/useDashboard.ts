import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import { getLatestNotifications, getOrderStats } from "../services/dashboard.service";

export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: getOrderStats,
  });
}

export function useLatestNotifications(limit = 5) {
  return useQuery({
    queryKey: ["notifications", "latest", limit] as const,
    queryFn: () => getLatestNotifications(limit),
  });
}
