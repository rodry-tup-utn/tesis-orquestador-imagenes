import logging
import os
import uuid
from typing import Any, Dict

import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian

logger = logging.getLogger(__name__)


def build_worklist_dataset(dicom_data: Dict[str, Any]) -> FileDataset:
    """Build a DICOM Modality Worklist dataset using the production mapping."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.31"
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    for tag_str, value in dicom_data.items():
        tag = pydicom.tag.Tag(tag_str.split(','))
        vr = pydicom.datadict.dictionary_VR(tag)
        if isinstance(value, list):
            seq = Sequence()
            for item_dict in value:
                item_ds = Dataset()
                for t_str, item_value in item_dict.items():
                    item_tag = pydicom.tag.Tag(t_str.split(','))
                    item_vr = pydicom.datadict.dictionary_VR(item_tag)
                    item_ds.add_new(item_tag, item_vr, str(item_value))
                seq.append(item_ds)
            ds.add_new(tag, 'SQ', seq)
        else:
            ds.add_new(tag, vr, str(value))
    return ds


class OrthancClient:
    """Cliente para generar localmente archivos DICOM de Modality Worklist."""

    async def create_worklist(self, dicom_data: Dict[str, Any]) -> bool:
        try:
            ds = build_worklist_dataset(dicom_data)
            os.makedirs("/worklists", exist_ok=True)
            file_name = f"/worklists/{uuid.uuid4().hex}.wl"
            pydicom.dcmwrite(file_name, ds)
            logger.info("Worklist generada y guardada correctamente: %s", file_name)
            return True
        except Exception as exc:
            logger.error("Error al generar worklist para Orthanc: %s", exc)
            return False
