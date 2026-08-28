# Prueba 01 - Transcripción de reunión simulada

## Metadatos entregados al modelo

- Fecha: 27 de agosto de 2026
- Hora: 09:30-10:08
- Tema declarado: cierre de pendientes y planificación del piloto del Portal Vecinal
- Participantes presentes:
  - Camila Rojas - jefa de proyecto
  - Diego Soto - desarrollo backend
  - Fernanda Leal - diseño UX/UI
  - Martín Pérez - aseguramiento de calidad
- Personas mencionadas que no participan en la reunión: Paula, Sergio y Andrés

## Transcripción

**[U001 | 09:30:04 | Camila]** Ya, partamos. Tenemos media hora... bueno, un poco más. Necesito que salgamos con una fecha real para el piloto y no con otro "vemos mañana".

**[U002 | 09:30:19 | Diego]** Antes: staging volvió, pero anoche duplicó invitaciones. No siempre; me pasó dos veces con la misma cuenta.

**[U003 | 09:30:32 | Fernanda]** ¿Eso explica los dos correos que me llegaron? Pensé que había apretado dos veces.

**[U004 | 09:30:44 | Camila]** Probablemente. La idea original era abrir mañana a las cinco, aunque con esto no sé.

**[U005 | 09:31:01 | Martín]** Mañana no lo firmo. Además del correo duplicado, en móvil el botón "Aceptar" queda debajo del teclado.

**[U006 | 09:31:15 | Diego]** Lo del teclado es front, eso no me...

**[U007 | 09:31:18 | Fernanda]** Sí, lo tengo yo, pero no es solo moverlo. El contraste del botón tampoco pasa AA.

**[U008 | 09:31:29 | Camila]** Entonces mañana descartado. ¿Lunes 31 a las cuatro?

**[U009 | 09:31:41 | Martín]** Si tengo una versión cerrada el lunes temprano, podría hacer humo al mediodía, pero una regresión completa no.

**[U010 | 09:31:54 | Camila]** Paula necesita avisar al cliente hoy. Bueno, necesita una fecha, no necesariamente hoy el correo.

**[U011 | 09:32:10 | Fernanda]** Yo puedo dejar las pantallas de alto contraste el lunes en la mañana.

**[U012 | 09:32:19 | Camila]** ¿No alcanzas mañana al mediodía? Aunque sea login, invitación y recuperación.

**[U013 | 09:32:28 | Fernanda]** Esas tres sí. El resto, no prometo. Mañana a las doce te dejo esas pantallas y las etiquetas definitivas de los botones.

**[U014 | 09:32:42 | Camila]** Perfecto, esas tres y etiquetas mañana viernes a las doce, a tu nombre.

**[U015 | 09:33:02 | Diego]** Para arreglar las invitaciones necesito la credencial del sandbox. Andrés dijo que la mandaba, pero no está.

**[U016 | 09:33:15 | Camila]** ¿Cuánto desde que llegue?

**[U017 | 09:33:21 | Diego]** Un día para reproducir y corregir; no quiero decir horas. Si Andrés la envía antes de mañana viernes a las doce, lo dejo listo el lunes a las seis. Si no, el lunes a primera hora les digo que no llego.

**[U018 | 09:33:43 | Martín]** Ahí el lunes a las cuatro tampoco existe.

**[U019 | 09:33:49 | Camila]** Sí, tienes razón. Igual anotemos lunes 31 a las cuatro como fecha tentativa mientras ordenamos lo demás.

**[U020 | 09:34:07 | Fernanda]** Cambiando de tema medio segundo: ¿seguimos con MailFast para los correos? Porque diseñé usando su plantilla.

**[U021 | 09:34:19 | Diego]** Yo no lo pondría. La licencia gratis agrega su logo y todavía no revisamos dónde guarda las direcciones.

**[U022 | 09:34:32 | Camila]** ¿Podemos usar el SMTP institucional solo para este piloto?

**[U023 | 09:34:40 | Diego]** Sí, para cuarenta cuentas aguanta. Para producción no.

**[U024 | 09:34:47 | Camila]** Ya: piloto con SMTP institucional. MailFast queda fuera del piloto y lo revisamos después con legal.

**[U025 | 09:35:01 | Martín]** Anoto. ¿Y la retención de los correos? En el documento dice treinta días, pero Sergio en el pasillo dijo seis meses.

**[U026 | 09:35:14 | Camila]** Eso no se decide con una conversación de pasillo. Yo le escribo a Sergio antes de mañana a las cinco y dejamos la duración pendiente hasta que responda por escrito.

**[U027 | 09:35:35 | Fernanda]** Perdón, me llegó un mensaje... listo. Para el onboarding propongo un botón de WhatsApp; bajaría harto las dudas.

**[U028 | 09:35:48 | Diego]** Eso abre otro consentimiento y además no tenemos número institucional conectado.

**[U029 | 09:35:57 | Martín]** Para el piloto yo lo sacaría. Podemos dejar un correo de soporte visible.

**[U030 | 09:36:06 | Camila]** De acuerdo: sin WhatsApp en el piloto; solo correo de soporte. Después vemos si vale la pena.

**[U031 | 09:36:22 | Diego]** Sobre métricas, alcancé a montar el dashboard con sesiones y embudo, pero consume bastante.

**[U032 | 09:36:33 | Camila]** Yo había pedido el dashboard para el piloto, ¿cierto?

**[U033 | 09:36:39 | Martín]** Sí, pero si cambia el comportamiento prefiero no sumar otra cosa. Con registro de ingreso y errores basta para diagnosticar.

**[U034 | 09:36:54 | Camila]** Bien. Decisión: para el piloto guardamos solo eventos de ingreso y error. El dashboard completo pasa a después del piloto.

**[U035 | 09:37:10 | Fernanda]** ¿La demostración con el cliente sigue presencial el miércoles? Reservé la sala chica.

**[U036 | 09:37:22 | Camila]** Era presencial, sí, a las once y media.

**[U037 | 09:37:29 | Diego]** Esa sala no tiene salida a la red de pruebas. Andrés la bloqueó la semana pasada.

**[U038 | 09:37:36 | Martín]** Hagámosla remota. Además puedo compartir la evidencia sin copiar archivos al notebook de la sala.

**[U039 | 09:37:49 | Camila]** Entonces cambia a remota, miércoles 2 a las once y media. Yo mando el enlace junto con el correo al cliente.

**[U040 | 09:38:05 | Fernanda]** Espera, si el piloto abre ese mismo miércoles, ¿la demo es antes o después?

**[U041 | 09:38:14 | Camila]** Abrimos a las diez y demostramos a las once y media. Esa es la fecha final: miércoles 2 de septiembre a las 10:00. Reemplaza mañana y el lunes tentativo.

**[U042 | 09:38:37 | Martín]** Para que yo firme eso, necesito el build el martes a las nueve como máximo.

**[U043 | 09:38:44 | Diego]** Si cierro el bug el lunes a las seis, puedo desplegar a staging esa misma noche.

**[U044 | 09:38:50 | Martín]** Ya. Yo hago la regresión el martes 1 entre nueve y una, y subo el informe antes de la una.

**[U045 | 09:39:04 | Camila]** Entonces yo envío la invitación al cliente el martes antes de las cuatro, pero solo si el informe de Martín sale sin bloqueadores. Si aparece uno, no se anuncia y nos reunimos.

**[U046 | 09:39:25 | Fernanda]** ¿Paula no iba a mandar esa invitación?

**[U047 | 09:39:29 | Camila]** No, Paula solo revisa el tono si alcanza. La responsable de enviarla soy yo.

**[U048 | 09:39:40 | Diego]** También me habían pedido documentar la API. Eso no entra antes del piloto.

**[U049 | 09:39:50 | Camila]** Entra como tarea tuya, pero sin fecha todavía. No bloquea el piloto.

**[U050 | 09:40:05 | Martín]** Hay otra cosa: quién responde el correo de soporte la tarde del lanzamiento. Yo puedo mirar hasta las dos, después estoy en capacitación.

**[U051 | 09:40:18 | Fernanda]** Yo tengo entrevista con usuarios. Quizás Paula, aunque ella ni siquiera está en esta reunión.

**[U052 | 09:40:31 | Camila]** No asignemos a alguien que no está. La cobertura de soporte queda pendiente; la cierro con Paula y operaciones fuera de esta reunión.

**[U053 | 09:40:45 | Diego]** Volviendo al bug: si no llega la credencial, ¿igual mostramos con datos falsos locales?

**[U054 | 09:40:56 | Martín]** Para demo quizá, para abrir cuentas reales no.

**[U055 | 09:41:02 | Camila]** Correcto. Sin credencial y sin regresión aprobada no se abre el piloto. La demo podría mantenerse con datos locales, pero eso lo decidimos el martes si ocurre.

**[U056 | 09:41:20 | Fernanda]** Entonces mis imágenes del lunes ya no... perdón, las de mañana sí siguen.

**[U057 | 09:41:28 | Camila]** Sí: viernes 28 a las doce, se mantiene.

**[U058 | 09:41:37 | Martín]** Por jugar al abogado del diablo: si el lunes a las diez está todo, podríamos volver a abrir el lunes a las cuatro.

**[U059 | 09:41:48 | Camila]** Prefiero que no. Queda miércoles 2 a las diez aunque terminemos antes; necesitamos la regresión completa.

**[U060 | 09:42:03 | Diego]** ¿Y si la regresión encuentra algo menor?

**[U061 | 09:42:08 | Martín]** Menor no bloquea. Bloqueador es duplicar invitaciones, perder datos o no poder aceptar desde móvil.

**[U062 | 09:42:21 | Camila]** Bien, usemos esa definición. Si no hay bloqueadores, seguimos. Si hay, se suspende el anuncio y replanificamos.

**[U063 | 09:42:38 | Fernanda]** Me tengo que ir a las diez menos cuarto. ¿Falta algo mío?

**[U064 | 09:42:44 | Camila]** Pantallas y etiquetas mañana a mediodía. Nada más asignado.

**[U065 | 09:42:52 | Diego]** Yo: invitaciones el lunes seis condicionado a la credencial; API sin fecha. Correcto.

**[U066 | 09:43:01 | Martín]** Regresión e informe el martes antes de la una.

**[U067 | 09:43:08 | Camila]** Y yo: Sergio mañana antes de las cinco, invitación el martes antes de las cuatro si QA aprueba, más el enlace remoto. Soporte queda pendiente.

**[U068 | 09:43:24 | Fernanda]** Listo, me fui. Bueno, sigo conectada pero sin cámara.

**[U069 | 09:43:31 | Camila]** Cerramos entonces. Después les mando el resumen, pero revisen que no cambie miércoles por lunes otra vez.
