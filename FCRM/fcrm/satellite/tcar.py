"""
fcrm.satellite.tcar
--------------------
Transition Cost-at-Risk (TCaR) module — Section 2.2 of the NSRAL spec.

The TCaR module quantifies the structural uncertainty introduced by the energy
transition as a function of the firm's unhedged Green CAPEX requirement.

Core equations:

    Imputed_Emissions_t = Revenue_t × PCAF_Sectoral_Intensity_NIC  [Eq. 10]

    CAPEX_Required,t = Imputed_Emissions_t × θ_NIC,t               [Eq. 11]

    TCaR_t = max(0, CAPEX_Required,t - ω × Green_CAPEX_Realized,t) [Eq. 12]
             ────────────────────────────────────────────────────────
                             Total_Revenue_0

Where:
    θ_NIC,t  – exogenous sector-specific abatement cost factor (USD/tCO2e),
                varying with the NGFS carbon price trajectory
    ω        – Abatement Efficiency Factor (haircut on self-reported green CAPEX)
    Green_CAPEX_Realized – sourced from BRSR filings where available

TCaR is then injected into the Merton credit engine as an additive scalar to
baseline asset volatility: σ_stressed = σ_base × (1 + TCaR_t)

This module also implements the PCAF Data Quality Score hierarchy (Tiers 1–5)
to determine confidence intervals on transition risk estimates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from fcrm.config import NGFSScenario, PCAF_CONFIDENCE_WIDTHS
from fcrm.data.ngfs_loader import fetch_carbon_price_trajectory
from fcrm.data.pcaf_loader import impute_emissions

logger = logging.getLogger(__name__)

# Sector-specific abatement cost multipliers θ_NIC (INR / tCO2e of required CAPEX
# to abate one tonne). Derived from McKinsey Global Energy Perspective 2022 and
# India-specific CEEW marginal abatement cost curves.
# The multiplier is applied to the carbon price trajectory to derive θ_NIC,t.
_ABATEMENT_MULTIPLIER_NIC2: dict[int, float] = {
    # Renewable electricity — lowest abatement cost (already cost-competitive)
    35: 0.8,
    # Steel & metals — significant CapEx for DRI/EAF routes
    24: 3.5, 25: 2.8,
    # Cement — process emissions need CCS (expensive)
    23: 4.2,
    # Petrochemicals
    19: 3.8, 20: 3.2,
    # Mining
    7: 2.5, 8: 2.2, 9: 2.0,
    # Transport
    49: 2.0, 50: 2.5, 51: 3.0,
    # Agriculture (methane/N2O reduction)
    1: 1.5, 2: 1.5, 3: 1.2, 4: 2.8,
    # General manufacturing
    **{k: 1.8 for k in range(11, 35)},
    # Services — minimal CAPEX needed
    **{k: 0.5 for k in range(45, 100)},
}
_DEFAULT_ABATEMENT_MULTIPLIER = 1.8


@dataclass
class BorrowingFirmProfile:
    """
    Minimum firm-level inputs required for TCaR computation.

    Attributes
    ----------
    entity_id : str
        Unique firm identifier.
    nic2 : int
        2-digit NIC sector code.
    total_revenue_base_cr : float
        Total Revenue at base year (INR crore). Used as denominator in Eq. 12.
    scope1_tco2e : float, optional
        Verified Scope 1 emissions from BRSR. If None, PCAF imputation is used.
    scope2_tco2e : float, optional
        Verified Scope 2 emissions from BRSR.
    green_capex_realized_cr : float
        Actual green CAPEX reported in BRSR filings (INR crore / year).
    abatement_efficiency_omega : float
        ω — haircut applied to self-reported green CAPEX to prevent greenwashing.
        Range [0, 1]. A firm with verified emissions decay record → ω near 1.0.
    pcaf_tier : int
        Data quality tier (1–5) from PCAF hierarchy.
    """

    entity_id: str
    nic2: int
    total_revenue_base_cr: float
    scope1_tco2e: Optional[float] = None
    scope2_tco2e: Optional[float] = None
    green_capex_realized_cr: float = 0.0
    abatement_efficiency_omega: float = 0.85
    pcaf_tier: int = 5


def compute_theta(
    nic2: int,
    scenario: NGFSScenario,
    year: int,
) -> float:
    """
    Compute the sector-specific abatement cost factor θ_NIC,t.

    θ_NIC,t = abatement_multiplier_NIC × carbon_price_t (INR / tCO2e)

    Parameters
    ----------
    nic2 : int
        2-digit NIC code.
    scenario : NGFSScenario
        NGFS pathway for the carbon price.
    year : int
        Projection year.

    Returns
    -------
    float
        θ_NIC,t in INR per tCO2e.
    """
    carbon_prices = fetch_carbon_price_trajectory(scenario, currency="INR")
    p_carbon = float(carbon_prices.get(year, 0.0))
    multiplier = _ABATEMENT_MULTIPLIER_NIC2.get(nic2, _DEFAULT_ABATEMENT_MULTIPLIER)
    return p_carbon * multiplier


def compute_tcar_ratio(
    firm: BorrowingFirmProfile,
    scenario: NGFSScenario,
    year: int,
) -> tuple[float, int]:
    """
    Compute TCaR_t for a given firm and scenario year [Equations 10–12].

    Returns
    -------
    tuple[float, int]
        (tcar_ratio, pcaf_quality_tier)
        tcar_ratio = max(0, CAPEX_Required - ω × Green_CAPEX_Realized) / Revenue_0
    """
    # Step 1: Impute emissions [Equation 10]
    imputed_emissions, pcaf_tier = impute_emissions(
        revenue_inr_cr=firm.total_revenue_base_cr,
        nic2=firm.nic2,
        scope1_tco2e=firm.scope1_tco2e,
        scope2_tco2e=firm.scope2_tco2e,
    )

    # Override tier with firm-level if BRSR data was provided
    effective_tier = min(pcaf_tier, firm.pcaf_tier)

    # Step 2: Required CAPEX [Equation 11]
    theta = compute_theta(firm.nic2, scenario, year)
    capex_required = imputed_emissions * theta  # tCO2e × INR/tCO2e = INR

    # Convert CAPEX to INR crore (theta units: INR/tCO2e × tCO2e → INR total)
    # Divide by 1e7 to convert INR to INR crore
    capex_required_cr = capex_required / 1e7

    # Step 3: Unhedged TCaR ratio [Equation 12]
    hedged_capex = firm.abatement_efficiency_omega * firm.green_capex_realized_cr
    unhedged = max(0.0, capex_required_cr - hedged_capex)
    tcar = unhedged / max(firm.total_revenue_base_cr, 1e-6)

    logger.debug(
        "TCaR [%s, year=%d]: emissions=%.1f tCO2e, θ=%.2f INR/tCO2e, "
        "CAPEX_req=%.2f cr, hedged=%.2f cr, TCaR=%.5f (tier=%d).",
        firm.entity_id, year, imputed_emissions, theta,
        capex_required_cr, hedged_capex, tcar, effective_tier,
    )
    return float(np.clip(tcar, 0.0, 10.0)), effective_tier  # cap at 10× revenue for stability


def compute_tcar_series(
    firm: BorrowingFirmProfile,
    scenario: NGFSScenario,
    years: List[int],
) -> pd.DataFrame:
    """
    Compute the full TCaR series for a firm across the NGFS projection horizon.

    Returns
    -------
    pd.DataFrame
        Columns: ['year', 'tcar_ratio', 'pcaf_tier', 'confidence_width']
    """
    records = []
    for year in years:
        tcar, tier = compute_tcar_ratio(firm, scenario, year)
        ci_width = PCAF_CONFIDENCE_WIDTHS.get(tier, 0.50)
        records.append({
            "year": year,
            "tcar_ratio": tcar,
            "pcaf_tier": tier,
            "confidence_width": ci_width,
        })
    return pd.DataFrame(records)


def compute_stressed_asset_volatility(
    sigma_base: float,
    tcar: float,
) -> float:
    """
    Apply TCaR as additive scalar to baseline asset volatility (spec Section 2.2).

    σ_stressed = σ_base × (1 + TCaR_t)

    Parameters
    ----------
    sigma_base : float
        Baseline asset volatility from Merton inversion.
    tcar : float
        TCaR ratio for the current year.

    Returns
    -------
    float
        Stressed asset volatility.
    """
    return sigma_base * (1.0 + tcar)
