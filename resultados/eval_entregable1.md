# Evaluación contra 01_gold.json

| Métrica | 01_salida_ministral_8k.md | 02_salida_qwen_8k.json | 03_salida_phi4_mini_8k.json |
|---|---|---|---|
| JSON válido | sí | no | sí |
| Decisiones+pendientes F1 | 0.50 (5/14, pred 6) | 0.00 (0/14, pred 0) | 0.43 (5/14, pred 9) |
| Tareas F1 | 0.92 (6/7, pred 6) | 0.00 (0/7, pred 0) | 0.20 (1/7, pred 3) |
| Macro-F1 estados | 0.39 | 0.00 | 0.25 |
| Responsable correcto | 6/7 | 0/7 | 1/7 |
| Plazo correcto | 5/7 | 0/7 | 1/7 |
| Condición correcta | 3/7 | 0/7 | 0/7 |
| Precisión de evidencia | 0.86 (21 citas) | 0.00 (0 citas) | 0.42 (12 citas) |
| Citas textuales exactas | 1.00 | 0.00 | 0.83 |
| Afirmaciones sin respaldo | 0.17 (5/30) | 0.00 (0/0) | 0.65 (13/20) |
| Tiempo (s) | 1326 | 968 | 478 |

**Errores especialmente penalizados**

| Métrica | 01_salida_ministral_8k.md | 02_salida_qwen_8k.json | 03_salida_phi4_mini_8k.json |
|---|---|---|---|
| asigna_a_no_participante | 1 | 0 | 3 |
| lunes_31_como_final | no | no | sí |
| omite_condicion_credencial | no | tarea omitida | tarea omitida |
| omite_condicion_QA | no | tarea omitida | tarea omitida |
| soporte_como_tarea | no | no | sí |
| herramienta_rechazada_aprobada | no | no | no |
| inventa_retencion | no | no | no |
| citas_no_textuales | 0 | 0 | 2 |

## Detalle por salida

### 01_salida_ministral_8k.md

| Gold | Esperado | Ítem emparejado | Estado |
|---|---|---|---|
| D1 Abrir piloto mañana 28 a las 17:00 | superseded/rejected | (omitido) | - |
| D2 Apertura tentativa lunes 31 a las 16:00 | superseded | (omitido) | - |
| D3 Apertura final miércoles 2 de septiembre 10:00 | final | Fecha del piloto del Portal Vecinal Se decide abrir el piloto el miércoles 2 de septiembre | final ✓ |
| D4 SMTP institucional; MailFast fuera del piloto | final/rejected | Servicio de correos (MailFast) MailFast queda fuera del piloto y se revisará después con l | final ✓ |
| D5 Sin WhatsApp; solo correo de soporte | final/rejected | (omitido) | - |
| D6 Solo eventos de ingreso y error; dashboard después | final | Métricas del piloto Se decide usar solo eventos de registro de ingreso y errores para el p | final ✓ |
| D7a Demo presencial miércoles 11:30 (estado anterior) | superseded | (omitido) | - |
| D7b Demo remota miércoles 2 a las 11:30 | final | (omitido) | - |
| D8 No se abre sin credencial y regresión aprobada | final | (omitido) | - |
| D9 Defectos menores no bloquean; definición de bloqueador | final | (omitido) | - |
| P1 Duración de retención de correos | pending | Retención de correos La duración de retención de correos se deja pendiente hasta que Sergi | pending ✓ |
| P2 Cobertura del correo de soporte la tarde del lanzamiento | pending | Cobertura de soporte para el piloto: asignación pendiente a alguien que esté presente en l | pending ✓ |
| P3 Uso futuro de MailFast, revisar con legal | pending | (omitido) | - |
| P4 Demo con datos locales si falta credencial | pending | (omitido) | - |

| Tarea gold | Ítem emparejado | Responsable | Plazo | Condición |
|---|---|---|---|---|
| T1 Pantallas alto contraste + etiquetas | Corregir duplicación de invitaciones y asegurar que el botón 'Aceptar' en móvil sea accesi | Fernanda Leal ✓ | 2026-08-28 12:00 ✓ | Proporcionar pantallas de alto contraste y etiquetas definit ✗ |
| T2 Corregir duplicación de invitaciones | Corregir el bug de las invitaciones y obtener la credencial del sandbox de Andrés para el  | Diego Soto ✓ | 2026-08-31 18:00 ✓ | Si Andrés envía la credencial antes del viernes 28 a las 12: ✓ |
| T3 Regresión 1-sep 09:00-13:00 e informe | Realizar regresión completa y subir informe antes de las 1:00 AM del martes 1 de septiembr | Martín Pérez ✓ | 2026-09-01 01:00 ✗ | Informe debe incluir bloqueadores como duplicación de invita ✓ |
| T4 Enviar invitación al cliente | Enviar invitaciones al cliente antes de las 4:00 PM del martes 1 de septiembre si la regre | Camila Rojas ✓ | 2026-09-01 16:00 ✓ | Solo si el informe de regresión de Martín no tiene bloqueado ✓ |
| T5 Enviar enlace de demo remota con el correo | (omitida) | - | - | - |
| T6 Escribir a Sergio por la retención | Contactar a Sergio para definir la retención de correos antes del viernes 28 de agosto a l | Camila Rojas ✓ | 2026-08-28 17:00 ✓ | Necesita respuesta por escrito. ✗ |
| T7 Documentar la API | Documentar la API del piloto | Diego Soto ✓ | None ✓ | Sin fecha asignada, pero no bloquea el piloto. ✗ |

Ítems predichos sin correspondencia en el gold:

- Definición de retención de correos: pendiente hasta respuesta de Sergio.

### 02_salida_qwen_8k.json

JSON inválido: evaluado como salida vacía.

| Gold | Esperado | Ítem emparejado | Estado |
|---|---|---|---|
| D1 Abrir piloto mañana 28 a las 17:00 | superseded/rejected | (omitido) | - |
| D2 Apertura tentativa lunes 31 a las 16:00 | superseded | (omitido) | - |
| D3 Apertura final miércoles 2 de septiembre 10:00 | final | (omitido) | - |
| D4 SMTP institucional; MailFast fuera del piloto | final/rejected | (omitido) | - |
| D5 Sin WhatsApp; solo correo de soporte | final/rejected | (omitido) | - |
| D6 Solo eventos de ingreso y error; dashboard después | final | (omitido) | - |
| D7a Demo presencial miércoles 11:30 (estado anterior) | superseded | (omitido) | - |
| D7b Demo remota miércoles 2 a las 11:30 | final | (omitido) | - |
| D8 No se abre sin credencial y regresión aprobada | final | (omitido) | - |
| D9 Defectos menores no bloquean; definición de bloqueador | final | (omitido) | - |
| P1 Duración de retención de correos | pending | (omitido) | - |
| P2 Cobertura del correo de soporte la tarde del lanzamiento | pending | (omitido) | - |
| P3 Uso futuro de MailFast, revisar con legal | pending | (omitido) | - |
| P4 Demo con datos locales si falta credencial | pending | (omitido) | - |

| Tarea gold | Ítem emparejado | Responsable | Plazo | Condición |
|---|---|---|---|---|
| T1 Pantallas alto contraste + etiquetas | (omitida) | - | - | - |
| T2 Corregir duplicación de invitaciones | (omitida) | - | - | - |
| T3 Regresión 1-sep 09:00-13:00 e informe | (omitida) | - | - | - |
| T4 Enviar invitación al cliente | (omitida) | - | - | - |
| T5 Enviar enlace de demo remota con el correo | (omitida) | - | - | - |
| T6 Escribir a Sergio por la retención | (omitida) | - | - | - |
| T7 Documentar la API | (omitida) | - | - | - |

### 03_salida_phi4_mini_8k.json

| Gold | Esperado | Ítem emparejado | Estado |
|---|---|---|---|
| D1 Abrir piloto mañana 28 a las 17:00 | superseded/rejected | (omitido) | - |
| D2 Apertura tentativa lunes 31 a las 16:00 | superseded | fecha del piloto marzo 31 a las 4:00 | final ✗ |
| D3 Apertura final miércoles 2 de septiembre 10:00 | final | fecha de la demostración miércoles 2 de septiembre a las 10:00 | final ✓ |
| D4 SMTP institucional; MailFast fuera del piloto | final/rejected | uso del SMTP institucional aplicado para el piloto | final ✓ |
| D5 Sin WhatsApp; solo correo de soporte | final/rejected | (omitido) | - |
| D6 Solo eventos de ingreso y error; dashboard después | final | (omitido) | - |
| D7a Demo presencial miércoles 11:30 (estado anterior) | superseded | (omitido) | - |
| D7b Demo remota miércoles 2 a las 11:30 | final | demostración con el cliente remota | final ✓ |
| D8 No se abre sin credencial y regresión aprobada | final | (omitido) | - |
| D9 Defectos menores no bloquean; definición de bloqueador | final | (omitido) | - |
| P1 Duración de retención de correos | pending | retención de correos | pending ✓ |
| P2 Cobertura del correo de soporte la tarde del lanzamiento | pending | (omitido) | - |
| P3 Uso futuro de MailFast, revisar con legal | pending | (omitido) | - |
| P4 Demo con datos locales si falta credencial | pending | (omitido) | - |

| Tarea gold | Ítem emparejado | Responsable | Plazo | Condición |
|---|---|---|---|---|
| T1 Pantallas alto contraste + etiquetas | (omitida) | - | - | - |
| T2 Corregir duplicación de invitaciones | (omitida) | - | - | - |
| T3 Regresión 1-sep 09:00-13:00 e informe | (omitida) | - | - | - |
| T4 Enviar invitación al cliente | (omitida) | - | - | - |
| T5 Enviar enlace de demo remota con el correo | (omitida) | - | - | - |
| T6 Escribir a Sergio por la retención | (omitida) | - | - | - |
| T7 Documentar la API | documentación de la API | Diego ✓ | None ✓ | sin bloquear el piloto ✗ |

Ítems predichos sin correspondencia en el gold:

- regresión y informe martes 1 de septiembre antes de la 1:00
- envío de la invitación al cliente martes antes de las 4:00
- pantallas y etiquetas mañana a mediodía
- confusión sobre la licencia de MailFast
- envío de la credencial del sandbox a Diego
- cobertura de soporte

Citas que no aparecen textualmente en la intervención citada:

- U041: "Entonces fechas finales: miércoles 2 de septiembre a las 10:00."
- U022: "Yo no lo pondría. La licencia gratis agrega su logo y todavía no revisamos dónde guarda las direccio"
