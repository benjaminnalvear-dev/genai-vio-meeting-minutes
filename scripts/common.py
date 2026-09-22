"""Utilidades compartidas: lectura de transcripciones y llamada a Ollama.

Todo el proyecto usa estos mismos parámetros para que baseline y pipeline
corran bajo condiciones idénticas (misma configuración del entregable 1).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "ministral-3:3b"
DEFAULT_OPTIONS = {"num_ctx": 8192, "temperature": 0, "seed": 42, "num_predict": 3000}

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

UTTERANCE_RE = re.compile(r"^\*\*\[(U\d+)\s*\|\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\|\s*([^\]]+?)\]\*\*\s*(.*)$")


# ---------------------------------------------------------------- transcripciones
def load_transcript(path: str | Path) -> dict:
    """Lee una transcripción en el formato de pruebas/ y la devuelve estructurada.

    Devuelve {"raw": texto completo, "date": "YYYY-MM-DD" | None,
              "utterances": [{"id", "time", "speaker", "text"}, ...]}
    """
    raw = Path(path).read_text(encoding="utf-8")
    utterances = []
    for line in raw.splitlines():
        m = UTTERANCE_RE.match(line.strip())
        if m:
            uid, t, speaker, text = m.groups()
            utterances.append({"id": uid, "time": t, "speaker": speaker.strip(), "text": text.strip()})

    meeting_date = None
    m = re.search(r"Fecha:\s*(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", raw, re.I)
    if m:
        d, mes, y = m.groups()
        meeting_date = date(int(y), MESES[mes.lower()], int(d)).isoformat()

    if not utterances:
        raise ValueError(f"No se encontraron intervenciones con formato **[U001 | hh:mm:ss | Nombre]** en {path}")
    return {"raw": raw, "date": meeting_date, "utterances": utterances}


# ---------------------------------------------------------------- normalización de texto
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_loose(s) -> str:
    """Para comparar palabras clave: sin tildes, minúsculas, espacios colapsados."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", strip_accents(str(s)).lower()).strip()


QUOTE_MAP = str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "‘": "'", "’": "'"})


def norm_quote(s) -> str:
    """Para verificar citas textuales: conserva tildes, ignora mayúsculas, comillas
    tipográficas, espacios repetidos y puntuación en los bordes."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", str(s)).translate(QUOTE_MAP).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s.strip(" .,;:…\"'¿?¡!")


# ---------------------------------------------------------------- Ollama
def ollama_host() -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not host.startswith("http"):
        host = "http://" + host
    return host.rstrip("/")


def ollama_version() -> str:
    try:
        out = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return f"desconocida ({e.__class__.__name__})"


def generate(prompt: str, model: str = DEFAULT_MODEL, options: dict | None = None,
             json_mode: bool = True, think: bool = False, timeout: int = 3600) -> dict:
    """Llama a /api/generate igual que run_model_test.ps1 y devuelve la respuesta cruda de Ollama."""
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "keep_alive": "10m",
        "options": {**DEFAULT_OPTIONS, **(options or {})},
    }
    if json_mode:
        body["format"] = "json"
    req = urllib.request.Request(
        ollama_host() + "/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_json_response(text: str):
    """Intenta leer JSON. Devuelve (objeto | None, es_valido)."""
    try:
        return json.loads(text), True
    except (json.JSONDecodeError, TypeError):
        return None, False
