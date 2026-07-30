"""
fcrm.institutional.total_loss
------------------------------
Five-component Total Institutional Loss aggregation — Section 4.2.3 of spec.

Loss_Total = ΔECLᵢₙ꜀ + Liquidity_Draw + Market_Loss + Funding_Cost + Op_Loss  [Eq. 27]

Where:
    ΔECLᵢₙ꜀   – Sum of all incremental Expected Credit Losses from borrower defaults
    Liquidity_Draw – Cash flow losses from distressed borrowers drawing undrawn lines
    Market_Loss    – Mark-to-market shock on treasury portfolio (credit spread widening)
    Funding_Cost   – Wholesale funding premium due to bank credit rating downgrade
    Op_Loss        – Physical damage to bank infrastructure + regulatory fines

Each component is modelled as an analytical function of the portfolio-level
stressed PD, LGD, and the climate severity score. These functions are
calibrated to observed Indian banking sector stress events (RBI FSR, 2020-2023).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class InstitutionalBalanceSheet:
    """
    Bank-level balance sheet inputs (static accounting, pre-climate shock).

    Attributes
    ----------
    institution_id : str
    cet1_capital_base_cr : float
        Core Equity Tier 1 capital (INR crore).
    rwa_base_cr : float
        Baseline aggregate Risk-Weighted Assets (INR crore).
    treasury_portfolio_cr : float
        Mark-to-market treasury bond portfolio (INR crore).
    total_credit_portfolio_cr : float
        Total committed credit portfolio (drawn + undrawn, INR crore).
    total_undrawn_commitments_cr : float
        Aggregate undrawn committed credit lines (INR crore).
    wholesale_funding_cr : float
        Outstanding wholesale funding obligations (INR crore).
    branch_replacement_cost_cr : float
        Physical infrastructure replacement cost (INR crore).
    """

    institution_id: str
    cet1_capital_base_cr: float
    rwa_base_cr: float
    treasury_portfolio_cr: float
    total_credit_portfolio_cr: float
    total_undrawn_commitments_cr: float
    wholesale_funding_cr: float = 0.0
    branch_replacement_cost_cr: float = 0.0


@dataclass
class LossComponents:
    """Breakdown of the five institutional loss components (INR crore)."""

    delta_ecl_cr: float = 0.0
    liquidity_draw_cr: float = 0.0
    market_loss_cr: float = 0.0
    funding_cost_cr: float = 0.0
    op_loss_cr: float = 0.0

    @property
    def total_cr(self) -> float:
        """Total institutional loss [Equation 27]."""
        return (
            self.delta_ecl_cr
            + self.liquidity_draw_cr
            + self.market_loss_cr
            + self.funding_cost_cr
            + self.op_loss_cr
        )


def estimate_liquidity_drawdown(
    total_undrawn_cr: float,
    portfolio_pd_stressed: float,
    drawdown_severity: float = 0.40,
) -> float:
    """
    Estimate Liquidity_Draw: cash flow losses from distressed borrowers
    maximizing undrawn credit lines prior to default (Section 4.2.3).

    The fraction of the undrawn portfolio that is drawn down is modelled as:
        Liquidity_Draw = total_undrawn × portfolio_PD_stressed × drawdown_severity

    Where drawdown_severity reflects the empirically observed fraction of
    distressed borrowers who max out revolving facilities before defaulting.
    Calibrated to Indian NPA data (RBI FSR, 2023): ~40%.

    Parameters
    ----------
    total_undrawn_cr : float
        Total undrawn committed credit lines (INR crore).
    portfolio_pd_stressed : float
        Portfolio-level weighted average stressed PD.
    drawdown_severity : float
        Fraction of distressed borrowers who fully draw undrawn lines.

    Returns
    -------
    float
        Liquidity drawdown loss (INR crore).
    """
    return total_undrawn_cr * portfolio_pd_stressed * drawdown_severity


def estimate_market_loss(
    treasury_portfolio_cr: float,
    spread_widening_bps: float,
    portfolio_duration_years: float = 5.0,
) -> float:
    """
    Estimate Market_Loss: mark-to-market shock on treasury portfolio.

    Sovereign bond price change from spread widening:
        Market_Loss ≈ treasury_portfolio × duration × Δspread

    Spread widening is driven by climate-induced rating migration and
    systemic risk premium expansion in wholesale markets.

    Parameters
    ----------
    treasury_portfolio_cr : float
        Treasury bond portfolio at market value (INR crore).
    spread_widening_bps : float
        Estimated credit spread widening in basis points (e.g., 50 bps).
    portfolio_duration_years : float
        Modified duration of the treasury portfolio in years.

    Returns
    -------
    float
        Mark-to-market loss (INR crore).
    """
    delta_spread = spread_widening_bps / 10_000.0  # convert bps to decimal
    return treasury_portfolio_cr * portfolio_duration_years * delta_spread


def estimate_funding_cost(
    wholesale_funding_cr: float,
    rating_downgrade_spread_bps: float,
    funding_maturity_years: float = 2.0,
) -> float:
    """
    Estimate Funding_Cost: premium paid in wholesale markets due to own
    credit rating downgrade under climate stress.

    Funding_Cost = wholesale_funding × downgrade_spread × maturity

    Parameters
    ----------
    wholesale_funding_cr : float
        Outstanding wholesale funding (INR crore).
    rating_downgrade_spread_bps : float
        Additional funding spread from bank's own rating downgrade (bps).
    funding_maturity_years : float
        Average residual maturity of wholesale funding.

    Returns
    -------
    float
        Incremental funding cost (INR crore per year).
    """
    spread = rating_downgrade_spread_bps / 10_000.0
    return wholesale_funding_cr * spread * funding_maturity_years


def estimate_operational_loss(
    branch_replacement_cost_cr: float,
    physical_damage_fraction: float,
    regulatory_fine_rate: float = 0.001,
    total_credit_portfolio_cr: float = 0.0,
) -> float:
    """
    Estimate Op_Loss: physical damage to bank infrastructure + regulatory fines.

    Op_Loss = branch_replacement_cost × physical_damage_fraction
              + regulatory_fines_rate × total_portfolio

    The regulatory fine component models transition-related penalties for
    banks failing to comply with RBI Climate Risk Disclosure mandates.

    Parameters
    ----------
    branch_replacement_cost_cr : float
        Total infrastructure replacement cost (INR crore).
    physical_damage_fraction : float
        Fraction of infrastructure physically damaged [0, 1].
    regulatory_fine_rate : float
        Regulatory fine as fraction of total portfolio (0.1% default).
    total_credit_portfolio_cr : float
        Total credit portfolio (INR crore).

    Returns
    -------
    float
        Operational loss (INR crore).
    """
    physical_damage = branch_replacement_cost_cr * physical_damage_fraction
    regulatory_fines = regulatory_fine_rate * total_credit_portfolio_cr
    return physical_damage + regulatory_fines


def compute_total_institutional_loss(
    balance_sheet: InstitutionalBalanceSheet,
    delta_ecl_cr: float,
    portfolio_pd_stressed: float,
    climate_severity: float,
) -> LossComponents:
    """
    Aggregate the five-component total institutional loss [Equation 27].

    Derives Market_Loss, Liquidity_Draw, Funding_Cost, and Op_Loss from
    the climate severity score and institutional balance sheet parameters.

    Parameters
    ----------
    balance_sheet : InstitutionalBalanceSheet
        Bank-level balance sheet inputs.
    delta_ecl_cr : float
        Sum of incremental ECL from the credit portfolio (INR crore).
    portfolio_pd_stressed : float
        Weighted-average stressed PD across the loan portfolio.
    climate_severity : float
        NGFS scenario severity ∈ [0.0, 1.0].

    Returns
    -------
    LossComponents
        All five loss components and their total.
    """
    # Liquidity drawdown
    liquidity_draw = estimate_liquidity_drawdown(
        balance_sheet.total_undrawn_commitments_cr,
        portfolio_pd_stressed,
    )

    # Treasury mark-to-market: spread widening scales with climate severity
    # At max severity (1.0), assume 150 bps spread widening (Indian corporate bond market)
    spread_widening = climate_severity * 150.0  # bps
    market_loss = estimate_market_loss(balance_sheet.treasury_portfolio_cr, spread_widening)

    # Funding cost: own rating downgrade driven by portfolio deterioration
    # Every 10% of PD increase → ~25 bps rating downgrade premium (calibrated to RBI FSR)
    downgrade_bps = min(portfolio_pd_stressed * 250.0, 100.0)  # capped at 100 bps
    funding_cost = estimate_funding_cost(balance_sheet.wholesale_funding_cr, downgrade_bps)

    # Operational loss: physical damage scales with severity
    physical_damage_frac = climate_severity * 0.05  # max 5% of infrastructure damaged
    op_loss = estimate_operational_loss(
        balance_sheet.branch_replacement_cost_cr,
        physical_damage_frac,
        total_credit_portfolio_cr=balance_sheet.total_credit_portfolio_cr,
    )

    components = LossComponents(
        delta_ecl_cr=delta_ecl_cr,
        liquidity_draw_cr=liquidity_draw,
        market_loss_cr=market_loss,
        funding_cost_cr=funding_cost,
        op_loss_cr=op_loss,
    )

    logger.info(
        "Total Loss [%s]: ΔECLᵢₙ꜀=%.2f, Liquidity=%.2f, Market=%.2f, "
        "Funding=%.2f, Op=%.2f | TOTAL=%.2f INR cr.",
        balance_sheet.institution_id,
        components.delta_ecl_cr, components.liquidity_draw_cr,
        components.market_loss_cr, components.funding_cost_cr,
        components.op_loss_cr, components.total_cr,
    )
    return components
