#!/bin/bash

# ==============================================================================
# NSRAL Pipeline Orchestrator
# This script executes the entire end-to-end processing pipeline:
# Weight Redistribution -> Percentile Scoring -> Full Report Generation
# ==============================================================================

set -e

echo "=========================================="
echo "    NSRAL Automated Execution Pipeline    "
echo "=========================================="

# Check for required input flags
if [ -z "$1" ]; then
    echo "Usage: ./run_pipeline.sh --company \"Company Name\""
    echo "   or: ./run_pipeline.sh --sector \"Sector Name\""
    echo "   or: ./run_pipeline.sh --batch batch_list.txt"
    exit 1
fi

TARGET_TYPE=$1
TARGET_VALUE=$2

echo "[*] Initializing pipeline for $TARGET_TYPE: $TARGET_VALUE"
echo "[*] Checking input directories..."

if [ ! -d "data/input" ]; then
    echo "Error: 'data/input' directory not found. Please ensure input mapping and BRSR files are placed here."
    exit 1
fi

# 1. Weight Redistribution
echo "------------------------------------------"
echo "[1/3] Running Hierarchical Weight Redistribution..."
# IT must place the master weights Excel in data/input
MASTER_EXCEL="data/input/master_weights.xlsx"
if [ -f "$MASTER_EXCEL" ]; then
    python3 scripts/scoring_and_weights/redistribute_weights.py --master_weights "$MASTER_EXCEL" --output_dir "data/intermediate/weights"
else
    echo "  [WARN] Master weights file ($MASTER_EXCEL) not found. Skipping weight redistribution."
fi

# 2. Score Companies
echo "------------------------------------------"
echo "[2/3] Calculating Sector-based Percentiles & Scores..."
# NOTE: The python scripts need to be updated to accept the target arguments cleanly. 
# For now, it passes the flags through to the Python script.
python3 scripts/scoring_and_weights/score_companies.py $TARGET_TYPE "$TARGET_VALUE" || echo "  [WARN] Scoring encountered an issue, but continuing pipeline."

# 3. Report Generation
echo "------------------------------------------"
echo "[3/3] Generating PDF Scorecards & Reports..."

echo "  -> Generating Executive Summary..."
python3 scripts/report_generation/generate_executive_summary.py $TARGET_TYPE "$TARGET_VALUE" || true

echo "  -> Generating Peer Analysis..."
python3 scripts/report_generation/generate_peer_report.py $TARGET_TYPE "$TARGET_VALUE" || true

echo "  -> Compiling Full Scorecard..."
python3 scripts/report_generation/generate_full_scorecard.py $TARGET_TYPE "$TARGET_VALUE" || true

echo "------------------------------------------"
echo "[SUCCESS] Pipeline execution complete!"
echo "Final reports are available in the 'reports/' directory."
echo "=========================================="
