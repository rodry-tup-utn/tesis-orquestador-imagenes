from app.modules.medical_order.model import MedicalOrder, MedicalPriority
from app.modules.triage.model import TriageRule, TriageOperator
from app.modules.systemsettings.model import SystemSettings


class TriageEngine:

    @staticmethod
    def evaluate(
        order: MedicalOrder,
        rules: list[TriageRule],
        settings: SystemSettings,
    ) -> MedicalPriority:
        score = 0
        for rule in rules:
            if not rule.enabled:
                continue
            field_value = getattr(order, rule.field, None)
            if field_value is None:
                continue
            if TriageEngine._matches(str(field_value), rule.operator, rule.value):
                score += rule.weight

        return TriageEngine._map_priority(score, settings)

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
        if score >= settings.triage_priority_threshold:
            return MedicalPriority.PRIORITY
        return MedicalPriority.ROUTINE
