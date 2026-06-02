#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def run_step(command_list, step_name):
    print(f"\n{'='*50}")
    print(f"🚀 Starting Step: {step_name}")
    print(f"Command: {' '.join(command_list)}")
    print(f"{'='*50}")
    
    result = subprocess.run(command_list)
    if result.returncode != 0:
        print(f"\n❌ ERROR: Step '{step_name}' failed with exit code {result.returncode}.")
        print("Pipeline aborted.")
        sys.exit(result.returncode)
    
    print(f"✅ Step '{step_name}' completed successfully.\n")


def main():
    parser = argparse.ArgumentParser(description="Run the complete NSRAL Report Pipeline (Exec Summary + Peer Analysis)")
    parser.add_argument("--company", required=True, help="Exact Company Name (e.g., 'Tata Motors Limited')")
    parser.add_argument("--industry", default=None, help="Force Basic Industry (for companies missing from scores.csv)")
    parser.add_argument("--model", default="deepseek-r1:14b", help="Local Ollama model to use for narrative generation")
    args = parser.parse_args()

    import re
    company_safe = re.sub(r'[^a-zA-Z0-9]+', '_', args.company).strip('_')
    company_spaced = args.company

    # Derived paths based on company name
    exec_summary_json = f"data/reports/json_data/{company_safe}_Executive_Summary.json"
    peer_analysis_json = f"data/reports/json_data/{company_safe}_Peer_Analysis.json"
    peer_narrative_json = f"data/reports/json_data/{company_spaced}_Peer_Narrative.json"

    print(f"\n{'*'*60}")
    print(f"🏁 INITIATING FULL REPORT PIPELINE FOR: {args.company}")
    print(f"{'*'*60}\n")

    # ---------------------------------------------------------
    # Phase 1: Peer Analysis (Data Extraction)
    # ---------------------------------------------------------
    peer_analysis_cmd = ["python3", "scripts/report_generation/peer_analysis.py", "--company", args.company]
    if args.industry:
        peer_analysis_cmd.extend(["--industry", args.industry])
        
    run_step(peer_analysis_cmd, "Generate Peer Benchmarking Analysis (Data Processing)")

    # ---------------------------------------------------------
    # Phase 2: Executive Summary (LLM Narrative)
    # ---------------------------------------------------------
    run_step([
        "python3", "scripts/report_generation/generate_executive_summary.py",
        "--company", args.company,
        "--peer_analysis_path", peer_analysis_json,
        "--model", args.model
    ], "Generate Executive Summary (LLM Narrative)")

    run_step([
        "python3", "scripts/report_generation/generate_pdf_report.py",
        "--company", args.company,
        "--peer_analysis_path", peer_analysis_json,
        "--blocks", exec_summary_json
    ], "Generate Executive Summary (PDF)")

    # ---------------------------------------------------------
    # Phase 3: Peer Analysis Narrative & Charts
    # ---------------------------------------------------------
    run_step([
        "python3", "scripts/report_generation/generate_peer_report.py",
        "--company", args.company,
        "--peer_analysis_path", peer_analysis_json,
        "--model", args.model
    ], "Generate Peer Narrative & Charts (LLM + Seaborn)")

    run_step([
        "python3", "scripts/report_generation/json_to_pdf.py",
        "--json_path", peer_narrative_json
    ], "Generate Peer Analysis (PDF)")

    print(f"\n{'*'*60}")
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY FOR: {args.company}")
    print(f"Executive Summary PDF: data/reports/pdfs/{company_safe}_Executive_Summary.pdf")
    print(f"Peer Analysis PDF: data/reports/pdfs/{company_spaced}_Peer_Narrative.pdf")
    print(f"{'*'*60}\n")

if __name__ == "__main__":
    main()
