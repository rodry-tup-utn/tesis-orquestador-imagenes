# Ejecución reproducible de la suite

Desde la raíz del repositorio:

```bash
python -m pytest server/tests -v
```

`conftest.py` define valores de prueba mediante `os.environ.setdefault`, por lo que una configuración externa válida mantiene prioridad y no es necesario crear un archivo `.env` para ejecutar las pruebas. Las seis variables que impedían la recolección completa en la revisión auditada quedan cubiertas por valores de prueba: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `PSEUDONYM_SECRET` y `AUTH_PASSWORD`. También se proveen valores de prueba para `AUTH_USERNAME`, `INTERNAL_API_KEY` y `ALERT_WEBHOOK_KEY`.

Las dependencias utilizadas por la suite están fijadas en `server/requirements.lock`. La ejecución de estas pruebas no requiere levantar PostgreSQL, n8n ni Orthanc. Las campañas de carga, estabilidad y resiliencia requieren el entorno desplegado y se mantienen fuera de esta suite.
