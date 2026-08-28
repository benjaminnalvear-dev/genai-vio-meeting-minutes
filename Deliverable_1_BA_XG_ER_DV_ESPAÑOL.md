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
\setlength{\parskip}{1.3pt}
\setlist[itemize]{leftmargin=1.1em,itemsep=0.35pt,topsep=0.65pt,parsep=0pt}
\setlist[enumerate]{leftmargin=1.35em,itemsep=0.35pt,topsep=0.65pt,parsep=0pt}
\renewcommand{\arraystretch}{1.06}
\color{ink}

\newcommand{\sectionbar}[1]{%
  \vspace{1pt}%
  \colorbox{navy}{\parbox{\dimexpr\linewidth-2\fboxsep}{\color{white}\bfseries\sffamily #1}}%
  \vspace{1pt}%
}
\newcommand{\callout}[1]{%
  \colorbox{ice}{\parbox{\dimexpr\linewidth-2\fboxsep}{#1}}%
}
\newcommand{\smallcapslabel}[1]{{\color{blue}\bfseries\sffamily #1}}

\begin{document}
\sffamily
\fontsize{8.55}{9.3}\selectfont

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

\vspace{3pt}

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
\sectionbar{4. FALLA OBSERVADA DEL PROMPT DIRECTO}

\textbf{Prueba reproducible.} Una reunión sintética de estilo espontáneo, con 69 intervenciones, cuatro asistentes y tres personas solo mencionadas, se entregó a \texttt{ministral-3:3b}. El prompt directo exigió estados finales/sustituidos/rechazados, tareas, condiciones y evidencia exacta.

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.43\linewidth}X}
\toprule
Elemento auditado & Resultado observado \\
\midrule
Contexto 4K predeterminado & Entrada recortada; Markdown en vez de JSON \\
8K controlado + modo JSON & JSON válido; 22m06s; 1.86 tok/s \\
Estados sustituidos & 0 de 2 esperados \\
Ideas rechazadas & 0; omitió el rechazo de WhatsApp \\
Tareas & 6 de 7; mezcló dos responsabilidades \\
Responsable sin respaldo & Asignó a Paula pese al rechazo explícito \\
Plazo revisado & Incorrecto: 01:00 en vez de 13:00 \\
Evidencia no concluyente & Al menos 5 vínculos de campo \\
\bottomrule
\end{tabularx}

\vspace{1pt}
Ampliar el contexto y forzar JSON nativo corrigió el formato y recuperó la fecha final del piloto, pero no el estado completo de la reunión. El modelo aún mezcló temas, omitió revisiones y rechazos, asignó a una persona ausente y citó evidencia que contradecía sus propios campos.

\sectionbar{5. TRES CANDIDATOS DE PESOS ABIERTOS ($<8$B)}

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.22\linewidth}p{0.12\linewidth}X}
\toprule
Modelo & Parám. & Justificación basada en benchmarks y tarea \\
\midrule
Ministral 3 & 3.8B & JSON/extracción nativos y soporte de español. Resultados oficiales: MMLU multilingüe 65.2; WildBench 56.8. El piloto local revela las debilidades que debe corregir el sistema. \\
Qwen 3.5 4B & 4B LM & Mejor candidato para resolver estados temporales: IFEval 89.8, LongBench v2 50.0 y MMMLU multilingüe 76.1; contexto nativo de 262K. \\
Phi-4 Mini & 3.8B & Candidato a verificador independiente: BigBench Hard 70.4 y MMLU multilingüe 49.3; soporte de español y contexto de 128K. \\
\bottomrule
\end{tabularx}

\callout{\textbf{Caso para bonificación.} Todos los candidatos tienen cerca de la mitad del límite de 8B. Se eligieron por capacidades complementarias de extracción, resolución multilingüe de contexto largo y verificación, no solo por su tamaño.}

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

\textbf{Datos de referencia.} Dos integrantes anotan independientemente transcripciones en español con interrupciones, plazos ausentes, tareas condicionales, referencias implícitas, propuestas rechazadas y decisiones revisadas más de una vez; los desacuerdos se adjudican.

\textbf{Comparaciones controladas}
\begin{enumerate}
  \item Mismo prompt directo para los tres modelos.
  \item Mismos roles de agentes con un modelo base a la vez.
  \item Sistema heterogéneo Ministral $\rightarrow$ Qwen $\rightarrow$ Phi.
  \item Ablaciones sin resolución temporal o verificación.
\end{enumerate}

\textbf{Controles.} Misma transcripción, esquema, cuantización clase Q4, presupuestos de contexto/salida y temperatura 0. Guardar prompts, salidas sin procesar, tiempo de ejecución y versión del modelo.

\textbf{Medidas principales}
\begin{itemize}
  \item F1 de decisiones finales y tareas acordadas;
  \item macro-F1 del estado final/rechazado/sustituido/pendiente;
  \item exactitud de responsable, plazo y condición;
  \item precisión de evidencia y tasa de afirmaciones sin respaldo;
  \item validez JSON, latencia y máximo uso de RAM/VRAM.
\end{itemize}

\sectionbar{8. FACTIBILIDAD DE EJECUCIÓN}

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.29\linewidth}X}
Hardware & Intel i5-9300H; 15.8 GB RAM; GTX 1050 3 GB \\
Entorno & Ollama 0.32.15 en Windows \\
Ejecución medida & Ministral 3 Q4\_K\_M, 3.0 GB: prueba 8K generó 2,386 tokens en 22m06s (1.86 tok/s) \\
Memoria & Los pesos de 4 bits ocupan aprox. 1.9--2.5 GB/modelo; cada uno cabe por separado en 15.8 GB RAM más la sobrecarga \\
Despliegue & CPU/GPU híbrido secuencial; bloques de 4K--8K; Colab gratuito como respaldo \\
\end{tabularx}

La carga secuencial evita mantener tres modelos simultáneamente en memoria. La ejecución medida de Ministral valida la inferencia local; los otros dos aún deben cronometrarse bajo los mismos controles.

\sectionbar{9. REPOSITORIO Y ESTADO ACTUAL}

\textbf{Repositorio:} \href{\repositoryurl}{\color{blue}\texttt{github.com/benjaminnalvear-dev/genai-vio-meeting-minutes}}

\textbf{Debe contener:} tarea/esquema, equipo, prompt y salida del piloto, auditoría, versiones de modelos/entorno y pasos de reproducción.

\textbf{Completado:} definición; prueba reproducible de 69 intervenciones; corridas Ministral 4K/8K; auditoría de hardware y salida.\par
\textbf{Siguiente:} anotar más datos de referencia; ejecutar Qwen y Phi; implementar resolución temporal y verificación de evidencia.

\vfill
{\fontsize{6.15}{6.8}\selectfont\color{muted}
Fuentes públicas de modelos y benchmarks:
\href{https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512}{Mistral AI, Ministral 3 3B};
\href{https://huggingface.co/Qwen/Qwen3.5-4B}{Qwen, Qwen3.5-4B};
\href{https://huggingface.co/microsoft/Phi-4-mini-instruct}{Microsoft, Phi-4 Mini Instruct}.
}

\end{minipage}

\end{document}
