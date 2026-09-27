"""Solución D2: Ministral 3 3B con tool use (registro de estado) + retrieval (BM25) + verificación.

Flujo completo (S4, config "tool_bloques_rag_verif"; la solución propuesta S2 omite los pasos de retrieval y 4):
  1. Código: parsea la transcripción y la divide en bloques de intervenciones.
  2. Ministral, bloque por bloque y en dos pasadas (decisiones / tareas): recibe el registro actual,
     el contexto recuperado por BM25 y las intervenciones nuevas, y responde SOLO con llamadas a
     herramientas (JSON restringido por schema: ids, intervenciones y responsables son enums).
  3. Código: ejecuta las llamadas sobre el registro (lo reemplazado pasa a superseded), ancla cada
     plazo al texto de la intervención citada y lo resuelve con reglas, y pega citas textuales por ID.
  4. Ministral, verificación corta por ítem: ¿la intervención respalda el ítem? sí/no. Si no, BM25
     propone intervenciones candidatas; si ninguna pasa, el ítem sale del acta y queda como alerta.
  5. Código: renderiza el acta con el mismo esquema del prompt canónico del D1.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from . import ollama_client
from .retrieval import BM25, tokenize, tokenize_stem
from .temporal import anchor, fold, resolve
from .transcript import Meeting, Utterance

CONFIGS = {
    # Cada una agrega una pieza a la anterior. La solución propuesta es S2 (tool_bloques).
    "tool_1pasada": {"window": None, "retrieval": False, "verify": False},          # S1
    "tool_bloques": {"window": 8, "retrieval": False, "verify": False},             # S2
    "tool_bloques_rag": {"window": 8, "retrieval": "bloque", "verify": False},      # S3
    "tool_bloques_rag_verif": {"window": 8, "retrieval": "bloque", "verify": True}, # S4
    # Agregadas el 27-sep para revisar el RAG:
    "tool_bloques_rag2": {"window": 8, "retrieval": "por_intervencion", "verify": False},  # S3b
    "tool_bloques_pasado": {"window": 8, "retrieval": "todo_el_pasado", "verify": False},  # control
    # Para usar con cualquier reunión: S2 mientras el registro cabe en el contexto; RAG cuando no cabe.
    "auto": {"window": 8, "retrieval": "auto", "verify": False},
}
EVAL_CONFIGS = ["tool_1pasada", "tool_bloques", "tool_bloques_rag", "tool_bloques_rag_verif",
                "tool_bloques_rag2", "tool_bloques_pasado"]   # las que corre `run.py todo`

# Presupuesto de contexto. Ministral usa ~2.8 caracteres por token en la transcripción 01; 2.5 es conservador.
CHARS_PER_TOKEN = 2.5
SAFETY_MARGIN = 300


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN) + 1
# retrieval: False = sin contexto extra; "bloque" = una consulta BM25 con el texto de todo el bloque;
# "por_intervencion" = una consulta por intervención nueva, con stemmer, 2 resultados c/u, tope 4;
# "todo_el_pasado" = todas las intervenciones anteriores (no es RAG: es el techo de cualquier buscador).
LABELS = {
    "baseline": "B · Baseline (prompt directo D1)",
    "pipeline_tool_1pasada": "S1 · Tool use, 1 pasada",
    "pipeline_tool_bloques": "S2 · Tool use por bloques",
    "pipeline_tool_bloques_rag": "S3 · S2 + RAG",
    "pipeline_tool_bloques_rag_verif": "S4 · S3 + verificación",
    "pipeline_tool_bloques_rag2": "S3b · S2 + RAG mejorado",
    "pipeline_tool_bloques_pasado": "Control · S2 + todo el pasado",
    "pipeline_auto": "Auto · S2 si cabe, RAG si no",
}
PREVIOUS_CONTEXT = 3       # intervenciones inmediatamente anteriores al bloque, solo como contexto
RETRIEVED_CONTEXT = 4      # intervenciones anteriores recuperadas por BM25
DECISION_STATES = ["propuesta", "final", "rechazada", "pendiente"]

COMMON_RULES = """Reglas generales:
- Registra solo lo que ocurre en INTERVENCIONES NUEVAS. El registro y el contexto son para entender, no para volver a registrar.
- Cada llamada cita UNA intervención de INTERVENCIONES NUEVAS en utterance_id.
- Si el asunto ya está en el registro, usa su id; no lo dupliques.
- Si no ocurre nada registrable, responde {"llamadas": []}."""

DECISION_PROMPT = """Eres el secretario de una reunión. En esta pasada registras DECISIONES llamando herramientas; el código guarda el registro y arma el acta. No registres tareas personales.

Una decisión es un acuerdo del grupo sobre cómo se hará algo: fecha, herramienta, proveedor, canal, alcance, regla, modalidad. También registras las propuestas sobre esos asuntos, porque después pueden aceptarse, rechazarse o reemplazarse. Una queja, un problema técnico o una pregunta suelta no es una decisión. El compromiso personal de alguien ("yo hago X", "te dejo X") es una tarea: no lo registres en esta pasada.

Herramientas:
- crear_decision: aparece una propuesta o un acuerdo NUEVO.
  estado = "propuesta" si se sugiere o se pregunta; "final" si quien dirige lo acepta explícitamente; "rechazada" si se descarta; "pendiente" si se deja explícitamente sin decidir.
  reemplaza = ids de decisiones del registro sobre el MISMO asunto que esta deja sin efecto (si no, lista vacía).
- cambiar_estado: una decisión que ya está en el registro pasa a "final", "rechazada" o "pendiente".
- confirmar: la intervención solo repite o ratifica una decisión del registro.

""" + COMMON_RULES + """

Ejemplo de otra reunión (no es parte de esta):
[U010 | Ana] ¿Contratamos el catering de Sabores?
[U011 | Luis] Cobran el doble que el año pasado.
[U012 | Ana] Entonces Sabores descartado. Vamos con Delicias, reemplaza a Sabores.
[U013 | Luis] ¿Y el menú vegano?
[U014 | Ana] Eso lo dejamos pendiente hasta tener la lista de invitados.
[U015 | Ana] Confirmo: Delicias.
{"llamadas": [
 {"herramienta": "crear_decision", "id": "D1", "tema": "catering", "contenido": "contratar Sabores", "estado": "propuesta", "reemplaza": [], "utterance_id": "U010"},
 {"herramienta": "cambiar_estado", "id": "D1", "tema": null, "contenido": null, "estado": "rechazada", "reemplaza": [], "utterance_id": "U012"},
 {"herramienta": "crear_decision", "id": "D2", "tema": "catering", "contenido": "contratar Delicias", "estado": "final", "reemplaza": ["D1"], "utterance_id": "U012"},
 {"herramienta": "crear_decision", "id": "D3", "tema": "menú vegano", "contenido": "definir si habrá menú vegano", "estado": "pendiente", "reemplaza": [], "utterance_id": "U014"},
 {"herramienta": "confirmar", "id": "D2", "tema": null, "contenido": null, "estado": null, "reemplaza": [], "utterance_id": "U015"}
]}"""

TASK_PROMPT = """Eres el secretario de una reunión. En esta pasada registras TAREAS llamando herramientas; el código guarda el registro y arma el acta. No registres decisiones generales.

Una tarea es un compromiso concreto de una persona PRESENTE (dice que hará algo) o un encargo que se le asigna explícitamente. Describir un problema, pedir algo, hacer una pregunta, "confirmar si..." o "revisar si..." no es una tarea.

Herramientas:
- crear_tarea: aparece un compromiso o encargo NUEVO.
  responsable = nombre de pila de quien hará la tarea (solo participantes presentes).
  contenido = qué hará, en pocas palabras.
  plazo_literal = copia EXACTA de las palabras del plazo, sin convertirlas (null si no hay plazo).
  condicion = de qué depende la tarea, copiada de la intervención (null si no depende de nada).
- actualizar_tarea: cambia el plazo o la condición de una tarea que ya está en el registro.
- confirmar: la intervención repite o ratifica una tarea del registro. En los resúmenes del final casi todo ya está en el registro: usa confirmar con su id.

Reglas de tareas:
- Una tarea por acción y por responsable: dos acciones distintas son dos tareas.
- Una persona mencionada que no está presente nunca es responsable; lo que deba hacer puede ser la condición de otra tarea.

""" + COMMON_RULES + """

Ejemplo de otra reunión (no es parte de esta; Marta no está presente):
[U020 | Luis] Yo reservo el salón mañana a las tres, si Marta me manda el presupuesto antes.
[U021 | Ana] Perfecto, a tu nombre. Y yo imprimo los afiches el lunes.
[U030 | Ana] Resumen: Luis el salón mañana, yo los afiches.
{"llamadas": [
 {"herramienta": "crear_tarea", "id": "T1", "responsable": "Luis", "contenido": "reservar el salón", "plazo_literal": "mañana a las tres", "condicion": "si Marta me manda el presupuesto antes", "utterance_id": "U020"},
 {"herramienta": "confirmar", "id": "T1", "responsable": null, "contenido": null, "plazo_literal": null, "condicion": null, "utterance_id": "U021"},
 {"herramienta": "crear_tarea", "id": "T2", "responsable": "Ana", "contenido": "imprimir los afiches", "plazo_literal": "el lunes", "condicion": null, "utterance_id": "U021"},
 {"herramienta": "confirmar", "id": "T1", "responsable": null, "contenido": null, "plazo_literal": null, "condicion": null, "utterance_id": "U030"},
 {"herramienta": "confirmar", "id": "T2", "responsable": null, "contenido": null, "plazo_literal": null, "condicion": null, "utterance_id": "U030"}
]}"""

PASSES = {
    "decisiones": {"prompt": DECISION_PROMPT, "kinds": {"decision"}, "tools": ["crear_decision", "cambiar_estado", "confirmar"]},
    "tareas": {"prompt": TASK_PROMPT, "kinds": {"tarea"}, "tools": ["crear_tarea", "actualizar_tarea", "confirmar"]},
}


# ---------------------------------------------------------------- registro

@dataclass
class Item:
    id: str
    kind: str                      # decision | tarea
    tema: str = ""
    contenido: str = ""
    estado: str = "propuesta"
    responsable: str | None = None
    plazo_literal: str | None = None
    plazo_uid: str | None = None
    condicion: str | None = None
    condicion_uid: str | None = None
    reemplazada_por: str | None = None
    decisive_uid: str | None = None   # intervención que fijó el estado actual
    evidence: list[tuple[str, str]] = field(default_factory=list)   # (utterance_id, rol)

    def add_evidence(self, uid: str, role: str):
        if all(u != uid for u, _ in self.evidence):
            self.evidence.append((uid, role))

    def line(self) -> str:
        if self.kind == "decision":
            state = f"reemplazada por {self.reemplazada_por}" if self.reemplazada_por else self.estado
            return f"{self.id} [{state}] {self.tema}: {self.contenido} ({self.evidence[0][0]})"
        return (f"{self.id} {self.responsable or '?'}: {self.contenido} | plazo: "
                f"{json.dumps(self.plazo_literal, ensure_ascii=False)} | condición: {self.condicion or '-'} ({self.evidence[0][0]})")


class Registry:
    PREFIX = {"decision": "D", "tarea": "T"}

    def __init__(self, meeting: Meeting):
        self.meeting = meeting
        self.items: dict[str, Item] = {}
        self.counters = {"decision": 0, "tarea": 0}
        self.log: list[str] = []
        self.present = meeting.first_names()

    def of_kind(self, kinds: set[str]) -> list[Item]:
        return [i for i in self.items.values() if i.kind in kinds]

    def free_ids(self, kind: str, n: int = 5) -> list[str]:
        c = self.counters[kind]
        return [f"{self.PREFIX[kind]}{c + i}" for i in range(1, n + 1)]

    def _new(self, kind: str, requested: str | None) -> Item:
        self.counters[kind] += 1
        new_id = f"{self.PREFIX[kind]}{self.counters[kind]}"
        if requested and requested != new_id:
            self.log.append(f"id pedido {requested} -> asignado {new_id}")
        item = Item(new_id, kind)
        self.items[new_id] = item
        return item

    def _person(self, name) -> str | None:
        if not isinstance(name, str) or not name.strip():
            return None
        for key in self.present:          # etiqueta exacta (el schema solo permite estas)
            if fold(key) == fold(name):
                return key
        first = name.strip().split()[0]
        for key in self.present:          # nombre de pila, solo si la etiqueta es de una palabra
            if " " not in key and fold(key) == fold(first):
                return key
        self.log.append(f"responsable '{name}' no está presente: se deja null")
        return None

    def apply(self, call: dict, window_ids: set[str]) -> str | None:
        tool = call.get("herramienta")
        uid = call.get("utterance_id")
        if uid not in window_ids:
            self.log.append(f"llamada descartada: {uid} no está en el bloque")
            return None
        ref = call.get("id")
        existing = self.items.get(ref) if isinstance(ref, str) else None

        if tool == "crear_decision":
            if existing and existing.kind == "decision":
                return self._change_state(existing, call.get("estado"), uid)
            item = self._new("decision", ref)
            item.tema = str(call.get("tema") or "")
            item.contenido = str(call.get("contenido") or "")
            item.estado = call.get("estado") if call.get("estado") in DECISION_STATES else "propuesta"
            item.decisive_uid = uid
            item.add_evidence(uid, "creacion")
            for old in call.get("reemplaza") or []:
                old_item = self.items.get(old)
                if old_item and old_item.kind == "decision" and old_item.id != item.id and not old_item.reemplazada_por:
                    old_item.reemplazada_por = item.id
                    old_item.add_evidence(uid, "reemplazo")
                    self.log.append(f"{old_item.id} reemplazada por {item.id} en {uid}")
            return item.id
        if tool == "cambiar_estado":
            if not existing or existing.kind != "decision":
                self.log.append(f"cambiar_estado sobre id inexistente {ref}")
                return None
            return self._change_state(existing, call.get("estado"), uid)
        if tool == "crear_tarea":
            if existing and existing.kind == "tarea":
                return self._update_task(existing, call, uid)
            item = self._new("tarea", ref)
            item.contenido = str(call.get("contenido") or "")
            item.responsable = self._person(call.get("responsable"))
            item.decisive_uid = uid
            item.add_evidence(uid, "creacion")
            self._update_task(item, call, uid)
            return item.id
        if tool == "actualizar_tarea":
            if not existing or existing.kind != "tarea":
                self.log.append(f"actualizar_tarea sobre id inexistente {ref}")
                return None
            return self._update_task(existing, call, uid)
        if tool == "confirmar":
            if not existing:
                self.log.append(f"confirmar sobre id inexistente {ref}")
                return None
            existing.add_evidence(uid, "confirmacion")
            return existing.id
        self.log.append(f"herramienta desconocida {tool}")
        return None

    def _change_state(self, item: Item, state, uid: str) -> str:
        if state in DECISION_STATES and state != item.estado:
            self.log.append(f"{item.id}: {item.estado} -> {state} en {uid}")
            item.estado = state
            item.decisive_uid = uid
            item.add_evidence(uid, "estado")
        else:
            item.add_evidence(uid, "confirmacion")
        return item.id

    def _update_task(self, item: Item, call: dict, uid: str) -> str:
        literal = call.get("plazo_literal")
        if isinstance(literal, str) and literal.strip() and fold(literal) not in {"null", "none"}:
            if item.plazo_literal and fold(literal) != fold(item.plazo_literal):
                self.log.append(f"{item.id}: plazo '{item.plazo_literal}' -> '{literal}' en {uid}")
            if not item.plazo_literal or item.plazo_uid != uid:
                item.plazo_literal, item.plazo_uid = literal.strip(), uid
            item.add_evidence(uid, "plazo")
        cond = call.get("condicion")
        if isinstance(cond, str) and cond.strip() and fold(cond) not in {"null", "none"}:
            item.condicion, item.condicion_uid = cond.strip(), uid
            item.add_evidence(uid, "condicion")
        item.add_evidence(uid, "confirmacion")
        return item.id

    def render_lines(self, kinds: set[str]) -> str:
        return "\n".join(i.line() for i in self.of_kind(kinds)) or "(vacío)"


# ---------------------------------------------------------------- llamadas al modelo

def calls_schema(pass_name: str, window_ids: list[str], item_ids: list[str], present: list[str]) -> dict:
    nullable_str = {"type": ["string", "null"]}
    props = {
        "herramienta": {"enum": PASSES[pass_name]["tools"]},
        "id": {"enum": item_ids},
    }
    if pass_name == "decisiones":
        existing = [i for i in item_ids if i.startswith("D")]
        props.update({
            "tema": nullable_str, "contenido": nullable_str,
            "estado": {"enum": DECISION_STATES + [None]},
            "reemplaza": {"type": "array", "items": {"enum": existing or ["D0"]}},
        })
    else:
        props.update({
            "responsable": {"enum": present + [None]},
            "contenido": nullable_str, "plazo_literal": nullable_str, "condicion": nullable_str,
        })
    props["utterance_id"] = {"enum": window_ids}
    return {
        "type": "object",
        "properties": {"llamadas": {"type": "array", "items": {
            "type": "object", "properties": props, "required": list(props)}}},
        "required": ["llamadas"],
    }


def build_user_message(meeting: Meeting, registry: Registry, pass_name: str,
                       new: list[Utterance], previous: list[Utterance], retrieved: list[Utterance],
                       context_label: str = "rag", shown: list[Item] | None = None) -> str:
    """Mensaje de cada llamada de extracción. `shown` limita el registro a esos ítems (reuniones largas)."""
    wd = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][meeting.date.weekday()]
    people = ", ".join(f"{lab} ({meeting.participants[full]})" if meeting.participants[full] else lab
                       for lab, full in meeting.first_names().items())
    kinds = PASSES[pass_name]["kinds"]
    kind = next(iter(kinds))
    label = "DECISIONES" if pass_name == "decisiones" else "TAREAS"
    all_items = registry.of_kind(kinds)
    if shown is None or len(shown) == len(all_items):
        registry_lines = registry.render_lines(kinds)
        registry_title = f"REGISTRO ACTUAL DE {label}:"
    else:
        registry_lines = "\n".join(i.line() for i in shown) or "(vacío)"
        registry_title = (f"REGISTRO ACTUAL DE {label} (se muestran {len(shown)} de {len(all_items)}: "
                          "los más relacionados con las intervenciones nuevas):")
    absent = ", ".join(meeting.absent_mentioned) or "ninguna"
    parts = [
        f"Reunión: {wd} {meeting.date.isoformat()}. Participantes presentes: {people}.",
        f"Personas mencionadas que NO están presentes: {absent}.",
        "",
        registry_title,
        registry_lines,
    ]
    if retrieved:
        context_title = ("INTERVENCIONES ANTERIORES (todas, ya procesadas):" if context_label == "todo"
                         else "CONTEXTO RECUPERADO (intervenciones anteriores relacionadas, ya procesadas):")
        parts += ["", context_title]
        parts += [u.render() for u in retrieved]
    if previous:
        parts += ["", "INTERVENCIONES ANTERIORES INMEDIATAS (ya procesadas):"]
        parts += [u.render() for u in previous]
    parts += ["", "INTERVENCIONES NUEVAS (registra lo que ocurre aquí):"]
    parts += [u.render() for u in new]
    parts += ["", f"Ids libres para {label.lower()} nuevas: " + ", ".join(registry.free_ids(kind)) + "."]
    return "\n".join(parts)


def claim_text(item: Item, meeting: Meeting) -> str:
    """Afirmación que el verificador contrasta con una intervención."""
    what = f"{item.tema} — {item.contenido}" if item.tema else item.contenido
    if item.kind == "tarea":
        return f"{item.responsable or 'Alguien'} se compromete a: {item.contenido}"
    if item.reemplazada_por:
        return f"Se propuso: {what}"
    return {"final": f"Se decidió: {what}", "rechazada": f"Se rechazó: {what}",
            "pendiente": f"Quedó pendiente: {what}"}.get(item.estado, f"Se propuso: {what}")


def verify(item: Item, uid: str, meeting: Meeting, calls: list) -> bool:
    """Pregunta sí/no en texto libre.

    Sin JSON schema a propósito: con la salida restringida a {"respalda": bool} Ministral responde
    "false" casi siempre (4/10 en el set de calibración de otra reunión, todo "no"); en texto libre
    acierta 8/10. Ver README, sección Verificador.
    """
    u = meeting.by_id[uid]
    content = (f"Intervención [{u.id} | {u.speaker}]: \"{u.text}\"\n"
               f"Afirmación: \"{claim_text(item, meeting)}\"\n"
               "¿La intervención respalda la afirmación? Responde solo \"sí\" o \"no\".")
    rec = ollama_client.chat([{"role": "user", "content": content}], num_predict=5)
    rec.update({"tipo": "verificacion", "item": item.id, "utterance_id": uid})
    calls.append(rec)
    return fold(rec["response_raw"]).lstrip(" \"'¡*").startswith(("si", "yes"))


# ---------------------------------------------------------------- render

def quote(meeting: Meeting, uid: str) -> dict:
    return {"utterance_id": uid, "exact_quote": meeting.by_id[uid].text}


def ordered_uids(item: Item) -> list[str]:
    uids = [uid for uid, _ in item.evidence]
    if item.decisive_uid in uids:
        uids.remove(item.decisive_uid)
        uids.insert(0, item.decisive_uid)
    return uids


def decision_state(item: Item) -> str | None:
    if item.reemplazada_por:
        return "superseded"
    return {"final": "final", "rechazada": "rejected", "pendiente": "pending"}.get(item.estado)


def render(registry: Registry, meeting: Meeting, alerts: list[dict], unverified: set[str]) -> dict:
    decisions, tasks, pendings = [], [], []
    full_names = meeting.first_names()
    for item in registry.items.values():
        if item.id in unverified:
            continue
        uids = ordered_uids(item)
        if item.kind == "decision":
            state = decision_state(item)
            if state is None:
                alerts.append({"alert": f"Propuesta sin resolución: {item.tema} — {item.contenido}",
                               "reason": "Nunca se aceptó, rechazó ni reemplazó explicitamente.", "utterance_ids": uids})
                continue
            if state == "pending":
                pendings.append({"issue": f"{item.tema}: {item.contenido}", "owner": None, "deadline": None,
                                 "evidence": [quote(meeting, u) for u in uids], "_id": item.id})
                continue
            outcome = item.contenido
            if resolve(item.contenido, meeting.date).value:
                when = anchor(item.contenido, meeting.by_id[item.evidence[0][0]].text, meeting.date)
                if when.value:
                    outcome += f" [{when.value}]"
            if item.reemplazada_por:
                outcome += f" (reemplazada por {item.reemplazada_por})"
            decisions.append({"topic": item.tema, "outcome": outcome, "state": state,
                              "evidence": [quote(meeting, u) for u in uids], "_id": item.id})
        else:
            when = anchor(item.plazo_literal, meeting.by_id[item.plazo_uid].text, meeting.date) if item.plazo_uid else resolve(None, meeting.date)
            for a in when.alerts:
                alerts.append({"alert": f"{item.id}: {a}", "reason": "; ".join(when.rules) or "plazo no resuelto",
                               "utterance_ids": [item.plazo_uid] if item.plazo_uid else uids})
            ev = [{"field": "task", **quote(meeting, uids[0])}]
            if item.plazo_uid:
                ev.append({"field": "deadline", **quote(meeting, item.plazo_uid)})
            if item.condicion_uid:
                ev.append({"field": "conditions", **quote(meeting, item.condicion_uid)})
            ev += [{"field": "status", **quote(meeting, u)} for u in uids
                   if u not in {uids[0], item.plazo_uid, item.condicion_uid}]
            tasks.append({
                "task": item.contenido,
                "assignee": full_names.get(item.responsable) if item.responsable else None,
                "deadline": when.value,
                "deadline_literal": item.plazo_literal,
                "deadline_rules": when.rules,
                "conditions": item.condicion,
                "status": "conditional" if item.condicion else "agreed",
                "evidence": ev, "_id": item.id,
            })
    return {
        "meeting": {"date": meeting.date.isoformat(), "topic": meeting.topic},
        "decisions": decisions, "action_items": tasks, "pending_issues": pendings, "review_alerts": alerts,
    }


# ---------------------------------------------------------------- consolidación (código)

def _jaccard(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def _merge(registry: Registry, keep: Item, drop: Item, reason: str):
    for uid, _ in drop.evidence:
        keep.add_evidence(uid, "confirmacion")
    if not keep.condicion and drop.condicion:
        keep.condicion, keep.condicion_uid = drop.condicion, drop.condicion_uid
    if keep.reemplazada_por == drop.id:
        # keep y drop son la misma decisión: queda con el estado del registro más reciente.
        keep.reemplazada_por = drop.reemplazada_por
        keep.estado, keep.decisive_uid = drop.estado, drop.decisive_uid
    for other in registry.items.values():
        if other.reemplazada_por == drop.id and other is not keep:
            other.reemplazada_por = keep.id
    del registry.items[drop.id]
    registry.log.append(f"consolidado: {drop.id} -> {keep.id} ({reason})")


def consolidate(registry: Registry, meeting: Meeting):
    """Une duplicados que el modelo creó en vez de usar confirmar.

    Tareas: mismo responsable y (mismo plazo resuelto y descripción parecida, o descripción casi igual).
    Decisiones: mismo estado efectivo y tema+contenido casi iguales.
    """
    def deadline(item: Item):
        if not item.plazo_uid:
            return None
        return anchor(item.plazo_literal, meeting.by_id[item.plazo_uid].text, meeting.date).value

    changed = True
    while changed:
        changed = False
        items = list(registry.items.values())
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a.kind != b.kind or a.id not in registry.items or b.id not in registry.items:
                    continue
                if a.kind == "tarea":
                    if not a.responsable or a.responsable != b.responsable:
                        continue
                    sim = _jaccard(a.contenido, b.contenido)
                    same_deadline = deadline(a) is not None and deadline(a) == deadline(b)
                    if (same_deadline and sim >= 0.25) or sim >= 0.6:
                        _merge(registry, a, b, f"mismo responsable, similitud {sim:.2f}, mismo plazo={same_deadline}")
                        changed = True
                else:
                    if decision_state(a) is None or decision_state(a) != decision_state(b):
                        continue
                    sim = _jaccard(f"{a.tema} {a.contenido}", f"{b.tema} {b.contenido}")
                    if sim >= 0.6:
                        _merge(registry, a, b, f"mismo estado, similitud {sim:.2f}")
                        changed = True


# ---------------------------------------------------------------- orquestación

def blocks(meeting: Meeting, window: int | None) -> list[tuple[int, int]]:
    n = len(meeting.utterances)
    if not window:
        return [(0, n)]
    return [(s, min(s + window, n)) for s in range(0, n, window)]


def verify_all(registry: Registry, meeting: Meeting, bm25: BM25, calls: list, alerts: list) -> tuple[set[str], list[str]]:
    unverified: set[str] = set()
    log: list[str] = []
    index_of = {u.id: i for i, u in enumerate(meeting.utterances)}
    for item in list(registry.items.values()):
        if item.kind == "decision" and decision_state(item) is None:
            continue  # no llega al acta como decisión
        primary = item.decisive_uid or item.evidence[0][0]
        if verify(item, primary, meeting, calls):
            log.append(f"{item.id}: {primary} respalda")
            continue
        own = [u for u, _ in item.evidence if u != primary]
        query = f"{item.tema} {item.contenido} {item.responsable or ''}"
        near = set(range(max(0, index_of[primary] - 12), min(len(meeting.utterances), index_of[primary] + 13)))
        cands = own + [meeting.utterances[i].id for i in bm25.top(query, 3, near)]
        cands = [c for c in dict.fromkeys(cands) if c != primary]
        found = next((c for c in cands if verify(item, c, meeting, calls)), None)
        if found:
            item.decisive_uid = found
            item.evidence = [(found, "verificada")] + [e for e in item.evidence if e[0] not in {found, primary}]
            log.append(f"{item.id}: {primary} no respalda; se usa {found}")
        else:
            unverified.add(item.id)
            log.append(f"{item.id}: sin evidencia verificada (probadas {[primary] + cands})")
            alerts.append({"alert": f"Ítem descartado por falta de evidencia: {item.line()}",
                           "reason": "Ni la intervención citada ni las candidatas recuperadas lo respaldan.",
                           "utterance_ids": [primary]})
    return unverified, log


def retrieve(meeting: Meeting, mode, start: int, new: list[Utterance], bm25: BM25, bm25_stem: BM25) -> list[Utterance]:
    """Intervenciones anteriores que se agregan como contexto al bloque que empieza en `start`."""
    allowed = set(range(0, max(0, start - PREVIOUS_CONTEXT)))
    if not mode or not allowed:
        return []
    if mode == "todo_el_pasado":
        picked = sorted(allowed)
    elif mode == "por_intervencion":
        best: dict[int, float] = {}
        for u in new:
            scores = bm25_stem.scores(u.text)
            for i in bm25_stem.top(u.text, 2, allowed):
                best[i] = max(best.get(i, 0.0), scores[i])
        picked = sorted(sorted(best, key=best.get, reverse=True)[:RETRIEVED_CONTEXT])
    else:  # "bloque" (o True en corridas antiguas)
        picked = sorted(bm25.top(" ".join(u.text for u in new), RETRIEVED_CONTEXT, allowed))
    return [meeting.utterances[i] for i in picked]


def select_items(items: list[Item], new: list[Utterance], budget_tokens: int, meeting: Meeting) -> list[Item]:
    """RAG sobre el registro: los ítems más relacionados con las intervenciones nuevas (BM25 + stemmer),
    desempatando por los más recientes, hasta llenar el presupuesto. Se devuelven en su orden original."""
    if not items:
        return []
    index_of = {u.id: i for i, u in enumerate(meeting.utterances)}
    bm = BM25([f"{i.tema} {i.contenido} {i.responsable or ''}" for i in items], tokenizer=tokenize_stem)
    relevance = [0.0] * len(items)
    for u in new:
        for k, sc in enumerate(bm.scores(u.text)):
            relevance[k] = max(relevance[k], sc)
    recency = [max(index_of.get(uid, 0) for uid, _ in it.evidence) for it in items]
    order = sorted(range(len(items)), key=lambda k: (relevance[k], recency[k]), reverse=True)
    chosen, used = set(), 0
    for k in order:
        cost = estimate_tokens(items[k].line()) + 1
        if used + cost > budget_tokens:
            continue
        chosen.add(k)
        used += cost
    return [items[k] for k in sorted(chosen)]


def plan_context(meeting: Meeting, registry: Registry, pass_name: str, start: int, new: list[Utterance],
                 previous: list[Utterance], mode, bm25: BM25, bm25_stem: BM25, num_predict: int):
    """Decide qué registro y qué contexto recuperado lleva la llamada, sin pasarse del contexto.

    Devuelve (ítems a mostrar, intervenciones recuperadas, modo usado, notas).
    - modo "auto": si el registro completo cabe, no usa RAG (es S2). Si no cabe (reunión larga), muestra
      solo los ítems más relacionados (RAG sobre el registro) y agrega intervenciones anteriores
      recuperadas por intervención (como S3b) con lo que sobre del presupuesto.
    - cualquier modo: si el mensaje estimado no cabe, recorta primero lo recuperado y después el registro.
    """
    spec = PASSES[pass_name]
    items = registry.of_kind(spec["kinds"])
    num_ctx = ollama_client.DEFAULT_OPTIONS["num_ctx"]
    fixed = build_user_message(meeting, registry, pass_name, new, previous, [], shown=[])
    budget = num_ctx - num_predict - SAFETY_MARGIN - estimate_tokens(spec["prompt"]) - estimate_tokens(fixed)
    notes: list[str] = []
    if budget <= 0:
        raise ValueError(f"El bloque {new[0].id}–{new[-1].id} no cabe en num_ctx={num_ctx} ni sin registro: "
                         "reduce el tamaño de bloque o sube num_ctx.")
    registry_cost = sum(estimate_tokens(i.line()) + 1 for i in items)
    if mode == "auto":
        if registry_cost <= budget:
            return items, [], "sin_rag", notes
        shown = select_items(items, new, int(budget * 0.7), meeting)
        left = budget - sum(estimate_tokens(i.line()) + 1 for i in shown)
        retrieved = []
        for u in retrieve(meeting, "por_intervencion", start, new, bm25, bm25_stem):
            cost = estimate_tokens(u.render()) + 1
            if cost <= left:
                retrieved.append(u)
                left -= cost
        notes.append(f"reunión larga: registro {registry_cost} tokens > presupuesto {budget}; "
                     f"se muestran {len(shown)}/{len(items)} ítems y {len(retrieved)} intervenciones recuperadas")
        return shown, retrieved, "rag", notes
    retrieved = retrieve(meeting, mode, start, new, bm25, bm25_stem)
    shown = items
    context_cost = sum(estimate_tokens(u.render()) + 1 for u in retrieved)
    while retrieved and registry_cost + context_cost > budget:
        dropped = retrieved.pop(0)
        context_cost -= estimate_tokens(dropped.render()) + 1
        notes.append(f"recorte: se quitó {dropped.id} del contexto para no pasarse de num_ctx")
    if registry_cost > budget:
        shown = select_items(items, new, budget, meeting)
        notes.append(f"recorte: registro {registry_cost} tokens > presupuesto {budget}; se muestran {len(shown)}/{len(items)} ítems")
    return shown, retrieved, (mode or "sin_rag"), notes


def run(meeting: Meeting, config_name: str = "tool_bloques") -> dict:
    cfg = CONFIGS[config_name]
    started = time.time()
    registry = Registry(meeting)
    present = list(meeting.first_names())
    bm25 = BM25([u.text for u in meeting.utterances])
    bm25_stem = BM25([u.text for u in meeting.utterances], tokenizer=tokenize_stem)
    calls: list[dict] = []
    tool_calls: list[dict] = []

    for start, end in blocks(meeting, cfg["window"]):
        new = meeting.utterances[start:end]
        previous = meeting.utterances[max(0, start - PREVIOUS_CONTEXT):start]
        window_ids = [u.id for u in new]
        num_predict = 1500 if cfg["window"] else 3000
        for pass_name, spec in PASSES.items():
            kind = next(iter(spec["kinds"]))
            shown, retrieved, mode_used, notes = plan_context(
                meeting, registry, pass_name, start, new, previous, cfg["retrieval"], bm25, bm25_stem, num_predict)
            registry.log.extend(f"{window_ids[0]}-{window_ids[-1]} {pass_name}: {n}" for n in notes)
            item_ids = [i.id for i in shown] + registry.free_ids(kind)
            user = build_user_message(meeting, registry, pass_name, new, previous, retrieved,
                                      "todo" if cfg["retrieval"] == "todo_el_pasado" else "rag", shown=shown)
            rec = ollama_client.chat(
                [{"role": "system", "content": spec["prompt"]}, {"role": "user", "content": user}],
                fmt=calls_schema(pass_name, window_ids, item_ids, present),
                num_predict=num_predict)
            rec.update({"tipo": "extraccion", "pasada": pass_name, "bloque": [window_ids[0], window_ids[-1]],
                        "recuperadas": [u.id for u in retrieved], "modo_usado": mode_used,
                        "registro_mostrado": f"{len(shown)}/{len(registry.of_kind(spec['kinds']))}"})
            limit = ollama_client.DEFAULT_OPTIONS["num_ctx"] - num_predict
            if (rec.get("prompt_eval_count") or 0) >= limit:
                registry.log.append(f"{window_ids[0]}-{window_ids[-1]} {pass_name}: ADVERTENCIA posible truncamiento "
                                    f"({rec.get('prompt_eval_count')} tokens de entrada, límite {limit})")
            calls.append(rec)
            try:
                parsed = json.loads(rec["response_raw"]).get("llamadas", [])
            except json.JSONDecodeError:
                registry.log.append(f"{pass_name} {window_ids[0]}-{window_ids[-1]}: JSON inválido ({rec.get('done_reason')})")
                parsed = []
            for call in parsed:
                applied = registry.apply(call, set(window_ids))
                tool_calls.append({"pasada": pass_name, **call, "_aplicada_a": applied})

    consolidate(registry, meeting)
    alerts: list[dict] = []
    unverified: set[str] = set()
    verification_log: list[str] = []
    if cfg["verify"]:
        unverified, verification_log = verify_all(registry, meeting, bm25, calls, alerts)

    acta = render(registry, meeting, alerts, unverified)
    extraction = [c for c in calls if c["tipo"] == "extraccion"]
    return {
        "condicion": f"pipeline_{config_name}",
        "config": cfg,
        "acta": acta,
        "registro_final": [i.line() for i in registry.items.values()],
        "llamadas_herramientas": tool_calls,
        "registro_log": registry.log,
        "verificacion_log": verification_log,
        "llamadas_modelo": calls,
        "n_llamadas": len(calls),
        "n_llamadas_extraccion": len(extraction),
        "prompt_eval_count": sum(c.get("prompt_eval_count") or 0 for c in calls),
        "eval_count": sum(c.get("eval_count") or 0 for c in calls),
        "bloques_cortados_por_limite": sum(1 for c in extraction if c.get("done_reason") == "length"),
        "modos_usados": sorted({c.get("modo_usado", "") for c in extraction}),
        "advertencias_transcripcion": meeting.warnings,
        "wall_total_s": round(time.time() - started, 2),
    }


def replay(meeting: Meeting, record: dict) -> dict:
    """Vuelve a aplicar las llamadas a herramientas ya registradas en una corrida, con el código actual.

    No llama al modelo. Sirve para configuraciones sin verificación (S1–S3): la extracción no depende
    de la consolidación ni del render, así que el resultado es el mismo que volver a correr.
    """
    if record["config"]["verify"]:
        raise ValueError("La verificación llama al modelo: esta configuración hay que volver a correrla")
    registry = Registry(meeting)
    for call in record["llamadas_herramientas"]:
        if call.get("_aplicada_a") is None:
            continue
        c = {k: v for k, v in call.items() if not k.startswith("_") and k != "pasada"}
        registry.apply(c, {c["utterance_id"]})
    consolidate(registry, meeting)
    return render(registry, meeting, [], set())
