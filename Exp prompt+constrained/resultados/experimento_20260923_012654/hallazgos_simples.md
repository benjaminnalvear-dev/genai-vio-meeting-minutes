# Hallazgos automáticos de las pruebas (M01-M10)

Este informe compara el baseline directo con un pipeline de dos etapas:
- P1 extrae candidatos de forma estructurada.
- P2 los unifica en un acta final resolviendo dependencias y plazos.
Las rúbricas se mantuvieron secretas para el modelo, utilizándose únicamente para evaluación.

## M01
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 51.18 s | **Tiempo del Pipeline**: 60.69 s (P1: 29.72 s, P2: 30.98 s).
- **Resultados Baseline**: Recuperó 5/7 decisiones y 5/7 tareas.
- **Resultados Pipeline**: Recuperó 4/7 decisiones y 4/7 tareas.
  - *Decisiones omitidas*: Fecha y hora del piloto: Realizar el piloto el lunes 21 a las 16:00; Fecha y hora del piloto: Realizar el piloto el martes 22 a las 10:00; Formato de la actividad: Demostración de quince minutos, prueba guiada y encuesta
  - *Tareas omitidas*: Preparar un borrador del correo de invitación y enviarlo para revisión; Presentar la demostración técnica; Revisar el borrador del correo de invitación
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M02
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 37.13 s | **Tiempo del Pipeline**: 89.75 s (P1: 51.33 s, P2: 38.42 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 5/6 tareas.
- **Resultados Pipeline**: Recuperó 3/6 decisiones y 6/6 tareas.
  - *Decisiones omitidas*: Herramienta para la encuesta: Usar Typeform; Alcance de la encuesta: Enviar la encuesta a los 640 clientes; Alcance de la encuesta: Realizar un piloto con 50 clientes equilibrados entre los tres segmentos
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M03
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 38.28 s | **Tiempo del Pipeline**: 74.61 s (P1: 36.90 s, P2: 37.71 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 6/12 tareas.
- **Resultados Pipeline**: Recuperó 6/6 decisiones y 4/12 tareas.
  - *Tareas omitidas*: Revisar el contrato del recinto y confirmar si incluye pantalla; Presentar el proyecto durante la feria; Guiar la prueba de la aplicación durante la feria; Registrar los contactos de las personas interesadas; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Integrarse a la feria a las 09:00
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M04
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 25.46 s | **Tiempo del Pipeline**: 73.93 s (P1: 31.53 s, P2: 42.40 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 4/4 tareas.
  - *Decisiones omitidas*: Fecha de publicación: Publicar el lunes 28 a las 10:00; Activación para clientes: Definir activación luego de evaluar el piloto interno
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M05
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 28.91 s | **Tiempo del Pipeline**: 49.93 s (P1: 23.32 s, P2: 26.61 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 4/4 tareas.
- **Resultados Pipeline**: Recuperó 2/5 decisiones y 4/4 tareas.
  - *Decisiones omitidas*: Formato de inducción: Sesión presencial de jornada completa; Fechas de sesiones: Lunes 5 y miércoles 7 de octubre a las 10:00; Visita presencial: Realizar visita el viernes 9 de octubre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M06
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 23.94 s | **Tiempo del Pipeline**: 66.78 s (P1: 37.39 s, P2: 29.39 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 3/3 tareas.
  - *Decisiones omitidas*: Plan de traslado: Trasladar equipos críticos el lunes 12 y mobiliario el martes 13; Escritorios antiguos: Vender seis escritorios dañados y trasladar los restantes
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M07
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 26.29 s | **Tiempo del Pipeline**: 58.58 s (P1: 33.84 s, P2: 24.75 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 3/6 decisiones y 3/4 tareas.
  - *Decisiones omitidas*: Formato del informe: Página de indicadores y anexo descargable; Fecha recurrente de envío: Último día hábil de cada mes; Fecha recurrente de envío: Segundo día hábil del mes siguiente
  - *Tareas omitidas*: Compartir el formato final con el equipo
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M08
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 32.03 s | **Tiempo del Pipeline**: 56.57 s (P1: 27.08 s, P2: 29.49 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 4/6 decisiones y 5/5 tareas.
  - *Decisiones omitidas*: Muestra de entrevistas: Entrevistar a cinco usuarios frecuentes y cinco nuevos; Formato de entrevista: Entrevistas de cuarenta minutos con encuesta previa
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M09
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 22.84 s | **Tiempo del Pipeline**: 41.07 s (P1: 20.71 s, P2: 20.36 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 3/3 tareas.
  - *Decisiones omitidas*: Fecha de primera prueba: Realizar la primera prueba el viernes; Fecha de primera prueba: Realizar la primera prueba el lunes 16 de noviembre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M10
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 24.73 s | **Tiempo del Pipeline**: 55.38 s (P1: 26.99 s, P2: 28.39 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 5/5 tareas.
  - *Decisiones omitidas*: Fecha de actividad: Viernes 18 de diciembre; Fecha de actividad: Miércoles 16 de diciembre a las 16:00
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.
