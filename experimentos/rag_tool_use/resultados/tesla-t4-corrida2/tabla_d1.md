| Criterio del D1 | D1 original | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación | S3b · S2 + RAG mejorado | Control · S2 + todo el pasado |
|---|---|---|---|---|---|---|---|---|
| Salida final | JSON válido; 2 errores de esquema | JSON válido; 2 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema |
| Historial apertura | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final omitida | 1/2 estados obsoletos; fecha final omitida | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final omitida | 2/2 estados obsoletos; fecha final correcta |
| Decisiones clave: soporte solo por correo (U030) | omitida | omitida | omitida | recuperada | recuperada | recuperada | recuperada | recuperada |
| Decisiones clave: demo remota, credencial + QA, bloqueadores (omitidas en el D1) | 0/3 | 0/3 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| Tareas | Escribió 6; recuperó 6/7; mezcló 1 | Escribió 6; recuperó 5/7; mezcló 1 | Escribió 4; recuperó 3/7; mezcló 0 | Escribió 19; recuperó 7/7; mezcló 0 | Escribió 16; recuperó 7/7; mezcló 0 | Escribió 15; recuperó 7/7; mezcló 0 | Escribió 19; recuperó 7/7; mezcló 0 | Escribió 21; recuperó 7/7; mezcló 0 |
| Tareas partidas o duplicadas | 0 | 0 | 1 | 4 | 5 | 4 | 6 | 5 |
| Tareas extra (no están en el gold) | 0 | 1 | 0 | 8 | 4 | 4 | 6 | 9 |
| Plazos: regresión de Martín (13:00) | ✗ 01:00 | ✗ 01:00 | tarea omitida | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 |
| Plazos: errores de 12 h (am/pm) | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Plazos: otros plazos incorrectos | 0 | 0 | 0 | 2 | 1 | 1 | 2 | 2 |
| Enlaces de evidencia incorrectos (automático) | 3/21 | 3/22 | 3/16 | 13/91 | 9/91 | 9/79 | 9/92 | 9/98 |
| Personas ausentes asignadas | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tiempo | 22m06s (i5-9300H + GTX 1050) | 45 s (Tesla T4; 2382 tokens) | 22 s (Tesla T4; 1069 tokens) | 119 s (Tesla T4; 6663 tokens) | 121 s (Tesla T4; 6559 tokens) | 127 s (Tesla T4; 6736 tokens) | 126 s (Tesla T4; 6899 tokens) | 155 s (Tesla T4; 7718 tokens) |
