from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
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
def list_triage_rules(session: Session = Depends(get_session)):
    with UnitOfWork(session) as uow:
        rules = uow.triage_rules.get_all()
        return [TriageRuleRead.model_validate(r) for r in rules]


@router.post("", response_model=TriageRuleRead, status_code=201)
def create_triage_rule(
    data: TriageRuleCreate, session: Session = Depends(get_session)
):
    with UnitOfWork(session) as uow:
        rule = TriageRule.model_validate(data)
        rule = uow.triage_rules.add(rule)
        return TriageRuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=TriageRuleRead)
def update_triage_rule(
    rule_id: int, data: TriageRuleUpdate, session: Session = Depends(get_session)
):
    with UnitOfWork(session) as uow:
        rule = uow.triage_rules.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Triage rule not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)

        uow.triage_rules.session.add(rule)
        uow.triage_rules.session.flush()
        uow.triage_rules.session.refresh(rule)
        return TriageRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
def delete_triage_rule(
    rule_id: int, session: Session = Depends(get_session)
):
    with UnitOfWork(session) as uow:
        rule = uow.triage_rules.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Triage rule not found")
        uow.triage_rules.delete(rule)
