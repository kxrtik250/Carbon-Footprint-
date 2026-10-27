import os
import joblib
import numpy as np
import pandas as pd
from config import Config

class Preprocessor:
    def __init__(self):
        self.scaler = None
        self.label_encoders = None
        self.is_loaded = False
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(Config.SCALER_PATH) and os.path.exists(Config.ENCODERS_PATH):
            self.scaler = joblib.load(Config.SCALER_PATH)
            self.label_encoders = joblib.load(Config.ENCODERS_PATH)
            self.is_loaded = True
        else:
            print("[Warning] Scaler or Encoders file not found!")

    def transform(self, input_dict):
        """
        Transforms user input dict into scaled 2D array for ML model inference.
        """
        if not self.is_loaded:
            self._load_artifacts()

        # Expected feature order matching training dataset:
        # District, Place, Area_Type, Population_Density, Electricity_kWh, Petrol_Liters,
        # Diesel_Liters, LPG_kg, Public_Transport_km, Waste_Generated_kg, Solar_Energy_kWh,
        # Tree_Cover_Percent, AQI, Region_Emission_Factor
        
        feature_order = [
            "District", "Place", "Area_Type", "Population_Density", "Electricity_kWh",
            "Petrol_Liters", "Diesel_Liters", "LPG_kg", "Public_Transport_km",
            "Waste_Generated_kg", "Solar_Energy_kWh", "Tree_Cover_Percent",
            "AQI", "Region_Emission_Factor"
        ]

        df_input = pd.DataFrame([input_dict])[feature_order]

        # Encode categorical
        for col in ["District", "Place", "Area_Type"]:
            le = self.label_encoders.get(col)
            if le:
                val = str(df_input[col].iloc[0])
                if val in le.classes_:
                    df_input[col] = le.transform([val])[0]
                else:
                    # Fallback to first class
                    df_input[col] = 0

        # Scale features
        scaled_array = self.scaler.transform(df_input)
        return scaled_array
