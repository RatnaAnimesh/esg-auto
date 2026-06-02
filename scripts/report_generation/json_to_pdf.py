import json
import argparse
import os
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'NSRAL Peer Benchmarking Report', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        # Ensure text is encoded properly for fpdf
        body = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, body)
        self.ln(10)

def generate_pdf(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pdf = PDFReport()
    pdf.add_page()
    
    company_name = os.path.basename(json_path).split('_Peer_Narrative')[0]
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Company: {company_name}", 0, 1, 'C')
    pdf.ln(5)

    if "company_overview" in data:
        pdf.chapter_title("Company Overview")
        pdf.chapter_body(data["company_overview"])

    for pillar in ["environmental", "social", "governance"]:
        if pillar in data and isinstance(data[pillar], list):
            pdf.chapter_title(pillar.upper())
            for metric in data[pillar]:
                m_name = metric.get("metric_name", "Unknown Metric")
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, m_name, 0, 1, 'L')
                
                # Analysis text
                analysis = metric.get("analysis", "")
                pdf.chapter_body(analysis)
                
                # Inject Chart if it was generated
                safe_company_name = company_name.replace(' ', '_')
                safe_m_name = m_name.replace(' ', '_').replace('/', '_')
                chart_path = f"data/reports/charts/chart_{safe_company_name}_{safe_m_name}.png"
                if os.path.exists(chart_path):
                    # add image and small line break
                    pdf.image(chart_path, x=10, w=150)
                    pdf.ln(5)
                else:
                    pdf.ln(2)

    pdf.output(output_path)
    print(f"Successfully generated PDF: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=True)
    args = parser.parse_args()
    
    out_path = args.json_path.replace('.json', '.pdf')
    generate_pdf(args.json_path, out_path)
