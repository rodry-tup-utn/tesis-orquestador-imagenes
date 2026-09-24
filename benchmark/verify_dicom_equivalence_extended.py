#!/usr/bin/env python3
"""Verificación extendida del mapeo DICOM MWL mediante el serializador productivo.

Compara siete atributos por orden en 50 órdenes sintéticas (350 checks). La prueba
usa exactamente `build_worklist_dataset`, la misma función de serialización invocada
por el cliente productivo. No sustituye una prueba C-FIND contra una modalidad real.
"""
from __future__ import annotations
import csv
import io
import os
import sys
from datetime import date
import pydicom

SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server"))
sys.path.insert(0, SERVER_DIR)
from app.core.orthanc_client import build_worklist_dataset

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(BENCHMARK_DIR, "results", "results_worklist_equivalence_extended_2026-09-23.csv")


def mapping_for(order: dict) -> dict:
    fecha = order["order_date"].strftime("%Y%m%d")
    hora = order["order_date"].strftime("%H%M%S")
    return {
        "0010,0010": f"{order['patient_lastname']}^{order['patient_name']}",
        "0010,0020": str(order["patient_dni"]),
        "0010,0030": order["patient_dob"].strftime("%Y%m%d"),
        "0010,0040": order["patient_sex"],
        "0020,000D": order["study_instance_uid"],
        "0008,0050": f"ACC-{order['id']}-{fecha}",
        "0040,0100": [{
            "0008,0060": order["modality"],
            "0040,0001": f"AET_{order['modality']}_1",
            "0040,0002": fecha,
            "0040,0003": hora,
            "0040,0007": order["description"],
        }],
    }


def main() -> int:
    modalities = ["CT", "MR", "US", "DX"]
    sexes = ["M", "F", "O"]
    rows = []
    total_checks = 0
    discrepancies = 0
    for i in range(1, 51):
        mod = modalities[i % len(modalities)]
        sex = sexes[i % len(sexes)]
        order = {
            "id": i, "patient_lastname": f"Paciente{i}", "patient_name": f"Nombre{i}",
            "patient_dni": str(32000000 + i),
            "patient_dob": date(1980 + (i % 30), (i % 12) + 1, (i % 28) + 1),
            "patient_sex": sex,
            "study_instance_uid": f"1.2.826.0.1.3680043.9.7134.{i}",
            "description": f"Estudio DICOM {mod} #{i}", "modality": mod,
            "order_date": date(2026, 9, 23),
        }
        ds = build_worklist_dataset(mapping_for(order))
        buf = io.BytesIO()
        pydicom.dcmwrite(buf, ds)
        buf.seek(0)
        read_ds = pydicom.dcmread(buf)
        sps = read_ds.ScheduledProcedureStepSequence[0]
        checks = {
            "name_ok": str(read_ds.PatientName) == f"{order['patient_lastname']}^{order['patient_name']}",
            "id_ok": str(read_ds.PatientID) == order["patient_dni"],
            "dob_ok": str(read_ds.PatientBirthDate) == order["patient_dob"].strftime("%Y%m%d"),
            "sex_ok": str(read_ds.PatientSex) == sex,
            "uid_ok": str(read_ds.StudyInstanceUID) == order["study_instance_uid"],
            "modality_ok": str(sps.Modality) == mod,
            "desc_ok": str(sps.ScheduledProcedureStepDescription) == order["description"],
        }
        total_checks += len(checks)
        discrepancies += sum(1 for ok in checks.values() if not ok)
        rows.append({"order_id": i, "patient_dni": order["patient_dni"], "modality": mod, **checks})

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        fields = ["order_id", "patient_dni", "modality", "name_ok", "id_ok", "dob_ok", "sex_ok", "uid_ok", "modality_ok", "desc_ok"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    tem = (discrepancies / total_checks) * 100.0
    print(f"Órdenes auditadas: {len(rows)}")
    print(f"Atributos evaluados: {total_checks}")
    print(f"Discrepancias: {discrepancies}")
    print(f"Tasa Error Mapeo (TEM): {tem:.2f} %")
    print(f"Resultado guardado en: {OUT_CSV}")
    return 0 if len(rows) == 50 and total_checks == 350 and discrepancies == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
