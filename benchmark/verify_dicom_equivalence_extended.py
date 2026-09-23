#!/usr/bin/env python3
"""Verificación formal de equivalencia DICOM Modality Worklist (.wl) - Campaña Extendida N=50.

Audita 50 órdenes sintéticas representativas de todas las modalidades (CT, MR, US, DX)
y sexos (M, F, O) verificando 7 atributos DICOM por orden (350 atributos en total)
contra la serialización binaria PS 3.4.

Salida:
    benchmark/results/results_worklist_equivalence_extended_<fecha>.csv
"""
import csv
import io
import os
import sys
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from datetime import date

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(BENCHMARK_DIR, "results", "results_worklist_equivalence_extended_2026-09-23.csv")


def build_dicom_dataset(order_dict: dict) -> FileDataset:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.31"
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    dicom_json = {
        "0010,0010": f"{order_dict['patient_lastname']}^{order_dict['patient_name']}",
        "0010,0020": str(order_dict["patient_dni"]),
        "0010,0030": order_dict["patient_dob"].strftime("%Y%m%d"),
        "0010,0040": order_dict["patient_sex"],
        "0020,000D": order_dict["study_instance_uid"],
        "0008,0050": f"ACC-{order_dict['id']}-20260923",
        "0040,0100": [{
            "0008,0060": order_dict["modality"],
            "0040,0001": f"AET_{order_dict['modality']}_1",
            "0040,0002": "20260923",
            "0040,0003": "120000",
            "0040,0007": order_dict["description"],
        }]
    }

    for tag_str, value in dicom_json.items():
        tag = pydicom.tag.Tag(tag_str.split(","))
        vr = pydicom.datadict.dictionary_VR(tag)
        if isinstance(value, list):
            seq = Sequence()
            for item_dict in value:
                item_ds = Dataset()
                for t_str, v in item_dict.items():
                    t = pydicom.tag.Tag(t_str.split(","))
                    item_vr = pydicom.datadict.dictionary_VR(t)
                    item_ds.add_new(t, item_vr, str(v))
                seq.append(item_ds)
            ds.add_new(tag, "SQ", seq)
        else:
            ds.add_new(tag, vr, str(value))

    return ds


def main():
    modalities = ["CT", "MR", "US", "DX"]
    sexes = ["M", "F", "O"]

    rows = []
    total_checks = 0
    discrepancies = 0

    for i in range(1, 51):
        mod = modalities[i % len(modalities)]
        sex = sexes[i % len(sexes)]
        order = {
            "id": i,
            "patient_lastname": f"Paciente{i}",
            "patient_name": f"Nombre{i}",
            "patient_dni": str(32000000 + i),
            "patient_dob": date(1980 + (i % 30), (i % 12) + 1, (i % 28) + 1),
            "patient_sex": sex,
            "study_instance_uid": f"1.2.826.0.1.3680043.9.7134.{i}",
            "description": f"Estudio DICOM {mod} #{i}",
            "modality": mod,
        }

        ds = build_dicom_dataset(order)
        buf = io.BytesIO()
        pydicom.dcmwrite(buf, ds)
        buf.seek(0)
        read_ds = pydicom.dcmread(buf)

        name_ok = str(read_ds.PatientName) == f"{order['patient_lastname']}^{order['patient_name']}"
        id_ok = str(read_ds.PatientID) == order["patient_dni"]
        dob_ok = str(read_ds.PatientBirthDate) == order["patient_dob"].strftime("%Y%m%d")
        sex_ok = str(read_ds.PatientSex) == sex
        uid_ok = str(read_ds.StudyInstanceUID) == order["study_instance_uid"]

        sps = read_ds.ScheduledProcedureStepSequence[0]
        mod_ok = str(sps.Modality) == mod
        desc_ok = str(sps.ScheduledProcedureStepDescription) == order["description"]

        checks = [name_ok, id_ok, dob_ok, sex_ok, uid_ok, mod_ok, desc_ok]
        total_checks += len(checks)
        discrepancies += sum(1 for c in checks if not c)

        rows.append({
            "order_id": i,
            "patient_dni": order["patient_dni"],
            "modality": mod,
            "name_ok": name_ok,
            "id_ok": id_ok,
            "dob_ok": dob_ok,
            "sex_ok": sex_ok,
            "uid_ok": uid_ok,
            "modality_ok": mod_ok,
            "desc_ok": desc_ok,
        })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "order_id", "patient_dni", "modality",
            "name_ok", "id_ok", "dob_ok", "sex_ok", "uid_ok", "modality_ok", "desc_ok"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    tem = (discrepancies / total_checks) * 100.0
    print("=" * 65)
    print("  VERIFICACIÓN DE EQUIVALENCIA DICOM MWL EXTENDIDA (N=50)")
    print("=" * 65)
    print(f"  Órdenes auditadas:     {len(rows)}")
    print(f"  Atributos evaluados:   {total_checks}")
    print(f"  Discrepancias:         {discrepancies}")
    print(f"  Tasa Error Mapeo (TEM):{tem:.2f} %")
    print(f"  Resultado guardado en: {OUT_CSV}")
    print("=" * 65)


if __name__ == "__main__":
    main()
