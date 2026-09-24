# Reporte de Soak Test Extendido de la API (Estabilidad sostenida)

**Fecha de ejecución:** 23 de septiembre de 2026
**Duración continua:** > 3.5 horas de operación ininterrumpida
**Intervalo de muestreo:** 30 segundos (3 peticiones por ciclo a endpoints de lectura: `/orders`, `/orders/stats`, `/orders/notifications`)
**Conjunto de datos crudo:** `benchmark/results/soak_test/raw/soak_2026-09-23_1540.csv`

---

## 1. Métricas Globales de Estabilidad Observada

| Métrica | Valor Medido | Criterio RNF-02 | Estado |
| :--- | :--- | :--- | :--- |
| **Peticiones Totales (N)** | 1.254 peticiones | Ventana prolongada | **OBSERVADO** |
| **Respuestas Exitosas (HTTP 200)** | 1.254 (100,00 %) | Descriptivo | **OBSERVADO** |
| **Tasa de Error** | 0,00 % (0 fallos) | Descriptivo | **OBSERVADO** |
| **Latencia Media** | 13,68 ms | Descriptivo | **OBSERVADO** |
| **Latencia Mediana (P50)** | 11,52 ms | Descriptivo | **OBSERVADO** |
| **Percentil 95 (P95)** | 20,47 ms | Descriptivo | **OBSERVADO** |
| **Percentil 99 (P99)** | 63,29 ms | Descriptivo | **OBSERVADO** |
| **Peor Latencia Registrada** | 876,08 ms | Descriptivo | **OBSERVADO** |

---

## 2. Análisis Exploratorio de Deriva Temporal (Drift Analysis)

Para explorar una posible degradación temporal de la respuesta, se dividió la serie en dos mitades cronológicas de igual tamaño (N=627). Esta comparación no constituye una medición directa de memoria, descriptores ni fugas de recursos:

| Segmento Temporal | Latencia Media | Percentil 95 (P95) | % Éxito |
| :--- | :--- | :--- | :--- |
| **Primera Mitad (0 a 1,75 h)** | 13,26 ms | 21,05 ms | 100,00 % |
| **Segunda Mitad (1,75 a 3,5 h)** | 14,10 ms | 19,00 ms | 100,00 % |

**Conclusión:** la latencia observada no muestra una deriva temporal evidente durante la campaña: la media pasó de 13,26 ms a 14,10 ms y el P95 de 21,05 ms a 19,00 ms. Esta evidencia caracteriza estabilidad de respuesta de los endpoints ensayados. No se midió directamente el consumo de memoria ni el número de conexiones durante toda la campaña, por lo que no se afirma la ausencia de fugas de memoria ni la liberación completa de recursos. El ensayo tampoco acredita por sí solo la disponibilidad del servicio DICOM requerida por RNF-02.
