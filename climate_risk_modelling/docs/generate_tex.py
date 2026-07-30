tex = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
}
\usepackage{booktabs}
\usepackage{xcolor}

\title{\textbf{NSRAL Institutional Climate Risk Engine: Executive Strategic Briefing \& Methodology}}
\author{Animesh Ratna \\ NSE Sustainability Ratings and Analytics Ltd. (NSRAL)}
\date{June 2026}

\begin{document}

\maketitle

\tableofcontents
\newpage

\begin{abstract}
\noindent This document outlines the mathematical architecture of the National Systemic Risk Assessment Layer (NSRAL) Climate Stress Testing Framework. The core engine incorporates empirical market data to calculate systemic risk. The architectural pivot reduces reliance on theoretical, normal-distribution approximations in favor of empirical market realities. 

Key structural upgrades include:
\begin{itemize}
    \item \textbf{Empirically-Mapped KMV Default Transformation:} The engine maps a firm's Distance-to-Default ($DD$) against an empirical Expected Default Frequency ($EDF$) function calibrated to true emerging market equity volatility, capturing the leptokurtic tail of compounding climate events.
    \item \textbf{Asymmetric Vine Copula Architecture:} The symmetric Student-t Copula has been replaced with a Clayton Copula to model downside Wrong Way Risk (WWR). This isolates the correlation between borrower default and physical collateral stranding during stress periods.
    \item \textbf{TCaR Structural Uncertainty Isolation:} The Transition Cost-at-Risk ($TCaR$) module evaluates the gap between a firm's Required Green CAPEX and their Realized Green CAPEX sourced from BRSR filings.
    \item \textbf{Spatial Tensor Interpolation:} Core probability and spatial mapping operations have been refactored to utilize JAX interpolations, supporting Monte Carlo execution.
\end{itemize}
These enhancements allow NSRAL to produce A-IRB-aligned capital degradation metrics.
\end{abstract}

\section{Macroeconomic Transmission and Scenarios}
\subsection{NGFS Scenario Architecture}
The engine executes multi-decade stress tests anchored by the Network for Greening the Financial System (NGFS) Phase 4 scenarios. The platform processes trajectories mapping the CMIP6 climate models.

\subsection{Leontief Matrix Inversion for Supply Chain Contagion ($\delta_{NIC}$)}
The supply chain transmission...

\subsection{Dynamic Transition Vulnerability Factor (DTVF)}
The dynamic formulation...

\section{Continuous Financial Vulnerability Satellite Models}
\subsection{Climate Earnings-at-Risk (CEaR)}
The CEaR...

\subsection{Transition Cost-at-Risk (TCaR)}
The TCaR module evaluates...

\section{The Basel Credit Risk Core Engine}
\subsection{Empirically-Mapped KMV Default Transformation (PD)}
The engine computes probability of default...

\subsection{Numerical Inversion of Unobservable Asset Parameters (Merton)}
Using Merton's model...

\subsection{Systemic Climate Stress Injection}
CEaR degrades the firm's expected cash flows (Asset Drift Penalty), while TCaR models the uncertainty of unmitigated transition liabilities (Asset Volatility Penalty).

Because a firm's baseline $DD_{base}$ represents its safety buffer from the default barrier, the combined macroeconomic and physical drift penalties are subtracted from the numerator. Concurrently, the transition uncertainty scales the variance in the denominator:

\begin{equation}
Macro\_Drift\_Penalty = 0.5 \times (\epsilon_{NIC,t} \times |\Delta GDP_t|)
\end{equation}

The 0.5 scalar acts as an empirical dampening factor, transforming the absolute gross domestic product collapse into a standardized Z-score asset drift penalty, calibrated against historical emerging market default dynamics.

\begin{equation}
DD_{stressed} = \frac{DD_{base} - Macro\_Drift\_Penalty - CEaR\_Drift\_Penalty}{1 + TCaR\_Volatility\_Penalty}
\end{equation}

Finally, the stressed Probability of Default ($PD_{stressed}$) is extracted by mapping $DD_{stressed}$ against the empirical logistic EDF curve calibrated to true emerging market volatility.

\textbf{Multivariate Topological Surface \& Continuity:} To support mathematical continuity during gradient-based risk calculations, the discrete empirical data is transformed into a geometric topological surface. Rather than relying on discrete binning, the engine mathematically shifts the Distance-to-Default coordinates across the continuous NGFS Severity domain. By using this continuous 3D topography, we prevent NaN gradient issues during marginal risk calculations and ensure that the probability tail expands continuously during systemic stress.

\begin{equation}
PD_{stressed} = EDF_{Empirical}(DD_{stressed})
\end{equation}

\subsection{Asymmetric Vine Copula (Clayton) for Wrong Way Risk (WWR)}
This architecture models the correlation between default timing and collateral degradation (Wrong Way Risk). Historically, some climate models treat PD and LGD as independent variables. However, standard symmetric models (like the Gaussian or Student-t Copula) apply this correlation to both tails of the distribution. Climate risk presents asymmetries: a severe physical event increases the correlation between default and physical ruin, while benign periods do not necessarily present equivalent upside correlation.

To capture this risk, the engine utilizes a \textbf{Clayton Copula}. The Clayton Copula exhibits lower-tail dependence and zero upper-tail dependence, mirroring the physical reality of a downside shock:

\begin{equation}
C^{Clayton}_{\theta}(u, v) = \left[ \max(u^{-\theta} + v^{-\theta} - 1, 0) \right]^{-1/\theta}
\end{equation}

This ensures that the expected loss reflects portfolios with concentrated physical risk, without distorting calculations during non-stressed baseline years.

\subsection{Market Stranding and Uninsurability Thresholds}
Physical damage to collateral is a component of the Loss Given Default (LGD) equation. Other considerations include market stranding (liquidity of the collateral) and insurability.

The engine introduces a decay function for insurability. Once the asset's Climate Risk Score surpasses an empirical threshold, the engine models a reduction in available insurance coverage. When the uninsurability threshold is breached, the insurance mitigation drops to zero. However, to translate the joint probability of the Copula into a physical loss severity, the engine computes a WWR Multiplier. This metric isolates the tail dependence by dividing the joint probability (the Copula output) by the probability of the events occurring independently:

\begin{equation}
WWR\_Multiplier = \frac{C^{Clayton}_{\theta}(PD_{stressed}, P_{Damage})}{PD_{stressed} \times P_{Damage}}
\end{equation}

This dependency ratio is applied as a scalar to the baseline physical collateral damage. To mathematically prevent the loss severity from exceeding the total value of the asset, the calculation is bounded at 1.0 (100\% loss) prior to the application of the dynamic insurance threshold:

\begin{equation}
LGD_{stressed} = \min(1.0, LGD_{base} \times WWR\_Multiplier) \times (1 - Insurance\_Cover_t)
\end{equation}

Ultimately, the primary goal of the preceding derivations is to compute the final Expected Credit Loss (ECL) for each loan under severe climate stress. While $PD_{stressed}$ and $LGD_{stressed}$ are heavily shocked by the complex climate manifolds, the bank's Exposure at Default (EAD) remains a relatively static accounting input (comprising drawn balances plus a standard credit conversion factor applied to undrawn credit lines), yielding the final loan-level loss metric:

\begin{equation}
ECL_{Stressed} = PD_{stressed} \times LGD_{stressed} \times EAD
\end{equation}

\section{Institutional Strategic Risk \& Capital Degradation}
While individual loan defaults drive portfolio losses, systemic climate events also influence strategic liquidity and market risks across the institution's balance sheet.

\subsection{Unit-Aligned CET1 Capital Degradation}
The engine scales micro-level exposures to match the macro-financial parameters of the bank (e.g., aligning EADs with the institution's Rupee capital base). The system aggregates facility losses ($\Delta ECL$) and institutional stresses (Treasury Mark-to-Market losses, Liquidity Drawdowns) into $Loss_{Total}$.

The metric of institutional survivability is the Common Equity Tier 1 Capital Ratio variation:

\begin{equation}
CET1_{Stressed} = \frac{CET1\_Capital_{Base} - Loss_{Total}}{RWA_{base}(1 + r_{inf})}
\end{equation}

This metric informs the assessment of the bank's capacity to absorb systemic climate shock relative to regulatory capital minimums.

\subsection{Institutional Stress Variable Definitions}
The components driving the stressed CET1 ratio are mathematically defined as follows:

\subsubsection{Baseline Regulatory Inputs}
The $CET1\_Capital_{Base}$ and $RWA_{base}$ are static accounting inputs derived from the institution's core balance sheet prior to the injection of the climate shock:
\begin{itemize}
    \item $CET1\_Capital_{Base}$: The core equity tier 1 capital held in reserve to absorb losses.
    \item $RWA_{base}$: The aggregate value of the bank's assets weighted by their historical baseline risk profiles.
\end{itemize}

\subsubsection{Risk-Weighted Asset Inflation ($r_{inf}$)}
As the underlying credit quality of the loan portfolio deteriorates due to the realization of physical and transition hazards, regulatory capital requirements force a highly non-linear inflation of the portfolio's Risk Weights. Rather than relying on a static or crude macroeconomic pass-through multiplier, the engine actively models this dynamic ratings migration as an emergent property of the portfolio.

For every loan in the simulated universe, the engine recalculates the precise capital requirement ($K$) under the Basel III Advanced Internal Ratings-Based (A-IRB) framework using the dynamically stressed Default Probability ($PD_{stressed}$) and Loss Given Default ($LGD_{stressed}$). The true systemic RWA inflation rate ($r_{inf}$) is explicitly derived by taking the ratio of the newly aggregated stressed RWA against the baseline RWA boundary:

\begin{equation}
r_{inf} = \frac{\sum_{i=1}^{N} \left[ K(PD_{stressed,i}, LGD_{stressed,i}) \times 12.5 \times EAD_i \right]}{\sum_{i=1}^{N} RWA_{base,i}} - 1
\end{equation}

Where $K(\cdot)$ represents the standardized Basel III corporate asset correlation and maturity adjustment function. The 12.5 scaling factor is a global regulatory constant derived from the Basel minimum capital ratio of 8\% (where mathematically, $RWA = \frac{Minimum\_Capital}{0.08}$, yielding the 12.5 multiplier to convert the raw capital requirement percentage $K$ back into an equivalent Risk-Weighted Asset volume).

\subsubsection{Total Institutional Loss ($Loss_{Total}$)}
The total loss is an aggregate of five distinct stress vectors sweeping across the institution's balance sheet, transcending simple loan defaults:

\begin{equation}
Loss_{Total} = \Delta ECL_{Inc} + Liquidity\_Draw + Market\_Loss + Funding\_Cost + Op\_Loss
\end{equation}

Where:
\begin{itemize}
    \item $\Delta ECL_{Inc}$: The sum of all incremental Expected Credit Losses generated by borrower defaults ($ECL_{Stressed} - ECL_{Base}$).
    \item $Liquidity\_Draw$: Cash flow losses caused by distressed borrowers maximizing their undrawn credit lines prior to default.
    \item $Market\_Loss$: Mark-to-market shock on the bank's treasury portfolio due to widening climate credit spreads.
    \item $Funding\_Cost$: The increased premium the bank must pay in wholesale funding markets due to its own credit rating downgrade.
    \item $Op\_Loss$: Direct physical damage to the bank's operational infrastructure and branch network, augmented by transition-related regulatory fines.
\end{itemize}

\end{document}
"""

with open("climate_risk_model_report.tex", "w") as f:
    f.write(tex)

