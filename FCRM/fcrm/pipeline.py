"""
fcrm.pipeline
-------------
End-to-end climate stress testing pipeline orchestrator.

Executes the full NSRAL FCRM engine in sequential module order:
    1. Macro: Leontief supply chain contagion + DTVF
    2. Satellite: CEaR (EBITDA compression) + TCaR (transition CAPEX risk)
    3. Credit: Merton inversion + KMV EDF + Stress injection + Clayton Copula + ECL
    4. Institutional: RWA inflation + CET1 degradation

Usage:
    from fcrm.pipeline import run_full_stress_test
    results = run_full_stress_test(scenario=NGFSScenario.DELAYED_TRANSITION)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from fcrm.config import EngineConfig, NGFSScenario
from fcrm.credit.clayton_copula import compute_stressed_lgd
from fcrm.credit.ecl import (
    LoanExposure,
    compute_ecl,
    compute_incremental_ecl,
    compute_rwa_contribution,
)
from fcrm.credit.kmv_edf import compute_empirical_edf
from fcrm.credit.merton import FirmSnapshot, invert_merton
from fcrm.credit.stress_injection import (
    StressInputs,
    compute_stressed_pd,
    compute_ngfs_severity_score,
)
from fcrm.institutional.cet1 import (
    InstitutionalBalanceSheet,
    LoanStressResult,
    run_institutional_stress,
    InstitutionalStressOutput,
)
from fcrm.macro.dtvf import compute_dtvf_series
from fcrm.macro.leontief import compute_supply_chain_contagion
from fcrm.satellite.cear import CorporateEntity, compute_entity_cear_series
from fcrm.satellite.tcar import BorrowingFirmProfile, compute_tcar_ratio

logger = logging.getLogger(__name__)


@dataclass
class BorrowerInput:
    """
    Complete borrower profile for end-to-end pipeline execution.

    For listed entities: equity data is market-derived.
    For unlisted SMEs: use accounting proxies.

    Attributes
    ----------
    entity_id : str
    firm_snapshot : FirmSnapshot
        Inputs for Merton inversion.
    tcar_profile : BorrowingFirmProfile
        Inputs for TCaR computation.
    cear_entity : CorporateEntity
        Inputs for CEaR computation (must include facilities).
    loan : LoanExposure
        Credit exposure.
    lgd_base : float
        Collateral-adjusted baseline LGD.
    climate_risk_score : float
        Physical risk composite score [0, 1] for insurance decay.
    physical_damage_probability : float
        P_Damage input to Clayton copula.
    nic5 : int
        5-digit NIC code for DTVF lookup.
    is_sme : bool
        Whether to apply SME Structural Proxy Transfer.
    """

    entity_id: str
    firm_snapshot: FirmSnapshot
    tcar_profile: BorrowingFirmProfile
    cear_entity: CorporateEntity
    loan: LoanExposure
    lgd_base: float = 0.45
    climate_risk_score: float = 0.40
    physical_damage_probability: float = 0.20
    nic5: int = 24101
    is_sme: bool = False


@dataclass
class BorrowerStressResult:
    """Complete per-borrower stress output for a single scenario year."""

    entity_id: str
    year: int
    scenario: str
    dd_base: float
    dd_stressed: float
    pd_base: float
    pd_stressed: float
    lgd_stressed: float
    ead_cr: float
    ecl_stressed_cr: float
    delta_ecl_cr: float
    cear_ratio: float
    tcar_ratio: float
    pcaf_tier: int
    epsilon_nic_t: float


@dataclass
class PortfolioStressResult:
    """Aggregated stress output for a portfolio at a single year."""

    year: int
    scenario: str
    borrower_results: List[BorrowerStressResult] = field(default_factory=list)
    institutional_result: Optional[InstitutionalStressOutput] = None

    @property
    def portfolio_pd_stressed(self) -> float:
        if not self.borrower_results:
            return 0.0
        total_ead = sum(r.ead_cr for r in self.borrower_results)
        if total_ead < 1e-6:
            return 0.0
        return sum(r.pd_stressed * r.ead_cr for r in self.borrower_results) / total_ead

    @property
    def total_delta_ecl_cr(self) -> float:
        return sum(r.delta_ecl_cr for r in self.borrower_results)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([{
            "entity_id": r.entity_id,
            "year": r.year,
            "scenario": r.scenario,
            "dd_base": r.dd_base,
            "dd_stressed": r.dd_stressed,
            "pd_base": r.pd_base,
            "pd_stressed": r.pd_stressed,
            "lgd_stressed": r.lgd_stressed,
            "ead_cr": r.ead_cr,
            "ecl_stressed_cr": r.ecl_stressed_cr,
            "delta_ecl_cr": r.delta_ecl_cr,
            "cear_ratio": r.cear_ratio,
            "tcar_ratio": r.tcar_ratio,
            "pcaf_tier": r.pcaf_tier,
            "epsilon_nic_t": r.epsilon_nic_t,
        } for r in self.borrower_results])


from fcrm.data.geospatial_loader import get_geospatial_risk

def _process_borrower_for_year(
    borrower: BorrowerInput,
    scenario: NGFSScenario,
    year: int,
    delta_gdp: float,
    climate_severity: float,
    config: EngineConfig,
) -> BorrowerStressResult:
    """
    Run all four engine modules for a single borrower at a single year.
    """
    # Geopatial Capacity-Weighted Aggregation (if facilities are provided)
    if borrower.cear_entity.facilities:
        agg_severity = 0.0
        agg_prob = 0.0
        for f in borrower.cear_entity.facilities:
            sev, prob = get_geospatial_risk(f.lat, f.lon)
            agg_severity += f.capacity_weight * sev
            agg_prob += f.capacity_weight * prob
            
        borrower.climate_risk_score = max(agg_severity, climate_severity)
        borrower.physical_damage_probability = max(agg_prob, 0.20 * climate_severity)
        
        # Only override climate_severity if geospatial data actually exists
        if agg_severity > 0.0:
            climate_severity = agg_severity


    # --- Module 1: DTVF ---
    dtvf_series = compute_dtvf_series(borrower.nic5, scenario, [year])
    epsilon_nic_t = float(dtvf_series.get(year, 0.5))

    # --- Module 2a: CEaR ---
    # Apply capacity-weighted climate shock scaling to CEaR if derived from local hazards
    # We pass the aggregated severity as a multiplier on the macro anomalies.
    cear_series = compute_entity_cear_series(
        borrower.cear_entity, scenario, [year]
    )
    cear_ratio = float(cear_series.get(year, 0.0))
    if borrower.cear_entity.facilities:
        # Scale CEaR by the localized hazard severity anomaly relative to baseline (assumed ~0.4)
        cear_ratio = min(cear_ratio * (climate_severity / 0.40), 1.0)

    # --- Module 2b: TCaR ---
    tcar, pcaf_tier = compute_tcar_ratio(borrower.tcar_profile, scenario, year)

    # --- Module 3a: Merton inversion ---
    try:
        _, sigma_V, dd_base = invert_merton(borrower.firm_snapshot, config, borrower.is_sme)
    except Exception as exc:
        logger.warning("Merton inversion failed for %s: %s. Using fallback.", borrower.entity_id, exc)
        dd_base = 3.0
        sigma_V = 0.30

    # Baseline PD (pre-stress)
    pd_base = float(compute_empirical_edf(dd_base, climate_severity=0.0))

    # --- Module 3b: Stress injection ---
    stress_inputs = StressInputs(
        entity_id=borrower.entity_id,
        dd_base=dd_base,
        epsilon_nic_t=epsilon_nic_t,
        delta_gdp_t=delta_gdp,
        cear_ratio_t=cear_ratio,
        tcar_t=tcar,
        climate_severity=climate_severity,
    )
    dd_stressed, pd_stressed = compute_stressed_pd(stress_inputs)

    # --- Module 3c: Clayton Copula LGD ---
    lgd_stressed = compute_stressed_lgd(
        lgd_base=borrower.lgd_base,
        pd_stressed=pd_stressed,
        p_damage=borrower.physical_damage_probability,
        climate_risk_score=borrower.climate_risk_score,
        config=config,
    )

    # --- Module 3d: ECL ---
    ead_cr = borrower.loan.drawn_balance_cr + borrower.loan.ccf * borrower.loan.undrawn_balance_cr
    ecl_stressed, delta_ecl = compute_incremental_ecl(
        pd_stressed=pd_stressed,
        lgd_stressed=lgd_stressed,
        pd_base=pd_base,
        lgd_base=borrower.lgd_base,
        loan=borrower.loan,
    )

    return BorrowerStressResult(
        entity_id=borrower.entity_id,
        year=year,
        scenario=scenario.value,
        dd_base=dd_base,
        dd_stressed=dd_stressed,
        pd_base=pd_base,
        pd_stressed=pd_stressed,
        lgd_stressed=lgd_stressed,
        ead_cr=ead_cr,
        ecl_stressed_cr=ecl_stressed,
        delta_ecl_cr=delta_ecl,
        cear_ratio=cear_ratio,
        tcar_ratio=tcar,
        pcaf_tier=pcaf_tier,
        epsilon_nic_t=epsilon_nic_t,
    )


def run_full_stress_test(
    borrowers: List[BorrowerInput],
    balance_sheet: InstitutionalBalanceSheet,
    scenario: NGFSScenario = NGFSScenario.NET_ZERO_2050,
    years: Optional[List[int]] = None,
    gdp_shocks: Optional[Dict[int, float]] = None,
    config: EngineConfig = EngineConfig(),
) -> List[PortfolioStressResult]:
    """
    Execute the full NSRAL FCRM stress testing pipeline.

    Parameters
    ----------
    borrowers : list of BorrowerInput
        All borrowers in the credit portfolio.
    balance_sheet : InstitutionalBalanceSheet
        Bank-level balance sheet.
    scenario : NGFSScenario
        NGFS pathway to run.
    years : list of int, optional
        Projection years. Defaults to config.horizon_years.
    gdp_shocks : dict, optional
        GDP growth by year. Defaults to -2% under stress scenarios.
    config : EngineConfig

    Returns
    -------
    list of PortfolioStressResult
        One result per projection year.
    """
    if years is None:
        years = config.horizon_years

    if gdp_shocks is None:
        # Default GDP shock calibrated to NGFS scenario severity
        severity = compute_ngfs_severity_score(scenario.value)
        gdp_shocks = {yr: -0.01 - severity * 0.04 for yr in years}

    climate_severity = compute_ngfs_severity_score(scenario.value)
    portfolio_results = []

    logger.info(
        "Running FCRM stress test: scenario=%s, years=%d–%d, borrowers=%d.",
        scenario.value, min(years), max(years), len(borrowers),
    )

    for year in years:
        delta_gdp = gdp_shocks.get(year, -0.02)
        borrower_results = []
        loan_stress_results = []

        for borrower in borrowers:
            b_result = _process_borrower_for_year(
                borrower, scenario, year, delta_gdp, climate_severity, config
            )
            borrower_results.append(b_result)

            # Build LoanStressResult for institutional engine
            loan_stress_results.append(LoanStressResult(
                facility_id=borrower.loan.facility_id,
                pd_stressed=b_result.pd_stressed,
                lgd_stressed=b_result.lgd_stressed,
                ead_cr=b_result.ead_cr,
                rwa_stressed_cr=compute_rwa_contribution(
                    b_result.pd_stressed, b_result.lgd_stressed, borrower.loan
                ),
                rwa_base_cr=compute_rwa_contribution(
                    b_result.pd_base, borrower.lgd_base, borrower.loan
                ),
                ecl_stressed_cr=b_result.ecl_stressed_cr,
                delta_ecl_cr=b_result.delta_ecl_cr,
            ))

        portfolio = PortfolioStressResult(year=year, scenario=scenario.value)
        portfolio.borrower_results = borrower_results

        # Module 4: Institutional stress
        institutional_out = run_institutional_stress(
            balance_sheet=balance_sheet,
            loan_results=loan_stress_results,
            portfolio_pd_stressed=portfolio.portfolio_pd_stressed,
            climate_severity=climate_severity,
            year=year,
            config=config,
        )
        portfolio.institutional_result = institutional_out
        portfolio_results.append(portfolio)

        logger.info(
            "Year %d: avg_PD_stressed=%.4f, ΔECLᵢₙ꜀=%.2f cr, CET1_stressed=%.4f.",
            year,
            portfolio.portfolio_pd_stressed,
            portfolio.total_delta_ecl_cr,
            institutional_out.cet1_stressed,
        )

    return portfolio_results
