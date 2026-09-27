"""Lectura de transcripciones de reuniones.

Acepta tres formatos de intervención (se puede mezclar metadatos de cabecera con cualquiera):

  1. Canónico del proyecto:   **[U001 | 09:30:04 | Camila]** texto
  2. Con hora:                [09:30] Camila: texto        o   09:30:04 Camila: texto
  3. Simple:                  Camila: texto

En los formatos 2 y 3 los IDs U001, U002… se asignan en orden. Metadatos reconocidos en la cabecera
(con o sin guion inicial): "Fecha: 27 de agosto de 2026" (o 2026-08-27, 27/08/2026), "Tema…: …",
"Participantes presentes:" seguido de líneas "  - Nombre - rol" o "Participantes: Ana, Luis y Pedro",
y "Personas mencionadas…: …" o "Ausentes: …". Todo se puede pasar también desde la línea de comandos.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

CANONICAL_RE = re.compile(r"^\*\*\[(U\d+) \| ([\d:\-]+) \| ([^\]]+)\]\*\*\s*(.*)$")
TIMED_RE = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s+([^:\[\]]{1,40}?):\s+(.+)$")
SIMPLE_RE = re.compile(r"^\*{0,2}([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñü.'\- ]{0,39}?)\*{0,2}:\*{0,2}\s+(.+)$")
META_KEYS = ("fecha", "hora", "tema", "participantes", "personas mencionadas", "ausentes", "asistentes")


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


@dataclass
class Utterance:
    id: str
    time: str
    speaker: str
    text: str

    def render(self) -> str:
        return f"[{self.id} | {self.time} | {self.speaker}] {self.text}" if self.time else f"[{self.id} | {self.speaker}] {self.text}"


@dataclass
class Meeting:
    date: date
    topic: str
    participants: dict[str, str]          # nombre completo -> rol
    absent_mentioned: list[str]
    utterances: list[Utterance] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def by_id(self) -> dict[str, Utterance]:
        return {u.id: u for u in self.utterances}

    def first_names(self) -> dict[str, str]:
        """Etiqueta corta -> nombre completo de cada participante presente.

        La etiqueta es el nombre de pila; si dos personas lo comparten, se usa el nombre completo.
        """
        firsts = [full.split()[0] for full in self.participants]
        return {(full.split()[0] if firsts.count(full.split()[0]) == 1 else full): full for full in self.participants}


def parse_date(text: str) -> date:
    t = _fold(text)
    m = re.search(r"(\d{1,2}) de (\w+) de (\d{4})", t)
    if m and m.group(2) in MONTHS:
        return date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    raise ValueError(f"Fecha no reconocida: {text!r}. Usa '27 de agosto de 2026', '2026-08-27' o '27/08/2026'.")


parse_spanish_date = parse_date  # nombre anterior


def split_names(text: str) -> list[str]:
    return [n.strip(" .") for n in re.split(r",|;| y ", text) if n.strip(" .")]


def _meta_key(stripped: str) -> tuple[str, str] | None:
    body = stripped.lstrip("-* ").strip()
    key, sep, value = body.partition(":")
    if not sep:
        return None
    k = _fold(key)
    for known in META_KEYS:
        if k.startswith(known):
            return known, value.strip()
    return None


def load_meeting(path: str | Path, *, fecha: str | None = None, presentes: str | None = None,
                 ausentes: str | None = None, tema: str | None = None) -> Meeting:
    """Lee una transcripción. Los argumentos con nombre reemplazan lo que diga la cabecera."""
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    meeting_date = None
    topic = ""
    participants: dict[str, str] = {}
    absent: list[str] = []
    utterances: list[Utterance] = []
    warnings: list[str] = []
    in_participants = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = CANONICAL_RE.match(stripped)
        if m:
            time = "" if "-" in m.group(2) else m.group(2)
            utterances.append(Utterance(m.group(1), time, m.group(3).strip(), m.group(4).strip()))
            in_participants = False
            continue
        meta = _meta_key(stripped) if not utterances else None
        if meta:
            key, value = meta
            in_participants = False
            if key == "fecha":
                meeting_date = parse_date(value)
            elif key == "tema":
                topic = value
            elif key in ("participantes", "asistentes"):
                if value:
                    for name in split_names(value):
                        n, _, role = name.partition("(")
                        participants[n.strip()] = role.rstrip(")").strip()
                else:
                    in_participants = True
            elif key in ("personas mencionadas", "ausentes"):
                absent = split_names(value)
            continue
        if in_participants and re.match(r"^\s*[-*]\s+", line):
            name, _, role = re.sub(r"^\s*[-*]\s+", "", line).partition(" - ")
            participants[name.strip()] = role.strip()
            continue
        in_participants = False
        m = TIMED_RE.match(stripped)
        if m:
            utterances.append(Utterance(f"U{len(utterances) + 1:03d}", m.group(1), m.group(2).strip(), m.group(3).strip()))
            continue
        m = SIMPLE_RE.match(stripped)
        if m and _fold(m.group(1)) not in META_KEYS:
            utterances.append(Utterance(f"U{len(utterances) + 1:03d}", "", m.group(1).strip(), m.group(2).strip()))
            continue
        if utterances:
            # Línea sin hablante después de una intervención: continuación del mismo turno.
            utterances[-1].text += " " + stripped

    if fecha:
        meeting_date = parse_date(fecha)
    if tema:
        topic = tema
    if presentes:
        participants = {n: participants.get(n, "") for n in split_names(presentes)}
    if ausentes is not None:
        absent = split_names(ausentes)

    if meeting_date is None:
        raise ValueError("La transcripción no declara fecha: agrega 'Fecha: …' en la cabecera o usa --fecha AAAA-MM-DD. "
                         "Sin fecha no se pueden resolver 'mañana', 'el lunes', etc.")
    if not utterances:
        raise ValueError("No se reconoció ninguna intervención. Formatos: '**[U001 | 09:30:04 | Ana]** texto', "
                         "'[09:30] Ana: texto' o 'Ana: texto'.")
    ids = [u.id for u in utterances]
    if len(set(ids)) != len(ids):
        raise ValueError("Hay IDs de intervención repetidos en la transcripción.")

    # Todo el que habla está presente. Se agrega a participantes si la cabecera no lo nombró.
    known_first = {_fold(full.split()[0]) for full in participants} | {_fold(full) for full in participants}
    for u in utterances:
        if _fold(u.speaker) not in known_first and _fold(u.speaker.split()[0]) not in known_first:
            participants[u.speaker] = ""
            known_first |= {_fold(u.speaker), _fold(u.speaker.split()[0])}
            warnings.append(f"'{u.speaker}' habla pero no estaba en la lista de presentes: se agregó.")
    for a in absent:
        if _fold(a) in known_first:
            warnings.append(f"'{a}' figura como ausente pero también como presente o hablante; revisa la cabecera.")
    meeting = Meeting(meeting_date, topic, participants, absent, utterances, warnings)
    labels = meeting.first_names()
    if len(labels) != len(participants):
        raise ValueError("Hay participantes con el mismo nombre completo; usa etiquetas distintas.")
    return meeting


def to_canonical(meeting: Meeting) -> str:
    """La reunión en el formato canónico del proyecto (con IDs), para el prompt del baseline."""
    lines = ["# Transcripción", "", "## Metadatos entregados al modelo", "",
             f"- Fecha: {meeting.date.day} de {[k for k, v in MONTHS.items() if v == meeting.date.month][0]} de {meeting.date.year}"]
    if meeting.topic:
        lines.append(f"- Tema declarado: {meeting.topic}")
    lines.append("- Participantes presentes:")
    lines += [f"  - {full}" + (f" - {role}" if role else "") for full, role in meeting.participants.items()]
    if meeting.absent_mentioned:
        lines.append(f"- Personas mencionadas que no participan en la reunión: {', '.join(meeting.absent_mentioned)}")
    lines += ["", "## Transcripción", ""]
    lines += [f"**[{u.id} | {u.time or '--:--'} | {u.speaker}]** {u.text}\n" for u in meeting.utterances]
    return "\n".join(lines)
