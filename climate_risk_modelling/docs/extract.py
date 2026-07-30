import pypdf

reader = pypdf.PdfReader("/Users/ashishmishra/Downloads/climate_risk_model_report.pdf")
with open("extracted_pdf.txt", "w") as f:
    for page in reader.pages:
        f.write(page.extract_text() + "\n--- PAGE BREAK ---\n")
