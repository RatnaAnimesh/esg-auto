import xml.etree.ElementTree as ET
from pathlib import Path
import re
import glob

BASE_DIR = Path(__file__).resolve().parent.parent
XBRL_DIR = BASE_DIR / "data" / "xbrl_annual_reports"

def camel_case_split(identifier):
    # Splits camelCase and handles numbers (e.g., RevenueFromOperations -> Revenue From Operations)
    identifier = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', identifier)
    identifier = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', identifier)
    identifier = re.sub(r'([a-z])(\d)', r'\1 \2', identifier)
    return identifier

def extract_tags():
    print(f"Scanning for XBRL files in {XBRL_DIR}...")
    xml_files = glob.glob(str(XBRL_DIR / "*.xml"))
    
    if not xml_files:
        print("No XML files found. Please ensure Annual Reports are downloaded.")
        return
        
    unique_tags = set()
    
    for file_path in xml_files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Iterate through all elements in the XML tree
            for elem in root.iter():
                # Extract the tag name without the namespace {...}
                tag = elem.tag.split('}')[-1]
                
                # Ignore generic XBRL linking tags
                if tag not in ['xbrli', 'context', 'unit', 'entity', 'identifier', 'period', 
                               'startDate', 'endDate', 'measure', 'divide', 'numerator', 'denominator']:
                    
                    # Split CamelCase for semantic matching
                    readable_tag = camel_case_split(tag)
                    unique_tags.add(readable_tag)
                    
        except ET.ParseError as e:
            print(f"XML Parse Error in {file_path}: {e}")
            continue
            
    # Save the global vocabulary
    out_file = BASE_DIR / "data" / "xbrl_tags_list.txt"
    with open(out_file, 'w') as f:
        for tag in sorted(unique_tags):
            f.write(f"{tag}\n")
            
    print(f"Extracted {len(unique_tags)} unique XBRL tags to {out_file}")

if __name__ == "__main__":
    extract_tags()
