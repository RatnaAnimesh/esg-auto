import xml.etree.ElementTree as ET
import json
import sys
import os

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

    # 3. Save to JSON
    output_filename = os.path.basename(file_path).replace('.xml', '_metrics.json')
    output_path = os.path.join(os.path.dirname(file_path), output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Extracted {len(metrics)} metrics. Saved to {output_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_xbrl_to_json(sys.argv[1])
    else:
        print("Usage: python extract_brsr_metrics.py <path_to_xbrl_file>")
