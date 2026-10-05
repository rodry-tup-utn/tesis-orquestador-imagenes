import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-32-bytes-minimum!!")
os.environ.setdefault("PSEUDONYM_SECRET", "test-pseudonym-secret")
os.environ.setdefault("AUTH_USERNAME", "admin")
os.environ.setdefault("AUTH_PASSWORD", "clave-de-prueba")
os.environ.setdefault("INTERNAL_API_KEY", "api-key-de-prueba")

from app.core.config import settings
from app.core.security import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    derive_patient_pseudonym,
)


def test_login_credentials_correctas():
    assert authenticate_user(settings.auth_username, settings.auth_password) is True


def test_login_credentials_incorrectas():
    assert authenticate_user(settings.auth_username, "incorrecta_inexistente") is False


def test_jwt_se_expide_y_se_decodifica():
    token = create_access_token({"sub": "admin", "role": "mvp-admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["type"] == "access"


def test_pseudonimo_es_estable_y_normaliza_formato_dni():
    a = derive_patient_pseudonym("20.123.456")
    b = derive_patient_pseudonym("20123456")
    assert a == b
    assert len(a) == 64


def test_pseudonimos_difieren_por_dni():
    assert derive_patient_pseudonym("20123456") != derive_patient_pseudonym("20123457")


def test_credenciales_no_ascii_devuelven_false_y_no_excepcion():
    # Regresion: secrets.compare_digest con str no ASCII lanza TypeError (500 en la API).
    assert authenticate_user(settings.auth_username, "contraseña_invalida_no_ascii") is False
    assert authenticate_user(settings.auth_username + "ñ", settings.auth_password) is False
