import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment
import nltk
from nltk.corpus import wordnet

# Download required NLTK data
try:
    wordnet.synsets('test')
except LookupError:
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

BASE_DIR = Path(__file__).resolve().parent.parent

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
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return ' '.join([m.group(0) for m in matches])

def preprocess_text(text, is_header=False):
    if not isinstance(text, str):
        return ""
    if is_header:
        # Split underscores and camelCase for headers
        text = text.replace('_', ' ')
        text = camel_case_split(text)
        
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text.strip()

def expand_query(text):
    words = text.split()
    expanded = list(words)
    
    for word in words:
        # 1. ESG Dictionary
        if word in ESG_DICTIONARY:
            expanded.extend(ESG_DICTIONARY[word])
            
        # 2. WordNet Synonyms
        syns = wordnet.synsets(word)
        added_syns = 0
        added_hyper = 0
        for syn in syns:
            if added_syns < 2:
                for lemma in syn.lemmas():
                    if lemma.name().lower() != word and added_syns < 2:
                        expanded.append(lemma.name().replace('_', ' '))
                        added_syns += 1
            if added_hyper < 1 and syn.hypernyms():
                hyper = syn.hypernyms()[0]
                expanded.append(hyper.lemmas()[0].name().replace('_', ' '))
                added_hyper += 1
                
    return " ".join(expanded)

def main():
    print("Loading data...")
    # Load headers
    header_file = BASE_DIR / "data" / "csv_headers_list.txt"
    if not header_file.exists():
        print(f"Error: {header_file} not found. Please run the header extraction first.")
        return
        
    with open(header_file, 'r') as f:
        headers = [line.strip() for line in f if line.strip()]
        
    # Load 315 questions
    q_file = BASE_DIR / "config" / "taxonomy_map_full.json"
    with open(q_file, 'r') as f:
        taxonomy = json.load(f)
        
    questions = []
    question_ids = []
    for q_text, meta in taxonomy.items():
        questions.append(q_text)
        question_ids.append(meta['question_id'])
        
    print(f"Loaded {len(questions)} questions and {len(headers)} CSV headers.")
    
    # Phase 1: Preprocessing & Expansion
    print("Phase 1: Ontological Expansion...")
    expanded_questions = [expand_query(preprocess_text(q)) for q in questions]
    processed_headers = [preprocess_text(h, is_header=True) for h in headers]
    
    # Phase 2: Vectorization & LSA
    print("Phase 2: TF-IDF and Truncated SVD (LSA)...")
    corpus = expanded_questions + processed_headers
    
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Truncated SVD (LSA)
    svd = TruncatedSVD(n_components=100, random_state=42)
    lsa_matrix = svd.fit_transform(tfidf_matrix)
    
    q_vectors = lsa_matrix[:len(questions)]
    h_vectors = lsa_matrix[len(questions):]
    
    # Cosine Similarity: Shape (315, 7995)
    similarity_matrix = cosine_similarity(q_vectors, h_vectors)
    
    # Phase 3: Global Optimization (Hungarian Algorithm)
    print("Phase 3: Global Optimization (Hungarian Algorithm)...")
    # linear_sum_assignment minimizes cost, so we pass negative similarity
    cost_matrix = -similarity_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # row_ind corresponds to question index, col_ind corresponds to header index
    optimal_mapping = {r: c for r, c in zip(row_ind, col_ind)}
    
    # Phase 4: Confidence Thresholding & Output Generation
    print("Phase 4: Generating Mapping Review CSV...")
    results = []
    
    for i in range(len(questions)):
        q_id = question_ids[i]
        q_text = questions[i]
        
        # Get all scores for this question
        scores = similarity_matrix[i]
        
        # Optimal match from Hungarian
        opt_idx = optimal_mapping[i]
        opt_score = scores[opt_idx]
        opt_header = headers[opt_idx]
        
        # Get top 3 overall (might be different from optimal if there were conflicts)
        top_indices = np.argsort(scores)[::-1][:3]
        
        best_match_1_idx = top_indices[0]
        best_match_2_idx = top_indices[1] if len(top_indices) > 1 else -1
        
        score_1 = scores[best_match_1_idx]
        score_2 = scores[best_match_2_idx] if best_match_2_idx != -1 else 0
        
        # Confidence Metrics
        margin_of_victory = score_1 - score_2
        
        confidence_flag = "High Confidence"
        if opt_score < 0.3:
            confidence_flag = "Low Confidence"
        elif margin_of_victory < 0.05:
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
    
    print(f"Successfully wrote mappings to {out_file}")
    
    # Print a quick summary of confidence
    counts = df_results['confidence_flag'].value_counts()
    print("\nConfidence Summary:")
    print(counts)
    print("\nPlease review the 'Low Confidence' and 'Ambiguous' flags in mapping_review.csv.")

if __name__ == "__main__":
    main()
