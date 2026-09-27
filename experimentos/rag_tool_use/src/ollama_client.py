"""Cliente mínimo de Ollama (solo biblioteca estándar) con registro de cada llamada."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import urllib.request

HOST = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
MODEL = os.environ.get("D2_MODEL", "ministral-3:3b")

# Mismos controles que scripts/run_model_test.ps1 (D1).
DEFAULT_OPTIONS = {"num_ctx": 8192, "temperature": 0, "seed": 42}


def _post(path: str, body: dict, timeout: float = 3600) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(HOST + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(HOST + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def environment(model: str = MODEL) -> dict:
    """Versión de Ollama, digest del modelo y hardware, para registrar en cada corrida."""
    info: dict = {"model": model, "python": platform.python_version(), "platform": platform.platform(),
                  "processor": platform.processor() or platform.machine()}
    try:
        info["ollama_version"] = _get("/api/version").get("version")
    except Exception as exc:  # noqa: BLE001
        info["ollama_version"] = f"error: {exc}"
    try:
        tags = _get("/api/tags").get("models", [])
        match = next((t for t in tags if t.get("name") == model or t.get("model") == model), None)
        if match:
            info["model_digest"] = match.get("digest")
            info["model_digest_short"] = (match.get("digest") or "")[:12]
            info["model_details"] = match.get("details")
    except Exception as exc:  # noqa: BLE001
        info["model_digest"] = f"error: {exc}"
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=10)
        if gpu.returncode == 0:
            info["gpu"] = gpu.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    if platform.system() == "Darwin":
        try:
            info["cpu"] = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                         capture_output=True, text=True).stdout.strip()
        except FileNotFoundError:
            pass
    return info


def _metrics(result: dict, started: float) -> dict:
    eval_count = result.get("eval_count") or 0
    eval_s = (result.get("eval_duration") or 0) / 1e9
    return {
        "prompt_eval_count": result.get("prompt_eval_count"),
        "eval_count": eval_count,
        "prompt_eval_duration_s": round((result.get("prompt_eval_duration") or 0) / 1e9, 3),
        "eval_duration_s": round(eval_s, 3),
        "load_duration_s": round((result.get("load_duration") or 0) / 1e9, 3),
        "total_duration_s": round((result.get("total_duration") or 0) / 1e9, 3),
        "wall_s": round(time.time() - started, 3),
        "tok_per_s": round(eval_count / eval_s, 2) if eval_s else None,
        "done_reason": result.get("done_reason"),
    }


def generate(prompt: str, *, model: str = MODEL, fmt="json", num_predict: int = 3000,
             keep_alive: str | int = "10m", think: bool = False, options: dict | None = None) -> dict:
    """/api/generate, como el script del D1. Devuelve registro con prompt, respuesta cruda y métricas."""
    opts = {**DEFAULT_OPTIONS, "num_predict": num_predict, **(options or {})}
    body = {"model": model, "prompt": prompt, "stream": False, "format": fmt, "think": think,
            "keep_alive": keep_alive, "options": opts}
    started = time.time()
    result = _post("/api/generate", body)
    return {"endpoint": "/api/generate", "options": opts, "format": fmt, "prompt": prompt,
            "response_raw": result.get("response", ""), **_metrics(result, started)}


def chat(messages: list[dict], *, model: str = MODEL, fmt=None, num_predict: int = 1024,
         keep_alive: str | int = "10m", options: dict | None = None) -> dict:
    """/api/chat con salida opcionalmente restringida por un JSON schema (`fmt`)."""
    opts = {**DEFAULT_OPTIONS, "num_predict": num_predict, **(options or {})}
    body = {"model": model, "messages": messages, "stream": False, "think": False,
            "keep_alive": keep_alive, "options": opts}
    if fmt is not None:
        body["format"] = fmt
    started = time.time()
    result = _post("/api/chat", body)
    return {"endpoint": "/api/chat", "options": opts, "messages": messages,
            "response_raw": (result.get("message") or {}).get("content", ""), **_metrics(result, started)}
