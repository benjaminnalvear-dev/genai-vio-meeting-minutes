| Criterio del D1 | D1 original | B · Baseline (prompt directo D1) | S1 · Tool use, 1 pasada | S2 · Tool use por bloques | S3 · S2 + RAG | S4 · S3 + verificación |
|---|---|---|---|---|---|---|
| Salida final | JSON válido; 2 errores de esquema | JSON válido; 2 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema | JSON válido; 0 errores de esquema |
| Historial apertura | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final correcta | 0/2 estados obsoletos; fecha final omitida | 1/2 estados obsoletos; fecha final omitida | 1/2 estados obsoletos; fecha final correcta | 1/2 estados obsoletos; fecha final correcta |
| Decisiones clave: soporte solo por correo (U030) | omitida | recuperada | omitida | recuperada | recuperada | recuperada |
| Decisiones clave: demo remota, credencial + QA, bloqueadores (omitidas en el D1) | 0/3 | 0/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| Tareas | Escribió 6; recuperó 6/7; mezcló 1 | Escribió 6; recuperó 5/7; mezcló 1 | Escribió 4; recuperó 3/7; mezcló 0 | Escribió 19; recuperó 7/7; mezcló 0 | Escribió 16; recuperó 7/7; mezcló 0 | Escribió 14; recuperó 7/7; mezcló 0 |
| Tareas partidas o duplicadas | 0 | 0 | 1 | 4 | 5 | 4 |
| Tareas extra (no están en el gold) | 0 | 1 | 0 | 8 | 4 | 3 |
| Plazos: regresión de Martín (13:00) | ✗ 01:00 | ✓ 13:00 | tarea omitida | ✓ 13:00 | ✓ 13:00 | ✓ 13:00 |
| Plazos: errores de 12 h (am/pm) | 1 | 1 | 0 | 0 | 0 | 0 |
| Plazos: otros plazos incorrectos | 0 | 0 | 0 | 2 | 1 | 1 |
| Enlaces de evidencia incorrectos (automático) | 3/21 | 8/27 | 3/16 | 13/91 | 9/91 | 8/74 |
| Personas ausentes asignadas | 1 | 0 | 0 | 0 | 0 | 0 |
| Tiempo | 22m06s (i5-9300H + GTX 1050) | 46 s (Tesla T4; 2455 tokens) | 21 s (Tesla T4; 1069 tokens) | 116 s (Tesla T4; 6663 tokens) | 116 s (Tesla T4; 6559 tokens) | 123 s (Tesla T4; 6747 tokens) |
