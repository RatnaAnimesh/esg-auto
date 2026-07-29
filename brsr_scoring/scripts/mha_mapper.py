import pandas as pd
import numpy as np
import torch
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

BASE_DIR = Path(__file__).resolve().parent.parent

def load_data():
    """Loads the 316 questions and the combined BRSR/AR headings."""
    # 1. Load Questions
    with open(BASE_DIR / "config" / "taxonomy_map_full.json", 'r') as f:
        taxonomy = json.load(f)
    questions = list(taxonomy.keys())
    
    # 2. Load Combined Headings
    brsr_file = BASE_DIR / "data" / "csv_headers_list.txt"
    ar_file = BASE_DIR / "data" / "xbrl_tags_list.txt"
    
    headings = []
    
    if brsr_file.exists():
        with open(brsr_file, 'r') as f:
            headings.extend([line.strip() for line in f if line.strip()])
            
    if ar_file.exists():
        with open(ar_file, 'r') as f:
            headings.extend([line.strip() for line in f if line.strip()])
            
    # Remove duplicates to save computation
    headings = list(set(headings))
        
    return questions, headings

def main():
    print("Loading Data...")
    questions, headings = load_data()
    print(f"Loaded {len(questions)} questions and {len(headings)} combined unique headings.")

    # 1. Load Multi-Head Attention Model
    print("Initializing Multi-Head Attention Encoder...")
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
    
    # 2. Encode Text into Dense Vector Space using MHA
    print("Encoding questions and headings via Multi-Head Attention...")
    q_embeddings = model.encode(questions, convert_to_tensor=True, show_progress_bar=True)
    h_embeddings = model.encode(headings, convert_to_tensor=True, show_progress_bar=True)
    
    # 3. Compute Cosine Similarity Matrix
    print("Computing Cosine Similarity Matrix...")
    cosine_scores = util.cos_sim(q_embeddings, h_embeddings)
    
    # Move to CPU for processing
    cosine_scores_cpu = cosine_scores.cpu().numpy()
    
    # Save the raw cosine similarity matrix and labels for visualization
    np.save(BASE_DIR / "data" / "mha_cosine_scores.npy", cosine_scores_cpu)
    with open(BASE_DIR / "data" / "mha_questions.json", "w") as f:
        json.dump(questions, f)
    with open(BASE_DIR / "data" / "mha_headings.json", "w") as f:
        json.dump(headings, f)
    
    # 4. Extract Top 3 MHA Mappings
    print("Extracting Top 3 MHA Mappings...")
    top_k = 3
    top_scores, top_indices = torch.topk(cosine_scores, k=top_k, dim=1)
    
    top_scores_cpu = top_scores.cpu().numpy()
    top_indices_cpu = top_indices.cpu().numpy()
    
    results = []
    for i, q in enumerate(questions):
        best_idx = top_indices_cpu[i, 0]
        best_score = top_scores_cpu[i, 0]
        best_heading = headings[best_idx]
        
        # Dynamic Confidence Thresholding for MHA
        if best_score >= 0.70:
            status = "High Confidence (MHA)"
        elif best_score >= 0.50:
            status = "Medium Confidence (MHA)"
        else:
            status = "Low Confidence (MHA)"
            
        results.append({
            "question_text": q,
            "best_match": best_heading,
            "mha_similarity_score": round(float(best_score), 4),
            "verification_status": status,
            "alt_match_1": headings[top_indices_cpu[i, 1]] if top_k > 1 else "",
            "alt_score_1": round(float(top_scores_cpu[i, 1]), 4) if top_k > 1 else 0,
            "alt_match_2": headings[top_indices_cpu[i, 2]] if top_k > 2 else "",
            "alt_score_2": round(float(top_scores_cpu[i, 2]), 4) if top_k > 2 else 0,
        })
        
    df_results = pd.DataFrame(results)
    
    # 5. Save Output
    out_file = BASE_DIR / "config" / "mha_mapping_review.csv"
    df_results.to_csv(out_file, index=False)
    
    print("\n--- Multi-Head Attention Mapping Summary ---")
    print(df_results['verification_status'].value_counts())
    print(f"\nResults saved to {out_file}")

if __name__ == "__main__":
    main()
