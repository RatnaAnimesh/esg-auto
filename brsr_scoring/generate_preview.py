import pandas as pd

df = pd.read_csv('config/mapping_review.csv')
md = "# BRSR Mapping Preview\n\n"
md += "| Question | Mapped Column | Confidence Score | Confidence Flag |\n"
md += "|---|---|---|---|\n"

for _, row in df.iterrows():
    q = str(row['question_text']).replace('|', '')
    col = str(row['global_optimal_match']).replace('|', '')
    score = f"{row['optimal_score']:.2f}"
    flag = str(row['confidence_flag'])
    md += f"| {q} | {col} | {score} | {flag} |\n"

with open('/Users/ashishmishra/.gemini/antigravity-ide/brain/899cfced-57c1-4e95-bb98-24c635654f1b/mapping_preview.md', 'w') as f:
    f.write(md)

print("Generated mapping_preview.md")
