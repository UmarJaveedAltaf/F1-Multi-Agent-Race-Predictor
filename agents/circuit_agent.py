from agents.base_agent import BaseAgent
from services.jolpica_service import JolpicaService
from typing import Dict
import numpy as np


class CircuitAgent(BaseAgent):
    """
    Data-backed Circuit Intelligence Agent
    """

    def __init__(self, jolpica: JolpicaService):
        super().__init__("CircuitAgent")
        self.jol = jolpica

    def run(self, context: dict) -> Dict:
        season = context["season"]
        round_no = context["round"]

        # ---- Fetch race metadata ----
        races = self.jol.races(season)
        race = next(
            r for r in races["MRData"]["RaceTable"]["Races"]
            if int(r["round"]) == round_no
        )

        circuit = race["Circuit"]
        circuit_name = circuit["circuitName"]

        # ---- Fetch race results ----
        results = self.jol.results(season, round_no)
        drivers = results["MRData"]["RaceTable"]["Races"][0]["Results"]

        # ---- Feature engineering ----
        grid_positions = []
        finish_positions = []

        for d in drivers:
            if d.get("grid") and d.get("position"):
                grid_positions.append(int(d["grid"]))
                finish_positions.append(int(d["position"]))

        grid_positions = np.array(grid_positions)
        finish_positions = np.array(finish_positions)

        # ---- Qualifying importance (grid vs finish correlation) ----
        if len(grid_positions) > 5:
            corr = np.corrcoef(grid_positions, finish_positions)[0, 1]
            qualifying_importance = float(abs(corr))
        else:
            qualifying_importance = 0.5

        # ---- Overtaking difficulty (lower avg change = harder) ----
        avg_position_change = np.mean(np.abs(grid_positions - finish_positions))
        overtaking_difficulty = float(1 / (1 + avg_position_change))

        # ---- Safety car / chaos proxy ----
        dnf_count = sum(1 for d in drivers if d["status"] != "Finished")
        safety_car_risk = min(1.0, dnf_count / len(drivers))

        # ---- Lap count (ROBUST handling) ----
        lap_count = None
        try:
            # Some Jolpica races include laps at race level
            if "laps" in race:
                lap_count = int(race["laps"])
            else:
                # Fallback: use winner's completed laps if present
                winner = drivers[0]
                if "laps" in winner:
                    lap_count = int(winner["laps"])
        except Exception:
            lap_count = None

        return {
            "circuit_name": circuit_name,
            "location": f"{circuit['Location']['locality']}, {circuit['Location']['country']}",
            "qualifying_importance": round(qualifying_importance, 3),
            "overtaking_difficulty": round(overtaking_difficulty, 3),
            "safety_car_risk": round(safety_car_risk, 3),
            "lap_count": lap_count
        }
