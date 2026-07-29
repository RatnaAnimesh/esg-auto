import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    df = pd.read_csv(BASE_DIR / 'config/master_schema.csv')
    md = "# Master Schema Preview\n\n"
    md += "| Question | Mapped Target | Source | BM25 Score | Status |\n"
    md += "|---|---|---|---|---|\n"

    for _, row in df.iterrows():
        q = str(row['question_text']).replace('|', '')
        target = str(row['extraction_target']).replace('|', '')
        source = str(row['primary_source'])
        score = f"{row['final_bm25_score']:.2f}"
        status = str(row['verification_status'])
        
        # Add visual indicators for the source without emojis
        if source == "BRSR":
            source_flag = "BRSR"
        elif source == "Annual_Report":
            source_flag = "Annual Report"
        else:
            source_flag = "Review"
            
        md += f"| {q} | {target} | {source_flag} | {score} | {status} |\n"

    out_file = "/Users/ashishmishra/.gemini/antigravity-ide/brain/899cfced-57c1-4e95-bb98-24c635654f1b/mapping_preview.md"
    with open(out_file, 'w') as f:
        f.write(md)

    print(f"Generated preview at {out_file}")

if __name__ == "__main__":
    main()
