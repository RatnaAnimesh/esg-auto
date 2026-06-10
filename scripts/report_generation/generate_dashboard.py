import argparse
import pandas as pd
import numpy as np
import json
import os
import re
import difflib
import webbrowser

try:
    from imputation_rules import IMPUTATION_RULES
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(__file__))
    from imputation_rules import IMPUTATION_RULES

try:
    from data_processing.extract_brsr_metrics import parse_live_xbrl_to_dict
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../data_processing'))
    from extract_brsr_metrics import parse_live_xbrl_to_dict

def generate_dashboard_html(target_company, basic_industry=None):
    
    print(f"Loading datasets for {target_company}...")
    scores_df = pd.read_csv('data/reference/mappings/company_to_basic_industry.csv')
    scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()
    
    target_clean = target_company.strip().lower()
    match = scores_df[scores_df['clean_name'] == target_clean]
    
    if not match.empty:
        target_company_actual = match.iloc[0]['Company Name']
        if not basic_industry: basic_industry = match.iloc[0]['Basic Industry']
    else:
        clean_names = scores_df['clean_name'].tolist()
        closest = difflib.get_close_matches(target_clean, clean_names, n=1, cutoff=0.6)
        if closest:
            match = scores_df[scores_df['clean_name'] == closest[0]]
            target_clean = closest[0]
            target_company_actual = match.iloc[0]['Company Name']
            if not basic_industry: basic_industry = match.iloc[0]['Basic Industry']
        else:
            raise ValueError(f"Company '{target_company}' not found in database.")
            
    print(f"Target Company using Basic Industry: {basic_industry}")
    
    peer_names = scores_df[scores_df['Basic Industry'] == basic_industry]['Company Name'].tolist()
    if target_company_actual not in peer_names:
        peer_names.append(target_company_actual)
    
    print(f"Reading consolidated data for {len(peer_names)} companies...")
    brsr_df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv')
    
    peers_brsr = brsr_df[brsr_df['Name Of The Company'].isin(peer_names)].copy()
    if peers_brsr.empty:
        raise ValueError(f"Could not find any consolidated data for industry {basic_industry}")
        
    peers_brsr['CompanyName'] = peers_brsr['Name Of The Company']
    peers_brsr['clean_name'] = peers_brsr['CompanyName'].astype(str).str.strip().str.lower()
    peers_brsr['Basic Industry'] = basic_industry
    
    merged_df = peers_brsr.copy()
    
    # Convert string columns extracted from XML into proper numeric types
    for col in merged_df.columns:
        if col not in ['CompanyName', 'clean_name', 'Basic Industry']:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
    
    company_row = merged_df[merged_df['clean_name'] == target_clean]
    if company_row.empty:
        raise ValueError(f"Raw XBRL for Company '{target_company_actual}' not found.")
        
    target_company = target_company_actual
    
    # --- Dynamic Imputation Engine (from Calculation Linkbase) ---
    try:
        from dynamic_imputer import apply_dynamic_imputation
        merged_df = apply_dynamic_imputation(merged_df)
    except Exception as e:
        print(f"Warning: Dynamic imputation failed: {e}")
    
    # --- Fallback/Custom Static Imputation Rules ---
    for derived_metric, formula in IMPUTATION_RULES.items():
        eval_formula = re.sub(r'\{(.*?)\}', r'`\1`', formula)
        prev_formula = re.sub(r'\{(.*?)\}', r'`\1 - Previous Year`', formula)
        
        try:
            computed_vals = merged_df.eval(eval_formula)
            if derived_metric not in merged_df.columns:
                merged_df[derived_metric] = computed_vals
            else:
                merged_df[derived_metric] = np.where(
                    merged_df[derived_metric].isna() | (merged_df[derived_metric] == 0),
                    computed_vals,
                    merged_df[derived_metric]
                )
        except Exception:
            pass
            
        try:
            computed_prev = merged_df.eval(prev_formula)
            prev_metric = f"{derived_metric} - Previous Year"
            if prev_metric not in merged_df.columns:
                merged_df[prev_metric] = computed_prev
            else:
                merged_df[prev_metric] = np.where(
                    merged_df[prev_metric].isna() | (merged_df[prev_metric] == 0),
                    computed_prev,
                    merged_df[prev_metric]
                )
        except Exception:
            pass
    # ---------------------------------
    
    # Filter dataset for peers
    peers_df = merged_df[merged_df['Basic Industry'] == basic_industry].copy()
    
    # Select the top 4 closest peers in market size (using Revenue as proxy)
    target_revenue = pd.to_numeric(company_row.iloc[0].get('Revenue From Operations', 0), errors='coerce')
    if pd.isna(target_revenue):
        target_revenue = 0
        
    peers_df['rev_diff'] = abs(pd.to_numeric(peers_df['Revenue From Operations'], errors='coerce').fillna(0) - target_revenue)
    
    target_df = peers_df[peers_df['clean_name'] == target_company.lower().strip()]
    others_df = peers_df[peers_df['clean_name'] != target_company.lower().strip()]
    closest_peers = others_df.sort_values('rev_diff').head(4)
    
    peers_df = pd.concat([target_df, closest_peers])
    print(f"Filtered down to {len(closest_peers)} closest market peers in {basic_industry}.")
    
    # Get all numeric columns that are not 'Previous Year'
    numeric_cols = peers_df.select_dtypes(include='number').columns
    base_metrics = [c for c in numeric_cols if not str(c).endswith('Previous Year') and c not in ['id', 'Unnamed: 0']]
    
    top_metrics = base_metrics
    
    dashboard_metrics = []
    
    for metric in top_metrics:
        if metric not in peers_df.columns:
            continue
            
        target_raw = company_row.iloc[0].get(metric)
        target_val = pd.to_numeric(target_raw, errors='coerce')
        if pd.isna(target_val):
            continue
            
        target_val = float(target_val)
            
        peer_mean = peers_df[metric].mean()
        
        peer_values = []
        for idx, row in peers_df.iterrows():
            peer_val = pd.to_numeric(row[metric], errors='coerce')
            if not pd.isna(peer_val) and row['clean_name'] != target_company.lower().strip():
                peer_name = row.get('CompanyName', row['clean_name'])
                if pd.isna(peer_name):
                    peer_name = row['clean_name']
                if isinstance(peer_name, str):
                    peer_name = peer_name.title()
                peer_values.append({"name": peer_name, "value": float(round(float(peer_val), 4))})
                
        # Check for YoY
        prev_year_col = f"{metric} - Previous Year"
        prev_val = None
        if prev_year_col in company_row.columns:
            p_val = pd.to_numeric(company_row.iloc[0][prev_year_col], errors='coerce')
            if not pd.isna(p_val):
                prev_val = float(round(float(p_val), 4))
                
        # Classify metric
        metric_lower = metric.lower()
        e_kw = ['emission', 'energy', 'water', 'waste', 'environment', 'climate', 'scope', 'renewable', 'fuel']
        s_kw = ['employee', 'turnover', 'training', 'worker', 'injury', 'health', 'safety', 'maternity', 'paternity', 'social', 'community', 'diversity', 'women', 'hiring', 'attrition']
        
        category = "Governance"
        if any(kw in metric_lower for kw in e_kw):
            category = "Environmental"
        elif any(kw in metric_lower for kw in s_kw):
            category = "Social"
            
        # Guess Unit
        unit = "Units"
        if 'percentage' in metric_lower or 'rate' in metric_lower or 'margin' in metric_lower:
            unit = "%"
        elif 'value' in metric_lower or 'turnover' in metric_lower or 'expenditure' in metric_lower or 'remuneration' in metric_lower or 'salary' in metric_lower or 'cost' in metric_lower or 'revenue' in metric_lower:
            unit = "INR"
        elif 'number' in metric_lower or 'count' in metric_lower:
            unit = "Count"
        elif 'waste' in metric_lower or 'emission' in metric_lower or 'scope 1' in metric_lower or 'scope 2' in metric_lower or 'scope 3' in metric_lower:
            unit = "Metric Tonnes (MT)"
        elif 'water' in metric_lower:
            unit = "Kilolitres (KL)"
        elif 'energy' in metric_lower or 'fuel' in metric_lower or 'electricity' in metric_lower:
            unit = "Gigajoules (GJ)"
        elif 'intensity' in metric_lower:
            unit = "Intensity Ratio"
            
        dashboard_metrics.append({
            "name": metric,
            "category": category,
            "unit": unit,
            "yoy": {
                "current": float(target_val) if not pd.isna(target_val) else None,
                "previous": float(prev_val) if not pd.isna(prev_val) else None
            },
            "peer_analytics": {
                "target": float(target_val) if not pd.isna(target_val) else None,
                "industry_average": float(peer_mean) if not pd.isna(peer_mean) else None,
                "peers": peer_values
            }
        })
        
    dashboard_data = {
        "company": target_company,
        "industry": basic_industry,
        "metrics": dashboard_metrics
    }
    
    # Generate Output
    os.makedirs('data/reports/dashboards', exist_ok=True)
    safe_company_name = re.sub(r'[^a-zA-Z0-9]+', '_', target_company)
    
    template_path = 'scripts/report_generation/dashboard_template.html'
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    html_content = html_content.replace('{{ company }}', target_company)
    html_content = html_content.replace('{{ industry }}', basic_industry)
    html_content = html_content.replace('{{ dashboard_data | safe }}', json.dumps(dashboard_data))
    
    return html_content

def main():
    parser = argparse.ArgumentParser(description="Generate Visual Dashboard for a given company")
    parser.add_argument("--company", type=str, required=True, help="Exact Company Name")
    parser.add_argument("--industry", type=str, default=None, help="Force Basic Industry")
    args = parser.parse_args()
    
    try:
        html_content = generate_dashboard_html(args.company, args.industry)
    except Exception as e:
        print(f"Error: {e}")
        return
        
    safe_company_name = re.sub(r'[^a-zA-Z0-9]+', '_', args.company)
    out_path = os.path.abspath(f"data/reports/dashboards/{safe_company_name}_Dashboard.html")
    
    os.makedirs('data/reports/dashboards', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"\nDashboard successfully generated at:\n{out_path}")
    print("Opening in web browser...")
    webbrowser.open('file://' + out_path)

if __name__ == "__main__":
    main()
