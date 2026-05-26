import pandas as pd
import json
import os

def build_leaf_paths(hierarchy, current_path=""):
    paths = {}
    for key, value in hierarchy.items():
        new_path = os.path.join(current_path, key) if current_path else key
        if not value: # It's a leaf node
            paths[key] = new_path
        else:
            # Recurse
            paths.update(build_leaf_paths(value, new_path))
    return paths

def build_hierarchical_db():
    print("Loading tree hierarchy and mappings...")
    
    with open('data/reference/tree_hierarchy.json', 'r') as f:
        hierarchy = json.load(f)
        
    with open('data/reference/tree_to_nic_mapping.json', 'r') as f:
        nic_mapping = json.load(f)
        
    leaf_paths = build_leaf_paths(hierarchy)
    
    # Invert mapping: NIC Code -> Leaf Node Path
    nic_to_path = {}
    for leaf_node, nic_codes in nic_mapping.items():
        path = leaf_paths.get(leaf_node, leaf_node)
        for code in nic_codes:
            nic_to_path[str(code)] = path
            
    print("Loading master consolidated CSV...")
    csv_path = 'data/processed/brsr_consolidated.csv'
    if not os.path.exists(csv_path):
        print("Error: Master CSV not found.")
        return
        
    df = pd.read_csv(csv_path)
    
    # Find NIC column
    sector_col = None
    for col in df.columns:
        if 'NIC' in col.upper():
            sector_col = col
            break
            
    # Find COMPANY column
    company_col = None
    for col in df.columns:
        if 'COMPANY' in col.upper():
            company_col = col
            break
            
    base_out_dir = 'data/database/hierarchy'
    
    print("Building deeply nested folder structure...")
    success_count = 0
    unclassified_count = 0
    
    for idx, row in df.iterrows():
        company_name = str(row[company_col]).strip().replace('/', '_') if company_col else f"Company_{idx}"
        if not company_name or company_name == 'nan':
            continue
            
        nic_val = str(row[sector_col]).replace('.0', '').strip() if sector_col else ""
        
        # Determine path
        if nic_val in nic_to_path:
            out_dir = os.path.join(base_out_dir, nic_to_path[nic_val])
            success_count += 1
        else:
            out_dir = os.path.join(base_out_dir, 'Unclassified')
            unclassified_count += 1
            
        os.makedirs(out_dir, exist_ok=True)
        
        # Transpose company data and drop NaNs
        company_data = row.to_frame(name='Value')
        company_data.index.name = 'Metric'
        company_data_clean = company_data.dropna()
        
        out_file = os.path.join(out_dir, f"{company_name}.csv")
        company_data_clean.to_csv(out_file)
        
    print(f"\nHierarchical database build complete!")
    print(f" - Mapped correctly to tree: {success_count} companies")
    print(f" - Unclassified (NIC not in map): {unclassified_count} companies")

if __name__ == "__main__":
    build_hierarchical_db()
