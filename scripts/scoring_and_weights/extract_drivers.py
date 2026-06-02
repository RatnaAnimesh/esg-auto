import argparse
import pandas as pd
import json
import sys
import os

def format_large_number(num):
    if num >= 1e12:
        return f"{num / 1e12:.2f} Trillion"
    elif num >= 1e9:
        return f"{num / 1e9:.2f} Billion"
    elif num >= 1e6:
        return f"{num / 1e6:.2f} Million"
    elif num >= 1e3:
        return f"{num / 1e3:.2f} Thousand"
    else:
        return str(num)

def main():
    parser = argparse.ArgumentParser(description="Deterministic Driver Engine")
    parser.add_argument("--company_name", type=str, required=True, help="Exact name of the company")
    parser.add_argument("--industry", type=str, default="Automotive", help="Basic Industry of the company")
    parser.add_argument("--output", type=str, default="data/processed/metadata/top_drivers.json", help="Output JSON path")
    args = parser.parse_args()

    db_path = "data/processed/consolidated/brsr_consolidated.csv"
    print(f"Loading master database from {db_path}...")
    try:
        df = pd.read_csv(db_path, low_memory=False)
    except FileNotFoundError:
        print("Error: Master database brsr_consolidated.csv not found.")
        sys.exit(1)
        
    company_row = df[(df['Name Of The Company'] == args.company_name) | (df['CompanyName'] == args.company_name)]
    if company_row.empty:
        print(f"Error: Could not find data for {args.company_name} in the master database.")
        sys.exit(1)

    weights_path = f"data/weights/sector_weights/{args.industry}.json"
    print(f"Loading industry weights from {weights_path}...")
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
    except FileNotFoundError:
        print(f"Error: Weights file {weights_path} not found.")
        sys.exit(1)

    # Convert the company's row into a dictionary of {ColumnName: Value}
    metrics = {}
    row_data = company_row.iloc[0].to_dict()
    for col_name, val in row_data.items():
        if col_name == 'CompanyName':
            continue
        try:
            metrics[col_name] = float(val)
        except (ValueError, TypeError):
            continue # Skip non-numeric values for the impact score calculation

    top_drivers = {"E": [], "S": [], "G": []}

    print("Calculating Impact Scores...")
    for category in ["E", "S", "G"]:
        impact_scores = []
        for metric, weight in weights[category].items():
            if metric in metrics:
                val = metrics[metric]
                # Impact Score = Value * Weight
                # Since placeholder weights are 1.0, impact is just the value
                impact = val * weight
                impact_scores.append((metric, impact, format_large_number(val)))
        
        # Sort by absolute impact to find the most significant drivers (positive or negative)
        impact_scores.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Take the top 5
        top_5 = impact_scores[:5]
        for item in top_5:
            top_drivers[category].append({
                "metric_name": item[0],
                "impact_score": item[1],
                "raw_value": item[2]
            })

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(top_drivers, f, indent=4)
        
    print(f"\\nTop Drivers isolated and saved to {args.output}")
    print("E Drivers:", [d['metric_name'] for d in top_drivers['E'][:2]])

if __name__ == "__main__":
    main()
