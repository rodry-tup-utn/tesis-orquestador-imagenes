# Resumen de verificación — entrega de defensa

## Identificación
- Artefacto: Middleware de Orquestación y Triaje para Diagnóstico por Imágenes.
- Fecha de las mediciones adicionales: 2026-09-20.
- La identificación criptográfica del ZIP definitivo se consigna en la tesis una vez congelado el paquete final.

## Evidencia incluida

| Evidencia | Archivo | Resultado | Alcance |
|---|---|---|---|
| RNF-01 | `benchmark/results/results_api_latency_2026-09-20.csv` | 600 requests; P95 11,57 / 16,08 / 10,36 ms; HTTP 200 en todas | Cliente único, secuencial |
| RF-04 | `benchmark/results/results_ws_latency_2026-09-20.csv` | n=10; media 43,64 ms; mediana 26,71 ms; IC 95 % [7,93; 79,34] ms | Una conexión WebSocket, secuencial |
| BD ↔ DICOM | `benchmark/results/results_worklist_equivalence_2026-09-20.csv` | 0/140 discrepancias | 20 órdenes auditadas |
| Regresión | `benchmark/test_orders_regression.json` + `benchmark/validate_motor.py` | 27/27 coincidencias | Consistencia contra reglas calibradas; no validación predictiva independiente |
| Suite | `server/tests/test_triage_engine.py` + `server/tests/test_security.py` | 34 + 6 = 40 pruebas presentes | El paquete no afirma que se hayan ejecutado durante su preparación |
| Privacidad de alertas | `server/app/modules/medical_order/notifier.py` + `n8n-workflow/Alertas Criticas.json` | payload externo por pseudónimo; sin nombre/DNI | Verificación estructural incorporada en `VERIFY_DELIVERY.py` |

## Límites

No se presenta evidencia de concurrencia, disponibilidad sostenida, validación clínica independiente o usabilidad con usuarios finales externos. Estas limitaciones permanecen explícitas en la tesis para evitar sobreinterpretar los resultados.
