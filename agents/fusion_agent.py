from agents.base_agent import BaseAgent
from typing import Dict
import math
import numpy as np


class FusionAgent(BaseAgent):
    """
    Fuses CircuitAgent + DriverAgent + ConstructorAgent outputs
    to predict race winner and podium.

    Features:
    - Experience regularization
    - Constructor dominance gating
    - Midfield uplift control
    - Score standardization (z-score)
    - Post-standardization dominance priors (Option B)
    - Temperature-scaled softmax
    - Defensive handling for empty / invalid inputs
    """

    def __init__(self):
        super().__init__("FusionAgent")

    def run(self, context: dict) -> Dict:
        circuit = context.get("circuit") or {}
        drivers = context.get("drivers") or {}
        constructors = context.get("constructors") or {}
        driver_to_constructor = context.get("driver_to_constructor") or {}

        qi = float(circuit.get("qualifying_importance", 0.5))
        od = float(circuit.get("overtaking_difficulty", 0.3))
        scr = float(circuit.get("safety_car_risk", 0.2))

        if not drivers:
            return {"winner": None, "podium": [], "probabilities": {}}

        raw_scores: Dict[str, float] = {}

        # -----------------------------
        # 1️⃣ Raw score computation
        # -----------------------------
        for driver, stats in drivers.items():
            if not isinstance(stats, dict):
                continue

            driver_id = stats.get("driver_id", driver)
            team = driver_to_constructor.get(driver_id)

            constructor_strength = float(
                constructors.get(team, {}).get("dominance_score", 0.1)
            )

            # Constructor strength gating
            if constructor_strength < 0.20:
                constructor_penalty = 0.85
            elif constructor_strength < 0.28:
                constructor_penalty = 0.94
            else:
                constructor_penalty = 1.0

            # Experience regularization
            race_count = float(stats.get("race_count", 0.0))
            experience_factor = min(1.0, race_count / 5.0)

            form_score = float(stats.get("form_score", 0.0))
            consistency = float(stats.get("consistency", 0.0))
            dnf_risk = float(stats.get("dnf_risk", 0.0))
            qualifying_delta = float(stats.get("qualifying_delta", 0.0))

            score = (
                (form_score * 0.30)
                + (consistency * (0.18 + od))
                + (constructor_strength * 0.30)
                - (dnf_risk * (0.20 + scr))
                - (abs(qualifying_delta) * qi * 0.04)
            )

            score *= experience_factor
            score *= constructor_penalty

            if math.isfinite(score):
                raw_scores[driver] = score

        if not raw_scores:
            return {"winner": None, "podium": [], "probabilities": {}}

        # -----------------------------
        # 2️⃣ Z-score standardization
        # -----------------------------
        values = np.array(list(raw_scores.values()), dtype=float)
        mean = float(values.mean())
        std = float(values.std() + 1e-9)

        standardized_scores = {
            k: (v - mean) / std for k, v in raw_scores.items()
        }

        # -----------------------------
        # 3️⃣ OPTION B — Dominance priors
        #     (applied AFTER standardization)
        # -----------------------------
        for driver, stats in drivers.items():
            if driver not in standardized_scores:
                continue

            driver_id = stats.get("driver_id", driver)
            team = driver_to_constructor.get(driver_id)

            # Jolpica constructor IDs
            if team == "red_bull":
                standardized_scores[driver] += 0.60
            elif team in ("ferrari", "mclaren"):
                standardized_scores[driver] += 0.25
            elif team == "mercedes":
                standardized_scores[driver] += 0.10

        # -----------------------------
        # 4️⃣ Temperature-scaled softmax
        # -----------------------------
        TEMPERATURE = 5.0 # calibrated for realistic F1 confidence

        max_score = max(standardized_scores.values())
        exp_scores = {
            k: math.exp((v - max_score) * TEMPERATURE)
            for k, v in standardized_scores.items()
        }

        total = sum(exp_scores.values())
        if total <= 0 or not math.isfinite(total):
            return {"winner": None, "podium": [], "probabilities": {}}

        probabilities = {
            k: round(exp_scores[k] / total, 3)
            for k in exp_scores
        }

        ranking = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        if not ranking:
            return {"winner": None, "podium": [], "probabilities": {}}

        return {
            "winner": ranking[0][0],
            "podium": [r[0] for r in ranking[:3]],
            "probabilities": probabilities,
        }
