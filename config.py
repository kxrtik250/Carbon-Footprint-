import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Set SECRET_KEY in the environment for shared or production deployments.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DB_PATH = os.path.join(BASE_DIR, "database", "carbon_emission.db")
    
    # ML Model Artifacts
    MODEL_PATH = os.path.join(BASE_DIR, "models", "carbon_model.pkl")
    SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")
    ENCODERS_PATH = os.path.join(BASE_DIR, "models", "label_encoders.pkl")
    
    # Environmental Thresholds (kg CO2 / month)
    EMISSION_THRESHOLDS = {
        "Low": 150.0,
        "Moderate": 350.0,
        "High": 600.0,
        "Very High": float("inf")
    }
    
    # Environmental Score scaling factor: 100 - (emission / MAX_BENCHMARK * 100)
    MAX_BENCHMARK_EMISSION = 800.0
    
    # Tree absorption factor: ~21.77 kg CO2 / tree / year (or ~1.81 kg CO2 / month)
    TREE_ABSORPTION_KG_PER_YEAR = 21.77
