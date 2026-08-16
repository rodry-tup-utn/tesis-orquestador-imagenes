import { http } from "../../../services/http";
import type { TriageRule, TriageRulePayload } from "../types/triageRule.types";

export async function getTriageRules(): Promise<TriageRule[]> {
  const { data } = await http.get<TriageRule[]>("/triage-rules");
  return data;
}

export async function createTriageRule(
  payload: TriageRulePayload
): Promise<TriageRule> {
  const { data } = await http.post<TriageRule>("/triage-rules", payload);
  return data;
}

export async function updateTriageRule(
  ruleId: number,
  payload: TriageRulePayload
): Promise<TriageRule> {
  const { data } = await http.patch<TriageRule>(`/triage-rules/${ruleId}`, payload);
  return data;
}

export async function deleteTriageRule(ruleId: number): Promise<void> {
  await http.delete(`/triage-rules/${ruleId}`);
}
