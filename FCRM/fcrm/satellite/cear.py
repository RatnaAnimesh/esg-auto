"""
fcrm.satellite.cear
--------------------
Climate Earnings-at-Risk (CEaR) module — Section 2.1 of the NSRAL spec.

The CEaR module translates local climate hazard anomalies into operational
cash flow compression. The core ratio is computed via the bivariate
exponential decay function [Equation 4]:

    CEaR_Ratio_t = 1 - exp(-(η_T × ΔT_t + η_P × |ΔP_t|))

Where:
    η_T  – empirical heat sensitivity elasticity (sector- and NIC5-specific)
    η_P  – empirical precipitation sensitivity elasticity
    ΔT_t – temperature anomaly (°C) at year t relative to 1995-2014 baseline
    |ΔP_t| – absolute precipitation anomaly (fraction) at year t

Applied CEaR ratio degrades the firm's EBITDA:
    EBITDA_stressed_t = EBITDA_base × (1 - CEaR_Ratio_t)

For multi-facility entities, Capacity-Weighted Aggregation is applied first
to derive a corporate-level climate shock vector before computing the ratio.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from fcrm.config import NGFSScenario
from fcrm.data.ngfs_loader import fetch_temperature_anomaly, fetch_precipitation_anomaly
from fcrm.satellite.elasticity_calibrator import build_nic5_elasticity_tensor

logger = logging.getLogger(__name__)


@dataclass
class Facility:
    """
    A single physical operating facility of a corporate entity.

    Attributes
    ----------
    name : str
        Facility identifier.
    lat : float
        Latitude of the facility.
    lon : float
        Longitude of the facility.
    capacity_weight : float
        Proportion of corporate capacity at this facility (weights sum to 1.0).
    nic5 : int
        5-digit NIC sector code of the facility's activity.
    """

    name: str
    lat: float
    lon: float
    capacity_weight: float
    nic5: int


@dataclass
class CorporateEntity:
    """
    Corporate entity with one or more geographically distributed facilities.

    Attributes
    ----------
    entity_id : str
        Unique identifier (e.g., CIN or ticker).
    ebitda_base_cr : float
        Baseline EBITDA in INR crore (consolidated entity level).
    facilities : list of Facility
        Physical asset locations and their capacity weights.
    """

    entity_id: str
    ebitda_base_cr: float
    facilities: List[Facility] = field(default_factory=list)


def _get_elasticities_for_nic5(
    nic5: int,
    elasticity_tensor: pd.DataFrame,
) -> Tuple[float, float]:
    """
    Look up η_T and η_P for a given 5-digit NIC code.

    Falls back to 4-digit → 2-digit lookup hierarchy if exact match is absent.
    """
    nic4 = nic5 // 10
    nic2 = nic5 // 1000

    mask5 = elasticity_tensor["nic4"] == nic4
    if mask5.any():
        row = elasticity_tensor[mask5].iloc[0]
        return float(row["eta_T"]), float(row["eta_P"])

    mask2 = elasticity_tensor["nic2"] == nic2
    if mask2.any():
        row = elasticity_tensor[mask2].iloc[0]
        return float(row["eta_T"]), float(row["eta_P"])

    logger.warning("No elasticity found for NIC5=%d. Using global default.", nic5)
    return -0.012, -0.006


def compute_cear_ratio(
    eta_T: float,
    eta_P: float,
    delta_T: float,
    delta_P: float,
) -> float:
    """
    Compute the CEaR compression ratio for a single facility-year [Equation 4].

    CEaR_Ratio_t = 1 - exp(-(η_T × ΔT_t + η_P × |ΔP_t|))

    Parameters
    ----------
    eta_T : float
        Heat elasticity coefficient (negative for damage; absolute value used).
    eta_P : float
        Precipitation elasticity coefficient (absolute value used).
    delta_T : float
        Temperature anomaly in °C.
    delta_P : float
        Precipitation anomaly (fractional, e.g., 0.10 = +10%).

    Returns
    -------
    float
        CEaR ratio in [0, 1]. 0 = no compression; 1 = complete destruction.
    """
    # Use absolute values of elasticities (both are negative by construction)
    stress = abs(eta_T) * abs(delta_T) + abs(eta_P) * abs(delta_P)
    ratio = 1.0 - np.exp(-stress)
    return float(np.clip(ratio, 0.0, 1.0))


def compute_entity_cear_series(
    entity: CorporateEntity,
    scenario: NGFSScenario,
    years: List[int],
    elasticity_tensor: Optional[pd.DataFrame] = None,
) -> pd.Series:
    """
    Compute the annual CEaR ratio series for a corporate entity.

    For multi-facility entities, applies Capacity-Weighted Aggregation to
    derive corporate-level climate shock prior to computing the CEaR ratio.

    Parameters
    ----------
    entity : CorporateEntity
        The firm whose EBITDA compression is to be computed.
    scenario : NGFSScenario
        NGFS pathway.
    years : list of int
        Projection years.
    elasticity_tensor : pd.DataFrame, optional
        Pre-computed elasticity tensor. If None, it is built on demand.

    Returns
    -------
    pd.Series
        Index = year, values = CEaR ratio ∈ [0, 1].
    """
    if elasticity_tensor is None:
        logger.info("Building NIC5 elasticity tensor (may take ~30s for first call).")
        elasticity_tensor = build_nic5_elasticity_tensor()

    # Fetch NGFS climate trajectories (regional — approximate to India average)
    temp_series = fetch_temperature_anomaly(scenario)
    precip_series = fetch_precipitation_anomaly(scenario)

    # Capacity-weighted aggregation of facility climate shocks
    assert abs(sum(f.capacity_weight for f in entity.facilities) - 1.0) < 1e-6 or not entity.facilities, \
        "Facility capacity weights must sum to 1.0"

    results = {}
    for year in years:
        delta_T_corp = float(temp_series.get(year, 0.0))
        delta_P_corp = float(precip_series.get(year, 0.0))

        if entity.facilities:
            # Capacity-weighted average anomaly across facilities
            # (In a full implementation, each facility has location-specific CMIP6 data)
            weighted_T = sum(
                f.capacity_weight * delta_T_corp for f in entity.facilities
            )
            weighted_P = sum(
                f.capacity_weight * delta_P_corp for f in entity.facilities
            )

            # Weighted-average elasticities
            weighted_eta_T = sum(
                f.capacity_weight * _get_elasticities_for_nic5(f.nic5, elasticity_tensor)[0]
                for f in entity.facilities
            )
            weighted_eta_P = sum(
                f.capacity_weight * _get_elasticities_for_nic5(f.nic5, elasticity_tensor)[1]
                for f in entity.facilities
            )
        else:
            weighted_T = delta_T_corp
            weighted_P = delta_P_corp
            weighted_eta_T = -0.012
            weighted_eta_P = -0.006

        results[year] = compute_cear_ratio(weighted_eta_T, weighted_eta_P, weighted_T, weighted_P)

    series = pd.Series(results, name=f"cear_{entity.entity_id}_{scenario.value}")
    logger.debug(
        "CEaR for entity %s, scenario %s: max=%.4f at year %d.",
        entity.entity_id, scenario.value,
        series.max(), int(series.idxmax()),
    )
    return series


def compute_stressed_ebitda(
    entity: CorporateEntity,
    scenario: NGFSScenario,
    years: List[int],
    elasticity_tensor: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Compute stressed EBITDA trajectory applying annual CEaR compression.

    Returns
    -------
    pd.DataFrame
        Columns: ['year', 'cear_ratio', 'ebitda_stressed_cr', 'ebitda_base_cr']
    """
    cear_series = compute_entity_cear_series(entity, scenario, years, elasticity_tensor)

    records = []
    for year in years:
        ratio = cear_series.get(year, 0.0)
        ebitda_stressed = entity.ebitda_base_cr * (1.0 - ratio)
        records.append({
            "year": year,
            "cear_ratio": ratio,
            "ebitda_stressed_cr": ebitda_stressed,
            "ebitda_base_cr": entity.ebitda_base_cr,
        })

    return pd.DataFrame(records)
