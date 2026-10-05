# Análisis Sistemático de Falsos Negativos del Motor de Triaje

- **Fecha:** 2026-09-23  
- **Corpus evaluado:** 50 órdenes médicas sintéticas (`motor_salida_fases_50_ordenes.csv`)  
- **Coincidencias exactas:** 39/50 (78.0 %)  
- **Sobreclasificaciones:** 0/50 (0,0 %)  
- **Subestimaciones totales:** 11/50 (22.0 %)  

## 1. Falsos Negativos en el Nivel Crítico (Tablas 29 del Cap. 6)

| Orden | Diagnóstico | Ubicación | Score | Motor | Referencia | Causa Técnica |
|---|---|---|:---:|:---:|:---:|---|
| GUA-1002 | Traumatismo cerrado de abdomen | Shock Room | 18.0 | URGENTE | CRITICO | Diagnóstico 'Traumatismo cerrado de abdomen' no contiene el acrónimo exacto 'politrauma' |
| GUA-1004 | Apendicitis Aguda | Sala de Espera | 20.0 | URGENTE | CRITICO | Apendicitis aguda activó regla de Urgente (+20 pts); no activó shock o peritonitis |

## 2. Falsos Negativos en el Nivel Urgente (Tabla 30 del Cap. 6)

| Orden | Diagnóstico | Ubicación | Score | Motor | Referencia | Causa Técnica |
|---|---|---|:---:|:---:|:---:|---|
| INT-2011 | Colico nefritico | Pediatria | 10.0 | PRIORITARIO | URGENTE | Cólico nefrítico carece de regla específica en diccionario; sumó solo puntaje de Pediatría (+10 pts) |
| INT-2013 | Control de via central | Unidad Coronaria | 4.0 | RUTINA | URGENTE | Control de vía central activó regla neutra de 'control' a pesar de ubicación en Unidad Coronaria (+15 pts) |

## 3. Subestimaciones en Nivel Prioritario (Asignadas a Rutina)

| Orden | Diagnóstico | Ubicación | Servicio | Score | Causa Técnica |
|---|---|---|---|:---:|---|
| GUA-1003 | Sospecha de Neumonia | Box Amarillo | Guardia | 5.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| GUA-1006 | Caida de propia altura | Sala de Espera | Guardia | 9.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| GUA-1012 | Dolor abdominal difuso | Sala de Espera | Guardia | 6.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| INT-2005 | Neumonia intrahospitalaria | Clinica Medica | Internación | 5.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| INT-2010 | Sospecha de tumoracion | Neurologia | Internación | 9.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| INT-2018 | Insuficiencia cardiaca | Cardiologia | Internación | 6.0 | Puntaje no alcanza umbral Prioritario (10 pts) |
| INT-2020 | Suboclusion intestinal | Cirugia General | Internación | 5.0 | Puntaje no alcanza umbral Prioritario (10 pts) |

## 4. Interpretación Metodológica y Rigor

El análisis sistemático demuestra que los errores del motor no responden a dispersión aleatoria, sino a límites de diseño intrínsecos de un clasificador por reglas deterministas:
1. **Dependencia léxica exacta:** Términos como 'traumatismo cerrado de abdomen' no activan la regla 'politrauma'.
2. **Sensibilidad de umbrales:** Casos de Apendicitis en Sala de Espera alcanzan 20 puntos (Urgente), requiriendo 40 puntos para Crítico.
3. **Casos limítrofes en el panel humano:** En GUA-1004, la concordancia del panel fue del 41 % (7 vs 6 votos), evidenciando discrepancia médica real.
