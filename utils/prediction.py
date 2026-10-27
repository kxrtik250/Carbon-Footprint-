import os
import joblib
import numpy as np
from config import Config
from utils.preprocessing import Preprocessor
from utils.llm_recommender import generate_llm_recommendations

class PredictionEngine:
    def __init__(self):
        self.model = None
        self.preprocessor = Preprocessor()
        self._load_model()

    def _load_model(self):
        if os.path.exists(Config.MODEL_PATH):
            self.model = joblib.load(Config.MODEL_PATH)
            print("[Info] ML Model loaded successfully into Flask memory.")
        else:
            print("[Warning] ML Model file carbon_model.pkl not found!")

    def predict(self, input_dict):
        """
        Executes complete inference pipeline.
        Returns: dict with prediction, score, category, tree_offset, feature_importance, recommendations, and LLM advice.
        """
        if self.model is None:
            self._load_model()

        scaled_data = self.preprocessor.transform(input_dict)
        pred_value = self.model.predict(scaled_data)[0]
        
        predicted_emission = max(10.0, round(float(pred_value), 2))
        
        env_score, env_rating = self.calculate_environmental_score(predicted_emission)
        category = self.get_emission_category(predicted_emission)
        tree_offset = self.calculate_tree_offset(predicted_emission)
        feature_contributions = self.calculate_feature_contributions(input_dict)
        rule_recommendations = self.generate_recommendations(input_dict)

        base_res = {
            "predicted_emission": predicted_emission,
            "environmental_score": env_score,
            "environmental_rating": env_rating,
            "emission_category": category,
            "tree_offset": tree_offset,
            "feature_contributions": feature_contributions,
            "recommendations": rule_recommendations
        }

        # Generate LLM Recommendations
        llm_advice = generate_llm_recommendations(input_dict, base_res)
        base_res["llm_recommendations"] = llm_advice

        return base_res

    def calculate_environmental_score(self, emission):
        benchmark = Config.MAX_BENCHMARK_EMISSION
        score = max(0, min(100, int(round(100 - (emission / benchmark) * 100))))
        
        if score >= 80:
            rating = "EXCELLENT"
        elif score >= 60:
            rating = "GOOD"
        elif score >= 40:
            rating = "MODERATE"
        elif score >= 20:
            rating = "POOR"
        else:
            rating = "CRITICAL"
            
        return score, rating

    def get_emission_category(self, emission):
        if emission < 150.0:
            return "Low"
        elif emission < 350.0:
            return "Moderate"
        elif emission < 600.0:
            return "High"
        else:
            return "Very High"

    def calculate_tree_offset(self, emission):
        annual_emission = emission * 12.0
        trees = int(np.ceil(annual_emission / Config.TREE_ABSORPTION_KG_PER_YEAR))
        return max(1, trees)

    def calculate_feature_contributions(self, input_dict):
        ef_region = float(input_dict.get("Region_Emission_Factor", 0.82))
        elec = float(input_dict.get("Electricity_kWh", 0)) * ef_region
        petrol = float(input_dict.get("Petrol_Liters", 0)) * 2.31
        diesel = float(input_dict.get("Diesel_Liters", 0)) * 2.68
        lpg = float(input_dict.get("LPG_kg", 0)) * 2.983
        waste = float(input_dict.get("Waste_Generated_kg", 0)) * 0.45
        pub_trans = float(input_dict.get("Public_Transport_km", 0)) * 0.089
        
        solar_off = float(input_dict.get("Solar_Energy_kWh", 0)) * ef_region * 0.95
        tree_off = (float(input_dict.get("Tree_Cover_Percent", 0)) / 100.0) * (elec + petrol + diesel) * 0.18

        contributions = [
            {"factor": "Electricity Consumption", "val": round(elec, 2), "type": "positive"},
            {"factor": "Petrol Consumption", "val": round(petrol, 2), "type": "positive"},
            {"factor": "Diesel Consumption", "val": round(diesel, 2), "type": "positive"},
            {"factor": "LPG Consumption", "val": round(lpg, 2), "type": "positive"},
            {"factor": "Waste Generation", "val": round(waste, 2), "type": "positive"},
            {"factor": "Public Transport", "val": round(pub_trans, 2), "type": "positive"},
            {"factor": "Solar Energy Offset", "val": round(solar_off, 2), "type": "negative"},
            {"factor": "Tree Cover Offset", "val": round(tree_off, 2), "type": "negative"}
        ]
        
        contributions = sorted(contributions, key=lambda x: x["val"], reverse=True)
        return contributions

    def generate_recommendations(self, input_dict):
        recs = []
        elec = float(input_dict.get("Electricity_kWh", 0))
        petrol = float(input_dict.get("Petrol_Liters", 0))
        diesel = float(input_dict.get("Diesel_Liters", 0))
        lpg = float(input_dict.get("LPG_kg", 0))
        waste = float(input_dict.get("Waste_Generated_kg", 0))
        solar = float(input_dict.get("Solar_Energy_kWh", 0))
        tree_cover = float(input_dict.get("Tree_Cover_Percent", 0))

        if elec > 300:
            recs.append("Electricity usage is high. Transition to energy-efficient 5-star LED appliances and consider installing rooftop solar PV panels.")
        if petrol > 80 or diesel > 80:
            recs.append("Vehicle fuel consumption is significant. Switch to electric mobility (EVs), carpooling, or public transport to reduce fossil fuel burn.")
        if solar < 100:
            recs.append("Solar energy adoption is low. Increasing solar energy generation can offset up to 40% of grid electricity emissions.")
        if waste > 40:
            recs.append("Waste generation is elevated. Implement 3-R practices (Reduce, Reuse, Recycle) and home composting to lower landfill methane emissions.")
        if tree_cover < 20:
            recs.append("Local green cover is under 20%. Participating in native tree plantation drives enhances local CO2 absorption and cools urban heat islands.")

        if not recs:
            recs.append("Great job! Your consumption profile is energy-efficient. Maintain your sustainable lifestyle choices.")

        return recs

prediction_engine = PredictionEngine()
