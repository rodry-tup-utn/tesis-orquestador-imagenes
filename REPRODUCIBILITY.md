# Reproducibilidad de la entrega

## Alcance

Este paquete contiene el código del MVP y los artefactos de prueba que forman parte de la entrega de software. La prueba de `benchmark/validate_motor.py` es una **regresión de consistencia**, no una validación predictiva independiente: las etiquetas esperadas del conjunto adicional se derivan de la configuración calibrada.

## Pruebas automatizadas

- `server/tests/test_triage_engine.py`: 34 pruebas del motor de triaje.
- `server/tests/test_security.py`: 6 pruebas de autenticación y seudonimización (incluye una regresión: credenciales con caracteres no ASCII deben dar 401 y no 500).
- Ejecución de control de la entrega: **40 passed** (34 + 6).

## Regresión del motor

- Archivo: `benchmark/test_orders_regression.json`.
- Casos: 27 órdenes sintéticas.
- Resultado de control: **27/27 (100 %)**.
- Distribución de etiquetas esperadas: 8 Crítico, 9 Urgente, 2 Prioritario y 8 Rutina.
- Esta prueba no demuestra desempeño predictivo frente a una referencia profesional independiente.

## Mediciones cuantitativas de rendimiento y verificación (RNF-01, RF-04, TET)

- **RNF-01 (Latencia en el límite de la API):** `benchmark/api_latency.py` mide el tiempo de respuesta HTTP con cliente autenticado vía JWT sobre 200 peticiones por endpoint. Resultados medidos:
  - `/orders?limit=10&offset=0`: P95 = 11,57 ms (media 9,40 ms).
  - `/orders/stats`: P95 = 16,08 ms (media 12,30 ms).
  - `/orders/notifications`: P95 = 10,36 ms (media 7,44 ms).
  - En todos los casos se satisface holgadamente el requisito (< 500 ms).
- **RF-04 (Latencia de difusión WebSocket):** `benchmark/ws_latency.py` mide la latencia extremo a extremo entre el commit en la API y la recepción del evento `orders_updated` en el cliente WebSocket.
  - 10 ensayos: media = 43,64 ms (mediana 26,71 ms; IC 95% Student-t [7,93; 79,34] ms).
- **Equivalencia BD ↔ DICOM Worklist (TET):** `benchmark/verify_worklist_mapping.py` audita 140 atributos mandatorios con `pydicom` en archivos `.wl` generados en `/worklists` contrastados contra PostgreSQL.
  - Resultados: 0 discrepancias sobre 20 órdenes; Tasa de Error de Mapeo (TET) = 0,00 %.
- **TDCC (Detección de caso crítico):** `benchmark/tdcc.py` envía `X-Internal-API-Key` (`INTERNAL_API_KEY` del `.env`). Probado contra el backend en ejecución sin errores 401.

## Prácticas DevSecOps (Definition of Done)

- **Cobertura de código:** `docker compose run --rm backend pytest tests --cov=app/modules/triage` (98 % de cobertura en el motor de triaje).
- **Análisis estático de seguridad:** `docker compose run --rm backend bandit -r app` (0 vulnerabilidades de severidad Alta o Media).
- **Auditoría de dependencias Python:** `docker compose run --rm backend pip-audit` (0 vulnerabilidades en paquetes de producción).
- **Auditoría de frontend:** `docker compose run --rm frontend npm audit` (0 vulnerabilidades críticas; dependencias de desarrollo documentadas).

## Seguridad del MVP

- El tablero requiere JWT emitido por `POST /auth/login`.
- La ingesta máquina-a-máquina desde n8n requiere `X-Internal-API-Key`.
- El backend autentica las llamadas al webhook interno de alertas mediante `X-Alert-API-Key`.
- El seudónimo de paciente se calcula en el backend mediante HMAC-SHA256 con `PSEUDONYM_SECRET`; el mismo valor se persiste y se reutiliza en la alerta.
- Las credenciales y secretos se suministran por variables de entorno.
- n8n lee `INTERNAL_API_KEY`, `ALERT_WEBHOOK_KEY` y `TELEGRAM_CHAT_ID` con `$env`; `docker-compose.yml` fija `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` porque las versiones recientes de n8n bloquean ese acceso por defecto. Para un piloto conviene migrarlas a credenciales de n8n.
- El JWT se guarda en `localStorage` del navegador (aceptable en el MVP; en producción se recomienda cookie HttpOnly).

## Ejecución local resumida

1. Copiar `.env.example` a `.env` y definir `SECRET_KEY`, `PSEUDONYM_SECRET`, `AUTH_PASSWORD`, `INTERNAL_API_KEY`, `ALERT_WEBHOOK_KEY` y `TELEGRAM_CHAT_ID`.
2. Levantar el stack con Docker Compose.
3. Obtener un JWT en `POST /auth/login`.
4. Usar el token como `Authorization: Bearer <token>` para los endpoints del tablero.
5. Ejecutar `pytest server/tests` para la suite y `python benchmark/validate_motor.py` para la regresión.
6. Antes de la defensa, levantar el stack desde cero y comprobar que n8n acepta `$env` (ingesta y alerta).

La disponibilidad sostenida, el control de acceso institucional/RBAC, el despliegue productivo del frontend y la validación clínica independiente permanecen fuera del alcance de este MVP académico.
