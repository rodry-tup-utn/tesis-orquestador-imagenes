# Instrucciones para Clasificación de Órdenes Médicas

## Propósito

Este formulario forma parte de una investigación para evaluar la precisión de un **motor de triaje automático** para órdenes de diagnóstico por imágenes. Se busca comparar la clasificación que realiza el sistema con el criterio de profesionales con experiencia clínica.

## Su rol

Usted actúa como **clasificador experto**. Su tarea es asignar un nivel de prioridad a cada una de las 50 órdenes médicas presentadas, basándose únicamente en la información clínica disponible en cada caso.

## Instrucciones

1. **Lea cada caso individualmente.** Cada fila del formulario contiene: ID de la orden, modalidad de imagen, diagnóstico/sospecha clínica, servicio de origen, ubicación del paciente y si es urgente.

2. **Clasifique en uno de cuatro niveles** según su criterio clínico:

   | Nivel | Definición |
   |-------|-----------|
   | **Crítico** | Amenaza vital inmediata. Requiere atención de imagen en **minutos**. Ejemplo: ACV agudo, politraumatismo inestable, hemorragia activa con inestabilidad hemodinámica. |
   | **Urgente** | Condición aguda que requiere atención en **1-2 horas**. No es inmediatamente mortal pero el retraso empeora el pronóstico. Ejemplo: TEP confirmado, colecistitis aguda con fiebre alta, fractura expuesta. |
   | **Prioritario** | Estudio que debe realizarse **hoy**, con prioridad en la agenda. Se programa primero que Rutina. Ejemplo: control post-quirúrgico programado, estudio de tumoración conocida, control oncológico. |
   | **Rutina** | Estudio programado para **hoy**, puede ocupar el último turno o espacio disponible. Sin prioridad de agenda. Ejemplo: control de asma, mastalgia de control, espondiloartrosis crónica. |

3. **No existe una respuesta "correcta" única.** Lo que se busca es su criterio profesional. Si un caso le genera duda, clasifíquelo en el nivel que **más se aproxime** a su juicio clínico.

4. **No consulte con otros evaluadores.** Cada persona debe clasificar de forma independiente.

5. **No revise casos anteriores** antes de clasificar uno nuevo. Cada caso es independiente.

6. **Complete la columna `clasificacion`** en el CSV con uno de estos valores exactos: `Crítico`, `Urgente`, `Prioritario` o `Rutina`.

## Datos del evaluador (completar)

- **Nombre/seudónimo:** _______________
- **Especialidad/rol:** _______________
- **Años de experiencia:** _______________
- **Fecha de clasificación:** _______________

## Formato del archivo a completar

El archivo `evaluator_template_<su_nombre>.csv` contiene 50 filas con las columnas:

```
order_id,modality,diagnosis,origin_service,patient_location,is_urgent,clasificacion
```

Las primeras 6 columnas ya vienen completadas. Solo debe escribir en la columna `clasificacion`.

## Consideraciones clínicas

- Tenga en cuenta la **combinación** de factores: un paciente en UTI con un estudio urgente tiene mayor prioridad que el mismo estudio en ambiente ambulatorio.
- La **modalidad** importa: una TC cerebral tiene mayor prioridad que una radiografía simple en el mismo contexto.
- La **ubicación** del paciente indica severidad: Shock Room, Box Rojo y UTI indican pacientes más graves que Sala de Espera o Box Verde.
- El campo "urgente" refleja la solicitud del médico solicitante, pero su criterio puede diferir.

## Agradecimiento

Su participación es fundamental para la validación de este sistema. Los resultados serán utilizados exclusivamente con fines académicos (tesis de grado).
