import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import numpy as np
import pandas as pd
import logging
import base64
import io

# Import FCRM modules
from fcrm.credit.ecl import LoanExposure
from fcrm.institutional.cet1 import InstitutionalBalanceSheet
from fcrm.credit.merton import FirmSnapshot
from fcrm.satellite.cear import CorporateEntity, Facility
from fcrm.satellite.tcar import BorrowingFirmProfile
from fcrm.pipeline import BorrowerInput, run_full_stress_test
from fcrm.config import EngineConfig, NGFSScenario

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default Asset Path
DF_ASSETS_PATH = "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/testing/datasets/geoasset_india.csv"

def load_default_portfolio():
    try:
        df_assets = pd.read_csv(DF_ASSETS_PATH)
        df_india = df_assets[df_assets['country'] == 'IND'].copy()
        df_india = df_india.dropna(subset=['latitude', 'longitude', 'capacity_mw'])
        return df_india.sort_values(by='capacity_mw', ascending=False).head(50)
    except Exception as e:
        logger.error(f"Failed to load geoasset_india.csv: {e}")
        return pd.DataFrame(columns=['name', 'capacity_mw', 'latitude', 'longitude'])

def get_color(val, vmin=0, vmax=100):
    val = max(vmin, min(vmax, val))
    ratio = (val - vmin) / (vmax - vmin) if vmax > vmin else 0
    # Yellow to Red gradient: rgb(255, 237, 160) to rgb(177, 0, 38)
    r = int(255 + ratio * (177 - 255))
    g = int(237 + ratio * (0 - 237))
    b = int(160 + ratio * (38 - 160))
    return f"rgb({r},{g},{b})"

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap",
        "/assets/style.css"
    ]
)
app.title = "FCRM Portfolio Climate Risk"

app.layout = html.Div(id="main-container", className="dashboard-container light-theme", children=[
    dcc.Store(id='theme-store', data='light'),
    
    # Nav
    html.Nav([
        html.Div("FCRM Platform", className="nav-brand"),
        html.Div([
            html.A("Documentation", href="#", className="nav-link"),
            html.A("API Reference", href="#", className="nav-link"),
        ], className="nav-links"),
        html.Div([
            html.Button("☀️ / 🌙", id="theme-toggle", className="btn--kbd"),
            html.A("Console", href="#", className="btn--primary")
        ], className="nav-actions")
    ], className="nav"),
    
    # Hero Stat-Led
    html.Section([
        html.Div(id="hero-stat", className="figure tnum", children="--"),
        html.P("Portfolio average baseline PD. Run the FCRM engine across various NGFS scenarios.", className="qualifier"),
        
        html.Div([
            dcc.Dropdown(
                id='scenario-dropdown',
                options=[
                    {'label': 'Orderly Transition (Net Zero 2050)', 'value': NGFSScenario.NET_ZERO_2050.value},
                    {'label': 'Disorderly Transition (Delayed Transition)', 'value': NGFSScenario.DELAYED_TRANSITION.value},
                    {'label': 'Hot House World (Current Policies - 3°C)', 'value': NGFSScenario.CURRENT_POLICIES.value},
                ],
                value=NGFSScenario.NET_ZERO_2050.value,
                clearable=False,
                className="scenario-dropdown",
                style={"color": "#111827"} # ensure dropdown text is readable
            ),
        ], style={'maxWidth': '400px', 'margin': '0 auto 1.5rem', 'textAlign': 'left'}),
        
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.Span('Select Portfolio CSV', className="upload-link")]),
            className="upload-box",
            multiple=False
        )
    ], className="stat-hero"),

    dcc.Loading(
        id="loading-map",
        type="default",
        color="oklch(58% 0.20 256)",
        children=[
            # Body supporting stats
            html.Section(id='stats-container', className="supporting-stats"),

            # Map in dark graphite band
            html.Section([
                html.Div([
                    html.H2("Geospatial Climate Exposure", className="section-title"),
                    html.P("Mapping facility locations to climate risk scores (ΔPD) via Leaflet.", className="section-lede")
                ], className="graphite-header"),
                html.Div(
                    id='map-container',
                    className="code-card map-container"
                )
            ], className="graphite-band")
        ]
    ),
    
    # Footer
    html.Footer([
        html.Div("FCRM Engine © 2026", className="footer-brand"),
        html.Div([
            html.A("Status: 200 OK", className="status--ok"),
        ], className="footer-links")
    ], className="footer")
])

def process_portfolio(df, scenario_value):
    """Run the pipeline for each row and return results."""
    results = []
    engine_config = EngineConfig(
        scenario=NGFSScenario(scenario_value),
        base_year=2024,
        horizon_years=[2050]
    )
    balance_sheet = InstitutionalBalanceSheet(
        institution_id="portfolio_bank",
        cet1_capital_base_cr=50000.0,
        rwa_base_cr=400000.0,
        treasury_portfolio_cr=50000.0,
        total_credit_portfolio_cr=500000.0,
        total_undrawn_commitments_cr=100000.0
    )
    
    for idx, row in df.iterrows():
        try:
            name = str(row.get('name', f'Asset_{idx}'))
            lat = float(row.get('latitude', 0))
            lon = float(row.get('longitude', 0))
            cap = float(row.get('capacity_mw', 100))
            loan_amount = float(row.get('loan_amount_cr', cap * 5))
            
            fac = Facility(name=name, lat=lat, lon=lon, capacity_weight=1.0, nic5=35102)
            cear_entity = CorporateEntity(entity_id=name, ebitda_base_cr=cap * 2, facilities=[fac])
            loan = LoanExposure(facility_id=name, drawn_balance_cr=loan_amount, undrawn_balance_cr=0.0, ccf=1.0, maturity_years=5.0)
            firm = FirmSnapshot(entity_id=name, equity_value_cr=loan_amount * 0.5, equity_volatility_annual=0.4, short_term_debt_cr=loan_amount * 0.2, long_term_debt_cr=loan_amount * 0.8)
            tcar = BorrowingFirmProfile(entity_id=name, nic2=35, total_revenue_base_cr=cap * 2, scope1_tco2e=1000, scope2_tco2e=500)
            
            borrower = BorrowerInput(entity_id=name, loan=loan, firm_snapshot=firm, cear_entity=cear_entity, tcar_profile=tcar)
            res_list = run_full_stress_test([borrower], balance_sheet, scenario=NGFSScenario(scenario_value), config=engine_config)
            res = res_list[0].borrower_results[0]
            print(f"[{name}] TCaR: {res.tcar_ratio:.4f}, CEaR: {res.cear_ratio:.4f}")
            
            results.append({
                'name': name,
                'lat': lat,
                'lon': lon,
                'capacity': cap,
                'loan_amount': loan_amount,
                'pd_base': res.pd_base,
                'pd_stressed': res.pd_stressed,
                'delta_pd': res.pd_stressed - res.pd_base,
                'climate_severity': borrower.climate_risk_score
            })
        except Exception as e:
            logger.error(f"Error processing {row.get('name', idx)}: {e}")
            
    return pd.DataFrame(results)

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return df
    except Exception as e:
        logger.error(f"Error parsing upload: {e}")
    return None

@app.callback(
    Output('theme-store', 'data'),
    Input('theme-toggle', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=True
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    return 'dark' if current_theme == 'light' else 'light'

@app.callback(
    Output('main-container', 'className'),
    Input('theme-store', 'data')
)
def update_container_class(theme):
    base = "dashboard-container"
    return f"{base} dark-theme" if theme == 'dark' else f"{base} light-theme"

@app.callback(
    [Output('hero-stat', 'children'),
     Output('stats-container', 'children'),
     Output('map-container', 'children')],
    [Input('upload-data', 'contents'),
     Input('scenario-dropdown', 'value'),
     Input('theme-store', 'data')],
    [State('upload-data', 'filename')]
)
def update_dashboard(list_of_contents, scenario_val, theme, list_of_names):
    if list_of_contents is not None:
        df = parse_contents(list_of_contents, list_of_names)
        if df is None:
            df = load_default_portfolio()
    else:
        df = load_default_portfolio()
        
    if len(df) == 0:
        return "--", html.Div("No data available.", className="stat-card"), html.Div()
        
    # Process portfolio through FCRM Engine
    results_df = process_portfolio(df, scenario_val)
    
    if len(results_df) == 0:
        return "--", html.Div("Error running pipeline.", className="stat-card"), html.Div()
        
    # Generate Stats
    total_assets = len(results_df)
    avg_pd_base = results_df['pd_base'].mean() * 100
    avg_pd_stressed = results_df['pd_stressed'].mean() * 100
    avg_delta_pd = results_df['delta_pd'].mean() * 100
    
    hero_stat = f"{avg_pd_base:.2f}%"
    
    stats = [
        html.Div([
            html.H3("Total Facilities"),
            html.P(f"{total_assets}")
        ], className="stat-card"),
        html.Div([
            html.H3(f"Stressed PD"),
            html.P(f"{avg_pd_stressed:.2f}%")
        ], className="stat-card"),
        html.Div([
            html.H3("Climate Risk (ΔPD)"),
            html.P(f"+{avg_delta_pd:.2f}%", className="delta positive")
        ], className="stat-card")
    ]
    
    # Generate Leaflet Map
    markers = []
    max_delta = max(results_df['delta_pd'].max() * 100, 1.0)
    max_loan = results_df['loan_amount'].max() or 1
    
    for idx, row in results_df.iterrows():
        d_pct = row['delta_pd'] * 100
        color = get_color(d_pct, vmin=0, vmax=max_delta)
        markers.append(
            dl.CircleMarker(
                center=[row['lat'], row['lon']],
                radius=row['loan_amount'] / max_loan * 15 + 5,
                color=color,
                fillColor=color,
                fillOpacity=0.8,
                weight=1,
                children=[
                    dl.Tooltip(
                        html.Div([
                            html.B(row['name']), html.Br(),
                            f"Loan: {row['loan_amount']:.0f} Cr", html.Br(),
                            f"Base PD: {row['pd_base']*100:.2f}%", html.Br(),
                            f"Stressed PD: {row['pd_stressed']*100:.2f}%", html.Br(),
                            f"Delta PD: +{d_pct:.2f}%"
                        ])
                    )
                ]
            )
        )
        
    tile_url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png' if theme == 'dark' else 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    
    map_element = dl.Map(
        [
            dl.TileLayer(url=tile_url),
            dl.LayerGroup(markers)
        ],
        center=[22.0, 78.0],
        zoom=4.5,
        style={'width': '100%', 'height': '100%'}
    )
    
    return hero_stat, stats, map_element

if __name__ == '__main__':
    app.run(debug=True, port=8050)
