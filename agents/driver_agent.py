from agents.base_agent import BaseAgent
from services.jolpica_service import JolpicaService
from typing import Dict, List
import numpy as np


class DriverAgent(BaseAgent):
    """
    Driver performance and form modeling agent
    """

    def __init__(self, jolpica: JolpicaService, window: int = 5):
        super().__init__("DriverAgent")
        self.jol = jolpica
        self.window = window

    def _get_recent_races(self, season: int, round_no: int) -> List[int]:
        start = max(1, round_no - self.window)
        return list(range(start, round_no))

    def run(self, context: dict) -> Dict[str, Dict]:
        season = context["season"]
        round_no = context["round"]

        recent_rounds = self._get_recent_races(season, round_no)

        driver_stats = {}

        for r in recent_rounds:
            results = self.jol.results(season, r)
            race_results = results["MRData"]["RaceTable"]["Races"][0]["Results"]

            for res in race_results:
                driver_id = res["Driver"]["driverId"]

                if driver_id not in driver_stats:
                    driver_stats[driver_id] = {
                        "finishes": [],
                        "grids": [],
                        "dnfs": 0,
                        "races":0
                    }

                # Grid & finish
                if res.get("grid") and res.get("position"):
                    driver_stats[driver_id]["grids"].append(int(res["grid"]))
                    driver_stats[driver_id]["finishes"].append(int(res["position"]))

                # DNF check
                if res["status"] != "Finished":
                    driver_stats[driver_id]["dnfs"] += 1
                    driver_stats[driver_id]["races"] += 1


        # ---- Compute features ----
        output = {}

        for driver_id, stats in driver_stats.items():
            finishes = np.array(stats["finishes"])
            grids = np.array(stats["grids"])

            if len(finishes) == 0:
                continue

            avg_finish = float(np.mean(finishes))
            consistency = float(1 / (1 + np.std(finishes)))
            dnf_risk = float(stats["dnfs"] / max(1, len(recent_rounds)))

            if len(grids) == len(finishes):
                quali_delta = float(np.mean(grids - finishes))
            else:
                quali_delta = 0.0

            # Normalized form score
            form_score = float(1 / (1 + avg_finish))

            # ✅ IMPORTANT: include driver_id explicitly
            output[driver_id] = {
                "driver_id": driver_id,
                "avg_finish": round(avg_finish, 3),
                "consistency": round(consistency, 3),
                "dnf_risk": round(dnf_risk, 3),
                "qualifying_delta": round(quali_delta, 3),
                "form_score": round(form_score, 3),
                "race_count": stats["races"]
            }

        return output
