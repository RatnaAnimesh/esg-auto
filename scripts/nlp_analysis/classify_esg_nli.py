import pandas as pd
import json
import torch
from transformers import pipeline
import time

def main():
    embeddings_path = 'data/processed/embeddings/column_embeddings.pkl'
    weights_path = 'data/weights/sector_weights/Automotive.json'
    
    print(f"Loading metrics from {embeddings_path}...")
    df = pd.read_pickle(embeddings_path)
    metrics = df['Prompt'].tolist()
    
    print("Initializing HuggingFace Zero-Shot Classification Pipeline...")
    # Force CPU to prevent MPS silent deadlocks with HuggingFace pipeline
    device = "cpu"
        
    print(f"Using device: {device}")
    
    # We use a slightly faster, highly accurate model if bart-large is too slow,
    # but bart-large-mnli is the gold standard for zero-shot accuracy.
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=device
    )
    
    # Define labels mapped to E, S, G
    labels = ["environmental impact", "social impact", "corporate governance"]
    label_to_pillar = {
        "environmental impact": "E",
        "social impact": "S",
        "corporate governance": "G"
    }
    
    print(f"Classifying {len(metrics)} metrics. This will take some time...")
    start_time = time.time()
    
    # Batch process for speed
    results = classifier(metrics, candidate_labels=labels, batch_size=32)
    
    print(f"Classification completed in {time.time() - start_time:.2f} seconds.")
    
    # Extract the top prediction for each metric
    pillars = []
    for res in results:
        top_label = res['labels'][0]
        pillars.append(label_to_pillar[top_label])
        
    df['Pillar'] = pillars
    
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
    print(df[df['Pillar'] == 'E']['Prompt'].head(5).tolist())
    print("\nSample S metrics:")
    print(df[df['Pillar'] == 'S']['Prompt'].head(5).tolist())
    print("\nSample G metrics:")
    print(df[df['Pillar'] == 'G']['Prompt'].head(5).tolist())

if __name__ == '__main__':
    main()
