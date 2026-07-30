import json
import logging
import os
import sys

# Add the project root to sys.path so we can import fcrm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fcrm.config import NGFSScenario
from fcrm.data.ngfs_loader import fetch_carbon_price_trajectory, fetch_temperature_anomaly, fetch_precipitation_anomaly

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ngfs_fetcher")

def main():
    data = {}
    
    for scenario in NGFSScenario:
        logger.info(f"Fetching data for scenario: {scenario.value}")
        data[scenario.value] = {}
        
        # Carbon Price
        try:
            cp_series = fetch_carbon_price_trajectory(scenario, currency="USD")
            data[scenario.value]["carbon_price_usd"] = cp_series.to_dict()
        except Exception as e:
            logger.error(f"Failed to fetch Carbon Price for {scenario.value}: {e}")
            
        # Temperature Anomaly
        try:
            temp_series = fetch_temperature_anomaly(scenario)
            data[scenario.value]["temperature_anomaly"] = temp_series.to_dict()
        except Exception as e:
            logger.error(f"Failed to fetch Temperature Anomaly for {scenario.value}: {e}")
            
        # Precipitation Anomaly
        try:
            precip_series = fetch_precipitation_anomaly(scenario)
            data[scenario.value]["precipitation_anomaly"] = precip_series.to_dict()
        except Exception as e:
            logger.error(f"Failed to fetch Precipitation Anomaly for {scenario.value}: {e}")
            
    # Define output path
    output_path = "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/ngfs_phase4_trajectories.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    logger.info(f"Successfully saved NGFS data to {output_path}")

if __name__ == "__main__":
    main()
