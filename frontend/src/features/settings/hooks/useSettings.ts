import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import type { ApiError } from "../../../services/http";
import { getSettings, updateSettings } from "../services/settings.service";
import type { SystemSettingsUpdate } from "../types/settings.types";

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: getSettings,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, SystemSettingsUpdate>({
    mutationFn: updateSettings,
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: queryKeys.settings }),
  });
}
