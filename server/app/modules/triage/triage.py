from enum import Enum
from app.modules.medical_order.model import MedicalOrder, MedicalPriority
from app.modules.triage.model import TriageRule, TriageOperator
from app.modules.systemsettings.model import SystemSettings


class TriageEngine:

    @staticmethod
    def _to_text(value) -> str:
        return value.value if isinstance(value, Enum) else str(value)

    @staticmethod
    def evaluate(
        order: MedicalOrder,
        rules: list[TriageRule],
        settings: SystemSettings,
    ) -> tuple[MedicalPriority, dict]:
        score = 0
        criterios = {"rules_matched": [], "total_score": 0}
        for rule in rules:
            if not rule.enabled:
                continue
            field_value = getattr(order, rule.field, None)
            if field_value is None:
                continue
            text_value = TriageEngine._to_text(field_value)
            if TriageEngine._matches(text_value, rule.operator, rule.value):
                score += rule.weight
                criterios["rules_matched"].append({
                    "field": rule.field,
                    "value_matched": text_value,
                    "operator": rule.operator,
                    "pattern": rule.value,
                    "weight": rule.weight
                })

        criterios["total_score"] = score
        return TriageEngine._map_priority(score, settings), criterios

    @staticmethod
    def _matches(field_value: str, operator: TriageOperator, pattern: str) -> bool:
        match operator:
            case TriageOperator.EQUALS:
                return field_value.lower() == pattern.lower()
            case TriageOperator.CONTAINS:
                return pattern.lower() in field_value.lower()
            case TriageOperator.STARTSWITH:
                return field_value.lower().startswith(pattern.lower())

    @staticmethod
    def _map_priority(score: int, settings: SystemSettings) -> MedicalPriority:
        if score >= settings.triage_critical_threshold:
            return MedicalPriority.CRITICAL
        if score >= settings.triage_urgent_threshold:
            return MedicalPriority.URGENT
        if score >= settings.triage_priority_threshold:
            return MedicalPriority.PRIORITY
        return MedicalPriority.ROUTINE
