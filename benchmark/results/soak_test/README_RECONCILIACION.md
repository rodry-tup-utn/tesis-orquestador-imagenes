# Reconciliación de la serie de soak

El archivo `soak_test_report_extended_2026-09-23.json/.md` es un reporte histórico generado sobre un corte parcial de la serie (1.254 observaciones; P95 20,47 ms).

El CSV crudo `raw/soak_2026-09-23_1540.csv` contiene 1.548 observaciones y constituye la fuente completa utilizada para el recálculo final: 1.548/1.548 respuestas HTTP 200, media 13,32 ms, P95 20,08 ms y P99 57,89 ms.

Ambos archivos se conservan sin sobrescribir la evidencia histórica. Las cifras del documento de tesis y de los resúmenes de la entrega final deben referirse al CSV completo. Este ensayo caracteriza estabilidad de los endpoints de lectura de la API; no acredita disponibilidad sostenida del servicio DICOM.
