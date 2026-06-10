# NSE Sustainability Ratings and Analytics Ltd. (NSRAL)
## ESG Scorecard Generation Pipeline

This repository contains the automated pipeline for evaluating corporate ESG metrics, generating percentile scores, and generating comprehensive PDF reports (Executive Summaries, Peer Benchmarking, and Thematic Scorecards).

---

## Directory Structure

To keep data and code organized, please adhere strictly to the following folder structure:

```text
nsral/
├── data/
│   ├── input/         # [DROP ZONE] Place all raw files here (BRSR dumps, master schemas, mappings)
│   └── intermediate/  # [INTERNAL] Temporary storage for generated JSON weights and processed data
├── reports/           # [OUTPUT] Generated PDF Scorecards, Executive Summaries, and Peer Reports
├── scripts/           
│   ├── data_processing/       # Scripts to parse BRSR/XBRL files
│   ├── scoring_and_weights/   # Hierarchical redistribution and sector-based percentile scoring
│   └── report_generation/     # PDF compilers and Matplotlib visual generators
├── run_pipeline.sh    # [ENTRY POINT] Master orchestration script
└── README.md
```

---

## Execution Instructions (For IT Operations)

Whenever new data is received, you do not need to modify the Python scripts. Simply swap out the files in the `data/input/` directory and execute the bash pipeline.

### Step 1: Update Data Files
Place your updated files into `data/input/`. Ensure the exact filenames and structures are preserved:
- `master_weights.xlsx`: The master hierarchical schema containing `Pillar -> Theme -> Question` and the `0/1` binary relevance columns for each Basic Industry.
- `nsral_sector_hierarchy.xlsx` (Optional): The company-to-industry mappings.
- Raw BRSR extraction dumps.

### Step 2: Run the Pipeline
Use the `run_pipeline.sh` script to trigger the full execution (Weight Redistribution -> Percentile Scoring -> Report Compilation).

You can target a specific company:
```bash
./run_pipeline.sh --company "Tata Motors"
```

Or run an entire sector at once:
```bash
./run_pipeline.sh --sector "Automotive"
```

Or pass a text file containing a batch list:
```bash
./run_pipeline.sh --batch target_companies.txt
```

### Step 3: Collect Reports
Once execution finishes, navigate to the `reports/` directory. You will find:
1. Executive Summaries
2. Peer Benchmarking Analysis
3. Full ESG Scorecards (which includes ESG Drivers, E/S/G Thematic representations and assessments, and Final Conclusions)

---

## Upcoming Rating Logic Modularity
*Note: The pipeline incorporates dynamic logic intended for future-proofing:*
1. **Dynamic Weight Redistribution:** The system calculates and drops weights for irrelevant questions (marked `0` in your Excel) and proportionally redistributes them to active themes in the same Pillar.
2. **Sector-Based Percentiles:** The underlying scoring engine calculates rank-based percentiles tailored strictly to basic industry cohorts rather than a global pool.
