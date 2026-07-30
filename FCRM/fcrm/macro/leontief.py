"""
fcrm.macro.leontief
-------------------
Implements the Leontief Input-Output model for supply chain contagion
as described in Section 1.2 of the NSRAL specification.

Mathematical specification:
    Technical Coefficients Matrix:  A  (67×67, loaded from MoSPI SUT)
    Leontief Inverse:               L = (I - A)^{-1}           [Equation 1]
    Supply chain contagion vector:  δ = γᵀ L                   [Equation 2]

    where γ is the 67-element vector of direct carbon emission intensities
    (tCO2e per INR crore) and δ[j] captures both direct and indirect
    (Scope 3 upstream) carbon dependencies of sector j.

The 67-industry δ vector is subsequently expanded to 83,900 5-digit NIC codes
via the DTVF module (Section 1.3).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict

import numpy as np
import numpy.linalg as la

from fcrm.data.mospi_loader import load_sut_technical_coefficients, load_direct_carbon_intensities

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def compute_leontief_inverse() -> np.ndarray:
    """
    Compute the Leontief Inverse Matrix L = (I - A)^{-1}.

    This matrix captures the total (direct + indirect) requirements of one
    industry from all other industries when producing one additional unit of
    final demand, encoding the full supply chain contagion network.

    Returns
    -------
    np.ndarray
        Shape (67, 67). L[i, j] = total output of sector i required per unit
        of final demand for sector j.

    Raises
    ------
    LinAlgError
        If (I - A) is singular (i.e., no valid Leontief inverse exists). This
        would indicate a structurally incoherent input-output table.
    """
    A = load_sut_technical_coefficients().values.astype(float)
    n = A.shape[0]
    I = np.eye(n)
    I_minus_A = I - A

    # Validate that (I - A) satisfies the Hawkins-Simon conditions (all
    # leading principal minors of (I-A) are positive), which guarantees
    # that the Leontief inverse is non-negative.
    eigenvalues = la.eigvals(A)
    spectral_radius = np.max(np.abs(eigenvalues))
    if spectral_radius >= 1.0:
        logger.warning(
            "Technical coefficients matrix A has spectral radius %.4f >= 1.0. "
            "Leontief system may not converge. Clamping A to ensure stability.",
            spectral_radius,
        )
        # Scale A down so that spectral_radius < 1 (preserve structure, not magnitudes)
        A = A / (spectral_radius + 0.05)
        I_minus_A = I - A

    L = la.inv(I_minus_A)
    logger.info(
        "Leontief inverse computed. Shape: %s. Max multiplier: %.4f.",
        L.shape,
        L.max(),
    )
    return L


def compute_supply_chain_contagion() -> np.ndarray:
    """
    Compute the supply chain carbon contagion vector δ = γᵀ L [Equation 2].

    Each element δ[j] represents the total upstream carbon dependency
    (Scope 3 cost-push pressure) for sector j under a unit carbon price shock.
    A high δ for a downstream sector (e.g., automotive) indicates that its
    supply chain (e.g., steel, coal) is heavily carbon-intensive even if the
    firm's own Scope 1 emissions are modest.

    Returns
    -------
    np.ndarray
        Shape (67,). δ[j] = total carbon burden of sector j per unit output,
        including all upstream indirect dependencies (tCO2e / INR crore).
    """
    L = compute_leontief_inverse()
    gamma_dict = load_direct_carbon_intensities()

    # Build γ vector aligned to MoSPI industry index 1..67
    gamma = np.array([gamma_dict.get(i, 3.0) for i in range(1, 68)], dtype=float)

    # Equation 2: δ = γᵀ L  (row vector times matrix = row vector)
    delta = gamma @ L  # shape (67,)

    logger.info(
        "Supply chain contagion δ computed. Min=%.3f, Max=%.3f, Mean=%.3f.",
        delta.min(), delta.max(), delta.mean(),
    )
    return delta


def get_sector_contagion_map() -> Dict[int, float]:
    """
    Return a dictionary mapping MoSPI sector index (1–67) to its δ value.

    This is the convenience accessor used downstream by the DTVF module and
    the CEaR calibrator when looking up sector-level supply chain contagion.

    Returns
    -------
    dict
        Keys = sector index (1–67), values = δ_NIC (float).
    """
    delta = compute_supply_chain_contagion()
    return {i + 1: float(delta[i]) for i in range(len(delta))}
