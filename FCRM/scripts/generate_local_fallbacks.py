import logging
import os
import sys
import pandas as pd

# Add the project root to sys.path so we can import fcrm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fcrm.data.mca_loader import _build_synthetic_mca_weights
from fcrm.credit.empirical_edf import train_empirical_edf_model
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fallback_generator")

def generate_historical_defaults(output_path: str):
    logger.info("Generating historical defaults data...")
    rng = np.random.default_rng(42)
    n_samples = 10000

    dd = rng.normal(loc=3.0, scale=2.0, size=n_samples)
    cs = rng.beta(a=2, b=5, size=n_samples)

    z = 3.5 - 1.2 * dd + 0.8 * cs - 0.4 * dd * cs
    pd_true = 1.0 / (1.0 + np.exp(-z))
    y = rng.binomial(n=1, p=pd_true)

    df = pd.DataFrame({
        "dd": dd,
        "climate_severity": cs,
        "default_in_4q": y
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved historical defaults to {output_path}")

def generate_mca_data(output_path: str):
    logger.info("Generating MCA Master Data...")
    df = _build_synthetic_mca_weights()
    # Ensure it matches the expected CSV format
    # The loader expects: ["nic5", "company_count", "paid_up_capital_cr"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved MCA Master Data to {output_path}")

def main():
    mca_path = "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/mca_master_data.csv"
    defaults_path = "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/historical_defaults.csv"
    
    generate_mca_data(mca_path)
    generate_historical_defaults(defaults_path)
    
if __name__ == "__main__":
    main()
