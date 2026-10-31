# Guion del video · Entregable 3 (≤ 3 min)

El enunciado pide grabar la pantalla con el sistema corriendo sobre entradas reales, mostrando el pipeline, los mensajes intermedios entre agentes y la salida final. Por eso el video es el grafo (unos segundos, para ubicar el pipeline) y luego el Colab con la reunión M01.

Duración objetivo: **unos 2:20**. Lo que está en *cursiva* es lo que se ve en pantalla; lo que va con `>` es lo que se dice.

## Antes de grabar (no sale en el video)

1. En Colab, con GPU T4, abre `notebooks/D3_Colab.ipynb`. En la celda 1 deja:
   - `MODE = 'DEMO'`;
   - `SOURCE = 'zip'`;
   - `PERSIST_DIR = '/content/d3_demo'`. Es una carpeta nueva, para que M01 corra de verdad y no se "reanude".
2. Ejecuta las celdas 1 a 4 (instalan Ollama, descargan el modelo y cargan el código y el dataset).
3. Abre la imagen del grafo, [`agent_graph.png`](agent_graph.png), en otra pestaña o ventana.
4. Graba con la Barra de juegos de Windows (`Win + Alt + R`) u OBS, en 1080p.

## Guion

### 0:00–0:25 · El pipeline (imagen del grafo)

*Imagen `agent_graph.png`. Recorrer con el cursor de izquierda a derecha.*

> Nuestro sistema convierte la transcripción de una reunión en un acta: decisiones con su estado, y tareas con responsable y plazo. Son tres agentes con el mismo modelo, Ministral 3B: Decisiones, Tareas y un Auditor. Arriba están sus herramientas. Abajo, en rojo, el loop: el Auditor puede devolver el acta a un especialista, máximo dos veces. Las barandas y el Finalizador son código.

### 0:25–0:45 · La ejecución (celdas 1 y 5)

*Colab, celda 1: señalar `MODE = 'DEMO'`. Luego ejecutar la celda 5 (acelerar la espera en la edición).*

> Lo corremos sobre una reunión real de test, la M01. Primero verifica que el modelo responde y luego procesa la reunión: 64 segundos y 8 llamadas al modelo. Veamos los mensajes entre los agentes.

### 0:45–1:55 · Los mensajes entre agentes (celda 6)

*Bloque `[decisions paso 1] call_tools`: señalar `find_revision_cues` y su observación (u04: "dejemos pendiente el logo").*

> En el paso 1, el agente de Decisiones decide no responder todavía: llama a la herramienta `find_revision_cues`, que le devuelve los turnos donde alguien cambia de opinión, como u04: "dejemos pendiente el logo". En el paso 2 entrega sus decisiones.

*Bloque `[tasks paso 1] call_tools`: señalar las observaciones de u33 y u22.*

> Después, el agente de Tareas pide cinco cálculos de plazo y verifica tres responsables. "El viernes 18 antes de las 17:00" pasa a una fecha exacta. Para "dos días después del piloto", la herramienta no adivina y devuelve nulo; el agente lo resuelve con la fecha del piloto.

*Bloque `[auditor paso 3] finish`: señalar `"route": "decisions"`. Luego `=== [baranda G3]` y `=== [router]`. Hacer una pausa aquí.*

> Ahora el Auditor revisa todo y dice que la decisión del logo pendiente tiene el estado mal, y pide devolverla a Decisiones. Pero la baranda G3 revisa el texto: el turno u04 sí dice "pendiente". Descarta ese reclamo, y la ruta cambia de `decisions` a `finish`.

*Línea `=== [finalize]`.*

> Por eso no hay rondas de revisión, y el Finalizador cierra con 8 decisiones y 5 tareas.

### 1:55–2:20 · La salida final (celda 7)

*En el JSON, señalar d03 ("veinte minutos", `superseded`) y d05 ("quince minutos", `final`, `"supersedes": "d03"`). Luego, en la tabla de métricas, `deadline_accuracy_matched 1.000`.*

> Esta es el acta final. Cada decisión y cada tarea cita el turno que la respalda. El cambio de la demostración, de veinte a quince minutos, quedó enlazado, y los cuatro plazos emparejados son correctos. La traza de esta corrida, los prompts versionados y los resultados sobre las diez reuniones están en el repositorio.

## Después de grabar

1. Ejecuta la celda 9: descarga `d3_outputs.zip` con la traza de esta corrida.
2. Sube el video a YouTube como **No listado** y copia el link.
3. Pasa el link y el zip: la traza se guarda en el repositorio y el link se agrega al PDF y al README.
