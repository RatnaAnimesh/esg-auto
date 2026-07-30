# FCRM — Full Climate Risk Model

**Developed by:** NSRAL (NSE Sustainability Ratings and Analytics Ltd.)

A Python implementation of the NSRAL Full Climate Risk Model (FCRM) — a
Basel A-IRB aligned, NGFS Phase 4 compliant, structural climate stress testing
engine for the Indian banking sector.

---

## Architecture

The engine is organized as four sequential analytical modules:

```
FCRM Engine
│
├── fcrm.macro          Section 1 — Supply Chain Contagion
│   ├── leontief.py     Leontief I/O inversion: L = (I-A)⁻¹, δ = γᵀL  [Eq. 1-2]
│   └── dtvf.py         Dynamic Transition Vulnerability Factor ε_NIC,t  [Eq. 3]
│
├── fcrm.satellite      Section 2 — Financial Vulnerability Satellites
│   ├── elasticity_calibrator.py  BIC-minimized polynomial OLS calibration [Eq. 5-7]
│   ├── ras_entropy.py  Cross-entropy RAS information-theoretic scaler     [Eq. 8-9]
│   ├── cear.py         Climate Earnings-at-Risk: 1 - exp(η_T|ΔT|+η_P|ΔP|) [Eq. 4]
│   └── tcar.py         Transition Cost-at-Risk via PCAF emission imputation [Eq. 10-12]
│
├── fcrm.credit         Section 3 — Basel A-IRB Structural Credit Engine
│   ├── merton.py       Merton BS inversion: Powell root-finding           [Eq. 14-17]
│   ├── kmv_edf.py      KMV Logistic EDF manifold + tail thickener        [Sec. 3.1]
│   ├── stress_injection.py  DD_stressed + PD_stressed                     [Eq. 18-20]
│   ├── clayton_copula.py   Asymmetric Clayton WWR + stressed LGD         [Eq. 21-23]
│   └── ecl.py          ECL + Basel A-IRB capital requirement K(PD, LGD) [Eq. 24-26]
│
├── fcrm.institutional  Section 4 — CET1 Capital Degradation
│   ├── total_loss.py   Five-component loss aggregation ΔECLᵢₙ꜀+Liq+Mkt+Fund+Op [Eq. 27]
│   └── cet1.py         CET1 stressed ratio + RWA inflation r_inf          [Eq. 25-26]
│
├── fcrm.data           Data Loaders
│   ├── ngfs_loader.py  NGFS Phase 4 API (IIASA) + fallback trajectories
│   ├── mospi_loader.py MoSPI SUT 67×67 A-matrix + ASI factor intensities
│   ├── pcaf_loader.py  PCAF emission imputation (5-tier hierarchy)
│   ├── equity_loader.py yfinance NSE equity data for Merton inversion
│   └── mca_loader.py   MCA structural weights for RAS optimizer
│
├── fcrm.pipeline       End-to-end orchestrator
└── fcrm.config         NGFS scenarios, Basel constants, NIC mappings
```

## Quickstart

```bash
pip install -e ".[dev]"
```

```python
from fcrm.pipeline import run_full_stress_test, BorrowerInput
from fcrm.config import NGFSScenario, EngineConfig
from fcrm.institutional.cet1 import InstitutionalBalanceSheet

# 1. Define your borrowers (see tests/ for a full example)
borrowers = [...]

# 2. Define the bank balance sheet
bank = InstitutionalBalanceSheet(
    institution_id="SBI",
    cet1_capital_base_cr=45_000,
    rwa_base_cr=450_000,
    treasury_portfolio_cr=80_000,
    total_credit_portfolio_cr=400_000,
    total_undrawn_commitments_cr=120_000,
    wholesale_funding_cr=90_000,
    branch_replacement_cost_cr=25_000,
)

# 3. Run the stress test
results = run_full_stress_test(
    borrowers=borrowers,
    balance_sheet=bank,
    scenario=NGFSScenario.DELAYED_TRANSITION,
    years=list(range(2025, 2051)),
)

# 4. Inspect CET1 trajectory
for r in results:
    print(r.year, r.institutional_result.cet1_stressed)
```

## Tests

```bash
# Fast unit tests only
pytest tests/ -m "not slow" -v

# Full test suite including integration tests
pytest tests/ -v
```

## Data Sources

| Module | Source | Fallback |
|--------|--------|---------|
| NGFS carbon prices | IIASA NGFS Phase 4 API | Hardcoded REMIND-MAgPIE headline values |
| NGFS temperature anomalies | IIASA MAGICC 7.5.3 | IPCC AR6 linear ramp |
| MoSPI SUT (67×67) | MoSPI official portal | Synthetic structural-prior matrix |
| ASI factor intensities | Zenodo record 7493834 | Synthetic Dirichlet priors |
| MCA structural weights | MCA open data portal | Synthetic Dirichlet priors |
| NSE equity data | yfinance (live) | Calibrated fallback μ_DD=4.2, σ_DD=2.1 |
| PCAF emission intensities | PCAF Global Standard v2.5 | NIC-coded sector averages |

## Key Mathematical References

All equations refer to the NSRAL Climate Risk Model Report (2024):

| Equation | Description |
|----------|-------------|
| Eq. 1 | Leontief inverse L = (I-A)⁻¹ |
| Eq. 2 | Supply chain contagion δ = γᵀL |
| Eq. 3 | DTVF: ε_NIC,t = ε_base + (γ+δ) × ln(1+P_carbon,t) |
| Eq. 4 | CEaR ratio = 1 - exp(-(η_T×ΔT + η_P×|ΔP|)) |
| Eq. 5 | Panel GVA model with BIC-minimized polynomial OLS |
| Eq. 6-7 | Micro-allocation of η to 5-digit NIC via ASI factor intensities |
| Eq. 8-9 | RAS cross-entropy KL-divergence minimization |
| Eq. 10-12 | TCaR: emission imputation, θ_NIC CAPEX, unhedged transition liability |
| Eq. 13 | Dynamic Default Point: DP = STD + 0.5×LTD |
| Eq. 14-16 | Merton option equations (V, σ_V simultaneous system) |
| Eq. 17 | DD_base = [ln(V/DP) + (r - 0.5σ_V²)T] / (σ_V√T) |
| Eq. 18-20 | Stress injection: macro drift, CEaR drift, TCaR volatility penalty |
| Eq. 21-23 | Clayton copula WWR, multiplier, stressed LGD |
| Eq. 24 | ECL_stressed = PD × LGD × EAD |
| Eq. 25 | CET1_stressed = (CET1_base - Loss_Total) / (RWA×(1+r_inf)) |
| Eq. 26 | RWA inflation rate r_inf |
| Eq. 27 | Loss_Total = ΔECLᵢₙ꜀ + Liquidity + Market + Funding + Op |
