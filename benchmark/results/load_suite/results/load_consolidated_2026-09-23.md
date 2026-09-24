## Resultados del Test de Carga Concurrente

**Fecha:** 2026-09-23  
**Backend:** http://localhost:8000  
**Solicitudes por cliente por nivel:** 100  

| Clientes | Total req | Exitosas | Fallidas | Error % | P50 (ms) | P95 (ms) | P99 (ms) | Ritmo observado (req/s) | RNF-01 P95<500ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 100 | 100 | 0 | 0.0 | 13.12 | 18.23 | 21.07 | 73.89 | ✓ |
| 5 | 500 | 500 | 0 | 0.0 | 57.75 | 105.35 | 208.7 | 77.82 | ✓ |
| 10 | 1000 | 1000 | 0 | 0.0 | 124.81 | 310.4 | 478.18 | 66.65 | ✓ |
| 25 | 2500 | 2042 | 458 | 18.32 | 373.01 | 827.15 | 1252.17 | 70.4 | ✗ |
| 50 | 5000 | 0 | 5000 | 100.0 | N/D | N/D | N/D | 815.52 | ✗ |

**Interpretación:** la campaña caracteriza el comportamiento de la API frente a cinco niveles de concurrencia sintética. El ritmo observado incluye todas las solicitudes intentadas y no debe interpretarse como throughput de operaciones exitosas. A 1, 5 y 10 clientes se obtuvieron 0 % de error; a 25 clientes se observó 18,32 % de error y a 50 clientes fallaron 5.000 de 5.000 solicitudes. El ensayo no caracteriza capacidad hospitalaria ni permite extrapolar los resultados a producción.
