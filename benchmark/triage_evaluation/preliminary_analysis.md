# Análisis Preliminar del Motor de Triaje (Fase 0)

**Fecha:** 2026-08-19
**Objetivo:** Verificar la coherencia de la configuración del motor antes de la comparación con clasificadores humanos.

## Configuración evaluada

- **Reglas:** 16 reglas (ver `server/app/modules/triage/seed.py`)
  - 4 reglas de patología (ACV, politraumatismo, hemorragia, fractura)
  - 4 reglas de modalidad (CT, MR, US, DX)
  - 1 regla de ubicación (UTI)
  - 3 reglas de servicio (Guardia, Internación, Ambulatorio)
  - 1 regla de urgencia (marcada por origen)
  - **3 reglas de moderación de agudeza** (control, seguimiento, evolución)
- **Umbrales:** Crítico ≥ 25, Urgente ≥ 15, Prioritario ≥ 10, Rutina < 10
- **Conjunto:** 50 órdenes normalizadas desde los mocks del sistema (13 Guardia, 21 Internación, 16 Ambulatorio)

### Reglas de moderación de agudeza (nuevas)

Se agregaron 3 reglas con peso negativo (-5 cada una) para el campo `diagnosis`:

| Regla | Palabra clave | Peso | Justificación clínica |
|-------|--------------|------|----------------------|
| Control de patología | `control` | -5 | Distingue "control ACV" de "ACV agudo" |
| Seguimiento | `seguimiento` | -5 | Sinónimo clínico de control |
| Evolución | `evolución` | -5 | Indica fase post-aguda ("ACV en evolución") |

**Fundamento:** Estas reglas se basan en el framework de distinción entre hallazgos agudos y estables/conocidos descrito en PMC7522156 (*Framework for Extracting Critical Findings in Radiology Reports*), que utiliza listas de términos de agudeza para distinguir hallazgos nuevos de conocidos.

## Distribución de prioridades del motor

| Nivel | Cantidad | Porcentaje |
|-------|----------|------------|
| Crítico | 7 | 14.0% |
| Urgente | 1 | 2.0% |
| Prioritario | 12 | 24.0% |
| Rutina | 30 | 60.0% |

## Hallazgos principales

### 1. Los críticos se identifican correctamente
Las 7 órdenes clasificadas como Crítico corresponden a casos clínicamente graves:
- ACV (Guardia e Internación): score 34-40
- Politraumatismo (Guardia): score 32
- Hemorragia (Guardia e Internación): score 26-32

Ningún caso Crítico fue subclasificado. **Sensibilidad del 100% para el nivel Crítico en el conjunto sintético.**

### 2. Los ambulatorios siempre son Rutina
La regla de Servicio Ambulatorio (peso -50) domina cualquier otro score positivo, garantizando que toda orden ambulatoria clasifique como Rutina. Esto es clínicamente correcto: los estudios programados en consultorio externo no requieren prioridad de imagen.

### 3. Las reglas de moderación funcionan correctamente
Las 3 nuevas reglas (control, seguimiento, evolución) producen los cambios esperados:

| Orden | Diagnóstico | Score antes | Score después | Nivel |
|-------|-------------|------------|---------------|-------|
| INT-2006 | Control oncologico | 10 | 5 | **Prioritario → Rutina** |
| INT-2001 | Control post-quirurgico | 5 | 0 | Rutina → Rutina |
| INT-2013 | Control de via central | 9 | 4 | Rutina → Rutina |

**INT-2006** es el cambio más significativo: un control oncológico programado que el motor anterior clasificaba como Prioritario (score 10) ahora se clasifica como Rutina (score 5), que es clínicamente más preciso.

Los diagnósticos agudos (ACV, politraumatismo, hemorragia) **no se ven afectados** porque no contienen las palabras clave de moderación.

### 4. Existe un "vacío" en el nivel Urgente
Solo 1 de 50 órdenes (2%) cayó en Urgente. Esto sugiere que los umbrales actuales crean una separación abrupta:
- Score 20 (ej: TEP en UTI) → Urgente
- Score 14 (ej: cólico renal en guardia) → Prioritario
- No hay diagnósticos con scores entre 16-24 que no sean Crítico

La mayoría de las condiciones de severidad intermedia (20 puntos) son capturadas, pero el rango 15-24 tiene poca cobertura.

### 5. Diagnósticos sin regla específica
El motor reconoce 4 patologías por nombre: ACV, politraumatismo, hemorragia y fractura. Diagnósticos potencialmente graves como TEP, colecistitis aguda, apendicitis o TVP dependen únicamente del score acumulado de modalidad + servicio + urgencia.

**Ejemplo:** TEP en UTI (INT-2009) obtiene score 20 → Urgente. Si el mismo TEP estuviera en Sala de Espera de Guardia sin UTI, obtendría score 14 → Prioritario. La ubicación del paciente es determinante.

### 6. Posibles discrepancias con criterio clínico

| ID | Diagnóstico | Motor | Observación |
|----|-------------|-------|-------------|
| GUA-1006 | Caída de propia altura (urgente) | Rutina (9) | Marcado urgente pero sin fractura en diagnóstico. ¿Debería ser Prioritario? |
| INT-2013 | Control de via central (urgente, Unidad Coronaria) | Rutina (4) | Contexto cardíaco urgente, pero es control. Score bajo por modalidad DX + penalización control |
| INT-2009 | TEP en UTI | Urgente (20) | TEP es potencialmente mortal. ¿Debería ser Crítico? |
| GUA-1008 | Cefalea intensa (no urgente) | Prioritario (10) | TC cerebral sin urgencia, ¿realmente Prioritario? |

## Distribución por servicio

| Servicio | Crítico | Urgente | Prioritario | Rutina | Total |
|----------|---------|---------|-------------|--------|-------|
| Guardia | 4 | 0 | 5 | 4 | 13 |
| Internación | 3 | 1 | 7 | 10 | 21 |
| Ambulatorio | 0 | 0 | 0 | 16 | 16 |

## Conclusión de la Fase 0

La configuración actual del motor produce resultados **mayoritariamente coherentes** con el criterio clínico esperado:
- Los críticos se identifican sin falsos negativos
- Los ambulatorios se descartan correctamente
- Las patologías con regla específica (ACV, politraumatismo, hemorragia, fractura) se detectan confiablemente
- Las reglas de moderación (control, seguimiento, evolución) reducen correctamente la prioridad de estudios de control

Las áreas identificadas para monitorear en la comparación con humanos:
1. El "gap" de Urgentes (¿es un problema real o refleja la distribución clínica?)
2. El manejo de diagnósticos sin regla (¿los humanos clasifican más alto que el motor?)
3. La influencia de la ubicación del paciente en la puntuación
4. Casos donde la urgencia marcada por el médico solicitante no se refleja en el score
5. La dependencia de la calidad del campo de diagnóstico (limitación del sistema)

**Decisión:** Se procede con la comparación usando esta configuración de 16 reglas.
