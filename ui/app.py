import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import streamlit as st

from services.cache_service import CacheService
from services.jolpica_service import JolpicaService

from agents.circuit_agent import CircuitAgent
from agents.driver_agent import DriverAgent
from agents.constructor_agent import ConstructorAgent
from agents.fusion_agent import FusionAgent
from agents.explanation_agent import ExplainabilityAgent


def build_driver_constructor_map(season: int, round_no: int, jol: JolpicaService) -> dict:
    """
    Map driverId -> constructorId from the selected race.
    Returns {} if results are unavailable.
    """
    data = jol.results(season, round_no)
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        return {}
    results = races[0].get("Results", [])
    return {r["Driver"]["driverId"]: r["Constructor"]["constructorId"] for r in results}


def safe_title_driver(driver_id: str | None) -> str:
    if not driver_id:
        return "N/A"
    return driver_id.replace("_", " ").title()


# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="F1 Multi-Agent Predictor", layout="wide")
st.title("🏎️ Formula 1 Race Predictor")
st.caption("Multi-Agent AI System using FastF1 + Jolpica")

# -------------------- RED BULL THEME (FIXED + TITLE SAFE) --------------------
st.markdown(
    """
    <style>
    /* Force true black background everywhere */
    html, body, [class*="css"] {
        background-color: #0B0B0B !important;
        color: #FFFFFF !important;
    }

    /* FIX: prevent title clipping */
    .block-container {
        padding-top: 3.5rem;
    }

    h1 {
        margin-top: 0rem !important;
        padding-top: 0.5rem !important;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #161616;
        border: 1px solid #E10600;
        padding: 12px;
        border-radius: 10px;
    }

    /* Progress bar track */
    div[data-testid="stProgress"] > div > div {
        background-color: #1A1A1A !important;
    }

    /* Progress bar fill */
    div[data-testid="stProgress"] > div > div > div {
        background-color: #E10600 !important;
    }

    /* Primary button */
    button[kind="primary"] {
        background-color: #E10600 !important;
        color: white !important;
        border-radius: 6px;
        border: none;
    }

    button[kind="primary"]:hover {
        background-color: #B80500 !important;
        color: white !important;
    }

    /* Expander header */
    div[data-testid="stExpander"] > details > summary {
        color: #E10600 !important;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------- INPUT FORM --------------------
with st.form("predict_form"):
    season = st.selectbox("Season", [2025, 2024, 2023, 2022], index=0)
    round_no = st.number_input("Race Round", min_value=1, max_value=24, value=5, step=1)
    submitted = st.form_submit_button("🔮 Predict Race")


# -------------------- RUN PREDICTION --------------------
if submitted:
    with st.spinner("Running AI agents..."):
        cache = CacheService()
        jol = JolpicaService(cache)

        try:
            base = {"season": int(season), "round": int(round_no)}

            circuit = CircuitAgent(jol).run(base)
            drivers = DriverAgent(jol).run(base)
            constructors = ConstructorAgent(jol).run(base)
            mapping = build_driver_constructor_map(int(season), int(round_no), jol)

            if not drivers or not mapping:
                st.error(
                    "No data available for this season/round yet "
                    "(or the API returned empty results)."
                )
                st.stop()

            prediction = FusionAgent().run(
                {
                    "circuit": circuit,
                    "drivers": drivers,
                    "constructors": constructors,
                    "driver_to_constructor": mapping,
                }
            )

            if not prediction or prediction.get("winner") is None:
                st.error(
                    "Prediction could not be generated (insufficient data). "
                    "Try a different season or round."
                )
                st.stop()

            explanation = ExplainabilityAgent().run(
                {"circuit": circuit, "drivers": drivers, "prediction": prediction}
            )

        except Exception as e:
            st.error(f"App error while generating prediction: {e}")
            st.stop()
        finally:
            cache.close()

    # -------------------- OUTPUT --------------------
    st.subheader("🏁 Race Prediction")

    c_name = circuit.get("circuit_name", "Unknown Circuit")
    c_loc = circuit.get("location", "Unknown Location")
    st.caption(
        f"**Circuit:** {c_name} — {c_loc} | "
        f"**Laps:** {circuit.get('lap_count', 'N/A')}"
    )

    st.metric("Winner 🏆", safe_title_driver(prediction.get("winner")))

    st.write("**Podium**")
    podium = prediction.get("podium", [])
    for i, d in enumerate(podium, start=1):
        st.write(f"{i}. {safe_title_driver(d)}")

    # -------------------- PROBABILITIES --------------------
    st.subheader("📊 Win Probabilities")

    probs = prediction.get("probabilities", {})
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    st.markdown("**Top 5 contenders**")
    for d, p in sorted_probs[:5]:
        st.progress(
            float(min(max(p, 0.0), 1.0)),
            text=f"{safe_title_driver(d)} — {p:.3f}",
        )

    with st.expander("🔍 Show Top 10 probabilities"):
        for i, (d, p) in enumerate(sorted_probs[:10], start=1):
            st.write(f"{i}. **{safe_title_driver(d)}** — {p:.3f}")

    # -------------------- EXPLANATION --------------------
    st.subheader("🧠 Explanation")
    for e in (explanation or {}).get("explanations", []):
        st.write("•", e)
