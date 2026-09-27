| Métrica | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación | S3b · S2 + RAG mejorado | Control · S2 + todo el pasado |
|---|---|---|---|---|---|---|---|
| JSON válido | no (cortado) | sí | sí | sí | sí | sí | sí |
| Errores de esquema | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Decisiones correctas | 5/9 | 4/9 | 7/9 | 6/9 | 7/9 | 6/9 | 7/9 |
| Precisión decisiones | 0.833 | 0.8 | 0.389 | 0.286 | 0.368 | 0.286 | 0.368 |
| Estados obsoletos | 0/2 | 0/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| Tareas identificadas | 6/7 | 4/7 | 7/7 | 7/7 | 6/7 | 7/7 | 7/7 |
| Precisión tareas | 1.0 | 0.8 | 0.368 | 0.333 | 0.353 | 0.333 | 0.35 |
| Responsable exacto | 5/6 | 4/4 | 7/7 | 7/7 | 6/6 | 7/7 | 7/7 |
| Plazo exacto | 4/6 | 4/4 | 5/7 | 5/7 | 5/6 | 4/7 | 5/7 |
| Condición obligatoria | 2/2 | 1/1 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Pendientes | 1/4 | 0/4 | 1/4 | 1/4 | 1/4 | 1/4 | 3/4 |
| Personas ausentes asignadas | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas no textuales (tipo 1+2) | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas byte a byte no exactas | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| Citas tipo 3 (proxy) | 15 | 1 | 6 | 3 | 4 | 5 | 5 |
| Llamadas al modelo | 1 | 2 | 18 | 18 | 92 | 18 | 18 |
| Tokens generados | 3000 | 928 | 6128 | 6583 | 6776 | 6689 | 7148 |
| Tokens de entrada | 4190 | 7575 | 33433 | 37809 | 85811 | 37579 | 56802 |
| Tiempo total (s) | 84.38 | 42.36 | 207.4 | 236.15 | 276.4 | 210.59 | 354.95 |

Hardware: Apple M5 · Ollama 0.33.3 · modelo ministral-3:3b (f04aa1c738f6)
