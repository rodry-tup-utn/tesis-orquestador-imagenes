# Resumen de verificación — entrega de defensa

## Identificación
- Artefacto: Middleware de Orquestación y Triaje para Diagnóstico por Imágenes.
- Evidencia técnica adicional: campañas conservadas en `benchmark/results/`.
- La versión evaluada se conserva en la rama `tesis-v10.6-reparada` y la versión final de entrega corresponde a la rama `tesis-v10.7`.

## Evidencia incluida

| Evidencia | Archivo | Resultado | Alcance |
|---|---|---|---|
| RNF-01 | `benchmark/results/results_api_latency_2026-09-20.csv` | 600 requests; P95 11,57 / 16,08 / 10,36 ms; 200 en todas | Cliente único, secuencial |
| RF-04/WebSocket | `benchmark/results/results_ws_latency_extended_n50_2026-09-23.csv` | N=50; media 19,56 ms; P50 18,37; P95 27,55; P99 35,00 ms | Una conexión, secuencial |
| BD ↔ DICOM | `benchmark/results/results_worklist_equivalence_2026-09-20.csv` | 0/140 discrepancias | 20 órdenes |
| DICOM extendido | `benchmark/results/results_worklist_equivalence_extended_2026-09-23.csv` | 0/350 discrepancias | 50 órdenes sintéticas; serializador productivo |
| Regresión | `benchmark/test_orders_regression.json` | 50/50 coincidencias | Consistencia contra reglas calibradas; no validación predictiva independiente |
| Suite | `server/tests/test_*.py` | 101 tests estructurados | 35 motor, 6 seguridad, 19 privacidad, 33 robustez, 4 contrato, 1 DICOM, 3 notificador |
| Carga concurrente | `benchmark/results/load_suite/results/load_consolidated_2026-09-23.json` | 1/5/10: 0 % error; 25/50 conservados con incidencia de reinicio | Los niveles de 25/50 no se usan para establecer límites de carga |
| Soak API | `benchmark/results/soak_test/raw/soak_2026-09-23_1540.csv` | 4,3 h; 516 ciclos; 1.548/1.548 HTTP 200; media 13,32; P95 20,08; P99 57,89 ms | Estabilidad de API; no disponibilidad DICOM ni memoria. El reporte JSON/MD conservado es un corte parcial de 1.254 registros. |
| Resiliencia | `benchmark/results/resilience/raw/resilience_2026-09-23_1529.json` | 3 PASS; 0 FAIL; 2 NO EJECUTADOS | Los no ejecutados no cuentan como éxitos |
| Seguridad | CI / reportes conservados | Bandit y pip-audit configurados para la entrega | `pip-audit` usa `server/requirements.lock` |

## Reconciliación del soak

El archivo `benchmark/results/soak_test_report_extended_2026-09-23.json` corresponde a un corte parcial de la serie histórica y conserva sus cifras originales (1.254 solicitudes; P95 20,47 ms). Para la entrega final, las cifras declaradas en la tesis y en este resumen se recalculan sobre el CSV crudo completo `benchmark/results/soak_test/raw/soak_2026-09-23_1540.csv` (1.548 solicitudes; P95 20,08 ms). No se modifica el artefacto histórico para evitar alterar la evidencia original.

## Límites
La validación predictiva independiente con referencia profesional nueva, la evaluación de usabilidad con participantes externos y la validación clínica/operacional real permanecen fuera del alcance. RNF-02 no se presenta como plenamente verificado: el soak caracteriza estabilidad de la API, no disponibilidad sostenida del servicio DICOM.
