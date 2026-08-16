import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import type { ApiError } from "../../../services/http";
import {
  createTriageRule,
  deleteTriageRule,
  getTriageRules,
  updateTriageRule,
} from "../services/triageRules.service";
import type { TriageRulePayload } from "../types/triageRule.types";

export function useTriageRules() {
  return useQuery({
    queryKey: queryKeys.triageRules,
    queryFn: getTriageRules,
  });
}

export function useCreateTriageRule() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, TriageRulePayload>({
    mutationFn: createTriageRule,
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: queryKeys.triageRules }),
  });
}

export function useUpdateTriageRule() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, { id: number; payload: TriageRulePayload }>({
    mutationFn: ({ id, payload }) => updateTriageRule(id, payload),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: queryKeys.triageRules }),
  });
}

export function useDeleteTriageRule() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, number>({
    mutationFn: deleteTriageRule,
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: queryKeys.triageRules }),
  });
}
