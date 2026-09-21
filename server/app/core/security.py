"""Autenticacion JWT y seudonimizacion HMAC del MVP."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def _safe_equal(a: str, b: str) -> bool:
    """Compara dos cadenas en tiempo constante.

    secrets.compare_digest lanza TypeError con str no ASCII (p. ej. «contraseña»);
    se comparan los bytes UTF-8 para que una credencial con tilde o «ñ» dé 401 y no 500.
    """
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def verify_password(plain_password: str, expected_password: str) -> bool:
    """Compara credenciales de forma constante; el secreto vive en el entorno."""
    if not expected_password:
        return False
    return _safe_equal(plain_password, expected_password)


def create_access_token(payload: dict) -> str:
    """Crea un JWT con expiracion UTC y tipo de token explicito."""
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": int(expire.timestamp()), "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "access" or not payload.get("sub"):
            return None
        return payload
    except PyJWTError:
        return None


def authenticate_user(username: str, password: str) -> bool:
    """Autentica el unico usuario del MVP mediante credenciales de entorno."""
    return _safe_equal(username, settings.auth_username) and verify_password(
        password, settings.auth_password
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticacion Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_ingestion_key(
    x_internal_api_key: str | None = Header(default=None, alias="X-Internal-API-Key"),
) -> None:
    """Autentica la ingesta maquina-a-maquina de n8n hacia FastAPI."""
    configured = settings.internal_api_key
    if not configured or x_internal_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere la credencial interna de ingesta",
        )
    if not _safe_equal(x_internal_api_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial interna invalida",
        )


def derive_patient_pseudonym(dni: str) -> str:
    """Genera un pseudonimo estable con HMAC-SHA256 usando una clave separada."""
    canonical_dni = re_digits(dni)
    key = settings.pseudonym_secret.encode("utf-8")
    return hmac.new(key, canonical_dni.encode("utf-8"), hashlib.sha256).hexdigest()


def re_digits(value: str) -> str:
    """Normaliza el DNI para que separadores de formato no cambien el pseudonimo."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or value.strip()
