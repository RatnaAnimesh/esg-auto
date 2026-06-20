import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import mesa
import numpy as np
import networkx as nx

# CBAM covers only iron/steel, aluminium, cement, fertilisers, electricity, hydrogen.
# EU CBAM Reg. 2023/956. NIC 2-digit codes for covered sectors:
#   20 = Manufacture of chemicals (fertilisers sub-sector)
#   23 = Manufacture of other non-metallic mineral products (cement)
#   24 = Manufacture of basic metals (steel, aluminium)
CBAM_COVERED_NIC = frozenset({20, 23, 24})

# Annual physical capital depreciation rate. 10-year asset life (straight-line proxy).
# Applied per simulation step (day): delta_daily = 1 / (365 * 10)
DEPRECIATION_RATE_DAILY = 1.0 / (365 * 10)

# Zeta calibration target: ~1 innovation event per MSME per simulated year (365 steps).
# With median RD_budget ~2500 INR:  zeta = -ln(1 - 1/365) / 2500 ≈ 1.1e-6
# Source: K+S original calibration (Dosi, Fagiolo & Roventini 2010), adapted for
# rupee-denominated budgets at this scale.
ZETA_RD = 1.1e-6

# Carbon pricing calibration (all in INR/tonne CO2):
#   India CCTS initial price: ₹800/tonne — midpoint of ₹600–1,000/tonne BEE/CarbonNeeti 2025-26 range.
#   EU CBAM in INR: €80 × EUR/INR 84 (2024 annual average) ≈ ₹6,720/tonne.
INDIA_CCTS_INITIAL = 800.0
EU_CBAM_INITIAL_INR = 6720.0  # Converted from €80 at 2024 average EUR/INR 84

# Wage calibration (INR/day):
#   Blue-Collar: ₹500 plausible for formal manufacturing (PLFS 2023-24)
#   Informal: ₹300 — midpoint of ₹225–401 casual/informal salaried range (PLFS 2022-23)
WAGE_BLUE_COLLAR = 500.0
WAGE_INFORMAL = 300.0


class CorporateAgent(mesa.Agent):
    """
    An empirical agent representing a listed company or MSME cluster.

    Tier-1: Listed BRSR companies (consumption-good producers, K+S Sector 2).
    Tier-3: MSME clusters (capital-good / intermediate suppliers, K+S Sector 1).
    """

    def __init__(self, model, region, tier, initial_capital, carbon_intensity, nic_code,
                 company_name, district_code=None, carbon_deficit_theta=1.0,
                 workers_per_unit=0, scaling_multiplier=1):
        super().__init__(model)
        self.region = region
        self.tier = tier
        self.capital = initial_capital
        self.carbon_intensity = carbon_intensity * carbon_deficit_theta
        self.nic_code = nic_code
        self.company_name = company_name

        # district_code must be set externally from empirical data.
        # A None here is a programming error that will surface quickly.
        self.district_code = district_code

        # MSME-specific attributes (K+S Sector 1: Capital/Intermediate Suppliers)
        self.carbon_deficit_theta = carbon_deficit_theta
        self.workers_per_unit = workers_per_unit
        self.scaling_multiplier = scaling_multiplier
        # Compliance cost is the annual regulatory filing burden.
        # Tier-3 (MSME): GST filing + basic environmental compliance = ~₹5,000/yr
        # Tier-1 (Listed): BRSR + CSDDD due diligence = ~₹100,000/yr
        # Source: MSME Ministry compliance burden estimates (2022)
        self.compliance_cost = 5_000 if tier == "Tier-3" else 100_000

        # Working capital runway: secondary bankruptcy indicator only.
        # Primary trigger is capital < 0. Runway counts consecutive days of zero production.
        self.working_capital_runway = 90 if tier == "Tier-3" else float('inf')

        # K+S Sector 1 (MSME) tech variables
        self.vintage_A = 1.2               # Productivity of machines they sell
        self.vintage_epsilon = self.carbon_intensity
        self.msme_productivity_B = np.random.uniform(1.0, 2.0)
        self.brochure_price = 0.0
        self.RD_budget = 0.0
        self.sales_history = 0.0

        # K+S Sector 2 (Listed) market variables
        self.market_share_f = 0.0
        self.backlog_l = 0.0
        self.competitiveness_E = 0.0
        self.demand_D = 0.0
        self.capacity_Y = 0.0
        self.current_vintage_A = 1.2
        self.current_vintage_epsilon = self.carbon_intensity

        # Per-firm price (markup over unit labor cost). Initialized to a plausible value;
        # updated each step via the markup rule.
        self.markup_mu = 0.20
        self.price = 100.0

        self.is_bankrupt = False

        # Production capabilities
        self.technology_a = 1.2
        # Physical capital in production units. Depreciated each step; increased by
        # machine purchases from MSME suppliers.
        self.physical_capital_k = np.random.uniform(10, 100) if tier == "Tier-1" else np.random.uniform(1, 10)
        self.daily_production = 0.0
        self.inventory = 0.0

        # Supply chain
        self.suppliers = []
        self.required_supplier_count = 0
        self.supplier_cooldown = 0

        # Zero-production streak counter (secondary bankruptcy indicator)
        self._zero_production_days = 0

    @property
    def compliance_fragility(self):
        """CF = Compliance Cost / Capital. Higher = more fragile."""
        if self.capital <= 0:
            return float('inf')
        return self.compliance_cost / self.capital

    def step(self):
        if self.is_bankrupt:
            return

        # Depreciate physical capital each day (10-year asset life)
        self.physical_capital_k = max(0.1, self.physical_capital_k * (1 - DEPRECIATION_RATE_DAILY))

        # Supplier cooldown countdown for re-sourcing
        if self.supplier_cooldown > 0:
            self.supplier_cooldown -= 1

        # --- K+S Sector 1: MSME R&D Innovation ---
        if self.tier == "Tier-3" and self.region == "India":
            nu = 0.05
            self.RD_budget = nu * self.sales_history

            # ZETA_RD calibrated so ~1 innovation per firm per simulated year.
            # See module constant for derivation.
            prob_innovate = 1.0 - np.exp(-ZETA_RD * self.RD_budget)
            if np.random.random() < prob_innovate:
                self.vintage_A *= np.random.uniform(1.0, 1.05)
                self.vintage_epsilon *= np.random.uniform(0.95, 1.0)

            # Brochure price: markup over unit labor cost
            base_wage = WAGE_INFORMAL
            unit_labor_cost = base_wage / max(0.01, self.msme_productivity_B)
            self.brochure_price = (1 + self.markup_mu) * unit_labor_cost

        # --- Supply health check (Tier-1 India only) ---
        supply_health = 1.0
        if self.tier == "Tier-1" and self.region == "India":
            if self.required_supplier_count > 0:
                supply_health = len(self.suppliers) / self.required_supplier_count
                if supply_health < 1.0 and self.supplier_cooldown == 0:
                    # Re-sourcing cooldown is set by model.py after supplier replacement
                    # using LEADS friction. Here we set a temporary placeholder.
                    self.supplier_cooldown = 30

        # --- Wage Bargaining and Hiring ---
        if self.region == "India":
            labor_class = "Blue-Collar" if self.tier == "Tier-1" else "Informal"
            skill_h = self.model.population.get_aggregate_skill(labor_class)
            scarcity = self.model.population.get_labor_scarcity(self.district_code)

            base_wage = WAGE_BLUE_COLLAR if labor_class == "Blue-Collar" else WAGE_INFORMAL
            wage_demanded = base_wage * skill_h * (1.0 + scarcity)

            # Daily payroll budget: 0.1% of capital — a firm shouldn't spend more than
            # ~1/1000 of its capital on a single day's wage bill. At PLFS-calibrated wages,
            # a ₹50k MSME can hire ~1-2 workers/day.
            daily_payroll_budget = self.capital * 0.001
            desired_workers = int(daily_payroll_budget / max(1.0, wage_demanded))
            
            # Ensure at least 1 worker is hired if they have the capital for it, 
            # otherwise tiny MSMEs never produce.
            if desired_workers == 0 and self.capital >= wage_demanded:
                desired_workers = 1

            workers_hired = self.model.population.hire_workers(self.district_code, desired_workers)

            if workers_hired > 0:
                actual_wage_bill = workers_hired * wage_demanded
                self.capital -= actual_wage_bill
                self.model.population.pay_wages(actual_wage_bill)

                effective_labor = skill_h * workers_hired
                raw_production = (
                    self.technology_a
                    * (self.physical_capital_k ** 0.3)
                    * (effective_labor ** 0.7)
                )
                self.daily_production = raw_production * supply_health
                self.inventory += self.daily_production

                # Update firm price from this step's unit labor cost
                if self.daily_production > 0:
                    unit_cost = actual_wage_bill / self.daily_production
                    self.price = (1 + self.markup_mu) * unit_cost
            else:
                self.daily_production = 0.0

        else:
            # EU agents: simplified production without labor market
            self.daily_production = self.technology_a * (self.physical_capital_k ** 0.3) * (10 ** 0.7)
            self.inventory += self.daily_production

        # --- Daily Fixed Operational Costs ---
        # Deduct a daily proportion of the annual compliance cost to simulate drag,
        # plus a fixed baseline operating expense (rent, utilities) to induce realistic
        # 5-8% bankruptcy rates for unproductive firms over a 365-day period.
        if self.region == "India":
            base_opex = 100.0 if self.tier == "Tier-3" else 1000.0
            self.capital -= ((self.compliance_cost / 365.0) + base_opex)

        # --- Sell inventory and update capital ---
        self.sell_inventory()

        # --- Update capacity for replicator dynamics (Tier-1 only) ---
        if self.tier == "Tier-1":
            self.capacity_Y = self.daily_production

        # --- Bankruptcy checks ---
        # Primary: capital < 0 (liquidity exhaustion)
        if self.capital < 0:
            self.bankrupt()
            return

        # Secondary: prolonged zero production AND capital below operating threshold
        if self.daily_production == 0:
            self._zero_production_days += 1
            if (self._zero_production_days >= 90
                    and self.capital < self.compliance_cost
                    and self.tier == "Tier-3"):
                self.bankrupt()
        else:
            self._zero_production_days = 0

    def sell_inventory(self):
        """
        Compute sales revenue and apply CBAM liability.

        CBAM applies only to:
        - Tier-1 (listed) exporters in India
        - NIC codes covered by EU CBAM Reg. 2023/956: metals (24), cement (23), fertilisers (20)

        MSMEs (Tier-3) do not export directly to EU and are not CBAM-liable here.
        CBAM cost pressure on MSMEs is transmitted indirectly via Tier-1 supplier
        switching (payback period evaluation in model.py).
        """
        import random
        if self.region == "India":
            # Stochastic demand constraint (clearance rate)
            # MSMEs (Tier-3) face higher demand uncertainty than Listed firms.
            if self.tier == "Tier-3":
                clearance = random.uniform(0.65, 1.0)
            else:
                clearance = random.uniform(0.85, 1.0)

            total_sales = self.inventory * clearance
            domestic_sales = total_sales * 0.5
            export_sales = total_sales * 0.5

            eu_agent = self.model.get_government("EU")
            india_agent = self.model.get_government("India")

            # CBAM liability: only Tier-1 exporters in covered sectors
            is_cbam_liable = (
                self.tier == "Tier-1"
                and self.nic_code in CBAM_COVERED_NIC
            )

            if is_cbam_liable:
                cbam_gross = self.carbon_intensity * eu_agent.cbam_price
                domestic_credit = self.carbon_intensity * india_agent.ccts_price
                net_cbam_per_unit = max(0.0, cbam_gross - domestic_credit)
                tax_bill = export_sales * net_cbam_per_unit
                eu_agent.collect_tax(tax_bill)
            else:
                tax_bill = 0.0

            export_revenue = export_sales * self.price
            domestic_revenue = domestic_sales * self.price

            self.sales_history = export_revenue + domestic_revenue
            self.capital += export_revenue - tax_bill + domestic_revenue
            self.inventory = 0.0

            # Green investment: high-capital, high-intensity Tier-1 firms invest in abatement
            if self.capital > 500_000 and self.carbon_intensity > 1.0 and self.tier == "Tier-1":
                investment = 50_000
                self.capital -= investment
                self.carbon_intensity = max(0.1, self.carbon_intensity - 0.05)

        else:
            # EU agents: simple domestic sale
            self.capital += self.inventory * self.price
            self.inventory = 0.0

    def bankrupt(self):
        if self.is_bankrupt:
            return
        self.is_bankrupt = True
        self.model.total_bankruptcies += 1
        if self.tier == "Tier-3":
            self.model.msme_bankruptcies += 1
            # Fire workers into the informal pool (labor market shock)
            workers_to_fire = max(1, int(self.workers_per_unit * self.scaling_multiplier / 10_000))
            self.model.population.fire_workers(self.district_code, workers_to_fire)


class GovernmentAgent(mesa.Agent):
    """
    Macro-agent representing the central authority of a region.
    Manages carbon pricing and fiscal policy.

    Carbon prices are in INR/tonne CO2:
    - India CCTS: starts at ₹800/tonne (BEE / CarbonNeeti 2025-26 midpoint)
    - EU CBAM: starts at ₹6,720/tonne (€80 × EUR/INR 84, 2024 average)
    """

    def __init__(self, model, region):
        super().__init__(model)
        self.region = region
        self.tax_revenue = 0.0

        if region == "India":
            self.cbam_price = 0.0
            self.ccts_price = INDIA_CCTS_INITIAL
        else:
            # EU: cbam_price is the CBAM levy in INR/tonne; ccts_price unused
            self.cbam_price = EU_CBAM_INITIAL_INR
            self.ccts_price = 0.0

    def collect_tax(self, amount):
        self.tax_revenue += amount
        if self.region == "EU":
            self.model.total_capital_flight += amount

    def step(self):
        # Use model.day_count (not mesa's self.steps) for policy timing
        day = self.model.day_count

        if self.region == "India":
            # CCTS price escalation: India gradually closes gap with EU CBAM.
            # Trigger: capital flight > ₹1M signals EU cost pressure.
            # Rate: +₹1/tonne per step until parity (slow escalation).
            if self.model.total_capital_flight > 1_000_000:
                eu_agent = self.model.get_government("EU")
                if self.ccts_price < eu_agent.cbam_price:
                    self.ccts_price += 1.0

            # Annual PLI subsidy: production-linked, targeted at MSMEs (Tier-3).
            # PLI scales with output above prior period average, not PageRank centrality.
            if day > 0 and day % 365 == 0:
                active_msmes = [
                    a for a in self.model.msme_agents if not a.is_bankrupt
                ]
                if active_msmes:
                    subsidy_pool = 50_000_000  # ₹5 Cr per year total pool
                    subsidy_per_msme = subsidy_pool / len(active_msmes)
                    for msme in active_msmes:
                        # Production-linked: multiplier based on recent output ratio
                        avg_daily_output = msme.sales_history / max(1.0, 365 * msme.price)
                        output_multiplier = max(0.5, min(2.0, msme.daily_production / max(0.1, avg_daily_output)))
                        msme.capital += subsidy_per_msme * output_multiplier

        elif self.region == "EU":
            # EU CBAM ramp: +₹420/tonne per year (≈ €5/yr × EUR/INR 84).
            # Full financial phase started Jan 2026; modelled as active from simulation start.
            if day > 0 and day % 365 == 0:
                self.cbam_price += 420.0  # ₹420 ≈ €5 annual ramp at EUR/INR 84
