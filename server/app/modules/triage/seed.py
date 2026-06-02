from sqlmodel import Session, select, func
from app.modules.triage.model import TriageRule, TriageField, TriageOperator


def seed_triage_rules(session: Session) -> list[TriageRule]:
    count = session.exec(select(func.count()).select_from(TriageRule)).one()
    if count > 0:
        return []

    rules = [
        TriageRule(
            name="ACV",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="ACV",
            weight=20,
        ),
        TriageRule(
            name="Politraumatismo",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="politrauma",
            weight=18,
        ),
        TriageRule(
            name="Hemorragia",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="hemorragia",
            weight=12,
        ),
        TriageRule(
            name="Fractura",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="fractura",
            weight=9,
        ),
        TriageRule(
            name="Tomografía (CT)",
            field=TriageField.MODALITY,
            operator=TriageOperator.EQUALS,
            value="CT",
            weight=6,
        ),
        TriageRule(
            name="Resonancia (MR)",
            field=TriageField.MODALITY,
            operator=TriageOperator.EQUALS,
            value="MR",
            weight=5,
        ),
        TriageRule(
            name="Ecografía (US)",
            field=TriageField.MODALITY,
            operator=TriageOperator.EQUALS,
            value="US",
            weight=2,
        ),
        TriageRule(
            name="Radiografía (DX)",
            field=TriageField.MODALITY,
            operator=TriageOperator.EQUALS,
            value="DX",
            weight=1,
        ),
        TriageRule(
            name="Ubicación en UTI",
            field=TriageField.PATIENT_LOCATION,
            operator=TriageOperator.CONTAINS,
            value="UTI",
            weight=6,
        ),
        TriageRule(
            name="Servicio: Guardia",
            field=TriageField.ORIGIN_SERVICE,
            operator=TriageOperator.CONTAINS,
            value="guardia",
            weight=4,
        ),
        TriageRule(
            name="Servicio: Internación",
            field=TriageField.ORIGIN_SERVICE,
            operator=TriageOperator.CONTAINS,
            value="internacion",
            weight=4,
        ),
        TriageRule(
            name="Servicio: Ambulatorio",
            field=TriageField.ORIGIN_SERVICE,
            operator=TriageOperator.CONTAINS,
            value="ambulatorio",
            weight=-50,
        ),
        TriageRule(
            name="Urgente desde origen",
            field=TriageField.IS_URGENT,
            operator=TriageOperator.EQUALS,
            value="True",
            weight=4,
        ),
    ]

    session.add_all(rules)
    session.flush()
    for r in rules:
        session.refresh(r)
    return rules
