import os
import glob
import pandas as pd
import numpy as np

def generate_sector_masters(base_dir='data/database/hierarchy'):
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found.")
        return

    # Iterate over sector directories
    for sector_name in os.listdir(base_dir):
        sector_path = os.path.join(base_dir, sector_name)
        
        # Skip if not a directory
        if not os.path.isdir(sector_path):
            continue
            
        print(f"Processing sector: {sector_name}...")
        
        # Find all CSV files recursively in this sector
        csv_files = glob.glob(os.path.join(sector_path, '**/*.csv'), recursive=True)
        
        # Filter out existing consolidated files
        csv_files = [f for f in csv_files if not f.endswith('_brsr_consolidated.csv')]
        
        if not csv_files:
            print(f"  No company CSVs found in {sector_name}. Skipping.")
            continue
            
        # List to hold each company's data
        company_records = []
        
        for csv_file in csv_files:
            try:
                # Read the CSV (Metric, Value)
                df = pd.read_csv(csv_file)
                if 'Metric' not in df.columns or 'Value' not in df.columns:
                    print(f"  Warning: {csv_file} does not have expected Metric/Value columns.")
                    continue
                    
                # Create a Series with Metric as index
                # Drop duplicates if any metric appears twice
                df = df.drop_duplicates(subset=['Metric'])
                series = df.set_index('Metric')['Value']
                
                # Get company name from file or data
                company_name = os.path.basename(csv_file).replace('.csv', '')
                if 'CompanyName' in series:
                    company_name = series['CompanyName']
                    
                series.name = company_name
                company_records.append(series)
                
            except Exception as e:
                print(f"  Error reading {csv_file}: {e}")
                
        if not company_records:
            print(f"  No valid data extracted for {sector_name}.")
            continue
            
        # Combine all company records into a single DataFrame
        # Rows = Companies, Columns = Metrics
        sector_df = pd.DataFrame(company_records)
        
        print(f"  Combined data for {len(sector_df)} companies.")
        
        import re
        
        def clean_cell(val):
            if pd.isna(val) or val == '':
                return val
                
            if isinstance(val, (int, float, bool)):
                return val
                
            s = str(val)
            
            # Text normalization: replace newlines with space, collapse multiple spaces, strip
            s = re.sub(r'[\r\n]+', ' ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            
            # Handle Percentages
            if re.match(r'^-?[\d,]+(\.\d+)?\s*%$', s):
                num_str = s.replace('%', '').replace(',', '').strip()
                try:
                    return float(num_str) / 100.0
                except ValueError:
                    pass
            
            # Numeric Cleaning: Handle currencies and commas
            # Match strings that are numbers but might have prefixes/suffixes
            # e.g., "Rs. 1,000", "₹ 500.50", "1,000,000"
            currency_pattern = r'^(?:Rs\.?|INR|₹|\$)?\s*(-?[\d,]+(\.\d+)?)\s*(?:/-)?$'
            match = re.match(currency_pattern, s, re.IGNORECASE)
            if match:
                num_str = match.group(1).replace(',', '')
                try:
                    return float(num_str)
                except ValueError:
                    pass
                    
            return s
            
        sector_df = sector_df.applymap(clean_cell)
        
        # Advanced boolean mapping per column to handle sentences and fill empty fields with 0
        def process_column(col):
            is_bool_col = False
            new_col = []
            for val in col:
                if pd.isna(val) or val == '':
                    new_col.append(np.nan)
                    continue
                
                if isinstance(val, bool):
                    new_col.append(1 if val else 0)
                    is_bool_col = True
                    continue
                
                if isinstance(val, (int, float)):
                    new_col.append(val)
                    continue
                
                s = str(val).strip().lower()
                if s in ['yes', 'true', 'y']:
                    new_col.append(1)
                    is_bool_col = True
                    continue
                if s in ['no', 'false', 'n']:
                    new_col.append(0)
                    is_bool_col = True
                    continue
                
                # Check for sentences starting with or containing 'yes ' / 'no '
                if 'yes, ' in s or 'yes ' in s or s.startswith('yes-') or s.startswith('yes.') or s.endswith(' yes'):
                    new_col.append(1)
                    is_bool_col = True
                    continue
                if 'no, ' in s or 'no ' in s or s.startswith('no-') or s.startswith('no.') or s.endswith(' no'):
                    new_col.append(0)
                    is_bool_col = True
                    continue
                if 'true, ' in s or 'true ' in s or s.startswith('true-') or s.startswith('true.') or s.endswith(' true'):
                    new_col.append(1)
                    is_bool_col = True
                    continue
                if 'false, ' in s or 'false ' in s or s.startswith('false-') or s.startswith('false.') or s.endswith(' false'):
                    new_col.append(0)
                    is_bool_col = True
                    continue
                
                new_col.append(val)
                
            new_series = pd.Series(new_col, index=col.index)
            if is_bool_col:
                new_series = new_series.fillna(0)
            return new_series

        mapped_df = sector_df.apply(process_column, axis=0)
        
        # We need to calculate Industry Average.
        # To do this safely, we convert columns to numeric where possible.
        numeric_df = mapped_df.apply(pd.to_numeric, errors='coerce')
        
        # Calculate mean for numeric columns, returning NaN for columns that are entirely non-numeric
        industry_avg = numeric_df.mean(skipna=True)
        
        # Prepare the Industry Average row. It will have NaN for string columns.
        # We can fill NaNs with empty string or leave as NaN.
        industry_avg.name = 'Industry Average'
        
        # Prepare the Polarity row
        polarity = pd.Series(index=sector_df.columns, dtype=object)
        polarity.name = 'Polarity'
        polarity[:] = '' # Placeholder for manual entry or future LLM filling
        
        # Append the new rows
        # The user requested: "last row is going to be the industry average... except the polarity row, or you can make the polarity row the last one"
        # We'll add Industry Average, then Polarity.
        sector_df = pd.concat([sector_df, pd.DataFrame([industry_avg, polarity])])
        
        # Save to the sector root folder
        output_filename = f"{sector_name}_brsr_consolidated.csv"
        # Replace spaces in filename with underscores if desired, or leave as is. User said "foldername_brsr_consolidated.csv"
        # Let's clean the sector name slightly if it has spaces, or just use exactly foldername
        safe_sector_name = sector_name.replace(' ', '_')
        output_path = os.path.join(sector_path, f"{safe_sector_name}_brsr_consolidated.csv")
        
        # Add index label as 'Company'
        sector_df.index.name = 'Company'
        
        sector_df.to_csv(output_path)
        print(f"  Saved {output_path}")

if __name__ == '__main__':
    generate_sector_masters()
