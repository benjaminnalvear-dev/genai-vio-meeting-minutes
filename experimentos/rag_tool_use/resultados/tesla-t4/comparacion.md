| Métrica | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación |
|---|---|---|---|---|---|
| JSON válido | sí | sí | sí | sí | sí |
| Errores de esquema | 2 | 0 | 0 | 0 | 0 |
| Decisiones correctas /9 | 3 | 3 | 5 | 6 | 6 |
| Precisión decisiones | 1.0 | 0.75 | 0.25 | 0.24 | 0.273 |
| Superseded lanzamiento /2 | 0 | 0 | 1 | 1 | 1 |
| Tareas identificadas /7 | 5 | 3 | 7 | 7 | 7 |
| Precisión tareas | 0.833 | 0.75 | 0.368 | 0.438 | 0.5 |
| Responsable exacto | 5/5 | 3/3 | 7/7 | 7/7 | 7/7 |
| Plazo exacto | 4/5 | 3/3 | 5/7 | 4/7 | 5/7 |
| Condición obligatoria | 2/2 | 1/1 | 2/2 | 2/2 | 2/2 |
| Pendientes /4 | 2 | 1 | 3 | 2 | 0 |
| Personas ausentes asignadas | 0 | 0 | 0 | 0 | 0 |
| Citas no textuales (tipo 1+2) | 3 | 0 | 0 | 0 | 0 |
| Citas byte a byte no exactas | 7 | 0 | 0 | 0 | 0 |
| Citas tipo 3 (proxy) | 5 | 3 | 13 | 9 | 8 |
| Llamadas al modelo | 1 | 2 | 18 | 18 | 90 |
| Tokens generados | 2455 | 1069 | 6663 | 6559 | 6747 |
| Tokens de entrada | 4190 | 7575 | 33107 | 37019 | 83624 |
| Tiempo total (s) | 45.87 | 21.37 | 116.38 | 116.36 | 122.99 |

Hardware: Tesla T4, 15360 MiB · Ollama 0.33.3 · modelo ministral-3:3b (f04aa1c738f6)
