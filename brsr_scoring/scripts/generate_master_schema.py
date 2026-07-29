import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "brsr.db"
BRSR_MAPPING = BASE_DIR / "config" / "mapping_review.csv" # Use BM25 only, bypass strict NCD
AR_MAPPING = BASE_DIR / "config" / "brsr_ar_mapping.csv"
OUTPUT_SCHEMA = BASE_DIR / "config" / "master_schema.csv"

def generate_master_schema():
    # 1. Load Canonical Question Master from DB
    conn = sqlite3.connect(DB_PATH)
    question_master = pd.read_sql_query("SELECT question_id, question_text, data_type FROM Question_Master", conn)
    conn.close()

    # 2. Load the mappings
    brsr_df = pd.read_csv(BRSR_MAPPING)
    ar_df = pd.read_csv(AR_MAPPING)
    
    # Prefix columns to avoid collisions when merging
    brsr_df = brsr_df.rename(columns={
        'confidence_flag': 'brsr_status',
        'global_optimal_match': 'brsr_target',
        'optimal_score': 'brsr_bm25'
    })
    
    ar_df = ar_df.rename(columns={
        'brsr_question': 'question_text',
        'verification_status': 'ar_status',
        'xbrl_tag': 'ar_target',
        'bm25_score': 'ar_bm25',
        'ncd_score': 'ar_ncd',
        'p_value': 'ar_pval'
    })
    
    # 3. Merge both mappings onto the canonical questions
    merged_df = pd.merge(question_master, brsr_df[['question_text', 'brsr_status', 'brsr_target', 'brsr_bm25']], on='question_text', how='left')
    merged_df = pd.merge(merged_df, ar_df[['question_text', 'ar_status', 'ar_target', 'ar_bm25', 'ar_ncd', 'ar_pval']], on='question_text', how='left')
    
    # 4. Apply Cascading Fallback Logic (BRSR First - Bypassing NCD)
    results = []
    
    for _, row in merged_df.iterrows():
        q_id = row['question_id']
        q_text = row['question_text']
        d_type = row['data_type']
        
        primary_source = ""
        extraction_target = ""
        final_status = ""
        bm25 = 0.0
        
        brsr_flag = str(row['brsr_status'])
        
        if pd.notna(row['brsr_status']) and brsr_flag in ["High Confidence", "Ambiguous"]:
            primary_source = "BRSR"
            extraction_target = row['brsr_target']
            final_status = f"Locked (BRSR: {brsr_flag})"
            bm25 = row['brsr_bm25']
            
        elif pd.notna(row['ar_status']) and str(row['ar_status']) == "Verified":
            primary_source = "Annual_Report"
            extraction_target = row['ar_target']
            final_status = "Verified (Annual Report Fallback)"
            bm25 = row['ar_bm25']
            
        else:
            primary_source = "BRSR"
            extraction_target = row['brsr_target'] if pd.notna(row['brsr_target']) else "No Match Found"
            final_status = "Unverified - Needs Manual Review"
            bm25 = row['brsr_bm25'] if pd.notna(row['brsr_bm25']) else 0.0
            
        results.append({
            'question_id': q_id,
            'question_text': q_text,
            'data_type': d_type,
            'primary_source': primary_source,
            'extraction_target': extraction_target,
            'verification_status': final_status,
            'final_bm25_score': round(bm25, 4)
        })
        
    master_df = pd.DataFrame(results)
    
    # 5. Save to CSV
    master_df.to_csv(OUTPUT_SCHEMA, index=False)
    
    print(f"Master Schema successfully generated at {OUTPUT_SCHEMA}")
    print("\n--- Fallback Status Summary ---")
    print(master_df['verification_status'].value_counts())

if __name__ == "__main__":
    generate_master_schema()
