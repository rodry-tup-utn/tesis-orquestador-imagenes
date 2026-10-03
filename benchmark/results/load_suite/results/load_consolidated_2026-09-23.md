## Resultados del Test de Carga Concurrente

**Fecha:** 2026-09-23  
**Backend:** http://localhost:8000  
**Solicitudes por cliente por nivel:** 100

| Clientes | Total req | Exitosas | Fallidas | Error % | P50 (ms) | P95 (ms) | P99 (ms) | Ritmo observado (req/s) | RNF-01 P95<500ms | Interpretación para capacidad |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---|
| 1 | 100 | 100 | 0 | 0.0 | 13.12 | 18.23 | 21.07 | 73.89 | ✓ | interpretable |
| 5 | 500 | 500 | 0 | 0.0 | 57.75 | 105.35 | 208.70 | 77.82 | ✓ | interpretable |
| 10 | 1000 | 1000 | 0 | 0.0 | 124.81 | 310.40 | 478.18 | 66.65 | ✓ | interpretable |
| 25 | 2500 | 2042 | 458 | 18.32 | 373.01 | 827.15 | 1252.17 | 70.40 | ✗ | no interpretable como límite de carga |
| 50 | 5000 | 0 | 5000 | 100.0 | N/D | N/D | N/D | 815.52 | ✗ | no interpretable como límite de carga |

**Alcance e interpretación.** Los registros crudos de 25 y 50 clientes se conservan íntegramente. En la reconstrucción temporal de la campaña se observó superposición con el escenario de resiliencia que reinicia el backend; por ello, los errores de esos dos niveles no se atribuyen causalmente a la carga ni se emplean para fijar límites operativos. En 25 clientes, el P95 de 827,15 ms corresponde exclusivamente a las 2.042 solicitudes exitosas anteriores a la interrupción. Los niveles de 1, 5 y 10 clientes son los puntos de carga que permanecen interpretables dentro de esta campaña.
