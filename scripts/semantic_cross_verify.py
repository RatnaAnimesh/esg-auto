import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Cross-verify custom questions against column embeddings using Lenient Tabular RAG.')
    parser.add_argument('--csv', type=str, help='Path to a questionnaire CSV to process all headers (e.g., testing/mock_esg_questionnaire.csv)')
    parser.add_argument('--query', type=str, help='A single custom question/metric to search for')
    parser.add_argument('--db', type=str, required=True, help='Path to the database pickle file (e.g., testing/owid_embeddings.pkl)')
    parser.add_argument('--threshold', type=float, default=0.25, help='Lenient baseline cosine similarity threshold (default: 0.25)')
    args = parser.parse_args()

    if not args.csv and not args.query:
        print("Please provide either --csv or --query")
        sys.exit(1)

    print(f"Loading embeddings database from {args.db}...")
    try:
        db_df = pd.read_pickle(args.db)
    except FileNotFoundError:
        print(f"Error: {args.db} not found. Run embed_columns.py first.")
        sys.exit(1)

    db_embeddings = np.stack(db_df['Embedding'].values)
    
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    queries = []
    if args.query:
        queries.append(args.query)
    if args.csv:
        try:
            q_df = pd.read_csv(args.csv, nrows=1)
            queries.extend([c for c in q_df.columns if c != 'Question']) # skip the index column if any
        except FileNotFoundError:
            print(f"Error: {args.csv} not found.")
            sys.exit(1)

    print(f"\nProcessing {len(queries)} queries against {len(db_df)} columns...")
    
    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        query_emb = model.encode([query])[0]

        # Calculate Cosine Similarity
        dot_products = np.dot(db_embeddings, query_emb)
        db_norms = np.linalg.norm(db_embeddings, axis=1)
        query_norm = np.linalg.norm(query_emb)
        
        similarities = dot_products / (db_norms * query_norm)
        db_df['Similarity'] = similarities

        filtered_df = db_df[db_df['Similarity'] > args.threshold].sort_values(by='Similarity', ascending=False)
        
        print(f"Columns passing threshold (> {args.threshold}): {len(filtered_df)}")
        if len(filtered_df) == 0:
            print("Status: FAILED -> Triggering Metadata Formula Fallback")
        else:
            print("Top Match:")
            top_match = filtered_df.iloc[0]
            print(f"  [{top_match['Similarity']:.4f}] {top_match['Prompt']}")

if __name__ == "__main__":
    main()
