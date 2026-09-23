## Resultados del Test de Carga Concurrente

**Fecha:** 2026-09-23  
**Backend:** http://localhost:8000  
**Solicitudes por cliente por nivel:** 100  

| Clientes | Total req | Exitosas | Fallidas | Error % | P50 (ms) | P95 (ms) | P99 (ms) | Throughput (req/s) | RNF-01 P95<500ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 100 | 100 | 0 | 0.0 | 13.12 | 18.23 | 21.07 | 73.89 | ✓ |
| 5 | 500 | 500 | 0 | 0.0 | 57.75 | 105.35 | 208.7 | 77.82 | ✓ |
| 10 | 1000 | 1000 | 0 | 0.0 | 124.81 | 310.4 | 478.18 | 66.65 | ✓ |
| 25 | 2500 | 2042 | 458 | 18.32 | 373.01 | 827.15 | 1252.17 | 70.4 | ✗ |
| 50 | 5000 | 0 | 5000 | 100.0 | N/D | N/D | N/D | 815.52 | ✗ |

**Interpretación:** La disponibilidad reportada corresponde a la API bajo carga sintética de lectura bajo las condiciones experimentales definidas. No incluye Orthanc ni n8n y no caracteriza carga clínica real.
