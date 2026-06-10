import xml.etree.ElementTree as ET
import json
import sys
import os
import re

def camel_to_space(text):
    return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)

def parse_live_xbrl_to_dict(xml_path, company_name):
    metrics = parse_xbrl_to_json(xml_path)
    if not metrics: return None
    
    company_data = {'CompanyName': company_name, 'clean_name': company_name.lower().strip()}
    for item in metrics:
        metric_name = camel_to_space(item['metric'])
        val = item['value']
        ctx = item.get('context_details', {})
        dims = ctx.get('dimensions', {})
        col_parts = [metric_name]
        for dim_key, dim_val in dims.items():
            col_parts.append(camel_to_space(str(dim_val)))
            
        if 'context_id' in item and not ('CYMain' in item['context_id'] or 'CYMain' in item['context_id']):
            if 'PY' in item['context_id'] and not 'PPY' in item['context_id']:
                col_parts.append('Previous Year')
            elif 'PPY' in item['context_id']:
                col_parts.append('Prior Previous Year')
                
        col_name = " - ".join(col_parts)
        company_data[col_name] = val
        
    return company_data

def load_live_xbrl_dataset(target_company, basic_industry=None):
    import pandas as pd
    import difflib
    
    scores_df = pd.read_csv('data/reference/scores/nsral_scores_full.csv')
    scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()
    
    target_clean = target_company.strip().lower()
    match = scores_df[scores_df['clean_name'] == target_clean]
    
    if not match.empty:
        target_company_actual = match.iloc[0]['Company Name']
        if not basic_industry: basic_industry = match.iloc[0]['Basic Industry']
    else:
        clean_names = scores_df['clean_name'].tolist()
        closest = difflib.get_close_matches(target_clean, clean_names, n=1, cutoff=0.6)
        if closest:
            match = scores_df[scores_df['clean_name'] == closest[0]]
            target_clean = closest[0]
            target_company_actual = match.iloc[0]['Company Name']
            if not basic_industry: basic_industry = match.iloc[0]['Basic Industry']
        else:
            raise ValueError(f"Company '{target_company}' not found in database.")
            
    peer_names = scores_df[scores_df['Basic Industry'] == basic_industry]['Company Name'].tolist()
    if target_company_actual not in peer_names:
        peer_names.append(target_company_actual)
    
    xbrl_dir = 'data/raw/xbrl'
    all_data = []
    
    for peer in peer_names:
        xml_path = os.path.join(xbrl_dir, f"{peer}.xml")
        if os.path.exists(xml_path):
            comp_dict = parse_live_xbrl_to_dict(xml_path, peer)
            if comp_dict:
                comp_dict['Basic Industry'] = basic_industry
                all_data.append(comp_dict)
                
    if not all_data:
        raise ValueError(f"Could not find any XBRL data for industry {basic_industry}")
        
    merged_df = pd.DataFrame(all_data)
    
    for col in merged_df.columns:
        if col not in ['CompanyName', 'clean_name', 'Basic Industry']:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            
    company_row = merged_df[merged_df['clean_name'] == target_clean]
    if company_row.empty:
        raise ValueError(f"Raw XBRL for Company '{target_company_actual}' not found.")
        
    return merged_df, target_company_actual, basic_industry

def parse_xbrl_to_json(file_path):
    print(f"Processing {file_path}...")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Failed to parse XML: {e}")
        return False

    # Namespaces commonly used in XBRL
    ns = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrldi': 'http://xbrl.org/2006/xbrldi'
    }

    contexts = {}
    
    # 1. Parse Contexts
    for context in root.findall('xbrli:context', ns):
        ctx_id = context.attrib['id']
        ctx_data = {}
        
        # Parse Period
        period = context.find('xbrli:period', ns)
        if period is not None:
            start_date = period.find('xbrli:startDate', ns)
            end_date = period.find('xbrli:endDate', ns)
            instant = period.find('xbrli:instant', ns)
            
            if start_date is not None and end_date is not None:
                ctx_data['period'] = f"{start_date.text} to {end_date.text}"
            elif instant is not None:
                ctx_data['period'] = f"As of {instant.text}"
                
        # Parse Scenario (Dimensions)
        scenario = context.find('xbrli:scenario', ns)
        if scenario is not None:
            dimensions = {}
            for typed_member in scenario.findall('.//xbrldi:typedMember', ns):
                dim = typed_member.attrib.get('dimension', '')
                if '}' in dim:
                    dim = dim.split('}')[1]
                elif ':' in dim:
                    dim = dim.split(':')[1]
                    
                val = typed_member.find('*')
                if val is not None:
                    dimensions[dim] = val.text
            
            for explicit_member in scenario.findall('.//xbrldi:explicitMember', ns):
                dim = explicit_member.attrib.get('dimension', '')
                if '}' in dim:
                    dim = dim.split('}')[1]
                elif ':' in dim:
                    dim = dim.split(':')[1]
                
                val = explicit_member.text
                if val is not None:
                    if '}' in val:
                        val = val.split('}')[1]
                    elif ':' in val:
                        val = val.split(':')[1]
                    dimensions[dim] = val
                    
            if dimensions:
                ctx_data['dimensions'] = dimensions

        contexts[ctx_id] = ctx_data

    # 2. Extract Data Elements
    metrics = []
    
    for elem in root:
        # Skip contexts, units, and non-data tags
        if '}' in elem.tag:
            tag_name = elem.tag.split('}')[1]
            namespace = elem.tag.split('}')[0][1:]
        else:
            tag_name = elem.tag
            namespace = ''
            
        if namespace in [ns['xbrli'], 'http://www.w3.org/1999/xlink', 'http://www.xbrl.org/2003/linkbase']:
            continue
            
        value = elem.text.strip() if elem.text else None
        
        # Only collect elements that have text/values or are empty strings
        if value is not None:
            ctx_ref = elem.attrib.get('contextRef')
            metric_data = {
                'metric': tag_name,
                'value': value,
                'context_id': ctx_ref
            }
            if ctx_ref in contexts:
                metric_data['context_details'] = contexts[ctx_ref]
                
            # Try to get unit
            unit_ref = elem.attrib.get('unitRef')
            if unit_ref:
                metric_data['unitRef'] = unit_ref
                
            metrics.append(metric_data)

    # 3. Save to JSON (optional) if it's run as a script
    output_filename = os.path.basename(file_path).replace('.xml', '_metrics.json')
    output_path = os.path.join(os.path.dirname(file_path), output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)
        
    # print(f"Extracted {len(metrics)} metrics. Saved to {output_path}")
    return metrics

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_xbrl_to_json(sys.argv[1])
    else:
        print("Usage: python extract_brsr_metrics.py <path_to_xbrl_file>")
