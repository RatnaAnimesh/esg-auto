import argparse
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler
import os
import re
import difflib

def main():
    parser = argparse.ArgumentParser(description="Run Peer Benchmarking Analysis for a given company")
    parser.add_argument("--company", type=str, required=True, help="Exact Company Name")
    parser.add_argument("--industry", type=str, default=None, help="Force Basic Industry (useful for unclassified companies)")
    parser.add_argument("--top_n", type=int, default=30, help="Number of top metrics to analyze")
    args = parser.parse_args()
    
    target_company = args.company
    
    print(f"Loading datasets for {target_company}...")
    brsr_df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv', low_memory=False)
    scores_df = pd.read_csv('data/reference/scores/nsral_scores_full.csv')
    
    brsr_df['clean_name'] = brsr_df['CompanyName'].astype(str).str.strip().str.lower()
    scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()
    
    
    # Do not inner join if we might need unclassified companies. Just keep BRSR data.
    if args.industry:
        # If industry is forced, we don't need inner join with scores to find it.
        # But we DO need the peers! Wait, if we don't inner join, peers won't have Basic Industry either unless we merge.
        # So let's merge with left join to keep target company, or just merge to get peers' industries.
        pass
        
    merged_df = pd.merge(brsr_df, scores_df[['clean_name', 'Basic Industry']], on='clean_name', how='left')
    
    # Find the target company
    company_row = merged_df[merged_df['clean_name'] == target_company.lower().strip()]
    
    if company_row.empty:
        print(f"Error: Company '{target_company}' not found in the BRSR dataset.")
        return
        
    basic_industry = args.industry
    if not basic_industry:
        if 'Basic Industry' in company_row.columns and not pd.isna(company_row.iloc[0].get('Basic Industry')):
            basic_industry = company_row.iloc[0]['Basic Industry']
        else:
            print(f"Error: 'Basic Industry' is missing for '{target_company}'. Please provide it via --industry.")
            return
    else:
        # Inject the forced industry into the target company's row so it is part of the peer group calculation
        merged_df.loc[merged_df['clean_name'] == target_company.lower().strip(), 'Basic Industry'] = basic_industry
        company_row = merged_df[merged_df['clean_name'] == target_company.lower().strip()]
            
    print(f"Target Company using Basic Industry: {basic_industry}")
    
    # Load the corresponding weight file
    safe_industry = re.sub(r'[^a-zA-Z0-9]+', '_', basic_industry)
    weight_path = f"data/weights/sector_weights/extracted_industries/{safe_industry}.json"
    
    if not os.path.exists(weight_path):
        print(f"Error: Weight file for industry '{basic_industry}' not found at {weight_path}")
        return
        
    with open(weight_path, 'r') as f:
        industry_weights = json.load(f)
        
    # Remove structural JSON keys for ranking
    for key in ['__Base_Score__', '__RMSE__', '__MSE__']:
        if key in industry_weights:
            del industry_weights[key]
        
    # Sort metrics by absolute weight
    sorted_metrics = sorted(industry_weights.items(), key=lambda item: abs(item[1]), reverse=True)
    top_metrics = sorted_metrics[:args.top_n]
    
    print(f"\nTop {args.top_n} drivers identified for {basic_industry}:")
    for metric, weight in top_metrics:
        print(f"  - {metric} (Weight: {weight})")
        
    # Filter dataset for peers
    peers_df = merged_df[merged_df['Basic Industry'] == basic_industry]
    print(f"\nFound {len(peers_df)} companies in {basic_industry} for peer benchmarking.")
    
    analysis_results = []
    
    # Exclude non-numeric processing errors
    for metric, weight in top_metrics:
        if metric not in peers_df.columns:
            continue
            
        # Convert to numeric, coercing errors
        peers_df[metric] = pd.to_numeric(peers_df[metric], errors='coerce')
        
        peer_mean = peers_df[metric].mean()
        peer_median = peers_df[metric].median()
        
        target_val = pd.to_numeric(company_row.iloc[0][metric], errors='coerce')
        
        # Determine if the target is outperforming or underperforming
        # If weight is positive, higher is better. If negative, lower is better.
        diff = target_val - peer_mean
        if pd.isna(diff):
            status = "N/A"
        elif weight > 0:
            status = "Outperforming" if diff > 0 else "Underperforming"
        else:
            status = "Outperforming" if diff < 0 else "Underperforming"
            
        # Create peer values dict mapping clean_name to value, filtering out NaNs
        peer_values = {}
        for idx, row in peers_df.iterrows():
            peer_val = pd.to_numeric(row[metric], errors='coerce')
            if not pd.isna(peer_val):
                # Use original name if available, else clean_name
                peer_name = row.get('CompanyName', row['clean_name'])
                if pd.isna(peer_name):
                    peer_name = row['clean_name']
                # Capitalize it nicely
                if isinstance(peer_name, str):
                    peer_name = peer_name.title()
                peer_values[peer_name] = float(round(peer_val, 4))
            
        analysis_results.append({
            "Metric": metric,
            "Linear_Weight": weight,
            "Target_Company_Value": float(round(target_val, 4)) if not pd.isna(target_val) else None,
            "Industry_Average": float(round(peer_mean, 4)) if not pd.isna(peer_mean) else None,
            "Industry_Median": float(round(peer_median, 4)) if not pd.isna(peer_median) else None,
            "Status": status,
            "Peer_Values": peer_values
        })
        
    # Generate Output
    os.makedirs('data/reports/json_data', exist_ok=True)
    os.makedirs('data/reports/pdfs', exist_ok=True)
    os.makedirs('data/reports/charts', exist_ok=True)
    #, exist_ok=True)
    safe_company_name = re.sub(r'[^a-zA-Z0-9]+', '_', target_company)
    
    # -----------------------------------------------------
    # Dynamically Calculate Predicted ESG Score using NNLS
    # -----------------------------------------------------
    numeric_cols = list(industry_weights.keys())
    
    # Apply MinMaxScaler strictly to the peer group to match extraction logic
    # Recreate the exact scaler used during weight extraction
    training_merged = pd.merge(brsr_df, scores_df, on='clean_name', how='inner')
    
    # Match the basic_industry to the training data name using difflib
    training_col = 'Basic Industry_x' if 'Basic Industry_x' in training_merged.columns else 'Basic Industry'
    unique_industries = training_merged[training_col].dropna().unique().tolist()
    
    training_group = None
    matches = difflib.get_close_matches(basic_industry, unique_industries, n=1, cutoff=0.6)
    
    if matches:
        matched_industry = matches[0]
        print(f"Matched '{basic_industry}' to training industry '{matched_industry}'")
        training_group = training_merged[training_merged[training_col] == matched_industry]
            
    scaler = MinMaxScaler(feature_range=(0, 100))
    if training_group is not None and not training_group.empty:
        scaler.fit(training_group[numeric_cols].fillna(0).values)
    else:
        scaler.fit(peers_df[numeric_cols].fillna(0).values)
        
    # Get the target company's scaled row
    target_raw = company_row[numeric_cols].fillna(0).values
    try:
        target_scaled = scaler.transform(target_raw)[0]
    except:
        target_scaled = target_raw[0]
        
    # Handle min==max case where scaler sets values to 0. 
    for idx in range(len(target_scaled)):
        if scaler.data_min_[idx] == scaler.data_max_[idx]:
            # Feature was constant in training set, meaning NNLS had no variance to fit.
            # But if it extracted a weight, we just give it 100 if the target has it.
            target_scaled[idx] = 100.0 if target_raw[0][idx] > 0 else 0.0
    
    weights_array = np.array([industry_weights[col] for col in numeric_cols])
    
    # Calculate mathematically predicted Total Score
    total_score = float(np.dot(target_scaled, weights_array))
    
    # Classify sub-scores
    e_kw = ['emission', 'energy', 'water', 'waste', 'environment', 'climate', 'scope', 'renewable', 'fuel']
    s_kw = ['employee', 'turnover', 'training', 'worker', 'injury', 'health', 'safety', 'maternity', 'paternity', 'social', 'community', 'diversity', 'women', 'hiring', 'attrition']
    
    e_w, s_w, g_w = 0.0, 0.0, 0.0
    e_v, s_v, g_v = 0.0, 0.0, 0.0
    
    for i, col in enumerate(numeric_cols):
        lower_col = col.lower()
        w = weights_array[i]
        v = target_scaled[i]
        
        cat = 'G'
        if any(k in lower_col for k in e_kw): cat = 'E'
        elif any(k in lower_col for k in s_kw): cat = 'S'
        
        if cat == 'E': 
            e_w += w; e_v += w * v
        elif cat == 'S': 
            s_w += w; s_v += w * v
        else: 
            g_w += w; g_v += w * v
            
    # Sub-scores are weighted averages scaled to 100 assuming the sub-weights map to max available
    # Wait, the NNLS total score maps to 0-100 directly. 
    # To find E_score, S_score, G_score out of 100, we find the weighted average of the scaled features (0-100)
    e_score = float(e_v / e_w) if e_w > 0 else 0.0
    s_score = float(s_v / s_w) if s_w > 0 else 0.0
    g_score = float(g_v / g_w) if g_w > 0 else 0.0

    # FALLBACK: If NNLS dropped an entire pillar (0 weight), calculate it using equal-weighted average of ALL available metrics for that pillar
    if e_w == 0.0 or s_w == 0.0 or g_w == 0.0:
        all_num_cols = [c for c in brsr_df.columns if c not in ['clean_name', 'CompanyName', 'Name Of The Company', 'Sector', 'Basic Industry'] and pd.api.types.is_numeric_dtype(brsr_df[c])]
        scaler_all = MinMaxScaler(feature_range=(0, 100))
        if training_group is not None and not training_group.empty:
            scaler_all.fit(training_group[all_num_cols].fillna(0).values)
        else:
            scaler_all.fit(peers_df[all_num_cols].fillna(0).values)
            
        target_raw_all = company_row[all_num_cols].fillna(0).values
        try:
            target_scaled_all = scaler_all.transform(target_raw_all)[0]
        except:
            target_scaled_all = target_raw_all[0]
            
        for idx in range(len(target_scaled_all)):
            if scaler_all.data_min_[idx] == scaler_all.data_max_[idx]:
                target_scaled_all[idx] = 100.0 if target_raw_all[0][idx] > 0 else 0.0
                
        fallback_e, fallback_s, fallback_g = [], [], []
        for i, col in enumerate(all_num_cols):
            lower_col = col.lower()
            cat = 'G'
            if any(k in lower_col for k in e_kw): cat = 'E'
            elif any(k in lower_col for k in s_kw): cat = 'S'
            
            if cat == 'E': fallback_e.append(target_scaled_all[i])
            elif cat == 'S': fallback_s.append(target_scaled_all[i])
            else: fallback_g.append(target_scaled_all[i])
            
        if e_w == 0.0 and fallback_e: e_score = float(np.mean(fallback_e))
        if s_w == 0.0 and fallback_s: s_score = float(np.mean(fallback_s))
        if g_w == 0.0 and fallback_g: g_score = float(np.mean(fallback_g))
    
    # Save as JSON
    json_out_path = f"data/reports/json_data/{safe_company_name}_Peer_Analysis.json"
    with open(json_out_path, 'w') as f:
        json.dump({
            "Company": target_company,
            "Basic_Industry": basic_industry,
            "Peer_Count": len(peers_df),
            "Predicted_ESG_Score": round(total_score, 1),
            "Predicted_E_Score": round(e_score, 1),
            "Predicted_S_Score": round(s_score, 1),
            "Predicted_G_Score": round(g_score, 1),
            "Analysis": analysis_results
        }, f, indent=4)
        
    # Save as CSV
    csv_out_path = f"data/reports/csv/{safe_company_name}_Peer_Analysis.csv"
    results_df = pd.DataFrame(analysis_results)
    results_df.to_csv(csv_out_path, index=False)
    
    print(f"\nReports successfully generated:")
    print(f" - {json_out_path}")
    print(f" - {csv_out_path}")

if __name__ == "__main__":
    main()
