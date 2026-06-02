import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from scipy.optimize import nnls
from sklearn.metrics import mean_squared_error
import json
import os
import re

os.makedirs('data/weights/sector_weights/extracted_industries', exist_ok=True)
os.makedirs('data/weights/sector_weights/extracted_sectors', exist_ok=True)

# ---------------------------------------------------------
# 1. DATA PREPARATION
# ---------------------------------------------------------
print("Loading datasets for Linear Weight Extraction...")
brsr_df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv', low_memory=False)
scores_df = pd.read_csv('data/reference/scores/nsral_scores_full.csv')

brsr_df['clean_name'] = brsr_df['CompanyName'].astype(str).str.strip().str.lower()
scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()

merged_df = pd.merge(brsr_df, scores_df, on='clean_name', how='inner')

exclude_cols = ['clean_name', 'CompanyName', 'Company Name', 'Sector', 'Basic Industry', 'ESG Ratings', 'Last Updated on']
numeric_cols = [c for c in brsr_df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(brsr_df[c])]

print(f"Total Companies: {len(merged_df)} | Numeric Features: {len(numeric_cols)}")

all_rmses = []

# ---------------------------------------------------------
# 2. FEATURE IMPORTANCE EXTRACTION LOOP
# ---------------------------------------------------------
def extract_weights_for_group(group_col, output_dir):
    valid_groups = merged_df[group_col].dropna().unique().tolist()
    print(f"\\nExtracting JSON weights for {len(valid_groups)} {group_col}s...")
    
    for group_val in valid_groups:
        group_df = merged_df[merged_df[group_col] == group_val].copy()
        
        X_raw = group_df[numeric_cols].fillna(0).values
        y_raw = group_df['ESG Ratings'].values.astype(np.float32).reshape(-1, 1)
        
        # Use MinMaxScaler to ensure pure weighted sum (0-100) mathematically aligns with final ESG score
        scaler = MinMaxScaler(feature_range=(0, 100))
        try:
            X_scaled = scaler.fit_transform(X_raw)
        except:
            X_scaled = X_raw # Fallback if scaling fails on 1 sample
        
        # NNLS finds the mathematically optimal strictly positive weights with NO intercept
        weights, rnorm = nnls(X_scaled, y_raw.flatten())
        extracted_weights = weights
        
        # Calculate evaluation metrics based on pure proportional dot product
        y_pred = X_scaled.dot(extracted_weights)
        mse = float(mean_squared_error(y_raw.flatten(), y_pred))
        rmse = float(np.sqrt(mse))
        all_rmses.append(rmse)
        
        json_weights = {
            "__RMSE__": round(rmse, 4),
            "__MSE__": round(mse, 4)
        }
        
        active_count = 0
        for idx, col_name in enumerate(numeric_cols):
            w = float(extracted_weights[idx])
            if w > 0.0:  # Only save non-zero importances to keep files manageable
                json_weights[col_name] = round(w, 6)
                active_count += 1
                
        safe_group_val = re.sub(r'[^a-zA-Z0-9]+', '_', group_val)
        file_path = f'{output_dir}/{safe_group_val}.json'
        
        with open(file_path, 'w') as f:
            json.dump(json_weights, f, indent=4)

extract_weights_for_group('Basic Industry', 'data/weights/sector_weights/extracted_industries')

print(f"\nExtracting JSON weights for {len(merged_df['Sector'].dropna().unique())} Sectors...")
extract_weights_for_group('Sector', 'data/weights/sector_weights/extracted_sectors')

if all_rmses:
    print(f"\nAverage RMSE across all runs: {np.mean(all_rmses):.4f}")
