from sqlmodel import Session, select, col, func
from app.medicalorder.model import MedicalOrder, MedicalOrderCreate


def get_all(session: Session, skip: int, limit: int):
    total_statement = select(func.count()).select_from(MedicalOrder)
    total = session.exec(total_statement).one()

    items_statement = (
        select(MedicalOrder)
        .order_by(col(MedicalOrder.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(items_statement).all()

    return items, total


def create_order(session: Session, data: MedicalOrderCreate):
    order = MedicalOrder.model_validate(data)

    session.add(order)
    session.commit()
    session.refresh(order)

    ##Aqui deberiamos llamar a la logica de validacion para completar los campos que faltan

    return order
