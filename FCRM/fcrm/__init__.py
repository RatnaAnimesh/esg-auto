"""
FCRM – Full Climate Risk Model
Top-level package for the NSRAL Climate Stress Testing Engine.

Module hierarchy:
    fcrm.config            – Constants and NGFS scenario parameters
    fcrm.data.*            – External data loaders (NGFS, MoSPI, PCAF, yfinance, MCA)
    fcrm.macro.*           – Macroeconomic transmission layer (Leontief, DTVF)
    fcrm.satellite.*       – CEaR and TCaR satellite models
    fcrm.credit.*          – Basel A-IRB Merton credit engine
    fcrm.institutional.*   – CET1 capital degradation and total loss aggregation
"""

from fcrm.config import NGFSScenario, EngineConfig

__all__ = ["NGFSScenario", "EngineConfig"]
