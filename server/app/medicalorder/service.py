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
