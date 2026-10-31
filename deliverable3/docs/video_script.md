# Guion del video · Entregable 3 (≤ 3 min)

Duración objetivo: **2:45**, con 15 s de margen. El texto de cada bloque se lee a un ritmo normal (unas 140 palabras por minuto). Lo que está en *cursiva* es lo que se ve en pantalla.

## Antes de grabar (no sale en el video)

1. En Colab, con GPU T4, abre `notebooks/D3_Colab.ipynb`.
2. En la celda 1 deja:
   - `MODE = 'DEMO'`;
   - `SOURCE = 'zip'` (o `'git'` cuando el repositorio ya esté subido);
   - `PERSIST_DIR = '/content/d3_demo'`. Es una carpeta nueva: así M01 se ejecuta de verdad y no se "reanuda" desde Drive.
3. Ejecuta las celdas 1 a 4. Instalan Ollama, descargan el modelo y cargan el código y el dataset (~3 min).
4. Deja abiertos en otra pestaña `Deliverable_3.pdf` y el repositorio.
5. Graba la pantalla con la Barra de juegos de Windows (`Win + Alt + R`) u OBS, en 1080p.

## Guion

### 0:00–0:20 · El problema

*PDF, sección 1: tabla "Why it is hard".*

> Convertimos la transcripción de una reunión en un acta: qué se decidió y quién hace qué, para cuándo. Lo difícil es que las reuniones cambian de opinión: de 56 decisiones en test, solo 26 son acuerdos directos. Ahí fallaba el Entregable 2, además de en plazos y estados de tareas.

### 0:20–0:45 · Los agentes

*PDF, el grafo. Señalar cada nodo con el cursor mientras se nombra.*

> Lo reconstruimos como tres agentes con el mismo modelo, Ministral 3B: Decisiones, Tareas y un Auditor que revisa el acta completa. En cada paso, cada agente decide si llama a una herramienta o entrega. El Auditor decide si el acta termina o vuelve a un especialista, con máximo dos revisiones, y unas barandas en código descartan los veredictos que el texto contradice.

### 0:45–1:55 · Demo en vivo con la reunión M01

*Colab: ejecutar la celda 5 (acelerar en la edición). Imprime solo el resumen: `Ollama OK.`, `[full] M01  64.0s  8 calls` y `decisions F1 0.667  tasks F1 0.667`.*

> Lo ejecutamos sobre la reunión M01 de test: 64 segundos y 8 llamadas al modelo. Veamos qué pasó dentro.

*Celda 6, bloque `[decisions paso 1] call_tools`: señalar `find_revision_cues` y su observación (u04: "dejemos pendiente el logo").*

> En el paso 1, Decisiones decide llamar a `find_revision_cues`, que le devuelve los turnos con cambios, como u04: "dejemos pendiente el logo". En el paso 2 entrega sus decisiones.

*Bloque `[tasks paso 1] call_tools`: señalar las observaciones de u33 y u22.*

> Tareas pide cinco plazos y verifica tres responsables. "El viernes 18 antes de las 17:00" pasa a una fecha exacta. Para "dos días después del piloto", la herramienta no adivina y devuelve nulo; el agente lo resuelve con la fecha del piloto.

*Bloque `[auditor paso 3] finish`: señalar la `Salida` (`wrong_state` sobre d01, `route: decisions`); luego `=== [baranda G3]` y `=== [router]`.*

> El Auditor dice que el logo pendiente tiene el estado mal y pide devolverlo a Decisiones. La baranda G3 revisa el texto: u04 sí dice "pendiente". Descarta el veredicto y la ruta pasa de `decisions` a `finish`.

*Línea `=== [finalize]`.*

> El Finalizador cierra con 8 decisiones y 5 tareas, cada una con el turno que la respalda.

*Celda 7: en el JSON, señalar d03 (`superseded`, "veinte minutos") y d05 (`final`, "quince minutos", `"supersedes": "d03"`); luego, en la tabla de métricas, `deadline_accuracy_matched 1.000`.*

> En el acta, el cambio de la demostración de veinte a quince minutos queda enlazado, y los cuatro plazos emparejados son correctos.

### 1:55–2:30 · Resultados

*PDF, sección 5: la figura de barras y luego la tabla.*

> Medimos sobre las 10 reuniones de test, con el mismo evaluador del Entregable 2. Frente al D2, el F1 estricto de tareas sube de 0,22 a 0,78; los plazos correctos, de 42 a 88 por ciento; y el estado correcto, de 55 a 94 por ciento. Pero las decisiones empeoran: el F1 baja de 0,67 a 0,56. Las ablaciones —quitar una técnica a la vez— lo explican: sin el ejemplo few-shot, que viene de reuniones de plantilla, las decisiones mejoran, y las barandas son lo que más aporta.

### 2:30–2:45 · Caso de falla y cierre

*PDF, sección 6 y luego el repositorio (`runs/test/traces/`).*

> El peor caso, la M09, muestra el límite: el agente de Decisiones fusiona una cadena de cambios en una sola decisión. Todas las trazas, los prompts versionados y el notebook para reproducir esta demo están en el repositorio.

## Después de grabar

1. Ejecuta la celda 9: descarga `d3_outputs.zip` con la traza de esta corrida.
2. Sube el video a YouTube como **No listado** (o a Drive, con "cualquier persona con el enlace") y copia el link.
3. Pasa el link y el zip: la traza del video se guarda en `runs/video/M01.jsonl` y el link se agrega al PDF y al README.
