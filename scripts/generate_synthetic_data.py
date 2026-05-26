import json
import requests
import pandas as pd
import sys

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "phi4-mini:latest"

def generate_synthetic_data():
    prompt = """
You are an expert synthetic data generator for enterprise testing.
Generate a JSON array of exactly 5 fictional companies.
For each company, provide realistic financial and ESG data based exactly on these keys:
- "Company_Name"
- "BRSR_Scope1" (numeric)
- "BRSR_Scope2" (numeric)
- "BRSR_Scope3" (numeric)
- "BRSR_Renewable_Electricity" (numeric)
- "BRSR_Renewable_Fuel" (numeric)
- "BRSR_NonRenewable_Electricity" (numeric)
- "BRSR_NonRenewable_Fuel" (numeric)
- "BRSR_Water_Withdrawal_Total" (numeric)
- "BRSR_Board_Female" (integer)
- "BRSR_Board_Total" (integer)
- "BRSR_Turnover_Total" (percentage as decimal)

CRITICAL INSTRUCTION: Inject adversarial edge cases. 
- Make Company 3 have a null (None) value for all Energy fields.
- Make Company 4 have 0 for Female board members.
- Make Company 5 have missing (None) Scope 3 emissions.

OUTPUT ONLY VALID JSON. Do not include markdown formatting or explanations.
[
    {...}
]
"""
    print(f"Requesting synthetic data from local {MODEL}...")
    try:
        response = requests.post(OLLAMA_API, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        })
        response.raise_for_status()
        
        data_text = response.json().get('response', '')
        try:
            data_json = json.loads(data_text)
            df = pd.DataFrame(data_json)
            df.to_csv('testing/synthetic/mock_brsr_data.csv', index=False)
            print("Successfully generated and saved testing/synthetic/mock_brsr_data.csv")
            return df
        except json.JSONDecodeError:
            print("Error: LLM did not return valid JSON.")
            print(data_text)
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_synthetic_data()
