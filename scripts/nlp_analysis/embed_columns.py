import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for the headers (columns) of any CSV file.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input CSV file (e.g., testing/owid_emissions_data.csv)')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output pickle file (e.g., testing/owid_embeddings.pkl)')
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    try:
        # We only need the first row to get the columns
        df_raw = pd.read_csv(args.input, nrows=1)
    except FileNotFoundError:
        print(f"Error: {args.input} not found.")
        sys.exit(1)

    # The 'prompts' are just the column headers of the CSV
    headers = list(df_raw.columns)
    df = pd.DataFrame({'Prompt': headers})

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Calculating embeddings for {len(df)} column headers. This is usually instant...")
    start_time = time.time()

    embeddings = model.encode(df['Prompt'].tolist(), batch_size=256, show_progress_bar=True)
    df['Embedding'] = list(embeddings)

    print(f"Finished encoding in {time.time() - start_time:.2f} seconds.")

    df.to_pickle(args.output)
    print(f"Saved binary array file to {args.output}")

if __name__ == "__main__":
    main()
