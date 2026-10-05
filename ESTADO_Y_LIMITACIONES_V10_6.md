# Estado y limitaciones — V10.6

## Evidencia incorporada

- RNF-01: 600 peticiones secuenciales, P95 11,57 / 16,08 / 10,36 ms, HTTP 200 en todas.
- Carga concurrente: 1/5/10 clientes sin errores; los registros de 25 y 50 clientes se conservan, pero sus tasas de error no se interpretan como límites de carga porque las ventanas se superpusieron con el reinicio del backend de resiliencia.
- Soak de API: estabilidad sostenida de endpoints de lectura durante 4,3 h; no equivale a disponibilidad DICOM.
- WebSocket extendido: N=50, media 19,56 ms, mediana 18,37 ms, P95 27,55 ms, IC 95 % [18,40; 20,72] ms.
- DICOM extendido: 50 órdenes, 350 atributos, 0 discrepancias usando el serializador productivo.
- Suite automatizada: 101 pruebas estructuradas, con valores de prueba provistos por `server/tests/conftest.py`.
- Dependencias: versiones directas fijadas en `server/requirements.lock`.
- Canal de alertas: existe un intento `FAILED` del 20/09/2026; no se presenta como ejecución exitosa.

## Pendientes / condiciones de uso

1. Validación predictiva independiente con referencia profesional nueva.
2. Evaluación de usabilidad con usuarios finales externos.
3. Validación clínica y operacional en una institución real.
4. RBAC institucional, TLS/proxy y controles de producción.
5. Reproducibilidad total de configuraciones externas de Orthanc/n8n e imágenes fijadas por digest.
6. Corrida exitosa de extremo a extremo del canal de alertas con la composición entregada.

Estas limitaciones delimitan el alcance de los resultados y evitan extrapolar el comportamiento del MVP a producción o a desempeño clínico.

## Condiciones de reproducción de la suite

La suite puede ejecutarse sin crear un archivo `.env`: `server/tests/conftest.py` define valores de prueba mediante `os.environ.setdefault`, por lo que una configuración externa válida mantiene prioridad. Las dependencias directas están fijadas en `server/requirements.lock`.
