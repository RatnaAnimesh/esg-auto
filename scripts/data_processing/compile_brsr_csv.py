import json
import glob
import os
import pandas as pd
import numpy as np
import re

def camel_to_space(text):
    # Insert space between lower/number and upper case letters
    return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)

def compile_metrics_to_csv():
    # Find all generated metric JSON files
    input_dir = 'data/raw/xbrl'
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = glob.glob(os.path.join(input_dir, '*_metrics.json'))
    
    all_companies_data = {}
    
    for file_path in json_files:
        print(f"Reading {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
            
        # Try to find the company name to use as row identifier
        company_name = None
        for item in metrics:
            if item['metric'] == 'NameOfTheCompany':
                company_name = item['value']
                break
                
        # Fallback to filename if no company name found
        if not company_name:
            company_name = os.path.basename(file_path).replace('_metrics.json', '')
            
        company_data = {}
        
        for item in metrics:
            metric_name = camel_to_space(item['metric'])
            val = item['value']
            
            ctx = item.get('context_details', {})
            dims = ctx.get('dimensions', {})
            
            col_parts = [metric_name]
            
            # Append dimensions to ensure uniqueness
            for dim_key, dim_val in dims.items():
                col_parts.append(camel_to_space(str(dim_val)))
                
            # Basic heuristic to flag "Previous Year" data based on period strings
            if 'context_id' in item and not ('CYMain' in item['context_id'] or 'CYMain' in item['context_id']):
                if 'PY' in item['context_id'] and not 'PPY' in item['context_id']:
                    col_parts.append('Previous Year')
                elif 'PPY' in item['context_id']:
                    col_parts.append('Prior Previous Year')
            
            # Join with a readable separator
            col_name = " - ".join(col_parts)
            
            # If multiple of the same column exists (rare, but possible), just take the last one or append
            company_data[col_name] = val
            
        all_companies_data[company_name] = company_data

    print(f"\nCompiling DataFrame for {len(all_companies_data)} companies...")
    
    # Create DataFrame from dictionary of dictionaries (orient='index')
    df = pd.DataFrame.from_dict(all_companies_data, orient='index')
    
    # Replace any empty strings or 'None' strings with actual np.nan
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    df.replace('None', np.nan, inplace=True)
    
    # Output to CSV
    output_file = os.path.join(output_dir, 'brsr_consolidated.csv')
    df.to_csv(output_file, index_label='CompanyName', na_rep='NaN')
    
    print(f"Successfully created CSV with shape {df.shape} at {output_file}")

if __name__ == "__main__":
    compile_metrics_to_csv()
