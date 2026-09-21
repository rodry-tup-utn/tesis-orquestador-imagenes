# Protocolos para la evidencia que la tesis declara pendiente

Cada sección deja lista la evidencia que hoy figura como limitación abierta (`ESTADO_Y_LIMITACIONES_V9.md`).
Los instrumentos están en `benchmark/`, probados con datos sintéticos que **no** forman parte del estudio.
Regla común: **se publica lo que resulte**, sin repetir la medición hasta obtener un valor favorable.

---

## 1. Validación predictiva independiente del motor (`eval_independent.py`)

**Qué cierra:** la limitación 1 de `ESTADO_Y_LIMITACIONES_V9.md`; el 78 % del Capítulo 6 se midió sobre el mismo conjunto en que se calibró, y la regresión de 27 órdenes es consistencia, no validación.

**Requisitos**
- ≥ 60 órdenes nuevas, **redactadas por clínicos que no son autores** y que no participaron de la calibración. Texto libre con abreviaturas, sinónimos, errores de tipeo y campos vacíos. Estratificar: ≈ 15 por nivel esperado.
- ≥ 5 evaluadores clínicos, que **no vieron** el motor ni sus reglas, cada uno por separado (formulario en línea o planilla individual).

**Pasos**
1. **Congelar** la configuración: `sha256sum server/app/modules/triage/configs/calibrada_fase4.json` y anotarlo (también en un commit/tag) **antes** de recibir las etiquetas.
2. Recolectar órdenes y etiquetas; armar el CSV con `benchmark/templates/validacion_independiente_PLANTILLA.csv` (una columna `rater_k` por evaluador).
3. Ejecutar **una sola vez**: `python benchmark/eval_independent.py --orders ordenes.csv`.
4. Guardar `results_independent_validation_<fecha>.csv/.md` en el ZIP.

**Qué reporta:** coincidencia exacta con IC de Clopper-Pearson, coincidencia dentro de un nivel, línea de base y p exacto, κ ponderado (motor–patrón), κ de Fleiss (entre evaluadores), sensibilidad/especificidad/F1 por nivel, matriz de confusión y falsos negativos críticos. El desempate usa el nivel más severo, igual que el Capítulo 6.

**En la tesis:** nueva sección 6.15 «Validación predictiva independiente» (diseño, resultados, matriz); actualizar H2/H3 (Tabla 36), la Tabla 37 y la sección 6.13 (quitar «corpus construido» del alcance); cambiar la limitación 1 de §5.6 y del Capítulo 8.
**Tiempo estimado:** 2–3 días (la mayor parte, esperar a los evaluadores).
**Si el resultado es peor que 78 %:** se informa igual y se discute; una validación honesta con resultado moderado vale más que una circular con 100 %.

---

## 2. Escenario A con varios operadores (`scenario_a_timer.py`)

**Qué cierra:** el TCM actual (90 s) es autoobservación de un coautor, sin registro por ciclo.

**Pasos**
1. ≥ 3 operadores distintos (técnicos de la institución), ≥ 10 órdenes cada uno, sobre el equipo/entorno real de carga manual.
2. `python benchmark/scenario_a_timer.py --operator OP1 --orders 10` (Enter inicia / Enter detiene). Repetir por operador.
3. `python benchmark/scenario_a_timer.py --summary` → media, mediana, sd e IC 95 %.

**En la tesis:** reemplazar el 90 s por la media medida en Tabla 9, §5.4 y Tabla 3; conservar la nota de que la medición es de un servicio (no generalizable). Recalcular el throughput de A (3600 ÷ TCM).
**Tiempo:** medio día.

---

## 3. Usabilidad con usuarios (`sus_score.py`)

**Qué cierra:** OE4/RNF-05 hoy sustentado solo por heurística de un evaluador coautor.

**Pasos**
1. 5–8 participantes (técnicos y licenciados), sin haber visto el tablero.
2. 4 tareas cronometradas sobre el tablero real, con observador:
   - T1 identificar la orden Crítica sin atender más antigua;
   - T2 cambiar el estado de una orden;
   - T3 buscar una orden por DNI o seudónimo;
   - T4 editar las observaciones de una orden y enviarla a Orthanc.
   Registrar éxito (1/0) y segundos por tarea.
3. Cuestionario SUS (adaptación al español):
   1. Creo que me gustaría utilizar este sistema con frecuencia.
   2. Encontré el sistema innecesariamente complejo.
   3. Pensé que el sistema era fácil de usar.
   4. Creo que necesitaría ayuda de un técnico para poder usar este sistema.
   5. Encontré que las funciones del sistema estaban bien integradas.
   6. Pensé que había demasiada inconsistencia en el sistema.
   7. Imagino que la mayoría de las personas aprendería a usarlo muy rápido.
   8. Encontré el sistema muy engorroso de usar.
   9. Me sentí muy seguro/a al usar el sistema.
   10. Necesité aprender muchas cosas antes de poder manejar el sistema.
   (escala 1 = totalmente en desacuerdo … 5 = totalmente de acuerdo)
4. `python benchmark/sus_score.py --csv sus.csv` (plantilla: `templates/sus_PLANTILLA.csv`).

**En la tesis:** ampliar el Anexo VIII con los resultados; cambiar OE4/RNF-05 en Tablas 3, 35–37. **Aclarar el régimen ético** de las personas participantes, como en el Capítulo 6.
**Tiempo:** 1–2 días.

---

## 4. Carga concurrente y disponibilidad (`load_test.py`)

**Qué cierra:** limitación 2 y 3 (concurrencia; RNF-02).

**Pasos**
1. Concurrencia: `python benchmark/load_test.py --clients 20 --minutes 5` → P50/P95/P99 con 20 clientes.
2. Disponibilidad: `python benchmark/load_test.py --clients 10 --minutes 240 --think-ms 500` → % de respuestas 200 y peor ventana de 1 minuto.
3. Documentar hardware, volumen de datos en la base y versión de la imagen.

**Alcance:** mide la API bajo carga de lectura; **no** incluye Orthanc ni n8n. Para RNF-02 completo agregar un chequeo periódico de C-ECHO a Orthanc.
**En la tesis:** anexar a VII.1 y pasar RNF-02 de «parcialmente sustentado» a «verificado en la ventana ensayada» (con la ventana explícita).
**Tiempo:** 1 día (la corrida larga corre sola).
