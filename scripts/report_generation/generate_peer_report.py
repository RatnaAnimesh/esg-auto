import argparse
import pandas as pd
import requests
import json
import os
import re

def query_local_llm(prompt, model="deepseek-r1:8b", format_json=True):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 32768}
    }
    if format_json:
        payload["format"] = "json"
        
    try:
        response = requests.post(url, json=payload, timeout=1800)
        response.raise_for_status()
        return response.json().get('response', '{}')
    except Exception as e:
        print(f"Error querying local LLM: {e}")
        return "{}"

def extract_python_code(response_text):
    import re
    match = re.search(r'```python\s*(.*?)\s*```', response_text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Fallback if no language specified
    match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
    if match:
        return match.group(1)
        
    return response_text # Hope for the best

def generate_charts(parsed_json, company_name):
    import subprocess
    import tempfile
    
    clean_company_name = company_name.replace(" Limited", "").replace(" Ltd.", "").replace(" Ltd", "").strip()
    
    print("\\nOrchestrating Chart Generation with qwen2.5-coder...")
    for pillar in ["environmental", "social", "governance"]:
        if pillar == "environmental":
            target_color = "#72ff85"
        elif pillar == "social":
            target_color = "#f2f8a1"
        else:
            target_color = "#a1cff8"
            
        metrics = parsed_json.get(pillar, [])
        for metric in metrics:
            if isinstance(metric, dict) and metric.get("requires_chart", False):
                m_name = metric.get('metric_name', 'unknown_metric')
                
                # 1. Anonymize Peers
                raw_peers = metric.get('peer_values', {})
                anon_peers = {}
                peer_idx = 1
                for peer, val in raw_peers.items():
                    try:
                        anon_peers[f"PEER{peer_idx}"] = float(val)
                        peer_idx += 1
                    except:
                        pass
                
                # Parse target val
                try:
                    target_val = float(metric.get('company_value', 0))
                except:
                    target_val = 0.0
                
                # 2. Percentage Scaling
                if 'Percentage' in m_name or '%' in m_name:
                    target_val = round(target_val * 100, 1)
                    for peer in anon_peers:
                        anon_peers[peer] = round(anon_peers[peer] * 100, 1)
                
                # 3. Variance Filter (10% Rule)
                all_vals = [target_val] + list(anon_peers.values())
                if len(all_vals) > 1:
                    max_v = max(all_vals)
                    min_v = min(all_vals)
                    if max_v != 0:
                        if (max_v - min_v) / abs(max_v) <= 0.10:
                            print(f"Skipping chart for {m_name} due to <10% variance.")
                            continue
                    elif max_v == 0 and min_v == 0:
                        print(f"Skipping chart for {m_name} (all values are 0).")
                        continue
                
                print(f"Generating chart for {m_name}...")
                
                data_dict = {clean_company_name: target_val}
                data_dict.update(anon_peers)
                
                chart_prompt = f"""
You are an expert Python data visualization engineer.
Write a seaborn script to generate a chart for the metric: '{m_name}'.

Constraint 1: You MUST output ONLY valid python code enclosed in ```python blocks. Do not explain.
Constraint 2: You MUST use the exact python boilerplate template provided below. Fill in the plotting logic where indicated. Do NOT change the data dictionary, colors, or save path.
Constraint 3: Use `ax.bar_label(ax.containers[0])` for labels if it's a bar chart. Do not loop over patches. Rotate x-axis labels by 45 degrees.
Constraint 4: If you use the `fmt` argument in `bar_label`, you MUST use standard C-style formatting like `fmt='%.1f'` or `fmt='%.1f%%'`. DO NOT use `{{y}}` or `{{x}}` format strings as they will cause a KeyError.

TEMPLATE:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Data
data = {data_dict}
df = pd.DataFrame(list(data.items()), columns=['Company', 'Value'])

# Colors
colors = ['{target_color}'] + ['#D3D3D3'] * {len(anon_peers)}

plt.figure(figsize=(10, 6))

# --- YOUR PLOTTING CODE HERE ---
# Use seaborn to plot 'Value' against 'Company' using the 'df' DataFrame.
# Example: ax = sns.barplot(x='Company', y='Value', data=df, hue='Company', palette=colors, legend=False)
# Add title and labels.


# --- END OF YOUR PLOTTING CODE ---

plt.tight_layout()
plt.savefig('data/reports/charts/chart_{company_name.replace(' ', '_')}_{m_name.replace(' ', '_').replace('/', '_')}.png')
```
"""
                
                max_retries = 3
                success = False
                current_prompt = chart_prompt
                
                for attempt in range(max_retries):
                    code_response = query_local_llm(current_prompt, model="qwen2.5-coder:7b", format_json=False)
                    code_response = re.sub(r'<think>.*?</think>', '', code_response, flags=re.DOTALL).strip()
                    python_code = extract_python_code(code_response)
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                        f.write(python_code)
                        temp_script_path = f.name
                    
                    try:
                        subprocess.run(["python3", temp_script_path], check=True, capture_output=True, text=True)
                        print(f" -> Successfully generated chart for {m_name}")
                        success = True
                        break
                    except subprocess.CalledProcessError as e:
                        print(f" -> Attempt {attempt+1} failed. Error:\\n{e.stderr}")
                        current_prompt += f"\\n\\nYour previous code failed with this error:\\n{e.stderr}\\nPlease fix the python code and output the corrected version."
                    finally:
                        os.unlink(temp_script_path)
                
                if not success:
                    print(f" -> Failed to generate chart for {m_name} after 3 attempts.")

def generate_report(peer_analysis_path, company_name, model="deepseek-r1:8b"):
    print(f"Loading peer benchmarking data from {peer_analysis_path}...")
    with open(peer_analysis_path, 'r') as f:
        peer_data = json.load(f)
        
    analysis = peer_data.get("Analysis", [])
    
    # Format the peer analysis into a readable string for the LLM
    drivers_str = ""
    for item in analysis:
        drivers_str += f"- {item['Metric']}\\n"
        drivers_str += f"  Target Company Value: {item['Target_Company_Value']}\\n"
        drivers_str += f"  Industry Average: {item['Industry_Average']}\\n"
        drivers_str += f"  Peer Values: {item.get('Peer_Values', {})}\\n"
        drivers_str += f"  Status: {item['Status']}\\n\\n"
        
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
You are a senior ESG financial analyst at NSRAL writing a Peer Benchmarking Report specifically for {company_name}.
WARNING: DO NOT confuse {company_name} with other companies (e.g. do not write about TCS or Tata Consultancy Services unless that is the company name).
You must use a strict institutional tone. 

STRICT TICKER CONSTRAINT: 
The verified official abbreviation/ticker for this company is: {nse_symbol}
You MUST use '{nse_symbol}' exclusively when referring to the company by abbreviation. DO NOT invent or hallucinate any other acronyms.

CRITICAL INSTRUCTION: You MUST NOT mention or reference mathematical 'weights' or the 'Linear_Weight' in your analysis text. Focus strictly on the performance values, the status, and the comparison to the industry average and peers.

You must output the final report as a valid JSON object with EXACTLY the following structure (no markdown formatting outside the JSON, do not include any other keys):

{{
  "company_overview": "1 paragraph overview about the company's business.",
  "environmental": [
    {{
      "metric_name": "Name of the metric",
      "company_value": "The target company value",
      "industry_average": "The industry average",
      "peer_values": {{"Peer A": 10.5, "Peer B": 12.1}},
      "analysis": "Detailed breakdown of performance vs industry for this specific metric, including any known disclosures or events. Explain how good or bad the performance is.",
      "requires_chart": true,
      "suggested_chart_type": "bar"
    }}
  ],
  "social": [
    {{
      "metric_name": "Name of the metric",
      "company_value": "The target company value",
      "industry_average": "The industry average",
      "peer_values": {{"Peer A": 10.5, "Peer B": 12.1}},
      "analysis": "Detailed breakdown of performance vs industry for this specific metric, including any known disclosures or events. Explain how good or bad the performance is.",
      "requires_chart": true,
      "suggested_chart_type": "bar"
    }}
  ],
  "governance": [
    {{
      "metric_name": "Name of the metric",
      "company_value": "The target company value",
      "industry_average": "The industry average",
      "peer_values": {{"Peer A": 10.5, "Peer B": 12.1}},
      "analysis": "Detailed breakdown of performance vs industry for this specific metric, including any known disclosures or events. Explain how good or bad the performance is.",
      "requires_chart": true,
      "suggested_chart_type": "bar"
    }}
  ]
}}

CRITICAL INSTRUCTION: You MUST iterate through EVERY SINGLE metric provided in the 'TOP DRIVERS VS PEERS' section below. Provide a detailed metric object in the corresponding array (environmental, social, or governance) for EACH metric.
Decide if 'requires_chart' should be true if visual comparison is meaningful (e.g. numerical data). You MUST include the 'peer_values' dictionary directly copied from the input data.

TOP DRIVERS VS PEERS:
{drivers_str}
"""
    
    response_text = query_local_llm(prompt, model=model).strip()
    
    os.makedirs("data/reports", exist_ok=True)
    report_path = f"data/reports/json_data/{company_name}_Peer_Narrative.json"
    
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
        
        # Trigger chart generation
        generate_charts(parsed_json, company_name)
        
    except json.JSONDecodeError:
        print("Failed to parse LLM response as JSON. Saving raw output for debugging.")
        with open(report_path.replace(".json", "_failed.txt"), "w") as f:
            f.write(response_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Peer Benchmarking Narrative")
    parser.add_argument("--peer_analysis_path", type=str, required=True, help="Path to the peer analysis JSON file")
    parser.add_argument("--company", type=str, required=True, help="Exact company name")
    parser.add_argument("--model", type=str, default="deepseek-r1:8b", help="Local Ollama model name")
    
    args = parser.parse_args()
    generate_report(args.peer_analysis_path, args.company, model=args.model)
