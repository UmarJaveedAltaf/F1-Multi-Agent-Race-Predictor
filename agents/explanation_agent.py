from agents.base_agent import BaseAgent
from typing import Dict, List


class ExplainabilityAgent(BaseAgent):
    """
    Generates human-readable explanations
    for race predictions
    """

    def __init__(self):
        super().__init__("ExplainabilityAgent")

    def run(self, context: dict) -> Dict:
        circuit = context["circuit"]
        drivers = context["drivers"]
        prediction = context["prediction"]

        winner = prediction["winner"]
        winner_stats = drivers[winner]

        explanations: List[str] = []

        # ---- Circuit-based explanation ----
        if circuit["qualifying_importance"] > 0.7:
            explanations.append(
                f"The circuit places high importance on qualifying "
                f"(score={circuit['qualifying_importance']}), favoring drivers "
                f"who convert grid position efficiently."
            )

        if circuit["overtaking_difficulty"] < 0.35:
            explanations.append(
                "Overtaking is relatively difficult on this circuit, "
                "which rewards consistency and clean race execution."
            )

        if circuit["safety_car_risk"] > 0.4:
            explanations.append(
                "Higher safety car risk introduces race variability, "
                "penalizing drivers with high DNF risk."
            )

        # ---- Driver-based explanation ----
        explanations.append(
            f"{winner.capitalize()} showed strong recent form "
            f"(form_score={winner_stats['form_score']}) "
            f"with low DNF risk ({winner_stats['dnf_risk']})."
        )

        if winner_stats["qualifying_delta"] < 0:
            explanations.append(
                f"{winner.capitalize()} tends to gain positions during races, "
                "which is valuable on this circuit."
            )

        # ---- Model transparency note ----
        explanations.append(
            "Note: This prediction is based on recent race form and circuit dynamics. "
            "Constructor performance and driver experience were incorporated to reduce small-sample bias and improve realism."

        )

        return {
            "winner": winner,
            "explanations": explanations
        }
