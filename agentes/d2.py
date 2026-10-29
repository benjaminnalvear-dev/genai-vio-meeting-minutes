"""Condiciones de referencia de D2: baseline (prompt directo), structured y combined.

El prompt `SYSTEM`, la instrucción de revisión y el flujo están copiados sin cambios de `run_one` en el
notebook de D2. Se ejecutan con el mismo cliente que los agentes para comparar en la misma sesión.
"""
import json

from .datos import transcript_text
from .esquemas import make_schema
from .herramientas import apply_safe_checks, revision_cues, tool_bundle
from .modelo import inference

# ---- Copiado de D2 (sin cambios) ----
SYSTEM = """Genera minutas verificables en español de una reunión COMPLETA. Devuelve exclusivamente un JSON con decisions y tasks.
Cada decisión tiene id, topic, statement, state, condition, supersedes, evidence_id.
Cada tarea tiene id, description, assignee, deadline, condition, state, evidence_id.
Estados: final si hay acuerdo que nunca fue revertido; superseded si una propuesta fue reemplazada (conserva ambos elementos y enlázalos); rejected solo con descarte explícito; pending si no existe cierre observable.
Una propuesta sin consenso no es final. Registra decisiones y tareas que aparecen explícitamente, incluso cuando son reemplazadas después. Distingue una elección de una obligación asignada. Solo asigna a una persona cuando la transcripción le encargue la acción; menciones de terceros no constituyen asignaciones.
Usa como evidencia un ID real cuya intervención respalde el campo; no inventes valores. Fechas absolutas ISO YYYY-MM-DD o YYYY-MM-DDTHH:MM según la fecha de la reunión; si no puedes resolverla, null. Campos no expresados: null. IDs de decisiones d01... y tareas t01... separados. No uses el texto literal "null"."""


def run_baseline(tr):
    msgs=[{'role':'system','content':SYSTEM},
          {'role':'user','content':transcript_text(tr)}]
    return inference(msgs)


def run_structured(tr):
    msgs=[{'role':'system','content':SYSTEM},
          {'role':'user','content':transcript_text(tr)}]
    return inference(msgs,make_schema(tr))


def run_combined(tr, structured):
    msgs=[{'role':'system','content':SYSTEM},
          {'role':'user','content':transcript_text(tr)}]
    schema=make_schema(tr)
    draft=structured['parsed'] if isinstance(structured['parsed'],dict) else {'decisions':[],'tasks':[]}
    reports=tool_bundle(tr,draft)
    review='BORRADOR (puede contener errores):\n'+json.dumps(draft,ensure_ascii=False)
    review+='\nSALIDAS DE HERRAMIENTAS (no incluyen rúbrica):\n'+json.dumps(reports,ensure_ascii=False)
    review+='\nINDICIOS DE CAMBIOS LOCALIZADOS POR HERRAMIENTA:\n'+json.dumps(revision_cues(tr),ensure_ascii=False)
    review+='\nRevisa todas las intervenciones. En cada reemplazo explícito incluye DOS decisiones: la opción anterior con state=superseded y la nueva con state=final y supersedes apuntando al ID anterior. Reemplazado no significa rejected. Conserva propuestas expresamente descartadas con state=rejected, y asuntos sin acuerdo con state=pending. Revisa todas las tareas confirmadas, incluidas las que luego se completaron. Corrige responsables, fechas y evidencia. Las herramientas verifican existencia y sugieren fechas; NO demuestran por sí solas que la cita entraña cada campo. No atribuyas horas a "hoy" si no se menciona una hora. Devuelve solo la minuta corregida.'
    out=inference(msgs+[{'role':'assistant','content':json.dumps(draft,ensure_ascii=False)},
                        {'role':'user','content':review}],schema)
    out['tool_reports']=reports
    # D2 reportó en `seconds` solo la segunda llamada; el costo real incluye el borrador.
    out['seconds_con_borrador']=round(out['seconds']+structured['seconds'],2)
    return apply_safe_checks(tr,out)
