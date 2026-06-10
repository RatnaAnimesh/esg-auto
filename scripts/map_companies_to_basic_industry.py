import pandas as pd
import json

# NIC 2-digit to Basic Industry Mapping (approximated logically to the 196 list)
nic_to_basic = {
    '01': 'other agricultural products',
    '02': 'forest products',
    '03': 'seafood',
    '05': 'coal',
    '06': 'oil exploration and production',
    '07': 'trading - minerals',
    '08': 'industrial minerals',
    '09': 'oil equipment and services',
    '10': 'packaged foods',
    '11': 'other beverages',
    '12': 'cigarettes and tobacco products',
    '13': 'other textile products',
    '14': 'garments and apparels',
    '15': 'leather and leather products',
    '16': 'plywood boards/laminates',
    '17': 'paper and paper products',
    '18': 'printing and publication',
    '19': 'refineries and marketing',
    '20': 'specialty chemicals',
    '21': 'pharmaceuticals',
    '22': 'tyres and rubber products',
    '23': 'cement and cement products',
    '24': 'iron and steel',
    '25': 'industrial products',
    '26': 'computers hardware and equipments',
    '27': 'heavy electrical equipment',
    '28': 'compressors, pumps and diesel engines',
    '29': 'passenger cars and utility vehicles',
    '30': 'commercial vehicles',
    '31': 'furniture, home furnishing',
    '32': 'diversified consumer products',
    '33': 'repair of computers and personal and household goods',
    '35': 'integrated power utilities',
    '36': 'water supply and management',
    '37': 'waste management',
    '38': 'waste management',
    '39': 'waste management',
    '41': 'residential, commercial projects',
    '42': 'civil construction',
    '43': 'other construction materials',
    '45': 'auto dealers',
    '46': 'trading and distributors',
    '47': 'speciality retail',
    '49': 'road transport',
    '50': 'shipping',
    '51': 'airline',
    '52': 'logistics solution provider',
    '53': 'logistics solution provider',
    '55': 'hotels and resorts',
    '56': 'restaurants',
    '58': 'print media',
    '59': 'film production, distribution and exhibition',
    '60': 'tv broadcasting and software production',
    '61': 'telecom - cellular and fixed line services',
    '62': 'software products',
    '63': 'it enabled services',
    '64': 'non banking financial company (nbfc)',
    '65': 'life insurance',
    '66': 'other financial services',
    '68': 'real estate related services',
    '69': 'consulting services',
    '70': 'consulting services',
    '71': 'civil construction',
    '72': 'healthcare research, analytics and technology',
    '73': 'advertising and media agencies',
    '74': 'consulting services',
    '75': 'healthcare service provider',
    '77': 'diversified commercial services',
    '78': 'business process outsourcing (bpo)/ knowledge process outsourcing (kpo)',
    '79': 'tour travel related services',
    '80': 'diversified commercial services',
    '81': 'diversified commercial services',
    '82': 'business process outsourcing (bpo)/ knowledge process outsourcing (kpo)',
    '84': 'development authority',
    '85': 'education',
    '86': 'hospital',
    '87': 'healthcare service provider',
    '88': 'wellness',
    '90': 'media and entertainment',
    '91': 'media and entertainment',
    '92': 'media and entertainment',
    '93': 'amusement parks/other recreation',
    '94': 'diversified commercial services',
    '95': 'diversified consumer products',
    '96': 'diversified consumer products',
    '97': 'diversified consumer products',
    '98': 'diversified consumer products',
    '99': 'diversified commercial services'
}

df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv')
nic_cols = [c for c in df.columns if 'NICCode' in c]

company_to_basic = []

for idx, row in df.iterrows():
    company = row.get('Name Of The Company', row.get('CompanyName', ''))
    assigned = 'diversified commercial services' # fallback
    
    # Check NIC columns for a valid prefix
    for col in nic_cols:
        val = str(row[col])
        if val != 'nan' and len(val) >= 2:
            prefix = val[:2]
            if prefix in nic_to_basic:
                assigned = nic_to_basic[prefix]
                break
                
    company_to_basic.append({
        'Company Name': company,
        'Basic Industry': assigned
    })

out_df = pd.DataFrame(company_to_basic)
out_df.to_csv('data/reference/mappings/company_to_basic_industry.csv', index=False)
print(f"Mapped {len(out_df)} companies to basic industries.")
