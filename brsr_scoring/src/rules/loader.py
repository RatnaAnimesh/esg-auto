import json
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

from db.client import get_connection

def load_weights_and_applicability(config_path):
    print("Loading rules and proprietary data...")
    prop_dir = BASE_DIR / "data" / "proprietary"
    prop_dir.mkdir(parents=True, exist_ok=True)
    
    with get_connection() as conn:
        conn.row_factory = None # reset to tuple
        cur = conn.cursor()
        
        # 1. Load Industry Mapping if it exists
        mapping_file = prop_dir / "industry_mapping.csv"
        if mapping_file.exists():
            print("Found proprietary industry mapping. Updating Company_Master...")
            df_map = pd.read_csv(mapping_file)
            for _, row in df_map.iterrows():
                cur.execute("""
                    UPDATE Company_Master
                    SET basic_industry = ?, sector = ?
                    WHERE cin = ?
                """, (row.get('basic_industry', ''), row.get('sector', ''), row.get('cin', '')))
        
        # 2. Get all distinct companies and questions
        cur.execute("SELECT cin, basic_industry FROM Company_Master")
        companies = cur.fetchall() # (cin, basic_industry)
        
        cur.execute("SELECT question_id FROM Question_Master")
        questions = [r[0] for r in cur.fetchall()]
        
        # 3. Load Applicability
        app_file = prop_dir / "applicability.csv"
        app_dict = {}
        if app_file.exists():
            print("Found proprietary applicability rules. Loading Matrix B...")
            df_app = pd.read_csv(app_file)
            for _, row in df_app.iterrows():
                app_dict[(row['basic_industry'], row['question_id'])] = int(row['is_applicable'])
                
        # 4. Load Weights
        weight_file = prop_dir / "weights.csv"
        weight_dict = {}
        if weight_file.exists():
            print("Found proprietary weights. Loading Matrix C...")
            df_w = pd.read_csv(weight_file)
            for _, row in df_w.iterrows():
                weight_dict[(row['basic_industry'], row['question_id'])] = float(row['weight'])
        else:
            print("No proprietary weights found. Falling back to default equal weights.")
            with open(config_path, 'r') as f:
                default_weights = json.load(f)
                
        # Populate matrices
        cur.execute("BEGIN TRANSACTION")
        for cin, ind in companies:
            for q in questions:
                # Check dicts, fallback to 1 (applicability) and config (weight)
                b_val = app_dict.get((ind, q), 1)
                
                if weight_dict:
                    c_val = weight_dict.get((ind, q), 0.25)
                else:
                    c_val = default_weights.get("default", {}).get(q, {}).get("weight", 0.25)
                    
                cur.execute("""
                    INSERT OR REPLACE INTO Matrix_B (cin, question_id, is_applicable)
                    VALUES (?, ?, ?)
                """, (cin, q, b_val))
                
                cur.execute("""
                    INSERT OR REPLACE INTO Matrix_C (cin, question_id, weight)
                    VALUES (?, ?, ?)
                """, (cin, q, c_val))
                
        conn.commit()
    print("Matrix B and Matrix C successfully populated.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(BASE_DIR / "config" / "weights.json"), help="Path to weights.json")
    args = parser.parse_args()
    
    load_weights_and_applicability(args.config)
