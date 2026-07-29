import pandas as pd
import requests
import json
from pathlib import Path
import difflib

BASE_DIR = Path(__file__).resolve().parent.parent

class LLMFinalJudge:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        # We will use Ollama API instead of loading locally into GPU via transformers
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model_id = "gemma4:latest"
        print(f"Using local Ollama model: {self.model_id} for Semantic Judging...")
        
        # Test connection
        try:
            resp = requests.get("http://localhost:11434/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            if self.model_id not in models:
                print(f"Warning: Model {self.model_id} not found in Ollama list. Make sure it is downloaded.")
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
        
    def aggregate_candidates(self):
        print("Aggregating candidates from all mathematical pipelines...")
        # Define file paths
        files = {
            "brsr": BASE_DIR / "config" / "mapping_review.csv",
            "ar": BASE_DIR / "config" / "brsr_ar_mapping.csv",
            "kalman": BASE_DIR / "config" / "kalman_fused_mapping.csv"
        }
        
        dfs = []
        for name, path in files.items():
            if path.exists():
                df = pd.read_csv(path)
                # Standardize question column name
                if 'brsr_question' in df.columns:
                    df = df.rename(columns={'brsr_question': 'question'})
                elif 'question_text' in df.columns:
                    df = df.rename(columns={'question_text': 'question'})
                
                # Dynamically identify candidate columns
                candidate_cols = []
                for col in df.columns:
                    if col in ['global_optimal_match', 'xbrl_tag', 'kalman_fused_match', 
                               'alt_match_1', 'alt_match_2', 'alt_xbrl_tag_1', 'alt_xbrl_tag_2',
                               'kalman_alt_match_1', 'alt_fused_score_1']:
                        # Exclude score columns if they accidentally share a name prefix
                        if "score" not in col:
                            candidate_cols.append(col)
                            
                if candidate_cols:
                    dfs.append(df[['question'] + candidate_cols].copy())
            else:
                print(f"Warning: {path.name} not found. Skipping.")
                
        if not dfs:
            raise FileNotFoundError("No mapping CSVs found. Please run previous pipelines.")
            
        # Merge all candidates into a single list per question
        # First, flatten the rows of each df into a single 'candidates' column
        for d in dfs:
            cols = [c for c in d.columns if c != 'question']
            d['candidates'] = d.apply(lambda row: [row[c] for c in cols if pd.notna(row[c]) and str(row[c]).strip() and str(row[c]) != 'nan'], axis=1)
            
        # Concat and group
        df_concat = pd.concat([d[['question', 'candidates']] for d in dfs])
        df_merged = df_concat.groupby('question').agg({'candidates': 'sum'}).reset_index()
        
        # Deduplicate
        df_merged['candidates'] = df_merged['candidates'].apply(lambda lst: list(set([str(c) for c in lst])))
        return df_merged
        
    def query_llm(self, question, candidates):
        if len(candidates) == 1:
            return candidates[0]
            
        # Format the candidate list for the prompt
        candidate_str = "\n".join([f"- {c}" for c in candidates])
        
        system_prompt = "You are an expert data mapper. You will be given a Question and a Candidate List. Your job is to select the candidate that best semantically matches the question. You MUST output the exact string from the list. Do not output anything else."
        user_prompt = f"Question: {question}\n\nCandidate List:\n{candidate_str}\n\nSelected String:"
        
        # Apply chat template via Ollama (Gemma does not support system roles natively)
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload)
            resp.raise_for_status()
            response = resp.json().get("message", {}).get("content", "").strip()
            # Remove any wrapping quotes that Gemma might add
            if response.startswith("'") and response.endswith("'"):
                response = response[1:-1]
            elif response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
        except Exception as e:
            print(f"Ollama API error: {e}")
            return candidates[0]
        
        # Fuzzy match enforcement (Safety net against LLM adding stray punctuation)
        if response not in candidates:
            # Maybe the model printed it with a bullet point or quotes
            for c in candidates:
                if c in response:
                    return c
                    
            closest_matches = difflib.get_close_matches(response, candidates, n=1, cutoff=0.6)
            if closest_matches:
                return closest_matches[0]
            else:
                return candidates[0]
                
        return response

    def run(self):
        self.load_model()
        df = self.aggregate_candidates()
        
        print(f"Judging {len(df)} questions via LLM...")
        
        # Checkpoint file to resume from
        out_file = BASE_DIR / "config" / "llm_judged_schema.csv"
        
        # Load existing if available to resume
        if out_file.exists():
            print("Loading existing progress...")
            existing_df = pd.read_csv(out_file)
            # Merge logic: if we already have a judgment, keep it
            df = df.set_index('question').join(existing_df.set_index('question')[['llm_final_match']], how='left').reset_index()
        else:
            df['llm_final_match'] = None

        for idx, row in df.iterrows():
            if pd.notna(row.get('llm_final_match')):
                continue
                
            q = row['question']
            cands = row['candidates']
            
            # Handle string representation of lists if loaded from CSV
            if isinstance(cands, str):
                import ast
                cands = ast.literal_eval(cands)
            
            if not cands:
                df.at[idx, 'llm_final_match'] = ""
                continue
                
            llm_choice = self.query_llm(q, cands)
            df.at[idx, 'llm_final_match'] = llm_choice
            
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(df)}...")
                df.to_csv(out_file, index=False)
                
        df.to_csv(out_file, index=False)
        print(f"\nFinal LLM judged schema saved to {out_file}")
        return df

if __name__ == "__main__":
    judge = LLMFinalJudge()
    df_final = judge.run()
    
    print("\n--- Sample Final Mappings ---")
    print(df_final[['question', 'llm_final_match']].head(10).to_markdown(index=False))
