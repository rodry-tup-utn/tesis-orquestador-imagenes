"""Fixtures compartidas para los tests del motor de triaje."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from datetime import date, datetime, timezone

from app.modules.medical_order.model import Modality, OrderSetting, Sex, OrderState, MedicalPriority
from app.modules.triage.model import TriageOperator


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
    """Umbrales de la configuracion calibrada (Fase 4)."""
    return make_settings(critical=25, urgent=12, priority=10)


@pytest.fixture
def calibrated_rules():
    """Subconjunto de reglas calibradas (Fase 4) para tests reproducibles."""
    rules = [
        make_rule("diagnosis",        TriageOperator.CONTAINS, "ACV",          20, "ACV"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "politrauma",    18, "Politraumatismo"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "hemorragia",    12, "Hemorragia"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "TEP",          10, "TEP"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "colecistitis",  10, "Colecistitis"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "apendicitis",   10, "Apendicitis"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "fractura",       9, "Fractura"),
        make_rule("modality",         TriageOperator.EQUALS,   "CT",             6, "CT"),
        make_rule("modality",         TriageOperator.EQUALS,   "MR",             5, "MR"),
        make_rule("modality",         TriageOperator.EQUALS,   "US",             2, "US"),
        make_rule("modality",         TriageOperator.EQUALS,   "DX",             1, "DX"),
        make_rule("patient_location", TriageOperator.CONTAINS, "UTI",            6, "UTI"),
        make_rule("patient_location", TriageOperator.CONTAINS, "Shock Room",     8, "Shock Room"),
        make_rule("patient_location", TriageOperator.CONTAINS, "Box Rojo",       6, "Box Rojo"),
        make_rule("origin_service",   TriageOperator.CONTAINS, "guardia",        4, "Guardia"),
        make_rule("origin_service",   TriageOperator.CONTAINS, "internacion",    4, "Internacion"),
        make_rule("origin_service",   TriageOperator.CONTAINS, "ambulatorio",  -50, "Ambulatorio"),
        make_rule("is_urgent",        TriageOperator.EQUALS,   "True",           4, "Urgente origen"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "control",       -5, "Control"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "seguimiento",   -5, "Seguimiento"),
        make_rule("diagnosis",        TriageOperator.CONTAINS, "evolucion",     -5, "Evolucion"),
    ]
    return rules
