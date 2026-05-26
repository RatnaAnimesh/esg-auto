import json
import requests
import pandas as pd
import sys

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "phi4-mini:latest"

def run_llm(prompt, format=None):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.0
    }
    if format:
        payload["format"] = format
        
    response = requests.post(OLLAMA_API, json=payload)
    response.raise_for_status()
    return response.json().get('response', '').strip()

def main():
    try:
        df = pd.read_csv('testing/synthetic/filled_questionnaire.csv', index_col=0)
    except FileNotFoundError:
        print("Error: filled_questionnaire.csv not found.")
        sys.exit(1)

    # Grab the data for Company_1 (index 1 since index 0 is Metadata Formula)
    company_data = df.iloc[1].to_dict()
    company_name = company_data.pop('Company_Name')

    print(f"\n--- 1. Testing Generation for {company_name} ---")
    
    # Format the facts for the prompt
    facts = "\n".join([f"{k}: {v}" for k, v in company_data.items() if k != "Question"])
    
    generation_prompt = f"""
    You are an expert financial analyst. Write a concise, 2-sentence summary of the company's 
    environmental profile based strictly on the following data points. Do not invent numbers.
    If a data point says "Undisclosed/Missing", mention that it is not disclosed.
    
    Data:
    {facts}
    """
    
    generated_text = run_llm(generation_prompt)
    print("\n[Generated Narrative]:")
    print(generated_text)
    
    print("\n--- 2. Executing LLM-as-a-Judge Evaluation ---")
    
    evaluation_prompt = f"""
    You are an autonomous auditor evaluating an AI-generated report for factual hallucinations.
    Compare the Generated Narrative against the Ground Truth Facts.
    
    Ground Truth Facts:
    {facts}
    
    Generated Narrative:
    {generated_text}
    
    Did the narrative invent any numbers or misrepresent any facts from the Ground Truth? 
    Reply ONLY with valid JSON in this format:
    {{
        "Hallucination_Detected": true/false,
        "Reason": "explanation of what was hallucinated, or 'All facts match exactly.'"
    }}
    """
    
    eval_result = run_llm(evaluation_prompt, format="json")
    print("\n[Audit Result]:")
    try:
        parsed_result = json.loads(eval_result)
        print(json.dumps(parsed_result, indent=2))
        
        if parsed_result.get("Hallucination_Detected"):
            print("\n❌ JUDGE FAILED: The model hallucinated.")
        else:
            print("\n✅ JUDGE PASSED: The model strictly adhered to the schema and facts.")
            
    except json.JSONDecodeError:
        print(eval_result)
        print("\nError parsing JSON from Judge.")

if __name__ == "__main__":
    main()
