import os

latex_content = r"""\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{longtable}
\usepackage{hyperref}

\geometry{a4paper, margin=1in}

\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}

\lstset{style=mystyle}

\begin{document}

% Title Page
\begin{titlepage}
    \centering
    \vspace*{1cm}
    
    {\Large \textbf{A REPORT}}\\[0.5cm]
    {\Large \textbf{ON}}\\[0.5cm]
    {\Large \textbf{A Multitude of Projects}}\\[1.5cm]
    
    {\Large \textbf{BY}}\\[1.0cm]
    
    \begin{tabular}{ccc}
    \textbf{Name of the student} & \textbf{ID No.} & \textbf{Discipline} \\
    Animesh Ratna & 2024A8PS0665P & B.E. in Electronics and Instrumentation \\
    \end{tabular}\\[2.0cm]
    
    Prepared in partial fulfillment of the\\[0.5cm]
    \textbf{Practice School - I}\\[0.5cm]
    \textbf{AT}\\[0.5cm]
    \textbf{NSE Indices, Mumbai}\\[1.5cm]
    
    A Practice School - I\\[0.5cm]
    Station of\\[0.5cm]
    \textbf{BIRLA INSTITUTE OF TECHNOLOGY \& SCIENCE, PILANI}\\[1.0cm]
    July 16, 2026
\end{titlepage}

% Second Page Info
\newpage
\begin{center}
    \textbf{BIRLA INSTITUTE OF TECHNOLOGY \& SCIENCE, PILANI}\\
    \textbf{Practice School Division}\\[1cm]
\end{center}

\noindent \textbf{Station:} NSE Indices \hfill \textbf{Centre:} Mumbai\\
\textbf{Duration:} PS-I \hfill \textbf{Date of start:} 25 May 2026\\
\textbf{Date of submission:} July 16, 2026\\[0.5cm]

\noindent \textbf{Title of the project:}\\
\begin{enumerate}
    \item Creation of a pipeline from BRSR Data to ESG Ratings
    \item Financial Climate Risk Modelling
    \item Analysis of Climate Policy Decisions between India and the EU
    \item Analysis of and Recommendations to the Colombo Stock Exchange
    \item Co-authoring The Sustainability Year Book 2026
    \item Developing a framework regarding rating green bonds
\end{enumerate}\vspace{0.5cm}

\noindent \textbf{ID No., Name and Discipline of the student:}\\
Animesh Ratna - 2024A8PS0665P - B.E. in Electronics and Instrumentation\\[0.5cm]

\noindent \textbf{Name(s) and Designation(s) of the expert(s):}\\
Vineeta Shetty, MD, NSRAL\\
Uday Bhoite, CCO, NSRAL\\[0.5cm]

\noindent \textbf{Name of the PS faculty member:}\\
Abhijeet Joshi\\[0.5cm]

\noindent \textbf{Key words:}\\
BRSR Automation, Financial Climate Risk Modelling, ESG Gap Analysis, NSE Indices, Regulatory Compliance, Climate Policy.\\[0.5cm]

\noindent \textbf{Project area(s):}\\
\begin{enumerate}
    \item Agent-Based Modelling (ABM)
    \item Financial Climate Risk Modelling
    \item Data Modelling \& Database Architecture
    \item Sustainability Reporting Automation (BRSR)
    \item Climate Policy Research \& Impact Analysis
    \item ESG Gap Analysis \& Framework Development
    \item Geospatial Network Analysis
    \item Green Bond Rating Methodologies
    \item Enterprise Data Pipelines
\end{enumerate}\vspace{0.5cm}

\noindent \textbf{Abstract:}\\
This comprehensive report documents work done at NSE Indices (NSRAL) across six critical workstreams focusing on automating the data collection process for BRSR reporting, developing Financial Climate Risk Models to ensure RBI compliance for small and medium banks, and macro-economic agent-based modelling. It details the technical architectures developed, including the BharatABM database schema and the FCRM Python package. Further contributions include an analysis of the 16th EU-India Summit's climate agenda, a comprehensive ESG gap analysis for the Colombo Stock Exchange, Green Bond methodologies, and contributions to The Sustainability Year Book 2026: Sectoral Outlook. The report mimics the depth of a full statutory compliance and systems audit, translating software engineering outcomes into granular financial risk and data management terminology.\\[1.5cm]

\noindent \begin{tabular}{@{}p{8cm} p{7cm}@{}}
Animesh Ratna & \\
\textbf{Signature of the student} & \textbf{Signature of the PS faculty member} \\
Date: 16-07-2026 & Date: \\
\end{tabular}

% Acknowledgements
\newpage
\chapter*{Acknowledgements}
We would like to thank the team at NSE Indices and NSRAL for the opportunity to work on live, high-impact projects during this placement. The guidance and operational context provided by our mentors were invaluable in shaping the work described in this report.

We are also grateful to the Practice School Division of BITS Pilani for facilitating this engagement.

I would like to express my sincere thanks to Prof. Abhijeet Joshi, our Faculty-in-Charge (FIC), for his constant guidance, encouragement, and support throughout the internship. I would also like to thank Vineeta Shetty (MD, NSRAL) and Uday Bhoite (CCO, NSRAL) for their time, feedback, and mentorship in shaping the direction of this work.

\vspace{2cm}
\noindent Signature of the student

% Table of Contents
\tableofcontents
\listoffigures
\listoftables

% Part I
\part{Introduction \& Methodology}

\chapter{Introduction \& Strategic Financing Overview}
\section{Context and Motivation}
In recent years, the global financial ecosystem has witnessed a paradigm shift towards sustainable investing and rigorous climate risk management. Regulatory bodies worldwide, including the Securities and Exchange Board of India (SEBI) and the Reserve Bank of India (RBI), are increasingly mandating comprehensive Environmental, Social, and Governance (ESG) disclosures. The transition from voluntary sustainability reporting to mandatory frameworks, such as the Business Responsibility and Sustainability Report (BRSR), underscores the critical need for robust, data-driven approaches to quantify both transition and physical climate risks. This evolving regulatory landscape presents unique challenges for financial institutions and corporations, particularly in standardizing data collection, ensuring auditability, and integrating complex macroeconomic climate scenarios into traditional risk management frameworks.

\section{NSE Indices and NSRAL: The Organisation}
NSE Indices Limited (formerly IISL), a subsidiary of the National Stock Exchange of India (NSE), provides a variety of indices and index-related services and products that serve as critical benchmarks for the Indian capital markets. NSE Sustainability Ratings \& Analytics Limited (NSRAL), a dedicated subsidiary, focuses exclusively on ESG analytics, sustainability reporting, and climate risk modelling. NSRAL plays a pivotal role in enabling financial institutions, asset managers, and listed companies to navigate the increasingly complex regulatory landscape surrounding climate risk and sustainability disclosures. By providing scalable technological solutions and deep research insights, NSRAL bridges the gap between regulatory mandates and actionable corporate strategy.

\section{The Six Major Workstreams}
This Practice School-I (PS-I) internship was designed to address these pressing industry challenges through a multidisciplinary approach encompassing software automation, macroeconomic modelling, and strategic policy research. The internship comprised six major workstreams:
\begin{enumerate}
    \item \textbf{Creation of a pipeline from BRSR Data to ESG Ratings:} Automating the data collection and processing required for generating Business Responsibility and Sustainability Reports (BRSR), ensuring seamless translation of raw corporate data into standardized ESG ratings.
    \item \textbf{Financial Climate Risk Modelling (BharatABM):} Developing robust macroeconomic agent-based models (ABM) to ensure RBI compliance for banks, tailored specifically for pitching actionable insights to CXOs of small and medium banks in India.
    \item \textbf{Analysis of Climate Policy Decisions (EU-India):} Authoring a strategic research paper for NSE on behalf of the Government of India, analyzing the macroeconomic and trade policy impacts arising from the 16th EU-India Summit held on 27 January 2026.
    \item \textbf{Colombo Stock Exchange Recommendations:} Conducting a detailed ESG gap analysis for the Colombo Stock Exchange (CSE) and formulating strategic recommendations to help them set up a comprehensive, internationally aligned ESG reporting framework.
    \item \textbf{The Sustainability Year Book 2026:} Co-authoring the \textit{Sectoral Outlook} chapter for NSE's flagship Sustainability Year Book, released on World Environment Day (June 5, 2026).
    \item \textbf{Green Bonds Rating Framework:} Developing a foundational methodological framework and criteria for the rigorous evaluation and rating of green bonds in the Indian market.
\end{enumerate}

\section{Structure of This Report}
This report comprehensively documents the objectives, methodologies, and outcomes of the aforementioned workstreams. Chapter 2 provides the technical review pipeline. Part II dives into the software systems, much like an ERP capability review, detailing the BRSR automation and the BharatABM database schema. Part III focuses on Financial Climate Risk and Green Bonds. Part IV reviews policy frameworks, including the EU-India summit and the Colombo Stock Exchange gap analysis. Finally, Part V provides conclusions and a risk prioritization matrix for software maintenance.


\chapter{Technical Methodology \& Review Pipeline}
\section{Sources \& Approach}
The data underlying this report originates from several proprietary codebases and data pipelines constructed during the PS-1 internship. The primary sources of truth are:
\begin{itemize}
    \item \textbf{The BRSR Automation Pipeline} (`brsr\_automation`): Comprising data ingestion scripts, peer analysis mechanisms, and automated HTML reporting based on real corporate filings.
    \item \textbf{Financial Climate Risk Modelling Framework} (`FCRM`): A comprehensive Python package structured to ingest macroeconomic, institutional, and credit data to stress-test financial assets.
    \item \textbf{BharatABM Data Schema} (`bharatabm\_schema.dbml`): The foundational architecture mapping millions of economic agents in India.
    \item \textbf{Financial Data Panels}: Datasets such as `10-Firm\_EVA\_FY16-FY25\_Master.xlsx` and `cse\_companies.csv` used for economic value-added (EVA) regressions and sector mapping.
\end{itemize}

\section{Three-Stage Review Pipeline}
The analysis in this report follows a structured three-stage pipeline to ensure rigor:
\subsection{Stage 1: Extraction \& Ingestion}
Data is programmatically extracted from raw sources (e.g., CSV files, PDF disclosures, and APIs). Scripts located in `scripts/data\_acquisition` and `scripts/data\_processing` handle the normalization of repetitive data groups into long-format datasets, similar to an ETL (Extract, Transform, Load) process used by institutional auditors.

\subsection{Stage 2: Reconciliation \& Validation}
Data streams are subjected to internal validation mechanisms. For instance, the `FCRM` package relies on rigorous unit tests (e.g., `test\_pd.py`, `test\_pipeline.py`) to reconcile mathematical climate risk outputs against expected baselines. In the BharatABM framework, spatial reconciliations are conducted by mapping H3 cell index keys against universal village/town keys (SHRID2) and Census 2011 numeric codes.

\subsection{Stage 3: Structured Findings \& Recommendations}
The final stage transforms raw arrays and analytical matrices into human-readable strategic outputs. This is manifested in the automated HTML reports generated by the BRSR pipeline and the policy briefs directed toward regulatory bodies (CSE, SEBI, EU-India).

\part{Software Systems \& Data Architecture}

\chapter{Finance Systems Review: BharatABM \& Database Architecture}
\section{System Capability Review: The BharatABM Database}
\subsection{What is BharatABM?}
Similar to how an Enterprise Resource Planning (ERP) system unifies corporate finance, the BharatABM platform serves as a 1:100 scale agent-based simulation of the Indian economy. It models the financial flows, supply chain interactions, and climate transition impacts across an operational horizon running from January 2021 (T-5) to January 2031 (T+5).

\subsection{Core Modules and Schema (DBML)}
The backbone of the simulation is the \texttt{bharatabm\_schema.dbml} database architecture, built on PostgreSQL. This schema strictly adheres to rigorous data normalization practices.
\begin{itemize}
    \item \textbf{Agent Taxonomy:} The system tracks individual agents ($\approx$ 14.4 million), household agents ($\approx$ 3.0 million), listed firm agents (5,500 at 1:1 scale), MSME agents ($\approx$ 630,000), farm agents ($\approx$ 1.46 million), and government agencies.
    \item \textbf{Polymorphic Relationships:} To map complex interactions such as an individual's employment across varying entity types (farms vs listed firms), the schema employs polymorphic keys (e.g., \texttt{target\_type ENUM} + \texttt{target\_id BIGINT}), enforcing referential integrity at the application layer.
\end{itemize}

\subsection{The Spatial Key Framework}
A critical challenge addressed in the architecture is the reconciliation of disparate geographical mapping systems. The database integrates three inherently incompatible spatial schemas:
\begin{enumerate}
    \item \texttt{shrid2}: The universal village/town key.
    \item \texttt{pc11\_codes}: Census 2011 numeric codes.
    \item \texttt{h3\_cell}: The high-resolution hexagonal operational key used by the simulation's Mesa-Frames kernel.
\end{enumerate}
A crosswalk spatial index was engineered using \texttt{build\_osm\_graph.py} to compute network-constrained commuting and routing distances via OpenStreetMap data, fundamentally shifting the model from synthetic assumed distances to real-world logistics parameters.

\chapter{The BRSR Automation Pipeline Workflow}
\section{Pipeline Execution and Audit Trail}
The BRSR reporting framework relies on accurate, timely ingestion of corporate sustainability metrics. To transition from manual, error-prone data collection to a systematic audit trail, an automated pipeline was engineered.

\subsection{The \texttt{main.py} Execution Flow}
The entry point of the pipeline is a scalable command-line interface developed in Python. It initiates a three-step peer analysis process that acts as the core "vendor workflow" for our sustainability metrics:
\begin{lstlisting}[language=Python, caption=Excerpt of the BRSR Pipeline Execution Flow]
def run_analysis(company_name: str, max_peers: int = 20, output_dir: str = None):
    # Step 1: Load and analyze
    analyzer = PeerAnalyzer()
    results = analyzer.analyze_company(company_name, max_peers=max_peers)
    
    # Step 2: Save JSON results
    results_path = analyzer.save_results()

    # Step 3: Generate HTML report
    generator = ReportGenerator()
    report_path = generator.generate_report(results)
\end{lstlisting}

This pipeline ingests unstructured and semi-structured ESG data, computes relative peer scoring across up to 20 industry peers (e.g., comparing Reliance Industries Ltd or Tata Steel Ltd), and serializes the state to a JSON ledger before rendering a final client-facing HTML report. This ensures a persistent, auditable trail from raw ingestion to the final generated ESG rating.

\part{Financial Climate Risk \& Green Bonds}

\chapter{FCRM: Financial Climate Risk Modelling Package}
\section{Architecture of the Risk Engine}
The \texttt{FCRM} module is the core computational engine deployed to ensure RBI compliance regarding transition and physical climate risk stress testing.

\subsection{Component Breakdown}
The Python package is modularized into distinct analytical silos:
\begin{itemize}
    \item \texttt{fcrm.macro}: Ingests macroeconomic indicators (e.g., carbon pricing impacts, GDP contraction curves).
    \item \texttt{fcrm.institutional} \& \texttt{fcrm.credit}: Maps the macro shocks onto institutional ledgers, calculating shifts in Probability of Default (PD) and Loss Given Default (LGD) metrics.
    \item \texttt{fcrm.satellite}: Handles geospatial hazards (e.g., flood zones, temperature extremes) mapping to physical asset locations.
\end{itemize}

\subsection{Testing and Validation}
Rigorous validation is crucial for financial models. The \texttt{test\_pd.py} and \texttt{test\_pipeline.py} scripts utilize mock financial ledgers to assert that the stochastic risk equations behave deterministically under controlled scenarios, ensuring the engine meets the strict compliance standards expected by SEBI and the RBI.

\chapter{Green Bond Rating Framework}
\section{The Tri-Factor Rating System}
The issuance of Green Bonds has surged, necessitating an independent, verifiable framework to assess "greenwashing" risk. The \texttt{NSRALTriFactorRatingSystem} was developed to programmatically compute a bond's ESG efficacy.

\subsection{Factor Analysis Methodology}
The algorithm evaluates three primary pillars, as demonstrated by the test case on the Adani Green Energy 2,167 MW Solar Bond (2024):
\begin{enumerate}
    \item \textbf{SEBI NCS Compliance \& ICMA Alignment:} Weighting the use of proceeds (e.g., 100\% Solar PV), ring-fencing in escrow accounts, and commitments to annual BRSR reporting.
    \item \textbf{Environmental Impact (India Context):} Quantifying the net mitigation benefit of displacing high-emission grid coal with renewable lifecycles.
    \item \textbf{Issuer ESG Integration:} Assessing the parent corporate governance structure against the specific subsidiary's transition plans.
\end{enumerate}

\begin{lstlisting}[language=Python, caption=Green Bond Rating Object Structure]
adani_green_bond_data = {
    "bond_name": "Adani Green Energy 2,167 MW Solar Green Bond",
    "icma_governance": {"use_and_selection": 95, "management_of_proceeds": 90},
    "environmental_impact": {"net_mitigation_benefit": 95},
    "issuer_esg": {"corporate_esg_score": 70, "strategic_transition_plan": 90}
}
\end{lstlisting}

This programmatic scoring mechanism allows NSRAL to generate consistent, bias-free green bond ratings across the domestic debt market.

\part{Policy, ESG Frameworks \& Economics}

\chapter{Colombo Stock Exchange: ESG Gap Analysis}
\section{Sectoral Mapping and Compliance Overlays}
The Colombo Stock Exchange (CSE) is actively transitioning toward mandating comprehensive ESG disclosures. A critical aspect of this workstream was conducting a gap analysis between the existing CSE frameworks and international standards (IFRS S1/S2).

\subsection{Data Normalization Operations}
Using data engineering pipelines (\texttt{add\_sectors.py}, \texttt{update\_sectors.py}), the raw universe of Sri Lankan listed firms (\texttt{cse\_companies.csv}) was mapped to standardized global sector classifications. This allowed us to programmatically query the dataset and apply sector-specific materiality maps (e.g., SASB standards) to highlight exact disclosure gaps currently present in the CSE market.

\chapter{Analysis of Climate Policy Decisions (EU-India)}
\section{Macroeconomic Impact of the 16th Summit}
The EU-India strategic climate agenda represents a monumental shift in international trade policy, particularly concerning the Carbon Border Adjustment Mechanism (CBAM). 

\subsection{Sentiment and News Flow Analysis}
To quantify the transition risk of these policies, our analysis integrated the \texttt{Government\_News\_Carbon} dataset alongside historical news sources like the GDELT project. By classifying news categories and scoring sentiment, the model maps policy announcements directly to potential financial impacts on carbon-intensive export sectors (e.g., Indian steel and aluminum).

\chapter{Financial Forecasting: Firm-Level Economic Value Added}
\section{Purpose and Historical Panel Data}
Similar to a statutory audit's forward-looking regression, the macroeconomic modelling work utilized a dense financial panel (\texttt{10-Firm\_EVA\_FY16-FY25\_Master.xlsx}) to track Economic Value Added (EVA) across key Indian corporations over a decade.

\subsection{Regression and Trend Analysis}
By evaluating the historical EVA, we derive a regression curve that highlights the structural decay or growth of capital efficiency across sectors prior to the imposition of severe climate levies. The data indicates that firms actively integrating ESG principles maintain a more resilient EVA trendline when subjected to the simulated climate shocks in the BharatABM framework.

\part{Conclusions \& Technical Recommendations}

\chapter{Technical Debt \& Code Prioritization Matrix}
\section{Software Risk Management}
Just as a financial audit reveals discrepancies in ledgers, a review of the developed codebases reveals areas of technical debt and required maintenance.

\begin{table}[h]
\centering
\caption{Codebase Risk \& Recommended Mitigation}
\begin{tabularx}{\textwidth}{lX}
\toprule
\textbf{Risk Area} & \textbf{Recommended Mitigation} \\
\midrule
\textbf{Spatial Keys in BharatABM} & The disconnect between H3 cells and PC11 census codes requires a dedicated crosswalk table generated via point-in-polygon operations against SHRID boundaries. \\
\textbf{FCRM Unit Test Coverage} & While \texttt{test\_pd.py} covers base calculations, integration tests mocking full macroeconomic shock scenarios must be expanded. \\
\textbf{BRSR Data Parsing} & The PDF text extraction relies heavily on layout heuristics. Implementing a robust NLP/LLM-driven parsing layer in \texttt{scripts/nlp\_analysis} is recommended for unstructured filings. \\
\bottomrule
\end{tabularx}
\end{table}

\chapter{Final Recommendations and Conclusion}
\section{A Robust Technological Baseline}
This Practice School-I internship successfully established a foundational suite of tools for NSE Indices and NSRAL. The delivery of a fully automated BRSR peer analysis pipeline, a comprehensive python-based Financial Climate Risk engine (FCRM), and the underlying architecture for a national-scale economic simulation (BharatABM) significantly advances NSRAL's operational capacities. 

\section{Recommendations}
\begin{enumerate}
    \item \textbf{Operationalize the FCRM Package:} The codebase should be deployed to a staging server, allowing internal analysts to run scenario generations directly against proprietary banking portfolios.
    \item \textbf{Expand Green Bond Testing:} The \texttt{NSRALTriFactorRatingSystem} should be tested against a broader historical panel of Indian bonds to refine its weighting parameters.
    \item \textbf{Continuous ABM Calibration:} The BharatABM model requires ongoing calibration. Integrating fresh data from the \texttt{nsral\_ibbi\_cirp\_dataset.csv} into the firm-bankruptcy modules will greatly enhance the simulation's fidelity.
\end{enumerate}

\end{document}
"""

with open("/Users/ashishmishra/animeshratna/nsral/ps1-report/2024A8PS0665P_PS1_complete.tex", "w") as f:
    f.write(latex_content)

print("Latex file written successfully.")
