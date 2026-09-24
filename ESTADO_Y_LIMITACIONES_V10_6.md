# Estado técnico y limitaciones de la entrega V10.6

## Evidencia incorporada

- RNF-01: 600 peticiones secuenciales, P95 11,57 / 16,08 / 10,36 ms, HTTP 200 en todas.
- Carga concurrente: 1/5/10 clientes sin errores; 25 clientes con 18,32 % de error; 50 clientes con 100 % de error.
- Soak de API: >3,5 h, 1.254 peticiones, 100 % HTTP 200, P95 20,47 ms.
- WebSocket extendido: N=50, media 19,56 ms, mediana 18,37 ms, P95 27,55 ms, IC 95 % [18,40; 20,72] ms.
- DICOM extendido: 50 órdenes, 350 atributos, 0 discrepancias usando el serializador productivo.
- Regresión del motor: 50/50 sobre etiquetas derivadas de las reglas calibradas; consistencia, no validación predictiva.
- Suite: 101 tests presentes.
- Seguridad: Bandit y pip-audit con resultados conservados de la campaña del 23/09/2026.
- Resiliencia: 3 escenarios ejecutados y superados; 2 no ejecutados por limitaciones del entorno.

## Limitaciones abiertas

1. Validación predictiva independiente del motor con referencia profesional nueva.
2. Disponibilidad directa del servicio DICOM durante una ventana operacional de ≥99 %.
3. Usabilidad con usuarios finales externos.
4. RBAC institucional, TLS/proxy y controles de producción.
5. Reproducibilidad total de configuraciones externas de Orthanc/n8n e imágenes fijadas por digest.

Estas limitaciones no se ocultan: delimitan el alcance de los resultados y evitan extrapolar el comportamiento del MVP a producción o a desempeño clínico.
