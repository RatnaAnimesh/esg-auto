import argparse
import pandas as pd
import requests
import json
import os

def get_llm_response(prompt, model="deepseek-r1:8b", max_retries=3):
    # This acts as the RAG query orchestration
    # In a full implementation, we would search our Vector DB for the exact question
    # and retrieve the relevant JSON chunks from `data/processed/annual_reports/{company_symbol}.json`
    # and inject them into the prompt here.
    
    # unstructured_context = retrieve_unstructured_context(company_symbol, prompt)
    # prompt += f"\n[UNSTRUCTURED CONTEXT FROM ANNUAL REPORT]: {unstructured_context}"

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get('response', '{}')
    except Exception as e:
        print(f"Error querying local LLM: {e}")
        return "{}"

def query_local_llm(prompt, model="phi4-mini"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get('response', '{}')
    except Exception as e:
        print(f"Error querying local LLM: {e}")
        return "{}"

def generate_report(peer_analysis_path, company_name, model="phi4-mini"):
    print(f"Loading top deterministic drivers from {peer_analysis_path}...")
    with open(peer_analysis_path, 'r') as f:
        data = json.load(f)
        
    e_kw = ['emission', 'energy', 'water', 'waste', 'environment', 'climate', 'scope', 'renewable', 'fuel']
    s_kw = ['employee', 'turnover', 'training', 'worker', 'injury', 'health', 'safety', 'maternity', 'paternity', 'social', 'community', 'diversity', 'women', 'hiring', 'attrition']
    
    e_drivers_list, s_drivers_list, g_drivers_list = [], [], []
    for a in data.get('Analysis', []):
        metric = a['Metric']
        lower_col = metric.lower()
        cat = 'G'
        if any(k in lower_col for k in e_kw): cat = 'E'
        elif any(k in lower_col for k in s_kw): cat = 'S'
        
        line = f"- {metric}: {a['Target_Company_Value']} (Weight: {a['Linear_Weight']:.4f}, Industry Avg: {a['Industry_Average']})"
        if cat == 'E': e_drivers_list.append(line)
        elif cat == 'S': s_drivers_list.append(line)
        else: g_drivers_list.append(line)
        
    e_drivers = "\\n".join(e_drivers_list) if e_drivers_list else "None"
    s_drivers = "\\n".join(s_drivers_list) if s_drivers_list else "None"
    g_drivers = "\\n".join(g_drivers_list) if g_drivers_list else "None"
    
    tot_score = data.get("Predicted_ESG_Score", "N/A")
    e_score = data.get("Predicted_E_Score", "N/A")
    s_score = data.get("Predicted_S_Score", "N/A")
    g_score = data.get("Predicted_G_Score", "N/A")
    
    print(f"RAG Retrieval: Querying brsr_consolidated.csv for {company_name} verified ticker...")
    nse_symbol = company_name  # Fallback
    try:
        brsr_df = pd.read_csv("data/processed/consolidated/brsr_consolidated.csv", low_memory=False)
        company_row = brsr_df[(brsr_df['Name Of The Company'] == company_name) | (brsr_df['CompanyName'] == company_name)]
        if not company_row.empty:
            extracted_symbol = str(company_row.iloc[0].get('NSESymbol', ''))
            if extracted_symbol and extracted_symbol.lower() != 'nan':
                nse_symbol = extracted_symbol
    except Exception:
        pass

    print("Starting Agentic ReAct Loop...")
    
    # Base Prompt
    prompt = f"""
You are a senior ESG financial analyst at NSRAL writing the Executive Summary for {company_name}.
You must use a strict institutional tone. 

STRICT TICKER CONSTRAINT: 
The verified official abbreviation/ticker for this company is: {nse_symbol}
You MUST use '{nse_symbol}' exclusively when referring to the company by abbreviation. DO NOT invent, generate, or hallucinate any other acronyms (such as TSML, etc.). If you fail to use '{nse_symbol}', the report will be rejected.

You have access to a massive database of verified ESG metrics. 
If you need any specific data points (e.g., "Corporate Identity Number", "Date Of Incorporation", "NSESymbol"), you can QUERY the database.
To query, output EXACTLY this string and nothing else:
QUERY: <Exact Column Name>

Once you have all the information you need, you must output the final report as a valid JSON object with EXACTLY the following five keys (no markdown formatting):
- "company_overview": A comprehensive, multi-paragraph overview of the company's business model, global footprint, and core operations (minimum 150 words).
- "overall_summary": A detailed, multi-paragraph summary analyzing the overarching ESG rating, how it relates to the industry, and the key narrative (minimum 200 words).
- "environment": A deep, multi-paragraph analysis of the Environmental drivers, citing the metrics heavily (minimum 200 words).
- "social": A deep, multi-paragraph analysis of the Social drivers, citing the metrics heavily (minimum 200 words).
- "governance": A deep, multi-paragraph analysis of the Governance drivers, citing the metrics heavily (minimum 200 words).

CRITICAL INSTRUCTION: EACH section must be extremely detailed, comprehensive, and well-written. Do not output brief single-sentence paragraphs. You must expand on the implications of the data and provide deep financial and ESG insights.

Do not hallucinate numbers. Base your analysis on these mathematically determined top ESG metrics driving their score:

MATHEMATICALLY PREDICTED SCORES (OUT OF 100):
- Total ESG Score: {tot_score}
- Environment (E) Sub-Score: {e_score}
- Social (S) Sub-Score: {s_score}
- Governance (G) Sub-Score: {g_score}

TOP ENVIRONMENTAL DRIVERS:
{e_drivers}

TOP SOCIAL DRIVERS:
{s_drivers}

TOP GOVERNANCE DRIVERS:
{g_drivers}
"""
    
    max_queries = 5
    query_count = 0
    conversation_history = prompt

    while query_count < max_queries:
        response_text = query_local_llm(conversation_history, model=model).strip()
        
        # Check if the LLM wants to query the database
        if response_text.startswith("QUERY:"):
            query_count += 1
            column_requested = response_text.replace("QUERY:", "").strip()
            print(f"[{query_count}/{max_queries}] LLM Querying Database for: {column_requested}")
            
            # Perform RAG lookup
            result = "Not Found or Empty"
            try:
                brsr_df = pd.read_csv("data/processed/consolidated/brsr_consolidated.csv", low_memory=False)
                company_row = brsr_df[(brsr_df['Name Of The Company'] == company_name) | (brsr_df['CompanyName'] == company_name)]
                if not company_row.empty and column_requested in company_row.columns:
                    val = str(company_row.iloc[0].get(column_requested, ''))
                    if val and val.lower() != 'nan':
                        result = val
            except Exception as e:
                result = f"Error querying database: {str(e)}"
            
            print(f" -> Result: {result}")
            # Feed the result back to the LLM
            conversation_history += f"\\n\\n{response_text}\\nSYSTEM RESPONSE: The value for '{column_requested}' is '{result}'. Now continue."
        else:
            # LLM is (hopefully) outputting the final JSON
            break

    if query_count >= max_queries:
        print("Maximum queries reached. Forcing final JSON output.")
        force_prompt = conversation_history + "\\n\\nSYSTEM: Maximum queries reached. You MUST output the final JSON object now."
        response_text = query_local_llm(force_prompt, model=model).strip()

    import re
    company_safe = re.sub(r'[^a-zA-Z0-9]+', '_', company_name)
    os.makedirs("data/reports/json_data", exist_ok=True)
    report_path = f"data/reports/json_data/{company_safe}_Executive_Summary.json"
    
    import re
    # Strip <think> tags for DeepSeek R1 compatibility
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
    
    try:
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        parsed_json = json.loads(response_text)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=4)
        print(f"\\nSuccessfully generated JSON Narrative Blocks at: {report_path}")
    except json.JSONDecodeError:
        print("Failed to parse LLM response as JSON. Saving raw output for debugging.")
        with open(report_path.replace(".json", "_failed.txt"), "w") as f:
            f.write(response_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Deterministic Narrative")
    parser.add_argument("--peer_analysis_path", type=str, required=True, help="Path to peer analysis JSON")
    parser.add_argument("--company", type=str, required=True, help="Exact company name")
    parser.add_argument("--model", type=str, default="deepseek-r1:8b", help="Local Ollama model name")
    
    args = parser.parse_args()
    generate_report(args.peer_analysis_path, args.company, model=args.model)

"""
# =====================================================================
# FUTURE vLLM / HUGGINGFACE INTEGRATION: HIDDEN STATE UNCERTAINTY PROBE
# =====================================================================
# When switching from Ollama to a native PyTorch/HuggingFace server (like vLLM 
# with hidden states exposed, or a native inference script), you can use this 
# logic to detect hallucination BEFORE it happens by probing the internal weights.

'''
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def probe_hidden_states_and_generate(prompt, model_path="microsoft/phi-4-mini"):
    # Load model with hidden states enabled
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, output_hidden_states=True)
    
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # We generate token by token to monitor the hidden states in real time
    generated_tokens = inputs.input_ids
    
    for i in range(MAX_NEW_TOKENS):
        with torch.no_grad():
            outputs = model(generated_tokens)
            
        # The hidden states of the last layer for the current token
        # outputs.hidden_states is a tuple of all layers: (embedding, layer_1, ..., layer_N)
        last_layer_hidden_state = outputs.hidden_states[-1][0, -1, :]
        
        # Calculate uncertainty. In practice, you would train a linear classifier (probe)
        # on these hidden states using a dataset of known hallucinations.
        # For demonstration, we calculate the L2 norm variance or entropy as a proxy.
        uncertainty_score = calculate_uncertainty(last_layer_hidden_state)
        
        if uncertainty_score > CONFIDENCE_FLOOR_THRESHOLD:
            print("INTERNAL UNCERTAINTY SPIKE DETECTED. HALTING GENERATION.")
            # Trigger Pandas RAG lookup here using the context so far
            retrieved_fact = retrieve_from_csv(context=tokenizer.decode(generated_tokens[0]))
            
            # Inject fact into prompt and restart generation
            new_prompt = tokenizer.decode(generated_tokens[0]) + f"\\n[SYSTEM INJECTION: {retrieved_fact}]"
            return probe_hidden_states_and_generate(new_prompt, model_path)
            
        # If confident, append the argmax token and continue
        next_token_logits = outputs.logits[0, -1, :]
        next_token_id = torch.argmax(next_token_logits).unsqueeze(0).unsqueeze(0)
        generated_tokens = torch.cat((generated_tokens, next_token_id), dim=-1)
        
        if next_token_id.item() == tokenizer.eos_token_id:
            break
            
    return tokenizer.decode(generated_tokens[0])
'''
"""
