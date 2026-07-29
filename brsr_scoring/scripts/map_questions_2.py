import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi
from scipy.optimize import linear_sum_assignment
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

# Ensure wordnet is downloaded
try:
    wordnet.synsets('test')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

BASE_DIR = Path(__file__).resolve().parent.parent
lemmatizer = WordNetLemmatizer()

# Hardcoded ESG Domain Dictionary
ESG_DICTIONARY = {
    "workers": ["employees", "laborers", "workforce", "personnel", "staff"],
    "ghg": ["greenhouse gas", "emissions", "carbon", "co2", "scope"],
    "turnover": ["attrition", "retention", "revenue", "sales"],
    "water": ["effluent", "discharge", "withdrawal", "consumption"],
    "energy": ["power", "electricity", "fuel", "renewable"],
    "waste": ["hazardous", "recycled", "recovered", "disposal"],
    "injuries": ["ltir", "fatalities", "accidents", "health", "safety"],
    "board": ["directors", "committee", "chairperson"],
}

def camel_case_split(identifier):
    # Splits camelCase and handles numbers (e.g., Scope1 -> Scope 1)
    identifier = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', identifier)
    identifier = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', identifier)
    identifier = re.sub(r'([a-z])(\d)', r'\1 \2', identifier)
    return identifier

def preprocess_text(text):
    if not isinstance(text, str):
        return []
    text = camel_case_split(text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    # Lemmatize to reduce words to root form (e.g., emissions -> emission)
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t]
    return tokens

def expand_query(tokens):
    expanded = list(tokens)
    for word in tokens:
        if word in ESG_DICTIONARY:
            for syn in ESG_DICTIONARY[word]:
                expanded.extend(preprocess_text(syn))
        syns = wordnet.synsets(word)
        added_syns = 0
        for syn in syns:
            if added_syns < 2:
                for lemma in syn.lemmas():
                    if lemma.name().lower() != word and added_syns < 2:
                        expanded.extend(preprocess_text(lemma.name().replace('_', ' ')))
                        added_syns += 1
    return list(set(expanded))

def extract_constraints(text):
    """Extracts hard metadata constraints to prevent cross-mapping."""
    text_lower = text.lower()
    constraints = {"year": "none", "gender": "none", "type": "none"}
    
    if "current year" in text_lower or "current fy" in text_lower:
        constraints["year"] = "current"
    elif "previous year" in text_lower or "previous fy" in text_lower:
        constraints["year"] = "previous"
        
    if re.search(r'\bfemale\b', text_lower):
        constraints["gender"] = "female"
    elif re.search(r'\bmale\b', text_lower):
        constraints["gender"] = "male"
    elif re.search(r'\bother gender\b', text_lower):
        constraints["gender"] = "other"
        
    if re.search(r'\bemployee[s]?\b', text_lower):
        constraints["type"] = "employee"
    elif re.search(r'\bworker[s]?\b', text_lower):
        constraints["type"] = "worker"
        
    return constraints

def apply_penalty(score, q_cons, h_cons):
    """Applies mathematical penalty if constraints conflict."""
    penalty = 1.0
    # Year constraint (crucial for preventing current/previous year overlaps)
    if q_cons["year"] != "none" and h_cons["year"] != "none":
        if q_cons["year"] != h_cons["year"]:
            penalty *= 0.1
            
    # Gender constraint
    if q_cons["gender"] != "none" and h_cons["gender"] != "none":
        if q_cons["gender"] != h_cons["gender"]:
            penalty *= 0.1
            
    # Worker/Employee constraint
    if q_cons["type"] != "none" and h_cons["type"] != "none":
        if q_cons["type"] != h_cons["type"]:
            penalty *= 0.1
            
    return score * penalty

def main():
    print("Loading data...")
    header_file = BASE_DIR / "data" / "csv_headers_list.txt"
    if not header_file.exists():
        print(f"Error: {header_file} not found.")
        return
        
    with open(header_file, 'r') as f:
        headers = [line.strip() for line in f if line.strip()]
        
    q_file = BASE_DIR / "config" / "taxonomy_map_full.json"
    with open(q_file, 'r') as f:
        taxonomy = json.load(f)
        
    questions = list(taxonomy.keys())
    question_ids = [meta['question_id'] for meta in taxonomy.values()]
    
    print(f"Loaded {len(questions)} questions and {len(headers)} CSV headers.")
    
    print("Preprocessing and Expanding Queries...")
    processed_questions = []
    q_constraints = []
    for q in questions:
        tokens = preprocess_text(q)
        exp_tokens = expand_query(tokens)
        processed_questions.append(exp_tokens)
        q_constraints.append(extract_constraints(q))
        
    processed_headers = [preprocess_text(h) for h in headers]
    h_constraints = [extract_constraints(h) for h in headers]
    
    print("Building BM25 Model (Replacing LSA)...")
    bm25 = BM25Okapi(processed_headers)
    
    print("Calculating Similarity Matrix with Hard Constraints...")
    similarity_matrix = np.zeros((len(questions), len(headers)))
    
    for i, q_tokens in enumerate(processed_questions):
        scores = bm25.get_scores(q_tokens)
        for j, score in enumerate(scores):
            # Apply penalties for Current/Previous year, Male/Female, etc.
            similarity_matrix[i, j] = apply_penalty(score, q_constraints[i], h_constraints[j])
            
    print("Phase 3: Global Optimization (Hungarian Algorithm)...")
    cost_matrix = -similarity_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    optimal_mapping = {r: c for r, c in zip(row_ind, col_ind)}
    
    print("Phase 4: Generating Mapping Review CSV...")
    results = []
    
    # Calculate dynamic thresholds for confidence flags based on BM25 distribution
    opt_scores = [similarity_matrix[i, optimal_mapping[i]] for i in range(len(questions))]
    low_thresh = np.percentile(opt_scores, 25) # Bottom 25% are Low Confidence
    
    for i in range(len(questions)):
        q_id = question_ids[i]
        q_text = questions[i]
        
        scores = similarity_matrix[i]
        opt_idx = optimal_mapping[i]
        opt_score = scores[opt_idx]
        opt_header = headers[opt_idx]
        
        # Get top 3 overall matches
        top_indices = np.argsort(scores)[::-1][:3]
        
        best_match_1_idx = top_indices[0]
        best_match_2_idx = top_indices[1] if len(top_indices) > 1 else -1
        
        score_1 = scores[best_match_1_idx]
        score_2 = scores[best_match_2_idx] if best_match_2_idx != -1 else 0
        
        margin_of_victory = score_1 - score_2
        
        confidence_flag = "High Confidence"
        if opt_score < low_thresh:
            confidence_flag = "Low Confidence"
        elif margin_of_victory < 1.0: # BM25 scores usually have margins > 1
            confidence_flag = "Ambiguous"
            
        res = {
            "question_id": q_id,
            "question_text": q_text,
            "global_optimal_match": opt_header,
            "optimal_score": round(opt_score, 4),
            "alt_match_1": headers[top_indices[0]],
            "alt_score_1": round(scores[top_indices[0]], 4),
            "alt_match_2": headers[top_indices[1]] if len(top_indices)>1 else "",
            "alt_score_2": round(scores[top_indices[1]], 4) if len(top_indices)>1 else 0.0,
            "alt_match_3": headers[top_indices[2]] if len(top_indices)>2 else "",
            "alt_score_3": round(scores[top_indices[2]], 4) if len(top_indices)>2 else 0.0,
            "confidence_flag": confidence_flag,
            "final_selected_column": opt_header
        }
        results.append(res)
        
    df_results = pd.DataFrame(results)
    out_file = BASE_DIR / "config" / "mapping_review.csv"
    df_results.to_csv(out_file, index=False)
    
    print(f"\nSuccessfully wrote mappings to {out_file}")
    
    counts = df_results['confidence_flag'].value_counts()
    print("\nConfidence Summary:")
    print(counts)

if __name__ == "__main__":
    main()
