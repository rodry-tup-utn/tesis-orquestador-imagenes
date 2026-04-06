from sqlmodel import Session, select
from app.medicalorder.model import MedicalOrder, MedicalOrderCreate
from typing import Sequence


def get_all(session: Session) -> Sequence[MedicalOrder]:
    statement = select(MedicalOrder)
    result = session.exec(statement)
    orders = result.all()

    return orders


def create_order(session: Session, data: MedicalOrderCreate):
    order = MedicalOrder.model_validate(data)

    session.add(order)
    session.commit()
    session.refresh(order)

    ##Aqui deberiamos llamar a la logica de validacion para completar los campos que faltan

    return order
