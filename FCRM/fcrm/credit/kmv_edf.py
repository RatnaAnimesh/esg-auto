"""
fcrm.credit.kmv_edf
--------------------
Empirically-Mapped KMV Default Transformation — Section 3.1 of the NSRAL spec.

Constructs a continuous 3D probability manifold mapping Distance-to-Default
(DD) and NGFS Climate Severity to Expected Default Frequency (EDF):

Step 1 – Historical Equity Extraction & Inversion:
    Streams 10 years of NSE equity data via yfinance and computes the empirical
    DD distribution for the Indian corporate universe.

Step 2 – Market Moment Extraction:
    Extracts empirical mean μ_DD and standard deviation σ_DD from the
    live Indian corporate solvency distribution.

Step 3 – Logistic EDF Calibration:
    Constructs an empirical EDF mapping via a Logistic CDF. The decay factor k
    is mathematically calibrated to be inversely proportional to σ_DD:
        k = 1.0 / (0.5 × σ_DD)

Step 4 – Systemic Contagion & Tail Thickening:
    Shifts DD coordinates downwards under climate stress and injects a
    probability "tail thickener" for firms near the default barrier.

The resulting geometric surface is the 3D topological manifold referenced in
Figure 1 of the NSRAL report.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import numpy as np
from scipy.special import expit  # logistic sigmoid

from fcrm.data.equity_loader import get_market_dd_moments

logger = logging.getLogger(__name__)

# Climate Severity axis: 0.0 = no additional stress, 1.0 = maximum NGFS shock
_SEVERITY_GRID = np.linspace(0.0, 1.0, 20)
# DD axis: range from deeply distressed to highly solvent
_DD_GRID = np.linspace(-2.0, 10.0, 200)

# Tail thickener injection threshold (below this DD, extra probability mass is added)
_TAIL_THICKENER_DD_THRESHOLD = 1.5
_TAIL_THICKENER_STRENGTH = 0.08  # maximum additional PD injected at DD=0


@lru_cache(maxsize=1)
def get_logistic_decay_factor() -> float:
    """
    Calibrate the logistic EDF decay factor k = 1.0 / (0.5 × σ_DD).

    Spec Section 3.1 Step 3: "the decay factor (k) is mathematically calibrated
    to be inversely proportional to the empirical market volatility."

    Returns
    -------
    float
        k — the logistic curve decay factor.
    """
    moments = get_market_dd_moments()
    sigma_dd = moments["sigma_dd"]
    k = 1.0 / (0.5 * sigma_dd)
    logger.info("Logistic EDF decay factor k=%.4f (σ_DD=%.4f).", k, sigma_dd)
    return k


def logistic_edf(
    dd: float | np.ndarray,
    k: Optional[float] = None,
    mu_dd: Optional[float] = None,
) -> float | np.ndarray:
    """
    Compute Expected Default Frequency using the empirically calibrated
    Logistic CDF, anchored to Indian corporate market moments.

    PD = σ(−k × (DD − μ_DD))

    where σ is the logistic sigmoid function.

    Parameters
    ----------
    dd : float or np.ndarray
        Distance-to-Default value(s).
    k : float, optional
        Decay factor. If None, fetched from calibrated market moments.
    mu_dd : float, optional
        Centre of the logistic curve (empirical mean DD). If None, from market.

    Returns
    -------
    float or np.ndarray
        Probability of Default ∈ (0, 1).
    """
    if k is None:
        k = get_logistic_decay_factor()
    if mu_dd is None:
        moments = get_market_dd_moments()
        mu_dd = moments["mu_dd"]

    # Logistic CDF: Φ_logistic(-k × (DD - μ_DD))
    # When DD = μ_DD, PD = 0.5 (firms at the empirical mean have 50% default probability)
    # When DD >> μ_DD, PD → 0 (highly solvent)
    # When DD << μ_DD, PD → 1.0 (deeply distressed)
    return expit(-k * (np.asarray(dd, dtype=float) - mu_dd))


def inject_tail_thickener(
    pd_raw: float | np.ndarray,
    dd: float | np.ndarray,
) -> float | np.ndarray:
    """
    Apply the probability "tail thickener" for firms near the default barrier.

    Spec Section 3.1 Step 4: "an explicit probability tail thickener is injected
    for firms near the default barrier to simulate sudden liquidity freezing."

    The thickener increases PD additively for firms with DD < threshold,
    peaking at DD=0 (exactly at the default barrier).

    Parameters
    ----------
    pd_raw : float or np.ndarray
        Raw logistic PD.
    dd : float or np.ndarray
        Distance-to-Default.

    Returns
    -------
    float or np.ndarray
        Thickened PD, still clipped to [0, 1].
    """
    dd_arr = np.asarray(dd, dtype=float)
    pd_arr = np.asarray(pd_raw, dtype=float)

    # Thickener: decays linearly from max at DD=0 to 0 at DD=threshold
    thickener = np.where(
        dd_arr < _TAIL_THICKENER_DD_THRESHOLD,
        _TAIL_THICKENER_STRENGTH * (1.0 - dd_arr / _TAIL_THICKENER_DD_THRESHOLD),
        0.0,
    )
    thickener = np.maximum(thickener, 0.0)
    return np.clip(pd_arr + thickener, 0.0, 1.0)


from fcrm.credit.empirical_edf import compute_empirical_edf_from_model

def compute_empirical_edf(
    dd: float | np.ndarray,
    climate_severity: float = 0.0,
    k: Optional[float] = None,
    mu_dd: Optional[float] = None,
) -> float | np.ndarray:
    """
    Compute the full empirical EDF from DD and climate severity.

    This is the core function used by the stress injection module (Section 3.3)
    and represents the topological manifold surface in Figure 1.

    It dynamically maps Distance-to-Default (DD) and Climate Severity using the 
    Logistic Regression classifier trained on historical observations.
    The tail thickener is applied for near-default firms to capture sudden liquidity freezing.

    Parameters
    ----------
    dd : float or np.ndarray
        Distance-to-Default (pre-stress or stressed).
    climate_severity : float
        NGFS severity score [0.0 = baseline, 1.0 = maximum stress].
    k : float, optional
        Ignored (maintained for backward compatibility with tests).
    mu_dd : float, optional
        Ignored (maintained for backward compatibility with tests).

    Returns
    -------
    float or np.ndarray
        EDF_empirical(DD, severity) ∈ [0, 1].
    """
    dd_effective = np.asarray(dd, dtype=float)

    # Use the empirical Logistic Regression classifier
    pd_raw = compute_empirical_edf_from_model(dd_effective, climate_severity)
    
    # Inject probability tail thickener for firms near default boundary
    pd_with_tail = inject_tail_thickener(pd_raw, dd_effective)
    
    if np.isscalar(dd) or np.ndim(dd) == 0:
        return float(pd_with_tail)
    return pd_with_tail


def build_3d_probability_manifold() -> np.ndarray:
    """
    Build the full 3D probability tensor over (DD grid × Severity grid).

    This is the geometric surface depicted in Figure 1 of the spec:
    P[i, j] = EDF(DD_GRID[i], SEVERITY_GRID[j])

    Returns
    -------
    np.ndarray
        Shape (len(_DD_GRID), len(_SEVERITY_GRID)).
    """
    logger.info("Building 3D probability manifold (%d DD × %d severity points).",
                len(_DD_GRID), len(_SEVERITY_GRID))

    manifold = np.zeros((len(_DD_GRID), len(_SEVERITY_GRID)))
    for j, severity in enumerate(_SEVERITY_GRID):
        manifold[:, j] = compute_empirical_edf(_DD_GRID, climate_severity=severity)

    logger.info(
        "Manifold built. PD at (DD=0, severity=0)=%.3f; PD at (DD=5, severity=1)=%.4f.",
        compute_empirical_edf(0.0, 0.0),
        compute_empirical_edf(5.0, 1.0),
    )
    return manifold
