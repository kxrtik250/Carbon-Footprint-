import sys
import os
import json
import sqlite3

BASE_DIR = r"C:\Users\User\.gemini\antigravity\scratch\carbon_emission_system"
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from app import app, get_db_connection
from utils.prediction import prediction_engine
from utils.llm_recommender import generate_llm_recommendations

print("--- 1. Testing LLM Recommendation Module ---")
sample_input = {
    "District": "Chennai",
    "Place": "Adyar",
    "Area_Type": "Urban",
    "Population_Density": 15000,
    "Electricity_kWh": 500,
    "Petrol_Liters": 60,
    "Diesel_Liters": 30,
    "LPG_kg": 20,
    "Public_Transport_km": 200,
    "Waste_Generated_kg": 40,
    "Solar_Energy_kWh": 100,
    "Tree_Cover_Percent": 15,
    "AQI": 120,
    "Region_Emission_Factor": 0.82
}

res = prediction_engine.predict(sample_input)
print("ML Output with LLM Recommendations:")
print("Engine Name:", res["llm_recommendations"]["engine"])
print("Summary:", res["llm_recommendations"]["summary"])
print("Immediate Actions:", res["llm_recommendations"]["immediate_actions"])
print("Medium Term Actions:", res["llm_recommendations"]["medium_term_actions"])
print("Long Term Actions:", res["llm_recommendations"]["long_term_actions"])

assert "llm_recommendations" in res, "Result must contain LLM recommendations"
assert len(res["llm_recommendations"]["immediate_actions"]) > 0, "Must have immediate actions"
assert res["llm_recommendations"]["estimated_co2_reduction_kg"] > 0, "Reduction must be > 0"

print("\n--- 2. Testing Database & Endpoints ---")
client = app.test_client()

login_res = client.post('/login', data={'email': 'demo@carbon.ai', 'password': 'admin123'}, follow_redirects=True)
assert login_res.status_code == 200

# Test LLM API endpoint
llm_api_res = client.get('/api/llm-recommendation/1')
assert llm_api_res.status_code == 200
llm_api_json = llm_api_res.get_json()
print("LLM API endpoint response engine:", llm_api_json.get("engine"))
assert "immediate_actions" in llm_api_json

print("\n=== ALL LLM INTEGRATION TESTS PASSED SUCCESSFULLY! ===")
