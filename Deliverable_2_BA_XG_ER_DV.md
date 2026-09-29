\documentclass[10pt]{article}
\usepackage[letterpaper,portrait,margin=0.34in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{tabularx,booktabs,array}
\usepackage{enumitem}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning}
\usepackage[hidelinks]{hyperref}

\definecolor{navy}{HTML}{12324A}
\definecolor{blue}{HTML}{1F6E8C}
\definecolor{ice}{HTML}{EAF3F6}
\definecolor{ink}{HTML}{17232B}
\definecolor{muted}{HTML}{52616B}
\definecolor{alert}{HTML}{A3382F}
\newcommand{\repo}{https://github.com/benjaminnalvear-dev/genai-vio-meeting-minutes}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{1.0pt}
\setlist[itemize]{leftmargin=1.05em,itemsep=0.25pt,topsep=0.4pt,parsep=0pt}
\renewcommand{\arraystretch}{1.06}
\color{ink}
\newcommand{\sectionbar}[1]{\vspace{5.5pt}{\bfseries\sffamily #1}\par\vspace{1.2pt}}
\newcommand{\callout}[1]{#1}

\begin{document}
\sffamily
\fontsize{8.65}{9.45}\selectfont

{\fontsize{14.2}{15.5}\selectfont\bfseries Actas verificables desde transcripciones ruidosas}\hfill
{\normalsize\bfseries Entregable 2}\par
\vspace{1pt}
{\fontsize{7.5}{8.0}\selectfont Benjamin Alvear \textbullet{} Xavier Godoy \textbullet{} Eduardo Ruiz \textbullet{} Damian Vera
\hfill Inteligencia Artificial Generativa (580694) \textbullet{} 30-sep-2026}

\vspace{2pt}
\begin{center}
\begin{tikzpicture}[
  node distance=2.8mm,
  box/.style={draw=blue,rounded corners=1.5pt,fill=ice,align=center,minimum height=7.5mm,text width=2.42cm,font=\fontsize{7.0}{7.5}\selectfont},
  arrow/.style={-{Latex[length=1.6mm]},very thick,color=blue}
]
\node[box] (in) {Transcripci\'on completa\\fecha, participantes, IDs};
\node[box,right=of in] (draft) {Ministral 3 3B\\borrador con JSON restringido};
\node[box,right=of draft] (tools) {Herramientas deterministas\\evidencia, fechas, revisiones};
\node[box,right=of tools] (rev) {Segunda pasada restringida\\correcci\'on del borrador};
\node[box,right=of rev] (out) {Acta trazable\\renderizado determinista};
\draw[arrow] (in)--(draft); \draw[arrow] (draft)--(tools); \draw[arrow] (tools)--(rev); \draw[arrow] (rev)--(out);
\end{tikzpicture}
\end{center}
\vspace{-2pt}

\begin{minipage}[t]{0.492\textwidth}
\vspace{0pt}
\sectionbar{1. TAREA, MODELO E INTERVENCI\'ON}

\textbf{Tarea de D1.} Convertir una reuni\'on ruidosa en un acta JSON con \texttt{meeting}, decisiones finales, sustituidas y rechazadas, tareas con responsable, plazo y condici\'on, \texttt{pending\_issues}, \texttt{review\_alerts} y citas literales con ID. La pauta penaliza propuestas tratadas como acuerdos, revisiones perdidas, tareas asignadas a ausentes, plazos inventados y citas que no respaldan el campo.

\textbf{Modelo elegido.} \texttt{ministral-3:3b-instruct-2512-q4\_K\_M}, digest \texttt{f04aa1c738f6}. Es el candidato m\'as peque\~no: clase 3B, frente a 3.8B de Phi-4 Mini y 4.7B de Qwen 3.5 4B. Adem\'as, corre localmente y en D1 recuper\'o 6/7 tareas. Qwen agot\'o 3,000 tokens y entreg\'o JSON inv\'alido; Phi recuper\'o correctamente 1/7 tareas. La cuantizaci\'on reduce memoria y mantiene la cantidad de par\'ametros.

\textbf{Intervenci\'on.} \emph{Constrained decoding + tool use determinista en dos pasadas}. El esquema fija claves, tipos, estados e IDs de evidencia permitidos. Python recupera cada cita con sus intervenciones vecinas, resuelve fechas desde el d\'ia de la reuni\'on, busca indicios de reemplazo y valida IDs y formatos. Luego Ministral revisa el borrador con esos informes. Los pesos permanecen intactos y Python coordina todas las herramientas.

\callout{\textbf{Qu\'e corrige cada pieza.} El esquema evita JSON, estados y campos inv\'alidos. El prompt y el informe de herramientas advierten sobre responsables no presentes; todav\'ia no existe un bloqueo determinista. El resolutor de fechas atiende errores como 13:00 convertido en 01:00. La revisi\'on de IDs y contexto reduce citas inventadas y ayuda a seguir decisiones reemplazadas.}

\sectionbar{2. EJECUCI\'ON Y DISE\~NO EXPERIMENTAL}

Ejecutamos el sistema completo en Google Colab con una Tesla T4 de 15 GB, el hardware de respaldo declarado en D1. Usamos temperatura 0, seed 42 y contexto de 12,288 tokens. El notebook instala el entorno, descarga el modelo, procesa las reuniones, calcula las m\'etricas y exporta respuestas crudas, conteos de tokens y JSON.

\textbf{Evaluaci\'on:} 10 reuniones de test, 347 intervenciones, 56 decisiones y 53 tareas de referencia. Las tres configuraciones usan las mismas entradas, el mismo modelo y el mismo criterio de emparejamiento por contenido e ID. La pauta se usa despu\'es de la inferencia. Comparamos prompt directo, JSON restringido y la intervenci\'on completa.

{\fontsize{7.0}{7.55}\selectfont
\setlength{\tabcolsep}{2.2pt}
\begin{tabularx}{\linewidth}{>{\raggedright\arraybackslash}Xrrrr}
\toprule
Configuraci\'on & JSON & F1 dec. & F1 tareas & Tiempo \\
\midrule
Prompt directo & 0/10 & 0.477 & 0.667 & 303.8 s \\
JSON restringido & 10/10 & 0.559 & 0.709 & 197.9 s \\
\textbf{JSON + herramientas} & \textbf{10/10} & \textbf{0.667} & \textbf{0.716} & 288.0 s \\
\bottomrule
\end{tabularx}}

El F1 de decisiones subi\'o 0.190 (+39.8\%) y el de tareas 0.049 (+7.3\%). La intervenci\'on encontr\'o 35/56 decisiones y 39/53 tareas; el baseline encontr\'o 21/56 y 32/53. Tambi\'en gener\'o 105 IDs existentes de 105, frente a 70/75. Esta comprobaci\'on cubre la existencia del ID; el respaldo sem\'antico requiere revisi\'on manual.

\sectionbar{3. PRUEBA CON EL FORMATO COMPLETO DE D1}

Tambi\'en procesamos la reuni\'on can\'onica de D1, de 69 intervenciones, con el evaluador completo. Tool use por bloques obtuvo 5/9 decisiones, 1/2 estados obsoletos, 7/7 tareas, 3/4 pendientes, 7/7 responsables y 5/7 plazos. El baseline obtuvo 3/9, 0/2, 6/7, 2/4, 6/6 y 3/6. Las asignaciones a ausentes bajaron de 2 a 0 y las citas inexactas de 3 a 0. El tiempo subi\'o de 44.62 a 119.23 s; la precisi\'on de decisiones baj\'o de 0.75 a 0.25 y la de tareas de 1.0 a 0.368.

\textbf{Alcance y continuidad.} El conjunto de 10 reuniones usa una pauta reducida para medir decisiones y tareas; no redefine la salida de D1. El formato completo de D1 se evalu\'o por separado sobre la reuni\'on can\'onica, incluyendo pendientes, alertas y citas literales. Por eso, los F1 agregados se limitan a decisiones y tareas y la prueba completa se reporta como evidencia complementaria, no como otra corrida del mismo pipeline.

\end{minipage}
\hfill
\begin{minipage}[t]{0.492\textwidth}
\vspace{0pt}
\sectionbar{4. ALTERNATIVAS Y ABLACIONES}

{\fontsize{7.0}{7.55}\selectfont
\setlength{\tabcolsep}{2.0pt}
\begin{tabularx}{\linewidth}{>{\raggedright\arraybackslash}p{0.25\linewidth}>{\raggedright\arraybackslash}X}
\toprule
Alternativa & Resultado observado \\
\midrule
Descomposici\'on de prompt & En 10 reuniones, v3 subi\'o el recall de decisiones de 54.7\% a 65.4\%. Los responsables correctos bajaron de 35 a 27 y la latencia se duplic\'o. \\
JSON restringido & Logr\'o 10/10 esquemas v\'alidos y F1 de 0.559/0.709. Persistieron errores de estado y fecha. \\
Tool use por bloques (S2) & En D1 completo recuper\'o 7/7 tareas y 5/9 decisiones. Los fragmentos adicionales dejaron precisiones de 0.368/0.250. \\
S2 + RAG (S3) & Recuper\'o 6/9 decisiones y 7/7 tareas, con precisiones de 0.240/0.438. El retrieval l\'exico agreg\'o resultados espurios. \\
RAG + verificador (S4) & Us\'o 85 llamadas y 127.17 s. La mejora fue marginal y perdi\'o pendientes correctos. \\
Todo el pasado & Recuper\'o 2/2 estados obsoletos. Tard\'o 155.48 s y obtuvo 0.333 de precisi\'on en tareas. \\
\bottomrule
\end{tabularx}}

\textbf{Decisi\'on.} Elegimos JSON restringido con herramientas en dos pasadas porque obtuvo los mejores F1 del conjunto de 10 y gener\'o 10/10 esquemas v\'alidos. RAG y el verificador aumentaron el costo y aportaron poco. Su uso en reuniones mayores a 8K queda pendiente de validaci\'on.

\sectionbar{5. CASO DE FALLA REAL: M01}

M01 es la primera reuni\'on del conjunto seg\'un el orden de los archivos. El baseline tard\'o 107.16 s y produjo un esquema inv\'alido, con 7 decisiones y 4 tareas. La intervenci\'on tard\'o 26.89 s, entreg\'o un esquema v\'alido, con 6 decisiones y 5 tareas, y us\'o IDs existentes. La salida todav\'ia present\'o estos errores:
\begin{itemize}
  \item fusion\'o dos fechas obsoletas del lunes y clasific\'o una como \texttt{rejected} en vez de \texttt{superseded};
  \item marc\'o tareas acordadas como \texttt{pending}, fusion\'o preparar/enviar el correo y omiti\'o como tareas separadas presentar la demo y revisar el borrador;
  \item convirti\'o ``antes de las seis'' en 17:00 al mezclarlo con la hora de revisi\'on;
  \item invent\'o 2026-09-23 como plazo para definir el escenario.
\end{itemize}
\callout{\textbf{Por qu\'e falla.} Las herramientas comprueban sintaxis e IDs. La relaci\'on sem\'antica entre una cita y cada campo queda a cargo del modelo. Al leer intervenciones vecinas, Ministral mezcl\'o la hora de revisi\'on con la de env\'io. La segunda pasada tambi\'en hered\'o omisiones del borrador y aplic\'o estados de decisi\'on a tareas.}

\sectionbar{6. LIMITACIONES}

\begin{itemize}
  \item La mejora se concentra en formato y cobertura. Del baseline a la intervenci\'on, la exactitud de estado pas\'o de 0.528 a 0.500; responsable, de 0.969 a 0.923; plazo, de 0.406 a 0.308; y cita exacta, de 0.849 a 0.824.
  \item Las 10 reuniones son sint\'eticas. El emparejamiento es autom\'atico y aproximado, y el tama\~no de la muestra impide estimaciones estables. Nuevos ajustes requieren otro conjunto de test.
  \item Un ID v\'alido puede citar una intervenci\'on irrelevante. Falta una revisi\'on humana de la evidencia. La versi\'on de Ollama y el hardware tambi\'en afectan tiempos y salidas.
  \item RAG sobre contextos mayores a 8K pas\'o pruebas mec\'anicas. Todav\'ia falta evaluarlo con una reuni\'on larga anotada.
\end{itemize}

\sectionbar{7. REPRODUCIBILIDAD Y DEMOSTRACI\'ON}

\textbf{Repositorio:} \href{\repo}{\color{blue}\texttt{genai-vio-meeting-minutes}}. El \href{https://github.com/benjaminnalvear-dev/genai-vio-meeting-minutes/blob/main/GenAI\%20Constrained\%2BTool\%20use/README.md}{\color{blue}README D2} explica la reproducci\'on: abrir \texttt{Ministral\_Minutas\_Colab.ipynb}, elegir una T4, ejecutar las celdas, subir \texttt{Fine Tuning.zip} y descargar los resultados. Ese archivo contiene el dataset; los pesos permanecen intactos. El pipeline complementario de D1 se ejecuta con \texttt{experimentos/rag\_tool\_use/run.py}; sus 13 pruebas unitarias pasan.

\textbf{Video ($<3$ min):} mostrar el commit y ejecutar en T4 baseline e intervenci\'on sobre M01, la primera entrada del test, con \texttt{DEMO\_ONLY=True}. Comparar ambas salidas, mostrar brevemente el resultado completo del caso D1 y cerrar con la tabla de 10 reuniones y un error concreto. Entrada, progreso y archivos quedan visibles.

\end{minipage}

\end{document}
