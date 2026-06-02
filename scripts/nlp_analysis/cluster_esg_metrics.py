import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

def main():
    embeddings_path = 'data/processed/embeddings/column_embeddings.pkl'
    weights_path = 'data/weights/sector_weights/Automotive.json'
    
    print(f"Loading embeddings from {embeddings_path}...")
    df = pd.read_pickle(embeddings_path)
    
    # Extract the embeddings matrix
    X = np.vstack(df['Embedding'].values)
    
    print("Running K-Means clustering (k=3)...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_
    
    df['Cluster'] = cluster_labels
    
    print("Loading SentenceTransformer to dynamically label clusters...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Define anchors
    anchors = {
        'E': "Environmental impact, emissions, energy consumption, waste management, pollution, water usage, and ecological footprint.",
        'S': "Social impact, employee welfare, worker safety, human rights, diversity, community relations, and labor practices.",
        'G': "Corporate governance, board of directors, ethics, anti-corruption, financial audits, management policies, and stakeholder transparency."
    }
    
    anchor_embeddings = model.encode(list(anchors.values()))
    
    # Map each cluster centroid to the closest anchor
    similarities = cosine_similarity(centroids, anchor_embeddings)
    
    # similarities shape: (3, 3) - rows are clusters, cols are anchors (E, S, G)
    cluster_to_pillar = {}
    pillars = list(anchors.keys())
    
    # Assign each cluster to the pillar with the highest similarity
    # We use argmax on each row, ensuring no duplicates if possible
    # Since it's a 3x3 assignment, we can just take the max for each cluster
    for i in range(3):
        best_anchor_idx = np.argmax(similarities[i])
        # Simple greedy assignment (works fine for well-separated clusters)
        # If there's a collision, this might overwrite, but semantic clusters should align well.
        # Let's do a strict assignment by taking the max similarity across the matrix iteratively
        pass
        
    # Better assignment: iterate 3 times, finding the max value in the matrix
    # and assigning that row to that col, then blanking them out
    sim_matrix = similarities.copy()
    for _ in range(3):
        r, c = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)
        cluster_to_pillar[r] = pillars[c]
        # Blank out row and col
        sim_matrix[r, :] = -np.inf
        sim_matrix[:, c] = -np.inf
        
    print("Cluster Mapping:")
    for cluster_id, pillar in cluster_to_pillar.items():
        print(f"  Cluster {cluster_id} -> {pillar}")
        
    # Map the pillar back to the dataframe
    df['Pillar'] = df['Cluster'].map(cluster_to_pillar)
    
    # Save mapping to CSV
    mapping_csv = 'data/processed/metadata/metric_esg_classification.csv'
    df[['Prompt', 'Pillar']].to_csv(mapping_csv, index=False)
    print(f"Saved metric classifications to {mapping_csv}")
    
    # Rebuild Automotive.json
    print(f"Rebuilding {weights_path} with accurate segments...")
    new_weights = {'E': {}, 'S': {}, 'G': {}}
    
    for _, row in df.iterrows():
        metric = row['Prompt']
        pillar = row['Pillar']
        new_weights[pillar][metric] = 1.0  # Default weight
        
    # Save the updated JSON
    with open(weights_path, 'w') as f:
        json.dump(new_weights, f, indent=4)
        
    print(f"Successfully updated {weights_path}")
    
    # Print a few examples
    print("\nSample E metrics:")
    print(df[df['Pillar'] == 'E']['Prompt'].head(3).tolist())
    print("\nSample S metrics:")
    print(df[df['Pillar'] == 'S']['Prompt'].head(3).tolist())
    print("\nSample G metrics:")
    print(df[df['Pillar'] == 'G']['Prompt'].head(3).tolist())

if __name__ == '__main__':
    main()
