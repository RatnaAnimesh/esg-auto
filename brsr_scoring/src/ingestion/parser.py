import pandas as pd
import json
import sys
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

from db.client import get_connection

def parse_and_load(csv_path, map_path):
    print("Loading taxonomy map...")
    with open(map_path, 'r') as f:
        taxonomy = json.load(f)
    
    print("Reading CSV...")
    # Read only needed columns to save memory
    company_cols = [
        'Corporate Identity Number', 'Name Of The Company', 'Date Of Incorporation',
        'Address Of Registered Office Of Company', 'Address Of Corporate Office Of Company',
        'EMail Of The Company', 'Telephone Of Company', 'Website Of Company',
        'Date Of Start Of Financial Year', 'Date Of End Of Financial Year',
        'Name Of Stock Exchange Where The Company Is Listed - Stock Exchange1',
        'Description Of Main Activity - Details Of Business Activities Accounting For Ninety Percent Of The Turnover Domain1',
        'Description Of Business Activity - Details Of Business Activities Accounting For Ninety Percent Of The Turnover Domain1'
    ]
    cols_to_use = company_cols + list(taxonomy.keys())
    try:
        df = pd.read_csv(csv_path, usecols=lambda c: c in cols_to_use)
    except ValueError as e:
        print(f"Error reading columns: {e}")
        return

    # Clean missing IDs
    df = df.dropna(subset=['Corporate Identity Number'])
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        print("Inserting Question Master...")
        for col, meta in taxonomy.items():
            cur.execute("""
                INSERT OR IGNORE INTO Question_Master (question_id, question_text, data_type)
                VALUES (?, ?, ?)
            """, (meta['question_id'], meta['question_text'], meta['data_type']))
            
        print("Processing companies and Matrix A...")
        # Min-Max Normalization (Sector-level fallback to global)
        min_max_cache = {}
        for col, meta in taxonomy.items():
            if col not in df.columns:
                continue
                
            if meta['data_type'] == 'numeric':
                df[col] = pd.to_numeric(df[col], errors='coerce')
                min_max_cache[col] = {
                    'min': df[col].min(),
                    'max': df[col].max()
                }
            elif meta['data_type'] == 'boolean':
                df[col] = df[col].astype(str).str.upper().map({'YES': 1, 'Y': 1, 'TRUE': 1, '1': 1}).fillna(0)

        for idx, row in df.iterrows():
            cin = str(row['Corporate Identity Number']).strip()
            name = str(row.get('Name Of The Company', '')).strip()
            date_inc = str(row.get('Date Of Incorporation', '')).strip()
            reg_off = str(row.get('Address Of Registered Office Of Company', '')).strip()
            corp_off = str(row.get('Address Of Corporate Office Of Company', '')).strip()
            email = str(row.get('EMail Of The Company', '')).strip()
            tel = str(row.get('Telephone Of Company', '')).strip()
            web = str(row.get('Website Of Company', '')).strip()
            fy_start = str(row.get('Date Of Start Of Financial Year', '')).strip()
            fy_end = str(row.get('Date Of End Of Financial Year', '')).strip()
            exchange = str(row.get('Name Of Stock Exchange Where The Company Is Listed - Stock Exchange1', '')).strip()
            sector = str(row.get('Description Of Main Activity - Details Of Business Activities Accounting For Ninety Percent Of The Turnover Domain1', 'Unknown')).strip()
            activity = str(row.get('Description Of Business Activity - Details Of Business Activities Accounting For Ninety Percent Of The Turnover Domain1', '')).strip()
            
            cur.execute("""
                INSERT OR IGNORE INTO Company_Master (
                    cin, name, date_of_incorporation, registered_office_address, corporate_office_address,
                    email, telephone, website, financial_year_start, financial_year_end,
                    stock_exchange, basic_industry, sector, business_activity
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cin, name, date_inc, reg_off, corp_off, email, tel, web, fy_start, fy_end, exchange, "General", sector, activity))

            for col, meta in taxonomy.items():
                raw_val = row.get(col)
                if pd.isna(raw_val):
                    continue
                
                score = 0.0
                if meta['data_type'] == 'numeric':
                    val = float(raw_val)
                    c_min = min_max_cache[col]['min']
                    c_max = min_max_cache[col]['max']
                    if c_max > c_min:
                        score = (val - c_min) / (c_max - c_min)
                    else:
                        score = 0.0
                elif meta['data_type'] == 'boolean':
                    val_str = str(raw_val).strip().lower()
                    if val_str in ['yes', 'y', 'true', '1']:
                        score = 1.0
                    else:
                        score = 0.0
                
                cur.execute("""
                    INSERT OR REPLACE INTO Matrix_A (cin, question_id, raw_value, score)
                    VALUES (?, ?, ?, ?)
                """, (cin, meta['question_id'], str(raw_val), score))
                
        conn.commit()
    print("Done parsing and loading Matrix A.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to brsr_consolidated.csv")
    parser.add_argument("--map", default=str(BASE_DIR / "config" / "taxonomy_map.json"), help="Path to taxonomy_map.json")
    args = parser.parse_args()
    
    parse_and_load(args.csv, args.map)
