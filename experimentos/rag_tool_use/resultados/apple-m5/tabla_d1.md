| Criterio del D1 | D1 original | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación | S3b · S2 + RAG mejorado | Control · S2 + todo el pasado |
|---|---|---|---|---|---|---|---|---|
| Salida final | JSON válido; 2 errores de esquema | JSON inválido; 2 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema |
| Historial apertura | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final omitida | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta |
| Decisiones clave: soporte solo por correo (U030) | omitida | recuperada | omitida | recuperada | recuperada | recuperada | recuperada | recuperada |
| Decisiones clave: demo remota, credencial + QA, bloqueadores (omitidas en el D1) | 0/3 | 1/3 | 2/3 | 2/3 | 1/3 | 2/3 | 1/3 | 2/3 |
| Tareas | Escribió 6; recuperó 6/7 (automático) | Escribió 6; recuperó 6/7 (automático) | Escribió 5; recuperó 4/7 (automático) | Escribió 19; recuperó 7/7 (automático) | Escribió 21; recuperó 7/7 (automático) | Escribió 17; recuperó 6/7 (automático) | Escribió 21; recuperó 7/7 (automático) | Escribió 20; recuperó 7/7 (automático) |
| Tareas partidas o duplicadas | - | - | - | - | - | - | - | - |
| Tareas extra (no están en el gold) | - | - | - | - | - | - | - | - |
| Plazos: regresión de Martín (13:00) | ✗ 01:00 | ✗ 01:00 | tarea omitida | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 |
| Plazos: errores de 12 h (am/pm) | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Plazos: otros plazos incorrectos | 0 | 1 | 0 | 2 | 2 | 1 | 3 | 2 |
| Enlaces de evidencia incorrectos (automático) | 3/21 | 18/37 | 1/16 | 6/79 | 3/85 | 4/68 | 5/86 | 5/97 |
| Personas ausentes asignadas | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tiempo | 22m06s (i5-9300H + GTX 1050) | 84 s (Apple M5; 3000 tokens) | 42 s (Apple M5; 928 tokens) | 207 s (Apple M5; 6128 tokens) | 236 s (Apple M5; 6583 tokens) | 276 s (Apple M5; 6776 tokens) | 211 s (Apple M5; 6689 tokens) | 355 s (Apple M5; 7148 tokens) |
