import xml.etree.ElementTree as ET
import os

def parse_calculation_linkbase(filepath):
    """
    Parses an XBRL calculation linkbase XML file to extract calculation relationships.
    Returns a dictionary where keys are 'summation' variables (Target) and 
    values are lists of tuples: (item_variable, weight).
    """
    if not os.path.exists(filepath):
        print(f"Warning: Taxonomy file not found at {filepath}")
        return {}

    tree = ET.parse(filepath)
    root = tree.getroot()

    # XML Namespaces used in XBRL
    ns = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink'
    }

    # Extract locators: mapping xlink:label -> element name
    locators = {}
    for loc in root.findall('.//link:loc', ns):
        label = loc.get(f"{{{ns['xlink']}}}label")
        href = loc.get(f"{{{ns['xlink']}}}href")
        if label and href:
            # href typically looks like "in-capmkt-ent.xsd#in-capmkt_WaterDischargeToSurfaceWater"
            element_id = href.split('#')[-1]
            # Remove namespace prefix if any (e.g. 'in-capmkt_')
            if '_' in element_id:
                element_name = element_id.split('_', 1)[1]
            else:
                element_name = element_id
            locators[label] = element_name

    calculations = {}
    
    # Extract calculation arcs
    for arc in root.findall('.//link:calculationArc', ns):
        from_label = arc.get(f"{{{ns['xlink']}}}from")
        to_label = arc.get(f"{{{ns['xlink']}}}to")
        weight_str = arc.get("weight")
        
        if from_label and to_label and weight_str:
            target = locators.get(from_label)
            item = locators.get(to_label)
            weight = float(weight_str)
            
            if target and item:
                if target not in calculations:
                    calculations[target] = []
                calculations[target].append((item, weight))
                
    return calculations

if __name__ == "__main__":
    # Test script
    mock_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'taxonomy', 'in-capmkt-cal.xml')
    print("Parsed Calculations:", parse_calculation_linkbase(mock_path))
