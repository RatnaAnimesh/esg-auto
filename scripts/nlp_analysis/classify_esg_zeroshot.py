import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json

def main():
    embeddings_path = 'data/processed/embeddings/column_embeddings.pkl'
    weights_path = 'data/weights/sector_weights/Automotive.json'
    
    print(f"Loading embeddings from {embeddings_path}...")
    df = pd.read_pickle(embeddings_path)
    
    # Extract the embeddings matrix for all 7995 metrics
    X = np.vstack(df['Embedding'].values)
    
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Define the 3 explicit anchor words. 
    # Using 'social' instead of 'sustainability' because 'sustainability' often 
    # strongly overlaps with 'environment' in semantic space, whereas 'social'
    # correctly captures the 'S' pillar of ESG.
    anchors = {
        'E': "environment",
        'S': "social",
        'G': "governance"
    }
    
    print(f"Computing embeddings for anchors: {list(anchors.values())}")
    anchor_embeddings = model.encode(list(anchors.values()))
    
    # Compute dot products (cosine similarity since these embeddings are typically normalized)
    print("Computing dot products for all 7995 metrics against the 3 anchors...")
    similarities = cosine_similarity(X, anchor_embeddings)
    
    # similarities shape: (7995, 3). Each row is a metric, cols are E, S, G scores.
    # Get the index of the highest score for each metric
    best_match_indices = np.argmax(similarities, axis=1)
    
    pillars = list(anchors.keys())
    # Map the indices to the pillar labels
    df['Pillar'] = [pillars[i] for i in best_match_indices]
    
    # Save mapping to CSV
    mapping_csv = 'data/processed/metadata/metric_esg_classification.csv'
    df[['Prompt', 'Pillar']].to_csv(mapping_csv, index=False)
    print(f"Saved metric classifications to {mapping_csv}")
    
    # Rebuild Automotive.json
    print(f"Rebuilding {weights_path} with accurate zero-shot segments...")
    new_weights = {'E': {}, 'S': {}, 'G': {}}
    
    for _, row in df.iterrows():
        metric = row['Prompt']
        pillar = row['Pillar']
        new_weights[pillar][metric] = 1.0  # Default weight
        
    with open(weights_path, 'w') as f:
        json.dump(new_weights, f, indent=4)
        
    print(f"Successfully updated {weights_path}")
    
    # Print examples
    print("\nSample E metrics:")
    print(df[df['Pillar'] == 'E']['Prompt'].head(3).tolist())
    print("\nSample S metrics:")
    print(df[df['Pillar'] == 'S']['Prompt'].head(3).tolist())
    print("\nSample G metrics:")
    print(df[df['Pillar'] == 'G']['Prompt'].head(3).tolist())

if __name__ == '__main__':
    main()
