"""
fcrm.data.pcaf_loader
---------------------
Loads PCAF (Partnership for Carbon Accounting Financials) sectoral emission
intensity data — the fallback mechanism for unlisted entities with no direct
carbon disclosure (Section 2.2 of the spec).

PCAF Data Quality Score hierarchy:
    Tier 1 – Verified BRSR Scope 1/2/3 disclosures
    Tier 2 – Physical production intensity factors
    Tier 3 – Economic revenue proxy (PCAF intensity × revenue)
    Tier 4 – Sector-average from peer disclosures
    Tier 5 – NIC-PCAF global sectoral intensity (this module)

Primary source:
    PCAF Global GHG Accounting & Reporting Standard for the Financial Industry
    Open data published at https://carbonaccountingfinancials.com/
    NIC-mapped intensities derived from EXIOBASE 3.8.2 and CEEW-India mappings.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# PCAF sectoral GHG intensities (tCO2e per INR 1 crore of revenue).
# Mapped to MoSPI 2-digit NIC codes (67 industries).
# Sources:
#   - PCAF (2022): Global GHG Accounting Standard, Annex 2 (NACE-to-PCAF mapping)
#   - CEEW (2021): India-specific EXIOBASE-to-NIC cross-walk
#   - IEA (2023): India Energy Balance emission factors
_PCAF_INTENSITY_NIC2: Dict[int, float] = {
    # --- PRIMARY ---
    1: 2.1,   2: 3.4,   3: 1.7,   4: 0.9,   5: 1.2,   6: 0.5,
    7: 9.2,   8: 7.1,   9: 5.8,   10: 4.5,
    # --- SECONDARY ---
    11: 13.2, 12: 10.5, 13: 8.0,  14: 7.5,  15: 6.0,  16: 8.8,
    17: 10.2, 18: 5.8,  19: 16.5, 20: 13.2, 21: 9.4,  22: 7.2,
    23: 20.5, 24: 25.0, 25: 10.0, 26: 6.0,  27: 6.8,  28: 7.9,
    29: 9.0,  30: 8.4,  31: 5.2,  32: 5.5,  33: 4.0,
    35: 65.0, 36: 1.5,  37: 1.0,  38: 5.2,
    41: 7.5,  42: 8.2,  43: 5.8,
    # --- TERTIARY ---
    45: 4.2,  46: 2.5,  47: 2.0,
    49: 17.0, 50: 20.0, 51: 30.0, 52: 3.5,  53: 3.0,
    55: 4.8,  56: 3.8,
    58: 0.9,  59: 0.7,
    61: 1.4,  62: 0.6,  63: 0.5,
    64: 0.7,  65: 0.6,  66: 0.5,
    68: 3.2,  69: 0.6,  70: 0.7,  71: 0.8,  72: 0.9,
    73: 0.6,  74: 0.7,  75: 0.5,
    77: 0.6,  78: 0.5,  79: 1.4,  80: 0.6,  81: 1.7,  82: 0.6,
    84: 1.4,  85: 0.9,  86: 1.1,  87: 1.0,  88: 0.8,
    90: 0.7,  91: 0.5,  92: 0.6,  93: 0.9,  94: 0.6,  95: 0.7,  96: 0.6,
    97: 0.4,  99: 0.3,
}

# PCAF Data Quality Score bounds per tier — maps to confidence interval widths
_PCAF_TIER_SCORE: Dict[int, int] = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}


_BRSR_LOCAL_PATH = (
    "/Users/ashishmishra/animeshratna/nsral/climate_risk_modelling/data/brsr_consolidated.csv"
)

@lru_cache(maxsize=1)
def get_pcaf_intensities() -> pd.DataFrame:
    """
    Return a DataFrame of PCAF emission intensities indexed by NIC-2 sector.
    Attempts to derive empirical intensity from local BRSR data first.

    Returns
    -------
    pd.DataFrame
        Columns: ['nic2', 'pcaf_intensity_tco2e_per_inr_cr', 'pcaf_tier']
    """
    records = []
    logger.info("Attempting to derive empirical PCAF intensities from BRSR.")
    try:
        # Load local BRSR if available
        df = pd.read_csv(_BRSR_LOCAL_PATH, low_memory=False)
        df.columns = df.columns.str.lower().str.strip()
        
        # Look for relevant columns, or use synthetic mapping if messy
        nic_col = next((c for c in df.columns if "nic" in c), None)
        rev_col = next((c for c in df.columns if "revenue" in c or "turnover" in c), None)
        s1_col = next((c for c in df.columns if "scope 1" in c or "scope_1" in c or "s1" in c), None)
        s2_col = next((c for c in df.columns if "scope 2" in c or "scope_2" in c or "s2" in c), None)
        
        if nic_col and rev_col and s1_col and s2_col:
            df["nic2"] = (df[nic_col].astype(str).str[:2]).astype(int)
            df["total_emissions"] = pd.to_numeric(df[s1_col], errors='coerce') + pd.to_numeric(df[s2_col], errors='coerce')
            df["revenue"] = pd.to_numeric(df[rev_col], errors='coerce')
            df = df.dropna(subset=["nic2", "total_emissions", "revenue"])
            df = df[df["revenue"] > 0]
            
            # Calculate intensity per NIC2
            grouped = df.groupby("nic2").agg({"total_emissions": "sum", "revenue": "sum"})
            grouped["pcaf_intensity_tco2e_per_inr_cr"] = grouped["total_emissions"] / grouped["revenue"]
            grouped["pcaf_tier"] = 4  # Tier 4 - Sector average from peer disclosures
            
            # Merge with default PCAF for missing sectors
            empirical_dict = grouped["pcaf_intensity_tco2e_per_inr_cr"].to_dict()
            for nic2, intensity in _PCAF_INTENSITY_NIC2.items():
                if nic2 in empirical_dict:
                    records.append({"nic2": nic2, "pcaf_intensity_tco2e_per_inr_cr": empirical_dict[nic2], "pcaf_tier": 4})
                else:
                    records.append({"nic2": nic2, "pcaf_intensity_tco2e_per_inr_cr": intensity, "pcaf_tier": 5})
            
            logger.info("Successfully derived empirical PCAF intensities for %d sectors.", len(empirical_dict))
            return pd.DataFrame(records).set_index("nic2")
    except Exception as exc:
        logger.warning("Failed to derive empirical PCAF from BRSR (%s). Using defaults.", exc)

    # Fallback to defaults
    records = [
        {"nic2": nic2, "pcaf_intensity_tco2e_per_inr_cr": intensity, "pcaf_tier": 5}
        for nic2, intensity in _PCAF_INTENSITY_NIC2.items()
    ]
    return pd.DataFrame(records).set_index("nic2")


def impute_emissions(
    revenue_inr_cr: float,
    nic2: int,
    scope1_tco2e: Optional[float] = None,
    scope2_tco2e: Optional[float] = None,
    physical_output_tonnes: Optional[float] = None,
    physical_intensity_tco2e_per_tonne: Optional[float] = None,
) -> tuple[float, int]:
    """
    Apply the PCAF hierarchical proxy fallback to derive absolute emissions.

    Implements Section 2.2 of the spec:
        Tier 1/2 – BRSR verified figures if present
        Tier 3/4 – Physical intensity × physical output
        Tier 5   – Revenue × PCAF sectoral intensity (this fallback)

    Parameters
    ----------
    revenue_inr_cr : float
        Total annual revenue in INR crore.
    nic2 : int
        2-digit NIC sector code.
    scope1_tco2e, scope2_tco2e : float, optional
        Verified Scope 1 and Scope 2 emissions from BRSR (Tier 1).
    physical_output_tonnes : float, optional
        Physical production volume (Tier 3).
    physical_intensity_tco2e_per_tonne : float, optional
        Emission intensity factor for the physical output (Tier 3).

    Returns
    -------
    tuple[float, int]
        (imputed_emissions_tco2e, pcaf_quality_tier)
    """
    # Tier 1 — BRSR verified
    if scope1_tco2e is not None and scope2_tco2e is not None:
        return scope1_tco2e + scope2_tco2e, 1

    # Tier 3 — Physical intensity
    if (
        physical_output_tonnes is not None
        and physical_intensity_tco2e_per_tonne is not None
    ):
        return physical_output_tonnes * physical_intensity_tco2e_per_tonne, 3

    # Tier 5 — Revenue × PCAF sectoral intensity (spec Equation 10)
    pcaf_df = get_pcaf_intensities()
    intensity = pcaf_df.loc[nic2, "pcaf_intensity_tco2e_per_inr_cr"] if nic2 in pcaf_df.index else 3.0
    imputed = revenue_inr_cr * intensity
    logger.debug(
        "Tier 5 PCAF imputation: NIC2=%d, revenue=%.2f INR cr, intensity=%.3f, emissions=%.1f tCO2e.",
        nic2, revenue_inr_cr, intensity, imputed,
    )
    return imputed, 5
