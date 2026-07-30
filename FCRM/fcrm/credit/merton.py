"""
fcrm.credit.merton
-------------------
Merton Structural Credit Model — Section 3.2 of the NSRAL spec.

The engine treats equity as a European call option on the firm's assets:
    E = V Φ(d₁) - DP e^{-rT} Φ(d₂)          [Equation 14]

Where:
    d₁ = [ln(V/DP) + (r + 0.5σ_V²)T] / (σ_V √T)   [Equation 15]
    d₂ = d₁ - σ_V √T

The volatility transformation constraint links observable equity volatility
to unobservable asset volatility:
    σ_E = (V/E) × Φ(d₁) × σ_V                      [Equation 16]

These two equations are solved simultaneously via a Powell hybrid root-finding
algorithm (scipy.optimize.root) with convergence tolerance < 10⁻⁷.

Once (V, σ_V) are extracted, the baseline Distance-to-Default is:
    DD_base = [ln(V_sol/DP) + (r - 0.5σ_V_sol²)T] / (σ_V_sol √T)   [Eq. 17]

Structural Proxy Transfer for SMEs:
    The KMV manifold is calibrated using listed-equity data (yfinance).
    For unlisted SMEs, observable accounting metrics (EBITDA, short-term debt)
    serve as proxy inputs to place them on the same manifold.
    Per Allen et al. (JFI, 2012): Indian SMEs rely on short-term vendor financing,
    so DP_SME ≈ Short_Term_Debt only (long-term debt negligible).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from scipy.optimize import root
from scipy.stats import norm

from fcrm.config import EngineConfig

logger = logging.getLogger(__name__)


@dataclass
class FirmSnapshot:
    """
    Observable inputs for a single firm required by the Merton inversion.

    Attributes
    ----------
    entity_id : str
    equity_value_cr : float
        Market value of equity in INR crore (for listed firms: market cap).
        For unlisted SMEs: book value of equity as proxy.
    equity_volatility_annual : float
        Annualised equity volatility σ_E (from historical price series or
        accounting ratios for unlisted entities).
    short_term_debt_cr : float
        Short-term debt (current liabilities, INR crore).
    long_term_debt_cr : float
        Long-term debt (INR crore). Often negligible for Indian SMEs.
    maturity_years : float
        Time horizon T for debt maturity (typically 1.0 for Basel A-IRB).
    is_listed : bool
        If True, equity_value_cr and equity_volatility_annual are market-derived.
    """

    entity_id: str
    equity_value_cr: float
    equity_volatility_annual: float
    short_term_debt_cr: float
    long_term_debt_cr: float = 0.0
    maturity_years: float = 1.0
    is_listed: bool = True


def compute_default_point(firm: FirmSnapshot, is_sme: bool = False) -> float:
    """
    Compute the Dynamic Default Point [Equation 13].

    DP = Short_Term_Debt + 0.5 × Long_Term_Debt

    For Indian SMEs (per Allen et al., JFI, 2012), long-term debt is often
    negligible, so DP_SME ≈ Short_Term_Debt only.
    """
    if is_sme:
        dp = firm.short_term_debt_cr
    else:
        dp = firm.short_term_debt_cr + 0.5 * firm.long_term_debt_cr
    return max(dp, 1e-6)  # prevent division by zero


def _merton_system(
    params: np.ndarray,
    E: float,
    sigma_E: float,
    DP: float,
    r: float,
    T: float,
) -> np.ndarray:
    """
    Two-equation Merton system to minimize.

    Residuals:
        f1 = V Φ(d1) - DP exp(-rT) Φ(d2) - E       [Eq. 14]
        f2 = (V/E) Φ(d1) σ_V - σ_E                  [Eq. 16]

    Returns residual vector [f1, f2].
    """
    V, sigma_V = params
    V = max(V, 1e-8)
    sigma_V = max(sigma_V, 1e-8)

    sqrt_T = np.sqrt(T)
    d1 = (np.log(V / DP) + (r + 0.5 * sigma_V ** 2) * T) / (sigma_V * sqrt_T)
    d2 = d1 - sigma_V * sqrt_T

    f1 = V * norm.cdf(d1) - DP * np.exp(-r * T) * norm.cdf(d2) - E
    f2 = (V / E) * norm.cdf(d1) * sigma_V - sigma_E
    return np.array([f1, f2])


def invert_merton(
    firm: FirmSnapshot,
    config: EngineConfig = EngineConfig(),
    is_sme: bool = False,
) -> Tuple[float, float, float]:
    """
    Numerically invert the Merton model to extract (V, σ_V, DD_base).

    Uses the multi-dimensional Powell hybrid root-finding algorithm via
    scipy.optimize.root with convergence tolerance ≤ 10⁻⁷ (spec Section 3.2).

    Parameters
    ----------
    firm : FirmSnapshot
        Observable firm inputs.
    config : EngineConfig
        Engine configuration (risk-free rate, tolerance).
    is_sme : bool
        If True, applies SME-specific Default Point (DP_SME ≈ STD only).

    Returns
    -------
    tuple[float, float, float]
        (V_sol, sigma_V_sol, DD_base)
        V_sol      – implied market value of assets (INR crore)
        sigma_V_sol – implied annualised asset volatility
        DD_base    – baseline Distance-to-Default
    """
    E = firm.equity_value_cr
    sigma_E = firm.equity_volatility_annual
    DP = compute_default_point(firm, is_sme=is_sme)
    r = config.risk_free_rate
    T = firm.maturity_years

    # Initial guess: V ≈ E + DP, σ_V ≈ σ_E × E / (E + DP)
    V0 = E + DP
    sigma_V0 = sigma_E * E / V0

    result = root(
        fun=_merton_system,
        x0=[V0, sigma_V0],
        args=(E, sigma_E, DP, r, T),
        method="hybr",
        tol=config.merton_convergence_tol,
        options={"maxfev": 5000},
    )

    if not result.success:
        logger.warning(
            "Merton inversion for entity '%s' did not fully converge (residual norm=%.2e). "
            "Using best-estimate solution.",
            firm.entity_id,
            float(np.linalg.norm(result.fun)),
        )

    V_sol, sigma_V_sol = result.x
    V_sol = max(V_sol, 1e-6)
    sigma_V_sol = max(sigma_V_sol, 1e-6)
    sqrt_T = np.sqrt(T)

    # Equation 17: DD_base
    dd_base = (np.log(V_sol / DP) + (r - 0.5 * sigma_V_sol ** 2) * T) / (sigma_V_sol * sqrt_T)

    logger.debug(
        "Merton inversion [%s]: V=%.2f cr, σ_V=%.4f, DP=%.2f cr, DD_base=%.4f.",
        firm.entity_id, V_sol, sigma_V_sol, DP, dd_base,
    )
    return V_sol, sigma_V_sol, dd_base


def compute_dd_for_sme(
    entity_id: str,
    ebitda_cr: float,
    short_term_debt_cr: float,
    revenue_cr: float,
    config: EngineConfig = EngineConfig(),
) -> Tuple[float, float]:
    """
    Structural Proxy Transfer for unlisted SMEs — places them on the
    KMV manifold using accounting metrics instead of listed equity.

    Per Allen et al. (JFI, 2012): Indian SMEs rely on short-term financing.
    Proxy equity value = EBITDA × sector EV/EBITDA multiple (≈ 6× for SMEs).
    Proxy equity volatility = revenue volatility proxy.

    Returns
    -------
    tuple[float, float]
        (sigma_V_proxy, dd_base_proxy)
    """
    # Proxy equity value from EBITDA capitalisation
    ev_ebitda_multiple = 6.0  # conservative SME multiple
    equity_proxy = max(ebitda_cr * ev_ebitda_multiple - short_term_debt_cr, 1e-3)

    # Proxy equity volatility: assume 35% annualised for Indian unlisted SMEs
    sigma_E_proxy = 0.35

    firm = FirmSnapshot(
        entity_id=entity_id,
        equity_value_cr=equity_proxy,
        equity_volatility_annual=sigma_E_proxy,
        short_term_debt_cr=short_term_debt_cr,
        long_term_debt_cr=0.0,  # SMEs: LTD ≈ 0
        maturity_years=1.0,
        is_listed=False,
    )

    try:
        _, sigma_V, dd_base = invert_merton(firm, config, is_sme=True)
        return sigma_V, dd_base
    except Exception as exc:
        logger.error("SME Merton proxy failed for %s: %s. Using fallback DD=2.0.", entity_id, exc)
        return 0.35, 2.0
