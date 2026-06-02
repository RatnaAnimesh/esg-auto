import argparse
import os
import json
from fpdf import FPDF

class NSRALReport(FPDF):
    def header(self):
        pass
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='R')
        
    def draw_esg_boxes(self, e_score="N/A", s_score="N/A", g_score="N/A", total_score="N/A"):
        self.set_y(20)
        colors = [
            (210, 235, 210), (210, 225, 245), (245, 235, 210), 
            (225, 210, 235), (225, 210, 235)
        ]
        titles = ["Environment Score", "Social Score", "Governance Score", "FY2025\\nESG Rating", "FY2024\\nESG Rating"]
        scores = [str(e_score), str(s_score), str(g_score), str(total_score), str(total_score)]
        
        box_w = 32
        box_h = 25
        spacing = 5
        start_x = (210 - (box_w * 5 + spacing * 4)) / 2 
        
        for i in range(5):
            x = start_x + i * (box_w + spacing)
            y = 20
            self.set_fill_color(*colors[i])
            self.rect(x, y, box_w, box_h, style='F')
            
            self.set_xy(x, y + 5)
            self.set_font('Helvetica', 'B', 7)
            self.set_text_color(100, 100, 100)
            if "\\n" in titles[i]:
                t1, t2 = titles[i].split("\\n")
                self.cell(box_w, 4, t1, align='C')
                self.set_xy(x, y + 9)
                self.cell(box_w, 4, t2, align='C')
            else:
                self.cell(box_w, 4, titles[i], align='C')
            
            self.set_xy(x, y + 15)
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(0, 0, 0)
            self.cell(box_w, 8, scores[i], align='C')
            
        self.set_y(50)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, "Rating Category : Leader", align='R')
        self.ln(15)

def sanitize_text(text):
    if not isinstance(text, str):
        return str(text)
    replacements = {
        '—': '-', '–': '-',
        '“': '"', '”': '"',
        '‘': "'", '’': "'",
        '…': '...',
        '\u2022': '-', # bullet
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Strip any remaining non-latin1 characters
    return text.encode('latin-1', errors='ignore').decode('latin-1')

def create_pdf(blocks_path, peer_analysis_path, company_name):
    print(f"Reading narrative blocks from {blocks_path}...")
    try:
        with open(blocks_path, 'r', encoding='utf-8') as f:
            blocks = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON blocks: {e}")
        return
        
    e_s, s_s, g_s, tot_s = "N/A", "N/A", "N/A", "N/A"
    if peer_analysis_path:
        try:
            with open(peer_analysis_path, 'r', encoding='utf-8') as f:
                peer_data = json.load(f)
                e_s = peer_data.get("Predicted_E_Score", "N/A")
                s_s = peer_data.get("Predicted_S_Score", "N/A")
                g_s = peer_data.get("Predicted_G_Score", "N/A")
                tot_s = peer_data.get("Predicted_ESG_Score", "N/A")
        except Exception as e:
            print(f"Failed to load peer analysis scores: {e}")
        
    pdf = NSRALReport()
    pdf.add_page()
    
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Executive Summary", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", '', 11)
    
    bp1 = "Environment, Social, and Governance (ESG) factors are increasingly shaping investor decisions, with companies expected to demonstrate not only financial performance but also responsible business conduct. ESG ratings serve as a lens into a company's strategic priorities, operational integrity, and long-term value creation. For this entity, these ratings reflect its evolving commitment to sustainability across climate action, workforce development, and governance oversight."
    pdf.multi_cell(0, 6, bp1)
    pdf.ln(4)
    
    # Block 1 (Company Overview)
    pdf.multi_cell(0, 6, sanitize_text(blocks.get("company_overview", "Company Overview Missing")))
    pdf.ln(4)
    
    bp2 = "As part of the ESG assessment, NSE Sustainability Ratings and Analytics Limited (NSRAL) evaluated the performance across key ESG dimensions including climate change, human rights, diversity, anti-corruption, stakeholder engagement amongst others. The methodology is rooted in materiality, transparency, and sector-specific relevance, combining both quantitative and qualitative indicators sourced from public disclosures and credible third-party reports."
    pdf.multi_cell(0, 6, sanitize_text(bp2))
    pdf.ln(4)
    
    pdf.multi_cell(0, 6, sanitize_text(blocks.get("overall_summary", "Overall Summary Missing")))
    pdf.ln(4)
    
    pdf.add_page()
    pdf.draw_esg_boxes(e_score=e_s, s_score=s_s, g_score=g_s, total_score=tot_s)
    pdf.set_font("Helvetica", '', 11)
    
    pdf.multi_cell(0, 6, sanitize_text(blocks.get("environment", "Environment Missing")))
    pdf.ln(4)
    
    pdf.multi_cell(0, 6, sanitize_text(blocks.get("social", "Social Missing")))
    pdf.ln(4)
    
    pdf.multi_cell(0, 6, sanitize_text(blocks.get("governance", "Governance Missing")))
    pdf.ln(4)
    
    conclusion = f"Overall, {company_name}'s performance reflects its structured and policy-driven approach to sustainability, with opportunities for focused improvements to further elevate its performance."
    pdf.multi_cell(0, 6, conclusion)
    
    output_path = f"data/reports/pdfs/{company_name}_Executive_Summary.pdf"
    pdf.output(output_path)
    print(f"\\nSuccessfully generated PDF at: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PDF Report")
    parser.add_argument("--blocks", type=str, default="data/reports/json_data/Tata Motors Limited_Narrative_Blocks.json", help="Path to LLM output blocks (JSON)")
    parser.add_argument("--peer_analysis_path", type=str, default=None, help="Path to peer analysis JSON for dynamic scores")
    parser.add_argument("--company", type=str, required=True, help="Exact company name")
    
    args = parser.parse_args()
    create_pdf(args.blocks, args.peer_analysis_path, args.company)
