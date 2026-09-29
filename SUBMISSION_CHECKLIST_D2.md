# Checklist final del Entregable 2

## Artefactos verificados

- [x] PDF vertical de una página compilado desde LaTeX.
- [x] Diagrama del pipeline.
- [x] Modelo y versión declarados.
- [x] Baseline y solución medidos sobre las mismas 10 entradas.
- [x] Tamaño del conjunto declarado.
- [x] Estrategias alternativas y ablaciones.
- [x] Caso de falla real con explicación causal.
- [x] README con pasos de reproducción.
- [x] 13 pruebas del pipeline modular aprobadas.
- [x] Respuestas crudas y resultados agregados versionados.

## Acciones humanas pendientes

- [ ] Grabar la ejecución real siguiendo `VIDEO_D2.md`.
- [ ] Publicar el video con acceso abierto.
- [ ] Confirmar que dura menos de 3:00.
- [ ] Revisar que no se muestren claves, tokens ni información personal.
- [ ] Hacer commit de los artefactos D2 y del workflow.
- [ ] Hacer push a `main`.
- [ ] Abrir en una ventana de incógnito el repositorio, PDF, notebook, ZIP y video.
- [ ] Entregar el enlace del video y el enlace al commit final, no a una copia local.

## Comprobaciones rápidas

```powershell
pdfinfo .\Deliverable_2.pdf
cd .\experimentos\rag_tool_use
python -m unittest discover -s tests -v
git status --short
```

El resultado de `pdfinfo` debe mostrar `Pages: 1`, tamaño Letter vertical y productor pdfTeX/MiKTeX o TeX Live.
