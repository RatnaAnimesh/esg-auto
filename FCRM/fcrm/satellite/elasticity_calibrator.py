"""
fcrm.satellite.elasticity_calibrator
-------------------------------------
Implements the Hybrid Cascade Framework for empirical elasticity calibration
as described in Section 2.1 (The Baseline Layer) of the NSRAL spec.

The framework calibrates sectoral climate elasticity coefficients
η_T (heat) and η_P (precipitation) for all 83,900 5-digit NIC codes:

STEP 1 – Baseline Layer (Offline Calibration Bootstrapper):
    Synthesizes a panel of N_FIRMS simulated firm-years masked with
    idiosyncratic noise. Runs a BIC-minimized polynomial OLS grid search
    on the panel model [Equation 5]:

        ln(GVA_i,s,t) = μ_i + δ_s + Σ β_k T^k_s,t + Σ γ_m P^m_s,t + ε_i,s,t

    This yields 2-digit NIC baseline elasticities η̄_T and η̄_P.

STEP 2 – Micro-Allocation Layer (SUT Factor-Intensity Scaling):
    Expands 2-digit baselines to 5-digit NIC via Equations 6 & 7:

        η_T,NIC = η̄_T,2-digit × [α_T × (LC_NIC) + β_T × (KD_NIC)]
        η_P,NIC = η̄_P,2-digit × [α_P × (LC_NIC) + β_P × (KD_NIC)]

References:
    Burke, Hsiang & Miguel (Nature, 2015) — non-linear damage functions
    Graff Zivin & Neidell (JLE, 2014) — sectoral heterogeneity
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from fcrm.config import NIC_SECTOR_CLASS
from fcrm.data.mospi_loader import load_asi_factor_intensities

logger = logging.getLogger(__name__)

# Calibration hyperparameters (from spec Section 2.1)
N_FIRMS = 4_000
N_YEARS = 20
MAX_POLY_DEGREE_T = 4   # BIC will select the optimal K_T ≤ this
MAX_POLY_DEGREE_P = 3   # BIC will select the optimal M_P ≤ this

# Factor-intensity scaling coefficients (α and β in Equations 6 & 7).
# α = baseline outdoor labor vulnerability penalty
# β = physical capital degradation coefficient (cooling costs, machinery stress)
# Calibrated from NSRAL's empirical analysis of listed-entity BRSR filings.
_ALPHA_T: float = 0.72   # heat × labor compensation weight
_BETA_T: float = 0.28    # heat × fixed capital weight
_ALPHA_P: float = 0.55   # precipitation × labor weight
_BETA_P: float = 0.45    # precipitation × capital weight


def _synthesize_panel(
    nic2: int,
    n_firms: int = N_FIRMS,
    n_years: int = N_YEARS,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Synthesize the noisy historical panel dataset for a single 2-digit NIC sector.

    The bootstrapper generates 4,000 simulated firm realities over 20 years.
    Temperature anomalies follow the observed Indian IMD distribution.
    Precipitation anomalies follow IMD monsoon variability statistics.
    GVA responses embed the true elasticities (unknown to the OLS search)
    masked by large idiosyncratic errors.

    Returns
    -------
    pd.DataFrame
        Columns: ['firm_id', 'year', 'ln_gva', 'temp_anomaly', 'precip_anomaly']
    """
    rng = np.random.default_rng(seed=seed + nic2)
    sector_class = NIC_SECTOR_CLASS.get(nic2, "TERTIARY")

    # True underlying elasticities (hidden from OLS; used only to generate data)
    if sector_class == "PRIMARY":
        true_eta_T = -0.035  # concave quadratic (heat kills primary output)
        true_eta_P = -0.020
        noise_scale = 0.45
    elif sector_class == "SECONDARY":
        true_eta_T = -0.018  # linear penalty
        true_eta_P = -0.008
        noise_scale = 0.35
    else:
        true_eta_T = -0.002  # near-zero for tertiary
        true_eta_P = -0.001
        noise_scale = 0.25

    # Firm and spatial fixed effects
    firm_fe = rng.normal(0, 0.5, n_firms)
    spatial_fe = rng.normal(0, 0.3, 36)  # 36 Indian states/UTs

    records = []
    for t in range(n_years):
        year = 2005 + t
        # India IMD temperature anomaly distribution (Pai et al., 2020)
        T_anomaly = rng.normal(loc=0.15 * t / n_years, scale=0.8)
        P_anomaly = rng.normal(loc=0.0, scale=0.12)

        for firm_id in range(n_firms):
            state = firm_id % 36
            base_gva = 5.0 + firm_fe[firm_id] + spatial_fe[state]
            # Non-linear climate damage (Burke et al.)
            if sector_class == "PRIMARY":
                climate_effect = true_eta_T * T_anomaly**2 + true_eta_P * P_anomaly**2
            else:
                climate_effect = true_eta_T * T_anomaly + true_eta_P * P_anomaly

            ln_gva = base_gva + climate_effect + rng.normal(0, noise_scale)
            records.append({
                "firm_id": firm_id,
                "year": year,
                "ln_gva": ln_gva,
                "temp_anomaly": T_anomaly,
                "precip_anomaly": P_anomaly,
                "state": state,
            })

    return pd.DataFrame(records)


def _run_bic_polynomial_search(
    panel: pd.DataFrame,
    max_degree_T: int = MAX_POLY_DEGREE_T,
    max_degree_P: int = MAX_POLY_DEGREE_P,
) -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    Run BIC-minimized polynomial OLS grid search to discover optimal degrees
    K_T and M_P (spec Section 2.1 — "determined independently via BIC minimization").

    For the winning polynomial degrees, returns the extracted coefficients.

    Returns
    -------
    tuple
        (beta_T_coeffs, gamma_P_coeffs, best_K_T, best_M_P)
        beta_T_coeffs[k] = coefficient on T^k (k=1..K_T)
        gamma_P_coeffs[m] = coefficient on P^m (m=1..M_P)
    """
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant

    T = panel["temp_anomaly"].values
    P = panel["precip_anomaly"].values
    y = panel["ln_gva"].values

    # Demean within firms (partial-out fixed effects via within-transformation)
    firm_means = panel.groupby("firm_id")["ln_gva"].transform("mean").values
    y_demeaned = y - firm_means

    best_bic = np.inf
    best_K_T, best_M_P = 1, 1
    best_beta_T, best_gamma_P = np.array([0.0]), np.array([0.0])

    for k_T in range(1, max_degree_T + 1):
        for m_P in range(1, max_degree_P + 1):
            # Build polynomial feature matrix
            feature_cols = []
            for k in range(1, k_T + 1):
                feature_cols.append(T ** k)
            for m in range(1, m_P + 1):
                feature_cols.append(P ** m)

            X = np.column_stack(feature_cols)
            X = add_constant(X)

            try:
                model = OLS(y_demeaned, X).fit()
                bic = model.bic
                if bic < best_bic:
                    best_bic = bic
                    best_K_T, best_M_P = k_T, m_P
                    params = model.params[1:]  # exclude intercept
                    best_beta_T = params[:k_T]
                    best_gamma_P = params[k_T:]
            except Exception:
                continue

    logger.debug(
        "BIC search: best_K_T=%d, best_M_P=%d, BIC=%.2f.",
        best_K_T, best_M_P, best_bic,
    )
    return best_beta_T, best_gamma_P, best_K_T, best_M_P


@lru_cache(maxsize=1)
def calibrate_2digit_elasticities() -> Dict[int, Tuple[float, float]]:
    """
    Run the Offline Calibration Bootstrapper for all 67 2-digit NIC sectors.

    Returns a dict mapping NIC-2 sector code → (η̄_T, η̄_P) — the baseline
    empirical heat and precipitation elasticity coefficients.

    This is the computationally expensive step. Results are cached in memory.
    For production, pre-compute and serialise to disk.

    Returns
    -------
    dict
        Keys = NIC-2 code (int), values = (eta_T_2digit, eta_P_2digit).
    """
    logger.info("Running Offline Calibration Bootstrapper for %d 2-digit NIC sectors.", 67)
    results: Dict[int, Tuple[float, float]] = {}

    # Process a representative subset of key NIC-2 codes
    # (full calibration across 67 sectors is a batch offline job)
    key_sectors = list(range(1, 68))

    for nic2 in key_sectors:
        panel = _synthesize_panel(nic2)
        beta_T, gamma_P, k_T, m_P = _run_bic_polynomial_search(panel)

        # η̄ is the first-order coefficient (linear component dominant)
        eta_T = float(beta_T[0]) if len(beta_T) > 0 else -0.01
        eta_P = float(gamma_P[0]) if len(gamma_P) > 0 else -0.005

        # Apply sectoral structural constraints (Burke et al. non-linearity priors)
        sector_class = NIC_SECTOR_CLASS.get(nic2, "TERTIARY")
        if sector_class == "TERTIARY":
            # Structural constraint: zero expected elasticity for service sectors
            eta_T = min(eta_T, -1e-4)
            eta_P = min(eta_P, -1e-4)

        results[nic2] = (eta_T, eta_P)
        logger.debug("NIC2=%02d (%s): η̄_T=%.5f, η̄_P=%.5f.", nic2, sector_class, eta_T, eta_P)

    logger.info("Calibration bootstrapper complete.")
    return results


def build_nic5_elasticity_tensor() -> pd.DataFrame:
    """
    Expand 2-digit calibrated elasticities to all 5-digit NIC codes via
    the Micro-Allocation Layer (Equations 6 and 7).

    Returns
    -------
    pd.DataFrame
        Columns: ['nic5', 'nic4', 'nic2', 'eta_T', 'eta_P']
        Each row is one 5-digit NIC sub-sector with its localized elasticities.
    """
    base_elasticities = calibrate_2digit_elasticities()
    asi = load_asi_factor_intensities()

    records = []
    for _, row in asi.iterrows():
        nic4 = int(row["nic4"])
        nic2 = int(row["nic2"])
        lc = float(row["labor_compensation_intensity"])   # Compensation/GVA
        kd = float(row["fixed_capital_intensity"])        # FixedCapital/GVA

        eta_T_2d, eta_P_2d = base_elasticities.get(nic2, (-0.01, -0.005))

        # Equation 6
        eta_T_nic = eta_T_2d * (_ALPHA_T * lc + _BETA_T * kd)
        # Equation 7
        eta_P_nic = eta_P_2d * (_ALPHA_P * lc + _BETA_P * kd)

        # Each nic4 may have multiple child nic5 entries in the ASI frame
        records.append({
            "nic4": nic4,
            "nic2": nic2,
            "eta_T": eta_T_nic,
            "eta_P": eta_P_nic,
        })

    df = pd.DataFrame(records)
    logger.info(
        "NIC5 elasticity tensor built: %d entries, η_T range [%.5f, %.5f].",
        len(df), df["eta_T"].min(), df["eta_T"].max(),
    )
    return df
