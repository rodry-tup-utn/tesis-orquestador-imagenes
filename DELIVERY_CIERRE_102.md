# Cierre de entrega de defensa — 21/09/2026

Esta entrega alinea código, documentación y evidencia disponible.

## Cambios de cierre sin nuevos datos
- Configuración Orthanc sin credenciales de respaldo `admin/admin`.
- Flujo de alertas: payload externo con pseudónimo HMAC, sin `patient_name` ni DNI.
- Suite de regresión con las cuatro categorías: 8 Crítico, 9 Urgente, 2 Prioritario y 8 Rutina.
- Verificación estructural consolidada mediante `VERIFY_DELIVERY.py`.
- Documentación de limitaciones: la regresión adicional es consistencia de implementación, no validación predictiva independiente; RNF-02 continúa parcialmente sustentado.

## Evidencia que no se inventa
Quedan fuera de esta entrega como resultados experimentales nuevos: validación humana independiente del motor, evaluación de usabilidad con usuarios externos, prueba de carga sostenida y campaña de disponibilidad de cuatro horas. Los scripts/protocolos para esas pruebas se conservan como material de trabajo futuro.

## Trazabilidad
La entrega se mantiene bajo control de versiones Git. El identificador exacto del commit final se consigna en el Anexo IV.7 de la tesis. El commit debe publicarse en el repositorio institucional/oficial para completar la trazabilidad externa.
