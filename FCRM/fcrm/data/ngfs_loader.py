"""
fcrm.data.ngfs_loader
---------------------
Fetches NGFS Phase 4 scenario trajectories from local data cache.
Returns tidy DataFrames with year-indexed carbon price,
temperature anomaly, and precipitation anomaly projections.

Local cache: data/ngfs_phase4_trajectories.json
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd

from fcrm.config import NGFS_CARBON_PRICE_USD, NGFSScenario, INR_PER_USD

logger = logging.getLogger(__name__)

_LOCAL_NGFS_PATH = "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/ngfs_phase4_trajectories.json"


@lru_cache(maxsize=1)
def _load_local_ngfs_data() -> dict:
    try:
        with open(_LOCAL_NGFS_PATH, 'r') as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load local NGFS data from %s: %s", _LOCAL_NGFS_PATH, exc)
        return {}


@lru_cache(maxsize=32)
def fetch_carbon_price_trajectory(
    scenario: NGFSScenario,
    model: str = "REMIND-MAgPIE 3.2-4.6",
    region: str = "World",
    currency: str = "INR",
) -> pd.Series:
    """
    Fetch the annual shadow carbon price trajectory for a given NGFS scenario.
    """
    data = _load_local_ngfs_data()
    scenario_data = data.get(scenario.value, {})
    
    if "carbon_price_usd" in scenario_data:
        # Convert string keys back to int years
        prices = {int(k): v for k, v in scenario_data["carbon_price_usd"].items()}
        series = pd.Series(prices, name=f"carbon_price_usd_{scenario.value}")
    else:
        logger.warning("NGFS local data missing for carbon price. Falling back.")
        fallback = NGFS_CARBON_PRICE_USD[scenario]
        series = pd.Series(fallback, name=f"carbon_price_usd_{scenario.value}")

    if currency.upper() == "INR":
        series = series * INR_PER_USD
        series.name = f"carbon_price_inr_{scenario.value}"

    return series.sort_index()


@lru_cache(maxsize=32)
def fetch_temperature_anomaly(
    scenario: NGFSScenario,
    region: str = "South Asia",
) -> pd.Series:
    """
    Fetch annual temperature anomaly (°C above pre-industrial baseline) from NGFS.
    """
    data = _load_local_ngfs_data()
    scenario_data = data.get(scenario.value, {})
    
    if "temperature_anomaly" in scenario_data:
        temps = {int(k): v for k, v in scenario_data["temperature_anomaly"].items()}
        return pd.Series(temps, name=f"delta_T_{scenario.value}").sort_index()

    # Fallback
    _FALLBACK_WARMING: dict[NGFSScenario, float] = {
        NGFSScenario.NET_ZERO_2050: 1.5,
        NGFSScenario.BELOW_2C: 1.8,
        NGFSScenario.DELAYED_TRANSITION: 1.8,
        NGFSScenario.DIVERGENT_NET_ZERO: 1.6,
        NGFSScenario.NDCS: 2.5,
        NGFSScenario.CURRENT_POLICIES: 3.0,
    }
    end_temp = _FALLBACK_WARMING[scenario]
    years = np.arange(2024, 2051)
    warming = np.linspace(1.1, end_temp, len(years))
    return pd.Series(warming, index=years, name=f"delta_T_{scenario.value}")


@lru_cache(maxsize=32)
def fetch_precipitation_anomaly(
    scenario: NGFSScenario,
    region: str = "South Asia",
) -> pd.Series:
    """
    Fetch annual precipitation anomaly (% change from 1995-2014 baseline).
    """
    data = _load_local_ngfs_data()
    scenario_data = data.get(scenario.value, {})
    
    if "precipitation_anomaly" in scenario_data:
        precip = {int(k): v for k, v in scenario_data["precipitation_anomaly"].items()}
        return pd.Series(precip, name=f"delta_P_{scenario.value}").sort_index()

    # Fallback
    _FALLBACK_PRECIP_2050: dict[NGFSScenario, float] = {
        NGFSScenario.NET_ZERO_2050: 0.05,
        NGFSScenario.BELOW_2C: 0.07,
        NGFSScenario.DELAYED_TRANSITION: 0.09,
        NGFSScenario.DIVERGENT_NET_ZERO: 0.08,
        NGFSScenario.NDCS: 0.12,
        NGFSScenario.CURRENT_POLICIES: 0.18,
    }
    years = np.arange(2024, 2051)
    end_val = _FALLBACK_PRECIP_2050[scenario]
    precip = np.linspace(0.01, end_val, len(years))
    return pd.Series(precip, index=years, name=f"delta_P_{scenario.value}")
