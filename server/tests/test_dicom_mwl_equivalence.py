"""Prueba de equivalencia DICOM MWL usando el serializador productivo."""
import io
from datetime import date, datetime

import pydicom
from app.core.orthanc_client import build_worklist_dataset
from app.modules.medical_order.model import Modality, Sex


class TestDicomWorklistEquivalence:
    def test_equivalencia_50_ordenes_tem_cero(self):
        modalities = [Modality.CT, Modality.MR, Modality.US, Modality.DX]
        sexes = [Sex.MALE, Sex.FEMALE, Sex.OTHER]
        discrepancies = 0
        total = 0
        for i in range(1, 51):
            mod = modalities[i % len(modalities)]
            sex = sexes[i % len(sexes)]
            sex_code = "M" if sex == Sex.MALE else ("F" if sex == Sex.FEMALE else "O")
            order_date = datetime(2026, 9, 23, 12, 0, 0)
            order = {
                "id": i, "patient_lastname": f"Perez{i}", "patient_name": f"Juan{i}",
                "patient_dni": str(30000000 + i),
                "patient_dob": date(1980 + (i % 30), (i % 12) + 1, (i % 28) + 1),
                "patient_sex": sex_code,
                "study_instance_uid": f"1.2.826.0.1.3680043.9.7134.{i}",
                "description": f"Estudio Protocolizado de {mod.value} Numero {i}",
                "modality": mod.value, "order_date": order_date,
            }
            mapping = {
                "0010,0010": f"{order['patient_lastname']}^{order['patient_name']}",
                "0010,0020": order["patient_dni"],
                "0010,0030": order["patient_dob"].strftime("%Y%m%d"),
                "0010,0040": sex_code, "0020,000D": order["study_instance_uid"],
                "0008,0050": f"ACC-{i}-20260923",
                "0040,0100": [{"0008,0060": mod.value, "0040,0001": f"AET_{mod.value}_1",
                                "0040,0002": "20260923", "0040,0003": "120000",
                                "0040,0007": order["description"]}],
            }
            ds = build_worklist_dataset(mapping)
            buf = io.BytesIO(); pydicom.dcmwrite(buf, ds); buf.seek(0)
            read_ds = pydicom.dcmread(buf); sps = read_ds.ScheduledProcedureStepSequence[0]
            checks = [
                str(read_ds.PatientName) == f"Perez{i}^Juan{i}",
                str(read_ds.PatientID) == order["patient_dni"],
                str(read_ds.PatientBirthDate) == order["patient_dob"].strftime("%Y%m%d"),
                str(read_ds.PatientSex) == sex_code, str(read_ds.StudyInstanceUID) == order["study_instance_uid"],
                str(sps.Modality) == mod.value, str(sps.ScheduledProcedureStepDescription) == order["description"],
            ]
            total += len(checks); discrepancies += sum(1 for ok in checks if not ok)
        assert total == 350
        assert discrepancies == 0
