from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.triage.model import TriageRule
from app.modules.triage.schemas import (
    TriageRuleCreate,
    TriageRuleRead,
    TriageRuleUpdate,
)

router = APIRouter(prefix="/triage-rules", tags=["Triage"])


@router.get("", response_model=list[TriageRuleRead])
async def list_triage_rules(session: AsyncSession = Depends(get_session)):
    async with UnitOfWork(session) as uow:
        rules = await uow.triage_rules.get_all()
        return [TriageRuleRead.model_validate(r) for r in rules]


@router.post("", response_model=TriageRuleRead, status_code=201)
async def create_triage_rule(
    data: TriageRuleCreate, session: AsyncSession = Depends(get_session)
):
    async with UnitOfWork(session) as uow:
        rule = TriageRule.model_validate(data)
        rule = await uow.triage_rules.add(rule)
        return TriageRuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=TriageRuleRead)
async def update_triage_rule(
    rule_id: int, data: TriageRuleUpdate, session: AsyncSession = Depends(get_session)
):
    async with UnitOfWork(session) as uow:
        rule = await uow.triage_rules.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Triage rule not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)

        uow.triage_rules.session.add(rule)
        await uow.triage_rules.session.flush()
        await uow.triage_rules.session.refresh(rule)
        return TriageRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_triage_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
):
    async with UnitOfWork(session) as uow:
        rule = await uow.triage_rules.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Triage rule not found")
        await uow.triage_rules.delete(rule)
