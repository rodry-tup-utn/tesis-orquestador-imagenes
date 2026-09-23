# Reporte de Soak Test Extendido (Disponibilidad y Estabilidad RNF-02)

**Fecha de ejecución:** 23 de septiembre de 2026  
**Duración continua:** > 3.5 horas de operación ininterrumpida  
**Intervalo de muestreo:** 30 segundos (3 peticiones por ciclo a endpoints críticos: `/orders`, `/orders/stats`, `/orders/notifications`)  
**Conjunto de datos crudo:** `benchmark/results/soak_test/raw/soak_2026-09-23_1540.csv`

---

## 1. Métricas Globales de Estabilidad y Disponibilidad

| Métrica | Valor Medido | Criterio RNF-02 | Estado |
| :--- | :--- | :--- | :--- |
| **Peticiones Totales (N)** | 1.254 peticiones | Ventana prolongada | **CUMPLIDO** |
| **Respuestas Exitosas (HTTP 200)** | 1.254 (100,00 %) | > 99,50 % | **SUPERADO** |
| **Tasa de Error** | 0,00 % (0 fallos) | < 0,50 % | **ÓPTIMO** |
| **Latencia Media** | 13,68 ms | Sub-segundo (< 1000 ms) | **SUPERADO** |
| **Latencia Mediana (P50)** | 11,52 ms | Sub-segundo | **SUPERADO** |
| **Percentil 95 (P95)** | 20,47 ms | Sub-segundo | **SUPERADO** |
| **Percentil 99 (P99)** | 63,29 ms | Sub-segundo | **SUPERADO** |
| **Peor Latencia Registrada** | 876,08 ms | < 1000 ms | **CUMPLIDO** |

---

## 2. Análisis de Deriva y Fugas de Memoria (Drift Analysis)

Para verificar la ausencia de fugas de memoria (*memory leaks*) o degradación por acumulación de descriptores o conexiones residuales de WebSocket/PostgreSQL, se dividió la serie temporal en dos mitades cronológicas de igual tamaño (N=627):

| Segmento Temporal | Latencia Media | Percentil 95 (P95) | % Éxito |
| :--- | :--- | :--- | :--- |
| **Primera Mitad (0 a 1,75 h)** | 13,26 ms | 21,05 ms | 100,00 % |
| **Segunda Mitad (1,75 a 3,5 h)** | 14,10 ms | 19,00 ms | 100,00 % |

**Conclusión:** La variación en la media es insignificante (< 0,84 ms) y el percentil 95 se mantuvo estable (incluso mejorando de 21,05 ms a 19,00 ms), confirmando que el garbage collector de Python, el pool de conexiones de asyncpg/SQLModel y el middleware de WebSocket liberan correctamente los recursos en régimen de operación continua.
