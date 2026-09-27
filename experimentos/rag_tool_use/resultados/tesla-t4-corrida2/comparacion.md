| Métrica | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación | S3b · S2 + RAG mejorado | Control · S2 + todo el pasado |
|---|---|---|---|---|---|---|---|
| JSON válido | sí | sí | sí | sí | sí | sí | sí |
| Errores de esquema | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Decisiones correctas | 3/9 | 3/9 | 5/9 | 6/9 | 6/9 | 5/9 | 6/9 |
| Precisión decisiones | 0.75 | 0.75 | 0.25 | 0.24 | 0.261 | 0.227 | 0.462 |
| Estados obsoletos | 0/2 | 0/2 | 1/2 | 1/2 | 1/2 | 1/2 | 2/2 |
| Tareas identificadas | 6/7 | 3/7 | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 |
| Precisión tareas | 1.0 | 0.75 | 0.368 | 0.438 | 0.467 | 0.368 | 0.333 |
| Responsable exacto | 6/6 | 3/3 | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 |
| Plazo exacto | 3/6 | 3/3 | 5/7 | 4/7 | 5/7 | 4/7 | 4/7 |
| Condición obligatoria | 2/2 | 1/1 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Pendientes | 2/4 | 1/4 | 3/4 | 2/4 | 1/4 | 2/4 | 1/4 |
| Personas ausentes asignadas | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas no textuales (tipo 1+2) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas byte a byte no exactas | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas tipo 3 (proxy) | 3 | 3 | 13 | 9 | 9 | 9 | 9 |
| Llamadas al modelo | 1 | 2 | 18 | 18 | 85 | 18 | 18 |
| Tokens generados | 2382 | 1069 | 6663 | 6559 | 6736 | 6899 | 7718 |
| Tokens de entrada | 4190 | 7575 | 33107 | 37019 | 80464 | 37012 | 56950 |
| Tiempo total (s) | 44.62 | 21.67 | 119.23 | 120.55 | 127.17 | 126.11 | 155.48 |

Hardware: Tesla T4, 15360 MiB · Ollama 0.33.3 · modelo ministral-3:3b (f04aa1c738f6)
