import numpy as np

class HotHouseWorldEngine:
    """
    Implements the mathematical architecture for the 3C Hot House World Scenario,
    focusing on Asymmetric Copulas (WWR), uninsurability thresholds, and Empirical EDF.
    """
    
    def __init__(self, copula_theta=2.0, empirical_dampening=0.5):
        """
        Args:
            copula_theta (float): Parameter for Clayton copula. theta > 0.
                                  Higher theta implies stronger lower-tail dependence.
            empirical_dampening (float): Scalar to transform GDP shocks to Z-scores.
        """
        self.theta = copula_theta
        self.empirical_dampening = empirical_dampening

    def calculate_clayton_copula(self, u, v):
        """
        Calculates the joint probability of two marginals under lower-tail dependence.
        C^{Clayton}_{theta}(u, v) = [max(u^{-theta} + v^{-theta} - 1, 0)]^{-1/theta}
        """
        # Ensure inputs are bounds strictly away from 0 to prevent division by zero in power
        u = np.clip(u, 1e-8, 1.0)
        v = np.clip(v, 1e-8, 1.0)
        
        inner = np.power(u, -self.theta) + np.power(v, -self.theta) - 1.0
        inner = np.maximum(inner, 0.0)
        
        # If inner is 0, probability is 0
        result = np.where(inner > 0, np.power(inner, -1.0 / self.theta), 0.0)
        return result

    def calculate_wwr_multiplier(self, pd, p_damage):
        """
        Calculates the Wrong Way Risk (WWR) Multiplier.
        WWR_Multiplier = Copula(PD, P_Damage) / (PD * P_Damage)
        """
        joint_prob = self.calculate_clayton_copula(pd, p_damage)
        independent_prob = pd * p_damage
        independent_prob = np.clip(independent_prob, 1e-12, 1.0)
        return joint_prob / independent_prob

    def calculate_insurance_cover(self, climate_risk_score, uninsurability_threshold):
        """
        Models insurance decay. 
        If risk_score > threshold, insurance cover drops to 0. 
        Otherwise, it maintains full coverage (1.0) minus a decay proportional to risk.
        """
        # Simplistic decay: Drops linearly then zeroes out
        # Base cover = 1.0 (Fully insured against damage)
        cover = np.where(
            climate_risk_score >= uninsurability_threshold,
            0.0,
            1.0 - (climate_risk_score / uninsurability_threshold)**2
        )
        return np.clip(cover, 0.0, 1.0)

    def calculate_stressed_lgd(self, lgd_base, pd, p_damage, climate_risk_score, uninsurability_threshold):
        """
        Calculates LGD_{stressed} = min(1.0, LGD_{base} * WWR_Multiplier) * (1 - Insurance_Cover_t)
        Note: The formula in the report bounds loss at 1.0 BEFORE applying insurance mitigation.
        Wait, if insurance pays, LGD is reduced. If no insurance, LGD is the physical damage.
        Actually, the report: LGD_stressed = min(1.0, LGD_base * WWR_Multiplier) * (1 - Insurance_Cover)
        """
        wwr_multiplier = self.calculate_wwr_multiplier(pd, p_damage)
        gross_stressed_lgd = np.minimum(1.0, lgd_base * wwr_multiplier)
        
        insurance_cover = self.calculate_insurance_cover(climate_risk_score, uninsurability_threshold)
        net_lgd = gross_stressed_lgd * (1.0 - insurance_cover)
        
        return np.clip(net_lgd, 0.0, 1.0)

    def calculate_macro_drift_penalty(self, epsilon_nic, delta_gdp):
        """
        Macro_Drift_Penalty = 0.5 * (epsilon_NIC * |Delta GDP|)
        """
        return self.empirical_dampening * (epsilon_nic * np.abs(delta_gdp))

    def calculate_stressed_dd(self, dd_base, macro_drift, cear_drift, tcar_volatility):
        """
        DD_stressed = (DD_base - Macro_Drift - CEaR_Drift) / (1 + TCaR_Volatility)
        """
        return (dd_base - macro_drift - cear_drift) / (1.0 + tcar_volatility)

    def map_empirical_edf(self, dd_stressed):
        """
        Maps DD_stressed to PD_stressed using an empirical logistic EDF curve.
        Using a standard logistic approximation calibrated to emerging markets.
        Higher DD means lower PD. Lower DD means higher PD.
        Standard normal CDF approximation via logistic: 1 / (1 + exp(1.702 * DD))
        """
        # A robust logistic mapping for probability
        # 1.702 makes logistic approximate normal CDF closely
        return 1.0 / (1.0 + np.exp(1.702 * dd_stressed))

    def calculate_stressed_ecl(self, pd_stressed, lgd_stressed, ead):
        """
        ECL_Stressed = PD_stressed * LGD_stressed * EAD
        """
        return pd_stressed * lgd_stressed * ead

