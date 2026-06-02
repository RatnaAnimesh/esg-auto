import pandas as pd
import json
import os

def parse_excel_tree(excel_path, sheet_name='Sheet2'):
    print(f"Parsing tree from {excel_path} (Sheet: {sheet_name})...")
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    # Forward fill to propagate the parent categories down the rows
    df_filled = df.ffill()
    
    hierarchy = {}
    leaf_nodes = set()
    
    for _, row in df_filled.iterrows():
        # Clean up nans
        row_vals = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() != 'nan']
        if not row_vals:
            continue
            
        # Build nested dictionary
        current_level = hierarchy
        for i, val in enumerate(row_vals):
            if val not in current_level:
                current_level[val] = {}
            # If it's the last element in this row, it's a leaf node for this path
            if i == len(row_vals) - 1:
                leaf_nodes.add(val)
            current_level = current_level[val]
            
    # Save the full hierarchy
    os.makedirs('data/reference', exist_ok=True)
    with open('data/reference/hierarchy/tree_hierarchy.json', 'w') as f:
        json.dump(hierarchy, f, indent=4)
        
    # Save the leaf nodes as a template for NIC mapping
    mapping_template = {node: [] for node in leaf_nodes}
    
    # If the mapping file already exists, don't overwrite existing mappings
    mapping_path = 'data/reference/mappings/tree_to_nic_mapping.json'
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            existing_mapping = json.load(f)
            for k, v in existing_mapping.items():
                if k in mapping_template:
                    mapping_template[k] = v
                    
    with open(mapping_path, 'w') as f:
        json.dump(mapping_template, f, indent=4)
        
    print(f"Extracted {len(leaf_nodes)} basic industries (leaf nodes).")
    print(f"Hierarchy saved to data/reference/hierarchy/tree_hierarchy.json")
    print(f"Mapping template saved to data/reference/mappings/tree_to_nic_mapping.json")
    
if __name__ == "__main__":
    parse_excel_tree('data/reference/hierarchy/nsral_sector_hierarchy.xlsx')
