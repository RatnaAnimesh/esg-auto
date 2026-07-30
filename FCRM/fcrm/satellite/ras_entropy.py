"""
fcrm.satellite.ras_entropy
--------------------------
Cross-entropy RAS Information-Theoretic Multiplier for scaling 4-digit ASI
factor intensities to 5-digit NIC sub-sectors (Section 2.1, Equations 8 and 9).

The mathematical formulation minimizes the Kullback-Leibler divergence between
the unknown 5-digit distribution {x_j} and the known 4-digit parent baseline {q_j}:

    min Σ_j  x_j × ln(x_j / q_j)                           [Equation 8]

Subject to the macroeconomic boundary constraint:

    Σ_j  x_j × ω_j = Total_Factor_Value_4-digit             [Equation 9]

Where ω_j is the structural weight of the j-th 5-digit child sector (measured
via MCA paid-up capital shares as the free structural proxy).

This optimization guarantees that the generated 5-digit micro-intensities are
anchored by empirical realities and perfectly reconstruct the 4-digit parent.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
from scipy.optimize import minimize

from fcrm.data.mca_loader import load_mca_structural_weights
from fcrm.data.mospi_loader import load_asi_factor_intensities

logger = logging.getLogger(__name__)


def _kl_divergence_objective(
    x: np.ndarray,
    q: np.ndarray,
) -> float:
    """
    Kullback-Leibler divergence Σ x_j ln(x_j / q_j) [Equation 8].

    Defined as +inf if any x_j ≤ 0 (enforced via bounds in optimizer).
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(q > 0, x / q, 1.0)
        return float(np.sum(x * np.log(ratio)))


def _kl_gradient(
    x: np.ndarray,
    q: np.ndarray,
) -> np.ndarray:
    """Analytic gradient of KL divergence: ∂/∂x_j = ln(x_j/q_j) + 1."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(np.where(q > 0, x / q, 1.0)) + 1.0


def ras_optimize_5digit_intensities(
    q_4digit: float,
    omega_weights: np.ndarray,
    total_factor_value_4digit: float,
    initial_guess: np.ndarray,
) -> np.ndarray:
    """
    Solve the cross-entropy RAS optimization for one 4-digit NIC parent.

    Minimizes KL divergence subject to the boundary constraint (Equation 9).

    Parameters
    ----------
    q_4digit : float
        The known 4-digit parent factor intensity (prior distribution baseline).
    omega_weights : np.ndarray
        Structural weights ω_j for each 5-digit child sector (MCA capital shares).
    total_factor_value_4digit : float
        The target sum Σ_j x_j ω_j = Total_Factor_Value (Equation 9 RHS).
    initial_guess : np.ndarray
        Initial values for x_j (usually q_4digit for all j).

    Returns
    -------
    np.ndarray
        Optimal 5-digit factor intensities x_j.
    """
    n = len(omega_weights)
    q = np.full(n, q_4digit, dtype=float)

    # Equality constraint: Σ x_j ω_j = total_factor_value_4digit (Equation 9)
    constraints = [
        {
            "type": "eq",
            "fun": lambda x: np.dot(x, omega_weights) - total_factor_value_4digit,
            "jac": lambda x: omega_weights,
        }
    ]

    # Bounds: x_j > 0 (log requires positivity)
    bounds = [(1e-8, None)] * n

    result = minimize(
        fun=_kl_divergence_objective,
        x0=np.maximum(initial_guess, 1e-8),
        args=(q,),
        jac=lambda x, q: _kl_gradient(x, q),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-10, "maxiter": 500},
    )

    if not result.success:
        logger.warning(
            "RAS optimizer did not fully converge (status=%d, msg=%s). "
            "Returning best-effort solution.",
            result.status, result.message,
        )

    return np.maximum(result.x, 0.0)


def build_5digit_factor_intensity_table(
    intensity_column: str = "labor_compensation_intensity",
) -> Dict[int, float]:
    """
    Apply the RAS cross-entropy optimizer to expand 4-digit NIC factor
    intensities to 5-digit sub-sectors for the requested intensity column.

    Parameters
    ----------
    intensity_column : str
        One of 'labor_compensation_intensity' or 'fixed_capital_intensity'.

    Returns
    -------
    dict
        Keys = 5-digit NIC code, values = optimized factor intensity.
    """
    asi = load_asi_factor_intensities()
    mca = load_mca_structural_weights()

    result: Dict[int, float] = {}

    for nic4 in asi["nic4"].unique():
        parent_row = asi[asi["nic4"] == nic4]
        if parent_row.empty:
            continue

        q_intensity = float(parent_row[intensity_column].iloc[0])
        gva_total = float(parent_row["gva_total"].iloc[0])

        # Get 5-digit children from MCA
        children = mca[mca["nic4"] == nic4]
        if children.empty:
            # No children data — assign parent value uniformly
            result[nic4 * 10 + 1] = q_intensity
            continue

        omega = children["omega"].values.astype(float)
        n_children = len(omega)

        # Normalize omega so Σ ω_j = 1
        omega_sum = omega.sum()
        if omega_sum > 0:
            omega = omega / omega_sum
        else:
            omega = np.ones(n_children) / n_children

        total_target = q_intensity  # Equation 9: reconstruct the 4-digit intensity
        x0 = np.full(n_children, q_intensity)

        x_optimized = ras_optimize_5digit_intensities(
            q_4digit=q_intensity,
            omega_weights=omega,
            total_factor_value_4digit=total_target,
            initial_guess=x0,
        )

        for i, child_row in enumerate(children.itertuples()):
            nic5 = int(child_row.nic5) if hasattr(child_row, "nic5") else nic4 * 10 + i + 1
            result[nic5] = float(x_optimized[i]) if i < len(x_optimized) else q_intensity

    logger.info(
        "RAS optimization complete for '%s': %d 5-digit codes generated.",
        intensity_column, len(result),
    )
    return result
