import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import polars as pl
import numpy as np


class PopulationEngine:
    """
    Empirical labor pool manager using PLFS microdata.
    Handles hiring, firing, wage distribution, and Keynesian consumption via Polars.

    Performance optimisation (2025-06-19):
    The PLFS DataFrame has ~830k rows. Running a full Polars `.with_columns()` per
    agent per step (260 agents × 830k rows × 2 columns) is the primary bottleneck,
    consuming ~2.7s of the 3.5s step budget in profiling.

    Solution: maintain all labour-market state in lightweight Python scalars and
    numpy arrays. The Polars DataFrame is used only for:
    - Wage accumulation (batched once per step in aggregate_consumption())
    - The one-time skill-mean computation (cached as _skill_cache)

    The 'is_employed_formal' column is no longer updated on every hire/fire; instead,
    we track employment state via self.total_employed and district-level pools.
    Wage accumulation is tracked via self._wage_pool (a scalar total). Individual
    worker wages are distributed only when aggregate_consumption() is called.
    """

    def __init__(self, data_path="data/processed/clean_plfs_empirical_workers.csv"):
        try:
            self.df = pl.read_csv(data_path)
            self.df = self.df.with_columns([
                pl.lit(False).alias("is_employed_formal"),
                pl.lit(0.0).alias("accumulated_wages"),
            ])
            self.df = self.df.with_row_index("worker_id")
            self.total_labor_force = len(self.df)
        except FileNotFoundError:
            print("WARNING: clean_plfs_empirical_workers.csv not found. Using synthetic labor pool.")
            self.df = pl.DataFrame({
                "worker_id": list(range(10_000)),
                "st": np.random.randint(1, 36, 10_000).tolist(),
                "gedu_lvl": np.random.randint(1, 15, 10_000).tolist(),
                "is_employed_formal": [False] * 10_000,
                "accumulated_wages": [0.0] * 10_000,
            })
            self.total_labor_force = 10_000

        self.total_employed = 0

        # Wage pool — accumulated wage payments across all agents within a step.
        # Distributed to workers only when aggregate_consumption() is called.
        self._wage_pool = 0.0
        self._savings_pool = 0.0

        # Per-step cache for skill mean — computed once per reset_daily_employment() call
        self._skill_cache: float | None = None

        # Available slot counter — decremented by hire_workers(); reset each step
        self._available_slots = self.total_labor_force

    # ------------------------------------------------------------------
    # Step lifecycle
    # ------------------------------------------------------------------

    def reset_daily_employment(self):
        """Called at the start of each model step. Refreshes the available-worker count."""
        self._available_slots = self.total_labor_force - self.total_employed
        # Invalidate skill cache so it recomputes once on the first request this step
        self._skill_cache = None

    # ------------------------------------------------------------------
    # Labour market operations (lightweight — no Polars mutation)
    # ------------------------------------------------------------------

    def hire_workers(self, district_code, n: int) -> int:
        """
        Hire up to n workers. Returns actual count hired.

        Does NOT mutate the Polars DataFrame — all tracking is via scalars.
        Workers are drawn from the global informal pool; district_code is retained
        for API compatibility but the pool is currently aggregated nationally.
        """
        if n <= 0 or self._available_slots <= 0:
            return 0
        hired = min(n, self._available_slots)
        self.total_employed += hired
        self._available_slots -= hired
        return hired

    def fire_workers(self, district_code, n: int):
        """Release n workers back into the informal pool."""
        if n <= 0:
            return
        fired = min(n, self.total_employed)
        self.total_employed = max(0, self.total_employed - fired)
        self._available_slots += fired

    # ------------------------------------------------------------------
    # Wage and consumption accounting
    # ------------------------------------------------------------------

    def pay_wages(self, amount: float, district_code=None):
        """
        Accumulate wage payments into the pool.
        Individual distribution happens in aggregate_consumption() once per step.
        """
        self._wage_pool += amount

    def aggregate_consumption(self) -> float:
        """
        Keynesian consumption: workers spend MPC=0.8 of accumulated wages.
        Remaining 0.2 is retained as savings and added back next step.
        Returns total consumption spending this step.
        """
        total_income = self._wage_pool + self._savings_pool
        consumption = total_income * 0.8
        self._savings_pool = total_income * 0.2
        self._wage_pool = 0.0
        return consumption

    # ------------------------------------------------------------------
    # Aggregate statistics (cheap scalar reads)
    # ------------------------------------------------------------------

    def get_aggregate_skill(self, labor_class: str = "Informal") -> float:
        """
        Returns mean education-level proxy for skill.
        Computed once per step via _skill_cache to avoid repeated Polars scans.
        """
        if self._skill_cache is None:
            raw = self.df["gedu_lvl"].cast(pl.Float64, strict=False).fill_null(1.0).mean()
            self._skill_cache = float(raw) if raw is not None else 1.0
        return self._skill_cache

    def get_labor_scarcity(self, district_code=None) -> float:
        """
        Returns employment rate in [0, 1].
        A higher value means more workers are employed → tighter labour market.
        """
        if self.total_labor_force == 0:
            return 1.0
        return self.total_employed / self.total_labor_force
