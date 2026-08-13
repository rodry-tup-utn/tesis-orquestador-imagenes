import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
import logging
import os
import uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OrthancClient:
    """
    Cliente para comunicarse con Orthanc y gestionar Worklists localmente.
    """
    def __init__(self):
        pass

    async def create_worklist(self, dicom_data: Dict[str, Any]) -> bool:
        """
        Genera un archivo DICOM de worklist usando pydicom y lo guarda en la carpeta monitoreada.
        """
        try:
            ds = Dataset()
            ds.is_little_endian = True
            ds.is_implicit_VR = True
            
            for tag_str, value in dicom_data.items():
                tag = pydicom.tag.Tag(tag_str.split(','))
                vr = pydicom.datadict.dictionary_VR(tag)
                
                if isinstance(value, list):
                    seq = Sequence()
                    for item_dict in value:
                        item_ds = Dataset()
                        for t_str, v in item_dict.items():
                            t = pydicom.tag.Tag(t_str.split(','))
                            item_vr = pydicom.datadict.dictionary_VR(t)
                            item_ds.add_new(t, item_vr, str(v))
                        seq.append(item_ds)
                    ds.add_new(tag, 'SQ', seq)
                else:
                    ds.add_new(tag, vr, str(value))
                    
            os.makedirs("/worklists", exist_ok=True)
            file_name = f"/worklists/{uuid.uuid4().hex}.wl"
            pydicom.dcmwrite(file_name, ds, write_like_original=True)
            logger.info(f"Worklist generada y guardada correctamente: {file_name}")
            return True
        except Exception as e:
            logger.error(f"Error al generar worklist para Orthanc: {str(e)}")
            return False
