import pandas as pd
import numpy as np
import torch
import re
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

BASE_DIR = Path(__file__).resolve().parent.parent

class KalmanFusionMapper:
    def __init__(self, questions, headings, device="mps"):
        self.device = torch.device(device if device == "mps" and torch.backends.mps.is_available() else "cpu")
        self.questions = questions
        self.headings = headings
        self.vocab = []
        self.word_to_idx = {}
        
    def _preprocess(self, text):
        if not isinstance(text, str): return []
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return text.split()

    def _compute_bm25_and_pvalues(self, permutations=100):
        print(f"Computing BM25 & {permutations} Permutations on {self.device}...")
        processed_headers = [self._preprocess(h) for h in self.headings]
        
        # 1. Build Vocab
        vocab_set = set()
        for tokens in processed_headers:
            vocab_set.update(tokens)
        self.vocab = list(vocab_set)
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        V = len(self.vocab)
        
        # 2. Header TF Matrix
        N = len(self.headings)
        H_tf = torch.zeros((N, V), dtype=torch.float32, device=self.device)
        H_len = torch.zeros(N, dtype=torch.float32, device=self.device)
        
        for i, tokens in enumerate(processed_headers):
            H_len[i] = len(tokens)
            for token in tokens:
                if token in self.word_to_idx:
                    H_tf[i, self.word_to_idx[token]] += 1
                
        avgdl = torch.mean(H_len)
        
        # 3. Compute IDF and BM25 Weighted Matrix
        df = torch.sum(H_tf > 0, dim=0).float()
        H_idf = torch.log(1 + (N - df + 0.5) / (df + 0.5))
        
        k1, b = 1.5, 0.75
        H_tf_sat = (H_tf * (k1 + 1)) / (H_tf + k1 * (1 - b + b * (H_len.unsqueeze(1) / avgdl)))
        H_weighted = H_tf_sat * H_idf
        
        # 4. True Query BM25 Scores
        Q_true_tf = torch.zeros((len(self.questions), V), dtype=torch.float32, device=self.device)
        Q_lens = []
        for i, q in enumerate(self.questions):
            tokens = self._preprocess(q)
            Q_lens.append(max(len(tokens), 1))
            for token in tokens:
                if token in self.word_to_idx:
                    Q_true_tf[i, self.word_to_idx[token]] += 1
                    
        true_scores = torch.matmul(Q_true_tf, H_weighted.T) # Shape: (M, N)
        
        # 5. Vectorized Monte Carlo Permutations
        total_rand = len(self.questions) * permutations
        Q_rand_tf = torch.zeros((total_rand, V), dtype=torch.float32, device=self.device)
        
        for i, q_len in enumerate(Q_lens):
            start = i * permutations
            end = start + permutations
            rand_indices = torch.randint(0, V, (permutations, q_len), device=self.device)
            ones = torch.ones_like(rand_indices, dtype=torch.float32)
            Q_rand_tf[start:end].scatter_add_(1, rand_indices, ones)
            
        rand_scores = torch.matmul(Q_rand_tf, H_weighted.T) # Shape: (M*perm, N)
        rand_scores = rand_scores.view(len(self.questions), permutations, len(self.headings))
        
        # 6. Extract Top 1 & Compute p-values
        top_scores, top_indices = torch.topk(true_scores, 1, dim=1)
        
        true_expanded = top_scores.expand(-1, permutations)
        rand_top1_scores = torch.gather(rand_scores, 2, top_indices.unsqueeze(2).expand(-1, permutations, 1)).squeeze(2)
        
        p_values = torch.sum(rand_top1_scores >= true_expanded, dim=1).float() / permutations
        
        return true_scores, p_values

    def _compute_mha_scores(self):
        print("Loading Multi-Head Attention Encoder...")
        model = SentenceTransformer('all-MiniLM-L6-v2', device=str(self.device))
        
        print("Encoding text via Multi-Head Attention...")
        q_embeds = model.encode(self.questions, convert_to_tensor=True, show_progress_bar=True)
        h_embeds = model.encode(self.headings, convert_to_tensor=True, show_progress_bar=True)
        
        # Cosine Similarity Matrix (M x N)
        mha_scores = util.cos_sim(q_embeds, h_embeds)
        return mha_scores

    def fuse_and_map(self, top_k=3, permutations=100):
        # Sensor 1: BM25 & p-values
        bm25_scores, p_values = self._compute_bm25_and_pvalues(permutations=permutations)
        
        # Sensor 2: MHA
        mha_scores = self._compute_mha_scores()
        
        print("Applying Kalman Filter Sensor Fusion...")
        # 1. Normalize BM25 scores to 0-1 range
        bm25_norm = bm25_scores / (torch.max(bm25_scores, dim=1, keepdim=True)[0] + 1e-5)
        
        # 2. Calculate MHA Margin of Victory (1st place - 2nd place)
        top2_mha, _ = torch.topk(mha_scores, 2, dim=1)
        mha_margin = top2_mha[:, 0] - top2_mha[:, 1] 
        mha_margin = mha_margin.unsqueeze(1) 
        
        # 3. Calculate Noise Variances (R)
        R_bm25 = p_values.unsqueeze(1) + 1e-5
        R_mha = (1.0 - mha_margin) + 1e-5
        
        # 4. Kalman Gain (K)
        kalman_gain = R_bm25 / (R_bm25 + R_mha)
        
        # 5. Fused Score Estimate
        fused_scores = bm25_norm + kalman_gain * (mha_scores - bm25_norm)
        
        # 6. Extract Top K
        top_scores, top_indices = torch.topk(fused_scores, top_k, dim=1)
        
        # Move to CPU
        top_scores_cpu = top_scores.cpu().numpy()
        top_indices_cpu = top_indices.cpu().numpy()
        fused_scores_cpu = fused_scores.cpu().numpy()
        mha_scores_cpu = mha_scores.cpu().numpy()
        bm25_norm_cpu = bm25_norm.cpu().numpy()
        
        results = []
        for i, q in enumerate(self.questions):
            best_idx = top_indices_cpu[i, 0]
            best_score = top_scores_cpu[i, 0]
            best_heading = self.headings[best_idx]
            
            if best_score >= 0.75:
                status = "Kalman Verified (High)"
            elif best_score >= 0.50:
                status = "Kalman Review (Medium)"
            else:
                status = "Kalman Failed"
                
            results.append({
                "question": q,
                "kalman_fused_match": best_heading,
                "fused_score": round(float(best_score), 4),
                "mha_score_raw": round(float(mha_scores_cpu[i, best_idx]), 4),
                "bm25_score_norm": round(float(bm25_norm_cpu[i, best_idx]), 4),
                "kalman_gain": round(float(kalman_gain[i].item()), 4),
                "p_value": round(float(p_values[i].item()), 4),
                "verification_status": status,
                "alt_match_1": self.headings[top_indices_cpu[i, 1]] if top_k > 1 else "",
                "alt_fused_score_1": round(float(top_scores_cpu[i, 1]), 4) if top_k > 1 else 0,
            })
            
        return pd.DataFrame(results)

def load_combined_headings():
    headings = []
    brsr_file = BASE_DIR / "data" / "csv_headers_list.txt"
    ar_file = BASE_DIR / "data" / "xbrl_tags_list.txt"
    
    if brsr_file.exists():
        with open(brsr_file, 'r') as f:
            headings.extend([line.strip() for line in f if line.strip()])
    if ar_file.exists():
        with open(ar_file, 'r') as f:
            headings.extend([line.strip() for line in f if line.strip()])
            
    return list(set(headings))

if __name__ == "__main__":
    print("Loading Data...")
    with open(BASE_DIR / "config" / "taxonomy_map_full.json", 'r') as f:
        taxonomy = json.load(f)
    questions = list(taxonomy.keys())
    
    headings = load_combined_headings()
    print(f"Loaded {len(questions)} questions and {len(headings)} combined unique headings.")
        
    mapper = KalmanFusionMapper(questions, headings, device="mps")
    df_results = mapper.fuse_and_map(top_k=3, permutations=100)
    
    out_file = BASE_DIR / "config" / "kalman_fused_mapping.csv"
    df_results.to_csv(out_file, index=False)
    
    print("\n--- Kalman Fusion Mapping Summary ---")
    print(df_results['verification_status'].value_counts())
    print(f"\nResults saved to {out_file}")
