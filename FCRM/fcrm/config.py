"""
fcrm.config
-----------
Central configuration: NGFS Phase 4 scenario parameters, engine constants,
and NIC classification mappings used across all modules.

Source: NGFS Phase 4 (2023), IPCC AR6, MoSPI industry classifications.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List


class NGFSScenario(str, enum.Enum):
    """
    NGFS Phase 4 canonical scenario identifiers.

    Net Zero 2050     – Orderly transition; coordinated policy; 1.5°C by 2100.
    Below 2C          – Orderly; 2°C limit; moderate policy stringency.
    Delayed Transition – Disorderly; policy delay to 2030 then abrupt escalation.
    Divergent Net Zero – Disorderly; fragmented policies; higher transition costs.
    NDCs              – Current nationally determined contributions only.
    Current Policies  – Hot House World; no new climate policies; ~3°C by 2100.
    """

    NET_ZERO_2050 = "Net Zero 2050"
    BELOW_2C = "Below 2°C"
    DELAYED_TRANSITION = "Delayed Transition"
    DIVERGENT_NET_ZERO = "Divergent Net Zero"
    NDCS = "Nationally Determined Contributions"
    CURRENT_POLICIES = "Current Policies"


# NGFS Phase 4 illustrative shadow carbon price trajectories (USD / tCO2e).
# Source: NGFS Scenario Explorer Phase 4, REMIND-MAgPIE model, global average.
# These are approximate headline values; the loader fetches full time-series.
NGFS_CARBON_PRICE_USD: Dict[NGFSScenario, Dict[int, float]] = {
    NGFSScenario.NET_ZERO_2050: {
        2025: 25.0, 2030: 80.0, 2035: 175.0, 2040: 320.0, 2045: 530.0, 2050: 800.0,
    },
    NGFSScenario.BELOW_2C: {
        2025: 20.0, 2030: 60.0, 2035: 130.0, 2040: 240.0, 2045: 380.0, 2050: 550.0,
    },
    NGFSScenario.DELAYED_TRANSITION: {
        2025: 5.0, 2030: 15.0, 2035: 200.0, 2040: 400.0, 2045: 600.0, 2050: 850.0,
    },
    NGFSScenario.DIVERGENT_NET_ZERO: {
        2025: 30.0, 2030: 100.0, 2035: 220.0, 2040: 380.0, 2045: 580.0, 2050: 820.0,
    },
    NGFSScenario.NDCS: {
        2025: 5.0, 2030: 10.0, 2035: 18.0, 2040: 28.0, 2045: 40.0, 2050: 55.0,
    },
    NGFSScenario.CURRENT_POLICIES: {
        2025: 0.0, 2030: 0.0, 2035: 0.0, 2040: 0.0, 2045: 0.0, 2050: 0.0,
    },
}

# Conversion: INR per USD (approximate 2025 mid-rate; override at runtime).
INR_PER_USD: float = 83.5


@dataclass(frozen=True)
class EngineConfig:
    """
    Immutable runtime configuration for the FCRM engine.

    Parameters
    ----------
    scenario : NGFSScenario
        The NGFS Phase 4 pathway to execute.
    base_year : int
        Calibration anchor year.
    horizon_years : List[int]
        Projection years to evaluate (inclusive).
    risk_free_rate : float
        Annualised risk-free rate for Merton inversion.
    merton_convergence_tol : float
        Residual tolerance for the Powell root-finding algorithm (< 10^-7 per spec).
    cet1_regulatory_minimum : float
        Basel III CET1 minimum ratio (8 % = 0.08).
    insurance_stress_threshold : float
        Climate Risk Score above which insurance cover begins to decay.
    """

    scenario: NGFSScenario = NGFSScenario.NET_ZERO_2050
    base_year: int = 2024
    horizon_years: List[int] = field(
        default_factory=lambda: list(range(2025, 2051))
    )
    risk_free_rate: float = 0.065          # 6.5% — approximate Indian G-Sec rate
    merton_convergence_tol: float = 1e-8   # stricter than the 1e-7 spec minimum
    cet1_regulatory_minimum: float = 0.08  # 8 % Basel III hard floor
    insurance_stress_threshold: float = 0.65


# NIC 2-digit sector classification into PRIMARY / SECONDARY / TERTIARY.
# Used by the Offline Calibration Bootstrapper to assign polynomial degree priors.
NIC_SECTOR_CLASS: Dict[int, str] = {
    # PRIMARY — Agriculture, Mining (concave, violent non-linear damage functions)
    **{k: "PRIMARY" for k in range(1, 10)},
    # SECONDARY — Manufacturing, Construction, Utilities (linear heat penalties)
    **{k: "SECONDARY" for k in list(range(10, 40)) + [41, 42, 43, 35, 36, 37, 38, 39]},
    # TERTIARY — Services, IT, Finance (zero expected elasticity)
    **{k: "TERTIARY" for k in range(45, 100)},
}

# Basel III regulatory constants
BASEL_MIN_CAPITAL_RATIO: float = 0.08           # 8 %
BASEL_RWA_SCALING_FACTOR: float = 12.5          # = 1 / 0.08
ASSET_CORRELATION_CORPORATE: float = 0.12       # R^2 per BCBS corporate formula
MATURITY_ADJUSTMENT_BASE: float = 2.5           # years

# Default Clayton copula theta (tail dependence parameter)
CLAYTON_THETA_DEFAULT: float = 2.0

# PCAF Data Quality Score thresholds for confidence interval width scaling
PCAF_CONFIDENCE_WIDTHS: Dict[int, float] = {
    1: 0.05,  # Tier 1 — verified Scope 1/2/3 BRSR (±5 % CI)
    2: 0.10,  # Tier 2 — audited physical production volumes
    3: 0.20,  # Tier 3 — physical intensity factors
    4: 0.30,  # Tier 4 — economic revenue proxies
    5: 0.50,  # Tier 5 — NIC-PCAF sectoral intensity only
}
