# Prueba 01 - Salida de Ministral 3 3B con contexto 8K

## Configuración observada

- Modelo: `ministral-3:3b`
- ID local: `f04aa1c738f6`
- Contexto: 8192 tokens
- Temperatura: 0
- Semilla: 42
- Formato solicitado a Ollama: JSON
- Límite de salida: 3000 tokens
- Tokens de entrada evaluados: 4196
- Tokens generados: 2386
- Razón de término: `stop`
- Duración total: 1326.31 s (22 min 6.31 s)
- Velocidad aproximada de generación: 1.86 tokens/s
- Distribución observada durante la ejecución: 82% CPU / 18% GPU

## Respuesta cruda

```json
{
  "meeting": {
    "date": "2026-08-27",
    "topic": "cierre de pendientes y planificación del piloto del Portal Vecinal"
  },
  "decisions": [
    {
      "topic": "Fecha del piloto del Portal Vecinal",
      "outcome": "Se decide abrir el piloto el miércoles 2 de septiembre a las 10:00 AM, reemplazando las fechas tentativas anteriores (lunes 31 a las 4 PM y viernes 28 a las 12 PM).",
      "state": "final",
      "evidence": [
        {
          "utterance_id": "U041",
          "exact_quote": "Esa es la fecha final: miércoles 2 de septiembre a las 10:00."
        },
        {
          "utterance_id": "U039",
          "exact_quote": "Entonces cambia a remota, miércoles 2 a las once y media. Yo mando el enlace junto con el correo al cliente."
        }
      ]
    },
    {
      "topic": "Métricas del piloto",
      "outcome": "Se decide usar solo eventos de registro de ingreso y errores para el piloto, excluyendo el dashboard completo.",
      "state": "final",
      "evidence": [
        {
          "utterance_id": "U034",
          "exact_quote": "Para el piloto guardamos solo eventos de ingreso y error. El dashboard completo pasa a después del piloto."
        }
      ]
    },
    {
      "topic": "Servicio de correos (MailFast)",
      "outcome": "MailFast queda fuera del piloto y se revisará después con legal.",
      "state": "final",
      "evidence": [
        {
          "utterance_id": "U024",
          "exact_quote": "Piloto con SMTP institucional. MailFast queda fuera del piloto y lo revisamos después con legal."
        }
      ]
    },
    {
      "topic": "Retención de correos",
      "outcome": "La duración de retención de correos se deja pendiente hasta que Sergio responda por escrito antes del viernes 28 de agosto a las 5:00 PM.",
      "state": "pending",
      "evidence": [
        {
          "utterance_id": "U026",
          "exact_quote": "Yo le escribo a Sergio antes de mañana a las cinco y dejamos la duración pendiente hasta que responda por escrito."
        }
      ]
    }
  ],
  "action_items": [
    {
      "task": "Corregir duplicación de invitaciones y asegurar que el botón 'Aceptar' en móvil sea accesible (alto contraste y ubicación)",
      "assignee": "Fernanda Leal",
      "deadline": "2026-08-28 12:00",
      "conditions": "Proporcionar pantallas de alto contraste y etiquetas definitivas de los botones para el piloto.",
      "status": "agreed",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U013",
          "exact_quote": "Esas tres sí. El resto, no prometo. Mañana a las doce te dejo esas pantallas y las etiquetas definitivas de los botones."
        },
        {
          "field": "assignee",
          "utterance_id": "U011",
          "exact_quote": "Yo puedo dejar las pantallas de alto contraste el lunes en la mañana."
        },
        {
          "field": "deadline",
          "utterance_id": "U014",
          "exact_quote": "viernes a las doce, a tu nombre."
        }
      ]
    },
    {
      "task": "Documentar la API del piloto",
      "assignee": "Diego Soto",
      "deadline": "null",
      "conditions": "Sin fecha asignada, pero no bloquea el piloto.",
      "status": "conditional",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U048",
          "exact_quote": "También me habían pedido documentar la API. Eso no entra antes del piloto."
        },
        {
          "field": "assignee",
          "utterance_id": "U049",
          "exact_quote": "Entra como tarea tuya, pero sin fecha todavía. No bloquea el piloto."
        }
      ]
    },
    {
      "task": "Corregir el bug de las invitaciones y obtener la credencial del sandbox de Andrés para el lunes 31 de agosto a las 6:00 PM",
      "assignee": "Diego Soto",
      "deadline": "2026-08-31 18:00",
      "conditions": "Si Andrés envía la credencial antes del viernes 28 a las 12:00, el despliegue en staging se hace el lunes 31 a las 6:00 PM. Si no, se suspende el despliegue hasta que llegue.",
      "status": "agreed",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U015",
          "exact_quote": "Para arreglar las invitaciones necesito la credencial del sandbox."
        },
        {
          "field": "assignee",
          "utterance_id": "U017",
          "exact_quote": "Si Andrés la envía antes de mañana viernes a las doce, lo dejo listo el lunes a las seis."
        },
        {
          "field": "deadline",
          "utterance_id": "U017",
          "exact_quote": "Si no, el lunes a primera hora les digo que no llego."
        }
      ]
    },
    {
      "task": "Realizar regresión completa y subir informe antes de las 1:00 AM del martes 1 de septiembre",
      "assignee": "Martín Pérez",
      "deadline": "2026-09-01 01:00",
      "conditions": "Informe debe incluir bloqueadores como duplicación de invitaciones, pérdida de datos o problemas de aceptación desde móvil.",
      "status": "agreed",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U044",
          "exact_quote": "Yo hago la regresión el martes 1 entre nueve y una, y subo el informe antes de la una."
        },
        {
          "field": "assignee",
          "utterance_id": "U066",
          "exact_quote": "Regresión e informe el martes antes de la una."
        },
        {
          "field": "deadline",
          "utterance_id": "U045",
          "exact_quote": "antes de las cuatro, pero solo si el informe de Martín sale sin bloqueadores."
        }
      ]
    },
    {
      "task": "Enviar invitaciones al cliente antes de las 4:00 PM del martes 1 de septiembre si la regresión de Martín no tiene bloqueadores",
      "assignee": "Camila Rojas",
      "deadline": "2026-09-01 16:00",
      "conditions": "Solo si el informe de regresión de Martín no tiene bloqueadores.",
      "status": "agreed",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U045",
          "exact_quote": "Yo envío la invitación al cliente el martes antes de las cuatro, pero solo si el informe de Martín sale sin bloqueadores."
        },
        {
          "field": "assignee",
          "utterance_id": "U047",
          "exact_quote": "La responsable de enviarla soy yo."
        }
      ]
    },
    {
      "task": "Contactar a Sergio para definir la retención de correos antes del viernes 28 de agosto a las 5:00 PM",
      "assignee": "Camila Rojas",
      "deadline": "2026-08-28 17:00",
      "conditions": "Necesita respuesta por escrito.",
      "status": "agreed",
      "evidence": [
        {
          "field": "task",
          "utterance_id": "U026",
          "exact_quote": "Yo le escribo a Sergio antes de mañana a las cinco y dejamos la duración pendiente hasta que responda por escrito."
        }
      ]
    }
  ],
  "pending_issues": [
    {
      "issue": "Cobertura de soporte para el piloto: asignación pendiente a alguien que esté presente en la reunión.",
      "owner": "Paula (operaciones)",
      "deadline": null,
      "evidence": [
        {
          "utterance_id": "U052",
          "exact_quote": "No asignemos a alguien que no está. La cobertura de soporte queda pendiente; la cierro con Paula y operaciones fuera de esta reunión."
        }
      ]
    },
    {
      "issue": "Definición de retención de correos: pendiente hasta respuesta de Sergio.",
      "owner": null,
      "deadline": null,
      "evidence": [
        {
          "utterance_id": "U026",
          "exact_quote": "Yo le escribo a Sergio antes de mañana a las cinco y dejamos la duración pendiente hasta que responda por escrito."
        }
      ]
    }
  ],
  "review_alerts": [
    {
      "alert": "Revisar si el piloto puede abrirse el lunes 31 de agosto a las 4:00 PM si la regresión de Martín se completa antes de las 10:00 AM del lunes.",
      "reason": "Martín propuso revisar la posibilidad de abrir el piloto antes del miércoles si la regresión se completa sin bloqueadores.",
      "utterance_ids": ["U058"]
    },
    {
      "alert": "Verificar que la credencial del sandbox llegue antes del viernes 28 de agosto a las 12:00 PM para cumplir con el despliegue del lunes 31.",
      "reason": "Diego depende de la credencial de Andrés para corregir el bug de las invitaciones.",
      "utterance_ids": ["U015", "U017"]
    }
  ]
}
```
