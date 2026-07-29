import pandas as pd
import numpy as np
import zlib
import torch
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent

def preprocess_text(text):
    if not isinstance(text, str): return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text.split()

def compute_ncd(s1, s2):
    """Approximates Kolmogorov Complexity using zlib compression."""
    if not isinstance(s1, str) or not isinstance(s2, str): return 1.0
    if len(s1) == 0 or len(s2) == 0: return 1.0
    
    c_s1 = len(zlib.compress(s1.encode('utf-8')))
    c_s2 = len(zlib.compress(s2.encode('utf-8')))
    c_s1s2 = len(zlib.compress((s1 + s2).encode('utf-8')))
    
    ncd = (c_s1s2 - min(c_s1, c_s2)) / max(c_s1, c_s2)
    return ncd

def main():
    # 1. Device Selection (Apple Silicon MPS)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Computing BM25 Null Distributions on: {device}")

    print("Loading mapping results...")
    review_file = BASE_DIR / "config" / "mapping_review.csv"
    df = pd.read_csv(review_file)
    
    header_file = BASE_DIR / "data" / "csv_headers_list.txt"
    with open(header_file, 'r') as f:
        headers = [line.strip() for line in f if line.strip()]
        
    # 2. Preprocess & Build Global Vocabulary
    print("Building global vocabulary tensor...")
    processed_headers = [preprocess_text(h) for h in headers]
    
    vocab = set()
    for tokens in processed_headers:
        vocab.update(tokens)
    vocab = list(vocab)
    word_to_idx = {word: i for i, word in enumerate(vocab)}
    V = len(vocab)
    
    # 3. Build Header TF Matrix (N x V) on MPS
    N = len(headers)
    H_tf = torch.zeros((N, V), dtype=torch.float32, device=device)
    H_len = torch.zeros(N, dtype=torch.float32, device=device)
    
    for i, tokens in enumerate(processed_headers):
        H_len[i] = len(tokens)
        for token in tokens:
            H_tf[i, word_to_idx[token]] += 1
            
    avgdl = torch.mean(H_len)
    
    # 4. Calculate IDF and Header TF Saturation (BM25 math)
    k1 = 1.5
    b = 0.75
    
    df_freq = torch.sum(H_tf > 0, dim=0).float()
    idf = torch.log(1 + (N - df_freq + 0.5) / (df_freq + 0.5))
    
    # H_tf_sat: (N, V)
    H_tf_sat = (H_tf * (k1 + 1)) / (H_tf + k1 * (1 - b + b * (H_len.unsqueeze(1) / avgdl)))
    
    # Weighted Header Matrix (IDF * TF_sat)
    H_weighted = H_tf_sat * idf
    
    print("Processing True Questions and Matched Headers...")
    questions = df['question_text'].tolist()
    matched_headers = df['global_optimal_match'].tolist()
    
    # Find matched header indices
    header_to_idx = {h: i for i, h in enumerate(headers)}
    matched_indices = [header_to_idx.get(h, -1) for h in matched_headers]
    
    # 5. Build True Question TF Matrix (Q x V)
    Q_true_tf = torch.zeros((len(questions), V), dtype=torch.float32, device=device)
    Q_lens = []
    for i, q in enumerate(questions):
        tokens = preprocess_text(q)
        Q_lens.append(max(len(tokens), 1)) # Prevent 0 length
        for token in tokens:
            if token in word_to_idx:
                Q_true_tf[i, word_to_idx[token]] += 1
                
    # Extract the specific weighted header vectors for the true matches
    # Shape: (Q, V)
    valid_matched_indices = torch.tensor(matched_indices, device=device, dtype=torch.long)
    H_matched_weighted = H_weighted[valid_matched_indices]
    
    # Compute True BM25 scores (Dot product of Q TF and H Weighted TF)
    true_scores = torch.sum(Q_true_tf * H_matched_weighted, dim=1)
    
    # 6. Generate Null Distribution (Monte Carlo Vocabulary Sampling)
    print("Generating 500 random queries per question on GPU...")
    N_PERMUTATIONS = 500
    total_rand_queries = len(questions) * N_PERMUTATIONS
    
    Q_rand_tf = torch.zeros((total_rand_queries, V), dtype=torch.float32, device=device)
    
    for i, q_len in enumerate(Q_lens):
        start_idx = i * N_PERMUTATIONS
        end_idx = start_idx + N_PERMUTATIONS
        
        # Sample random word indices from the global vocabulary
        rand_indices = torch.randint(0, V, (N_PERMUTATIONS, q_len), device=device)
        
        # Scatter to create random TF vectors
        ones = torch.ones_like(rand_indices, dtype=torch.float32)
        Q_rand_tf[start_idx:end_idx].scatter_add_(1, rand_indices, ones)
        
    # Expand matched headers to align with the random queries
    expanded_matched_indices = torch.repeat_interleave(valid_matched_indices, N_PERMUTATIONS)
    H_matched_expanded = H_weighted[expanded_matched_indices]
    
    # Compute Random BM25 scores
    rand_scores = torch.sum(Q_rand_tf * H_matched_expanded, dim=1)
    rand_scores = rand_scores.view(len(questions), N_PERMUTATIONS)
    
    # 7. Calculate p-values
    # p = count(random_scores >= true_score) / N_PERMUTATIONS
    true_scores_expanded = true_scores.unsqueeze(1)
    p_values_tensor = torch.sum(rand_scores >= true_scores_expanded, dim=1).float() / N_PERMUTATIONS
    
    # Move results back to CPU for Pandas
    p_values = p_values_tensor.cpu().numpy()
    true_scores_np = true_scores.cpu().numpy()
    
    print("Calculating Kolmogorov (NCD) on CPU...")
    ncd_scores = []
    for idx, row in df.iterrows():
        ncd = compute_ncd(row['question_text'], row['global_optimal_match'])
        ncd_scores.append(round(ncd, 4))
        
    print("Applying Verification Logic...")
    verification_flags = []
    for i in range(len(df)):
        ncd = ncd_scores[i]
        p_val = p_values[i]
        
        if ncd < 0.5 and p_val < 0.05:
            verification_flags.append("Mathematically Verified")
        elif ncd < 0.7 and p_val < 0.10:
            verification_flags.append("Weak Match - Review")
        else:
            verification_flags.append("Failed Verification")
            
    df['true_bm25_score'] = np.round(true_scores_np, 4)
    df['ncd_score'] = ncd_scores
    df['p_value'] = np.round(p_values, 4)
    df['verification_status'] = verification_flags
    
    out_file = BASE_DIR / "config" / "verified_mapping.csv"
    df.to_csv(out_file, index=False)
    
    print("\n--- Verification Summary ---")
    print(df['verification_status'].value_counts())
    print(f"\nResults saved to {out_file}")

if __name__ == "__main__":
    main()
