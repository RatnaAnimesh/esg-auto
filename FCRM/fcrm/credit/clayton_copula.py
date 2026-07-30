"""
fcrm.credit.clayton_copula
--------------------------
Asymmetric Clayton Copula for Wrong Way Risk (WWR) — Section 3.4 of the spec.

The Clayton Copula exhibits lower-tail dependence and zero upper-tail dependence,
mirroring the asymmetric physical reality of climate stress:

    C_Clayton(u, v) = max(u^{-θ} + v^{-θ} - 1, 0)^{-1/θ}    [Equation 21]

Where:
    u = PD_stressed (normalized to [0, 1])
    v = P_Damage   = probability of physical collateral damage
    θ > 0          = tail dependence parameter (higher = stronger lower-tail correlation)

The WWR Multiplier isolates the tail dependence by normalizing the copula
output against independent probability [Equation 22]:

    WWR_Multiplier = C_Clayton(PD_stressed, P_Damage)
                     ────────────────────────────────
                     PD_stressed × P_Damage

Applied to compute stressed LGD [Equation 23]:

    LGD_stressed = min(1.0, LGD_base × WWR_Multiplier) × (1 - Insurance_Cover_t)

The insurance cover decays to zero once the Climate Risk Score surpasses
the empirical uninsurability threshold (fcrm.config.EngineConfig).

References:
    Clayton, D.G. (1978) — A model for association in bivariate life tables
    Embrechts, McNeil & Straumann (2002) — Correlation and dependence in RM
"""

from __future__ import annotations

import logging

import numpy as np

from fcrm.config import EngineConfig, CLAYTON_THETA_DEFAULT

logger = logging.getLogger(__name__)


def clayton_copula(
    u: float | np.ndarray,
    v: float | np.ndarray,
    theta: float = CLAYTON_THETA_DEFAULT,
) -> float | np.ndarray:
    """
    Evaluate the bivariate Clayton Copula [Equation 21].

    C_Clayton(u, v; θ) = max(u^{-θ} + v^{-θ} - 1, 0)^{-1/θ}

    Parameters
    ----------
    u : float or np.ndarray
        First uniform marginal ∈ (0, 1). Typically PD_stressed.
    v : float or np.ndarray
        Second uniform marginal ∈ (0, 1). Typically P_Damage.
    theta : float
        Clayton tail dependence parameter. Must be > 0.
        θ → 0: independence; θ → ∞: perfect positive lower-tail dependence.

    Returns
    -------
    float or np.ndarray
        Joint probability ∈ [0, 1] under Clayton dependence structure.
    """
    u_arr = np.asarray(u, dtype=float)
    v_arr = np.asarray(v, dtype=float)

    # Clip inputs to avoid numerical issues at 0 and 1
    u_arr = np.clip(u_arr, 1e-8, 1.0 - 1e-8)
    v_arr = np.clip(v_arr, 1e-8, 1.0 - 1e-8)

    # Equation 21: C = max(u^{-θ} + v^{-θ} - 1, 0)^{-1/θ}
    inner = u_arr ** (-theta) + v_arr ** (-theta) - 1.0
    inner_clipped = np.maximum(inner, 0.0)
    result = inner_clipped ** (-1.0 / theta)

    return float(result) if np.ndim(u) == 0 else result


def compute_wwr_multiplier(
    pd_stressed: float,
    p_damage: float,
    theta: float = CLAYTON_THETA_DEFAULT,
) -> float:
    """
    Compute the Wrong Way Risk multiplier [Equation 22].

    WWR_Multiplier = C_Clayton(PD_stressed, P_Damage; θ)
                     ─────────────────────────────────────
                     PD_stressed × P_Damage

    This ratio is > 1 when PD and collateral damage are positively correlated
    (lower-tail co-dependence). It equals exactly 1.0 under independence
    (Gaussian or Student-t copula in the symmetric regime).

    Parameters
    ----------
    pd_stressed : float
        Stressed Probability of Default ∈ (0, 1).
    p_damage : float
        Physical damage probability ∈ (0, 1). Derived from climate hazard
        exposure scores (flood depth exceedance, heat wave frequency, etc.).
    theta : float
        Clayton copula tail dependence parameter.

    Returns
    -------
    float
        WWR Multiplier ≥ 1.0 (bounded below by 1.0 under independence).
    """
    joint_prob = float(clayton_copula(pd_stressed, p_damage, theta))
    independent_prob = pd_stressed * p_damage

    if independent_prob < 1e-10:
        return 1.0

    multiplier = joint_prob / independent_prob
    logger.debug(
        "WWR Multiplier: joint=%.6f, independent=%.6f → multiplier=%.4f.",
        joint_prob, independent_prob, multiplier,
    )
    return float(np.clip(multiplier, 1.0, 10.0))  # cap at 10× for stability


def compute_insurance_cover(
    climate_risk_score: float,
    config: EngineConfig = EngineConfig(),
) -> float:
    """
    Compute the dynamic insurance coverage fraction.

    Once the Climate Risk Score surpasses the uninsurability threshold,
    insurance coverage decays linearly to 0 (total uninsurability).

    Below the threshold: coverage maintained at its initial level (assumed 1.0).
    Above the threshold: linear decay to 0.

    Parameters
    ----------
    climate_risk_score : float
        Composite climate hazard score ∈ [0, 1] (e.g., NSRAL Physical Risk Score).
    config : EngineConfig
        Engine config with insurance_stress_threshold.

    Returns
    -------
    float
        Insurance coverage fraction ∈ [0, 1].
    """
    threshold = config.insurance_stress_threshold
    if climate_risk_score <= threshold:
        return 1.0
    # Linear decay from threshold to complete uninsurability at score=1.0
    coverage = 1.0 - (climate_risk_score - threshold) / (1.0 - threshold)
    return float(max(coverage, 0.0))


def compute_stressed_lgd(
    lgd_base: float,
    pd_stressed: float,
    p_damage: float,
    climate_risk_score: float,
    theta: float = CLAYTON_THETA_DEFAULT,
    config: EngineConfig = EngineConfig(),
) -> float:
    """
    Compute the stressed LGD incorporating WWR and dynamic insurance [Equation 23].

    LGD_stressed = min(1.0, LGD_base × WWR_Multiplier) × (1 - Insurance_Cover_t)

    Parameters
    ----------
    lgd_base : float
        Baseline Loss Given Default ∈ [0, 1].
    pd_stressed : float
        Stressed PD from the Merton engine.
    p_damage : float
        Physical damage probability.
    climate_risk_score : float
        Composite hazard score driving insurance decay.
    theta : float
        Clayton copula parameter.
    config : EngineConfig

    Returns
    -------
    float
        Stressed LGD ∈ [0, 1].
    """
    wwr_mult = compute_wwr_multiplier(pd_stressed, p_damage, theta)
    insurance_cover = compute_insurance_cover(climate_risk_score, config)

    lgd_physical = min(1.0, lgd_base * wwr_mult)
    lgd_stressed = lgd_physical * (1.0 - insurance_cover)

    # However, the standard banking interpretation is that insurance reduces LGD.
    # If insurance cover = 1.0 (fully insured), LGD_final = 0.
    # If insurance cover = 0.0 (uninsurable), LGD_final = lgd_physical.
    # The spec formula: LGD_stressed = min(1.0, LGD_base × WWR) × (1 - Insurance_Cover)
    # This means: if fully insured, LGD → 0. This matches the spec exactly.

    logger.debug(
        "LGD: base=%.4f, WWR_mult=%.4f, insurance=%.4f → stressed=%.4f.",
        lgd_base, wwr_mult, insurance_cover, lgd_stressed,
    )
    return float(np.clip(lgd_stressed, 0.0, 1.0))
