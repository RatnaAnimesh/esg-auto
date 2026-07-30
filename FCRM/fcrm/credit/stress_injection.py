"""
fcrm.credit.stress_injection
-----------------------------
Systemic Climate Stress Injection — Section 3.3 of the NSRAL spec.

Injects CEaR and TCaR satellite outputs into the Merton structural model
to compute the stressed Distance-to-Default and Probability of Default.

Mathematical specification:

    Macro_Drift_Penalty = 0.5 × |ε_NIC,t × ΔGDPₜ|              [Equation 18]

    DD_stressed = (DD_base - Macro_Drift_Penalty - CEaR_Drift_Penalty)
                  ─────────────────────────────────────────────────────  [Eq. 19]
                         (1 + TCaR_Volatility_Penalty)

    PD_stressed = EDF_Empirical(DD_stressed)                      [Equation 20]

The 0.5 scalar in Equation 18 is an empirical dampening factor transforming
the absolute GDP collapse into a standardised Z-score drift penalty, calibrated
against historical emerging market default dynamics.

CEaR Drift Penalty:
    The CEaR ratio directly penalises asset drift (it represents permanent
    cash flow compression rather than a volatility shock).

TCaR Volatility Penalty:
    TCaR scales the denominator (asset volatility), amplifying uncertainty
    for firms with unmitigated transition liabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from fcrm.credit.kmv_edf import compute_empirical_edf

logger = logging.getLogger(__name__)


@dataclass
class StressInputs:
    """
    All stress inputs required to compute DD_stressed and PD_stressed.

    Attributes
    ----------
    entity_id : str
    dd_base : float
        Baseline Distance-to-Default from Merton inversion.
    epsilon_nic_t : float
        Dynamic Transition Vulnerability Factor for the firm's NIC sector at year t.
    delta_gdp_t : float
        GDP growth rate at year t (negative = contraction). E.g., -0.03 = -3%.
    cear_ratio_t : float
        CEaR ratio ∈ [0, 1] from the satellite model.
    tcar_t : float
        TCaR ratio from the satellite model.
    climate_severity : float
        NGFS severity score [0.0, 1.0] for manifold positioning.
    """

    entity_id: str
    dd_base: float
    epsilon_nic_t: float
    delta_gdp_t: float
    cear_ratio_t: float
    tcar_t: float
    climate_severity: float = 0.5


def compute_macro_drift_penalty(
    epsilon_nic_t: float,
    delta_gdp_t: float,
) -> float:
    """
    Compute the macroeconomic drift penalty [Equation 18].

    Macro_Drift_Penalty = 0.5 × |ε_NIC,t × ΔGDPₜ|

    The 0.5 scalar is the empirical dampening factor calibrated to
    historical Indian corporate default cycles (CRISIL/ICRA data).

    Parameters
    ----------
    epsilon_nic_t : float
        DTVF for the firm's NIC sector (captures combined Scope 1+3 exposure).
    delta_gdp_t : float
        GDP growth (negative for contraction; e.g., -0.03 for -3% GDP shock).

    Returns
    -------
    float
        Macro drift penalty (positive = reduces DD).
    """
    return 0.5 * abs(epsilon_nic_t * delta_gdp_t)


def compute_stressed_dd(
    inputs: StressInputs,
) -> float:
    """
    Compute the stressed Distance-to-Default [Equation 19].

    DD_stressed = (DD_base - Macro_Drift_Penalty - CEaR_Drift_Penalty)
                  ────────────────────────────────────────────────────
                               (1 + TCaR_Volatility_Penalty)

    The CEaR ratio acts as a direct drift penalty (permanent EBITDA compression).
    The TCaR ratio acts as a volatility penalty (transition uncertainty inflates σ).

    Returns
    -------
    float
        Stressed Distance-to-Default (may be negative for severely distressed firms).
    """
    macro_drift = compute_macro_drift_penalty(inputs.epsilon_nic_t, inputs.delta_gdp_t)
    cear_drift = inputs.cear_ratio_t * abs(inputs.dd_base)  # CEaR acts as a structural wipeout on DD

    dd_numerator = inputs.dd_base - macro_drift - cear_drift
    dd_denominator = 1.0 + inputs.tcar_t  # TCaR inflates volatility denominator

    dd_stressed = dd_numerator / dd_denominator
    logger.debug(
        "Stress injection [%s]: DD_base=%.4f → DD_stressed=%.4f "
        "(macro_drift=%.4f, cear_drift=%.4f, tcar=%.4f).",
        inputs.entity_id, inputs.dd_base, dd_stressed,
        macro_drift, cear_drift, inputs.tcar_t,
    )
    return float(dd_stressed)


def compute_stressed_pd(
    inputs: StressInputs,
) -> tuple[float, float]:
    """
    Compute the stressed PD by evaluating DD_stressed on the empirical EDF
    manifold [Equation 20].

    PD_stressed = EDF_Empirical(DD_stressed)

    Returns
    -------
    tuple[float, float]
        (dd_stressed, pd_stressed)
    """
    dd_stressed = compute_stressed_dd(inputs)
    pd_stressed = float(compute_empirical_edf(dd_stressed, inputs.climate_severity))
    logger.debug(
        "Stressed PD [%s]: DD_stressed=%.4f → PD_stressed=%.5f.",
        inputs.entity_id, dd_stressed, pd_stressed,
    )
    return dd_stressed, pd_stressed


def compute_ngfs_severity_score(
    scenario_name: str,
) -> float:
    """
    Map NGFS scenario name to a continuous severity score [0, 1].

    Used to position the firm on the correct slice of the 3D manifold.

    Returns
    -------
    float
        Severity in [0, 1]. 0 = Net Zero 2050 (lowest), 1 = Current Policies.
    """
    severity_map = {
        "Net Zero 2050": 0.10,
        "Below 2°C": 0.20,
        "Delayed Transition": 0.55,
        "Divergent Net Zero": 0.45,
        "Nationally Determined Contributions": 0.65,
        "Current Policies": 0.90,
    }
    return severity_map.get(scenario_name, 0.50)
