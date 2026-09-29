# Hallazgos automáticos de las pruebas (M01-M10)

Este informe compara el baseline directo con un pipeline de dos etapas:
- P1 extrae candidatos de forma estructurada.
- P2 los unifica en un acta final resolviendo dependencias y plazos.
Las rúbricas se mantuvieron secretas para el modelo, utilizándose únicamente para evaluación.

## M01
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 27.50 s | **Tiempo del Pipeline**: 51.44 s (P1: 28.76 s, P2: 22.68 s).
- **Resultados Baseline**: Recuperó 4/7 decisiones y 4/7 tareas.
- **Resultados Pipeline**: Recuperó 3/7 decisiones y 4/7 tareas.
  - *Decisiones omitidas*: Fecha y hora del piloto: Realizar el piloto el lunes 21 a las 16:00; Fecha y hora del piloto: Realizar el piloto el martes 22 a las 10:00; Formato de la actividad: Demostración de quince minutos, prueba guiada y encuesta; Uso de cámara en el piloto: No mostrar la funcionalidad de cámara durante el piloto
  - *Tareas omitidas*: Preparar un borrador del correo de invitación y enviarlo para revisión; Presentar la demostración técnica; Revisar el borrador del correo de invitación
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M02
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 33.10 s | **Tiempo del Pipeline**: 64.96 s (P1: 36.49 s, P2: 28.47 s).
- **Resultados Baseline**: Recuperó 5/6 decisiones y 6/6 tareas.
- **Resultados Pipeline**: Recuperó 3/6 decisiones y 6/6 tareas.
  - *Decisiones omitidas*: Herramienta para la encuesta: Usar Typeform; Alcance de la encuesta: Enviar la encuesta a los 640 clientes; Alcance de la encuesta: Realizar un piloto con 50 clientes equilibrados entre los tres segmentos
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M03
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 23.18 s | **Tiempo del Pipeline**: 41.27 s (P1: 20.54 s, P2: 20.73 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 5/12 tareas.
- **Resultados Pipeline**: Recuperó 4/6 decisiones y 4/12 tareas.
  - *Decisiones omitidas*: Contenido de demostración: Mostrar texto y voz con audífonos; no mostrar cámara; Cantidad de folletos: Imprimir 120 folletos y usar códigos QR
  - *Tareas omitidas*: Revisar el contrato del recinto y confirmar si incluye pantalla; Presentar el proyecto durante la feria; Guiar la prueba de la aplicación durante la feria; Registrar los contactos de las personas interesadas; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Integrarse a la feria a las 09:00
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M04
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 16.80 s | **Tiempo del Pipeline**: 42.64 s (P1: 24.12 s, P2: 18.52 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 3/4 tareas.
  - *Decisiones omitidas*: Fecha de publicación: Publicar el jueves a las 18:00; Activación para clientes: Definir activación luego de evaluar el piloto interno
  - *Tareas omitidas*: Consolidar los comentarios del piloto interno
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M05
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 21.95 s | **Tiempo del Pipeline**: 44.35 s (P1: 19.88 s, P2: 24.48 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 4/4 tareas.
- **Resultados Pipeline**: Recuperó 2/5 decisiones y 4/4 tareas.
  - *Decisiones omitidas*: Fechas de sesiones: Martes y jueves de la primera semana de octubre; Fechas de sesiones: Lunes 5 y miércoles 7 de octubre a las 10:00; Visita presencial: Realizar visita el viernes 9 de octubre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M06
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 18.05 s | **Tiempo del Pipeline**: 41.86 s (P1: 22.29 s, P2: 19.57 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 4/5 decisiones y 3/3 tareas.
  - *Decisiones omitidas*: Fecha de mudanza: Realizar toda la mudanza el sábado 10
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M07
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 17.13 s | **Tiempo del Pipeline**: 45.57 s (P1: 26.06 s, P2: 19.51 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 2/6 decisiones y 3/4 tareas.
  - *Decisiones omitidas*: Formato del informe: Presentación de veinte diapositivas; Fecha recurrente de envío: Último día hábil de cada mes; Fecha recurrente de envío: Segundo día hábil del mes siguiente; Fecha de envío del informe actual: Enviar el miércoles 4 de noviembre
  - *Tareas omitidas*: Compartir el formato final con el equipo
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M08
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 22.81 s | **Tiempo del Pipeline**: 46.45 s (P1: 20.54 s, P2: 25.91 s).
- **Resultados Baseline**: Recuperó 4/6 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 4/6 decisiones y 5/5 tareas.
  - *Decisiones omitidas*: Muestra de entrevistas: Entrevistar solo a usuarios frecuentes; Inicio de entrevistas: Iniciar el martes 10 de noviembre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M09
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 16.41 s | **Tiempo del Pipeline**: 34.98 s (P1: 18.93 s, P2: 16.05 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 4/5 decisiones y 2/3 tareas.
  - *Decisiones omitidas*: Fecha de primera prueba: Realizar la primera prueba el lunes 16 de noviembre
  - *Tareas omitidas*: Revisar la conciliación
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M10
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 17.00 s | **Tiempo del Pipeline**: 45.18 s (P1: 23.90 s, P2: 21.28 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 2/5 decisiones y 4/5 tareas.
  - *Decisiones omitidas*: Formato de actividad de cierre: Evento presencial para todo el equipo; Fecha de actividad: Viernes 18 de diciembre; Fecha de actividad: Miércoles 16 de diciembre a las 16:00
  - *Tareas omitidas*: Consultar disponibilidad de presencia
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.
