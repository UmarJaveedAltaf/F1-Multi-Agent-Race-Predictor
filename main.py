from services.cache_service import CacheService
from services.jolpica_service import JolpicaService
from agents.circuit_agent import CircuitAgent
from agents.driver_agent import DriverAgent
from agents.constructor_agent import ConstructorAgent
from agents.fusion_agent import FusionAgent
from agents.explanation_agent import ExplainabilityAgent

def build_driver_constructor_map(season, round_no, jol):
    results = jol.results(season, round_no)
    race_results = results["MRData"]["RaceTable"]["Races"][0]["Results"]
    return {
        r["Driver"]["driverId"]: r["Constructor"]["constructorId"]
        for r in race_results
    }

def main():
    cache = CacheService()
    jol = JolpicaService(cache)

    base = {"season": 2024, "round": 5}

    circuit = CircuitAgent(jol).run(base)
    drivers = DriverAgent(jol).run(base)
    constructors = ConstructorAgent(jol).run(base)
    print("\n🏗️ CONSTRUCTOR AGENT (sample)\n")
    top_teams = sorted(
        constructors.items(),
        key=lambda x: x[1]["dominance_score"],
        reverse=True
    )[:5]
    for team, stats in top_teams:
        print(team, stats)

    mapping = build_driver_constructor_map(2024, 5, jol)

    print("\n🔗 DRIVER → CONSTRUCTOR MAP (sample)\n")
    for i, (d, c) in enumerate(mapping.items()):
        print(d, "->", c)
        if i == 5:
            break




    prediction = FusionAgent().run({
        "circuit": circuit,
        "drivers": drivers,
        "constructors": constructors,
        "driver_to_constructor": mapping
    })

    explanation = ExplainabilityAgent().run({
        "circuit": circuit,
        "drivers": drivers,
        "prediction": prediction
    })

    print("\n🏁 RACE PREDICTION")
    print("Winner:", prediction["winner"])
    print("Podium:", prediction["podium"])

    print("\n🧠 EXPLANATION")
    for e in explanation["explanations"]:
        print("-", e)

    cache.close()

if __name__ == "__main__":
    main()
