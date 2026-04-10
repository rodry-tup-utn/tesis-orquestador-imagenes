import requests
from sqlmodel import Session
from app.medicalorder.model import MedicalOrder
from app.database import engine
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())
URL_WEBHOOK_N8N = os.getenv("URL_WEBHOOK_N8N")


def evaluate_and_notify(order_id: int):
    if not URL_WEBHOOK_N8N:
        raise ValueError(
            "🚨 ¡ERROR CRITICO! La variable URL_WEBHOOK_N8N no fue encontrada. Revisa el archivo .env"
        )
    with Session(engine) as session:
        print(f"🚀 Notificador: Iniciando proceso para orden ID: {order_id}")

        try:
            # get para traer la orden
            order = session.get(MedicalOrder, order_id)

            if not order:
                print(
                    f"⚠️ Error: No se encontró la orden {order_id} en la base de datos."
                )
                return

            if not order.is_urgent:
                print(f"ℹ️ Orden {order_id} no es urgente. Fin del proceso.")
                return

            payload = {
                "message": "🚨 ALERTA MÉDICA CRÍTICA",
                "patient": f"{order.patient_name} {order.patient_lastname}",  # Para pruebas con Nombre y apellido, en produccion con pseudónimo
                "diagnosis": order.diagnosis,
                "date": order.order_date.isoformat(),
                "location": order.location,
                "setting": order.study_setting,
                "order_id": order.id,
            }

            print(f"📡 Enviando POST a n8n para paciente: {order.patient_name}...")

            # timeout de 5 segundos para que no se trabe
            response = requests.post(URL_WEBHOOK_N8N, json=payload, timeout=5)

            if response.status_code == 200:
                order.was_notified = True
                session.add(order)
                session.commit()
                print(
                    f"✅ ÉXITO: n8n confirmó recepción. Orden {order_id} marcada como notificada."
                )
            else:
                print(
                    f"⚠️ n8n respondió con error {response.status_code}: {response.text}"
                )

        # manejo de errores
        except requests.exceptions.ConnectionError:
            print(
                "❌ ERROR DE CONEXIÓN: No se pudo contactar a n8n. ¿Está encendido el servicio?"
            )
        except Exception as e:
            print(f"❌ ERROR INESPERADO en el notifier: {type(e).__name__} - {e}")
