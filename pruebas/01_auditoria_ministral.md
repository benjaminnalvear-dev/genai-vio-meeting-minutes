# Prueba 01 - Auditoría de Ministral 3 3B

## Diseño

- Reunión sintética realista de 69 intervenciones.
- Cuatro participantes declarados y tres personas únicamente mencionadas.
- Prompt directo único con esquema, reglas contra invención y evidencia obligatoria.
- Pauta de referencia escrita antes de ejecutar el modelo y mantenida fuera del contexto.
- Corrida exploratoria: contexto predeterminado de Ollama de 4096 tokens, temperatura 0.15.
- Corrida controlada principal: contexto 8192, temperatura 0, semilla 42 y formato JSON de Ollama.

## Resultado de la corrida exploratoria de 4K

La entrada superó el contexto disponible y Ollama recortó el inicio. El modelo respondió con un informe Markdown, no con JSON, no incluyó citas ni IDs y produjo errores severos de estado y fechas. Entre los errores observados:

- convirtió la retención pendiente en una retención vigente de 30 días;
- asignó la cobertura de soporte a Paula, aunque U052 prohíbe asignarla;
- interpretó “lunes a las seis” como “lunes 6 de septiembre”;
- desplazó el piloto del 2 al 8 de septiembre;
- convirtió la posible demo local, explícitamente pendiente, en una decisión afirmativa;
- revivió la apertura del lunes, rechazada posteriormente por Camila.

Esta corrida demuestra un fallo combinado de límite de contexto, seguimiento de instrucciones y resolución temporal. No debe compararse directamente con modelos ejecutados a 8K.

## Resultado de la corrida controlada de 8K

| Criterio | Resultado observado |
|---|---|
| JSON sintácticamente válido | Sí |
| Claves superiores requeridas | 5 de 5 |
| Terminación natural | Sí (`stop`) |
| Evidencia incluida en cada registro | Sí, pero no siempre respalda el campo |
| Estados `superseded` recuperados | 0 de 2 esperados |
| Ideas rechazadas recuperadas | 0; se omitió WhatsApp |
| Tareas producidas | 6 frente a 7 esperadas |
| Personas ausentes asignadas | 1: Paula como dueña de soporte |
| Fecha final del piloto | Correcta: 2026-09-02 10:00 |
| Plazo de regresión | Incorrecto: 01:00 frente a 13:00 |
| Duración total | 1326.31 s |
| Velocidad de generación | 1.86 tokens/s |

## Aciertos principales

- Recuperó la fecha final del piloto y evitó dejar el lunes como fecha final.
- Identificó correctamente la decisión sobre SMTP/MailFast.
- Identificó correctamente la reducción de métricas a eventos de ingreso y error.
- Recuperó correctamente las tareas de Camila de contactar a Sergio y enviar la invitación condicionada a QA.
- Recuperó el plazo de Diego y la dependencia general de la credencial.
- Produjo JSON analizable cuando se utilizó el modo JSON nativo de Ollama.

## Errores de contenido y esquema

1. **Estados temporales incompletos.** No creó registros `superseded` para la salida del viernes ni para el lunes tentativo, pese a la regla explícita del prompt.
2. **Rechazo omitido.** No informó que WhatsApp fue rechazado para el piloto.
3. **Decisiones finales omitidas.** No registró la demo remota, la condición de no abrir sin credencial y QA, ni la definición de bloqueadores.
4. **Mezcla de tareas.** Asignó a Fernanda “corregir duplicación de invitaciones”, responsabilidad de Diego, y mezcló ese bug con accesibilidad móvil y pantallas.
5. **Condición alterada.** Indicó que Diego debía “obtener” la credencial, aunque Andrés debía entregarla. También inventó que, si no llegaba, el despliegue se suspendía hasta recibirla; lo acordado era que Diego avisaría el lunes que no llegaba.
6. **Hora incorrecta.** Transformó “entre nueve y una” y “antes de la una” en 01:00, cuando el contexto establece 09:00-13:00.
7. **Tipo JSON incorrecto.** Escribió `"deadline": "null"` para la API, usando una cadena en vez de `null`.
8. **Estado fuera del esquema.** Usó `"state": "pending"` dentro de `decisions`, aunque el esquema permitía solo `final`, `superseded` o `rejected`.
9. **Responsable contradicho por la evidencia.** Asignó `Paula (operaciones)` a soporte usando U052, cuya cita dice literalmente “No asignemos a alguien que no está”. Además inventó que Paula pertenece a operaciones.
10. **Alerta obsoleta.** Sugirió revisar una apertura el lunes basándose solo en U058, sin aplicar U059, donde Camila rechaza expresamente volver al lunes.
11. **Evidencia no concluyente.** Usó U039, sobre la demo remota, como evidencia de la fecha de apertura; y U045, sobre el correo de Camila, como evidencia del plazo de Martín.
12. **Estado inventado.** Afirmó que el viernes 28 a las 12:00 fue una fecha tentativa anterior del piloto, pero esa fecha correspondía a la entrega de Fernanda.

## Conclusión para el estudio

Ampliar el contexto y forzar JSON corrigió la forma de la respuesta y varios errores de fecha de la corrida de 4K, pero no resolvió la tarea completa. Los fallos restantes son precisamente los que motivan el sistema propuesto: separación de temas, seguimiento del estado temporal, verificación de responsable/plazo/condición y comprobación de que la evidencia realmente implica el campo generado.
