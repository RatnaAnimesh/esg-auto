import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    print("Loading MHA matrix data...")
    # Load data
    cosine_scores = np.load(BASE_DIR / "data" / "mha_cosine_scores.npy")
    
    with open(BASE_DIR / "data" / "mha_questions.json", "r") as f:
        questions = json.load(f)
        
    with open(BASE_DIR / "data" / "mha_headings.json", "r") as f:
        headings = json.load(f)
        
    print(f"Matrix shape: {cosine_scores.shape}")
    
    # Plotting 1: Zoomed-in Heatmap (Subset of 15 questions)
    print("Generating zoomed-in heatmap with labels...")
    
    # Pick a subset of 15 questions that had strong matches to showcase
    # We will find 15 questions with the highest max similarity
    max_scores = np.max(cosine_scores, axis=1)
    top_15_q_indices = np.argsort(max_scores)[-15:]
    
    # For these 15 questions, get their best matching heading indices
    top_15_h_indices = np.argmax(cosine_scores[top_15_q_indices], axis=1)
    
    # Create the sub-matrix (15x15)
    sub_matrix = cosine_scores[np.ix_(top_15_q_indices, top_15_h_indices)]
    
    # Get labels
    q_labels = [questions[i][:50] + "..." for i in top_15_q_indices]
    h_labels = [headings[i][:50] + "..." for i in top_15_h_indices]
    
    plt.figure(figsize=(16, 10), dpi=300)
    sns.heatmap(
        sub_matrix, 
        cmap="inferno", 
        cbar_kws={'label': 'Cosine Similarity'},
        xticklabels=h_labels,
        yticklabels=q_labels,
        vmin=0.0, 
        vmax=1.0,
        annot=True,     # Show the actual similarity numbers
        fmt=".2f"
    )
    
    plt.title("MHA Semantic Similarity (Zoomed-in Sample)", fontsize=18, pad=20)
    plt.xlabel("Top Matched XBRL Headings", fontsize=14)
    plt.ylabel("Canonical Questions", fontsize=14)
    plt.xticks(rotation=45, ha='right')
    
    artifact_path = "/Users/ashishmishra/.gemini/antigravity-ide/brain/899cfced-57c1-4e95-bb98-24c635654f1b/mha_heatmap.png"
    plt.tight_layout()
    plt.savefig(artifact_path, format="png", bbox_inches='tight')
    plt.close()
    
    print(f"Readable heatmap successfully saved to {artifact_path}")

if __name__ == "__main__":
    main()
