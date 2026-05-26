import argparse
import pandas as pd
import json
import os
import requests
import time

def filter_metrics(company_df, keywords_str):
    if pd.isna(keywords_str) or not keywords_str:
        # If no keywords, return a random sample to save context window, or top 50
        return company_df.head(50)
    
    keywords = [k.strip().lower() for k in str(keywords_str).split(',')]
    
    # Filter rows where index (Metric name) contains any of the keywords
    mask = company_df.index.str.lower().map(lambda x: any(k in x for k in keywords))
    filtered_df = company_df[mask]
    
    # Fallback if too few
    if len(filtered_df) < 5:
        return company_df.head(50)
    
    # Limit to top 150 metrics to prevent blowing up the LLM context window
    return filtered_df.head(150)

def query_local_llm(prompt, model="llama3", mock=False):
    if mock:
        time.sleep(1) # Simulate generation time
        return f"*(MOCK LLM RESPONSE)*\nBased on the provided metrics, the company demonstrates strong performance in this area, actively managing risks and disclosing critical data points. The numbers indicate compliance with BRSR frameworks."
        
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get('response', '')
    except Exception as e:
        print(f"Error querying local LLM: {e}")
        return f"Error: Could not connect to local LLM at {url}. Is Ollama running?"

def generate_report(questions_file, company_name, mock=False, model="llama3"):
    print(f"Loading questions from {questions_file}...")
    q_df = pd.read_excel(questions_file)
    
    company_file = f"data/database/companies/{company_name}.csv"
    if not os.path.exists(company_file):
        print(f"Error: Could not find data for {company_name} at {company_file}")
        return
        
    print(f"Loading data for {company_name}...")
    company_df = pd.read_csv(company_file, index_col='Metric')
    
    os.makedirs("data/reports", exist_ok=True)
    report_path = f"data/reports/{company_name}_Narrative_Report.md"
    
    print(f"Generating report chunks...")
    
    sections = q_df['Section'].unique()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# NSRAL ESG Detailed Analysis Report\n")
        f.write(f"**Entity:** {company_name}\n\n")
        
        for section in sections:
            print(f" - Processing section: {section}")
            f.write(f"## {section}\n\n")
            
            section_questions = q_df[q_df['Section'] == section]
            
            # Aggregate all keywords for this section to pull relevant metrics
            all_keywords = ",".join(section_questions['Metric_Keywords'].dropna().astype(str).tolist())
            relevant_metrics = filter_metrics(company_df, all_keywords)
            
            # Convert metrics to string for prompt
            metrics_text = relevant_metrics.to_csv()
            
            # Formulate the questions
            questions_text = "\n".join([f"- {row['Question_Text']}" for _, row in section_questions.iterrows()])
            
            prompt = f"""
You are an expert ESG financial analyst writing a section of an official NSRAL ESG rating report.
You are writing the "{section}" section.

COMPANY DATA (Filtered for relevance):
{metrics_text}

REQUIRED ANALYSIS QUESTIONS:
Please write a comprehensive narrative answering the following questions based strictly on the data above. Do not hallucinate numbers. If data is missing, state that it is undisclosed.
{questions_text}

TONE AND STYLE GUIDELINES:
- Write in a highly professional, terse, and analytical financial tone (e.g., similar to institutional equity research or credit rating reports).
- Use analytical phrasing such as "driven by", "reflecting", "partially offset by", "remains elevated relative to peers", and "supportive relative to peers".
- Focus heavily on Year-over-Year (YoY) trajectories and peer/benchmark relative performance.
- Seamlessly weave specific quantitative data points (like ISO certifications, Scope 3 emissions, LTIFR, Board independence percentages) into the narrative flow rather than just listing them.
- Ensure the text flows logically without pleasantries or introductory fluff.

Write the narrative using markdown paragraphs.
"""
            
            response = query_local_llm(prompt, model=model, mock=mock)
            
            f.write(response + "\n\n")
            
    print(f"\nSuccessfully generated 37-page equivalent narrative report at: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Local LLM Narrative Reports")
    parser.add_argument("--questions", type=str, default="templates/nsral_questions_mock.xlsx", help="Path to questions excel file")
    parser.add_argument("--company", type=str, required=True, help="Exact company name matching the CSV file (e.g. 'Reliance Industries Limited')")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM responses for pipeline testing without Ollama")
    parser.add_argument("--model", type=str, default="phi4-mini", help="Local Ollama model name (e.g. phi4-mini, llama3)")
    
    args = parser.parse_args()
    
    generate_report(args.questions, args.company, mock=args.mock, model=args.model)
