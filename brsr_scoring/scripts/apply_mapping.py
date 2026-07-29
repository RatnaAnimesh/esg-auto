import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def apply_mapping():
    print("Reading audited mapping_review.csv...")
    review_file = BASE_DIR / "config" / "mapping_review.csv"
    if not review_file.exists():
        print(f"Error: {review_file} not found. Run map_questions.py first.")
        return
        
    df = pd.read_csv(review_file)
    
    print("Reading base taxonomy_map_full.json...")
    base_tax_file = BASE_DIR / "config" / "taxonomy_map_full.json"
    with open(base_tax_file, 'r') as f:
        base_taxonomy = json.load(f)
        
    # Build lookup for data types based on question_id
    id_to_meta = {}
    for q_text, meta in base_taxonomy.items():
        id_to_meta[meta['question_id']] = meta
        
    final_taxonomy = {}
    
    print("Building final taxonomy_map.json...")
    for _, row in df.iterrows():
        q_id = row['question_id']
        csv_column = row['final_selected_column']
        
        if pd.isna(csv_column) or str(csv_column).strip() == "":
            print(f"Warning: Question {q_id} has no mapped column. Skipping.")
            continue
            
        meta = id_to_meta[q_id]
        final_taxonomy[csv_column] = meta
        
    out_file = BASE_DIR / "config" / "taxonomy_map.json"
    with open(out_file, 'w') as f:
        json.dump(final_taxonomy, f, indent=2)
        
    print(f"Successfully wrote {len(final_taxonomy)} mapped questions to {out_file}")
    print("The ingestion pipeline (parser.py) will now use this mapping to strictly extract data.")

if __name__ == "__main__":
    apply_mapping()
