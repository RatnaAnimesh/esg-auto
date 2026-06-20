import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import math
import mesa
import pandas as pd
import polars as pl
import networkx as nx
import random
from src.arch_corporate.agents import CorporateAgent, GovernmentAgent, WAGE_BLUE_COLLAR, WAGE_INFORMAL
from src.arch_corporate.population import PopulationEngine

try:
    from src.extraction_pipeline.empirical_proxies import leads_scores
except Exception:
    leads_scores = {}

# K+S brochure count: each capital-good firm (MSME) sends brochures to at most Z buyers
# per step. Consistent with Dosi, Fagiolo & Roventini (2010) original protocol.
KS_BROCHURE_COUNT = 5

# Payback threshold: accept new supplier if payback period <= 3 years (K+S standard).
PAYBACK_YEARS_THRESHOLD = 3.0

# Re-sourcing cooldown bounds (days). Modulated by LEADS logistics score.
COOLDOWN_MIN_DAYS = 7
COOLDOWN_MAX_DAYS = 90

# Spatial distance decay. gamma=2.0 on [0,1] normalized distances gives exp(-2*0.5)=0.37
# for a mid-range pair — reasonable brochure arrival probability.
SPATIAL_GAMMA = 2.0


class IndiaEUMacroModel(mesa.Model):
    """
    India-EU K+S Macro ABM with CBAM/CCTS carbon pricing channel.

    Sector 1 (Capital Goods): MSME clusters — produce machines/intermediates,
    set brochure prices, innovate via R&D.
    Sector 2 (Consumption Goods): Listed Indian corporates — buy machines,
    produce final goods, compete via replicator dynamics on price + backlog.
    """

    def __init__(self, n_eu=200, formalized_msmes=None):
        super().__init__()
        self.my_agents = []

        # day_count is the model's own step counter.
        # Mesa's self.steps is managed internally by Mesa — do NOT shadow it.
        self.day_count = 0

        # Global macro tracking
        self.total_capital_flight = 0.0
        self.total_bankruptcies = 0
        self.msme_bankruptcies = 0

        # Set of bankrupt MSMEs already processed for replacement (entry dynamics)
        self._replaced_bankrupts = set()

        # Labor pool (PLFS-backed)
        self.population = PopulationEngine()

        # Governments
        self.gov_india = GovernmentAgent(self, "India")
        self.my_agents.append(self.gov_india)
        self.gov_eu = GovernmentAgent(self, "EU")
        self.my_agents.append(self.gov_eu)

        # Supply chain network
        self.supply_chain = nx.DiGraph()

        STATE_CODE_MAP = {
            "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
            "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
            "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
            "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
            "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
            "25": "Daman & Diu", "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
            "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
            "34": "Puducherry", "35": "Andaman & Nicobar Islands", "36": "Telangana"
        }

        # Load ASUSE empirical agent data
        try:
            full_df = pd.read_csv("data/processed/clean_asuse_empirical_agents.csv", low_memory=False)
        except FileNotFoundError:
            print("Warning: ASUSE agents not found. Using minimal synthetic fallback.")
            full_df = pd.DataFrame([{
                "value_rs": 1_000_000, "major_nic_2dig": 24, "fsu_serial_no": 1, "District": 1, "st": "27"
            }])

        # Build inter-district distance table from logistics GraphML + state-level path lengths.
        # Distances are normalized to [0,1] before the spatial brochure lottery so that
        # SPATIAL_GAMMA=2.0 produces meaningful probabilities.
        try:
            logistics_g = nx.read_graphml("data/processed/india_abstract_highways.graphml")
            path_lengths = dict(
                nx.all_pairs_dijkstra_path_length(logistics_g, weight="distance_km")
            )
        except Exception as e:
            print(f"GraphML load error: {e}. Using fallback distances.")
            path_lengths = {}

        dist_data = self._build_distance_table(full_df, path_lengths, STATE_CODE_MAP)
        self.distances_df = pl.DataFrame(dist_data)

        # Normalize distances to [0,1] for spatial gamma calibration
        if len(self.distances_df) > 0:
            max_dist = self.distances_df["dist"].max()
            if max_dist > 0:
                self.distances_df = self.distances_df.with_columns(
                    (pl.col("dist") / max_dist).alias("dist_norm")
                )
            else:
                self.distances_df = self.distances_df.with_columns(
                    pl.lit(0.0).alias("dist_norm")
                )
        else:
            self.distances_df = pl.DataFrame({
                "c_district": ["1"], "m_district": ["1"], "dist": [0.0], "dist_norm": [0.0]
            })

        # Convert to dict for O(1) lookups inside the hot brochure matching loop
        self._dist_norm_lookup: dict[tuple[str, str], float] = {
            (row["c_district"], row["m_district"]): row["dist_norm"]
            for row in self.distances_df.to_dicts()
        }

        # Keep ASUSE full_df for entry dynamics (replacement draws)
        self._asuse_df = full_df

        self.listed_agents = []
        self.msme_agents = []

        # Listed BRSR companies (Sector 2 — consumption-good producers)
        df_listed = full_df.sample(n=min(50, len(full_df)))
        for idx, row in df_listed.iterrows():
            district = str(row.get("District", 1))
            annual_output = float(row.get("value_rs", 5_000_000))
            # Listed companies: 6 months working capital from annual output
            initial_capital = max(2_000_000, annual_output / 2)
            
            # Force at least half of the listed firms into a CBAM-covered sector (24)
            # to ensure the capital flight channel is active in simulations.
            nic_code = 24 if len(self.listed_agents) < 25 else int(row.get("major_nic_2dig", 24))
            
            a = CorporateAgent(
                model=self,
                region="India",
                tier="Tier-1",
                initial_capital=initial_capital,
                carbon_intensity=1.2,
                nic_code=nic_code,
                company_name=f"Listed_{row.get('fsu_serial_no', idx)}",
                district_code=district,
            )
            self.my_agents.append(a)
            self.supply_chain.add_node(a)
            self.listed_agents.append(a)

        if self.listed_agents:
            uniform_share = 1.0 / len(self.listed_agents)
            for buyer in self.listed_agents:
                buyer.market_share_f = uniform_share

        # MSME clusters (Sector 1 — capital-good / intermediate suppliers)
        if formalized_msmes is not None:
            print(f"Loading {len(formalized_msmes)} formalized MSMEs from informal architecture...")
            for fa in formalized_msmes:
                nic_map = {"Manufacturing": 24, "Trade": 47, "Other Services": 62}
                nic = nic_map.get(fa.sector, 24)
                district = str(abs(hash(fa.state)) % 640 + 1)
                a = CorporateAgent(
                    model=self,
                    region="India",
                    tier="Tier-3",
                    initial_capital=max(10_000, float(fa.turnover)),
                    carbon_intensity=1.5,
                    nic_code=nic,
                    company_name=f"Formalized_{fa.agent_id}",
                    district_code=district,
                    carbon_deficit_theta=1.0,
                    workers_per_unit=fa.workers,
                    scaling_multiplier=fa.mlt,
                )
                self.my_agents.append(a)
                self.supply_chain.add_node(a)
                self.msme_agents.append(a)
                self.population.hire_workers(district, fa.workers)
        else:
            df_msmes = full_df.sample(n=min(200, len(full_df)))
            for idx, row in df_msmes.iterrows():
                district = str(row.get("District", 1))
                annual_output = float(row.get("value_rs", 100_000))
                # MSME working capital: 2 months of annual output (value_rs/6)
                # Floor at ₹50,000 to ensure at least one day's hiring budget.
                initial_capital = max(50_000, annual_output / 6)
                a = CorporateAgent(
                    model=self,
                    region="India",
                    tier="Tier-3",
                    initial_capital=initial_capital,
                    carbon_intensity=1.5,
                    nic_code=int(row.get("major_nic_2dig", 24)),
                    company_name=f"MSME_{row.get('fsu_serial_no', idx)}",
                    district_code=district,
                    carbon_deficit_theta=1.0,
                    workers_per_unit=5,
                    scaling_multiplier=1,
                )
                self.my_agents.append(a)
                self.supply_chain.add_node(a)
                self.msme_agents.append(a)
                self.population.hire_workers(district, 5)

        # EU buyer agents (synthetic Sector 2 counterparts)
        for i in range(n_eu):
            a = CorporateAgent(
                model=self,
                region="EU",
                tier="Tier-1",
                initial_capital=5_000_000,
                carbon_intensity=1.2,
                nic_code=24,
                company_name=f"EU_Buyer_{i}",
                district_code="9999",
            )
            self.my_agents.append(a)

        # Initial supply chain topology: IO-weighted bipartite links
        self._initialize_supply_links()

        # Mesa DataCollector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Capital_Flight": "total_capital_flight",
                "Listed_Bankruptcies": "total_bankruptcies",
                "MSME_Bankruptcies": "msme_bankruptcies",
                "Informal_Unemployment": self.get_informal_unemployment,
                "India_CCTS_Price": lambda m: m.gov_india.ccts_price,
                "Daily_Consumption": lambda m: m.population.aggregate_consumption(),
            }
        )

    # ------------------------------------------------------------------
    # Helper: build inter-district distance table
    # ------------------------------------------------------------------

    def _build_distance_table(self, full_df, path_lengths, state_code_map):
        dist_data = []
        if "st" in full_df.columns and "District" in full_df.columns:
            full_df = full_df.copy()
            full_df["st"] = full_df["st"].fillna("99").astype(str).str.zfill(2)
            full_df["District"] = full_df["District"].fillna("99").astype(str)
            dist_to_st = full_df.drop_duplicates("District").set_index("District")["st"].to_dict()
            unique_dists = list(dist_to_st.keys())
            for d1 in unique_dists:
                st1 = state_code_map.get(dist_to_st.get(d1, "99"), "Unknown")
                for d2 in unique_dists:
                    st2 = state_code_map.get(dist_to_st.get(d2, "99"), "Unknown")
                    if st1 == st2:
                        dist = 50.0
                    elif st1 in path_lengths and st2 in path_lengths.get(st1, {}):
                        dist = float(path_lengths[st1][st2])
                    else:
                        dist = 1000.0
                    dist_data.append({"c_district": str(d1), "m_district": str(d2), "dist": dist})
        else:
            dist_data = [{"c_district": "1", "m_district": "1", "dist": 0.0}]
        return dist_data

    # ------------------------------------------------------------------
    # Helper: initial supply chain topology
    # ------------------------------------------------------------------

    def _initialize_supply_links(self):
        """Bipartite IO-weighted supplier assignment at model start."""
        for buyer in self.listed_agents:
            buyer.required_supplier_count = 10
            for _ in range(buyer.required_supplier_count):
                if not self.msme_agents:
                    break
                prob_weights = []
                for msme in self.msme_agents:
                    weight = 0.01
                    if buyer.nic_code == 24:  # Metals — needs manufacturing MSMEs
                        weight = 0.6 if msme.nic_code == 24 else 0.1
                    elif buyer.nic_code == 62:  # Software
                        weight = 0.8 if msme.nic_code == 62 else 0.1
                    elif buyer.nic_code == 47:  # Trade
                        weight = 0.5 if msme.nic_code in {47, 24} else 0.1
                    weight += 1.0 / (msme.scaling_multiplier + 1) * 10
                    prob_weights.append(weight)

                total_w = sum(prob_weights)
                if total_w <= 0:
                    continue
                prob_weights = [w / total_w for w in prob_weights]
                chosen = random.choices(self.msme_agents, weights=prob_weights, k=1)[0]
                self.supply_chain.add_edge(chosen, buyer)
                buyer.suppliers.append(chosen)
                buyer.current_vintage_A = chosen.vintage_A
                buyer.current_vintage_epsilon = chosen.vintage_epsilon

    # ------------------------------------------------------------------
    # Helper: entry dynamics — replace a bankrupt MSME
    # ------------------------------------------------------------------

    def _replace_bankrupt_msme(self, dead_msme):
        """
        Draw a replacement MSME from the ASUSE empirical CDF.
        Same coarse sector and district as the bankrupt firm; starting capital
        at the median for its NIC sector from ASUSE data.
        """
        # Determine sector to match
        nic = dead_msme.nic_code
        try:
            candidates = self._asuse_df[
                self._asuse_df["major_nic_2dig"].astype(int) == nic
            ]
            if len(candidates) == 0:
                candidates = self._asuse_df
            row = candidates.sample(n=1).iloc[0]
            start_capital = max(10_000, float(candidates["value_rs"].median()))
        except Exception:
            start_capital = 50_000
            row = self._asuse_df.sample(n=1).iloc[0]

        new_agent = CorporateAgent(
            model=self,
            region="India",
            tier="Tier-3",
            initial_capital=start_capital,
            carbon_intensity=1.5,
            nic_code=nic,
            company_name=f"Entrant_{self.day_count}_{nic}",
            district_code=dead_msme.district_code,
            carbon_deficit_theta=1.0,
            workers_per_unit=int(row.get("workers_per_unit", 5)),
            scaling_multiplier=1,
        )

        self.my_agents.append(new_agent)
        self.supply_chain.add_node(new_agent)
        self.msme_agents.append(new_agent)
        # New entrant starts with no market share in supply chain; buyers will pick it up via brochures

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_government(self, region):
        return self.gov_india if region == "India" else self.gov_eu

    def get_informal_unemployment(self):
        return 1.0 - self.population.get_labor_scarcity()

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self):
        """Advance the model by one simulation day."""
        self.population.reset_daily_employment()

        # 1. Step all agents (production, R&D, wages, selling)
        random.shuffle(self.my_agents)
        for a in self.my_agents:
            a.step()

        # 2. K+S Brochure Matching and Payback Evaluation (Polars-vectorized)
        self._run_brochure_matching()

        # 3. Replicator Dynamics and Keynesian Demand
        self._run_replicator_dynamics()

        # 4. Entry Dynamics — replace newly bankrupt MSMEs
        self._handle_entry_dynamics()

        self.day_count += 1
        self.datacollector.collect(self)

    # ------------------------------------------------------------------
    # K+S Brochure Matching
    # ------------------------------------------------------------------

    def _run_brochure_matching(self):
        """
        K+S brochure protocol: each buyer receives brochures from at most
        KS_BROCHURE_COUNT = 5 randomly sampled MSMEs per step.

        Replaces the O(N*M) cross-join with O(N*K) sampling. The spatial
        arrival probability is evaluated only on the sampled pairs. This is
        consistent with the original Dosi et al. (2010) K+S protocol.

        Distances are normalized to [0,1] before the gamma filter so that
        SPATIAL_GAMMA=2.0 gives exp(-2*0) = 1.0 for same-district pairs and
        exp(-2*1) ≈ 0.14 for the most distant pair.

        Payback wage uses the buyer's actual labor class:
        - Tier-1 (Blue-Collar): WAGE_BLUE_COLLAR
        - Tier-3 (Informal): WAGE_INFORMAL
        """
        import numpy as np

        active_msmes = [m for m in self.msme_agents if not m.is_bankrupt and m.brochure_price > 0]
        active_listed = [c for c in self.listed_agents if not c.is_bankrupt]

        if not active_msmes or not active_listed:
            return

        tau_e = self.gov_eu.cbam_price

        for corp in active_listed:
            # Sample K candidates
            k = min(KS_BROCHURE_COUNT, len(active_msmes))
            candidates = random.sample(active_msmes, k)

            best_payback = float("inf")
            best_msme = None

            # Wage for this buyer's tier (used in payback calculation)
            buyer_wage = WAGE_BLUE_COLLAR if corp.tier == "Tier-1" else WAGE_INFORMAL
            is_exporter = corp.region == "India"

            for msme in candidates:
                # O(1) normalized distance lookup (pre-built in __init__)
                key = (str(corp.district_code), str(msme.district_code))
                dist_norm = self._dist_norm_lookup.get(key, 1.0)

                prob_arrive = math.exp(-SPATIAL_GAMMA * dist_norm)

                if random.random() > prob_arrive:
                    continue  # Brochure did not arrive

                # Payback period evaluation
                c_current = (
                    buyer_wage / max(0.01, corp.current_vintage_A)
                    + (tau_e * corp.current_vintage_epsilon if is_exporter else 0.0)
                )
                c_new = (
                    buyer_wage / max(0.01, msme.vintage_A)
                    + (tau_e * msme.vintage_epsilon if is_exporter else 0.0)
                )

                cost_saving = c_current - c_new
                if cost_saving <= 0 or msme.brochure_price <= 0:
                    continue

                payback = msme.brochure_price / cost_saving
                if payback < best_payback:
                    best_payback = payback
                    best_msme = msme

            # Execute supplier replacement if payback is within threshold
            if best_msme is not None and best_payback <= PAYBACK_YEARS_THRESHOLD:
                if corp.suppliers:
                    old_supplier = corp.suppliers[0]
                    if self.supply_chain.has_edge(old_supplier, corp):
                        self.supply_chain.remove_edge(old_supplier, corp)
                    corp.suppliers.remove(old_supplier)

                self.supply_chain.add_edge(best_msme, corp)
                corp.suppliers.append(best_msme)

                # Capital accumulation: buyer pays for machine; MSME earns revenue
                machine_cost = best_msme.brochure_price
                corp.physical_capital_k += machine_cost
                corp.capital -= machine_cost
                best_msme.capital += machine_cost
                best_msme.sales_history += machine_cost

                # Update vintage: buyer adopts new supplier's technology
                corp.current_vintage_A = best_msme.vintage_A
                corp.current_vintage_epsilon = best_msme.vintage_epsilon

                # LEADS-friction cooldown for re-sourcing (buyer end)
                # Low-LEADS states (poor logistics) → longer cooldown to settle new supplier
                supplier_state_code = str(best_msme.district_code)
                # Map district to state name via ASUSE data (best effort)
                leads = leads_scores.get(supplier_state_code, 50.0)
                cooldown_days = int(
                    COOLDOWN_MAX_DAYS * (1.0 - leads / 100.0)
                )
                cooldown_days = max(COOLDOWN_MIN_DAYS, cooldown_days)
                corp.supplier_cooldown = cooldown_days

    # ------------------------------------------------------------------
    # K+S Replicator Dynamics
    # ------------------------------------------------------------------

    def _run_replicator_dynamics(self):
        """
        Canonical K+S replicator update (Dosi et al. 2010):

            E_j(t) = -omega_1 * price_j(t) - omega_2 * unfilled_demand_j(t)
            f_j(t+1) = f_j(t) * (1 + chi * (E_j - mean_E) / mean_E)

        Key corrections vs. previous implementation:
        - price_j is per-firm (computed from unit labor cost + markup in agents.py)
        - divisor is E_mean, NOT abs(E_mean) — the canonical formula
        - aggregate_demand from household consumption drives individual firm demand
        """
        aggregate_demand = self.population.aggregate_consumption()

        omega_1 = 0.5
        omega_2 = 0.5
        chi = 0.1

        active = [c for c in self.listed_agents if not c.is_bankrupt]
        if not active:
            return

        for c in active:
            c.competitiveness_E = -omega_1 * c.price - omega_2 * c.backlog_l

        e_vals = [c.competitiveness_E for c in active]
        e_mean = sum(e_vals) / len(e_vals)

        total_new_f = 0.0
        for c in active:
            c.demand_D = aggregate_demand * c.market_share_f
            c.backlog_l = max(0.0, c.backlog_l + c.demand_D - c.capacity_Y)

            # Canonical replicator: divide by E_mean (which is negative here)
            # Direction: firm with E_j > E_mean (less negative = more competitive) gains share
            if e_mean != 0:
                new_f = c.market_share_f * (1.0 + chi * (c.competitiveness_E - e_mean) / e_mean)
            else:
                new_f = c.market_share_f

            c.market_share_f = max(0.0, new_f)
            total_new_f += c.market_share_f

        # Normalize to sum = 1.0
        if total_new_f > 0:
            for c in active:
                c.market_share_f /= total_new_f

    # ------------------------------------------------------------------
    # Entry Dynamics
    # ------------------------------------------------------------------

    def _handle_entry_dynamics(self):
        """
        Replace each newly bankrupt MSME with a new entrant drawn from the
        ASUSE empirical CDF (same sector). Maintains industrial ecology stability.
        """
        newly_bankrupt = [
            m for m in self.msme_agents
            if m.is_bankrupt and id(m) not in self._replaced_bankrupts
        ]
        for dead in newly_bankrupt:
            self._replaced_bankrupts.add(id(dead))
            self._replace_bankrupt_msme(dead)
