import pandas as pd
import json
import os
import random

# Load the master BRSR database to get the comprehensive list of unique metrics
csv_path = "data/processed/consolidated/brsr_consolidated.csv"
print(f"Loading master database: {csv_path}")

df = pd.read_csv(csv_path, nrows=0) # Only read headers to save memory
columns = df.columns.tolist()

weights = {"E": {}, "S": {}, "G": {}}

for metric in columns:
    # Skip the index column
    if metric == "CompanyName":
        continue
        
    # Randomly assign to E, S, or G for the placeholder
    category = random.choice(["E", "S", "G"])
    # Placeholder weight of 1.0
    weights[category][metric] = 1.0

os.makedirs("data/weights", exist_ok=True)
with open("data/weights/sector_weights/Automotive.json", "w") as f:
    json.dump(weights, f, indent=4)

total_metrics = sum(len(v) for v in weights.values())
print(f"Successfully created data/weights/sector_weights/Automotive.json with placeholder weights for {total_metrics} unique metrics.")
