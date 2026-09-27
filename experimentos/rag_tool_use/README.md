# Experimento D2: retrieval y tool use con Ministral 3 3B

Este experimento prueba si **retrieval (RAG)** y **tool use** corrigen los errores que el D1 encontró en
Ministral 3 3B al hacer actas de reuniones. Todo se compara contra el **baseline** (el prompt directo del
D1), con la misma transcripción, el mismo modelo y el mismo corrector.

- **Modelo:** `ministral-3:3b` en Ollama (Q4_K_M, digest `f04aa1c738f6`, el mismo del D1).
- **Controles:** `num_ctx` 8192, temperatura 0, seed 42 (los del D1).
- **Transcripción:** `pruebas/01_transcripcion_reunion_simulada.md`, 69 intervenciones. Es la única
  reunión con gold que hay en el repo.
- **Detalle técnico completo:** [DETALLES_TECNICOS.md](DETALLES_TECNICOS.md).

**Correr en Colab (GPU T4):**
[abrir el notebook](https://colab.research.google.com/github/benjaminnalvear-dev/genai-vio-meeting-minutes/blob/main/experimentos/rag_tool_use/notebooks/d2_colab.ipynb)
→ `Entorno de ejecución → Cambiar tipo → T4` → `Ejecutar todas`. Tarda unos 10 minutos más la instalación.

---

## 1. El problema

En el baseline, Ministral recibe las 69 intervenciones de una vez y tiene que escribir el acta completa en
JSON: entender, recordar lo que cambió, convertir fechas, copiar citas y respetar el formato, todo a la vez.
En el D1 se equivocó en eso:

| Error del D1 (Ministral) | Ejemplo |
|---|---|
| Historial apertura: 0/2 estados obsoletos | No registró que "mañana a las cinco" y "lunes 31" fueron reemplazados por "miércoles 2" |
| Decisiones clave: omitió soporte solo por correo | U030 "sin WhatsApp; solo correo de soporte" no aparece |
| Tareas: escribió 6/7; mezcló 2 | La tarea de Fernanda incluye "corregir duplicación de invitaciones", que es de Diego |
| Plazos: cambió 13:00 por 01:00 | U044 "antes de la una" quedó 01:00 |
| Enlaces de evidencia: al menos 5 incorrectos | Citas que no respaldan lo que se afirma |
| Personas ausentes asignadas: 1 | Paula quedó a cargo del soporte aunque no estaba |

## 2. Las dos técnicas, en simple

**Tool use: "el modelo pide, el código hace".** El modelo no escribe el acta. Responde "formularios"
(llamadas a herramientas) como este, que el modelo devolvió de verdad para U044:

```
crear_tarea(responsable="Martín", contenido="hacer la regresión y subir informe",
            plazo_literal="martes 1 de septiembre entre las 9 y las 1", utterance_id="U044")
```

Con eso, el **código**:
- convierte la fecha con reglas fijas ("la una", en horario laboral, es 13:00 → `2026-09-01 13:00`);
- pega la cita exacta de U044 desde la transcripción;
- solo acepta responsables de la lista de presentes, porque el formulario no permite otros nombres;
- guarda todo en un **registro**, donde lo reemplazado queda marcado como *superseded*.

**RAG (retrieval): "buscar antes de preguntar".** Antes de cada llamada, el código busca en la reunión las
intervenciones anteriores más parecidas a lo que se está leyendo y se las agrega al mensaje. Usamos **BM25**,
una fórmula que puntúa por palabras compartidas y les da más peso a las poco comunes. No es otro modelo.

## 3. Los experimentos

Cada variante agrega una pieza a la anterior, para ver qué aporta cada una.

| | Qué hace | Por qué la probamos |
|---|---|---|
| **B** · Baseline | Prompt directo del D1: una llamada, el modelo escribe todo el acta | Punto de comparación |
| **S1** · Tool use, 1 pasada | El modelo lee la reunión completa una vez y solo devuelve llamadas; el código arma el acta | Ver cuánto arregla el tool use por sí solo |
| **S2** · Tool use por bloques | La reunión se lee en 9 bloques de 8 intervenciones. En cada bloque el modelo ve el registro de lo anotado hasta ahí | Que no se le escapen cosas y que el registro sea la memoria del historial |
| **S3** · S2 + RAG | Cada bloque recibe además 4 intervenciones anteriores encontradas por BM25 (una búsqueda por bloque) | Ver si el contexto recuperado ayuda |
| **S4** · S3 + verificación | Se le pregunta al modelo "¿esta intervención respalda este ítem? sí/no" y se borra lo que no pasa | Filtrar lo que el modelo anota de más |
| **S3b** · S2 + RAG mejorado | Una búsqueda por intervención, con stemmer ("abrimos" y "abrir" calzan) | S3 buscaba mal (ver 4.3) |
| **Control** · S2 + todo el pasado | Cada bloque recibe todas las intervenciones anteriores. No es RAG | Es el máximo que podría dar cualquier buscador |

Cómo es un bloque paso a paso (código → modelo → código):

1. **Código:** arma el mensaje con los datos de la reunión (fecha y presentes/ausentes), el registro actual,
   el contexto recuperado (S3, S3b y el control), las 3 intervenciones anteriores y las 8 nuevas.
2. **Modelo:** hace dos llamadas, una para decisiones y otra para tareas, y responde solo llamadas a herramientas
   (JSON restringido por un schema).
3. **Código:** ejecuta las llamadas sobre el registro. Si una decisión nueva `reemplaza` a otra, marca la
   anterior como *superseded*.
4. Pasa al bloque siguiente, que ya ve el registro actualizado.
5. **Al final (código):** une duplicados, convierte los plazos, pega las citas y escribe el acta con el mismo
   formato JSON del D1.

## 4. Resultados

### 4.1 Resultados oficiales (Colab, Tesla T4, corrida 2 del 27-sep)

Se corrieron las 8 condiciones con el código final. "D1 original" es la salida guardada del D1 (otro equipo),
puntuada con el mismo corrector.

| Criterio del D1 | D1 original | B | S1 | S2 | S3 | S4 | S3b | Control |
|---|---|---|---|---|---|---|---|---|
| Salida final (errores de esquema) | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Historial apertura (estados obsoletos; fecha final) | 0/2; ✓ | 0/2; ✓ | 0/2; ✗ | 1/2; ✗ | 1/2; ✓ | 1/2; ✓ | 1/2; ✗ | **2/2; ✓** |
| Decisiones clave: soporte solo por correo | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Decisiones correctas /9 (precisión) | 3 (0.75) | 3 (0.75) | 3 (0.75) | 5 (0.25) | 6 (0.24) | 6 (0.26) | 5 (0.23) | 6 (0.46) |
| Tareas recuperadas / mezcladas | 6/7 / 1 | 5/7 / 1 | 3/7 / 0 | 7/7 / 0 | 7/7 / 0 | 7/7 / 0 | 7/7 / 0 | 7/7 / 0 |
| Tareas anotadas de más (partidas + extra) | 0 | 1 | 1 | 12 | 9 | 8 | 12 | 14 |
| Plazos: Martín 13:00 / errores de am/pm | ✗ 01:00 / 1 | ✗ 01:00 / 2 | — / 0 | ✓ / 0 | ✓ / 0 | ✓ / 0 | ✓ / 0 | ✓ / 0 |
| Enlaces de evidencia incorrectos | 14 % | 14 % | 19 % | 14 % | 10 % | 11 % | 10 % | 9 % |
| Personas ausentes asignadas | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tiempo | 22 min (Windows) | 45 s | 22 s | 119 s | 121 s | 127 s | 126 s | 155 s |

Tablas completas en `resultados/tesla-t4-corrida2/` (`tabla_d1.md`, `comparacion.md`). La fila de tareas se
juzgó a mano, como en la auditoría del D1, y cada juicio está explicado en `adjudicacion_tareas.json`.

**Reproducibilidad entre las dos corridas de Colab.** La corrida 1 (22-sep) está en `resultados/tesla-t4/`.
- S1, S2 y S3 dieron **exactamente las mismas respuestas del modelo** en las dos corridas.
- **El baseline no:** en la corrida 2 reprodujo casi exacto los errores del D1: Martín a las 01:00, la tarea de
  Fernanda mezclada con la de Diego, "solo correo" omitido y 2 personas ausentes como responsables. En la
  corrida 1 había acertado las 13:00 y el soporte.
- La respuesta larga del prompt directo varía entre sesiones del mismo hardware; las llamadas cortas del tool
  use, no.

### 4.2 Qué aportó cada pieza

- **Tool use (S1)** arregla lo "mecánico" por construcción: cero errores de esquema, ningún error de am/pm y
  nadie ausente asignado, en todas las corridas. Pero en una sola pasada se le escapan tareas (3/7).
- **Bloques con registro (S2)** hacen que no se escapen cosas (7/7 tareas, sin mezclas, "solo correo"
  recuperado) y mejoran el historial (1/2). **El costo:** el modelo anota de más y tarda más.
- **RAG (S3, S3b)** no mejora de forma consistente frente a S2. S3 recuperó la fecha final en la T4; S3b no.
- **Más contexto sí parece ayudar.** El control, con todas las intervenciones anteriores, es la única
  condición con el historial completo (2/2) y la mejor precisión en decisiones (0.46) en la T4. En el Mac
  quedó igual que S2 en decisiones y mejor en pendientes.
- **Verificación (S4)** saca algo de lo que sobra, pero también borra pendientes correctos.

### 4.3 Por qué el RAG no aportó, pero el contexto completo sí un poco

1. **La búsqueda de S3 traía ruido.** Usaba el texto de las 8 intervenciones juntas, que mezclan temas, y
   comparaba palabras exactas ("abrimos" no calza con "abrir").
2. **Mejorarla ayudó poco.** Con búsqueda por intervención y stemmer (S3b), trae 7 de 19 intervenciones
   relevantes, contra 6 de 19 de S3. Todas las variantes que comparan palabras se quedan cerca del 40 %.
3. **El control trae el 100 %** y es el que mejor resuelve el historial en la T4.

**Conclusión:** en esta reunión, lo que ayuda es darle al modelo el contexto *completo*, y nuestro RAG no llega
a reproducir eso porque busca mal. Como la reunión cabe entera en el contexto (unos 4.000 tokens), no hace
falta buscar: se le puede dar todo. **El RAG tiene sentido cuando la reunión no cabe.** Con una sola reunión y
una corrida por hardware, estas diferencias entre S2, S3 y el control son chicas y pueden ser variación.

### 4.4 Recomendación

- **Solución: tool use por bloques.** Es lo que ataca la falla central del D1 (historial y errores formales) en
  todas las corridas.
- **Contexto:** los datos favorecen dar **todo el pasado cuando la reunión cabe** (el control), por encima de no
  dar nada (S2) o de buscar con RAG (S3, S3b). Hoy el modo `auto` usa S2 cuando la reunión cabe; se puede cambiar
  para que use el control cuando cabe y el RAG solo cuando no. Decisión pendiente (sección 8).
- **El RAG va como alternativa evaluada:** se probaron tres búsquedas y un control, y el control ganó.

### 4.5 Casos de falla (para el documento)

1. **Anota de más.** Cuando Camila, que dirige la reunión, "revisa" o "confirma" algo, el modelo lo registra
   como tarea suya (por ejemplo, "revisar uso de SMTP institucional", U022–U024).
2. **Elige la expresión equivocada para el plazo.** Para "mandar el enlace de la demo", copió "miércoles 2 a
   las once y media", que es la hora de la demo. El código la convierte bien, pero no era esa. El tool use saca
   el error de la conversión (am/pm) y lo deja en la elección de la expresión.
3. **Clasifica mal una intervención clave.** En Colab, S2 tomó U041 (la fecha final) como "modalidad de la
   demo" y el acta quedó sin fecha final.
4. **Reemplaza entre temas distintos** (visto en la reunión de prueba de la feria). Marcó la fecha de la feria
   como reemplazada por la decisión del catering, y el código lo aceptó.

### 4.6 Límites

- Hay una sola reunión con gold y una corrida por condición. Los resultados ilustran; no son evidencia
  estadística.
- **La salida depende del hardware:** con los mismos parámetros, el baseline dio JSON válido en Colab y JSON
  cortado en el Mac. Por eso solo se comparan corridas del mismo hardware.
- Los prompts se ajustaron mirando la reunión 01. Los ejemplos del prompt y la calibración del verificador
  usan otra reunión, pero las decisiones de diseño no.
- En el notebook del D1 (1.86 tok/s), S2 tardaría mucho más que el baseline. Para el video conviene Colab.

## 5. Cómo se mide

- **`gold/01_gold.json`** es la pauta de Benjamin (`pruebas/01_gold_referencia.md`) en JSON. Nunca se le entrega
  al modelo.
- **`src/score.py`** es el corrector automático. Empareja cada ítem del acta con el gold por las intervenciones
  que cita y revisa estado, fecha, responsable, plazo y citas. Aplicado a la salida guardada del D1, reproduce
  la auditoría manual de Benjamin (`tests/test_score_d1.py`).
- **La fila "Tareas"** se revisa a mano (`adjudicacion_tareas.json`), porque el emparejamiento automático se
  equivoca cuando hay tareas duplicadas.
- Eduardo subió a `main` otro gold y otro evaluador (`pruebas/01_gold.json`, `scripts/evaluate.py`). Falta
  alinear los dos antes del documento.

## 6. Usarlo con cualquier reunión

```bash
cd experimentos/rag_tool_use
python run.py acta ruta/reunion.md                    # acta en modo auto
python run.py acta ruta/reunion.md --fecha 2026-10-01 --presentes "Ana Díaz, Luis Mora" --ausentes "Marta"
python run.py acta ruta/reunion.md --config baseline  # el prompt directo del D1, para comparar
```

- **Formatos que lee:** el del proyecto (`**[U001 | 09:30:04 | Ana]** …`), `[09:30] Ana: …` o `Ana: …`. La fecha
  es obligatoria, porque sin ella no se puede resolver "mañana" ni "el lunes".
- **Modo `auto`:** si el registro cabe en el contexto, funciona igual que S2, sin RAG. Si no cabe (reunión
  larga), le muestra al modelo solo lo más relacionado del registro y agrega búsqueda por intervención. En
  cualquier modo, si el mensaje no cabe, se recorta y queda anotado, en vez de que Ollama corte el principio
  sin avisar.
- **Probado:** con la reunión de prueba `ejemplos/feria_colegio_formato_simple.md` (otro formato, otros nombres,
  sin gold). Las 4 tareas reales salieron con responsable, plazo y condición correctos. **No probado:** una
  reunión larga real.

## 7. Qué hay en la carpeta

| Archivo | Qué hace |
|---|---|
| `run.py` | Comandos: `baseline`, `pipeline --config …`, `todo`, `acta`, `score`, `compare` y `tabla-d1` |
| `src/transcript.py` | Lee la reunión (los tres formatos) y sus datos: fecha, presentes y ausentes |
| `src/pipeline.py` | Las herramientas, el registro, los bloques, el modo `auto`, la verificación y el armado del acta |
| `src/temporal.py` | Convierte "el martes antes de la una" en `2026-09-01 13:00` con reglas fijas |
| `src/retrieval.py` | El buscador BM25 y el stemmer |
| `src/baseline.py` | El baseline: el mismo texto y los mismos parámetros que `scripts/run_model_test.ps1` |
| `src/ollama_client.py` | Llama a Ollama y guarda prompt, respuesta, tokens, tiempos, versión y digest |
| `src/score.py` | El corrector automático |
| `gold/01_gold.json` | La pauta de la reunión 01 en JSON |
| `tests/` | Pruebas sin modelo: fechas, corrector, formatos y modo `auto` (`python -m unittest discover -s tests`) |
| `evaluar_retrieval.py` | Mide qué tan bien busca cada variante de RAG, sin llamar al modelo |
| `calibracion_verificador.py` | Mide el verificador sí/no con ejemplos de otra reunión |
| `notebooks/d2_colab.ipynb` | Corre todo en Colab y permite subir otra reunión |
| `ejemplos/` | La reunión de prueba de la feria |
| `resultados/tesla-t4-corrida2/` | Resultados oficiales (Colab, 27-sep, las 8 condiciones con el código final) |
| `resultados/tesla-t4/` | Primera corrida en Colab (22-sep): B y S1–S4; sirve para ver la reproducibilidad |
| `resultados/apple-m5/` | Resultados de desarrollo (Mac), incluidos S3b, el control y el acta de la feria |

Cada JSON de resultados guarda los prompts, las respuestas crudas del modelo, las llamadas a herramientas, las
métricas de Ollama y el acta final, así que todo se puede auditar sin volver a correr.

## 8. Pendiente

1. Decidir si el modo `auto` usa el control (todo el pasado) cuando la reunión cabe, en vez de S2. Es lo que
   mejor resolvió el historial en la T4.
2. Alinear este corrector con el evaluador de Eduardo, para usar un solo criterio en el documento.
3. Una reunión nueva con gold, que no hayamos visto e idealmente larga, para medir sin sesgo y probar el RAG del
   modo `auto`.
4. Decidir si se agrega la validación de reemplazos (solo entre decisiones del mismo tema). Corrige el caso de
   falla 4, pero cambia el sistema ya medido.
