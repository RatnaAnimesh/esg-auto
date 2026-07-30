"""
fcrm.data.mca_loader
--------------------
Loads Ministry of Corporate Affairs (MCA) Master Data — used as structural
proxy weights in the cross-entropy RAS optimizer (Section 2.1 of the spec).

The MCA publishes:
    - Count of active companies per NIC-5 code
    - Total authorised and paid-up capital per NIC-5 code

These serve as the structural weight ω_j in the KL-divergence minimization
(Equation 9), which distributes 4-digit ASI factor intensities down to
5-digit NIC sub-sectors without requiring expensive proprietary data.

Data endpoint: https://www.mca.gov.in/mcafoportal/viewOpenDataDownload.do
"""

from __future__ import annotations

import io
import logging
from functools import lru_cache

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

_MCA_LOCAL_PATH = (
    "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/mca_master_data.csv"
)

@lru_cache(maxsize=1)
def load_mca_structural_weights() -> pd.DataFrame:
    """
    Load MCA company count and paid-up capital by 5-digit NIC code.

    These are used as structural priors for the RAS cross-entropy optimizer,
    representing the weight ω_j in Equation 9.

    Returns
    -------
    pd.DataFrame
        Columns: ['nic5', 'nic4', 'nic2', 'company_count', 'paid_up_capital_cr', 'omega']
        omega = paid_up_capital_cr / sum(paid_up_capital_cr within nic4 group)
    """
    logger.info("Attempting to read local MCA Master Data.")
    try:
        df = pd.read_csv(_MCA_LOCAL_PATH)
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

        # Try to parse NIC5, company count, paid-up capital
        nic_col = next((c for c in df.columns if "nic" in c or "industry" in c), None)
        count_col = next((c for c in df.columns if "count" in c or "company" in c), None)
        capital_col = next((c for c in df.columns if "capital" in c or "paid" in c), None)

        if nic_col and count_col and capital_col:
            df = df[[nic_col, count_col, capital_col]].dropna()
            df.columns = ["nic5", "company_count", "paid_up_capital_cr"]
            df["nic5"] = df["nic5"].astype(int)
            df["nic4"] = df["nic5"] // 10
            df["nic2"] = df["nic5"] // 1000

            group_sums = df.groupby("nic4")["paid_up_capital_cr"].transform("sum")
            df["omega"] = df["paid_up_capital_cr"] / group_sums.replace(0, np.nan).fillna(1.0)
            logger.info("MCA Master Data loaded (%d 5-digit NIC entries).", len(df))
            return df

    except Exception as exc:
        logger.warning("Local MCA data read failed (%s). Building synthetic omega weights.", exc)

    return _build_synthetic_mca_weights()


def _build_synthetic_mca_weights() -> pd.DataFrame:
    """
    Build synthetic MCA omega weights using Dirichlet priors.

    Each 4-digit NIC code is assumed to contain between 2 and 9 child
    5-digit sub-sectors. Weights are drawn from a Dirichlet(1) distribution
    to reflect equal prior uncertainty, then perturbed by a log-normal
    company-count proxy.
    """
    records = []
    rng = np.random.default_rng(seed=99)

    for nic4 in range(100, 9900, 100):
        nic2 = nic4 // 100
        n_children = rng.integers(2, 9)
        weights = rng.dirichlet(np.ones(n_children))
        for i, w in enumerate(weights):
            nic5 = nic4 * 10 + i + 1
            company_count = int(rng.lognormal(mean=4.0, sigma=1.5))
            paid_up = float(rng.lognormal(mean=10.0, sigma=2.0))
            records.append({
                "nic5": nic5,
                "nic4": nic4,
                "nic2": nic2,
                "company_count": company_count,
                "paid_up_capital_cr": paid_up,
                "omega": w,
            })

    df = pd.DataFrame(records)
    logger.info("Synthetic MCA weights built (%d 5-digit NIC codes).", len(df))
    return df
