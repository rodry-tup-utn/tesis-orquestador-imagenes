from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.modules.triage.model import TriageRule, TriageField, TriageOperator


async def seed_triage_rules(session: AsyncSession) -> list[TriageRule]:
    statement = select(func.count()).select_from(TriageRule)
    result = await session.execute(statement)
    count = result.scalar_one()
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
            name="TEP",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="TEP",
            weight=10,
        ),
        TriageRule(
            name="Colecistitis aguda",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="colecistitis",
            weight=10,
        ),
        TriageRule(
            name="Apendicitis",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="apendicitis",
            weight=10,
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
            name="Ubicación Shock Room",
            field=TriageField.PATIENT_LOCATION,
            operator=TriageOperator.CONTAINS,
            value="Shock Room",
            weight=8,
        ),
        TriageRule(
            name="Ubicación Box Rojo",
            field=TriageField.PATIENT_LOCATION,
            operator=TriageOperator.CONTAINS,
            value="Box Rojo",
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
        # Reglas de moderación de agudeza: reducen prioridad para estudios de
        # control/seguimiento/evolución (no agudos). Peso -5 cada una.
        # Basado en PMC7522156 (Framework for Extracting Critical Findings).
        TriageRule(
            name="Control de patología",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="control",
            weight=-5,
        ),
        TriageRule(
            name="Seguimiento",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="seguimiento",
            weight=-5,
        ),
        TriageRule(
            name="Evolución",
            field=TriageField.DIAGNOSIS,
            operator=TriageOperator.CONTAINS,
            value="evolución",
            weight=-5,
        ),
    ]

    session.add_all(rules)
    await session.flush()
    for r in rules:
        await session.refresh(r)
    return rules
