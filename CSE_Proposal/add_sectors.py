import csv
import re

sectors = {
    'Banks': ['Bank'],
    'Diversified Financials': ['Finance', 'Capital', 'Leasing', 'Investments', 'Holdings', 'Credit', 'Trust', 'Development Company', 'Fund'],
    'Insurance': ['Insurance', 'Assurance', 'Takaful'],
    'Telecommunication Services': ['Telecom', 'Axiata', 'Dialog'],
    'Food, Beverage & Tobacco': ['Plantation', 'Tea', 'Farms', 'Estates', 'Food', 'Beverage', 'Distilleries', 'Brewery', 'Tobacco', 'Milk', 'Salterns', 'Agri'],
    'Consumer Services': ['Hotel', 'Resort', 'Leisure', 'Symphony'],
    'Materials': ['Plastics', 'Aluminium', 'Graphite', 'Ceramic', 'Tiles', 'Glass', 'Cement', 'Chemicals', 'P P L'],
    'Capital Goods': ['Engineering', 'Cables', 'Motors', 'Dockyard', 'Industries', 'Apparel', 'Ventures'],
    'Health Care Equipment & Services': ['Hospital', 'Asiri', 'Nawaloka', 'Singhe', 'Lanka Hospitals', 'Health', 'Medical', 'Channelling'],
    'Real Estate': ['Property', 'Land', 'Housing', 'Properties', 'Realty', 'Residencies'],
    'Utilities': ['Power', 'Energy', 'Hydro', 'WindForce', 'Laxapana', 'Vidullanka'],
    'Consumer Durables & Apparel': ['Apparel', 'Hela', 'Textile', 'Garment', 'Footwear', 'Jewellery', 'Blue Diamonds'],
    'Transportation': ['Cargo', 'Shipping', 'Logistics', 'Aviation', 'Marine'],
    'Retailing': ['Odel', 'Singer', 'Softlogic', 'Cargills', 'Keells'],
    'Software & Services': ['hSenid', 'Software', 'IT', 'Tech'],
    'Automobiles & Components': ['Automobile', 'Tyre', 'Kelani Tyres'],
    'Commercial & Professional Services': ['Printers', 'Publishers', 'Printing', 'Printcare', 'Gestetner'],
    'Energy': ['Lanka IOC', 'LAUGFS Gas']
}

def guess_sector(name):
    name_lower = name.lower()
    for sector, keywords in sectors.items():
        for kw in keywords:
            if re.search(r'\b' + kw.lower() + r'\b', name_lower):
                return sector
    
    # Fallbacks
    if 'holdings' in name_lower:
        return 'Diversified Financials'
    if 'lanka' in name_lower and 'ventures' in name_lower:
        return 'Diversified Financials'
    
    return 'Unclassified (Approximate)'

with open('cse_companies.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

with open('cse_companies.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header + ['Sector'])
    for row in rows:
        name = row[0]
        sector = guess_sector(name)
        writer.writerow(row + [sector])

print("Done")
