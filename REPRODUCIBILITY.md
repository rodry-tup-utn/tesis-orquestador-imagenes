# Reproducibilidad y verificación de la entrega

Esta guía describe cómo reconstruir el artefacto y cómo interpretar la evidencia incluida en `benchmark/results/`. Los resultados se presentan con el alcance experimental declarado en la tesis y no deben interpretarse como validación clínica o de producción.

## Suite automatizada

La entrega contiene 101 pruebas automatizadas:

- 35 en `server/tests/test_triage_engine.py`;
- 6 en `server/tests/test_security.py`;
- 19 en `server/tests/test_privacy.py`;
- 33 en `server/tests/test_robustness.py`;
- 4 en `server/tests/test_contract.py`;
- 1 en `server/tests/test_dicom_mwl_equivalence.py`;
- 3 en `server/tests/test_notifier.py`.

El comando reproducible es:

```bash
cd server
python -m pytest tests -v
```

El recuento describe el artefacto. La ejecución completa requiere un entorno con las dependencias declaradas instaladas y, para los tests que acceden a infraestructura, el backend/servicios correspondientes.

## Regresión del motor

```bash
python benchmark/validate_motor.py
```

`benchmark/test_orders_regression.json` contiene 50 órdenes adicionales. Sus etiquetas esperadas se derivan de `calibrada_fase4.json`, por lo que la coincidencia 27/27 (100 %) documentada en la entrega acredita consistencia de la implementación con la especificación calibrada y no desempeño predictivo independiente.

## Evidencia cuantitativa incluida

### RNF-01 — Latencia de API

El archivo `benchmark/results/results_api_latency_2026-09-20.csv` contiene 600 observaciones: 200 por endpoint y todas con HTTP 200. Los P95, calculados con el método `inclusive` utilizado por `benchmark/api_latency.py`, son:

| Endpoint | n | Media | P95 |
|---|---:|---:|---:|
| `/orders?limit=10&offset=0` | 200 | 9,40 ms | 11,57 ms |
| `/orders/stats` | 200 | 12,30 ms | 16,08 ms |
| `/orders/notifications` | 200 | 7,44 ms | 10,36 ms |

La medición corresponde a un único cliente secuencial y no caracteriza carga concurrente ni disponibilidad sostenida.

### RF-04 — Actualización mediante WebSocket

`benchmark/results/results_ws_latency_2026-09-20.csv` contiene 10 corridas. Se obtuvo media de 43,64 ms, mediana de 26,71 ms, desviación estándar de 49,92 ms e intervalo de confianza del 95 % de [7,93; 79,34] ms. La medición corresponde a una conexión WebSocket y a carga secuencial.

### Equivalencia PostgreSQL ↔ DICOM Worklist

`benchmark/results/results_worklist_equivalence_2026-09-20.csv` contiene 20 órdenes. Se compararon 7 atributos por orden (140 atributos en total) y no se detectaron discrepancias. La métrica representa la tasa de error de mapeo de la muestra auditada: 0/140 = 0,00 %. No constituye garantía de interoperabilidad universal.

### TDCC

Los CSV históricos de TDCC se conservan en `benchmark/results/`. El script actual `benchmark/tdcc.py` incorpora la cabecera `X-Internal-API-Key`; no se presenta aquí una nueva corrida del script contra el stack actual como resultado de esta preparación.

## Verificación mecánica del Capítulo 6 (panel de 17 evaluadores)

`benchmark/verify_chapter6_panel.py` y `benchmark/stats.py` recalculan, a partir de dos CSV crudos incluidos en este ZIP
(`benchmark/panel_votos_50_ordenes.csv`, extraído literalmente de la Tabla 32 del Anexo V, y
`benchmark/motor_salida_fases_50_ordenes.csv`, extraído de la Tabla 33), sin depender de ninguna
cifra publicada en el texto:

- el patrón de referencia (moda de 17 evaluadores, empate → nivel más severo) y su coincidencia
  con la columna «Patrón» de la Tabla 32;
- la matriz de confusión y la coincidencia exacta del motor en la Fase 0 y en la Fase 4;
- el κ de Fleiss entre los 17 evaluadores;
- la concordancia individual de E02, E09 y E12 contra el motor (Fase 4) y contra el patrón
  reconstruido con los 14 evaluadores restantes — las dos cifras que la sección 6.9 reporta;
- la prueba de exclusión sistemática (17 iteraciones, un evaluador afuera por vez).

Ejecutar: `python benchmark/verify_chapter6_panel.py`. Reproduce exactamente 66,0 % (Fase 0),
78,0 % (Fase 4), κ de Fleiss ≈ 0,382, y las cifras individuales de E02/E09/E12 citadas en §6.9.
`VERIFY_DELIVERY.py` corre este script y falla si alguna cifra deja de coincidir. El verificador estadístico es deliberadamente independiente del backend y no requiere importar FastAPI, SQLModel ni PostgreSQL.

## Evidencia adicional ejecutada en esta entrega

La entrega conserva resultados de carga concurrente (`benchmark/results/load_suite/`), soak de API (`benchmark/results/soak_test/`), resiliencia (`benchmark/results/resilience/`), equivalencia DICOM extendida (`benchmark/results/results_worklist_equivalence_extended_2026-09-23.csv`), seguridad (`benchmark/results/security/`) y WebSocket extendido. Estas campañas caracterizan el artefacto bajo condiciones sintéticas y controladas.

## Instrumentos que continúan pendientes

`PROTOCOLOS_EVIDENCIA_ADICIONAL.md` mantiene el protocolo para la validación predictiva independiente (`benchmark/eval_independent.py`), la medición multi-operador del Escenario A (`scenario_a_timer.py`) y la prueba de usabilidad con usuarios (`sus_score.py`). No se ejecutaron porque requieren participación humana independiente.

## Notas de interpretación de las mediciones del 20/09/2026

- **RF-04 (`ws_latency.py`):** el instante final se toma cuando la petición de persistencia ya retornó y el backend emite el evento antes de responder; la cifra es una **cota superior** que incluye la duración completa de la ingesta y no aísla la propagación del evento.
- **Equivalencia BD ↔ worklist (`verify_worklist_mapping.py`):** el valor esperado proviene del servicio que genera el archivo; se comparan 7 atributos (no Accession Number, AET ni fecha/hora del paso).
- **RNF-01 (`api_latency.py`):** un solo cliente, secuencial, sobre una base de desarrollo con pocas órdenes.
- **`benchmark/results/diagnostico/results_tdcc_FAILED_2026-09-20.csv`:** corrida de TDCC del 20/09/2026 con estado `FAILED` (una fila). Se conserva como registro; no integra las series del Capítulo 5 y su causa no fue diagnosticada. La cadena de alertas con autenticación debe re-verificarse de extremo a extremo (procedimiento: `python benchmark/tdcc.py`).

## Scripts de análisis

- `benchmark/analyze_results.py`: análisis descriptivo de T_proc, TDCC y, cuando está disponible, la medición de latencia HTTP de RNF-01.
- `benchmark/api_latency.py`: medición de latencia HTTP y P95.
- `benchmark/ws_latency.py`: medición de latencia WebSocket e IC 95 %.
- `benchmark/verify_worklist_mapping.py`: comprobación de equivalencia de atributos entre datos persistidos y DICOM Worklist.
- `benchmark/validate_motor.py`: prueba de regresión del motor sobre el conjunto adicional.

## Prácticas DevSecOps

El repositorio conserva los comandos previstos para análisis de dependencias, análisis estático y cobertura, pero **no se presentan como resultados cuantitativos auditados de esta entrega**. Cualquier cifra de cobertura o de vulnerabilidades debe considerarse válida únicamente si se vuelve a ejecutar en el entorno fijado y se conserva el informe correspondiente.

## Seguridad del MVP

- El tablero requiere JWT emitido por `POST /auth/login`.
- La ingesta máquina-a-máquina desde n8n requiere `X-Internal-API-Key`.
- El backend autentica las llamadas al webhook interno de alertas mediante `X-Alert-API-Key`.
- El seudónimo de paciente se calcula en el backend mediante HMAC-SHA256 con `PSEUDONYM_SECRET`; el mismo valor se persiste y se reutiliza en la alerta.
- Las credenciales y secretos se suministran por variables de entorno.
- n8n lee `INTERNAL_API_KEY`, `ALERT_WEBHOOK_KEY` y `TELEGRAM_CHAT_ID` mediante `$env`; el `docker-compose.yml` fija `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` porque la configuración actual de los flujos depende de ese acceso. Para un piloto conviene migrarlas a credenciales gestionadas por n8n.
- El JWT se almacena en `localStorage` en el MVP; para producción se recomienda una estrategia basada en cookie `HttpOnly` y controles adicionales contra XSS.

## Ejecución del entorno

1. Copiar `.env.example` a `.env` y completar los secretos.
2. Levantar el stack con Docker Compose. PostgreSQL dispone de un healthcheck y el backend espera `service_healthy` antes de ejecutar las migraciones.
3. Importar y activar los workflows de `n8n-workflow/`.
4. Ejecutar las mediciones que correspondan y conservar sus CSV junto con la fecha y configuración utilizada.

La validación de disponibilidad del servicio DICOM ≥ 99 % en horario operativo, el RBAC institucional, la configuración de TLS/proxy y la validación clínica independiente permanecen fuera del alcance de este MVP. La API sí cuenta con una campaña de soak sostenido y la carga concurrente fue caracterizada experimentalmente.
