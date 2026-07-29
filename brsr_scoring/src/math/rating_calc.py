import pandas as pd
import numpy as np
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

from db.client import get_connection

def compute_final_ratings():
    print("Loading matrices from database...")
    with get_connection() as conn:
        # Load matrices. We use pivot to create Company (rows) x Question (cols) matrices
        df_a = pd.read_sql_query("SELECT cin, question_id, score FROM Matrix_A", conn)
        df_b = pd.read_sql_query("SELECT cin, question_id, is_applicable FROM Matrix_B", conn)
        df_c = pd.read_sql_query("SELECT cin, question_id, weight FROM Matrix_C", conn)
        df_p = pd.read_sql_query("SELECT cin, question_id, percentile FROM Matrix_P", conn)

    if df_a.empty or df_b.empty or df_c.empty or df_p.empty:
        print("One or more matrices are empty. Aborting.")
        return

    # Pivot to create 2D matrices
    A = df_a.pivot(index='cin', columns='question_id', values='score').fillna(0)
    B = df_b.pivot(index='cin', columns='question_id', values='is_applicable').fillna(0)
    C = df_c.pivot(index='cin', columns='question_id', values='weight').fillna(0)
    P = df_p.pivot(index='cin', columns='question_id', values='percentile').fillna(0)
    
    print("Aligning matrices...")
    # Align all matrices to have the exact same shape (intersection of indices and columns)
    A, B = A.align(B, join='inner')
    A, C = A.align(C, join='inner')
    A, P = A.align(P, join='inner')
    B, C = B.align(C, join='inner')
    B, P = B.align(P, join='inner')
    C, P = C.align(P, join='inner')

    print("Computing Hadamard Product: (A * B * C) * P ...")
    # Pandas multiplication is element-wise for aligned DataFrames
    Final_Rating_Matrix = (A * B * C) * P
    
    # Sum across questions axis to get final company score
    Company_Final_Score = Final_Rating_Matrix.sum(axis=1).reset_index(name='final_rating')
    
    print("Saving Final Ratings to database...")
    with get_connection() as conn:
        cur = conn.cursor()
        for idx, row in Company_Final_Score.iterrows():
            cur.execute("""
                INSERT OR REPLACE INTO Final_Ratings (cin, final_rating)
                VALUES (?, ?)
            """, (row['cin'], float(row['final_rating'])))
        conn.commit()

    print(f"Final Ratings computed for {len(Company_Final_Score)} companies.")
    return Company_Final_Score

if __name__ == "__main__":
    df = compute_final_ratings()
    print("\nSample top 10 ratings:")
    print(df.sort_values(by='final_rating', ascending=False).head(10))
