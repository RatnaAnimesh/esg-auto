import pandas as pd
from pathlib import Path

# Paths
brain_dir = Path("/Users/ashishmishra/.gemini/antigravity-ide/brain/899cfced-57c1-4e95-bb98-24c635654f1b")
artifact_path = brain_dir / "full_mapping_review.md"

df = pd.read_csv('config/verified_mapping.csv')
df = df.sort_values(by='optimal_score', ascending=False)

# Let's select the most important columns to show the NLP results
cols_to_show = [
    'question_id', 
    'question_text', 
    'global_optimal_match', 
    'optimal_score', 
    'ncd_score',
    'p_value',
    'confidence_flag',
    'verification_status'
]

md_table = df[cols_to_show].to_markdown(index=False)

content = f"""# Full 316 Question NLP Mapping Output

Here is the complete output from the Tri-Verification Pipeline (BM25 + NCD + Permutation Testing). 
This includes the mathematical **Similarity Scores**, the **Kolmogorov Approximations (NCD)**, and the **Statistical Significance (p-values)** for all 316 questions.

{md_table}
"""

with open(artifact_path, "w") as f:
    f.write(content)
