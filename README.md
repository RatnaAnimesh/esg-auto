# NSE Sustainability Ratings and Analytics Ltd. (NSRAL)
## Master Repository Manual and Architecture Specification

This repository contains the complete analytical suite, data processing pipelines, financial climate risk models, scoring engines, and research infrastructure developed by NSE Sustainability Ratings and Analytics Ltd. (NSRAL).

---

## 1. Master Repository Directory Overview

```text
nsral/
├── BRSR/                   # Business Responsibility and Sustainability Reporting Data Hub
├── CSE_Proposal/           # Colombo Stock Exchange ESG Rating & Classification Proposal
├── FCRM/                   # Full Climate Risk Model (Basel A-IRB Structural Stress Engine)
├── brsr_scoring/           # BRSR Scoring Engine, Kalman Fusion & Taxonomy Mappers
├── climate_risk_modelling/ # Macro-Financial Climate Risk Analytics & Physical Risk Engine
├── data/                   # Input & Intermediate Data Dropzones for Main Pipeline
├── green_bonds/            # NSRAL Tri-Factor Green Bond Rating Engine
├── india-eu_report/        # India-EU Trade, CBAM Policy & BharatABM Economic Simulator
├── other_work/             # Long-Term EVA Valuation Studies & Empirical Data Analytics
├── report_automation/      # Automated PDF Report Ingestion & Question Mapping Engine
├── reports/                # Destination Directory for Generated PDF Deliverables
├── scripts/                # Modular Core ESG Pipeline Scripts
├── sources/                # Reference Standards and Institutional Datasets
├── templates/              # Report Layout Specifications and Matplotlib Style Presets
├── app.py                  # Streamlit Interactive ESG Analytics & Preview Dashboard
├── generate_report.py      # Primary PDF Scorecard & Graphic Report Compiler
├── run_pipeline.sh         # Master Bash Orchestrator for ESG Evaluation Pipeline
├── requirements.txt        # Python Dependency Manifest
├── package.json            # Node.js Module Configuration
├── package-lock.json       # Node.js Locked Dependency Graph
└── skills-lock.json        # Workspace Skill State Lockfile
```

---

## 2. Core ESG Pipeline and Orchestration Entry Points

The primary ESG scorecard pipeline evaluates corporate disclosures, calculates sector-relative percentiles, applies dynamic weight redistribution across environmental, social, and governance pillars, and compiles PDF deliverables.

### Entry Scripts

#### `run_pipeline.sh`
The master bash orchestration script. It automates the execution sequence across three analytical stages:
1. **Weight Redistribution:** Parses raw disclosures against `master_weights.xlsx` and redistributes dropped or non-revisable question weights proportionally across active themes within the same pillar.
2. **Percentile Scoring:** Evaluates raw company metrics against industry-specific peer distributions rather than a global pool.
3. **Report Generation:** Calls `generate_report.py` to compile executive summaries, peer benchmark matrices, and thematic scorecards.

Usage examples:
```bash
# Execute pipeline for a single target company
./run_pipeline.sh --company "Tata Motors"

# Execute pipeline across an entire industry sector cohort
./run_pipeline.sh --sector "Automotive"

# Execute pipeline in batch mode from a text file manifest
./run_pipeline.sh --batch target_companies.txt
```

#### `generate_report.py`
The core python report compiler built on ReportLab and Matplotlib. It handles:
- Dynamic page layout generation for Executive Summaries, Peer Benchmarks, and Full ESG Scorecards.
- Generation of vector graphics for pillar breakdown charts, radar charts, and risk matrices.
- Automated insertion of thematic qualitative commentary and key driver highlights.

#### `app.py`
The interactive Streamlit dashboard. It allows analysts to:
- Select target companies and basic industry cohorts.
- Adjust pillar/theme weighting assumptions dynamically.
- Inspect real-time ESG scorecard output prior to generating formal PDF artifacts.

---

## 3. Core Data and Infrastructure Directories

### `data/`
Structured dropzone for the main ESG evaluation pipeline:
- `data/input/`: Dropzone for raw input files, including `master_weights.xlsx` (Pillar -> Theme -> Question hierarchy with basic industry relevance flags), `nsral_sector_hierarchy.xlsx` (company sector mappings), and raw BRSR data dumps.
- `data/intermediate/`: Internal storage for JSON weight schemas, normalized company features, and intermediate percentile calculations.

### `reports/`
Output repository for generated PDF artifacts:
- **Executive Summaries:** High-level one-page ESG performance overviews.
- **Peer Benchmarking Analysis:** Comparative positioning metrics within specific basic industry cohorts.
- **Full ESG Scorecards:** Detailed assessments covering ESG Drivers, E/S/G Thematic breakdowns, and final composite scores.

### `scripts/`
Modular analytical scripts supporting the main pipeline:
- `scripts/data_processing/`: Parsers for BRSR Excel and XBRL filing extractions.
- `scripts/scoring_and_weights/`: Hierarchical weight redistribution logic and sector-based percentile algorithms.
- `scripts/report_generation/`: Layout definition scripts and graphical chart rendering engines.

### `sources/`
Reference standards, institutional datasets, regulatory guidelines, and SEBI BRSR Core compliance parameters.

### `templates/`
Matplotlib visual presets, color maps (tailored color palettes), typography configurations, and ReportLab page layout templates.

---

## 4. Sub-Projects and Specialized Analytical Engines

### 4.1. BRSR (`/BRSR`)
The primary data warehouse for Business Responsibility and Sustainability Reporting disclosures.
- **Directory Path:** `BRSR/data/`
- **Key Files:**
  - `brsr_consolidated.csv`: Comprehensive tabular database containing raw BRSR parameters across listed Indian equities.
  - `CF-BRSR-equities-17-Jul-2026.csv`: Updated equity coverage dataset containing structured corporate disclosures.

---

### 4.2. BRSR Scoring Engine (`/brsr_scoring`)
An advanced scoring, taxonomy mapping, and schema alignment subsystem.
- **Directory Path:** `brsr_scoring/`
- **Core Architecture (`brsr_scoring/src/`):**
  - `src/math/percentile.py`: Rank-based percentile transformation engine tailored to basic industry peer groups.
  - `src/math/build_scale.py`: Dynamic weight scaling and normalization algorithms.
  - `src/math/rating_calc.py`: Composite score aggregation logic.
  - `src/db/client.py` & `src/db/schema.sql`: SQLite database interface for local taxonomy and score storage.
  - `src/ingestion/parser.py`: Parser for structured BRSR question sets.
  - `src/rules/loader.py`: Rule loader for industry relevance filtering.
- **Advanced Machine Learning & Mapping Scripts (`brsr_scoring/scripts/`):**
  - `download_nse_xbrl.py`: Automated retrieval engine for NSE XBRL filings.
  - `extract_xbrl_tags.py`: Extraction utility for parsing taxonomy tags from annual report XBRL instances.
  - `mha_mapper.py`: Multi-Head Attention mapping engine for matching raw BRSR disclosures to standard taxonomy items.
  - `kalman_fusion_mapper.py`: Kalman filter state-space model for fusing disparate reporting schemas under uncertainty.
  - `llm_final_judge.py`: Large Language Model verification module to arbitrate ambiguous mapping edge cases.
  - `pdf_fallback_extractor.py`: Optical and text extraction fallback pipeline for PDF annual reports when XBRL is unavailable.

---

### 4.3. Report Automation Subsystem (`/report_automation`)
Automated mapping and data processing subsystem for large-scale report generation.
- **Directory Path:** `report_automation/`
- **Key Components:**
  - `data/reports/mapped_questions.csv`: Standardized question mapping directory linking raw company responses to evaluation metrics.
  - `scripts/data_processing/map_questions.py`: Data transformation script aligning ingested corporate responses with internal scoring schemas.

---

### 4.4. Colombo Stock Exchange Proposal (`/CSE_Proposal`)
A classification and rating framework proposal tailored for listed equities on the Colombo Stock Exchange (CSE).
- **Directory Path:** `CSE_Proposal/`
- **Key Components:**
  - `cse_companies.csv`: Comprehensive directory of listed CSE corporate entities.
  - `add_sectors.py`: Rule-based classification script mapping company entity names to global GICS industry sectors.
  - `update_sectors.py`: Maintenance utility for updating Sri Lankan corporate sector assignments.

---

### 4.5. Full Climate Risk Model (`/FCRM`)
A Basel Advanced Internal Ratings-Based (A-IRB) aligned, NGFS Phase 4 compliant structural climate stress testing engine built for the Indian banking sector.
- **Directory Path:** `FCRM/`
- **Analytical Modules:**
  1. `fcrm.macro`:
     - `leontief.py`: Input-Output Leontief inversion for inter-sectoral supply chain contagion analysis.
     - `dtvf.py`: Dynamic Transition Vulnerability Factor calculation.
  2. `fcrm.satellite`:
     - `elasticity_calibrator.py`: BIC-minimized polynomial OLS calibration for macro elasticity.
     - `ras_entropy.py`: Cross-entropy RAS information-theoretic scaling engine.
     - `cear.py`: Climate Earnings-at-Risk (CEaR) calculation.
     - `tcar.py`: Transition Cost-at-Risk (TCaR) via PCAF emission imputation.
  3. `fcrm.credit`:
     - `merton.py`: Merton structural option inversion using Powell root-finding.
     - `kmv_edf.py`: KMV Expected Default Frequency manifold and tail thickener.
     - `stress_injection.py`: Stressed Distance-to-Default and Probability-of-Default injection.
     - `clayton_copula.py`: Asymmetric Clayton copula for Wrong-Way Risk (WWR) and stressed Loss Given Default (LGD).
     - `ecl.py`: Stressed Expected Credit Loss (ECL) and Basel capital requirement K(PD, LGD).
  4. `fcrm.institutional`:
     - `total_loss.py`: Five-component loss aggregation (ECL increment, Liquidity, Market, Funding, Operational).
     - `cet1.py`: Common Equity Tier 1 (CET1) stressed capital ratio degradation and Risk-Weighted Asset (RWA) inflation modeling.

---

### 4.6. Climate Risk Modelling Subsystem (`/climate_risk_modelling`)
Analytics framework for physical and transition climate risk assessments.
- **Directory Path:** `climate_risk_modelling/`
- **Key Components:**
  - `backend/api/models/physical_risk_engine.py`: Engine for evaluating physical climate hazards (flooding, heat stress, cyclone exposure) for asset locations.
  - `frontend/`: User interface components for geographic climate vulnerability mapping.
  - `docs/`: Regulatory documentation, literature extractions on Reserve Bank of India climate guidelines, and LaTeX report sources.

---

### 4.7. Green Bond Rating Engine (`/green_bonds`)
The NSRAL Tri-Factor Green Bond Rating System for evaluating green debt instruments.
- **Directory Path:** `green_bonds/`
- **Key Script:** `test_indian_bond.py`
- **Evaluation Factors:**
  1. **SEBI NCS & ICMA Alignment:** Evaluates use of proceeds, project selection governance, management of proceeds, and annual reporting transparency.
  2. **Environmental Impact:** Measures net mitigation benefits (e.g., renewable energy capacity displacing high-carbon grid emissions) and technology lifecycle maturity.
  3. **Issuer ESG Integration:** Assesses parent corporate ESG performance and long-term strategic decarbonization targets.

---

### 4.8. India-EU Policy & BharatABM Simulator (`/india-eu_report`)
A dual research and modeling initiative focused on India-EU trade relations, the EU Carbon Border Adjustment Mechanism (CBAM), and a national-scale agent-based economic simulator.
- **Directory Path:** `india-eu_report/`
- **Sub-Projects:**
  - `paper/`: Research manuscripts, policy trade analysis, and empirical evaluations of CBAM impacts on Indian industrial exports.
  - `BharatABM/`: A national-scale agent-based model of the Indian economy specified against the 2026 research frontier.
  - **Formal Proofs (`BharatABM/formal/BharatABM/`):** Written in Lean 4 + Mathlib (68 theorems, 0 sorry, 0 axiom). Formally proves double-entry accounting conservation (`Ledger.lean`), tick confluence (`Determinism.lean`), QUAIDS demand properties (`Demand.lean`), market clearing existence/uniqueness (`Clearing.lean`), and self-exciting hazard stationarity (`Hazard.lean`).

---

### 4.9. Financial Valuations & Corporate Research (`/other_work`)
Empirical financial analytics and valuation models.
- **Directory Path:** `other_work/`
- **Key Assets:**
  - `10-Firm_EVA_FY16-FY25_Master.xlsx`: Master Economic Value Added (EVA) longitudinal dataset covering ten key Indian corporate entities across FY16-FY25.
  - `Chapter IV draft (Data Analysis).docx`: Analytical manuscript detailing firm financial performance and capital efficiency trends.
  - `EVA_Trend_Chart.png`: Visualization of enterprise EVA trajectories over the ten-year observation window.

---

## 5. Standalone Utilities and Verification Scripts

Located in the repository root directory:
- `test_bse.py`: Automated retrieval client for fetching corporate announcements and filings from the Bombay Stock Exchange (BSE) portal.
- `test_nse.py`: API test client for querying National Stock Exchange (NSE) corporate disclosure services.
- `test_scrape.py`: Utility scraper for extracting text and tabular metrics from PDF sustainability reports.
- `test_wayback.py`: Wayback Machine API client for retrieving historical corporate web disclosures across multi-year baselines.
- `test_manim.py`: Animation rendering script utilizing Manim for generating mathematical and graphic visual presentations of ESG metrics.

---

## 6. System Requirements and Environment Setup

### Python Environment
Required Python version: 3.10+

Dependencies can be installed via `pip`:
```bash
pip install -r requirements.txt
```

For full `FCRM` development and stress testing:
```bash
cd FCRM
pip install -e ".[dev]"
```

### Formal Verification (Lean 4)
To verify the Lean 4 formal proofs in `BharatABM`:
```bash
cd india-eu_report/BharatABM/formal/BharatABM
lake exe cache get
lake build
```

---

## 7. Operational Workflow for New Rating Cycles

1. **Ingest Raw Data:** Drop new BRSR disclosures, master weights, and sector hierarchy files into `data/input/`.
2. **Execute Master Pipeline:** Run `./run_pipeline.sh --batch target_companies.txt` to trigger dynamic weight redistribution, percentile calculation, and PDF compiling.
3. **Review Deliverables:** Inspect output PDF reports in the `reports/` directory.
4. **Interactive Audit:** Launch `streamlit run app.py` to inspect scoring distribution dynamics and run interactive scenario sensitivity checks.
