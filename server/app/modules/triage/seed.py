from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.modules.triage.model import TriageRule, TriageField, TriageOperator
from app.modules.triage.configuration import load_triage_config


async def seed_triage_rules(session: AsyncSession) -> list[TriageRule]:
    statement = select(func.count()).select_from(TriageRule)
    result = await session.execute(statement)
    count = result.scalar_one()
    if count > 0:
        return []

    rules = [
        TriageRule(
            name=rule["name"],
            field=TriageField(rule["field"]),
            operator=TriageOperator(rule["operator"]),
            value=rule["value"],
            weight=rule["weight"],
        )
        for rule in load_triage_config()["rules"]
    ]

    session.add_all(rules)
    await session.flush()
    for r in rules:
        await session.refresh(r)
    return rules
