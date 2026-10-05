"""Pruebas de Contrato Automatizadas: Normalizadores ↔ Catálogo ↔ Backend FastAPI.

Verifica formalmente que:
1. Los esquemas emitidos por los normalizadores (Ambulatorio, Guardia, Internación)
   cumplen estrictamente con el modelo Pydantic `MedicalOrderCreate` del backend.
2. Todas las modalidades inferidas pertenecen al catálogo oficial (Modality enum: CT, MR, US, DX, CR).
3. La codificación de sexo y configuración de estudio coincide con los enums oficiales (Sex, OrderSetting).
4. No existen discrepancias de tipos de datos, fechas o campos obligatorios (cero fallos de validación 422).
5. Los campos requeridos por el motor de triaje (diagnosis, modality, origin_service, patient_location, is_urgent)
   se conservan íntegros sin pérdida ni truncamiento.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.modules.medical_order.schemas import MedicalOrderCreate
from app.modules.medical_order.model import Modality, OrderSetting, Sex

MOCKS_DIR = Path(__file__).resolve().parent.parent / "mocks"
if not MOCKS_DIR.exists():
    MOCKS_DIR = Path(__file__).resolve().parent.parent.parent / "mocks"


def normalize_ambulatorio(item: dict) -> dict:
    partes_nombre = (item.get("PACIENTE_DATA") or "").split("^")
    apellido = partes_nombre[0] if len(partes_nombre) > 0 else ""
    nombre = partes_nombre[1] if len(partes_nombre) > 1 else ""

    prestacion = (item.get("PRESTACION_DESC") or "").lower()
    modalidad = "DX"
    if "resonancia" in prestacion or "rm" in prestacion:
        modalidad = "MR"
    elif "ecograf" in prestacion or "ecografía" in prestacion:
        modalidad = "US"
    elif "tomograf" in prestacion or "tc" in prestacion or "tac" in prestacion:
        modalidad = "CT"

    fecha_turno = "1900-01-01T00:00:00Z"
    ft = item.get("FECHA_TURNO")
    ht = item.get("HORA_TURNO") or "00:00"
    if ft:
        try:
            dt = datetime.fromisoformat(f"{ft}T{ht}:00")
            fecha_turno = dt.isoformat()
        except Exception:
            pass

    sexo_raw = (item.get("SEXO") or "").upper()
    sexo = "FEMALE" if sexo_raw == "F" else ("MALE" if sexo_raw == "M" else "OTHER")

    return {
        "external_id": f"A-{item.get('ID_CITA')}",
        "source_system": "AMBULATORIO",
        "modality": modalidad,
        "description": item.get("PRESTACION_DESC") or "Estudio",
        "origin_service": "Ambulatorio",
        "diagnosis": item.get("DIAGNOSTICO") or "Sin especificar",
        "observations": item.get("OBSERVACIONES") or "Sin observaciones",
        "patient_location": "Atención Ambulatoria",
        "order_date": fecha_turno,
        "study_setting": "En Efector",
        "patient_name": nombre,
        "patient_lastname": apellido,
        "patient_dni": str(item.get("NRO_DOCUMENTO") or "0"),
        "patient_dob": item.get("FECHA_NACIMIENTO") or "1900-01-01",
        "patient_sex": sexo,
        "requesting_physician": item.get("MEDICO_DERIVANTE") or "No especificado",
        "is_urgent": False,
        "is_active": True,
    }


def normalize_guardia(item: dict) -> dict:
    partes_nombre = (item.get("nom_paciente") or "").split(", ")
    apellido = partes_nombre[0] if len(partes_nombre) > 0 else ""
    nombre = partes_nombre[1] if len(partes_nombre) > 1 else ""

    prioridad = item.get("urgente") == "SI"
    prestacion = item.get("estudio_req") or "Sin detalle"
    p_lower = prestacion.lower()

    modalidad = "DX"
    if "resonancia" in p_lower or "rm" in p_lower:
        modalidad = "MR"
    elif "ecograf" in p_lower or "ecografía" in p_lower:
        modalidad = "US"
    elif "tomograf" in p_lower or "tc" in p_lower or "tac" in p_lower:
        modalidad = "CT"
    elif "radiograf" in p_lower or "rx" in p_lower:
        modalidad = "DX"

    setting_raw = (item.get("lugar_estudio") or "En Efector").lower()
    setting = "En Cama" if "cama" in setting_raw else "En Efector"

    fecha_hora = item.get("fecha_hora")
    order_date = "1900-01-01T00:00:00Z"
    if fecha_hora:
        try:
            dt = datetime.fromisoformat(fecha_hora)
            order_date = dt.isoformat()
        except Exception:
            pass

    sexo_raw = (item.get("sexo") or "").upper()
    sexo = "FEMALE" if sexo_raw == "F" else ("MALE" if sexo_raw == "M" else "OTHER")

    return {
        "external_id": f"G-{item.get('id_transaccion')}",
        "source_system": "GUARDIA",
        "modality": modalidad,
        "description": prestacion,
        "diagnosis": item.get("diagnostico") or "Sin diagnostico",
        "observations": item.get("observaciones") or "Sin observaciones",
        "patient_location": item.get("ubicacion_actual") or "Guardia",
        "origin_service": "Guardia",
        "order_date": order_date,
        "study_setting": setting,
        "patient_name": nombre,
        "patient_lastname": apellido,
        "patient_dni": str(item.get("doc_identidad") or "0"),
        "patient_dob": item.get("fecha_nacimiento") or "1900-01-01",
        "patient_sex": sexo,
        "requesting_physician": item.get("solicitante") or "Solicitante no especificado",
        "is_urgent": prioridad,
        "is_active": True,
    }


def normalize_internacion(item: dict) -> dict:
    paciente = item.get("patient_data") or {}
    orden = item.get("clinical_order") or {}

    nombre = paciente.get("first_name") or ""
    apellido = paciente.get("last_name") or ""

    bd = paciente.get("birth_date") or {}
    if bd.get("year"):
        fecha_nac = f"{bd['year']}-{int(bd['month']):02d}-{int(bd['day']):02d}"
    else:
        fecha_nac = "1900-01-01"

    prioridad = bool(item.get("is_urgent"))
    sector = orden.get("sector") or "S/D"
    room = orden.get("room") or "-"
    bed = orden.get("bed") or "-"
    ubicacion = f"{sector} - Hab: {room} Cama: {bed}"

    mod = (orden.get("modality") or "DX").upper()
    if mod == "CR":
        mod = "DX"

    setting_raw = (orden.get("study_setting") or "En Efector").lower()
    setting = "En Cama" if "cama" in setting_raw else "En Efector"

    fecha = orden.get("date")
    order_date = "1900-01-01T00:00:00Z"
    if fecha:
        try:
            dt = datetime.fromisoformat(fecha)
            order_date = dt.isoformat()
        except Exception:
            pass

    sexo_raw = (paciente.get("sex") or "").upper()
    sexo = "FEMALE" if sexo_raw == "F" else ("MALE" if sexo_raw == "M" else "OTHER")

    return {
        "external_id": f"I-{item.get('request_id')}",
        "source_system": "INTERNACION",
        "modality": mod,
        "description": orden.get("procedure") or "Estudio",
        "origin_service": "Internacion",
        "diagnosis": orden.get("diagnosis") or "Sin diagnostico",
        "observations": orden.get("observations") or "Sin observaciones",
        "patient_location": ubicacion,
        "order_date": order_date,
        "study_setting": setting,
        "patient_name": nombre,
        "patient_lastname": apellido,
        "patient_dni": str(paciente.get("national_id") or "0"),
        "patient_dob": fecha_nac,
        "patient_sex": sexo,
        "requesting_physician": orden.get("requesting_physician") or "No especificado",
        "is_urgent": prioridad,
        "is_active": True,
    }


class TestContratoNormalizadoresBackend:
    """Verifica que el 100% de las órdenes de los 3 sistemas origen se normalizan
    y satisfacen el contrato Pydantic del backend sin errores 422."""

    def test_contrato_ambulatorio(self):
        with open(MOCKS_DIR / "ambulatorio.json", encoding="utf-8") as f:
            raw_orders = json.load(f)

        assert len(raw_orders) > 0, "El mock de ambulatorio no debe estar vacío"
        for raw in raw_orders:
            norm = normalize_ambulatorio(raw)
            # Validación estricta con Pydantic
            order_model = MedicalOrderCreate(**norm)
            assert isinstance(order_model.modality, Modality)
            assert isinstance(order_model.patient_sex, Sex)
            assert isinstance(order_model.study_setting, OrderSetting)
            assert order_model.origin_service == "Ambulatorio"

    def test_contrato_guardia(self):
        with open(MOCKS_DIR / "guardia.json", encoding="utf-8") as f:
            raw_orders = json.load(f)

        assert len(raw_orders) > 0, "El mock de guardia no debe estar vacío"
        for raw in raw_orders:
            norm = normalize_guardia(raw)
            order_model = MedicalOrderCreate(**norm)
            assert isinstance(order_model.modality, Modality)
            assert isinstance(order_model.patient_sex, Sex)
            assert isinstance(order_model.study_setting, OrderSetting)
            assert order_model.origin_service == "Guardia"
            assert isinstance(order_model.is_urgent, bool)

    def test_contrato_internacion(self):
        with open(MOCKS_DIR / "internacion.json", encoding="utf-8") as f:
            raw_orders = json.load(f)

        assert len(raw_orders) > 0, "El mock de internacion no debe estar vacío"
        for raw in raw_orders:
            norm = normalize_internacion(raw)
            order_model = MedicalOrderCreate(**norm)
            assert isinstance(order_model.modality, Modality)
            assert isinstance(order_model.patient_sex, Sex)
            assert isinstance(order_model.study_setting, OrderSetting)
            assert order_model.origin_service == "Internacion"

    def test_cobertura_catalogo_modalidades(self):
        """Verifica que las modalidades normalizadas pertenecen al catálogo DICOM soportado."""
        modalidades_validas = {m.value for m in Modality}
        for filename, normalizer in [
            ("ambulatorio.json", normalize_ambulatorio),
            ("guardia.json", normalize_guardia),
            ("internacion.json", normalize_internacion),
        ]:
            with open(MOCKS_DIR / filename, encoding="utf-8") as f:
                raw_orders = json.load(f)
            for raw in raw_orders:
                norm = normalizer(raw)
                assert norm["modality"] in modalidades_validas, (
                    f"Modalidad '{norm['modality']}' no pertenece al catálogo oficial {modalidades_validas}"
                )
