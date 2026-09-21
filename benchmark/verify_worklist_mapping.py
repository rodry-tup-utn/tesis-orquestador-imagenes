#!/usr/bin/env python3
"""Verificacion de equivalencia entre Base de Datos y archivos DICOM Worklist (.wl).

Resuelve el pendiente metodologico declarado en §4.12 y §5.4:
    Medicion formal de la Tasa de Error de Mapeo (TEM)
    entre los registros de `medicalorder` y los atributos serializados
    en formato DICOM Modality Worklist (PS3.4 / PS3.3).

Para cada orden despachada hacia Orthanc (send_to_orthanc):
  1. Toma los valores esperados de la respuesta del endpoint de despacho, que
     los lee de la base de datos (PostgreSQL) y los usa para generar el archivo.
  2. Lee con pydicom el archivo .wl generado en /worklists.
  3. Compara campo por campo (7 atributos por orden):
     - (0010,0010) Patient's Name             == Apellido^Nombre
     - (0010,0020) Patient ID                 == DNI
     - (0010,0030) Patient's Birth Date       == YYYYMMDD
     - (0010,0040) Patient's Sex              == M / F / O
     - (0020,000D) Study Instance UID         == study_instance_uid
     - (0040,0100)[0] (0008,0060) Modality    == modality
     - (0040,0100)[0] (0040,0007) Description == description

Limitaciones (declaradas): (a) el valor esperado proviene del mismo servicio que
genera el archivo, de modo que se detectan errores de serializacion y de
anidamiento DICOM, no errores de lectura de la base; (b) no se comparan
Accession Number (0008,0050), Station AET (0040,0001) ni Step Date/Time
(0040,0002/0003).

Uso (dentro del contenedor o con acceso al volumen /worklists):
    docker compose exec backend python /benchmark/verify_worklist_mapping.py
"""
from __future__ import annotations
import asyncio
import csv
import glob
import json
import os
import sys
import time
import urllib.request
import pydicom

# Soporte de paths segun ejecucion en host o en contenedor
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BENCHMARK_DIR)
if os.path.exists("/app/app/modules"):
    sys.path.insert(0, "/app")
    WORKLISTS_DIR = "/worklists"
else:
    sys.path.insert(0, os.path.join(REPO_ROOT, "server"))
    WORKLISTS_DIR = "/worklists" if os.path.exists("/worklists") else os.path.join(REPO_ROOT, "worklists")

import common


def get_jwt(backend_url: str, user: str, password: str) -> str:
    body = json.dumps({"username": user, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{backend_url}/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def get_orders(backend_url: str, token: str) -> list[dict]:
    req = urllib.request.Request(
        f"{backend_url}/orders?limit=100&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        return data.get("items", []) if isinstance(data, dict) else data


def create_sample_orders(backend_url: str, api_key: str, count: int = 10) -> None:
    modalities = ["CT", "MR", "DX", "US"]
    sexes = ["MALE", "FEMALE", "OTHER"]
    sample_orders = []
    for i in range(1, count + 1):
        mod = modalities[(i - 1) % len(modalities)]
        sex = sexes[(i - 1) % len(sexes)]
        sample_orders.append({
            "external_id": f"WL-EVAL-{i:03d}",
            "source_system": "SISTEMA_ORIGEN",
            "description": f"Estudio Protocolizado {mod} #{i}",
            "modality": mod,
            "origin_service": "Guardia" if i % 2 == 0 else "Ambulatorio",
            "patient_location": "Box 1" if i % 2 == 0 else "Consultorio 2",
            "study_setting": "En Efector",
            "diagnosis": "Diagnostico de evaluacion TEM",
            "observations": "Verificacion formal de integridad DICOM MWL",
            "order_date": "2026-09-20T12:00:00",
            "requesting_physician": "Dr. Evaluador",
            "patient_lastname": f"Apellido{i}",
            "patient_name": f"Nombre{i}",
            "patient_dni": f"350000{i:02d}",
            "patient_dob": f"1985-0{(i % 9) + 1:01d}-15",
            "patient_sex": sex,
            "is_urgent": (i % 2 == 0),
        })

    body = json.dumps({"cycle_id": "WL-VERIF", "orders": sample_orders}).encode("utf-8")
    req = urllib.request.Request(
        f"{backend_url}/orders/batch",
        data=body,
        headers={"Content-Type": "application/json", "X-Internal-API-Key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def send_to_orthanc(backend_url: str, token: str, order_id: int) -> dict:
    req = urllib.request.Request(
        f"{backend_url}/orders/{order_id}/send-to-orthanc",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def match_wl_file(study_instance_uid: str, worklists_dir: str) -> pydicom.Dataset | None:
    for path in glob.glob(os.path.join(worklists_dir, "*.wl")):
        try:
            ds = pydicom.dcmread(path, force=True)
            if getattr(ds, "StudyInstanceUID", None) == study_instance_uid:
                return ds
        except Exception:
            continue
    return None


def main() -> None:
    default_backend = "http://backend:8000" if os.path.exists("/app/app") else "http://localhost:8000"
    backend_url = os.environ.get("BACKEND_URL", default_backend)
    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    password = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    api_key = os.environ.get("INTERNAL_API_KEY") or env.get("INTERNAL_API_KEY", "")

    if not password:
        sys.exit("[ERROR] Falta AUTH_PASSWORD")

    token = get_jwt(backend_url, user, password)
    orders = get_orders(backend_url, token)

    # Si hay pocas ordenes, creamos un conjunto representativo de 15 ordenes
    if len(orders) < 15:
        print(f"Cargando lote de prueba de 15 ordenes para evaluacion exhaustiva...")
        create_sample_orders(backend_url, api_key, count=15)
        orders = get_orders(backend_url, token)

    print(f"\n{'='*70}")
    print("  EVALUACION DE EQUIVALENCIA BD <-> DICOM WORKLIST (.wl)")
    print("  Tasa de Error de Mapeo (TEM)")
    print(f"{'='*70}")

    dispatched = []
    for o in orders[:20]:  # Evaluar hasta 20 ordenes representativas
        oid = o["id"]
        res = send_to_orthanc(backend_url, token, oid)
        dispatched.append(res)
        p = res.get("patient", {})
        print(f"  [DESPACHADA] Orden #{oid:2d} (DNI {p.get('dni', '')}) -> MWL generada")

    print(f"\nInspeccionando archivos DICOM en '{WORKLISTS_DIR}' con pydicom...")
    comparisons = []
    total_fields_checked = 0
    total_field_errors = 0
    orders_checked = 0
    order_errors = 0

    sex_map = {"MALE": "M", "FEMALE": "F", "OTHER": "O"}

    for o in dispatched:
        uid = o.get("study_instance_uid")
        ds = match_wl_file(uid, WORKLISTS_DIR)
        if not ds:
            print(f"  [ERROR] No se hallo archivo .wl para StudyInstanceUID={uid}")
            order_errors += 1
            continue

        orders_checked += 1
        order_has_error = False

        patient = o.get("patient", {})
        order_details = o.get("order", {})

        # Verificaciones campo por campo
        # 1. PatientName
        expected_name = f"{patient.get('lastname', '')}^{patient.get('name', '')}"
        actual_name = str(getattr(ds, "PatientName", ""))
        err_name = actual_name != expected_name

        # 2. PatientID
        expected_id = str(patient.get("dni", ""))
        actual_id = str(getattr(ds, "PatientID", ""))
        err_id = actual_id != expected_id

        # 3. PatientBirthDate
        expected_dob = str(patient.get("dob", "")).replace("-", "")
        actual_dob = str(getattr(ds, "PatientBirthDate", ""))
        err_dob = actual_dob != expected_dob

        # 4. PatientSex
        expected_sex = sex_map.get(str(patient.get("sex", "")), "O")
        actual_sex = str(getattr(ds, "PatientSex", ""))
        err_sex = actual_sex != expected_sex

        # 5. StudyInstanceUID
        expected_uid = str(uid)
        actual_uid = str(getattr(ds, "StudyInstanceUID", ""))
        err_uid = actual_uid != expected_uid

        # 6. ScheduledProcedureStepSequence
        seq = getattr(ds, "ScheduledProcedureStepSequence", None)
        has_seq = seq is not None and len(seq) > 0
        step = seq[0] if has_seq else None

        actual_mod = str(getattr(step, "Modality", "")) if step else ""
        expected_mod = str(order_details.get("modality", ""))
        err_mod = actual_mod != expected_mod

        actual_desc = str(getattr(step, "ScheduledProcedureStepDescription", "")) if step else ""
        expected_desc = str(order_details.get("description", ""))
        err_desc = actual_desc != expected_desc

        field_checks = [
            ("PatientName", expected_name, actual_name, err_name),
            ("PatientID", expected_id, actual_id, err_id),
            ("PatientBirthDate", expected_dob, actual_dob, err_dob),
            ("PatientSex", expected_sex, actual_sex, err_sex),
            ("StudyInstanceUID", expected_uid, actual_uid, err_uid),
            ("Modality", expected_mod, actual_mod, err_mod),
            ("StepDescription", expected_desc, actual_desc, err_desc),
        ]

        total_fields_checked += len(field_checks)
        for field, exp, act, err in field_checks:
            if err:
                total_field_errors += 1
                order_has_error = True

        if order_has_error:
            order_errors += 1

        comparisons.append({
            "order_id": o["id"],
            "patient_dni": patient.get("dni", ""),
            "modality": order_details.get("modality", ""),
            "name_ok": not err_name,
            "id_ok": not err_id,
            "dob_ok": not err_dob,
            "sex_ok": not err_sex,
            "uid_ok": not err_uid,
            "mod_ok": not err_mod,
            "desc_ok": not err_desc,
        })

    # Guardar reporte
    stamp = time.strftime("%Y-%m-%d")
    out_csv = os.path.join(BENCHMARK_DIR, "results", f"results_worklist_equivalence_{stamp}.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "order_id", "patient_dni", "modality",
            "name_ok", "id_ok", "dob_ok", "sex_ok", "uid_ok", "mod_ok", "desc_ok"
        ])
        writer.writeheader()
        writer.writerows(comparisons)

    tem = (order_errors / orders_checked * 100.0) if orders_checked else 0.0
    field_accuracy = ((total_fields_checked - total_field_errors) / total_fields_checked * 100.0) if total_fields_checked else 0.0

    print(f"\n{'='*70}")
    print("  RESULTADO DE VERIFICACION DE MAPEO DICOM MWL")
    print(f"{'='*70}")
    print(f"  Ordenes evaluadas:              {orders_checked}")
    print(f"  Campos DICOM auditados:         {total_fields_checked}")
    print(f"  Campos discrepantes:            {total_field_errors}")
    print(f"  Exactitud de atributos:         {field_accuracy:.2f}%")
    print(f"  TEM (Tasa de Error de Mapeo):   {tem:.2f}% ({order_errors}/{orders_checked})")
    print(f"  CSV guardado en:                {out_csv}")
    print(f"{'='*70}")
    if tem == 0.0:
        print("  -> EQUIVALENCIA EXACTA: 0 errores de mapeo entre BD y dataset DICOM.\n")


if __name__ == "__main__":
    main()
