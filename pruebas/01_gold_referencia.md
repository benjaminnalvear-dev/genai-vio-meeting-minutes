# Prueba 01 - Pauta de referencia reservada

> No entregar este archivo al modelo. Sirve para auditar su salida después de la ejecución.

## Fenómenos incluidos sin señalarlos en la transcripción

- Interrupciones y frases incompletas.
- Cambios de tema y retorno a asuntos anteriores.
- Personas mencionadas que no participan.
- Propuestas tentativas, rechazos y decisiones sustituidas.
- Cambio de fecha de lanzamiento más de una vez.
- Cambio de modalidad de una demostración.
- Tareas con y sin fecha.
- Tareas sujetas a una condición externa.
- Acuerdos implícitos confirmados posteriormente.
- Un asunto deliberadamente sin responsable.
- Fechas relativas que deben resolverse usando la fecha de la reunión.
- Una sugerencia tardía que no reemplaza la decisión final.

## Decisiones esperadas

1. **Apertura del piloto mañana a las 17:00 - descartada/sustituida.**
   - U004: “La idea original era abrir mañana a las cinco, aunque con esto no sé.”
   - U008: “Entonces mañana descartado.”
2. **Apertura tentativa el lunes 31 a las 16:00 - sustituida.**
   - U019: “anotemos lunes 31 a las cuatro como fecha tentativa”.
   - U041: “Reemplaza mañana y el lunes tentativo.”
3. **Apertura final del piloto el miércoles 2 de septiembre de 2026 a las 10:00.**
   - U041: “Esa es la fecha final: miércoles 2 de septiembre a las 10:00.”
   - U059 confirma que no vuelve al lunes.
4. **Usar SMTP institucional para el piloto; MailFast queda fuera y se revisa después.**
   - U024.
5. **No usar WhatsApp en el piloto; mostrar solo correo de soporte.**
   - U030.
6. **Registrar solo eventos de ingreso y error; dashboard completo después del piloto.**
   - U034.
7. **Demostración remota el miércoles 2 a las 11:30, sustituyendo la modalidad presencial.**
   - U036 establece el estado anterior; U039 establece el final.
8. **El piloto no abre sin credencial y regresión aprobada.**
   - U055.
9. **Los defectos menores no bloquean; duplicación de invitaciones, pérdida de datos o imposibilidad de aceptar desde móvil sí bloquean.**
   - U061-U062.

## Tareas esperadas

1. **Fernanda:** entregar pantallas de alto contraste de login, invitación y recuperación, más etiquetas definitivas.
   - Plazo final: 2026-08-28 12:00.
   - Evidencia: U013-U014, confirmada en U057 y U064.
2. **Diego:** corregir la duplicación de invitaciones.
   - Plazo: 2026-08-31 18:00.
   - Condición: Andrés debe entregar la credencial del sandbox antes de 2026-08-28 12:00; si no, Diego avisará el 31 a primera hora que no llega.
   - Evidencia: U017, resumida en U065.
3. **Martín:** ejecutar regresión el 2026-09-01 de 09:00 a 13:00 y subir informe antes de las 13:00.
   - Evidencia: U044, confirmada en U066.
4. **Camila:** enviar invitación al cliente antes de 2026-09-01 16:00.
   - Condición: informe de Martín sin bloqueadores; de lo contrario no anunciar y reunirse.
   - Evidencia: U045; U047 aclara que Paula no es responsable.
5. **Camila:** enviar el enlace de la demostración remota junto con el correo al cliente.
   - Plazo derivado del envío del correo: 2026-09-01 16:00, aunque conviene marcar una alerta porque U039 no da una hora propia para el enlace.
   - Evidencia: U039 y U067.
6. **Camila:** escribir a Sergio antes de 2026-08-28 17:00 para resolver la retención.
   - Evidencia: U026, confirmada en U067.
7. **Diego:** documentar la API.
   - Plazo: `null`.
   - No bloquea el piloto.
   - Evidencia: U049 y U065.

## Asuntos pendientes esperados

1. Duración de retención de correos, pendiente de respuesta escrita de Sergio. Camila gestiona la consulta antes del 28 a las 17:00. U025-U026.
2. Cobertura del correo de soporte durante la tarde del lanzamiento. Sin responsable ni plazo acordados dentro de la reunión. U050-U052 y U067.
3. Uso futuro de MailFast, a revisar después del piloto con legal. U024.
4. Posible continuidad de la demo con datos locales si falta la credencial. Solo se decidirá el martes si ocurre. U053-U055.

## Errores especialmente penalizados

- Asignar tareas a Paula, Sergio o Andrés.
- Reportar el lunes 31 como fecha final del piloto.
- Omitir la condición de la credencial en la tarea de Diego.
- Omitir la condición de QA en la invitación de Camila.
- Convertir la cobertura de soporte en tarea asignada.
- Informar WhatsApp o MailFast como herramientas aprobadas para el piloto.
- Inventar una duración final de retención.
- Usar citas aproximadas en vez de texto exacto.
