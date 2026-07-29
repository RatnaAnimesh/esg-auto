import pandas as pd
import numpy as np
import zlib
import torch
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class GeneralizedMapper:
    def __init__(self, queries, headers, device="mps"):
        self.device = torch.device(device if device == "mps" and torch.backends.mps.is_available() else "cpu")
        self.queries = queries
        self.headers = headers
        self.vocab = []
        self.word_to_idx = {}
        self.H_tf = None
        self.H_idf = None
        self.H_len = None
        self.H_weighted = None
        
    def _preprocess(self, text):
        if not isinstance(text, str): return []
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return text.split()

    def _extract_entities(self, text):
        """Extracts alphanumeric acronyms/standards (e.g., ISO 9001, IND AS)"""
        if not isinstance(text, str): return set()
        entities = re.findall(r'\b[A-Z]{2,}[0-9]*\b', text)
        return set(e.lower() for e in entities)

    def _compute_ncd(self, s1, s2):
        """Approximates Kolmogorov Complexity using zlib compression."""
        if not isinstance(s1, str) or not isinstance(s2, str): return 1.0
        if len(s1) == 0 or len(s2) == 0: return 1.0
        
        c_s1 = len(zlib.compress(s1.encode('utf-8')))
        c_s2 = len(zlib.compress(s2.encode('utf-8')))
        c_s1s2 = len(zlib.compress((s1 + s2).encode('utf-8')))
        
        return (c_s1s2 - min(c_s1, c_s2)) / max(c_s1, c_s2)

    def build_index(self):
        print(f"Building XBRL index on {self.device}...")
        processed_headers = [self._preprocess(h) for h in self.headers]
        
        # 1. Build Vocab
        vocab_set = set()
        for tokens in processed_headers:
            vocab_set.update(tokens)
        self.vocab = list(vocab_set)
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        V = len(self.vocab)
        
        # 2. Header TF Matrix
        N = len(self.headers)
        self.H_tf = torch.zeros((N, V), dtype=torch.float32, device=self.device)
        self.H_len = torch.zeros(N, dtype=torch.float32, device=self.device)
        
        for i, tokens in enumerate(processed_headers):
            self.H_len[i] = len(tokens)
            for token in tokens:
                if token in self.word_to_idx:
                    self.H_tf[i, self.word_to_idx[token]] += 1
                
        avgdl = torch.mean(self.H_len)
        
        # 3. Compute IDF and Boilerplate Penalty (Filters out generic XBRL dimension tags)
        df = torch.sum(self.H_tf > 0, dim=0).float()
        self.H_idf = torch.log(1 + (N - df + 0.5) / (df + 0.5))
        
        mean_idf = torch.sum(self.H_tf * self.H_idf, dim=1) / (self.H_len + 1e-5)
        min_idf, max_idf = torch.min(mean_idf), torch.max(mean_idf)
        idf_penalty = 0.5 + 0.5 * ((mean_idf - min_idf) / (max_idf - min_idf + 1e-5))
        
        # 4. Compute BM25 Weighted Header Matrix
        k1, b = 1.5, 0.75
        H_tf_sat = (self.H_tf * (k1 + 1)) / (self.H_tf + k1 * (1 - b + b * (self.H_len.unsqueeze(1) / avgdl)))
        self.H_weighted = H_tf_sat * self.H_idf * idf_penalty.unsqueeze(1)

    def map_and_verify(self, top_k=3, permutations=500):
        print(f"Mapping {len(self.queries)} BRSR queries to XBRL with {permutations} permutations each...")
        
        results = []
        Q_true_tf = torch.zeros((len(self.queries), len(self.vocab)), dtype=torch.float32, device=self.device)
        Q_lens = []
        
        for i, q in enumerate(self.queries):
            tokens = self._preprocess(q)
            Q_lens.append(max(len(tokens), 1))
            for token in tokens:
                if token in self.word_to_idx:
                    Q_true_tf[i, self.word_to_idx[token]] += 1
                    
        # 1. Compute True BM25 Scores (Q x N)
        true_scores = torch.matmul(Q_true_tf, self.H_weighted.T)
        
        # 2. Generate Null Distribution (Monte Carlo Vocabulary Sampling)
        total_rand = len(self.queries) * permutations
        Q_rand_tf = torch.zeros((total_rand, len(self.vocab)), dtype=torch.float32, device=self.device)
        
        for i, q_len in enumerate(Q_lens):
            start = i * permutations
            end = start + permutations
            rand_indices = torch.randint(0, len(self.vocab), (permutations, q_len), device=self.device)
            ones = torch.ones_like(rand_indices, dtype=torch.float32)
            Q_rand_tf[start:end].scatter_add_(1, rand_indices, ones)
            
        rand_scores = torch.matmul(Q_rand_tf, self.H_weighted.T)
        rand_scores = rand_scores.view(len(self.queries), permutations, len(self.headers))
        
        # 3. Extract Top K & Compute p-values
        top_scores, top_indices = torch.topk(true_scores, top_k, dim=1)
        top1_scores = top_scores[:, 0]
        top1_indices = top_indices[:, 0]
        
        true_expanded = top1_scores.unsqueeze(1).expand(-1, permutations)
        rand_top1_scores = torch.gather(rand_scores, 2, top1_indices.unsqueeze(1).unsqueeze(2).expand(-1, permutations, 1)).squeeze(2)
        
        p_values = torch.sum(rand_top1_scores >= true_expanded, dim=1).float() / permutations
        
        top_scores_cpu = top_scores.cpu().numpy()
        top_indices_cpu = top_indices.cpu().numpy()
        p_values_cpu = p_values.cpu().numpy()
        
        print("Calculating Kolmogorov (NCD) and compiling final schema...")
        for i, q in enumerate(self.queries):
            q_entities = self._extract_entities(q)
            
            matches = []
            for k in range(top_k):
                h_idx = top_indices_cpu[i, k]
                h_text = self.headers[h_idx]
                score = top_scores_cpu[i, k]
                
                # Entity Boosting (e.g., matching "IND AS" or "ISO 14001")
                h_entities = self._extract_entities(h_text)
                if q_entities and q_entities.intersection(h_entities):
                    score *= 2.0 
                
                ncd = self._compute_ncd(q, h_text)
                matches.append({"header": h_text, "score": round(float(score), 4), "ncd": round(ncd, 4)})
            
            best_match = matches[0]
            p_val = p_values_cpu[i]
            
            # Dynamic NCD threshold based on text length asymmetry
            len_ratio = max(len(q), len(best_match['header'])) / (min(len(q), len(best_match['header'])) + 1)
            ncd_thresh = 0.5 + (0.15 * min(len_ratio, 3))
            
            if best_match['score'] > 0 and p_val < 0.05 and best_match['ncd'] < ncd_thresh:
                status = "Verified"
            elif best_match['score'] > 0 and p_val < 0.10:
                status = "Weak Match - Review"
            else:
                status = "Failed"
                
            results.append({
                "brsr_question": q,
                "xbrl_tag": best_match['header'],
                "bm25_score": best_match['score'],
                "ncd_score": best_match['ncd'],
                "p_value": round(float(p_val), 4),
                "verification_status": status,
                "alt_xbrl_tag_1": matches[1]['header'] if len(matches)>1 else "",
                "alt_score_1": matches[1]['score'] if len(matches)>1 else 0,
            })
            
        return pd.DataFrame(results)

if __name__ == "__main__":
    # 1. Load BRSR Questions
    with open(BASE_DIR / "config" / "taxonomy_map_full.json", 'r') as f:
        taxonomy = json.load(f)
    questions = list(taxonomy.keys())
    
    # 2. Load Extracted XBRL Tags
    xbrl_file = BASE_DIR / "data" / "xbrl_tags_list.txt"
    if not xbrl_file.exists():
        print("Error: xbrl_tags_list.txt not found. Run extract_xbrl_tags.py first.")
        exit()
        
    with open(xbrl_file, 'r') as f:
        xbrl_tags = [line.strip() for line in f if line.strip()]
        
    # 3. Run PyTorch MPS Engine
    mapper = GeneralizedMapper(questions, xbrl_tags, device="mps")
    mapper.build_index()
    df_results = mapper.map_and_verify(top_k=3, permutations=500)
    
    # 4. Save Schema and Markdown Artifact
    csv_out = BASE_DIR / "config" / "brsr_ar_mapping.csv"
    df_results.to_csv(csv_out, index=False)
    
    # Generate Markdown Summary for Human Audit
    md_out = BASE_DIR / "brsr_ar_mapping_review.md"
    with open(md_out, 'w') as f:
        f.write("# BRSR to Annual Report (XBRL) Mapping Schema\n\n")
        f.write("Mathematically verified using BM25, Kolmogorov Complexity (NCD), and Monte Carlo Permutation Testing.\n\n")
        f.write("| BRSR Question | XBRL Tag | BM25 Score | NCD | p-value | Status |\n")
        f.write("|---|---|---|---|---|---|\n")
        for _, row in df_results.iterrows():
            f.write(f"| {row['brsr_question'][:80]}... | `{row['xbrl_tag']}` | {row['bm25_score']} | {row['ncd_score']} | {row['p_value']} | {row['verification_status']} |\n")
    
    print("\n--- BRSR to AR Mapping Summary ---")
    print(df_results['verification_status'].value_counts())
    print(f"\nSchema saved to {csv_out}")
    print(f"Review artifact saved to {md_out}")
