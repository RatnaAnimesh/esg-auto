import os
import fitz  # PyMuPDF
import json

def parse_pdf(file_path):
    print(f"Parsing {file_path}...")
    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\\n\\n"
        
        # Super simple chunking: split by double newlines and filter out very short chunks
        chunks = [c.strip() for c in full_text.split("\\n\\n") if len(c.strip()) > 50]
        print(f"Extracted {len(chunks)} chunks from {os.path.basename(file_path)}.")
        return chunks
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def main():
    pdf_dir = "data/raw/pdfs"
    output_dir = "data/processed/annual_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_dir):
        print(f"PDF directory {pdf_dir} does not exist. Run the scraper first.")
        return
        
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            symbol = filename.replace(".pdf", "")
            chunks = parse_pdf(file_path)
            
            output_file = os.path.join(output_dir, f"{symbol}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"symbol": symbol, "chunks": chunks}, f, indent=4)
                
    print("PDF parsing complete.")

if __name__ == "__main__":
    main()
