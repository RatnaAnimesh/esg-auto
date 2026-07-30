"""
fcrm.institutional.cet1
------------------------
CET1 Capital Degradation Engine — Sections 4.1 and 4.2 of the NSRAL spec.

The metric of institutional survivability is the Common Equity Tier 1
Capital Ratio variation [Equation 25]:

    CET1_Stressed = (CET1_CapitalBase - Loss_Total)
                    ─────────────────────────────────────────
                    RWA_base × (1 + r_inf)

Where:
    CET1_CapitalBase – Core equity tier 1 capital (static balance sheet input)
    Loss_Total       – Five-component total institutional loss (Eq. 27)
    RWA_base         – Baseline risk-weighted assets (static input)
    r_inf            – Dynamic RWA inflation rate from portfolio ratings migration

RWA Inflation Rate r_inf [Equation 26]:

    r_inf = [Σᵢ K(PD_stressed,i, LGD_stressed,i) × 12.5 × EAD_i] / Σᵢ RWA_base,i - 1

Where K(·) is the Basel III A-IRB capital requirement function.

The 12.5 scaling factor is the global regulatory constant (= 1 / 0.08).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from fcrm.config import EngineConfig, BASEL_RWA_SCALING_FACTOR
from fcrm.credit.ecl import compute_rwa_contribution, LoanExposure
from fcrm.institutional.total_loss import (
    InstitutionalBalanceSheet,
    LossComponents,
    compute_total_institutional_loss,
)

logger = logging.getLogger(__name__)


@dataclass
class LoanStressResult:
    """Per-loan stress output required for RWA inflation calculation."""

    facility_id: str
    pd_stressed: float
    lgd_stressed: float
    ead_cr: float
    rwa_stressed_cr: float
    rwa_base_cr: float
    ecl_stressed_cr: float
    delta_ecl_cr: float


def compute_rwa_inflation_rate(
    loan_results: List[LoanStressResult],
) -> float:
    """
    Compute the dynamic RWA inflation rate r_inf [Equation 26].

    r_inf = Σᵢ [K(PD_stressed,i, LGD_stressed,i) × 12.5 × EAD_i]
            ─────────────────────────────────────────────────────── - 1
                          Σᵢ RWA_base,i

    Parameters
    ----------
    loan_results : list of LoanStressResult
        Per-loan stressed RWA and baseline RWA contributions.

    Returns
    -------
    float
        r_inf ≥ 0. Positive value indicates RWA inflation under stress.
    """
    total_rwa_stressed = sum(r.rwa_stressed_cr for r in loan_results)
    total_rwa_base = sum(r.rwa_base_cr for r in loan_results)

    if total_rwa_base < 1e-6:
        logger.warning("Total baseline RWA near zero; returning r_inf = 0.")
        return 0.0

    r_inf = (total_rwa_stressed / total_rwa_base) - 1.0
    logger.debug(
        "RWA inflation: stressed=%.2f cr, base=%.2f cr → r_inf=%.4f.",
        total_rwa_stressed, total_rwa_base, r_inf,
    )
    return float(max(r_inf, 0.0))


def compute_cet1_stressed(
    balance_sheet: InstitutionalBalanceSheet,
    loss_components: LossComponents,
    r_inf: float,
) -> float:
    """
    Compute the stressed CET1 Capital Ratio [Equation 25].

    CET1_Stressed = (CET1_CapitalBase - Loss_Total)
                    ─────────────────────────────────────────
                    RWA_base × (1 + r_inf)

    Parameters
    ----------
    balance_sheet : InstitutionalBalanceSheet
        Institutional inputs (CET1_CapitalBase, RWA_base).
    loss_components : LossComponents
        Five-component loss breakdown (total = Loss_Total).
    r_inf : float
        Dynamic RWA inflation rate from portfolio stress.

    Returns
    -------
    float
        Stressed CET1 ratio. May be negative (capital shortfall).
    """
    numerator = balance_sheet.cet1_capital_base_cr - loss_components.total_cr
    denominator = balance_sheet.rwa_base_cr * (1.0 + r_inf)

    if denominator < 1e-6:
        logger.error(
            "RWA denominator near zero for institution '%s'. CET1 ratio undefined.",
            balance_sheet.institution_id,
        )
        return -1.0  # undefined / severe capital shortfall

    cet1_ratio = numerator / denominator
    logger.info(
        "CET1 Stressed [%s]: %.4f (regulatory minimum: %.4f) | "
        "Loss=%.2f cr, RWA_stressed=%.2f cr.",
        balance_sheet.institution_id,
        cet1_ratio,
        EngineConfig().cet1_regulatory_minimum,
        loss_components.total_cr,
        denominator,
    )
    return float(cet1_ratio)


@dataclass
class InstitutionalStressOutput:
    """
    Complete output of the institutional stress engine for one scenario year.

    Attributes
    ----------
    institution_id : str
    year : int
    cet1_stressed : float
        Stressed CET1 ratio (Equation 25).
    cet1_base : float
        Pre-stress CET1 ratio (= CET1_CapitalBase / RWA_base).
    cet1_decline : float
        Absolute decline in CET1 ratio.
    capital_shortfall_cr : float
        Capital shortfall relative to 8% minimum (INR crore). 0 if solvent.
    loss_components : LossComponents
        Breakdown of the five loss vectors.
    r_inf : float
        RWA inflation rate.
    passes_regulatory_minimum : bool
        Whether the institution clears the 8% CET1 threshold.
    """

    institution_id: str
    year: int
    cet1_stressed: float
    cet1_base: float
    cet1_decline: float
    capital_shortfall_cr: float
    loss_components: LossComponents
    r_inf: float
    passes_regulatory_minimum: bool


def run_institutional_stress(
    balance_sheet: InstitutionalBalanceSheet,
    loan_results: List[LoanStressResult],
    portfolio_pd_stressed: float,
    climate_severity: float,
    year: int,
    config: EngineConfig = EngineConfig(),
) -> InstitutionalStressOutput:
    """
    Full institutional stress engine: from loan-level results to CET1 ratio.

    Orchestrates RWA inflation, total loss aggregation, and CET1 computation
    for a single scenario year.

    Parameters
    ----------
    balance_sheet : InstitutionalBalanceSheet
        Static balance sheet inputs.
    loan_results : list of LoanStressResult
        Per-loan stress outputs from the credit engine.
    portfolio_pd_stressed : float
        Portfolio-level weighted average stressed PD.
    climate_severity : float
        NGFS severity ∈ [0.0, 1.0].
    year : int
        Projection year.
    config : EngineConfig

    Returns
    -------
    InstitutionalStressOutput
    """
    # Aggregate ΔECLᵢₙ꜀
    delta_ecl_total = sum(r.delta_ecl_cr for r in loan_results)

    # Compute total loss (all five components)
    loss = compute_total_institutional_loss(
        balance_sheet=balance_sheet,
        delta_ecl_cr=delta_ecl_total,
        portfolio_pd_stressed=portfolio_pd_stressed,
        climate_severity=climate_severity,
    )

    # RWA inflation rate
    r_inf = compute_rwa_inflation_rate(loan_results)

    # Stressed CET1 ratio
    cet1_stressed = compute_cet1_stressed(balance_sheet, loss, r_inf)

    # Baseline CET1 ratio
    cet1_base = balance_sheet.cet1_capital_base_cr / max(balance_sheet.rwa_base_cr, 1e-6)

    # Capital shortfall vs. regulatory minimum
    min_ratio = config.cet1_regulatory_minimum
    denominator = balance_sheet.rwa_base_cr * (1.0 + r_inf)
    min_capital_required = min_ratio * denominator
    capital_available = balance_sheet.cet1_capital_base_cr - loss.total_cr
    shortfall = max(0.0, min_capital_required - capital_available)

    return InstitutionalStressOutput(
        institution_id=balance_sheet.institution_id,
        year=year,
        cet1_stressed=cet1_stressed,
        cet1_base=cet1_base,
        cet1_decline=cet1_base - cet1_stressed,
        capital_shortfall_cr=shortfall,
        loss_components=loss,
        r_inf=r_inf,
        passes_regulatory_minimum=cet1_stressed >= min_ratio,
    )
