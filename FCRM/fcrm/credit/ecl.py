"""
fcrm.credit.ecl
---------------
Expected Credit Loss aggregation — terminal credit engine output.

Implements ECL computation and Basel A-IRB capital requirement per
Sections 3.5 and 4.2.2 of the NSRAL spec.

Final loan-level loss metric [Equation 24]:
    ECL_Stressed = PD_stressed × LGD_stressed × EAD                [Eq. 24]

Where EAD = drawn balance + (undrawn credit line × CCF).

Basel A-IRB capital requirement K per loan:
    K(PD, LGD) = LGD × [Φ(√(1/(1-R)) × Φ⁻¹(PD) + √(R/(1-R)) × Φ⁻¹(0.999))
                         - PD × LGD] × (1 - 1.5b) / (1 - 1.5b) × (1 + (M-2.5)b)

Where R = 0.12 (corporate asset correlation), M = maturity (years),
b = (0.11852 - 0.05478 × ln(PD))²

(Basel Committee on Banking Supervision, BCBS 2006, paragraphs 272-279)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.stats import norm

from fcrm.config import (
    ASSET_CORRELATION_CORPORATE,
    BASEL_RWA_SCALING_FACTOR,
    MATURITY_ADJUSTMENT_BASE,
)

logger = logging.getLogger(__name__)

# Standard credit conversion factor for undrawn revolving commitments
_CCF_REVOLVING = 0.75  # 75% — Basel III standardised approach


@dataclass
class LoanExposure:
    """
    Single loan / credit facility inputs.

    Attributes
    ----------
    facility_id : str
    drawn_balance_cr : float
        Currently drawn outstanding balance (INR crore).
    undrawn_balance_cr : float
        Undrawn committed credit line (INR crore).
    ccf : float
        Credit Conversion Factor for undrawn portion. Default = 75%.
    lgd_base : float
        Baseline Loss Given Default (collateral-adjusted).
    maturity_years : float
        Remaining contractual maturity.
    """

    facility_id: str
    drawn_balance_cr: float
    undrawn_balance_cr: float = 0.0
    ccf: float = _CCF_REVOLVING
    lgd_base: float = 0.45
    maturity_years: float = MATURITY_ADJUSTMENT_BASE


def compute_ead(loan: LoanExposure) -> float:
    """
    Compute Exposure at Default [Basel III, paragraph 311].

    EAD = Drawn + CCF × Undrawn

    EAD is treated as a static accounting input in the climate stress engine.
    Distressed borrowers may maximize drawdowns pre-default (handled in
    the Liquidity_Draw component of total institutional loss).
    """
    return loan.drawn_balance_cr + loan.ccf * loan.undrawn_balance_cr


def compute_basel_capital_requirement(
    pd: float,
    lgd: float,
    maturity_years: float,
    r_asset: float = ASSET_CORRELATION_CORPORATE,
) -> float:
    """
    Compute Basel III A-IRB capital requirement K(PD, LGD) per loan.

    Following BCBS paragraphs 272–279 (corporate exposure formula).

    K = LGD × [Φ(G(PD)/√(1-R) × √(R/(1-R)) × G(0.999)) - PD]
        × maturity adjustment / (1 - 1.5 × b)

    Where G = Φ⁻¹ and b = smoothing parameter.

    Parameters
    ----------
    pd : float
        Stressed Probability of Default ∈ (0, 1).
    lgd : float
        Stressed Loss Given Default ∈ (0, 1).
    maturity_years : float
        Effective remaining maturity.
    r_asset : float
        Corporate asset correlation coefficient.

    Returns
    -------
    float
        Capital requirement K ∈ [0, 1] (fraction of EAD).
    """
    pd_safe = np.clip(pd, 1e-6, 1.0 - 1e-6)
    lgd_safe = np.clip(lgd, 0.0, 1.0)

    # Maturity adjustment smoothing parameter b
    b = (0.11852 - 0.05478 * np.log(pd_safe)) ** 2

    # Maturity adjustment factor M_adj
    m_adj = (1.0 + (maturity_years - 2.5) * b) / (1.0 - 1.5 * b)
    m_adj = max(m_adj, 0.0)

    # Asset correlation R
    R = r_asset

    # Conditional loss under systematic factor (99.9% confidence)
    G_pd = norm.ppf(pd_safe)
    G_999 = norm.ppf(0.999)
    conditional_pd = norm.cdf(
        (G_pd / np.sqrt(1.0 - R)) + (np.sqrt(R / (1.0 - R)) * G_999)
    )

    K = lgd_safe * (conditional_pd - pd_safe) * m_adj
    return float(np.clip(K, 0.0, lgd_safe))


def compute_ecl(
    pd_stressed: float,
    lgd_stressed: float,
    loan: LoanExposure,
) -> float:
    """
    Compute Expected Credit Loss [Equation 24].

    ECL_Stressed = PD_stressed × LGD_stressed × EAD

    Returns
    -------
    float
        ECL in INR crore.
    """
    ead = compute_ead(loan)
    return pd_stressed * lgd_stressed * ead


def compute_incremental_ecl(
    pd_stressed: float,
    lgd_stressed: float,
    pd_base: float,
    lgd_base: float,
    loan: LoanExposure,
) -> tuple[float, float]:
    """
    Compute stressed and base ECL, returning the incremental ECL ΔECLᵢₙ꜀.

    ΔECLᵢₙ꜀ = ECL_Stressed - ECL_Base

    Returns
    -------
    tuple[float, float]
        (ecl_stressed_cr, delta_ecl_cr) in INR crore.
    """
    ecl_stressed = compute_ecl(pd_stressed, lgd_stressed, loan)
    ecl_base = compute_ecl(pd_base, lgd_base, loan)
    delta_ecl = max(ecl_stressed - ecl_base, 0.0)  # only deterioration counts
    return ecl_stressed, delta_ecl


def compute_rwa_contribution(
    pd_stressed: float,
    lgd_stressed: float,
    loan: LoanExposure,
) -> float:
    """
    Compute the stressed Risk-Weighted Asset contribution for a loan.

    RWA = K(PD_stressed, LGD_stressed) × 12.5 × EAD      (Equation 26 numerator)

    Returns
    -------
    float
        RWA in INR crore.
    """
    K = compute_basel_capital_requirement(pd_stressed, lgd_stressed, loan.maturity_years)
    ead = compute_ead(loan)
    return K * BASEL_RWA_SCALING_FACTOR * ead
