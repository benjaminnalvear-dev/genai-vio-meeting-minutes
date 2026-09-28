# Deliverable 2: Constrained Decoding + Tool Use con Ministral 3B

## 1. Objetivo del experimento

El objetivo fue evaluar si una intervención basada en **constrained decoding** y **tool use** mejora el desempeño de un modelo pequeño al transformar transcripciones de reuniones en minutas estructuradas.

La tarea consiste en leer una reunión completa en español y extraer:

- decisiones y su estado final;
- tareas, responsables y fechas límite;
- referencias de evidencia que permitan rastrear cada elemento hasta la transcripción;
- relaciones de reemplazo entre decisiones cuando una decisión posterior corrige o sustituye una anterior.

Los principales errores identificados previamente eran:

- colapso de modalidad: confundir propuestas, dudas o rechazos con decisiones finales;
- seguimiento incorrecto del estado cuando una decisión cambia durante la reunión;
- atribución incorrecta de responsables;
- invención o asignación forzada de información que no aparece en la conversación.

## 2. Modelo y entorno

- **Modelo:** Ministral 3 3B Instruct 2512.
- **Versión ejecutada:** `ministral-3:3b-instruct-2512-q4_K_M`.
- **Cuantización:** Q4_K_M.
- **Motor de inferencia:** Ollama.
- **Entorno:** Google Colab con GPU NVIDIA T4 de 15 GB.
- **Idioma de las reuniones:** español.
- **Conjunto evaluado:** 10 reuniones completas del split de test.

Se eligió un modelo de 3 mil millones de parámetros porque el trabajo premia el uso de modelos pequeños y porque esta versión puede ejecutarse de forma reproducible en un Colab con T4.

## 3. Archivos enviados

### `Ministral_Minutas_Colab.ipynb`

Notebook completo y reproducible. Instala Ollama, descarga el modelo, carga el dataset, ejecuta las tres configuraciones, calcula las métricas y genera el ZIP final.

### `Fine Tuning.zip`

Dataset del proyecto. A pesar de su nombre, en este experimento no se utilizó para entrenar el modelo. Sus reuniones y rúbricas se usaron para desarrollo, validación y evaluación. Los resultados reportados corresponden exclusivamente a las 10 reuniones completas del split de test.

### `minutas_resultados_test.zip`

Resultados finales. Contiene:

- 10 archivos de la configuración `baseline`;
- 10 archivos de `structured`;
- 10 archivos de `combined_v2`;
- `summary.json`, con las métricas agregadas y los resultados por reunión.

## 4. Diseño experimental

Se compararon tres configuraciones usando exactamente el mismo modelo y las mismas 10 reuniones.

### A. Baseline

El modelo recibe la transcripción y una instrucción directa para producir la minuta. La generación es libre y no se impone un esquema durante la decodificación.

Esta configuración representa el comportamiento original del modelo.

### B. Structured: constrained decoding

Se usa el formato estructurado de Ollama con un esquema JSON. Durante la generación, el modelo queda restringido a una salida compatible con la estructura requerida.

El esquema exige campos para decisiones, estados, tareas, responsables, fechas y evidencia. Esto busca eliminar respuestas con texto adicional, claves incorrectas o JSON inválido.

### C. Combined: constrained decoding + tool use

Se mantiene el mismo esquema JSON y se agregan herramientas locales determinísticas. El flujo realiza una primera extracción, consulta las herramientas y devuelve sus resultados al modelo para que revise la minuta antes de generar la respuesta final.

Las herramientas utilizadas son:

1. **Inspección de evidencia:** busca un `evidence_id` en la transcripción y entrega su intervención junto con el contexto cercano.
2. **Resolución de fechas:** convierte expresiones explícitas de plazo en fechas ISO usando la fecha de la reunión.
3. **Detección de revisiones:** identifica expresiones asociadas con reemplazo, rechazo, aprobación o elementos pendientes.
4. **Validaciones determinísticas:** comprueba que las referencias de evidencia existan y que las fechas tengan un formato válido.

Aquí `tool use` significa que el notebook orquesta funciones locales y entrega sus resultados al modelo. No corresponde a llamadas autónomas nativas del modelo.

## 5. Resultados finales en test

| Configuración | JSON válido | Esquema válido | F1 decisiones | F1 tareas | Tiempo total |
|---|---:|---:|---:|---:|---:|
| Baseline | 0/10 | 0/10 | 0,477 | 0,667 | 303,8 s |
| Constrained decoding | 10/10 | 10/10 | 0,559 | 0,709 | 197,9 s |
| Constrained decoding + tools | 10/10 | 10/10 | **0,667** | **0,716** | 288,0 s |

### Resultados complementarios

| Configuración | Decisiones recuperadas | Tareas recuperadas | Evidencias existentes |
|---|---:|---:|---:|
| Baseline | 21/56 | 32/53 | 70/75 |
| Constrained decoding | 26/56 | 39/53 | 94/94 |
| Constrained decoding + tools | **35/56** | **39/53** | **105/105** |

Las cantidades recuperadas corresponden a coincidencias del evaluador automático. El F1 combina precisión y recall, por lo que es la medida principal para comparar la extracción entre configuraciones.

## 6. Interpretación

El constrained decoding resolvió el problema de formato: pasó de 0 de 10 salidas JSON válidas a 10 de 10. También mejoró la extracción de decisiones y tareas.

La incorporación de herramientas produjo la mayor mejora en decisiones. El F1 aumentó de 0,477 en el baseline a 0,667 en la configuración combinada. En términos de coincidencias, se pasó de 21 a 35 decisiones recuperadas sobre un total de 56.

En tareas, el cambio fue más pequeño: el F1 aumentó de 0,667 a 0,716. La combinación recuperó la misma cantidad de tareas que constrained decoding, pero obtuvo un equilibrio ligeramente mejor entre precisión y recall.

La configuración combinada también aseguró que todas las referencias generadas existieran en la transcripción: 105 de 105. Sin embargo, esto solo comprueba la existencia del identificador; no garantiza por sí solo que cada referencia sea la mejor evidencia semántica.

## 7. Costo de la intervención

La configuración combinada tardó 288,0 segundos para las 10 reuniones, aproximadamente 28,8 segundos por reunión. Constrained decoding sin herramientas tardó 197,9 segundos, aproximadamente 19,8 segundos por reunión.

Por lo tanto, las herramientas mejoraron principalmente la recuperación de decisiones, pero agregaron alrededor de 9 segundos por reunión frente a la configuración estructurada.

El baseline alcanzó 303,8 segundos debido principalmente a una primera ejecución atípicamente lenta. Por eso, la comparación más clara de costo computacional es entre `structured` y `combined_v2`.

## 8. Limitaciones

- El conjunto de test contiene solo 10 reuniones, por lo que los resultados deben interpretarse como evidencia inicial.
- El emparejamiento semántico entre predicciones y rúbricas es automático y aproximado. Conviene revisar manualmente ejemplos representativos antes de redactar conclusiones definitivas.
- Persisten errores en el estado de las decisiones, especialmente al distinguir entre `final`, `rejected`, `pending` y `superseded`.
- La resolución de fechas sigue siendo imperfecta cuando el plazo es relativo, ambiguo o presenta inconsistencias con la rúbrica.
- La validez del JSON no implica que su contenido sea correcto.
- La existencia de una referencia de evidencia no garantiza que esa intervención respalde correctamente la afirmación.
- Solo se probó una versión cuantizada de un modelo y un conjunto de prompts.

## 9. Conclusión sugerida para el informe

Los resultados apoyan la hipótesis de que constrained decoding y tool use pueden mejorar un modelo pequeño sin modificar sus pesos. Constrained decoding garantizó salidas válidas y elevó el desempeño semántico. Las herramientas aportaron una mejora adicional especialmente visible en la recuperación de decisiones y en la validez de las referencias de evidencia. El costo principal fue un aumento de latencia y todavía existen errores al seguir el estado final de una decisión y resolver fechas. Por ello, la intervención es prometedora, pero requiere una evaluación manual complementaria y pruebas sobre un conjunto mayor.

## 10. Reproducción rápida en Google Colab

1. Abrir `Ministral_Minutas_Colab.ipynb` en Google Colab.
2. Seleccionar una GPU T4 en **Entorno de ejecución > Cambiar tipo de entorno de ejecución**.
3. Ejecutar todas las celdas en orden.
4. Cuando el notebook lo solicite, subir `Fine Tuning.zip` sin modificar su estructura.
5. Esperar la descarga del modelo y la ejecución de las 10 reuniones.
6. Al finalizar, descargar `minutas_resultados_test.zip`.

La descarga del modelo ocurre una vez por sesión. La ejecución completa puede tardar varios minutos según la velocidad de Colab.

## 11. Cuidado al redactar el informe

- Reportar las métricas del split de test, no mezclar resultados de validación.
- Indicar que las métricas semánticas provienen de un emparejamiento automático aproximado.
- Describir las herramientas como funciones determinísticas orquestadas por el notebook.
- No afirmar que se realizó fine tuning: la intervención no cambió los pesos del modelo.
- No concluir que las herramientas mejoraron todas las métricas. La mejora más clara aparece en formato, recuperación de decisiones y referencias existentes.
- Presentar la latencia como un costo de la configuración combinada.
