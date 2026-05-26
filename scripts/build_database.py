import os
import pandas as pd
import re

def sanitize_filename(name):
    name = str(name).strip()
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def build_database():
    csv_path = 'data/processed/brsr_consolidated.csv'
    companies_dir = 'data/database/companies'
    sectors_dir = 'data/database/sectors'
    
    os.makedirs(companies_dir, exist_ok=True)
    os.makedirs(sectors_dir, exist_ok=True)
    
    print(f"Loading master CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Identify the NIC Code column
    sector_col = None
    for col in df.columns:
        if 'NIC' in col.upper() and 'CODE' in col.upper() and 'PRODUCT' in col.upper():
            sector_col = col
            break
            
    # Load official NIC 2008 mapping
    import json
    mapping_path = 'data/reference/nic_2008_mapping.json'
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            nic_mapping = json.load(f)
    else:
        nic_mapping = {}

    if not sector_col:
        print("Warning: Could not find NIC Code column. Grouping all into 'Unknown_Sector'.")
        df['Sector_Group'] = 'Unknown_Sector'
    else:
        # Standardize sector names using the official MoSPI 2-digit divisions
        def get_sector_name(nic_val):
            nic_str = str(nic_val).replace('.0', '').strip()
            if not nic_str.isdigit():
                return "Unknown_Sector"
            
            # NIC codes are 5 digits. The first 2 digits represent the Division.
            division = nic_str[:2]
            
            if division in nic_mapping:
                return nic_mapping[division]
            return f"Sector_NIC_{division}"
            
        df['Sector_Group'] = df[sector_col].apply(get_sector_name)
        
    print(f"Creating individual files for {len(df)} companies...")
    for idx, row in df.iterrows():
        company_name = row['CompanyName']
        safe_name = sanitize_filename(company_name)
        
        # Save transposed for easier LLM reading (Metric Name | Value)
        # Drop NaNs to save space and context window
        company_df = pd.DataFrame(row).dropna()
        company_df.columns = ['Value']
        company_df.index.name = 'Metric'
        
        out_path = os.path.join(companies_dir, f"{safe_name}.csv")
        company_df.to_csv(out_path)
        
    print(f"Creating sector files...")
    # Group by sector and save standard wide format for the sector groups
    grouped = df.groupby('Sector_Group')
    for sector_name, group_df in grouped:
        safe_sector = sanitize_filename(sector_name)
        out_path = os.path.join(sectors_dir, f"{safe_sector}.csv")
        
        # Drop columns that are entirely NaN for this sector to save space
        group_df_cleaned = group_df.dropna(axis=1, how='all')
        group_df_cleaned.to_csv(out_path, index=False)
        
    print(f"Database build complete.")
    print(f" - Saved {len(df)} company files to {companies_dir}/")
    print(f" - Saved {len(grouped)} sector files to {sectors_dir}/")

if __name__ == "__main__":
    build_database()
