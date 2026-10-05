"""Fixtures compartidas para los tests del motor de triaje."""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Valores exclusivamente de prueba: permiten ejecutar la suite documentada
# sin exigir un archivo .env ni secretos reales. Cualquier variable definida
# por el entorno del ejecutor tiene precedencia gracias a setdefault().
os.environ.setdefault("POSTGRES_USER", "test_postgres_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_postgres_password")
os.environ.setdefault("POSTGRES_DB", "test_postgres_db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-32-bytes-minimum!!")
os.environ.setdefault("PSEUDONYM_SECRET", "test-pseudonym-secret-key-para-tests-unitarios")
os.environ.setdefault("AUTH_PASSWORD", "clave-de-prueba")
os.environ.setdefault("AUTH_USERNAME", "admin")
os.environ.setdefault("INTERNAL_API_KEY", "api-key-de-prueba")
os.environ.setdefault("ALERT_WEBHOOK_KEY", "alert-webhook-key-de-prueba")

import pytest
from unittest.mock import MagicMock
from datetime import date, datetime, timezone

from app.modules.medical_order.model import Modality, OrderSetting, Sex, OrderState, MedicalPriority
from app.modules.triage.model import TriageOperator


CALIBRATION_PATH = Path(__file__).resolve().parents[1] / "app" / "modules" / "triage" / "configs" / "calibrada_fase4.json"


def load_calibrated_config():
    """Carga la configuración calibrada versionada que acompaña a la entrega."""
    with CALIBRATION_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_calibrated_rules():
    """Construye los mocks de regla directamente desde calibrada_fase4.json."""
    config = load_calibrated_config()
    return [
        make_rule(
            rule["field"],
            TriageOperator(rule["operator"]),
            rule["value"],
            rule["weight"],
            rule.get("name"),
            rule.get("enabled", True),
        )
        for rule in config["rules"]
    ]


def make_settings(critical=25, urgent=12, priority=10):
    """Genera un objeto SystemSettings mockeado con los umbrales dados."""
    s = MagicMock()
    s.triage_critical_threshold = critical
    s.triage_urgent_threshold = urgent
    s.triage_priority_threshold = priority
    return s


def make_rule(field, operator, value, weight, name=None, enabled=True):
    """Genera un objeto TriageRule mockeado."""
    r = MagicMock()
    r.field = field
    r.operator = operator
    r.value = value
    r.weight = weight
    r.name = name or f"{field}:{value}"
    r.enabled = enabled
    return r


def make_order(
    modality=None,
    diagnosis="Rutina",
    origin_service="Ambulatorio",
    patient_location="Consultorio",
    is_urgent=False,
    **kwargs,
):
    """Genera un objeto MedicalOrder mockeado usando los enums reales."""
    order = MagicMock()
    order.modality = modality if modality is not None else Modality.DX
    order.diagnosis = diagnosis
    order.origin_service = origin_service
    order.patient_location = patient_location
    order.is_urgent = is_urgent
    order.description = kwargs.get("description", "Estudio de prueba")
    order.patient_name = kwargs.get("patient_name", "Paciente")
    order.patient_lastname = kwargs.get("patient_lastname", "Test")
    order.patient_dni = kwargs.get("patient_dni", "12345678")
    order.patient_dob = kwargs.get("patient_dob", date(1990, 1, 1))
    order.order_date = kwargs.get("order_date", datetime.now(timezone.utc))
    # Atributos extra: getattr devolverá el valor si existe
    for k, v in kwargs.items():
        setattr(order, k, v)
    return order


@pytest.fixture
def default_settings():
    """Umbrales de la configuración calibrada (Fase 4) versionados en JSON."""
    thresholds = load_calibrated_config()["thresholds"]
    return make_settings(
        critical=thresholds["critical"],
        urgent=thresholds["urgent"],
        priority=thresholds["priority"],
    )


@pytest.fixture
def calibrated_rules():
    """Reglas calibradas cargadas desde el archivo versionado de Fase 4."""
    return load_calibrated_rules()
