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

> Nuestro sistema convierte la transcripción de una reunión en un acta: qué se decidió y quién hace qué, para cuándo. El problema es que las reuniones reales cambian de opinión: en nuestras 10 reuniones de prueba, de 56 decisiones solo 26 son acuerdos directos. El resto fueron reemplazadas, rechazadas o quedaron pendientes. El sistema del Entregable 2 fallaba justo ahí, y también en los plazos y en el estado de las tareas.

### 0:20–0:45 · Los agentes

*PDF, el grafo. Señalar cada nodo con el cursor mientras se nombra.*

> Lo reconstruimos como tres agentes con el mismo modelo, Ministral 3B. El agente de Decisiones extrae decisiones y sus cambios; el de Tareas, responsables y plazos; y el Auditor revisa el acta completa. Cada agente decide en cada paso si llama a una herramienta —por ejemplo, la que calcula una fecha relativa— o si entrega su resultado. El Auditor decide si el acta termina o vuelve a un especialista, con un máximo de dos revisiones. Unas barandas en código descartan los veredictos que las herramientas contradicen.

### 0:45–1:50 · Demo en vivo con la reunión M01

*Colab: ejecutar la celda 5. Se ve la salida en vivo.*

> Ahora lo ejecutamos sobre una reunión real de test, la M01.

*Mientras corre (se puede acelerar en la edición):*

> Cada línea es una llamada al modelo: primero Decisiones, luego Tareas, luego el Auditor.

*Celda 6: recorrer la traza de arriba hacia abajo.*

> Esta es la traza: los mensajes entre agentes. Aquí el agente de Decisiones pidió la herramienta `find_revision_cues` y recibió los turnos donde alguien cambia de opinión. Aquí Tareas usó `resolve_deadline` para convertir "hoy antes de las seis" en una fecha exacta.

*Detenerse en las líneas `[baranda …]` y `[router]`.*

> Aquí el Auditor pidió revisar una decisión, pero la baranda rechazó ese veredicto: el turno citado sí dice "pendiente". Por eso la ruta queda en `finish` y el acta pasa al Finalizador.

*Celda 7: el acta final en JSON.*

> Y esta es el acta final. Cada decisión y tarea cita el turno que la respalda.

**Nota:** si la ejecución en vivo toma otra ruta (por ejemplo, una ronda de revisión), narra lo que aparezca en pantalla: "el Auditor marcó X, se devolvió a Y". Lo importante es que se vean los mensajes entre agentes.

### 1:50–2:30 · Resultados

*PDF, sección 5: la figura de barras y luego la tabla.*

> Medimos sobre las 10 reuniones de test, con el mismo evaluador del Entregable 2. Frente al D2, el F1 estricto de tareas sube de 0,22 a 0,78; los plazos correctos, de 42 a 88 por ciento; y el estado correcto, de 55 a 94 por ciento. Pero las decisiones empeoran: el F1 baja de 0,67 a 0,56. Las ablaciones —quitar una técnica a la vez— lo explican: sin el ejemplo few-shot, que viene de reuniones de plantilla, las decisiones mejoran, y las barandas son lo que más aporta.

### 2:30–2:45 · Caso de falla y cierre

*PDF, sección 6 y luego el repositorio (`runs/test/traces/`).*

> El peor caso, la M09, muestra el límite: el agente de Decisiones fusiona una cadena de cambios en una sola decisión. Todas las trazas, los prompts versionados y el notebook para reproducir esta demo están en el repositorio.

## Después de grabar

1. Ejecuta la celda 9: descarga `d3_outputs.zip` con la traza de esta corrida.
2. Sube el video a YouTube como **No listado** (o a Drive, con "cualquier persona con el enlace") y copia el link.
3. Pasa el link y el zip: la traza del video se guarda en `runs/video/M01.jsonl` y el link se agrega al PDF y al README.
