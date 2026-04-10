from sqlmodel import Session, select, col, func
from app.medicalorder.model import MedicalOrder, MedicalOrderCreate, MedicalOrderUpdate
from typing import Optional
from fastapi import Query
from datetime import datetime, timedelta, timezone


def get_all(
    session: Session,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    only_active: bool = True,
    patient_dni: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    statement = select(MedicalOrder).order_by(col(MedicalOrder.created_at).desc())

    if only_active:
        statement = statement.where(MedicalOrder.is_active)

    if start_date:
        statement = statement.where(MedicalOrder.order_date >= start_date)

    if end_date:
        statement = statement.where(MedicalOrder.order_date <= end_date)

    if not start_date and not end_date:
        time_limit = datetime.now(timezone.utc) - timedelta(hours=24)
        statement = statement.where(MedicalOrder.created_at >= time_limit)

    if patient_dni:
        statement = statement.where(MedicalOrder.patient_dni == patient_dni)

    count_statement = select(func.count()).select_from(statement.subquery())

    total = session.exec(count_statement).one()
    items = session.exec(statement.offset(skip).limit(limit)).all()

    return items, total


def get_order_id(session: Session, order_id: int):
    order = session.get(MedicalOrder, order_id)

    if not order:
        raise LookupError(f"No se encontró la orden con el id {order_id}")

    return order


def create_order(session: Session, data: MedicalOrderCreate):

    order = MedicalOrder.model_validate(data)

    session.add(order)
    session.commit()
    session.refresh(order)

    ##Aqui deberiamos llamar a la logica de validacion para completar los campos que faltan

    return order


def create_orders_batch_service(session: Session, data_list: list[MedicalOrderCreate]):
    ids_externos = [d.external_id for d in data_list]

    existentes_row = session.exec(
        select(MedicalOrder.external_id).where(
            col(MedicalOrder.external_id).in_(ids_externos)
        )
    ).all()

    existentes = set(existentes_row)
    nuevas_instancias = []

    for data in data_list:
        if data.external_id not in existentes:
            nueva = MedicalOrder.model_validate(data)
            session.add(nueva)
            nuevas_instancias.append(nueva)

    if nuevas_instancias:

        session.commit()
        # Refrescamos para tener los IDs de Postgres
        for n in nuevas_instancias:
            session.refresh(n)

    return nuevas_instancias


def delete_order(session: Session, order_id):
    order = session.get(MedicalOrder, order_id)

    if order is None:
        raise LookupError(f"No se encontro una orden con el id {order_id}")

    if not order.is_active:
        raise ValueError("La orden ya se encuentra borrada")

    order.is_active = False

    session.add(order)
    session.commit()
    session.refresh(order)

    return order


def update_order(session: Session, order_id: int, data: MedicalOrderUpdate):

    order = session.get(MedicalOrder, order_id)

    if not order:
        raise LookupError(f"Orden con id {order_id} no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(order, key, value)

    session.add(order)
    session.commit()
    session.refresh(order)

    return order
