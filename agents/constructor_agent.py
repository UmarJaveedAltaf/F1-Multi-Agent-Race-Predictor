from agents.base_agent import BaseAgent
from services.jolpica_service import JolpicaService
from typing import Dict
import numpy as np


class ConstructorAgent(BaseAgent):
    """
    Models constructor (car) performance and dominance
    """

    def __init__(self, jolpica: JolpicaService, window: int = 5):
        super().__init__("ConstructorAgent")
        self.jol = jolpica
        self.window = window

    def _recent_rounds(self, round_no: int):
        return list(range(max(1, round_no - self.window), round_no))

    def run(self, context: dict) -> Dict[str, Dict]:
        season = context["season"]
        round_no = context["round"]

        rounds = self._recent_rounds(round_no)

        teams = {}

        for r in rounds:
            results = self.jol.results(season, r)
            race_results = results["MRData"]["RaceTable"]["Races"][0]["Results"]

            for res in race_results:
                constructor = res["Constructor"]["constructorId"]

                if constructor not in teams:
                    teams[constructor] = {
                        "finishes": [],
                        "points": [],
                        "dnfs": 0
                    }

                if res.get("position"):
                    teams[constructor]["finishes"].append(int(res["position"]))

                if res.get("points"):
                    teams[constructor]["points"].append(float(res["points"]))

                if res["status"] != "Finished":
                    teams[constructor]["dnfs"] += 1

        # ---- Compute metrics ----
        output = {}

        for team, stats in teams.items():
            finishes = np.array(stats["finishes"])
            points = np.array(stats["points"])

            if len(finishes) == 0:
                continue

            avg_finish = float(np.mean(finishes))
            points_per_race = float(np.mean(points)) if len(points) > 0 else 0.0
            dnf_rate = float(stats["dnfs"] / max(1, len(rounds) * 2))

            dominance_score = float(
                (1 / (1 + avg_finish)) * (1 + points_per_race / 25)
            )

            output[team] = {
                "avg_finish": round(avg_finish, 3),
                "points_per_race": round(points_per_race, 3),
                "dnf_rate": round(dnf_rate, 3),
                "dominance_score": round(dominance_score, 3)
            }

        return output
