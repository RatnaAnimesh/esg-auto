import os
import glob
import pandas as pd
import numpy as np

def score_sector(sector_path):
    sector_name = os.path.basename(sector_path)
    safe_sector_name = sector_name.replace(' ', '_')
    csv_file = os.path.join(sector_path, f"{safe_sector_name}_brsr_consolidated.csv")
    
    if not os.path.exists(csv_file):
        return
        
    print(f"Scoring sector: {sector_name}...")
    
    # Read the consolidated file
    df = pd.read_csv(csv_file, index_col=0)
    
    if len(df) <= 2:
        print(f"  Not enough data in {sector_name} to score.")
        return
        
    # Extract Polarity row
    polarity_row = df.loc['Polarity'] if 'Polarity' in df.index else pd.Series(index=df.columns, dtype=object)
    
    # Isolate company data by dropping 'Industry Average' and 'Polarity' if they exist
    companies_df = df.drop(index=['Industry Average', 'Polarity'], errors='ignore')
    
    # Convert data to numeric
    numeric_df = companies_df.apply(pd.to_numeric, errors='coerce')
    
    # Initialize the scored dataframe
    scored_df = pd.DataFrame(index=numeric_df.index, columns=numeric_df.columns)
    
    for col in numeric_df.columns:
        series = numeric_df[col]
        
        # Skip columns that are entirely NaN or if the metric name contains "remarks"
        if series.isna().all() or 'remarks' in str(col).lower():
            scored_df[col] = np.nan
            continue
            
        polarity = str(polarity_row.get(col, 'positive')).strip().lower()
        if polarity == '' or polarity == 'nan':
            polarity = 'positive' # Default
            
        # Calculate percentiles (0 to 1)
        # Using method='min' means if multiple companies are tied (e.g. all have 0),
        # they all get the minimum rank. Alternatively, method='average' is standard.
        # Let's use method='average' to be fair on boolean ties.
        percentiles = series.rank(pct=True, method='average')
        
        # Scoring Logic
        scores = pd.Series(index=series.index, dtype=float)
        
        for idx, val in percentiles.items():
            if pd.isna(val):
                scores[idx] = np.nan
                continue
                
            if polarity == 'negative':
                # Less is better -> lower values get higher scores.
                # Since rank(pct=True) gives highest percentile to largest value,
                # we invert the thresholds.
                if val <= 0.10:
                    score = 5
                elif val <= 0.35:
                    score = 4
                elif val <= 0.70:
                    score = 3
                elif val <= 0.95:
                    score = 2
                else:
                    score = 1
            else:
                # Positive (More is better)
                if val >= 0.90:
                    score = 5
                elif val >= 0.65:
                    score = 4
                elif val >= 0.30:
                    score = 3
                elif val >= 0.05:
                    score = 2
                else:
                    score = 1
                    
            scores[idx] = score
            
        scored_df[col] = scores
        
    # Append Polarity row for reference
    scored_df = pd.concat([scored_df, pd.DataFrame([polarity_row])])
    
    # Save the output
    output_filename = f"{safe_sector_name}_brsr_scored.csv"
    output_path = os.path.join(sector_path, output_filename)
    scored_df.to_csv(output_path)
    print(f"  Saved scored matrix: {output_path}")

def main(base_dir='data/database/hierarchy'):
    for sector_name in os.listdir(base_dir):
        sector_path = os.path.join(base_dir, sector_name)
        if os.path.isdir(sector_path):
            score_sector(sector_path)

if __name__ == '__main__':
    main()
