from sqlmodel import Session, select, col, func
from app.medicalorder.model import MedicalOrder, MedicalOrderCreate, MedicalOrderUpdate


def get_all(session: Session, skip: int, limit: int, only_active: bool = True):
    statement = select(MedicalOrder).order_by(col(MedicalOrder.created_at).desc())
    total_statement = select(func.count()).select_from(MedicalOrder)

    if only_active:
        statement = statement.where(MedicalOrder.is_active)
        total_statement = total_statement.where(MedicalOrder.is_active)

    items = session.exec(statement.offset(skip).limit(limit)).all()
    total = session.exec(total_statement).one()

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

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(order, key, value)

    session.add(order)
    session.commit()
    session.refresh(order)

    return order
