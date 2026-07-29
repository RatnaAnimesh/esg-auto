import fitz  # PyMuPDF
import re
import pandas as pd
from pathlib import Path
from rank_bm25 import BM25Okapi

class PDFFallbackExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        self.raw_text = ""
        self.paragraphs = []
        self.tokenized_paragraphs = []
        self.bm25 = None
        self._load_and_chunk_pdf()

    def _load_and_chunk_pdf(self):
        """Extracts text via PyMuPDF and chunks it into paragraphs for BM25 ranking."""
        try:
            doc = fitz.open(self.pdf_path)
            for page in doc:
                # Extract blocks of text (preserves some physical layout grouping)
                blocks = page.get_text("blocks")
                for block in blocks:
                    # block is a tuple: (x0, y0, x1, y1, text, block_type, block_no)
                    text = block[4].strip()
                    if len(text) > 20: # Ignore tiny artifacts
                        # Normalize whitespace
                        text = re.sub(r'\s+', ' ', text)
                        self.paragraphs.append(text)
            
            # Initialize BM25 corpus
            self.tokenized_paragraphs = [self._tokenize(p) for p in self.paragraphs]
            if self.tokenized_paragraphs:
                self.bm25 = BM25Okapi(self.tokenized_paragraphs)
                
        except Exception as e:
            print(f"Error loading PDF {self.pdf_path}: {e}")

    def _tokenize(self, text):
        # simple lowercase alphanumeric tokenization
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).split()

    def search_question(self, question, top_k=3):
        """Searches the PDF for paragraphs most relevant to the question."""
        if not self.bm25:
            return []
            
        tokenized_q = self._tokenize(question)
        # get top k paragraphs
        top_paragraphs = self.bm25.get_top_n(tokenized_q, self.paragraphs, n=top_k)
        return top_paragraphs

if __name__ == "__main__":
    # Test it on the same PDF
    test_pdf = "/Users/ashishmishra/animeshratna/nsral/india-eu_report/BharatABM/data/Corporate_MSME/brsr-reports/brsr reports 2025-26/files/PARAS_31072025001634_BRSR.pdf"
    extractor = PDFFallbackExtractor(test_pdf)
    
    print(f"Loaded {len(extractor.paragraphs)} paragraphs from {Path(test_pdf).name}.\n")
    
    # Load all 316 canonical questions
    schema_path = Path("/Users/ashishmishra/animeshratna/nsral/brsr_scoring/config/kalman_fused_mapping.csv")
    df_questions = pd.read_csv(schema_path)
    
    if 'brsr_question' in df_questions.columns:
        questions = df_questions['brsr_question'].dropna().unique()
    elif 'question' in df_questions.columns:
        questions = df_questions['question'].dropna().unique()
    else:
        questions = df_questions.iloc[:, 0].dropna().unique()
        
    print(f"Loaded {len(questions)} canonical questions.")
    
    results = []
    for q in questions:
        matches = extractor.search_question(q, top_k=1)
        top_match = matches[0] if matches else ""
        results.append({"question": q, "matched_pdf_paragraph": top_match})
        
    df_results = pd.DataFrame(results)
    out_file = Path("/Users/ashishmishra/animeshratna/nsral/brsr_scoring/config/pdf_extracted_headers.csv")
    df_results.to_csv(out_file, index=False)
    
    print(f"\nSaved results to {out_file}")
    
    print("\n--- Sample Results ---")
    print(df_results.head(10).to_markdown(index=False))
