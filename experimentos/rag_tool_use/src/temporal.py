"""Resolvedor temporal determinista (herramienta del error 4).

El modelo solo copia la expresión literal ("el martes antes de la una") y el ID de la intervención.
Este módulo la convierte a fecha y hora con reglas explícitas y la fecha de la reunión.

Reglas de hora sin "am/pm": 1–7 -> tarde (13–19), 8–11 -> mañana, 12 -> mediodía.
En "entre X y Y" el plazo es el extremo final Y.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

WEEKDAYS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
MONTHS = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
          "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
HOUR_WORDS = {"una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
              "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
HOUR_TOKEN = r"(\d{1,2}(?::\d{2})?|" + "|".join(HOUR_WORDS) + r")"
MINUTE_SUFFIX = r"(?:\s+(y media|y cuarto|menos cuarto|en punto))?"
AMPM = r"(?:\s*(am|a\.m\.|pm|p\.m\.|de la manana|de la tarde|de la noche|de la madrugada))?"


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


@dataclass
class Resolution:
    value: str | None
    date: date | None = None
    time: str | None = None
    rules: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- fechas

def _day_expressions(t: str, meeting: date) -> list[tuple[int, date, str]]:
    """(posición, fecha, regla) para cada expresión de día encontrada en el texto."""
    found: list[tuple[int, date, str]] = []
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", t):
        found.append((m.start(), date(int(m.group(1)), int(m.group(2)), int(m.group(3))), "fecha ISO"))
    for m in re.finditer(r"\b(\d{1,2}) de (" + "|".join(MONTHS) + r")\b", t):
        d = date(meeting.year, MONTHS[m.group(2)], int(m.group(1)))
        if d < meeting:
            d = date(meeting.year + 1, d.month, d.day)
        found.append((m.start(), d, "día y mes explícitos"))
    for m in re.finditer(r"\b(" + "|".join(WEEKDAYS) + r")(?:\s+(\d{1,2})\b)?", t):
        if any(abs(m.start() - p) < 12 for p, _, r in found if r == "día y mes explícitos"):
            continue
        wd = WEEKDAYS[m.group(1)]
        delta = (wd - meeting.weekday()) % 7 or 7
        d = meeting + timedelta(days=delta)
        rule = f"próximo {m.group(1)}"
        if m.group(2):
            num = int(m.group(2))
            candidates = [meeting + timedelta(days=k) for k in range(0, 40) if (meeting + timedelta(days=k)).day == num]
            if candidates:
                cand = candidates[0]
                rule = f"{m.group(1)} {num}"
                if cand.weekday() != wd:
                    rule += " (el número no coincide con el día de la semana; se usa el número)"
                d = cand
        found.append((m.start(), d, rule))
    for m in re.finditer(r"\bpasado manana\b", t):
        found.append((m.start(), meeting + timedelta(days=2), "pasado mañana"))
    for m in re.finditer(r"(?<!pasado )(?<!la )(?<!de la )\bmanana\b", t):
        if re.match(r"manana\s+(" + "|".join(WEEKDAYS) + ")", t[m.start():]):
            continue  # "mañana viernes": lo resuelve el día de la semana
        found.append((m.start(), meeting + timedelta(days=1), "mañana = reunión + 1"))
    for m in re.finditer(r"\bhoy\b", t):
        found.append((m.start(), meeting, "hoy"))
    return sorted(found, key=lambda x: x[0])


# ---------------------------------------------------------------- horas

def _hour_value(token: str) -> tuple[int, int]:
    if ":" in token:
        h, mi = token.split(":")
        return int(h), int(mi)
    if token.isdigit():
        return int(token), 0
    return HOUR_WORDS[token], 0


def _apply_suffix(h: int, mi: int, suffix: str | None) -> tuple[int, int]:
    if suffix == "y media":
        mi = 30
    elif suffix == "y cuarto":
        mi = 15
    elif suffix == "menos cuarto":
        h, mi = h - 1, 45
    return h, mi


def _apply_meridiem(h: int, mi: int, marker: str | None, explicit_24h: bool) -> tuple[int, int, str]:
    if explicit_24h and h > 12:
        return h, mi, "hora en formato 24 h"
    if marker in ("pm", "p.m.", "de la tarde", "de la noche"):
        return (h + 12 if h < 12 else h), mi, "marcador de tarde"
    if marker in ("am", "a.m.", "de la manana", "de la madrugada"):
        return (0 if h == 12 else h), mi, "marcador de mañana"
    if 1 <= h <= 7:
        return h + 12, mi, f"{h} sin am/pm -> {h + 12}:00 (horario laboral)"
    return h, mi, "hora laboral de mañana" if h < 12 else "mediodía"


def _time_expressions(t: str) -> list[tuple[int, int, int, str]]:
    """(posición, hora, minuto, regla)."""
    found: list[tuple[int, int, int, str]] = []
    rng = re.finditer(r"\bentre (?:las |la )?" + HOUR_TOKEN + MINUTE_SUFFIX + r" y (?:las |la )?" + HOUR_TOKEN + MINUTE_SUFFIX + AMPM, t)
    spans = []
    for m in rng:
        h1, m1 = _apply_suffix(*_hour_value(m.group(1)), m.group(2))
        h2, m2 = _apply_suffix(*_hour_value(m.group(3)), m.group(4))
        h1, m1, _ = _apply_meridiem(h1, m1, None, ":" in m.group(1))
        h2, m2, rule = _apply_meridiem(h2, m2, m.group(5), ":" in m.group(3))
        if h2 <= h1:
            h2 += 12
        found.append((m.start(), h2, m2, f"rango: se usa el extremo final ({rule})"))
        spans.append((m.start(), m.end()))
    pattern = r"\b(?:a|de|antes de|hasta|desde|para|tipo)?\s*(?:las|la)\s+" + HOUR_TOKEN + MINUTE_SUFFIX + AMPM
    for m in re.finditer(pattern, t):
        if any(a <= m.start() < b for a, b in spans):
            continue
        token = m.group(1)
        h, mi = _apply_suffix(*_hour_value(token), m.group(2))
        h, mi, rule = _apply_meridiem(h, mi, m.group(3), ":" in token)
        found.append((m.start(), h, mi, rule))
    for m in re.finditer(r"\b(\d{1,2}):(\d{2})\b", t):
        if any(abs(m.start() - p) < 12 for p, *_ in found):
            continue
        found.append((m.start(), int(m.group(1)), int(m.group(2)), "hora explícita"))
    for m in re.finditer(r"\bmediodia\b", t):
        found.append((m.start(), 12, 0, "mediodía"))
    for m in re.finditer(r"\b(diez|nueve|once|doce|\d{1,2}) menos cuarto\b", t):
        if any(abs(m.start() - p) < 12 for p, *_ in found):
            continue
        h = _hour_value(m.group(1))[0] - 1
        found.append((m.start(), h, 45, "menos cuarto"))
    return sorted(found, key=lambda x: x[0])


# ---------------------------------------------------------------- API

def resolve(literal: str | None, meeting: date, utterance_text: str | None = None) -> Resolution:
    if not literal or not literal.strip() or fold(literal) in {"null", "none", "sin fecha"}:
        return Resolution(None, rules=["sin plazo"])
    t = fold(literal)
    days = _day_expressions(t, meeting)
    times = _time_expressions(t)
    res = Resolution(None)

    if times:
        pos, h, mi, rule = times[-1]
        res.time = f"{h:02d}:{mi:02d}"
        res.rules.append(rule)
        before = [d for d in days if d[0] <= pos]
        chosen = before[-1] if before else (days[-1] if days else None)
    else:
        chosen = days[-1] if days else None

    if chosen is None and utterance_text:
        u = fold(utterance_text)
        udays = _day_expressions(u, meeting)
        if udays:
            anchor = u.find(t[:20]) if t[:20] in u else len(u)
            before = [d for d in udays if d[0] <= anchor]
            chosen = before[-1] if before else udays[0]
            res.rules.append("día tomado de la intervención citada")
    if chosen is not None:
        res.date = chosen[1]
        res.rules.append(chosen[2])

    if re.search(r"primera hora|en la manana|en la tarde|temprano", t) and res.time is None:
        res.alerts.append(f"plazo sin hora exacta: '{literal}'")
    if res.date is None and res.time is not None:
        res.alerts.append(f"hora sin día: '{literal}'")
        return res
    if res.date is None:
        res.alerts.append(f"expresión temporal no reconocida: '{literal}'")
        return res
    res.value = f"{res.date.isoformat()} {res.time}" if res.time else res.date.isoformat()
    return res


TEMPORAL_WORDS = set(WEEKDAYS) | set(HOUR_WORDS) | {"manana", "hoy", "mediodia", "media", "cuarto", "pasado"}


def _temporal_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9:]+", fold(text)) if t in TEMPORAL_WORDS or re.fullmatch(r"\d{1,2}(:\d{2})?", t)}


def anchor(literal: str | None, utterance_text: str, meeting: date) -> Resolution:
    """Resuelve el plazo usando la intervención citada como fuente de verdad.

    Si el literal del modelo aparece textual en la intervención, se resuelve tal cual. Si no
    (el modelo lo parafraseó o lo inventó), se elige la cláusula de la intervención con expresión
    temporal que más palabras temporales comparte con el literal.
    """
    if not literal or fold(literal) in {"null", "none", "sin fecha"}:
        return resolve(None, meeting)
    if fold(literal) in fold(utterance_text):
        res = resolve(literal, meeting, utterance_text)
        if res.value:
            res.rules.insert(0, "literal textual")
            return res
    clauses = [c.strip() for c in re.split(r"[.;:!?,]", utterance_text) if c.strip()]
    candidates = []
    for c in clauses:
        r = resolve(c, meeting, utterance_text)
        if r.value:
            candidates.append((len(_temporal_tokens(c) & _temporal_tokens(literal)), c, r))
    if candidates:
        best = max(candidates, key=lambda x: x[0])
        if best[0] > 0 or len(candidates) == 1:
            best[2].rules.insert(0, f"literal '{literal}' anclado a '{best[1]}'")
            return best[2]
    res = resolve(literal, meeting, utterance_text)
    res.alerts.append(f"plazo '{literal}' no aparece en la intervención citada")
    return res
