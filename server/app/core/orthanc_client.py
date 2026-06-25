import httpx
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class OrthancClient:
    """
    Cliente HTTP para comunicarse con la API REST de Orthanc.
    """
    def __init__(self):
        self.base_url = settings.orthanc_url
        self.username = settings.orthanc_user
        self.password = settings.orthanc_password

    async def create_worklist(self, dicom_data: Dict[str, Any]) -> bool:
        """
        Envía un payload DICOM JSON al endpoint de Worklists de Orthanc.
        """
        url = f"{self.base_url}/worklists"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=dicom_data,
                    auth=(self.username, self.password),
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info("Worklist DICOM enviada correctamente a Orthanc")
                return True
            except httpx.HTTPStatusError as exc:
                logger.error(f"Error HTTP al crear worklist: {exc.response.status_code} - {exc.response.text}")
                return False
            except Exception as e:
                logger.error(f"Error de conexión con Orthanc: {str(e)}")
                return False
