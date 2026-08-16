import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import { listNotifications } from "../services/notifications.service";

export function useNotifications(offset: number, limit: number) {
  return useQuery({
    queryKey: queryKeys.notificationsList(offset, limit),
    queryFn: () => listNotifications(offset, limit),
    placeholderData: (prev) => prev,
  });
}
