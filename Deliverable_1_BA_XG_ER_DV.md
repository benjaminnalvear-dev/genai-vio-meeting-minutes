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
    {\fontsize{17}{18.5}\selectfont\bfseries Reliable Meeting Minutes from Noisy Transcripts}\hfill
    {\normalsize Deliverable 1}\par
    \vspace{1pt}
    {\fontsize{7.4}{8}\selectfont Benjamin Alvear \textbullet{} Eduardo Ruiz \textbullet{} Xavier Godoy \textbullet{} Damian Vera
    \hfill Generative Artificial Intelligence (580694) \textbullet{} Due August 31, 2026}
  }%
}

\vspace{3pt}

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
\sectionbar{4. OBSERVED DIRECT-PROMPT FAILURE}

\textbf{Reproducible test.} A synthetic but unscripted-style meeting with 69 utterances, four attendees, and three mentioned non-participants was given to \texttt{ministral-3:3b}. The direct prompt required final/superseded/rejected states, tasks, conditions, and exact evidence.

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.43\linewidth}X}
\toprule
Audit item & Observed result \\
\midrule
Default 4K context & Input truncated; Markdown instead of JSON \\
Controlled 8K + JSON mode & Valid JSON; 22m06s; 1.86 tok/s \\
Superseded states & 0 of 2 expected \\
Rejected ideas & 0; WhatsApp rejection omitted \\
Action items & 6 of 7; two responsibilities merged \\
Unsupported assignee & Paula assigned despite explicit rejection \\
Revised deadline & Wrong: 01:00 instead of 13:00 \\
Non-entailing evidence & At least 5 field links \\
\bottomrule
\end{tabularx}

\vspace{1pt}
Expanding context and enforcing native JSON fixed the output format and recovered the final launch date, but not the complete meeting state. The model still merged topics, missed revisions/rejections, assigned an absent person, and cited evidence that contradicted its own fields.

\sectionbar{5. THREE OPEN-WEIGHT CANDIDATES ($<8$B)}

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.22\linewidth}p{0.12\linewidth}X}
\toprule
Model & Params. & Benchmark- and task-grounded rationale \\
\midrule
Ministral 3 & 3.8B & Native JSON/data extraction and Spanish support. Official results: Multilingual MMLU 65.2; WildBench 56.8. Local pilot exposes the exact weaknesses the pipeline must correct. \\
Qwen 3.5 4B & 4B LM & Best temporal resolver candidate: IFEval 89.8, LongBench v2 50.0, and multilingual MMMLU 76.1; 262K native context. \\
Phi-4 Mini & 3.8B & Independent verifier candidate: BigBench Hard 70.4 and Multilingual MMLU 49.3; Spanish support and 128K context. \\
\bottomrule
\end{tabularx}

\callout{\textbf{Bonus case.} All candidates are roughly half the 8B ceiling. They were chosen for complementary extraction, long-context multilingual resolution, and verification capabilities---not for size alone.}

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

\begin{tabularx}{\linewidth}{>{\bfseries}p{0.29\linewidth}X}
Hardware & Intel i5-9300H; 15.8 GB RAM; GTX 1050 3 GB \\
Runtime & Ollama 0.32.15 on Windows \\
Measured run & Ministral 3 Q4\_K\_M, 3.0 GB: 8K test generated 2,386 tokens in 22m06s (1.86 tok/s) \\
Memory check & Raw 4-bit weights are about 1.9--2.5 GB/model; each fits individually in 15.8 GB RAM plus runtime overhead \\
Deployment & Sequential CPU/GPU hybrid; 4K--8K chunks; free Colab GPU fallback \\
\end{tabularx}

Sequential loading avoids holding three backbones in memory simultaneously. The measured Ministral run validates the local inference path; the other two remain to be timed under the same controls.

\sectionbar{9. REPOSITORY \& CURRENT STATE}

\textbf{Repository:} \href{\repositoryurl}{\color{blue}\texttt{github.com/benjaminnalvear-dev/genai-vio-meeting-minutes}}

\textbf{Must contain:} task/schema, team, pilot prompt and output, audit, model/runtime versions, and reproducibility steps.

\textbf{Completed:} task definition; reproducible 69-utterance test; controlled 4K/8K Ministral runs; hardware and output audit.\par
\textbf{Next:} annotate more gold data; run Qwen and Phi; implement temporal resolution and evidence verification.

\vfill
{\fontsize{6.15}{6.8}\selectfont\color{muted}
Public benchmark/model sources:
\href{https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512}{Mistral AI, Ministral 3 3B};
\href{https://huggingface.co/Qwen/Qwen3.5-4B}{Qwen, Qwen3.5-4B};
\href{https://huggingface.co/microsoft/Phi-4-mini-instruct}{Microsoft, Phi-4 Mini Instruct}.
}

\end{minipage}

\end{document}
