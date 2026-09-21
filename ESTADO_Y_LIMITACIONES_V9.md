# Estado técnico y limitaciones de la entrega de defensa

Este archivo resume qué evidencia forma parte de la entrega y qué aspectos permanecen fuera del alcance del MVP académico.

## Evidencia incorporada

- **RNF-01:** 600 peticiones HTTP autenticadas, 200 por endpoint, todas con HTTP 200. P95 de 11,57 ms, 16,08 ms y 10,36 ms para los tres endpoints de lectura.
- **RF-04:** 10 corridas WebSocket; media 43,64 ms; mediana 26,71 ms; IC 95 % [7,93; 79,34] ms.
- **Equivalencia PostgreSQL ↔ DICOM Worklist:** 20 órdenes y 140 atributos comparados, con 0 discrepancias en la muestra auditada.
- **Regresión del motor:** 27 órdenes adicionales y 27/27 coincidencias respecto de las etiquetas esperadas derivadas de la configuración calibrada.
- **Suite automatizada:** 34 pruebas del motor y 6 pruebas de seguridad, 40 en total, presentes en el código.
- **Privacidad del canal de alertas:** el backend construye el payload externo con `patient_pseudonym` y el workflow de Telegram consume ese campo; no se incluye nombre ni DNI en el payload externo. `VERIFY_DELIVERY.py` comprueba esta condición estructuralmente.

## Correcciones de trazabilidad

- H1 y el TPO se delimitan hasta la disponibilidad clasificada en el tablero. El despacho posterior de la MWL se reconoce como una acción explícita del operador y queda fuera del TPO medido.
- La tesis y el software describen el mismo recuento de pruebas: 40.
- Las nuevas mediciones de RNF-01, RF-04 y equivalencia DICOM están documentadas tanto en la tesis como en `benchmark/results/`.
- El paquete final se identifica mediante un SHA-256 consignado en la tesis una vez congelado el archivo ZIP definitivo.

## Limitaciones que permanecen abiertas

Los instrumentos y protocolos para cerrar las cuatro primeras están en `PROTOCOLOS_EVIDENCIA_ADICIONAL.md`; no se ejecutaron para esta entrega.

1. **Validación predictiva independiente del motor.** Las etiquetas del conjunto de regresión adicional se derivan de la misma especificación calibrada; no sustituyen una nueva referencia humana independiente.
2. **Concurrencia y disponibilidad sostenida.** Las mediciones de RNF-01 y RF-04 son secuenciales y no equivalen a una prueba de carga ni a un SLO operacional sostenido.
3. **RNF-02.** No se realizó una campaña longitudinal que permita acreditar una disponibilidad DICOM ≥ 99 %.
4. **Usabilidad con usuarios finales.** El Anexo VIII contiene una evaluación heurística de un evaluador coautor; no constituye una prueba de tareas con participantes externos.
5. **Preparación productiva.** El MVP no implementa RBAC institucional, gestión centralizada de credenciales, TLS/proxy ni la totalidad de los controles jurídicos, éticos e institucionales requeridos para operar con datos reales.
6. **Reproducibilidad completa del entorno.** Algunas configuraciones de Orthanc y de las imágenes Docker dependen del entorno y no quedan totalmente fijadas en el archivo de composición.

Estas limitaciones se mantienen explícitas para evitar extrapolar los resultados del entorno controlado a producción o a desempeño clínico.
