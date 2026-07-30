"""
conftest.py — pytest fixtures for the FCRM test suite.

Fast mocking of the computationally expensive BIC calibration bootstrapper
so that unit tests that exercise the CEaR/TCaR pipeline run in seconds.
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd


@pytest.fixture(autouse=True)
def mock_elasticity_tensor(monkeypatch):
    """
    Patch `build_nic5_elasticity_tensor` and `calibrate_2digit_elasticities`
    with a lightweight precomputed mock so tests do not trigger the 67-sector
    BIC polynomial search (which takes ~5 minutes in full).
    """
    import fcrm.satellite.elasticity_calibrator as ec

    # Fast mock: return a minimal DataFrame for any NIC4/NIC2 query
    def _fast_tensor():
        records = []
        for nic2 in range(1, 100):
            for i in range(3):
                records.append({
                    "nic4": nic2 * 100 + i * 10,
                    "nic2": nic2,
                    "eta_T": -0.015,
                    "eta_P": -0.007,
                })
        return pd.DataFrame(records)

    def _fast_2digit():
        return {nic2: (-0.015, -0.007) for nic2 in range(1, 100)}

    monkeypatch.setattr(ec, "build_nic5_elasticity_tensor", _fast_tensor)
    monkeypatch.setattr(ec, "calibrate_2digit_elasticities", _fast_2digit)

    # Also patch the cear module's reference
    import fcrm.satellite.cear as cear_mod
    monkeypatch.setattr(cear_mod, "build_nic5_elasticity_tensor", _fast_tensor)
