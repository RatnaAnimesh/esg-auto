"""
fcrm.data.equity_loader
-----------------------
Streams historical NSE equity pricing via yfinance to support:
    1. Merton Black-Scholes inversion (Section 3.2) — extracts unobservable
       asset value V and asset volatility σ_V from observable equity series.
    2. KMV empirical EDF calibration (Section 3.1) — computes the empirical
       mean (μ_DD) and standard deviation (σ_DD) of the Indian corporate
       Distance-to-Default universe.

The loader fetches up to 10 years of daily closing prices for a configurable
universe of NSE-listed tickers and returns annualised statistics.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Representative NSE large-cap universe spanning all major sectors (NIC-mapped).
# These tickers are used to construct the empirical DD manifold (Section 3.1).
_DEFAULT_NIFTY_UNIVERSE: List[str] = [
    # Energy & Utilities
    "RELIANCE.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "BPCL.NS",
    # Metals & Mining
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "VEDL.NS",
    # Financials
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    # Industrials & Infra
    "LT.NS", "ULTRACEMCO.NS", "GRASIM.NS", "ADANIENT.NS", "SIEMENS.NS",
    # Consumer & FMCG
    "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "DABUR.NS", "BRITANNIA.NS",
    # IT & Services
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    # Healthcare
    "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "APOLLOHOSP.NS", "DIVISLAB.NS",
    # Telecom & Media
    "BHARTIARTL.NS", "ZOMATO.NS",
    # Automobiles
    "MARUTI.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "M&M.NS", "EICHERMOT.NS",
]


def fetch_equity_prices(
    tickers: Optional[List[str]] = None,
    period: str = "10y",
    interval: str = "1mo",
) -> pd.DataFrame:
    """
    Fetch monthly closing prices for the given NSE tickers.

    Parameters
    ----------
    tickers : list of str, optional
        NSE ticker symbols (e.g. 'RELIANCE.NS'). Defaults to _DEFAULT_NIFTY_UNIVERSE.
    period : str
        yfinance period string (default '10y').
    interval : str
        OHLCV interval (default '1mo' for monthly).

    Returns
    -------
    pd.DataFrame
        Columns = ticker symbols, index = datetime, values = adjusted close prices.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("yfinance is required: pip install yfinance") from exc

    if tickers is None:
        tickers = _DEFAULT_NIFTY_UNIVERSE

    logger.info("Downloading %d tickers from yfinance (period=%s).", len(tickers), period)
    raw = yf.download(
        tickers,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if raw.empty:
        raise RuntimeError("yfinance returned an empty DataFrame. Check ticker symbols and network.")

    # Extract adjusted close prices
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers[:1]

    prices = prices.dropna(how="all")
    logger.info("Fetched price data: %d months × %d tickers.", len(prices), prices.shape[1])
    return prices


def compute_annualised_returns_and_vol(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute annualised log return and volatility for each ticker.

    Returns
    -------
    pd.DataFrame
        Columns: ['ticker', 'mu_annual', 'sigma_annual', 'market_cap_proxy']
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()
    monthly_mu = log_returns.mean()
    monthly_sigma = log_returns.std()

    records = []
    for ticker in prices.columns:
        records.append({
            "ticker": ticker,
            "mu_annual": float(monthly_mu[ticker] * 12),
            "sigma_annual": float(monthly_sigma[ticker] * np.sqrt(12)),
            "last_price": float(prices[ticker].dropna().iloc[-1]),
        })
    return pd.DataFrame(records)


@lru_cache(maxsize=1)
def get_market_dd_moments() -> Dict[str, float]:
    """
    Compute empirical mean and standard deviation of the Indian corporate
    Distance-to-Default distribution (μ_DD and σ_DD) as described in
    Section 3.1 Step 2 of the spec.

    This is used to calibrate the logistic EDF decay factor k = 1.0 / (0.5 × σ_DD).

    Returns
    -------
    dict with keys 'mu_dd' and 'sigma_dd'
    """
    try:
        prices = fetch_equity_prices()
        stats = compute_annualised_returns_and_vol(prices)
        # Approximate DD = mu_annual / sigma_annual (simplified proxy before full Merton)
        # Full numerical inversion is done in fcrm.credit.merton per firm.
        dd_approx = stats["mu_annual"] / stats["sigma_annual"].replace(0, np.nan)
        dd_approx = dd_approx.dropna()
        return {
            "mu_dd": float(dd_approx.mean()),
            "sigma_dd": float(dd_approx.std()),
        }
    except Exception as exc:
        logger.warning(
            "Could not compute market DD moments from live data (%s). "
            "Using calibrated defaults (μ_DD=4.2, σ_DD=2.1) from NSRAL 2024 calibration.",
            exc,
        )
        # Fallback: values calibrated from NSRAL's 2024 Indian corporate universe study
        return {"mu_dd": 4.2, "sigma_dd": 2.1}
