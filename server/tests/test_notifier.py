import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.modules.medical_order.notifier import NotifierService

@pytest.mark.anyio
async def test_send_with_retry_exito_primer_intento():
    service = NotifierService(session=MagicMock())
    payload = {"patient_pseudonym": "abc123hash", "study": "TC"}

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success, error, attempts = await service._send_with_retry(payload, order_id=1, max_retries=3, backoff_base=0.01)
        assert success is True
        assert error is None
        assert attempts == 1
        assert mock_post.call_count == 1

@pytest.mark.anyio
async def test_send_with_retry_exito_en_reintento():
    service = NotifierService(session=MagicMock())
    payload = {"patient_pseudonym": "abc123hash", "study": "TC"}

    mock_fail = MagicMock()
    mock_fail.status_code = 502

    mock_success = MagicMock()
    mock_success.status_code = 200

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Primer intento falla con 502, segundo intento tiene éxito con 200
        mock_post.side_effect = [mock_fail, mock_success]
        success, error, attempts = await service._send_with_retry(payload, order_id=1, max_retries=3, backoff_base=0.01)
        assert success is True
        assert error is None
        assert attempts == 2
        assert mock_post.call_count == 2

@pytest.mark.anyio
async def test_send_with_retry_agota_reintentos():
    service = NotifierService(session=MagicMock())
    payload = {"patient_pseudonym": "abc123hash", "study": "TC"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        success, error, attempts = await service._send_with_retry(payload, order_id=1, max_retries=3, backoff_base=0.01)
        assert success is False
        assert "Connection refused" in error
        assert attempts == 3
        assert mock_post.call_count == 3
