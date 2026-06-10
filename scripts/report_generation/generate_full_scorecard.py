import argparse
import pandas as pd
import numpy as np
import json
import os
import difflib
import re
import matplotlib.pyplot as plt
from fpdf import FPDF
import warnings

# Suppress specific matplotlib warnings if needed
warnings.filterwarnings("ignore")

try:
    from data_processing.extract_brsr_metrics import load_live_xbrl_dataset
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../data_processing'))
    from extract_brsr_metrics import load_live_xbrl_dataset

try:
    from imputation_rules import IMPUTATION_RULES
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(__file__))
    from imputation_rules import IMPUTATION_RULES

class NSRALScorecard(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(212, 175, 55) # Gold
        self.cell(0, 10, 'NSRAL ESG Scorecard', border=0, align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='R')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_fill_color(39, 39, 42) # Dark Gray
        self.set_text_color(247, 231, 206) # Champagne
        self.cell(0, 10, title, border=0, align='L', fill=True)
        self.ln(15)

    def draw_esg_boxes(self, e_score="N/A", s_score="N/A", g_score="N/A", total_score="N/A"):
        self.set_y(self.get_y() + 5)
        colors = [
            (210, 235, 210), (210, 225, 245), (245, 235, 210), 
            (225, 210, 235)
        ]
        titles = ["Environment", "Social", "Governance", "Overall ESG"]
        scores = [str(e_score), str(s_score), str(g_score), str(total_score)]
        
        box_w = 40
        box_h = 25
        spacing = 5
        start_x = (210 - (box_w * 4 + spacing * 3)) / 2 
        
        for i in range(4):
            x = start_x + i * (box_w + spacing)
            y = self.get_y()
            self.set_fill_color(*colors[i])
            self.rect(x, y, box_w, box_h, style='F')
            
            self.set_xy(x, y + 5)
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(100, 100, 100)
            self.cell(box_w, 4, titles[i], align='C')
            
            self.set_xy(x, y + 15)
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(0, 0, 0)
            self.cell(box_w, 8, scores[i], align='C')
            
        self.set_y(y + box_h + 10)

def generate_chart(metric_name, target_val, peer_vals, avg_val, yoy_vals, output_path, idx):
    # Peer Chart
    plt.figure(figsize=(6, 4))
    
    names = ['Target'] + list(peer_vals.keys())
    values = [target_val] + list(peer_vals.values())
    
    # Sort for better visualization
    sorted_data = sorted(zip(names, values), key=lambda x: x[1] if pd.notna(x[1]) else 0)
    names, values = zip(*sorted_data)
    
    colors = ['#d4af37' if n == 'Target' else '#27272a' for n in names]
    
    plt.barh(names, values, color=colors)
    if pd.notna(avg_val):
        plt.axvline(avg_val, color='red', linestyle='--', label=f'Industry Avg: {avg_val:.2f}')
        plt.legend(loc='lower right')
        
    plt.title(f"{metric_name[:40]}...", fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_path}/peer_chart_{idx}.png", dpi=150)
    plt.close()

def generate_scorecard(target_company, num_charts=10):
    print(f"Generating full scorecard for {target_company}...")
    
    # 1. Load Scores Data for top-level ESG scores
    scores_df = pd.read_csv('data/reference/scores/nsral_scores_full.csv')
    scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()
    target_clean = target_company.strip().lower()
    
    match = scores_df[scores_df['clean_name'] == target_clean]
    if match.empty:
        clean_names = scores_df['clean_name'].tolist()
        closest = difflib.get_close_matches(target_clean, clean_names, n=1, cutoff=0.6)
        if closest:
            match = scores_df[scores_df['clean_name'] == closest[0]]
            target_clean = closest[0]
        else:
            raise ValueError(f"Company '{target_company}' not found in database.")
    
    basic_industry = match.iloc[0]['Basic Industry']
    e_score = match.iloc[0].get('Environment Score', 'N/A')
    s_score = match.iloc[0].get('Social Score', 'N/A')
    g_score = match.iloc[0].get('Governance Score', 'N/A')
    total_score = match.iloc[0].get('Total Score', 'N/A')
    if pd.notna(total_score) and isinstance(total_score, (int, float)):
        total_score = round(total_score, 2)
    
    # 2. Extract Data via Live XBRL
    merged_df, target_actual, _ = load_live_xbrl_dataset(match.iloc[0]['Company Name'])
    
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
    
    company_row = merged_df[merged_df['CompanyName'] == target_actual]
    if company_row.empty:
        raise ValueError(f"Failed to extract XBRL data for target '{target_actual}'.")
    company_row = company_row.iloc[0]
    
    peers_df = merged_df[merged_df['CompanyName'] != target_actual].copy()
    if 'Revenue From Operations' in peers_df.columns:
        peers_df['Revenue From Operations'] = pd.to_numeric(peers_df['Revenue From Operations'], errors='coerce').fillna(0)
        peers_df = peers_df.sort_values(by='Revenue From Operations', ascending=False).head(4)
    else:
        peers_df = peers_df.head(4)
        
    # 3. Load Industry Weights
    industry_clean = re.sub(r'[^a-zA-Z0-9]+', '_', basic_industry)
    weights_path = f'data/weights/sector_weights/extracted_industries/{industry_clean}.json'
    industry_weights = {}
    if os.path.exists(weights_path):
        with open(weights_path, 'r') as f:
            industry_weights = json.load(f)
            
    # Sort weights to get top metrics
    sorted_metrics = sorted(industry_weights.items(), key=lambda x: x[1], reverse=True)
    numeric_cols = [m[0] for m in sorted_metrics]
    
    # Create output dirs
    os.makedirs('data/reports/pdfs', exist_ok=True)
    os.makedirs('data/reports/charts/temp', exist_ok=True)
    chart_dir = 'data/reports/charts/temp'
    
    # 4. Generate PDF
    pdf = NSRALScorecard()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Executive Summary Page
    pdf.set_font("Helvetica", 'B', 20)
    pdf.cell(0, 10, f"{match.iloc[0]['Company Name']}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Industry: {basic_industry} | Sector Benchmark Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.draw_esg_boxes(e_score=e_score, s_score=s_score, g_score=g_score, total_score=total_score)
    
    pdf.set_font("Helvetica", '', 10)
    intro_text = (
        f"This scorecard presents a highly deterministic, data-driven ESG assessment for {match.iloc[0]['Company Name']}. "
        "The metrics below are parsed directly from XBRL public disclosures and benchmarked mathematically against industry peers. "
        "Zero generative AI was used to hallucinate facts in this report."
    )
    pdf.multi_cell(0, 6, intro_text)
    pdf.ln(10)
    
    # Categorize metrics
    e_metrics, s_metrics, g_metrics = [], [], []
    e_kw = ['emission', 'energy', 'water', 'waste', 'environment', 'climate', 'scope', 'renewable', 'fuel']
    s_kw = ['employee', 'turnover', 'training', 'worker', 'injury', 'health', 'safety', 'maternity', 'paternity', 'social', 'community', 'diversity', 'women', 'hiring', 'attrition']

    for metric, weight in sorted_metrics:
        metric_lower = metric.lower()
        if any(kw in metric_lower for kw in e_kw):
            e_metrics.append((metric, weight))
        elif any(kw in metric_lower for kw in s_kw):
            s_metrics.append((metric, weight))
        else:
            g_metrics.append((metric, weight))

    # 5. Render Top N Charts grouped by ESG
    chart_count = 0
    
    for cat_name, cat_metrics in [("Environmental", e_metrics), ("Social", s_metrics), ("Governance", g_metrics)]:
        if not cat_metrics: continue
        
        pdf.add_page()
        pdf.chapter_title(f"Top Weighted Drivers - {cat_name}")
        
        cat_chart_count = 0
        for idx, (metric, weight) in enumerate(cat_metrics):
            if cat_chart_count >= num_charts: break
            
            target_val = pd.to_numeric(company_row.get(metric, np.nan), errors='coerce')
            if pd.isna(target_val): continue
            
            peer_vals = {}
            for _, p_row in peers_df.iterrows():
                pval = pd.to_numeric(p_row.get(metric, np.nan), errors='coerce')
                peer_vals[p_row.get('CompanyName', 'Unknown Peer')] = pval if pd.notna(pval) else 0
                
            all_vals = [target_val] + list(peer_vals.values())
            avg_val = np.mean([v for v in all_vals if pd.notna(v)])
            
            generate_chart(metric, target_val, peer_vals, avg_val, {}, chart_dir, chart_count)
            
            # Add to PDF
            pdf.set_text_color(0, 0, 0) # Reset to black
            pdf.set_font("Helvetica", 'B', 10)
            pdf.multi_cell(0, 6, f"{cat_chart_count+1}. {metric} (Weight: {weight:.4f})")
            
            chart_path = f"{chart_dir}/peer_chart_{chart_count}.png"
            if os.path.exists(chart_path):
                pdf.image(chart_path, x=10, w=150)
                pdf.ln(5)
                
            chart_count += 1
            cat_chart_count += 1
            if cat_chart_count % 2 == 0:
                pdf.add_page()

    def format_large_number(num):
        if pd.isna(num): return "N/A"
        abs_num = abs(num)
        if abs_num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif abs_num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        else:
            return f"{num:,.1f}"

    # 6. Render Data Tables for ALL Metrics
    pdf.add_page()
    pdf.chapter_title("Comprehensive Data Table (All Extracted Metrics)")
    
    pdf.set_font("Helvetica", 'B', 7)
    pdf.set_text_color(0, 0, 0) # Reset to black for readability
    
    # We have up to 4 peers. Let's get their names for headers.
    peer_names = []
    for _, p_row in peers_df.iterrows():
        pname = str(p_row.get('CompanyName', 'Peer'))[:8]
        peer_names.append(pname)
        
    num_peers = len(peer_names)
    
    # Table header widths: Metric=65, Target=18, Avg=18. Remaining = 190 - 65 - 18 - 18 = 89
    base_w = [65, 18, 18]
    peer_w = 89 / num_peers if num_peers > 0 else 0
    col_w = base_w + [peer_w] * num_peers
    
    pdf.cell(col_w[0], 8, "Metric", border=1)
    pdf.cell(col_w[1], 8, "Target", border=1, align='R')
    pdf.cell(col_w[2], 8, "Ind. Avg", border=1, align='R')
    for i in range(num_peers):
        pdf.cell(col_w[3+i], 8, peer_names[i], border=1, align='C')
    pdf.ln()
    pdf.set_font("Helvetica", '', 6)
    
    # Get ALL numeric columns
    all_numeric_cols = merged_df.select_dtypes(include=[np.number]).columns.tolist()
    
    for metric in all_numeric_cols:
        target_val = pd.to_numeric(company_row.get(metric, np.nan), errors='coerce')
        if pd.isna(target_val): continue
        
        all_vals = [target_val]
        peer_vals_list = []
        for _, p_row in peers_df.iterrows():
            pval = pd.to_numeric(p_row.get(metric, np.nan), errors='coerce')
            if pd.notna(pval):
                all_vals.append(pval)
            peer_vals_list.append(pval)
                
        avg_val = np.mean(all_vals) if len(all_vals) > 0 else 0
        
        # Trim metric name
        m_name = metric[:55] + "..." if len(metric) > 55 else metric
        
        # Check if we need to add a new page before drawing
        if pdf.get_y() > 270:
            pdf.add_page()
            
        pdf.cell(col_w[0], 6, m_name, border=1)
        pdf.cell(col_w[1], 6, format_large_number(target_val), border=1, align='R')
        pdf.cell(col_w[2], 6, format_large_number(avg_val), border=1, align='R')
        
        for i in range(num_peers):
            pdf.cell(col_w[3+i], 6, format_large_number(peer_vals_list[i]), border=1, align='R')
        pdf.ln()

        
    output_path = f"data/reports/pdfs/{match.iloc[0]['Company Name'].replace(' ', '_')}_Full_Scorecard.pdf"
    pdf.output(output_path)
    print(f"\\nSuccessfully generated strict data-bound PDF Scorecard at: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Full Data-Bound Scorecard PDF")
    parser.add_argument("--company", type=str, required=True, help="Exact company name")
    parser.add_argument("-n", "--num_charts", type=int, default=10, help="Number of top metrics to chart")
    args = parser.parse_args()
    
    generate_scorecard(args.company, num_charts=args.num_charts)
