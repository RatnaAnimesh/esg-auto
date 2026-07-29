import re
import pandas as pd
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi
from scipy.optimize import linear_sum_assignment
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

try:
    wordnet.synsets('test')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

BASE_DIR = Path(__file__).resolve().parent.parent
lemmatizer = WordNetLemmatizer()

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
    penalty = 1.0
    if q_cons["year"] != "none" and h_cons["year"] != "none":
        if q_cons["year"] != h_cons["year"]:
            penalty *= 0.1
    if q_cons["gender"] != "none" and h_cons["gender"] != "none":
        if q_cons["gender"] != h_cons["gender"]:
            penalty *= 0.1
    if q_cons["type"] != "none" and h_cons["type"] != "none":
        if q_cons["type"] != h_cons["type"]:
            penalty *= 0.1
    return score * penalty

def main():
    print("Loading data...")
    header_file = BASE_DIR / "data" / "csv_headers_list.txt"
    with open(header_file, 'r') as f:
        headers = [line.strip() for line in f if line.strip()]
        
    schema_file = BASE_DIR / "config" / "master_schema.csv"
    schema_df = pd.read_csv(schema_file)
    
    # Build Master Queries (Question Text + XBRL Tag)
    queries = []
    question_ids = []
    original_texts = []
    
    for _, row in schema_df.iterrows():
        q_id = row['question_id']
        q_text = str(row['question_text'])
        xbrl = str(row['xbrl_tag'])
        
        # Concatenate for denser semantic target
        if pd.isna(row['xbrl_tag']) or xbrl == "nan" or xbrl == "":
            combined_query = q_text
        else:
            combined_query = f"{q_text} {xbrl}"
            
        queries.append(combined_query)
        question_ids.append(q_id)
        original_texts.append(q_text)
        
    print(f"Loaded {len(queries)} Master Schema queries and {len(headers)} raw CSV headers.")
    
    print("Preprocessing and Expanding Queries...")
    processed_queries = []
    q_constraints = []
    for q in queries:
        tokens = preprocess_text(q)
        exp_tokens = expand_query(tokens)
        processed_queries.append(exp_tokens)
        q_constraints.append(extract_constraints(q))
        
    processed_headers = [preprocess_text(h) for h in headers]
    h_constraints = [extract_constraints(h) for h in headers]
    
    print("Building BM25 Model on Raw Headers...")
    bm25 = BM25Okapi(processed_headers)
    
    print("Calculating Similarity Matrix with Hard Constraints...")
    similarity_matrix = np.zeros((len(queries), len(headers)))
    
    for i, q_tokens in enumerate(processed_queries):
        scores = bm25.get_scores(q_tokens)
        for j, score in enumerate(scores):
            similarity_matrix[i, j] = apply_penalty(score, q_constraints[i], h_constraints[j])
            
    print("Global Optimization (Hungarian Algorithm)...")
    cost_matrix = -similarity_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    optimal_mapping = {r: c for r, c in zip(row_ind, col_ind)}
    
    print("Generating Mapping Review CSV...")
    results = []
    
    opt_scores = [similarity_matrix[i, optimal_mapping[i]] for i in range(len(queries))]
    low_thresh = np.percentile(opt_scores, 25)
    
    for i in range(len(queries)):
        q_id = question_ids[i]
        q_text = original_texts[i]
        q_combined = queries[i]
        
        scores = similarity_matrix[i]
        opt_idx = optimal_mapping[i]
        opt_score = scores[opt_idx]
        opt_header = headers[opt_idx]
        
        top_indices = np.argsort(scores)[::-1][:3]
        best_match_1_idx = top_indices[0]
        best_match_2_idx = top_indices[1] if len(top_indices) > 1 else -1
        
        score_1 = scores[best_match_1_idx]
        score_2 = scores[best_match_2_idx] if best_match_2_idx != -1 else 0
        
        margin_of_victory = score_1 - score_2
        
        confidence_flag = "High Confidence"
        if opt_score < low_thresh:
            confidence_flag = "Low Confidence"
        elif margin_of_victory < 1.0:
            confidence_flag = "Ambiguous"
            
        res = {
            "question_id": q_id,
            "original_question_text": q_text,
            "combined_query": q_combined,
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
    out_file = BASE_DIR / "config" / "raw_to_master_mapping.csv"
    df_results.to_csv(out_file, index=False)
    
    print(f"\nSuccessfully wrote mappings to {out_file}")
    print("\nConfidence Summary:")
    print(df_results['confidence_flag'].value_counts())

if __name__ == "__main__":
    main()
