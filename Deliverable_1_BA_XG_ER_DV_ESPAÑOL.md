% PAR SINCRONIZADO: Mantener este archivo alineado con Deliverable_1_BA_XG_ER_DV.md.
% Aplicar cada cambio futuro de contenido o formato a ambas versiones.
\documentclass[10pt]{article}
\usepackage[letterpaper,landscape,margin=0.38in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}

\definecolor{navy}{HTML}{12324A}
\definecolor{blue}{HTML}{1F6E8C}
\definecolor{ice}{HTML}{EAF3F6}
\definecolor{ink}{HTML}{17232B}
\definecolor{muted}{HTML}{52616B}
\definecolor{alert}{HTML}{A3382F}

\newcommand{\repositoryurl}{https://github.com/benjaminnalvear-dev/genai-vio-meeting-minutes}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.9pt}
\setlist[itemize]{leftmargin=1.1em,itemsep=0.35pt,topsep=0.65pt,parsep=0pt}
\setlist[enumerate]{leftmargin=1.35em,itemsep=0.35pt,topsep=0.65pt,parsep=0pt}
\renewcommand{\arraystretch}{1.06}
\color{ink}

\newcommand{\sectionbar}[1]{%
  \vspace{0.25pt}%
  \colorbox{navy}{\parbox{\dimexpr\linewidth-2\fboxsep}{\color{white}\bfseries\sffamily #1}}%
  \vspace{0.25pt}%
}
\newcommand{\callout}[1]{%
  \colorbox{ice}{\parbox{\dimexpr\linewidth-2\fboxsep}{#1}}%
}
\newcommand{\smallcapslabel}[1]{{\color{blue}\bfseries\sffamily #1}}

\begin{document}
\sffamily
\fontsize{7.9}{8.5}\selectfont

\colorbox{navy}{%
  \parbox{\dimexpr\textwidth-2\fboxsep}{%
    \color{white}
    {\fontsize{17}{18.5}\selectfont\bfseries Actas Confiables desde Transcripciones Ruidosas}\hfill
    {\normalsize Entregable 1}\par
    \vspace{1pt}
    {\fontsize{7.4}{8}\selectfont Benjamin Alvear \textbullet{} Eduardo Ruiz \textbullet{} Xavier Godoy \textbullet{} Damian Vera
    \hfill Inteligencia Artificial Generativa (580694) \textbullet{} Entrega: 31 de agosto de 2026}
  }%
}

\vspace{2pt}

\begin{minipage}[t]{0.318\textwidth}
\vspace{0pt}
\raggedright
\sectionbar{1. ESPECIFICACIÓN DE LA TAREA}

\textbf{Objetivo principal.} Crear un sistema que transforme automáticamente la transcripción de una reunión en español en un acta clara, confiable y estructurada. El sistema debe recuperar lo que finalmente se acordó, no limitarse a resumir lo conversado.

\textbf{Entrada inicial.} Una transcripción en texto con IDs de intervención, etiquetas de hablante, marcas de tiempo y fecha de reunión.

\textbf{Salida requerida}
\begin{itemize}
  \item decisiones finales, incluidas las modificadas durante la reunión;
  \item tareas acordadas con responsable, plazo, condiciones y estado;
  \item ideas rechazadas, sustituidas y no resueltas;
  \item temas pendientes y alertas de revisión;
  \item para cada decisión o tarea, un fragmento exacto de respaldo y su ID.
\end{itemize}

\callout{\textbf{Qué cuenta como correcto.} El acta debe reflejar el estado final de la reunión y cada decisión o tarea debe estar sustentada por el fragmento citado. Una propuesta no es una decisión, una persona mencionada no es necesariamente responsable y una afirmación posterior solo sustituye a otra cuando la conversación respalda ese cambio. Los atributos ausentes son \texttt{null}; se prohíbe inventar información.}

\sectionbar{2. POR QUÉ FALLA EL PROMPT DIRECTO}

Las reuniones reales son desordenadas: las personas se interrumpen, cambian de tema y de opinión, y muchas veces dejan los acuerdos implícitos. Un modelo pequeño puede producir un resumen general, pero un prompt directo no reconstruye de forma confiable el estado final de cada decisión y tarea.

\textbf{Mecanismos de error esperados}
\begin{itemize}
  \item propuestas confundidas con decisiones finales;
  \item personas mencionadas asignadas como responsables de tareas;
  \item decisiones, plazos o tareas modificadas que quedan obsoletas;
  \item condiciones y temas pendientes omitidos;
  \item acuerdos implícitos ignorados o exagerados;
  \item detalles sin respaldo inventados para completar el acta.
\end{itemize}

\sectionbar{3. ALCANCE E HIPÓTESIS DEL PROYECTO}

\textbf{Alcance inicial:} analizar transcripciones en texto. \textbf{Extensión futura:} aceptar un archivo MP3, transcribirlo mediante una herramienta externa y enviar la transcripción resultante al mismo sistema de análisis.

\textit{Separar la extracción de información, la resolución temporal y la verificación de evidencia producirá actas finales más confiables que un prompt directo con el mismo modelo pequeño.}

\end{minipage}
\hfill
\begin{minipage}[t]{0.349\textwidth}
\vspace{0pt}
\raggedright
\fontsize{7.7}{8.25}\selectfont
\sectionbar{4. LA PRUEBA Y SU RESULTADO}

\textbf{Qué pidió el prompt.} Convertir 69 intervenciones en solo JSON válido; separar decisiones finales, sustituidas y rechazadas; extraer tareas con responsable, plazo, condición y estado; resolver fechas relativas; y citar evidencia textual exacta sin inventar datos. La pauta no se entregó al modelo.

{\fontsize{6.35}{6.9}\selectfont
\setlength{\tabcolsep}{2.2pt}
\renewcommand{\arraystretch}{1.10}
\renewcommand{\tabularxcolumn}[1]{m{#1}}
\begin{tabularx}{\linewidth}{>{\bfseries\raggedright\arraybackslash}m{0.18\linewidth}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X}
\toprule
Criterio & Ministral 3B & Qwen 3.5 4B & Phi-4 Mini \\
\midrule
Salida final & JSON válido; no confiable & JSON truncado e inválido & JSON válido; baja cobertura \\
\midrule
Historial apertura & 0/2 estados obsoletos & 2/2 estados obsoletos & 0/2; dejó lunes como final \\
\midrule
Decisiones clave & Omitió soporte solo por correo & Recuperó correo; rechazó WhatsApp & Recuperó SMTP; omitió WhatsApp \\
\midrule
Tareas & Escribió 6/7; mezcló 2 & Escribió 7; al menos 3 mal & Reconoció 1/7; agregó 2 falsas \\
\midrule
Plazos & Cambió 13:00 por 01:00 & Al menos 4 fechas erróneas & Perdió fecha final; usó 01:00/04:00 \\
\midrule
Enlaces de evidencia & Al menos 5 incorrectos & Al menos 6 incorrectos & Al menos 9 no concluyentes \\
\midrule
Tiempo & 22m06s & 16m08s & \textbf{7m58s} \\
\midrule
Veredicto & \textbf{\color{alert}NO APROBÓ} & \textbf{\color{alert}NO APROBÓ} & \textbf{\color{alert}NO APROBÓ} \\
\bottomrule
\end{tabularx}
}

\vspace{1pt}
\callout{\textbf{Por qué no funcionó.} Ministral omitió revisiones; Qwen siguió mejor los cambios, pero agotó 3.000 tokens; Phi terminó más rápido y con JSON válido, pero perdió la fecha final y reconoció solo 1/7 tareas. \textbf{Ninguno produjo el acta verificable solicitada.}}

\sectionbar{5. TRES CANDIDATOS DE PESOS ABIERTOS ($<8$B)}

{\fontsize{7.2}{7.8}\selectfont
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\renewcommand{\tabularxcolumn}[1]{m{#1}}
\begin{tabularx}{\linewidth}{>{\bfseries\raggedright\arraybackslash}m{0.22\linewidth}>{\raggedright\arraybackslash}m{0.12\linewidth}>{\raggedright\arraybackslash}X}
\toprule
Modelo & Parám. & Justificación basada en benchmarks y tarea \\
\midrule
\href{https://artificialanalysis.ai/models/ministral-3-3b}{Ministral 3} & Clase 3B & AA 7, contexto 256K, pesos abiertos, Apache 2.0 y JSON nativo. El piloto lo sostiene como línea base de extracción. \\
\midrule
\href{https://artificialanalysis.ai/models/qwen3-5-4b}{Qwen 3.5 4B} & 4.7B & AA 20 (razonamiento, estimado) y 16 (sin razonamiento), contexto 262K y Apache 2.0. Recuperó 2/2 fechas obsoletas: candidato restringido para resolución temporal pese al corte y errores. \\
\midrule
\href{https://artificialanalysis.ai/models/phi-4-mini}{Phi-4 Mini} & 3.8B & AA 6 (estimado), contexto 128K, pesos abiertos y MIT. Su piloto válido y conciso fue el más rápido, pero solo reconoció bien 1/7 tareas. \\
\bottomrule
\end{tabularx}
}

\callout{\textbf{Selección.} \href{https://artificialanalysis.ai/models/}{Artificial Analysis} aporta el marco común; los tres pilotos locales ya entregan evidencia de la tarea. La selección usa F1, precisión de evidencia, afirmaciones sin respaldo, validez JSON y tiempo.}

\sectionbar{6. SISTEMA PROPUESTO}

\smallcapslabel{Preprocesamiento por código} $\rightarrow$
\smallcapslabel{extracción con Ministral} $\rightarrow$
\smallcapslabel{resolución temporal con Qwen} $\rightarrow$
\smallcapslabel{verificación con Phi} $\rightarrow$
\smallcapslabel{renderizador JSON determinista}

Las etapas intercambian JSON validado contra el esquema. Solo los registros verificados llegan al renderizador, evitando que un modelo final invente personas, fechas o decisiones.

\end{minipage}
\hfill
\begin{minipage}[t]{0.305\textwidth}
\vspace{0pt}
\raggedright
\sectionbar{7. PLAN DE EVALUACIÓN}

\textbf{Datos de referencia.} Dos integrantes anotan por separado transcripciones en español con interrupciones, plazos ausentes, tareas condicionales, referencias implícitas, rechazos y decisiones revisadas; los desacuerdos se adjudican.

\textbf{Comparaciones controladas}
\begin{enumerate}
  \item Mismo prompt directo para los tres modelos.
  \item Mismos roles; un modelo base a la vez.
  \item Sistema heterogéneo Ministral $\rightarrow$ Qwen $\rightarrow$ Phi.
  \item Ablaciones sin resolución temporal o verificación.
\end{enumerate}

\textbf{Controles.} Misma transcripción, esquema, cuantización Q4, presupuestos de contexto/salida y temperatura 0. Se guardan prompts, salidas crudas, tiempo y versión.

\textbf{Medidas principales}
\begin{itemize}
  \item F1 de decisiones finales y tareas acordadas;
  \item macro-F1 del estado final/rechazado/sustituido/pendiente;
  \item exactitud de responsable, plazo y condición;
  \item precisión de evidencia y afirmaciones sin respaldo;
  \item validez JSON, latencia y máximo uso de RAM/VRAM.
\end{itemize}

\sectionbar{8. FACTIBILIDAD DE EJECUCIÓN}

\begin{tabularx}{\linewidth}{>{\bfseries\raggedright\arraybackslash}p{0.29\linewidth}>{\raggedright\arraybackslash}X}
Hardware & Intel i5-9300H; 15.8 GB RAM; GTX 1050 3 GB \\
Entorno & Ollama 0.32.15--0.33.2; Windows \\
Corrida Ministral & Q4\_K\_M, 3.0 GB: 2,386 tokens en 22m06s (1.86 tok/s) \\
Corrida Qwen & Q4\_K\_M, 3.4 GB: 3,000 tokens en 16m08s (3.24 tok/s); 75/25 CPU/GPU \\
Corrida Phi & Q4\_K\_M, 2.5 GB: 1,211 tokens en 7m58s (2.93 tok/s); 65/35 CPU/GPU \\
Memoria & Qwen: aprox. 1.74 GB VRAM; Phi: aprox. 1.49 GB \\
Despliegue & CPU/GPU secuencial; bloques 4K--8K; Colab como respaldo \\
\end{tabularx}

Los tres modelos cargaron y generaron localmente. Phi fue el más rápido y conciso, pero tuvo la menor cobertura semántica.

\sectionbar{9. REPOSITORIO Y ESTADO ACTUAL}

\textbf{Repositorio:} \href{\repositoryurl}{\color{blue}\texttt{Repositorio del proyecto en GitHub}}

\textbf{Debe contener:} tarea/esquema, equipo, piloto y salida, auditoría, versiones y pasos de reproducción.

\textbf{Completado:} definición; pauta de 69 intervenciones; corridas controladas de los tres modelos; salidas, auditorías y evidencia de hardware.\par
\textbf{Siguiente:} ampliar la pauta; implementar resolución temporal y verificación de evidencia; probar cada modelo en su rol acotado.

\vfill
{\fontsize{6.15}{6.8}\selectfont\color{muted}
Fuentes públicas de modelos y benchmarks:
\href{https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512}{Mistral AI, Ministral 3 3B};
\href{https://huggingface.co/Qwen/Qwen3.5-4B}{Qwen, Qwen3.5-4B};
\href{https://huggingface.co/microsoft/Phi-4-mini-instruct}{Microsoft, Phi-4 Mini Instruct}.
Comparación independiente consultada el 28 de agosto de 2026: \href{https://artificialanalysis.ai/models/}{Artificial Analysis, Model Benchmarks}.
}

\end{minipage}

\end{document}
