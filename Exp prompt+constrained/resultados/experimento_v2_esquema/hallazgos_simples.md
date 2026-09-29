# Hallazgos automáticos de las pruebas (M01-M10)

Este informe compara el baseline directo con un pipeline de dos etapas:
- P1 extrae candidatos de forma estructurada.
- P2 los unifica en un acta final resolviendo dependencias y plazos.
Las rúbricas se mantuvieron secretas para el modelo, utilizándose únicamente para evaluación.

## M01
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 25.00 s | **Tiempo del Pipeline**: 81.97 s (P1: 33.22 s, P2: 48.75 s).
- **Resultados Baseline**: Recuperó 4/7 decisiones y 4/7 tareas.
- **Resultados Pipeline**: Recuperó 3/7 decisiones y 4/7 tareas.
  - *Decisiones omitidas*: Fecha y hora del piloto: Realizar el piloto el lunes 21 a las 10:00; Fecha y hora del piloto: Realizar el piloto el lunes 21 a las 16:00; Formato de la actividad: Demostración de veinte minutos seguida de encuesta; Uso de cámara en el piloto: No mostrar la funcionalidad de cámara durante el piloto
  - *Tareas omitidas*: Preparar un borrador del correo de invitación y enviarlo para revisión; Presentar la demostración técnica; Revisar el borrador del correo de invitación
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M02
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 41.94 s | **Tiempo del Pipeline**: 86.73 s (P1: 43.46 s, P2: 43.27 s).
- **Resultados Baseline**: Recuperó 4/6 decisiones y 6/6 tareas.
- **Resultados Pipeline**: Recuperó 1/6 decisiones y 5/6 tareas.
  - *Decisiones omitidas*: Herramienta para la encuesta: Usar Typeform; Alcance de la encuesta: Enviar la encuesta a los 640 clientes; Alcance de la encuesta: Realizar un piloto con 50 clientes equilibrados entre los tres segmentos; Fecha de envío: Enviar la encuesta el lunes 21 de septiembre; Plan ante baja respuesta: Definir una acción si responde menos del 10% de la muestra
  - *Tareas omitidas*: Monitorear la tasa de respuesta durante la semana posterior al envío
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M03
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 28.57 s | **Tiempo del Pipeline**: 50.85 s (P1: 25.00 s, P2: 25.85 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 5/12 tareas.
- **Resultados Pipeline**: Recuperó 2/6 decisiones y 3/12 tareas.
  - *Decisiones omitidas*: Tipo de stand: Contratar un stand con pantalla; Contenido de demostración: Mostrar solo el módulo de texto sin cámara; Cantidad de folletos: Imprimir 200 folletos; Cantidad de folletos: Imprimir 120 folletos y usar códigos QR
  - *Tareas omitidas*: Revisar el contrato del recinto y confirmar si incluye pantalla; Solicitar la estimación de asistentes al organizador; Presentar el proyecto durante la feria; Guiar la prueba de la aplicación durante la feria; Registrar los contactos de las personas interesadas; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Realizar el montaje del stand a las 07:00; Integrarse a la feria a las 09:00
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M04
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 21.73 s | **Tiempo del Pipeline**: 56.96 s (P1: 31.11 s, P2: 25.85 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 4/4 tareas.
  - *Decisiones omitidas*: Fecha de publicación: Publicar el jueves a las 18:00; Activación para clientes: Definir activación luego de evaluar el piloto interno
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M05
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 31.79 s | **Tiempo del Pipeline**: 54.13 s (P1: 25.20 s, P2: 28.93 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 4/4 tareas.
- **Resultados Pipeline**: Recuperó 2/5 decisiones y 4/4 tareas.
  - *Decisiones omitidas*: Fechas de sesiones: Martes y jueves de la primera semana de octubre; Fechas de sesiones: Lunes 5 y miércoles 7 de octubre a las 10:00; Visita presencial: Realizar visita el viernes 9 de octubre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M06
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 21.78 s | **Tiempo del Pipeline**: 65.25 s (P1: 34.08 s, P2: 31.17 s).
- **Resultados Baseline**: Recuperó 3/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 4/5 decisiones y 3/3 tareas.
  - *Decisiones omitidas*: Escritorios antiguos: Trasladar todos los escritorios
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M07
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 21.19 s | **Tiempo del Pipeline**: 43.62 s (P1: 23.66 s, P2: 19.95 s).
- **Resultados Baseline**: Recuperó 3/6 decisiones y 3/4 tareas.
- **Resultados Pipeline**: Recuperó 2/6 decisiones y 3/4 tareas.
  - *Decisiones omitidas*: Formato del informe: Presentación de veinte diapositivas; Fecha recurrente de envío: Último día hábil de cada mes; Fecha recurrente de envío: Segundo día hábil del mes siguiente; Fecha de envío del informe actual: Enviar el miércoles 4 de noviembre
  - *Tareas omitidas*: Compartir el formato final con el equipo
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M08
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 29.25 s | **Tiempo del Pipeline**: 58.13 s (P1: 25.90 s, P2: 32.23 s).
- **Resultados Baseline**: Recuperó 4/6 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 4/6 decisiones y 5/5 tareas.
  - *Decisiones omitidas*: Muestra de entrevistas: Entrevistar solo a usuarios frecuentes; Inicio de entrevistas: Iniciar el martes 10 de noviembre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M09
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 25.75 s | **Tiempo del Pipeline**: 41.81 s (P1: 19.27 s, P2: 22.54 s).
- **Resultados Baseline**: Recuperó 4/5 decisiones y 3/3 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 3/3 tareas.
  - *Decisiones omitidas*: Fecha de primera prueba: Realizar la primera prueba el viernes; Fecha de primera prueba: Realizar la primera prueba el lunes 16 de noviembre
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.

## M10
- **Prueba realizada**: Comparativa directa de Baseline versus Pipeline de dos etapas (P1 + P2).
- **Tiempo del Baseline**: 24.56 s | **Tiempo del Pipeline**: 67.97 s (P1: 31.65 s, P2: 36.32 s).
- **Resultados Baseline**: Recuperó 2/5 decisiones y 5/5 tareas.
- **Resultados Pipeline**: Recuperó 3/5 decisiones y 5/5 tareas.
  - *Decisiones omitidas*: Fecha de actividad: Viernes 18 de diciembre; Fecha de actividad: Miércoles 16 de diciembre a las 16:00
- *Casos para revisión manual*: Todas las métricas de coinciencia semántica son de carácter orientativo. Coincidencias o exclusiones dudosas requieren inspección manual directa en el archivo JSON mediante el utterance_id y exact_quote.
