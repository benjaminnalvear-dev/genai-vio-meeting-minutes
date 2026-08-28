% SYNCHRONIZED PAIR: Keep this file aligned with Deliverable_1_BA_XG_ER_DV_ESPAÑOL.md.
% Apply every future content or layout change to both language versions.
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
    {\fontsize{15.5}{17}\selectfont\bfseries Reliable Meeting Minutes from Noisy Transcripts}\hfill
    {\normalsize Deliverable 1}\par
    \vspace{1pt}
    {\fontsize{6.8}{7.4}\selectfont Benjamin Alvear \textbullet{} Eduardo Ruiz \textbullet{} Xavier Godoy \textbullet{} Damian Vera
    \hfill Generative Artificial Intelligence (580694) \textbullet{} Due August 31, 2026}
  }%
}

\vspace{2pt}

\begin{minipage}[t]{0.318\textwidth}
\vspace{0pt}
\raggedright
\sectionbar{1. TASK SPECIFICATION}

\textbf{Main objective.} Build a system that automatically turns a Spanish meeting transcript into clear, trustworthy, and structured minutes. The system must recover what was finally agreed, not merely summarize what was discussed.

\textbf{Initial input.} A text transcript with utterance IDs, speaker labels, timestamps, and meeting date.

\textbf{Required output}
\begin{itemize}
  \item final decisions, including decisions revised during the meeting;
  \item agreed tasks with assignee, deadline, conditions, and status;
  \item rejected, superseded, and unresolved ideas;
  \item pending topics and review alerts;
  \item an exact supporting excerpt and utterance ID for every decision or task.
\end{itemize}

\callout{\textbf{What counts as correct.} The minutes must reflect the meeting's final state and every decision or task must be entailed by its cited excerpt. A proposal is not a decision, a mentioned person is not necessarily an assignee, and a later statement only supersedes an earlier one when the conversation supports that change. Missing attributes are \texttt{null}; invented information is forbidden.}

\sectionbar{2. WHY DIRECT PROMPTING FAILS}

Real meetings are disorderly: people interrupt one another, switch topics, change their minds, and often leave agreements implicit. A small model can produce a general summary, but direct prompting does not reliably reconstruct the final state of each decision and task.

\textbf{Expected error mechanisms}
\begin{itemize}
  \item proposals confused with final decisions;
  \item people mentioned in discussion assigned as task owners;
  \item revised decisions, deadlines, or tasks left outdated;
  \item conditions and pending issues omitted;
  \item implicit agreements missed or overstated;
  \item unsupported details invented to make the minutes sound complete.
\end{itemize}

\sectionbar{3. SCOPE AND PROJECT HYPOTHESIS}

\textbf{Initial scope:} analyze text transcripts. \textbf{Future extension:} accept an MP3 file, transcribe it with an external speech-to-text tool, and pass the resulting transcript to the same analysis system.

\textit{Separating information extraction, temporal resolution, and evidence verification will produce more reliable final minutes than direct prompting with the same small model.}

\end{minipage}
\hfill
\begin{minipage}[t]{0.349\textwidth}
\vspace{0pt}
\raggedright
\fontsize{7.7}{8.25}\selectfont
\sectionbar{4. THE TEST AND ITS RESULT}

\textbf{What the prompt required.} Convert 69 utterances into valid JSON only; separate final, superseded, and rejected decisions; extract tasks with assignee, deadline, condition, and status; resolve relative dates; and cite exact textual evidence without inventing data. The reference annotation was withheld.

{\fontsize{7.2}{7.8}\selectfont
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.18}
\renewcommand{\tabularxcolumn}[1]{m{#1}}
\begin{tabularx}{\linewidth}{>{\bfseries\raggedright\arraybackslash}m{0.24\linewidth}>{\raggedright\arraybackslash}m{0.31\linewidth}>{\raggedright\arraybackslash}X}
\toprule
Criterion & Ministral 3B & Qwen 3.5 4B \\
\midrule
Final output & Complete JSON, but unreliable & Truncated, invalid JSON \\
\midrule
Launch dates & Missed discarded Friday and Monday & Recorded Friday $\rightarrow$ Monday $\rightarrow$ final Wednesday \\
\midrule
Support channel & Missed the email-only decision & Recorded email; WhatsApp discarded \\
\midrule
Tasks & 6 of 7; merged 2 & Wrote 7; at least 3 were wrong \\
\midrule
Deadlines & Changed 13:00 to 01:00 & At least 4 wrong dates \\
\midrule
Supporting quotes & At least 5 incorrect & At least 6 incorrect \\
\midrule
Time & 22m06s & 16m08s; about 6m faster \\
\midrule
Verdict & \textbf{\color{alert}DID NOT PASS} & \textbf{\color{alert}DID NOT PASS} \\
\bottomrule
\end{tabularx}
}

\vspace{1pt}
\callout{\textbf{Why it failed.} Ministral met the format but omitted revisions and cited quotes that did not support its fields. Qwen tracked changes better, but exhausted 3,000 tokens, left invalid JSON, invented tasks, and normalized dates incorrectly. \textbf{Neither produced the requested verifiable minutes.}}

\sectionbar{5. THREE OPEN-WEIGHT CANDIDATES ($<8$B)}

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.22\linewidth}p{0.12\linewidth}X}
\toprule
Model & Params. & Benchmark- and task-grounded rationale \\
\midrule
\href{https://artificialanalysis.ai/models/ministral-3-3b}{Ministral 3} & 3B class & AA 7, 256K context, open weights, Apache 2.0, and native JSON. The pilot supports it as the extraction baseline. \\
\href{https://artificialanalysis.ai/models/qwen3-5-4b}{Qwen 3.5 4B} & 4.7B & AA 20 (reasoning, estimated) and 16 (non-reasoning), 262K context, and Apache 2.0. It recovered 2/2 obsolete dates: a constrained temporal candidate despite truncation and errors. \\
\href{https://artificialanalysis.ai/models/phi-4-mini}{Phi-4 Mini} & 3.8B & AA 6 (estimated), 128K context, open weights, and MIT. A distinct architecture for evidence verification. \\
\bottomrule
\end{tabularx}

\callout{\textbf{Selection.} \href{https://artificialanalysis.ai/models/}{Artificial Analysis} supplies the common framework and local pilots provide task evidence. The final choice will use F1, evidence precision, unsupported claims, JSON validity, and runtime.}

\sectionbar{6. PROPOSED SYSTEM}

\smallcapslabel{Code preprocessing} $\rightarrow$
\smallcapslabel{Ministral extraction} $\rightarrow$
\smallcapslabel{Qwen temporal resolver} $\rightarrow$
\smallcapslabel{Phi verification} $\rightarrow$
\smallcapslabel{deterministic JSON renderer}

Stages exchange schema-validated JSON. Only verified records reach the renderer, preventing a final prose model from inventing people, dates, or decisions.

\end{minipage}
\hfill
\begin{minipage}[t]{0.305\textwidth}
\vspace{0pt}
\raggedright
\sectionbar{7. EVALUATION PLAN}

\textbf{Gold data.} Two team members independently annotate Spanish transcripts containing interruptions, absent deadlines, conditional tasks, implicit references, rejected proposals, and decisions revised more than once; disagreements are adjudicated.

\textbf{Controlled comparisons}
\begin{enumerate}
  \item Same direct prompt for all three models.
  \item Same agent roles with one backbone at a time.
  \item Heterogeneous Ministral $\rightarrow$ Qwen $\rightarrow$ Phi system.
  \item Ablations without temporal resolution or verification.
\end{enumerate}

\textbf{Controls.} Same transcript, schema, Q4-class quantization, context/output budgets, and temperature 0. Save prompts, raw outputs, runtime, and model version.

\textbf{Primary measures}
\begin{itemize}
  \item F1 for final decisions and agreed tasks;
  \item macro-F1 for final/rejected/superseded/pending state;
  \item assignee, deadline, and condition accuracy;
  \item evidence precision and unsupported-claim rate;
  \item JSON validity, latency, and peak RAM/VRAM.
\end{itemize}

\sectionbar{8. EXECUTION FEASIBILITY}

\begin{tabularx}{\linewidth}{>{\bfseries\raggedright\arraybackslash}p{0.29\linewidth}>{\raggedright\arraybackslash}X}
Hardware & Intel i5-9300H; 15.8 GB RAM; GTX 1050 3 GB \\
Runtime & Ollama 0.32.15 (Ministral) / 0.33.1 (Qwen), Windows \\
Ministral run & Q4\_K\_M, 3.0 GB: 2,386 tokens in 22m06s (1.86 tok/s) \\
Qwen run & Q4\_K\_M, 3.4 GB: 3,000 tokens in 16m08s (3.24 tok/s); 75/25 CPU/GPU \\
Memory check & Qwen used about 1.74 GB VRAM and under 6 GB private memory in observed samples \\
Deployment & Sequential CPU/GPU hybrid; 4K--8K chunks; free Colab GPU fallback \\
\end{tabularx}

Both tested backbones loaded and generated locally; sequential loading avoids holding them simultaneously. Phi remains to be timed under the same controls.

\sectionbar{9. REPOSITORY \& CURRENT STATE}

\textbf{Repository:} \href{\repositoryurl}{\color{blue}\texttt{Project repository on GitHub}}

\textbf{Must contain:} task/schema, team, pilot prompt and output, audit, model/runtime versions, and reproducibility steps.

\textbf{Completed:} task definition; 69-utterance gold test; controlled Ministral and Qwen runs; raw outputs, audits, and hardware evidence.\par
\textbf{Next:} run Phi; expand gold data; implement temporal resolution and evidence verification.

\vfill
{\fontsize{6.15}{6.8}\selectfont\color{muted}
Public benchmark/model sources:
\href{https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512}{Mistral AI, Ministral 3 3B};
\href{https://huggingface.co/Qwen/Qwen3.5-4B}{Qwen, Qwen3.5-4B};
\href{https://huggingface.co/microsoft/Phi-4-mini-instruct}{Microsoft, Phi-4 Mini Instruct}.
Independent comparison accessed August 28, 2026: \href{https://artificialanalysis.ai/models/}{Artificial Analysis, Model Benchmarks}.
}

\end{minipage}

\end{document}
