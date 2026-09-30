# Video D2: guion de demostración real

Duración objetivo: **2:45 a 2:55**. Grabar una sola toma en Google Colab con GPU T4. No ocultar el comando, el progreso ni la salida.

## Preparación antes de grabar

1. Trabajar sobre el commit final ya publicado en `main`.
2. Abrir `GenAI Constrained+Tool use/Ministral_Minutas_Colab.ipynb` desde GitHub.
3. Ejecutar las celdas de instalación, descarga del modelo y carga del dataset antes de iniciar la grabación.
4. En la celda de configuración cambiar `DEMO_ONLY = False` por `DEMO_ONLY = True`. No modificar prompts, modelo ni parámetros.
5. Dejar abiertas estas pestañas:
   - commit final de GitHub;
   - notebook listo para ejecutar M01;
   - `GenAI Constrained+Tool use/minutas_resultados_test.zip`;
   - `resultados/tesla-t4/tabla_d1.md`, como prueba complementaria del formato completo.
6. Usar una sesión nueva o borrar `/content/minutas_d2/results/test` para impedir que `run_cached` reutilice salidas.

## Toma única

### 0:00–0:10 · Trazabilidad

- Mostrar el repositorio público y el hash corto del commit.
- Decir: «Usamos Ministral 3B, el candidato más pequeño; M01 es la primera entrada del test, no un caso escogido por rendimiento».

### 0:10–0:20 · Entrada y baseline

- Mostrar la entrada M01, su fecha, participantes e IDs.
- Dejar visible `DEMO_ONLY=True` y que se ejecutarán baseline, JSON restringido e intervención sobre la misma entrada.

### 0:20–2:48 · Ejecución real

Ejecutar visiblemente las celdas de inferencia y evaluación del notebook. Deben aparecer las tres llamadas de M01 y sus tiempos. Mantener visibles el progreso y el final; no reemplazar este tramo por una animación o una salida preparada.

### 2:48–2:55 · Resultado y evidencia

- Comparar `M01_baseline.json` con `M01_combined_v2.json`.
- Destacar que la intervención produce esquema válido, seis decisiones, cinco tareas e IDs existentes.
- Mostrar el fallo: fusiona las dos fechas obsoletas y convierte «antes de las seis» en 17:00.
- Mostrar la tabla final ya preparada en pantalla: decisiones `0,477 → 0,667`, tareas `0,667 → 0,716`, JSON `0/10 → 10/10`.
- Cerrar: «Mejora formato y cobertura, pero aún falla en estados, plazos y respaldo semántico; el caso D1 completo está trazado en el repositorio».

## Comprobación antes de enviar

- El archivo dura menos de 3:00.
- La entrada y el baseline corresponden exactamente al mismo caso.
- El comando y el progreso son legibles.
- El enlace abre sin iniciar sesión.
- El commit mostrado contiene los mismos archivos y resultados del video.
