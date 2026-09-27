# Detalles técnicos — experimento D2 (retrieval y tool use)

> La explicación simple está en [README.md](README.md). Este archivo guarda el registro técnico completo:
> cómo se mide, las tablas completas, la revisión del RAG, el modo `auto` y las correcciones hechas en el camino.
>
> **Corrida oficial vigente:** `resultados/tesla-t4-corrida2/` (Colab T4, 27-sep, las 8 condiciones con el código
> final). Las tablas de "Resultados oficiales" más abajo son de la corrida 1 (`resultados/tesla-t4/`, 22-sep); en
> ella S1–S3 dieron respuestas idénticas a la corrida 2, pero el baseline no.

Pregunta: ¿retrieval y tool use corrigen las fallas de Ministral 3 3B diagnosticadas en el D1, y cuánto?
Todo corre contra la misma transcripción (`pruebas/01_transcripcion_reunion_simulada.md`), el mismo
modelo (`ministral-3:3b`, digest `f04aa1c738f6`, el mismo del D1) y el mismo corrector.

## Condiciones

| Nombre | Archivo de resultados | Qué hace | Llamadas |
|---|---|---|---|
| **B** · Baseline | `baseline.json` | Prompt directo canónico del D1, una llamada (igual a `scripts/run_model_test.ps1`) | 1 |
| **S1** · Tool use, 1 pasada | `pipeline_tool_1pasada.json` | El modelo lee la transcripción completa y solo emite llamadas a herramientas; el código arma el acta | 2 |
| **S2** · Tool use por bloques | `pipeline_tool_bloques.json` | S1, pero la reunión se procesa en bloques de 8 intervenciones con un registro de estado | 18 |
| **S3** · S2 + RAG | `pipeline_tool_bloques_rag.json` | S2 + retrieval BM25: cada bloque recibe las 4 intervenciones anteriores más relacionadas | 18 |
| **S4** · S3 + verificación | `pipeline_tool_bloques_rag_verif.json` | S3 + verificación sí/no de cada ítem; si falla, BM25 propone evidencia alternativa | ~90 |
| **S3b** · S2 + RAG mejorado | `pipeline_tool_bloques_rag2.json` | S2 + una consulta BM25 por intervención, con stemmer (2 resultados c/u, tope 4) | 18 |
| **Control** · S2 + todo el pasado | `pipeline_tool_bloques_pasado.json` | S2 + todas las intervenciones anteriores. No es RAG: es el techo de cualquier buscador | 18 |

Todas usan `num_ctx` 8192, temperatura 0 y seed 42. **Recomendación actual: S2** (ver "Revisión del RAG");
hasta el 27-sep era S3.

## Qué pieza ataca cada error del D1

Los nombres son los de la tabla de Ministral del D1.

| Error del D1 (Ministral) | Pieza | Cómo |
|---|---|---|
| Historial apertura: 0/2 estados obsoletos | Tool use (registro de estado) + bloques | El modelo emite `crear_decision(..., reemplaza=[D1])`; el código marca lo anterior como `superseded` |
| Decisiones clave: omitió soporte solo por correo | Bloques + RAG | Cada bloque de 8 intervenciones se revisa aparte; BM25 trae el contexto anterior relacionado |
| Tareas: escribió 6/7; mezcló 2 | Tool use | Una llamada `crear_tarea` por acción y responsable; `confirmar` para resúmenes; consolidación de duplicados en código |
| Plazos: cambió 13:00 por 01:00 | Tool use (resolvedor temporal) | El modelo copia el plazo literal; `src/temporal.py` lo ancla a la intervención y lo convierte con reglas |
| Enlaces de evidencia: al menos 5 incorrectos | Tool use + verificación | Citas por ID (el código pega el texto exacto); verificación sí/no (S4) |
| Personas ausentes asignadas (auditoría D1) | Tool use (schema) | `responsable` es un enum con los participantes presentes |
| Salida final: errores de esquema (auditoría D1) | Tool use (schema) | La salida del modelo está restringida por JSON schema; el acta la arma el código |

## Reproducir

### Colab (hardware de respaldo declarado en el D1)

1. Abrir el notebook directo desde GitHub:
   <https://colab.research.google.com/github/benjaminnalvear-dev/genai-vio-meeting-minutes/blob/main/experimentos/rag_tool_use/notebooks/d2_colab.ipynb>
   (o subir `notebooks/d2_colab.ipynb` con `Archivo → Subir cuaderno`).
2. Elegir GPU T4 y ejecutar todo. La primera celda clona `main`; con
   `USAR_GITHUB = False` pide en cambio el zip del experimento.
3. Al final se descarga un zip con todos los resultados. Las cinco condiciones suman unos 7 minutos en la T4, más la instalación de Ollama y la descarga del modelo.

### Local (Windows, macOS o Linux)

Requisitos: Python ≥ 3.10 (solo biblioteca estándar) y Ollama corriendo con `ollama pull ministral-3:3b`.
En el notebook del D1 (1.86 tok/s) el conjunto completo tardaría horas; ahí conviene correr solo
`baseline` y `pipeline --config tool_bloques_rag`.

```bash
cd experimentos/rag_tool_use
python run.py todo                                 # B + S1–S4 + comparación
python run.py baseline                             # solo B
python run.py pipeline --config tool_bloques_rag   # solo S3 (solución propuesta)
python run.py tabla-d1 resultados/tesla-t4         # tabla con los criterios del D1
python run.py score ../../pruebas/01_salida_ministral_8k.md   # puntuar la salida guardada del D1
python -m unittest discover -s tests               # pruebas del resolvedor y del corrector
```

## Cómo se mide

- **`src/score.py`**: corrector automático contra `gold/01_gold.json` (la pauta de Benjamin en JSON).
  - Un ítem corresponde a uno del gold si cita al menos una de sus intervenciones de respaldo.
  - Una decisión (o un estado obsoleto) cuenta si su estado es el aceptado y, cuando el gold fija fecha
    y hora, el texto las menciona.
  - En la salida guardada del D1 reproduce la auditoría manual: 0/2 estados obsoletos, 6/7 tareas,
    01:00, Paula asignada y 2 errores de esquema.
- **`resultados/tesla-t4/adjudicacion_tareas.json`**: la fila "Tareas" (recuperadas, mezcladas, partidas,
  extra) se juzga a mano leyendo cada tarea, como en la auditoría del D1, porque el emparejamiento por IDs
  se equivoca cuando hay tareas duplicadas. Cada juicio lleva su razón.
- **Evidencia**: automática. Cuenta como incorrecta una cita que no es textual o cuyo ID no está entre los
  respaldos del ítem del gold (proxy). En la salida del D1 el proxy encuentra 3; la auditoría manual
  encontró al menos 5, así que el proxy cuenta de menos.
- **Cambios respecto de la pauta**, marcados en el JSON: `respaldo_extra` agrega intervenciones que también
  respaldan un ítem, y hay ítems opcionales que no suman ni restan: la demo presencial (D7b), la sugerencia
  tardía del lunes (D10) y el plazo `null` aceptado para el enlace de la demo (T5).

### Verificador sí/no (S4)

`calibracion_verificador.py` lo mide con 12 pares de **otra reunión**, no la evaluada.

| Formato de respuesta | Aciertos |
|---|---|
| JSON restringido `{"respalda": bool}` | 4/10: responde "no" a todo |
| Texto libre, "¿Muestra que…?" | 7/12: responde "sí" a casi todo |
| Texto libre, afirmación + "¿la intervención la respalda?" (el que se usa) | 10/12 |

Forzar JSON ayuda en la extracción, pero en la verificación sesga a Ministral hacia "no".

## Resultados oficiales: Colab, Tesla T4 (`resultados/tesla-t4/tabla_d1.md`)

Ollama 0.33.3; una corrida por condición. "D1 original" es la salida guardada en `pruebas/`, puntuada con
el mismo corrector.

| Criterio del D1 | D1 original | B | S1 | S2 | **S3** | S4 |
|---|---|---|---|---|---|---|
| Salida final | JSON válido; 2 errores de esquema | JSON válido; 2 errores | JSON válido; 0 errores | JSON válido; 0 errores | JSON válido; 0 errores | JSON válido; 0 errores |
| Historial apertura | 0/2 estados obsoletos; fecha final correcta | 0/2; fecha final correcta | 0/2; fecha final omitida | 1/2; fecha final omitida | **1/2; fecha final correcta** | 1/2; fecha final correcta |
| Decisiones clave: soporte solo por correo | omitida | recuperada | omitida | recuperada | recuperada | recuperada |
| Decisiones clave: demo remota, credencial + QA, bloqueadores | 0/3 | 0/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| Tareas | escribió 6; recuperó 6/7; mezcló 1 | escribió 6; recuperó 5/7; mezcló 1 | escribió 4; recuperó 3/7; mezcló 0 | escribió 19; recuperó 7/7; mezcló 0 | **escribió 16; recuperó 7/7; mezcló 0** | escribió 14; recuperó 7/7; mezcló 0 |
| Tareas partidas o duplicadas | 0 | 0 | 1 | 4 | 5 | 4 |
| Tareas extra (no están en el gold) | 0 | 1 | 0 | 8 | 4 | 3 |
| Plazos: regresión de Martín (13:00) | ✗ 01:00 | ✓ 13:00 | tarea omitida | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 |
| Plazos: errores de 12 h (am/pm) | 1 | 1 (Diego 06:00) | 0 | 0 | 0 | 0 |
| Plazos: otros incorrectos | 0 | 0 | 0 | 2 | 1 | 1 |
| Enlaces de evidencia incorrectos | 3/21 | 8/27 (30 %) | 3/16 | 13/91 (14 %) | 9/91 (10 %) | 8/74 (11 %) |
| Personas ausentes asignadas | 1 | 0 | 0 | 0 | 0 | 0 |
| Tiempo | 22m06s (i5-9300H + GTX 1050) | 46 s | 21 s | 116 s | 116 s | 123 s |

"Mezcló 1" significa una tarea que junta dos del gold, que es lo que el D1 llama "mezcló 2".

### Lectura

**Solución propuesta: S3 (tool use por bloques + RAG).** Fue la mejor corrida en la T4: igual o mejor
que S2 en todas las filas. El aporte propio del RAG no está demostrado (ver abajo); lo que sí funciona es
el tool use por bloques. Frente a B:

- **Mejora en lo que el D1 diagnosticó para Ministral:** el historial de apertura pasa de 0/2 a 1/2
  estados obsoletos manteniendo la fecha final; las tareas pasan de 5/7 con una mezcla a 7/7 sin mezclas;
  ya no hay errores de am/pm; los errores de esquema bajan a 0; la tasa de citas incorrectas baja del 30 %
  al 10 %.
- **No mejora:** "soporte solo por correo" ya salía bien en el baseline de la T4, y "regresión de Martín
  13:00" también. Esos dos errores del D1 no se reproducen en este hardware.
- **Empeora:** aparecen 5 tareas partidas y 4 extra (antes 0 y 1) y tarda 2.5× más (116 s contra 46 s).

**Qué aporta cada pieza:**
- **Tool use (S1):** elimina los errores formales, pero en una sola pasada omite mucho (3/7 tareas).
- **Bloques con registro (S2):** sube la cobertura (7/7 tareas, 1/2 estados obsoletos), pero en la T4
  perdió la fecha final: clasificó U041 como "modalidad de la demo".
- **RAG (S3):** en la T4, S3 tiene la fecha final que S2 perdió, 4 tareas extra en vez de 8 y 1 plazo
  incorrecto en vez de 2. **Pero esa mejora no se puede atribuir al contexto recuperado.** En el bloque de
  la fecha final (U041–U048), BM25 trajo U001, U002, U010 y U012, y no las propuestas de fecha anteriores
  (U008, U019). Además U001 aparece en 5 de 8 bloques solo por palabras genéricas ("piloto", "fecha"). En
  otros bloques sí trajo contexto útil: U044, U045 y U055 para el resumen final. En el Mac el historial
  queda igual con y sin RAG. Lo defendible es que S3 fue la mejor corrida, no que el RAG la causó.
- **Verificación (S4):** saca 1 tarea extra y 1 partida más, pero borra 2 pendientes que eran correctos
  (retención, U025; cobertura de soporte, U067). No compensa.

## Revisión del RAG (27-sep-2026; S3b y control solo en el Mac)

**Por qué falló la búsqueda de S3.** Hacía una sola consulta con el texto de las 8 intervenciones del bloque,
que mezclan varios temas, y comparaba palabras exactas: "abrimos" no calza con "abrir", ni "tentativo" con
"tentativa". En el bloque de la fecha final trajo U001, U002, U010 y U012, en vez de U004, U008 y U019.

**1. Calidad del buscador, sin modelo** (`python evaluar_retrieval.py`). Se cuentan las intervenciones
anteriores que, según el gold, tratan el mismo asunto que el bloque:

| Variante | Relevantes traídas | Precisión |
|---|---|---|
| S3 · una consulta por bloque | 6/19 (32 %) | 19 % |
| S3b · una consulta por intervención + stemmer | 7/19 (37 %) | 22 % |
| Sobre el registro + stemmer (explorado) | 7/19 (37 %) | 24 % |
| Control · todo el pasado | 19/19 (100 %) | 7 % |

Todas las variantes léxicas se quedan cerca del 40 %. Buscar por significado (embeddings) necesita otro
modelo: Ollama no entrega embeddings de `ministral-3:3b`, y un segundo modelo se sale del compromiso de un
solo modelo del D2.

**2. Efecto en el acta** (Apple M5; se compara solo dentro del mismo hardware). S3b y el control se
volvieron a correr el 27-sep después de corregir un bug que dejaba mal la última línea del mensaje
("Ids libres para contexto recuperado…"); los números de abajo son los corregidos.

| Métrica | S2 | S3 | S3b | Control |
|---|---|---|---|---|
| Historial apertura | 1/2; fecha final correcta | 1/2; correcta | 1/2; correcta | 1/2; correcta |
| Decisiones correctas /9 (precisión) | 7 (0.39) | 6 (0.29) | 6 (0.29) | 7 (0.37) |
| Tareas identificadas /7 (precisión) | 7 (0.37) | 7 (0.33) | 7 (0.33) | 7 (0.35) |
| Pendientes /4 | 1 | 1 | 1 | 3 |
| Plazos exactos | 5/7 | 5/7 | 4/7 | 5/7 |
| Citas tipo 3 (proxy) | 6 | 3 | 5 | 5 |
| Tokens de entrada / tiempo | 33 K / 207 s | 38 K / 236 s | 38 K / 211 s | 57 K / 355 s |

**Lectura.**
- El RAG mejorado trae algo mejor contexto (U019 aparece en el bloque de la fecha final), pero el acta no
  mejora frente a S2: queda igual o un poco peor.
- **Con todo el pasado a la vista (el techo), el acta queda prácticamente igual que S2**; solo mejora en
  pendientes (3 contra 1) y tarda 1.7× más. El cuello de botella no es la falta de contexto: el registro
  del tool use ya le da al modelo la memoria que necesita, y el error que queda es la confusión de tipo
  (registrar de más).
- En esta reunión (69 intervenciones, unos 4 K tokens, que caben enteras en el contexto) el RAG no aporta.
  Tiene sentido cuando la reunión no cabe; por eso quedó como regla automática en el modo `auto` (abajo).
- **Recomendación: S2 (tool use por bloques) como solución, y el RAG (S3, S3b y el control) como
  alternativa evaluada.** Pendiente: correr S3b y el control en Colab. En la T4, S2 perdió la fecha final
  (ver arriba); eso es parte de sus casos de falla.

## Uso con cualquier reunión (27-sep-2026)

```bash
python run.py acta ruta/a/reunion.md                      # modo auto (recomendado)
python run.py acta ruta/a/reunion.md --fecha 2026-10-01 --presentes "Ana Díaz, Luis Mora" --ausentes "Marta"
python run.py acta ruta/a/reunion.md --config baseline    # el prompt directo del D1, para comparar
python run.py acta ruta/a/reunion.md --gold ruta/gold.json   # puntuar si hay gold con la estructura de gold/01_gold.json
```

Deja en `resultados/<hardware>/actas/` el registro completo (`.json`) y el acta legible (`.md`).

**Formatos de entrada** (`src/transcript.py`): el canónico del proyecto (`**[U001 | 09:30:04 | Ana]** …`),
con hora (`[09:30] Ana: …`) o simple (`Ana: …`); en los dos últimos los IDs se asignan en orden y las
líneas sin hablante se pegan a la intervención anterior. La cabecera puede traer `Fecha:`, `Tema:`,
`Participantes:` y `Ausentes:`, o se pasan por línea de comandos. Sin fecha el programa se detiene, porque
no podría resolver "mañana" ni "el lunes". Todo el que habla se considera presente (con aviso). Si dos
personas comparten nombre de pila, se identifican con el nombre completo.

**Regla del RAG (modo `auto`, `pipeline.plan_context`).** Antes de cada llamada se estima el tamaño del
mensaje (2.5 caracteres por token, conservador: la 01 da unos 2.8):
- **Si el registro completo cabe** en `num_ctx` (8192) menos la salida (1500) y un margen (300), no se usa
  RAG: es exactamente S2. En la reunión 01 los 18 mensajes de `auto` son idénticos a los de S2.
- **Si no cabe** (reunión larga), se muestran solo los ítems del registro más relacionados con el bloque
  (BM25 con stemmer sobre el registro, desempatando por los más recientes) y, con lo que sobra del
  presupuesto, las intervenciones anteriores que trae la búsqueda por intervención (S3b).
- **En cualquier modo**, si el mensaje no cabe se recorta primero el contexto recuperado y después el
  registro, y queda anotado. Si Ollama reporta tantos tokens de entrada como el límite, se registra
  una advertencia de posible truncamiento. El baseline avisa si su entrada no cabe.

**Qué está probado y qué no.**
- Probado sin modelo (`tests/test_generalidad.py`): los tres formatos, la fecha faltante, los nombres
  repetidos, que la 01 se lee igual que antes, que `auto` pasa a RAG cuando el registro no cabe y que el
  mensaje queda dentro del límite.
- Probado con el modelo, una vez, en `ejemplos/feria_colegio_formato_simple.md`. Es una reunión de humo
  escrita para esto, de 25 intervenciones en formato simple y **sin gold**. Corrió de punta a punta en
  modo `auto` (eligió "sin RAG") y las 4 tareas reales salieron con responsable, plazo y condición
  correctos: gimnasio 02-10 15:00 si Marta firma; presupuesto 05-10 12:00; afiche 07-10; invitación
  09-10 17:00 si Marta aprueba. No asignó nada a los ausentes.
- Mostró los mismos límites que la 01: tareas y decisiones de más, y un error nuevo. En U009 el modelo
  marcó la fecha de la feria como reemplazada por la decisión del catering (`reemplaza` entre temas
  distintos) y el código lo aceptó.
- **No probado: una reunión larga real.** La regla del RAG para reuniones largas está implementada y
  probada en lo mecánico (cabe en el contexto), pero no se midió si mejora el acta. Hace falta una
  transcripción larga con gold.

### Casos de falla de S3

1. **Tareas partidas y extra (precisión).** Camila, que dirige la reunión, "revisa" o "confirma" cosas y
   el modelo lo registra como tarea suya ("revisar uso de SMTP institucional", U022–U024). T1 se parte en
   pantallas y etiquetas, y la oferta reemplazada del lunes (U011) queda como otra tarea. En bloques de 8
   intervenciones, el modelo ve cada frase sin el cierre que la resuelve.
2. **Plazo con la expresión equivocada.** Para "mandar el enlace de la demo" (T5), el modelo copió "miércoles
   2 a las once y media" (la hora de la demo) como plazo del envío. El resolvedor la convierte bien
   (02-09 11:30), pero es la expresión equivocada. El tool use saca el error de la conversión (am/pm) y lo
   deja en la elección de la expresión.
3. **Un estado obsoleto se registra como decisión positiva.** La apertura "mañana a las cinco" (U004–U008)
   quedó como decisión final "descartar la fecha original" en vez de como propuesta rechazada, así que el
   historial queda en 1/2.

### Límites

- n = 1 transcripción y una corrida por condición y hardware: las diferencias entre S2, S3 y S4 son del
  tamaño del ruido entre hardware (Mac contra T4).
- La salida depende del hardware. Mac y T4 usan la misma versión de Ollama y la misma entrada (4190
  tokens), pero el baseline dio JSON cortado en el Mac y válido en la T4.
- Los prompts y el verificador se ajustaron mirando esta transcripción (los ejemplos y la calibración usan
  otra reunión, pero las decisiones de diseño no). Hace falta una transcripción nueva, no vista.
- El proxy de evidencia no detecta citas del ítem correcto que no respaldan el campo específico.
- En el notebook del D1 (1.86 tok/s), S3 genera 2.7× más tokens que el baseline: no es viable para el video
  en ese equipo; en Colab sí.

### Correcciones posteriores a la corrida de Colab

- **Corrector:** contaba un estado obsoleto con la fecha equivocada como recuperado. Corregido: ahora exige
  estado y fecha. Solo cambia la fila "Historial apertura"; los números de arriba ya usan el criterio
  corregido.
- **Consolidación de duplicados:** una decisión podía quedar "reemplazada por sí misma". Corregido.
  `pipeline.replay` vuelve a aplicar las llamadas guardadas de S2 y S3 con el código nuevo sin llamar al
  modelo: la tabla del D1 sale idéntica, así que no hizo falta volver a correr en Colab.
- Los archivos `pipeline_tool_completo` y `pipeline_final` se renombraron a `pipeline_tool_1pasada` y
  `pipeline_tool_bloques_rag_verif`; el campo `condicion_nombre_original` guarda el nombre anterior.
