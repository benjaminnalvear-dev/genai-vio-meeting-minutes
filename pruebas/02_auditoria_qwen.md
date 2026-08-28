# Prueba 02 - Auditoría de Qwen 3.5 4B

## Diseño controlado

- Misma transcripción, prompt y pauta reservada que la prueba de Ministral.
- Modelo: `qwen3.5:4b` de Ollama, ID local `2a654d98e6fb`.
- Arquitectura reportada: Qwen 3.5, 4.7B parámetros, cuantización Q4_K_M, 3.4 GB.
- Contexto: 8192 tokens.
- Temperatura: 0.
- Semilla: 42.
- Razonamiento interno: desactivado para mantener una comparación directa y el mismo presupuesto de salida.
- Formato solicitado a Ollama: JSON.
- Límite de salida: 3000 tokens.
- Codificación: lectura y transporte UTF-8 explícitos.
- Hardware: Intel i5-9300H, 15.8 GB RAM y GTX 1050 de 3 GB.

La pauta de referencia no fue incluida en el contexto del modelo. La salida cruda y las métricas de Ollama están preservadas en `02_salida_qwen_8k.json`.

## Métricas de ejecución

| Métrica | Resultado |
|---|---|
| Versión de Ollama | 0.33.1 |
| Tokens de entrada evaluados | 3727 |
| Tokens generados | 3000 |
| Razón de término | `length` |
| Duración total | 968.36 s (16 min 8.36 s) |
| Tiempo de evaluación de salida | 926.49 s |
| Velocidad aproximada | 3.24 tokens/s |
| Distribución observada | 75% CPU / 25% GPU |
| VRAM observada | aproximadamente 1.74 de 3 GB |
| Memoria residente observada durante las corridas | aproximadamente 3.1-3.5 GB |
| Memoria privada observada durante las corridas | aproximadamente 5.5-5.9 GB |

El modelo cargó y generó exitosamente en el equipo local. Por lo tanto, la prueba demuestra factibilidad de ejecución, aunque no cumplimiento completo de la tarea.

## Resultado estructural

| Criterio | Resultado observado |
|---|---|
| JSON sintácticamente válido | No; terminó dentro del octavo elemento de `action_items` |
| Terminación natural | No; agotó los 3000 tokens |
| Claves superiores iniciadas | 3 de 5: `meeting`, `decisions`, `action_items` |
| Decisiones completas antes del corte | 12 |
| Tareas completas antes del corte | 7, más una octava truncada |
| `pending_issues` y `review_alerts` | No producidos antes del corte |
| Fechas obsoletas de apertura representadas | 2 de 2: una `rejected` y una `superseded` |
| Rechazo de WhatsApp | Recuperado |

## Aciertos principales

- Recuperó la apertura descartada del día siguiente, la apertura tentativa del lunes y la fecha final del miércoles.
- Recuperó el rechazo de WhatsApp y de MailFast.
- Identificó las decisiones sobre métricas, demo remota y definición de bloqueadores.
- Recuperó correctamente varios responsables, entre ellos Camila, Diego, Fernanda y Martín.
- Fue aproximadamente 1.7 veces más rápido que Ministral en generación local.

## Errores de contenido y esquema

1. **Salida incompleta.** El modelo agotó el límite de 3000 tokens, dejó el JSON sin cerrar y no alcanzó las secciones `pending_issues` ni `review_alerts`.
2. **Estados fuera del esquema.** Usó `state: "pending"` dos veces dentro de `decisions`, aunque el esquema permitía solo `final`, `superseded` o `rejected`.
3. **Fechas relativas incorrectas.** Convirtió varias referencias correctamente comprendidas como texto en fechas calendario erróneas:
   - entrega de Fernanda: `2026-08-29 12:00` en vez de `2026-08-28 12:00`;
   - regresión de Martín: `2026-08-29 13:00` en vez de `2026-09-01 13:00`;
   - invitación de Camila: `2026-08-29 16:00` en vez de `2026-09-01 16:00`;
   - entrega de la credencial: `2026-08-29 12:00` en vez de `2026-08-28 12:00`.
4. **Tarea falsa para Paula.** Creó “Enviar aviso de fecha al cliente (Paula)” y la condicionó a la respuesta de Sergio, mezclando dos temas sin respaldo.
5. **Tarea impropia para Andrés.** Convirtió la credencial mencionada como dependencia externa en una tarea del acta, pese a que Andrés no participaba en la reunión.
6. **Cobertura de soporte mal asignada.** Creó una tarea acordada para Martín hasta las 14:00, aunque U052 deja expresamente la cobertura sin responsable.
7. **Fallback sobreafirmado.** Registró como decisión final que la demo con datos locales estaba aceptada condicionalmente; U055 dice que se decidiría el martes si la situación ocurría.
8. **Elementos mal clasificados.** Incluyó la documentación de API como decisión y también como tarea; la credencial y la cobertura pendiente también aparecieron dentro de `decisions`.
9. **Cita no exacta.** La evidencia atribuida a U041 combina texto de U039 y U041 con puntos suspensivos, por lo que no es una cita exacta de una intervención.
10. **Evidencia no concluyente.** Se observaron al menos seis enlaces de evidencia problemáticos, incluyendo:
    - U042, sobre el build, usada como evidencia del plazo de regresión;
    - U042 usada también como evidencia de una supuesta fecha de cobertura de soporte;
    - U026, sobre retención, usada como condición del aviso de fecha al cliente;
    - U062, que acepta una definición, usada sin U061 para respaldar la lista concreta de bloqueadores;
    - U008 y U019 usadas para afirmar que el lunes fue sustituido sin citar U041;
    - U055 usada para afirmar que el fallback local quedó aceptado, aunque la cita dice que se decidirá después.

## Comparación con Ministral

Qwen mostró una ventaja clara en seguimiento temporal: representó las dos fechas de apertura obsoletas y recuperó el rechazo de WhatsApp, mientras Ministral las omitió. También generó más rápido. Sin embargo, Qwen fue mucho más verboso, agotó el presupuesto, produjo JSON inválido y cometió más errores de normalización de fechas y clasificación de tareas.

El resultado apoya usar Qwen como candidato para resolución temporal, pero no como generador final sin límites de salida, validación de esquema, normalización determinista de fechas y verificación de evidencia.
