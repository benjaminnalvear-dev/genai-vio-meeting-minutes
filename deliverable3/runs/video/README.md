# Corrida del video (M01, condición `full`)

Salida de la corrida grabada en el [video](https://www.youtube.com/watch?v=pexxeQTg9Mk): notebook en modo `DEMO`, Colab con GPU T4, código del commit `999c930` y Ollama 0.40.13, con el mismo modelo (digest `f04aa1c7…`).

| Archivo | Contenido |
|---|---|
| `M01_trace.jsonl` | Mensajes entre agentes que muestra la celda 6 del notebook |
| `M01_result.json` | Acta final que muestra la celda 7 |
| `summary.json` | Métricas de esa corrida (una reunión) |

La traza es idéntica, evento por evento, a la de la corrida evaluada [`../test/traces/full/M01.jsonl`](../test/traces/full/M01.jsonl). Solo cambian las marcas de tiempo y los segundos. El acta final también es idéntica.
