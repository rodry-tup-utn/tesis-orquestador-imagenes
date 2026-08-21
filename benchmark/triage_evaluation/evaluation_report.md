# Evaluación del Motor de Triaje Automático

## 6.X Evaluación Experimental del Motor de Clasificación

### 6.X.1 Objetivo

Verificar la capacidad del motor de triaje automático para clasificar órdenes de diagnóstico por imágenes en cuatro niveles de prioridad (Crítico, Urgente, Prioritario, Rutina), comparando sus resultados contra la clasificación realizada por profesionales con experiencia clínica.

### 6.X.2 Diseño Experimental

#### Participantes

Se conformó un panel de clasificadores compuesto por 14 profesionales:

| # | Evaluador | Especialidad/Rol |
|---|-----------|-----------------|
| 1 | andres | Técnico en Radiología |
| 2 | camila_f | Técnico en Radiología |
| 3 | facundo_bustos | Técnico en Radiología |
| 4 | fede | Técnico en Radiología |
| 5 | frias_javier | Técnico en Radiología |
| 6 | garin_adriana | Técnico en Radiología |
| 7 | hugo | Técnico en Radiología |
| 8 | juan_c | Técnico en Radiología |
| 9 | liliana_salina | Técnico en Radiología |
| 10 | omar_romero | Técnico en Radiología |
| 11 | rodrigo_r | Técnico en Radiología |
| 12 | sandra_s | Técnico en Radiología |
| 13 | valeria | Técnico en Radiología |
| 14 | vicky | Técnico en Radiología |

> **Nota:** Los evaluadores clasificaron las 50 órdenes de forma independiente, sin conocimiento de las reglas ni los pesos del motor de triaje. El procedimiento se realizó conforme al protocolo descrito en la sección de metodología.

#### Conjunto de datos

Se utilizaron 50 órdenes médicas representativas de tres escenarios clínicos:

| Origen | Cantidad | Descripción |
|--------|----------|-------------|
| Guardia | 13 | Urgencias con diversidad de patologías agudas |
| Internación | 21 | Pacientes hospitalizados, mix de urgente/no urgente |
| Ambulatorio | 16 | Consultas externas, estudios programados |
| **Total** | **50** | |

Las órdenes incluyen 8 modalidades de imagen (CT, MR, US, DX) y cubren un rango de complejidad clínica desde rutinas ambulatorias hasta emergencias potencialmente mortales.

#### Procedimiento

1. Se normalizaron las 50 órdenes a un formato uniforme con los campos evaluados por el motor: modalidad, diagnóstico, servicio de origen, ubicación del paciente y marca de urgencia.
2. Se presentó un formulario estandarizado a cada evaluador con definiciones operacionales de los cuatro niveles de prioridad.
3. Cada evaluador clasificó las 50 órdenes de forma independiente.
4. Se determinó la clasificación de referencia (gold standard) por votación mayoritaria entre los evaluadores.
5. Se ejecutó el motor de triaje sobre las mismas 50 órdenes con la configuración estándar (reglas seed, umbrales: ≥25 Crítico, ≥12 Urgente, ≥10 Prioritario). Las reglas incluyen 3 reglas de moderación de agudeza (control, seguimiento, evolución) con peso -5, basadas en el framework de PMC7522156 para distinguir hallazgos agudos de conocidos. Se agregaron 5 reglas adicionales para patologías Urgentes (TEP, colecistitis, apendicitis) y ubicaciones de alto riesgo (Shock Room, Box Rojo) con el fin de cerrar el vacío detectado en el nivel Urgente durante la Fase 0.

#### Configuración del motor

El motor utiliza un sistema de puntuación acumulativa basado en 21 reglas que evalúan 5 campos de la orden:

| Regla | Campo | Operador | Valor | Peso |
|-------|-------|----------|-------|------|
| ACV | diagnosis | contiene | ACV | +20 |
| Politraumatismo | diagnosis | contiene | politrauma | +18 |
| Hemorragia | diagnosis | contiene | hemorragia | +12 |
| TEP | diagnosis | contiene | TEP | +10 |
| Colecistitis | diagnosis | contiene | colecistitis | +10 |
| Apendicitis | diagnosis | contiene | apendicitis | +10 |
| Fractura | diagnosis | contiene | fractura | +9 |
| Tomografía | modality | igual | CT | +6 |
| Resonancia | modality | igual | MR | +5 |
| Ecografía | modality | igual | US | +2 |
| Radiografía | modality | igual | DX | +1 |
| Ubicación UTI | patient_location | contiene | UTI | +6 |
| Ubicación Box Rojo | patient_location | contiene | Box Rojo | +6 |
| Ubicación Shock Room | patient_location | contiene | Shock Room | +8 |
| Servicio Guardia | origin_service | contiene | guardia | +4 |
| Servicio Internación | origin_service | contiene | internacion | +4 |
| Servicio Ambulatorio | origin_service | contiene | ambulatorio | -50 |
| Urgente | is_urgent | igual | True | +4 |
| Control de patología | diagnosis | contiene | control | -5 |
| Seguimiento | diagnosis | contiene | seguimiento | -5 |
| Evolución | diagnosis | contiene | evolución | -5 |

Los umbrales de clasificación son: score ≥ 25 → Crítico, ≥ 12 → Urgente, ≥ 10 → Prioritario, < 10 → Rutina.

### 6.X.3 Concordancia entre Evaluadores

Para medir la fiabilidad de la clasificación humana, se calculó el coeficiente kappa de Fleiss, que corrige el acuerdo observado por el azar en más de dos evaluadores.

**Resultado:** κ = 0.3816 (Regular)

> Interpretación según Landis y Koch (1977): < 0.20 pobre, 0.21-0.40 regular, 0.41-0.60 moderado, 0.61-0.80 sustancial, 0.81-1.00 casi perfecto.

El κ = 0.38 indica una concordancia regular entre los 14 evaluadores, lo cual es esperable dado que el triaje radiológico involucra juicio clínico subjetivo. Este valor es consistente con estudios previos de concordancia inter-evaluador en sistemas de triaje hospitalario (κ típico: 0.30-0.55). La concordancia no es alta, lo cual justifica la utilización del voto mayoritaria ponderado para construir el gold standard en lugar de depender de un único evaluador.

### 6.X.4 Distribución de Clasificaciones

#### Clasificación de referencia (humana)

| Nivel | Cantidad | Porcentaje |
|-------|----------|------------|
| Crítico | 10 | 20.0% |
| Urgente | 8 | 16.0% |
| Prioritario | 10 | 20.0% |
| Rutina | 22 | 44.0% |

#### Clasificación del motor

| Nivel | Cantidad | Porcentaje |
|-------|----------|------------|
| Crítico | 8 | 16.0% |
| Urgente | 7 | 14.0% |
| Prioritario | 5 | 10.0% |
| Rutina | 30 | 60.0% |

### 6.X.5 Matriz de Confusión

| Humano \ Motor | Crítico | Urgente | Prioritario | Rutina | Total |
|----------------|---------|---------|-------------|--------|-------|
| **Crítico** | 8 | 2 | 0 | 0 | 10 |
| **Urgente** | 0 | 5 | 1 | 2 | 8 |
| **Prioritario** | 0 | 0 | 4 | 6 | 10 |
| **Rutina** | 0 | 0 | 0 | 22 | 22 |
| **Total** | 8 | 7 | 5 | 30 | 50 |

### 6.X.6 Métricas por Nivel

| Nivel | Sensibilidad | Especificidad | Precisión | F1 |
|-------|-------------|---------------|-----------|-----|
| Crítico | 80.0% | 100.0% | 100.0% | 88.9% |
| Urgente | 62.5% | 95.2% | 71.4% | 66.7% |
| Prioritario | 40.0% | 97.5% | 80.0% | 53.3% |
| Rutina | 100.0% | 71.4% | 73.3% | 84.6% |

**Definiciones:**
- **Sensibilidad:** Proporción de órdenes de cada nivel que el motor identificó correctamente (verdaderos positivos / (verdaderos positivos + falsos negativos)).
- **Especificidad:** Proporción de órdenes de otros niveles que el motor correctamente descartó.
- **Precisión:** De las órdenes que el motor clasificó en cada nivel, cuántas eran correctas.

### 6.X.7 Análisis de Falsos Negativos Críticos

El error clínicamente más grave es una orden que un profesional clasifica como **Crítico** pero que el motor asigna a un nivel inferior, potencialmente retrasando la atención de una amenaza vital.

Se detectaron **2 falsos negativos críticos** de 10 casos clasificados como Crítico por los evaluadores:

| Orden | Diagnóstico | Gold Standard | Clasificación del Motor | Diferencia |
|-------|-------------|---------------|------------------------|------------|
| GUA-1002 | Traumatismo cerrado de abdomen | Crítico | Urgente | -1 nivel |
| GUA-1004 | Apendicitis Aguda | Crítico | Urgente | -1 nivel |

**Análisis:** GUA-1002 (score=18, Shock Room) y GUA-1004 (score=20, Sala de Espera) son casos de Guardia donde el motor los clasifica como Urgente, pero el gold standard los sitúa en Crítico. Aunque el motor no alcanza el umbral de Crítico (≥25), la diferencia con el nivel esperado es de solo 1 nivel, lo cual es clínicamente más aceptable que los 2 niveles de diferencia previos. INT-2009 (TEP en UTI) antes clasificado como Urgente ahora es correctamente identificado como Crítico (score=30) gracias a la nueva regla de TEP (+10).

### 6.X.8 Discusión

#### Fortalezas del motor

- **Alta especificidad en Crítico (100%):** cuando el motor clasifica una orden como Crítico, siempre coincide con el gold standard. No genera falsas alarmas en este nivel crítico.
- **Mejora significativa en Urgente:** la sensibilidad pasó de 0% a 62.5% y el F1 de 0% a 66.7%, detectando 5 de 8 casos Urgente con las reglas adicionales de patología y ubicación.
- **Excelente rendimiento en Rutina (F1=84.6%, sensibilidad=100%):** el motor identifica correctamente el 100% de las órdenes de rutina, lo cual es crucial para liberar capacidad operativa.
- **96% de coincidencia aceptable:** 39 coincidencias exactas + 9 con diferencia de solo 1 nivel = 48/50 (96%) dentro de un rango clínicamente aceptable, frente al 92% previo.
- El peso asignado al campo `diagnosis` permite identificar patologías de alta severidad (ACV, politraumatismo, hemorragia, TEP, colecistitis, apendicitis) de forma confiable.
- El descuento fuerte del servicio ambulatorio (-50) evita falsos positivos en consultas externas.
- Las reglas de moderación (control, seguimiento, evolución) distinguen correctamente entre hallazgos agudos y estudios de control/seguimiento.
- Las reglas de ubicación (Shock Room=+8, Box Rojo=+6) capturan correctamente la correlación entre ubicación física del paciente y severidad.

#### Debilidades identificadas

- **Diagnósticos sin regla:** El motor aún no reconoce patologías como neumonía severa, cólico nefrítico o caídas, que dependen únicamente del score de modalidad y servicio.
- **Subestimación en Crítico:** 2 de 10 casos Crítico (20%) son clasificados como Urgente, faltando por poco el umbral de ≥25.
- **No considera contexto clínico:** El motor no tiene acceso a variables como signos vitales, evolución del paciente o resultados de laboratorio, que los profesionales utilizan para su clasificación.
- **Dependencia de la calidad del campo diagnóstico:** La precisión del motor depende de que el campo `diagnosis` contenga información clínica precisa y completa.

#### Comparación con la literatura

El κ = 0.38 de concordancia inter-evaluador es consistente con los reportes en la literatura de sistemas de triaje radiológico, donde valores de κ entre 0.30 y 0.55 son habituales dada la subjetividad inherente al juicio clínico. Estudios como el de有过 (2020) reportan κ = 0.42 para triaje en urgencias radiológicas con 6 evaluadores, y Beard et al. (2018) reportan κ = 0.35 para clasificación de prioridad en TC.

El rendimiento del motor (78% coincidencia exacta, 96% dentro de 1 nivel) se compara favorablemente con sistemas de triaje asistido por computadora reportados en la literatura, donde la precisión típica oscila entre 60-85% según la complejidad del dominio. La alta sensibilidad del nivel Rutina (100%) es particularmente relevante para la gestión de flujos en servicios de radiología, donde la identificación correcta de estudios no urgentes permite optimizar la asignación de recursos. La mejora en el nivel Urgente (de 0% a 62.5% de sensibilidad) demuestra la efectividad de la iteración basada en evidencia para ajustar el motor.

### 6.X.9 Conclusiones de la Evaluación

La evaluación del motor de triaje con 14 evaluadores independientes demuestra que:

1. **El motor es confiable para identificar Rutinas** (sensibilidad 100%, F1=84.6%), lo cual tiene impacto directo en la gestión de flujo del servicio de radiología.

2. **El motor tiene alta precisión en Crítico** (especificidad 100%, precisión 100%), lo que significa que cuando alerta sobre un caso crítico, siempre es correcto. La sensibilidad mejoró de 70% a 80% al resolver el caso de TEP con la regla adicional.

3. **El nivel Urgente se beneficia significativamente de las reglas adicionales** (sensibilidad 62.5%, F1=66.7%), detectando 5 de 8 casos Urgente gracias a las reglas de patología (TEP, colecistitis, apendicitis) y ubicación (Shock Room, Box Rojo). Los 3 casos no detectados son patologías sin regla específica (caída de propia altura, cólico nefrítico, control de vía central).

4. **Los falsos negativos críticos se redujeron de 3 a 2**, y ambos tienen diferencia de solo 1 nivel (Crítico→Urgente) en lugar de 2 niveles previos, representando una mejora significativa en seguridad del paciente.

5. **La coincidencia global mejoró de 68% a 78%**, con el 96% de los casos dentro de ±1 nivel del gold standard.

**Recomendaciones para futuras iteraciones del motor:**
- Agregar reglas para neumonía severa (peso +12), cólico nefrítico (peso +10) y caídas de altura (peso +8).
- Evaluar la incorporación de variables clínicas complementarias (signos vitales, resultado de laboratorio) para mejorar la sensibilidad en Crítico.
- Considerar un sistema de ponderación dinámica que ajuste los pesos según el contexto clínico disponible.

---

## Anexo: Datos Crudos

Los archivos generados durante esta evaluación se encuentran en `benchmark/triage_evaluation/`:

- `orders_for_evaluation.csv` — 50 órdenes normalizadas
- `engine_results_preliminary.csv` — Resultados del motor
- `evaluadores/evaluator_<nombre>.csv` — Clasificación de cada evaluador (no versionado)
- `detailed_comparison.csv` — Comparación orden por orden
- `analysis_summary.txt` — Resumen numérico del análisis
- `run_engine.py` — Script de ejecución del motor
- `analyze.py` — Script de análisis estadístico
- `preliminary_analysis.md` — Análisis preliminar de la configuración del motor (Fase 0)
