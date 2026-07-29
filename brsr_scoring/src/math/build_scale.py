import pandas as pd
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

from db.client import get_connection

def build_historical_scale():
    print("Fetching historical Matrix A and Company data...")
    with get_connection() as conn:
        # Load Matrix A joined with Company_Master to get sectors
        query = """
            SELECT a.cin, a.question_id, a.score, c.sector 
            FROM Matrix_A a
            JOIN Company_Master c ON a.cin = c.cin
        """
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No data in Matrix A. Cannot build scale.")
            return

        print("Aggregating scores by Sector and Question...")
        
        # Group by sector and question_id and collect scores into a list
        scale_df = df.groupby(['sector', 'question_id'])['score'].apply(list).reset_index()
        
        print("Inserting historical baseline into Historical_Scale table...")
        cur = conn.cursor()
        for idx, row in scale_df.iterrows():
            historical_scores_json = json.dumps(row['score'])
            cur.execute("""
                INSERT OR REPLACE INTO Historical_Scale (sector, question_id, historical_scores)
                VALUES (?, ?, ?)
            """, (row['sector'], row['question_id'], historical_scores_json))
        
        conn.commit()
    print(f"Historical scale successfully populated for {len(scale_df)} sector-question combinations.")

if __name__ == "__main__":
    build_historical_scale()
