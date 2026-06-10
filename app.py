from flask import Flask, render_template, request, jsonify, abort
import pandas as pd
import sys
import os

# Add scripts directory to path to import generate_dashboard
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'report_generation'))
from generate_dashboard import generate_dashboard_html

app = Flask(__name__)

import json

# Load metadata on startup
print("Loading metadata...")
try:
    df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv', usecols=['Name Of The Company'])
    VALID_COMPANIES = sorted(df['Name Of The Company'].dropna().unique().tolist())
    
    df_scores = pd.read_csv('data/reference/mappings/company_to_basic_industry.csv', usecols=['Company Name', 'Basic Industry'])
    df_scores = df_scores.dropna(subset=['Company Name', 'Basic Industry'])
    df_scores = df_scores[df_scores['Company Name'].isin(VALID_COMPANIES)]
    
    basic_to_companies = df_scores.groupby('Basic Industry')['Company Name'].apply(list).to_dict()
    for k in basic_to_companies:
        basic_to_companies[k].sort()
        
    with open('data/reference/mappings/sasb_to_brsr_mapping.json', 'r') as f:
        sasb_to_basic = json.load(f)
        
    print(f"Loaded {len(VALID_COMPANIES)} valid companies and mapping data.")
except Exception as e:
    print(f"Error loading metadata: {e}")
    VALID_COMPANIES = []
    basic_to_companies = {}
    sasb_to_basic = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metadata')
def api_metadata():
    return jsonify({
        "companies": VALID_COMPANIES,
        "basic_to_companies": basic_to_companies,
        "sasb_to_basic": sasb_to_basic
    })

@app.route('/dashboard')
def dashboard():
    company = request.args.get('company')
    if not company:
        return abort(400, "Missing company parameter")
    
    try:
        # Generate the HTML dynamically
        html = generate_dashboard_html(company)
        return html
    except ValueError as ve:
        return abort(404, str(ve))
    except Exception as e:
        return abort(500, f"Error generating dashboard: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
