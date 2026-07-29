import pandas as pd
from scipy.stats import percentileofscore
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

from db.client import get_connection

def calculate_percentiles():
    print("Fetching Matrix A and Company data...")
    with get_connection() as conn:
        # Load Matrix A joined with Company_Master to get sectors
        query = """
            SELECT a.cin, a.question_id, a.score, c.sector 
            FROM Matrix_A a
            JOIN Company_Master c ON a.cin = c.cin
        """
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No data in Matrix A.")
            return

        print("Fetching Historical Scale...")
        scale_df = pd.read_sql_query("SELECT sector, question_id, historical_scores FROM Historical_Scale", conn)
        
        if scale_df.empty:
            print("Historical_Scale table is empty. Please run build_scale.py on historical data first.")
            return
            
        # Parse JSON lists
        import json
        scale_dict = {}
        for _, row in scale_df.iterrows():
            scale_dict[(row['sector'], row['question_id'])] = json.loads(row['historical_scores'])

        print("Calculating percentiles by Sector and Question against historical baseline...")
        
        def get_percentile(row):
            key = (row['sector'], row['question_id'])
            if key in scale_dict:
                hist_scores = scale_dict[key]
                # percentileofscore returns 0-100. We divide by 100 to get [0, 1]
                return percentileofscore(hist_scores, row['score'], kind='weak') / 100.0
            else:
                # If no historical baseline exists for this sector/question, 
                # default to 0.5 (median) or calculate among current batch.
                # For this implementation, we return a neutral 0.5
                return 0.5

        df['percentile'] = df.apply(get_percentile, axis=1)
        
        print("Inserting into Matrix P...")
        cur = conn.cursor()
        for idx, row in df.iterrows():
            cur.execute("""
                INSERT OR REPLACE INTO Matrix_P (cin, question_id, percentile)
                VALUES (?, ?, ?)
            """, (row['cin'], row['question_id'], row['percentile']))
        
        conn.commit()
    print("Matrix P successfully populated against historical scale.")

if __name__ == "__main__":
    calculate_percentiles()
