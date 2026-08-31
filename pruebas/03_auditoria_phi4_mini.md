# Prueba 03 - Auditoría de Phi-4 Mini

## Diseño controlado

- Misma transcripción, prompt y pauta reservada que las pruebas de Ministral y Qwen.
- Modelo: `phi4-mini:latest` de Ollama, ID local `78fad5d182a7`.
- Arquitectura reportada: Phi-3, 3.8B parámetros, contexto máximo 131072 y cuantización Q4_K_M, 2.5 GB.
- Contexto de prueba: 8192 tokens.
- Temperatura: 0.
- Semilla: 42.
- Razonamiento interno: desactivado.
- Formato solicitado a Ollama: JSON.
- Límite de salida: 3000 tokens.
- Codificación: lectura y transporte UTF-8 explícitos.
- Hardware: Intel i5-9300H, 15.8 GB RAM y GTX 1050 de 3 GB.

La pauta de referencia no fue incluida en el contexto. La salida cruda y las métricas de Ollama están preservadas en `03_salida_phi4_mini_8k.json`.

## Métricas de ejecución

| Métrica | Resultado |
|---|---|
| Versión de Ollama | 0.33.2 |
| Tokens de entrada evaluados | 3283 |
| Tokens generados | 1211 |
| Razón de término | `stop` |
| Duración total | 477.65 s (7 min 57.65 s) |
| Tiempo de evaluación de salida | 412.78 s |
| Velocidad aproximada | 2.93 tokens/s |
| Distribución observada | 65% CPU / 35% GPU |
| VRAM observada | aproximadamente 1.49 de 3 GB |

Phi fue el modelo más rápido de los tres en tiempo total y finalizó sin agotar el presupuesto. El equipo pudo mantener los tres modelos instalados; no fue necesario borrar Ministral ni Qwen.

## Resultado estructural

| Criterio | Resultado observado |
|---|---|
| JSON sintácticamente válido | Sí |
| Terminación natural | Sí (`stop`) |
| Claves superiores requeridas | 5 de 5 |
| Decisiones producidas | 7 |
| Tareas producidas | 3 |
| Asuntos pendientes producidos | 2 |
| Alertas producidas | 1 |
| Estados `superseded` recuperados | 0 de 2 esperados |
| Rechazo de WhatsApp | Omitido |
| Tareas esperadas reconocidas sin cambiar tarea/responsable | 1 de 7: documentación de API |

## Aciertos principales

- Produjo JSON válido, completo en sus cinco secciones y terminó naturalmente con solo 1211 tokens.
- Recuperó correctamente el uso de SMTP institucional y la exclusión de MailFast durante el piloto.
- Recuperó correctamente que la demostración sería remota el miércoles 2 a las 11:30.
- Reconoció la documentación de la API como tarea de Diego, sin fecha y sin bloquear el piloto, aunque serializó el plazo con un tipo incorrecto.
- Generó aproximadamente 2.8 veces más rápido en tiempo total que Ministral y 2 veces más rápido que Qwen.

## Errores de contenido y esquema

1. **Fecha final del piloto perdida.** Marcó el lunes tentativo como decisión final, cambió agosto por “marzo 31” y omitió la apertura final del miércoles 2 de septiembre a las 10:00.
2. **Historia temporal omitida.** No representó como `superseded` ni la apertura del viernes ni la del lunes; recuperó 0 de 2 estados obsoletos.
3. **Decisiones finales omitidas.** No registró el rechazo de WhatsApp, el alcance reducido de eventos, la regla de no abrir sin credencial y regresión aprobada ni la definición de bloqueadores.
4. **Tareas clasificadas como decisiones.** Registró como decisiones la regresión de Martín, el correo condicionado de Camila y las pantallas de Fernanda.
5. **Apertura confundida con demostración.** Atribuyó las 10:00 de U041 a la demostración, aunque U039 fija la demo a las 11:30 y U041 usa las 10:00 para abrir el piloto.
6. **Cobertura de tareas muy baja.** Solo reconoció 1 de 7 tareas esperadas sin cambiar tarea o responsable. Omitió las entregas de Fernanda, la corrección de Diego, la regresión de Martín y las tres tareas de Camila.
7. **Tareas falsas para personas ausentes.** Asignó a Andrés el envío de la credencial y a Paula la cobertura de soporte. U052 prohíbe expresamente asignar a alguien ausente y deja la cobertura pendiente.
8. **Normalización temporal incorrecta.** Dejó “mañana viernes” y “sin fecha” como cadenas fuera del formato; interpretó “antes de la una” como 01:00 y “antes de las cuatro” como 04:00 en vez de 13:00 y 16:00.
9. **`null` inválido.** Usó las cadenas `"null"` y `"sin fecha"` en campos que exigían el valor JSON `null` o una fecha normalizada.
10. **Asuntos pendientes mal atribuidos.** Convirtió una observación de privacidad de MailFast en “confusión sobre la licencia” y atribuyó a Sergio la propiedad de la retención, aunque Camila se comprometió a consultarlo y la duración quedó sin resolver.
11. **Citas no exactas.** La cita atribuida a U041 fue reescrita y la atribuida a U022 pertenece a otra intervención. Diez de doce fragmentos sí eran extractos textuales, pero exactitud textual no implicó evidencia correcta.
12. **Evidencia no concluyente.** Al menos nueve enlaces no respaldaron la clasificación o los campos generados, incluidos U019 como fecha final, U044/U045/U064 como decisiones, U017 como tarea de Andrés, U052 como tarea de Paula y U026 como plazo/propiedad de Sergio.

## Comparación con Ministral y Qwen

Phi mejoró la disciplina de salida respecto de Qwen: entregó JSON válido, incluyó las cinco secciones y no agotó los 3000 tokens. También fue el más rápido en tiempo total. Sin embargo, tuvo la menor cobertura semántica: perdió la fecha final del piloto, no recuperó ningún estado sustituido, omitió el rechazo de WhatsApp y solo reconoció una de las siete tareas esperadas sin cambiar su naturaleza o responsable.

El resultado no respalda usar Phi como generador directo del acta. Su posible función como verificador debe evaluarse con una entrada más estrecha y estructurada, donde solo deba validar afirmaciones contra evidencia, no reconstruir toda la reunión en una sola respuesta.
