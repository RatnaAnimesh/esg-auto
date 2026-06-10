import pandas as pd
import numpy as np
import json
import os
import argparse

def process_weights(excel_path, output_dir, industries_to_process=None):
    """
    Reads a master Excel file containing Pillar -> Theme -> Question mapping with base weights.
    For each Basic Industry, it redistributes the weight of dropped (0) questions to the other 
    active themes within the same pillar proportionally.
    """
    print(f"Loading master schema from: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # Required base columns
    base_cols = ['Pillar', 'Theme', 'Question', 'Base_Weight', 'Polarity']
    for c in base_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column '{c}' in the Excel file.")
            
    # Identify basic industry columns (everything that is not a base column)
    industry_cols = [c for c in df.columns if c not in base_cols]
    
    if industries_to_process:
        industry_cols = [c for c in industry_cols if c in industries_to_process]
        
    os.makedirs(output_dir, exist_ok=True)
    
    for industry in industry_cols:
        print(f"\nProcessing Industry: {industry}")
        ind_df = df.copy()
        
        # 1. Filter out dropped questions for this industry
        # The column contains 1 if active, 0 if dropped.
        ind_df['is_active'] = ind_df[industry].fillna(0).astype(int)
        
        final_weights = {}
        
        # Group by Pillar
        for pillar, pillar_df in ind_df.groupby('Pillar'):
            # Calculate original baseline weights
            theme_base_weights = pillar_df.groupby('Theme')['Base_Weight'].sum().to_dict()
            total_pillar_base_weight = sum(theme_base_weights.values())
            
            # Identify active and unallocated weights per theme
            theme_active_weights = {}
            unallocated_pillar_weight = 0.0
            
            for theme, theme_df in pillar_df.groupby('Theme'):
                # Sum weights of active questions in this theme
                active_q_df = theme_df[theme_df['is_active'] == 1]
                active_sum = active_q_df['Base_Weight'].sum()
                theme_active_weights[theme] = active_sum
                
                # The weight dropped from this theme (questions marked 0)
                original_sum = theme_base_weights[theme]
                dropped_weight = original_sum - active_sum
                unallocated_pillar_weight += dropped_weight
                
            # Which themes are still alive (have at least 1 active question)?
            alive_themes = {t: w for t, w in theme_base_weights.items() if theme_active_weights[t] > 0}
            total_alive_base_weight = sum(alive_themes.values())
            
            if total_alive_base_weight == 0:
                print(f"  Warning: Pillar '{pillar}' has NO active themes for industry '{industry}'.")
                continue
                
            # Redistribute the unallocated weight PROPORTIONALLY among the ALIVE themes
            # based on their original base weights.
            theme_final_targets = {}
            for theme in theme_active_weights.keys():
                if theme in alive_themes:
                    proportion = alive_themes[theme] / total_alive_base_weight
                    bonus_weight = unallocated_pillar_weight * proportion
                    theme_final_targets[theme] = theme_active_weights[theme] + bonus_weight
                else:
                    theme_final_targets[theme] = 0.0
            
            # Now distribute each theme's final target weight to its active questions proportionally
            for theme, theme_df in pillar_df.groupby('Theme'):
                if theme_final_targets[theme] == 0:
                    continue # No active questions
                    
                active_q_df = theme_df[theme_df['is_active'] == 1]
                active_base_sum = active_q_df['Base_Weight'].sum()
                
                for _, row in active_q_df.iterrows():
                    question = row['Question']
                    base_q_weight = row['Base_Weight']
                    
                    # Proportional weight inside the theme
                    q_proportion = base_q_weight / active_base_sum if active_base_sum > 0 else 0
                    final_q_weight = q_proportion * theme_final_targets[theme]
                    
                    final_weights[question] = round(final_q_weight, 6)
                    
        # Verify conservation of mass (weights)
        total_final = sum(final_weights.values())
        total_original = df['Base_Weight'].sum()
        
        print(f"  Original Total Weight: {total_original:.4f} | Final Total Weight: {total_final:.4f}")
        if not np.isclose(total_original, total_final, atol=1e-4):
            print(f"  WARNING: Weight mismatch for {industry}!")
            
        # Save output JSON in the exact format required by NSRAL
        json_payload = {
            "__RMSE__": 0.0, # Placeholder for deterministic
            "__MSE__": 0.0
        }
        json_payload.update(final_weights)
        
        safe_industry = str(industry).replace(' ', '_').replace('/', '_')
        out_path = os.path.join(output_dir, f"{safe_industry}.json")
        with open(out_path, 'w') as f:
            json.dump(json_payload, f, indent=4)
            
    print(f"\nSuccessfully generated redistributed weight schemas in '{output_dir}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redistribute Pillar->Theme->Question weights dynamically.")
    parser.add_argument("--master_weights", type=str, required=True, help="Path to master Excel file containing mappings.")
    parser.add_argument("--output_dir", type=str, default="data/weights/sector_weights/extracted_industries", help="Output directory for generated JSONs.")
    args = parser.parse_args()
    
    process_weights(args.master_weights, args.output_dir)
