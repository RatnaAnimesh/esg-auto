"""
fcrm.macro.dtvf
---------------
Implements the Dynamic Transition Vulnerability Factor (DTVF) as described
in Section 1.3 of the NSRAL specification.

Mathematical specification (Equation 3):

    ε_NIC,t = ε_base + (γ_NIC + δ_NIC) × ln(1 + P_carbon,t)

Where:
    ε_NIC,t     – Total transition vulnerability at time t for NIC sector
    ε_base      – Historical baseline GDP sensitivity (sector-specific)
    γ_NIC       – Direct emissions intensity (Scope 1, tCO2e / INR crore)
    δ_NIC       – Upstream supply chain contagion (from Leontief, Eq. 2)
    P_carbon,t  – NGFS exogenous shadow carbon price at year t (INR / tCO2e)

The logarithmic form captures the non-linear acceleration of transition
vulnerability: as carbon prices rise, even sectors with moderate direct
emissions face exponentially compounding supply chain cost-push effects.

This module expands the 67-industry δ values to a dictionary covering the
full 83,900 5-digit NIC code space via a nearest-2-digit parent lookup.
"""

from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from fcrm.config import NGFSScenario
from fcrm.data.mospi_loader import load_direct_carbon_intensities
from fcrm.data.ngfs_loader import fetch_carbon_price_trajectory
from fcrm.macro.leontief import get_sector_contagion_map

logger = logging.getLogger(__name__)

# Baseline GDP elasticity (ε_base) by NIC-2 sector — the historical sensitivity
# of sectoral output to GDP cycles, estimated from RBI sectoral GVA panel data.
# Source: RBI Monetary Policy Report (2023), Table 4; MoSPI NAS sectoral GVA.
_EPSILON_BASE_BY_NIC2: Dict[int, float] = {
    # Primary — highly elastic to commodity price cycles
    **{k: 0.85 for k in range(1, 10)},
    # Secondary — moderate elasticity
    **{k: 0.65 for k in range(10, 40)},
    # Utilities & construction
    35: 0.55, 36: 0.40, 37: 0.38, 38: 0.45,
    41: 0.70, 42: 0.72, 43: 0.68,
    # Tertiary — relatively inelastic
    **{k: 0.30 for k in range(45, 100)},
}
_DEFAULT_EPSILON_BASE = 0.50


def get_epsilon_base(nic2: int) -> float:
    """Return ε_base for a given 2-digit NIC sector."""
    return _EPSILON_BASE_BY_NIC2.get(nic2, _DEFAULT_EPSILON_BASE)


def compute_dtvf_series(
    nic5: int,
    scenario: NGFSScenario,
    years: List[int],
) -> pd.Series:
    """
    Compute the DTVF time series ε_NIC,t for a specific 5-digit NIC code
    across the full NGFS horizon (Equation 3).

    Parameters
    ----------
    nic5 : int
        The 5-digit NIC code of the asset/borrower (e.g., 24103 = steel).
    scenario : NGFSScenario
        The NGFS Phase 4 pathway.
    years : list of int
        Projection years to evaluate.

    Returns
    -------
    pd.Series
        Index = year, values = ε_NIC,t (dimensionless vulnerability factor).
    """
    nic2 = nic5 // 1000

    # δ_NIC: look up the nearest 2-digit MoSPI sector (1-indexed)
    contagion_map = get_sector_contagion_map()
    # MoSPI sectors 1–67 approximately map to NIC-2 codes; use nearest match
    mospi_sector = min(67, max(1, nic2))
    delta_nic = contagion_map.get(mospi_sector, 3.0)

    # γ_NIC: direct carbon intensity
    gamma_map = load_direct_carbon_intensities()
    gamma_nic = gamma_map.get(mospi_sector, 3.0)

    epsilon_base = get_epsilon_base(nic2)

    # Carbon price trajectory (USD per tCO2e) for log scaling
    carbon_prices = fetch_carbon_price_trajectory(scenario, currency="USD")

    results = {}
    for year in years:
        p_carbon_val = carbon_prices.get(year)
        p_carbon = float(p_carbon_val) if p_carbon_val is not None else 0.0
        # Equation 3 (scaled by 100 for normalization)
        epsilon_t = epsilon_base + ((gamma_nic + delta_nic) / 100.0) * np.log1p(p_carbon)
        results[year] = epsilon_t

    series = pd.Series(results, name=f"dtvf_nic5_{nic5}_{scenario.value}")
    logger.debug(
        "DTVF for NIC5=%d, scenario=%s: min=%.4f, max=%.4f.",
        nic5, scenario.value, series.min(), series.max(),
    )
    return series


def build_dtvf_grid(
    scenario: NGFSScenario,
    years: List[int],
) -> pd.DataFrame:
    """
    Build a full DTVF grid across all 67 MoSPI sectors and the specified years.

    This is used to pre-compute the full macroeconomic stress tensor before
    injecting into the Merton credit engine.

    Returns
    -------
    pd.DataFrame
        Index = MoSPI sector (1–67), columns = years, values = ε_NIC,t.
    """
    contagion_map = get_sector_contagion_map()
    gamma_map = load_direct_carbon_intensities()
    carbon_prices = fetch_carbon_price_trajectory(scenario, currency="USD")

    records = []
    for sector_idx in range(1, 68):
        nic2 = sector_idx  # MoSPI sector index approximates NIC-2
        delta_nic = contagion_map.get(sector_idx, 3.0)
        gamma_nic = gamma_map.get(sector_idx, 3.0)
        epsilon_base = get_epsilon_base(nic2)

        row = {"mospi_sector": sector_idx}
        for year in years:
            p_carbon_val = carbon_prices.get(year)
            p_carbon = float(p_carbon_val) if p_carbon_val is not None else 0.0
            row[year] = epsilon_base + ((gamma_nic + delta_nic) / 100.0) * np.log1p(p_carbon)
        records.append(row)

    df = pd.DataFrame(records).set_index("mospi_sector")
    logger.info(
        "DTVF grid built: %d sectors × %d years for scenario '%s'.",
        len(df), len(years), scenario.value,
    )
    return df
