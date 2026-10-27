import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Define base paths
BASE_DIR = r"C:\Users\User\.gemini\antigravity\scratch\carbon_emission_system"
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "notebooks")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

print("--- Generating Tamil Nadu Carbon Emission Dataset ---")

# 10 Districts and 50 Places with accurate coordinates
LOCATION_DATA = {
    "Chennai": {
        "places": ["Adyar", "Anna Nagar", "Guindy", "Velachery", "T. Nagar"],
        "coords": [(13.0067, 80.2572), (13.0850, 80.2101), (13.0067, 80.2020), (12.9815, 80.2180), (13.0418, 80.2341)],
        "default_area": "Urban"
    },
    "Coimbatore": {
        "places": ["Gandhipuram", "Peelamedu", "RS Puram", "Saravanampatti", "Singanallur"],
        "coords": [(11.0168, 76.9558), (11.0284, 77.0007), (11.0084, 76.9490), (11.0800, 76.9930), (10.9980, 77.0300)],
        "default_area": "Industrial"
    },
    "Madurai": {
        "places": ["Mattuthavani", "Goripalayam", "Simmakkal", "Thiruparankundram", "Anna Nagar"],
        "coords": [(9.9472, 78.1561), (9.9290, 78.1250), (9.9230, 78.1180), (9.8820, 78.0710), (9.9180, 78.1460)],
        "default_area": "Urban"
    },
    "Tiruchirappalli": {
        "places": ["Srirangam", "Thillai Nagar", "Cantonment", "K.K. Nagar", "Chatram"],
        "coords": [(10.8622, 78.6946), (10.8250, 78.6850), (10.8060, 78.6880), (10.7850, 78.6960), (10.8340, 78.6910)],
        "default_area": "Semi-Urban"
    },
    "Salem": {
        "places": ["Hasthampatti", "Fairlands", "Suramangalam", "Ammapet", "Shevapet"],
        "coords": [(11.6740, 78.1630), (11.6710, 78.1420), (11.6850, 78.1200), (11.6540, 78.1800), (11.6450, 78.1400)],
        "default_area": "Industrial"
    },
    "Tirunelveli": {
        "places": ["Palayamkottai", "Junction", "Melapalayam", "Vannarpettai", "Pettai"],
        "coords": [(8.7139, 77.7340), (8.7290, 77.7000), (8.7010, 77.7120), (8.7240, 77.7260), (8.7400, 77.6700)],
        "default_area": "Semi-Urban"
    },
    "Erode": {
        "places": ["Perundurai", "Collectorate", "BPS", "Thindal", "Surampatti"],
        "coords": [(11.2750, 77.5830), (11.3360, 77.7180), (11.3410, 77.7270), (11.3200, 77.6780), (11.3280, 77.7100)],
        "default_area": "Industrial"
    },
    "Vellore": {
        "places": ["Sathuvachari", "Katpadi", "Gandhi Nagar", "Thorapadi", "Bagayam"],
        "coords": [(12.9350, 79.1600), (12.9750, 79.1350), (12.9550, 79.1450), (12.8950, 79.1200), (12.8750, 79.1300)],
        "default_area": "Semi-Urban"
    },
    "Thanjavur": {
        "places": ["Old Bus Stand", "Medical College Road", "Vallam", "Karanthai", "Punnainallur"],
        "coords": [(10.7870, 79.1370), (10.7600, 79.1150), (10.7100, 79.0560), (10.8010, 79.1450), (10.7750, 79.1850)],
        "default_area": "Rural"
    },
    "Kanchipuram": {
        "places": ["Little Kanchipuram", "Big Kanchipuram", "Enathur", "Collectorate", "Orikkai"],
        "coords": [(12.8250, 79.7150), (12.8380, 79.7000), (12.8650, 79.7280), (12.8310, 79.6950), (12.8050, 79.7020)],
        "default_area": "Semi-Urban"
    }
}

AREA_TYPES = ["Urban", "Semi-Urban", "Industrial", "Rural"]

np.random.seed(42)
NUM_SAMPLES = 5000

data = []
districts_list = list(LOCATION_DATA.keys())

for i in range(NUM_SAMPLES):
    district = np.random.choice(districts_list)
    place_idx = np.random.choice(len(LOCATION_DATA[district]["places"]))
    place = LOCATION_DATA[district]["places"][place_idx]
    
    area_type = np.random.choice(AREA_TYPES, p=[0.4, 0.3, 0.2, 0.1])
    
    if area_type == "Urban":
        pop_density = np.random.uniform(8000, 25000)
        elec_kwh = np.random.uniform(250, 1800)
        petrol_l = np.random.uniform(30, 250)
        diesel_l = np.random.uniform(10, 200)
        lpg_kg = np.random.uniform(14, 60)
        pub_trans_km = np.random.uniform(50, 800)
        waste_kg = np.random.uniform(20, 150)
        solar_kwh = np.random.uniform(0, 300)
        tree_cover = np.random.uniform(5, 25)
        aqi = np.random.uniform(80, 280)
    elif area_type == "Industrial":
        pop_density = np.random.uniform(4000, 15000)
        elec_kwh = np.random.uniform(500, 3500)
        petrol_l = np.random.uniform(40, 300)
        diesel_l = np.random.uniform(80, 500)
        lpg_kg = np.random.uniform(20, 90)
        pub_trans_km = np.random.uniform(30, 500)
        waste_kg = np.random.uniform(40, 300)
        solar_kwh = np.random.uniform(0, 500)
        tree_cover = np.random.uniform(3, 20)
        aqi = np.random.uniform(110, 320)
    elif area_type == "Semi-Urban":
        pop_density = np.random.uniform(3000, 10000)
        elec_kwh = np.random.uniform(150, 1000)
        petrol_l = np.random.uniform(20, 180)
        diesel_l = np.random.uniform(10, 150)
        lpg_kg = np.random.uniform(10, 45)
        pub_trans_km = np.random.uniform(20, 400)
        waste_kg = np.random.uniform(15, 90)
        solar_kwh = np.random.uniform(0, 250)
        tree_cover = np.random.uniform(12, 35)
        aqi = np.random.uniform(50, 180)
    else: # Rural
        pop_density = np.random.uniform(500, 4000)
        elec_kwh = np.random.uniform(80, 600)
        petrol_l = np.random.uniform(10, 100)
        diesel_l = np.random.uniform(5, 120)
        lpg_kg = np.random.uniform(5, 30)
        pub_trans_km = np.random.uniform(10, 250)
        waste_kg = np.random.uniform(8, 50)
        solar_kwh = np.random.uniform(0, 350)
        tree_cover = np.random.uniform(25, 65)
        aqi = np.random.uniform(30, 120)
        
    region_emission_factor = np.random.uniform(0.78, 0.88)
    
    elec_co2 = elec_kwh * region_emission_factor
    petrol_co2 = petrol_l * 2.31
    diesel_co2 = diesel_l * 2.68
    lpg_co2 = lpg_kg * 2.983
    waste_co2 = waste_kg * 0.45
    pub_co2 = pub_trans_km * 0.089
    
    solar_offset = solar_kwh * region_emission_factor * 0.95
    tree_offset = (tree_cover / 100.0) * (elec_co2 + petrol_co2 + diesel_co2) * 0.18
    
    multiplier = 1.0 + (aqi / 1500.0) + (pop_density / 200000.0)
    raw_emission = (elec_co2 + petrol_co2 + diesel_co2 + lpg_co2 + waste_co2 + pub_co2 - solar_offset - tree_offset) * multiplier
    
    noise = np.random.normal(0, 12.0)
    total_co2 = max(25.0, round(raw_emission + noise, 2))
    
    data.append({
        "District": district,
        "Place": place,
        "Area_Type": area_type,
        "Population_Density": round(pop_density, 1),
        "Electricity_kWh": round(elec_kwh, 1),
        "Petrol_Liters": round(petrol_l, 1),
        "Diesel_Liters": round(diesel_l, 1),
        "LPG_kg": round(lpg_kg, 1),
        "Public_Transport_km": round(pub_trans_km, 1),
        "Waste_Generated_kg": round(waste_kg, 1),
        "Solar_Energy_kWh": round(solar_kwh, 1),
        "Tree_Cover_Percent": round(tree_cover, 1),
        "AQI": round(aqi, 1),
        "Region_Emission_Factor": round(region_emission_factor, 3),
        "Carbon_Emission_kgCO2": total_co2
    })

df = pd.DataFrame(data)
dataset_path = os.path.join(DATASET_DIR, "carbon_emission_dataset.csv")
df.to_csv(dataset_path, index=False)
print(f"Dataset successfully created with {len(df)} records at: {dataset_path}")

print("--- Training & Comparing ML Regressors ---")

X = df.drop(columns=["Carbon_Emission_kgCO2"])
y = df["Carbon_Emission_kgCO2"]

categorical_cols = ["District", "Place", "Area_Type"]
label_encoders = {}
X_encoded = X.copy()

for col in categorical_cols:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X[col])
    label_encoders[col] = le

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
    "Extra Trees": ExtraTreesRegressor(n_estimators=100, random_state=42)
}

best_model = None
best_model_name = ""
best_r2 = -1
results = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    results[name] = {"MAE": mae, "MSE": mse, "RMSE": rmse, "R2": r2}
    print(f"Model: {name} | MAE: {mae:.3f} | RMSE: {rmse:.3f} | R2: {r2:.4f}")
    
    if r2 > best_r2:
        best_r2 = r2
        best_model = model
        best_model_name = name

print(f"\nBest Performing Model: {best_model_name} with R² = {best_r2:.4f}")

# Save artifacts
joblib.dump(best_model, os.path.join(MODELS_DIR, "carbon_model.pkl"))
joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))
joblib.dump(label_encoders, os.path.join(MODELS_DIR, "label_encoders.pkl"))

print("Saved model artifacts to models/ directory successfully.")

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# AI Carbon Emission Prediction & Monitoring - ML Training Notebook\n",
    "This notebook loads the Tamil Nadu carbon emission dataset, performs exploratory data analysis, encodes categorical variables, scales features, compares 4 regression algorithms (Linear Regression, Random Forest, Gradient Boosting, Extra Trees), evaluates performance metrics (MAE, MSE, RMSE, R²), and exports the optimal model artifacts for Flask application deployment."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import joblib\n",
    "from sklearn.model_selection import train_test_split\n",
    "from sklearn.preprocessing import StandardScaler, LabelEncoder\n",
    "from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor\n",
    "from sklearn.linear_model import LinearRegression\n",
    "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\n",
    "\n",
    "# Load Dataset\n",
    "df = pd.read_csv('../dataset/carbon_emission_dataset.csv')\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Data Summary\n",
    "print('Dataset Shape:', df.shape)\n",
    "df.info()\n",
    "df.describe()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Categorical Encoding & Feature Scaling\n",
    "X = df.drop(columns=['Carbon_Emission_kgCO2'])\n",
    "y = df['Carbon_Emission_kgCO2']\n",
    "\n",
    "label_encoders = {}\n",
    "X_encoded = X.copy()\n",
    "for col in ['District', 'Place', 'Area_Type']:\n",
    "    le = LabelEncoder()\n",
    "    X_encoded[col] = le.fit_transform(X[col])\n",
    "    label_encoders[col] = le\n",
    "\n",
    "scaler = StandardScaler()\n",
    "X_scaled = scaler.fit_transform(X_encoded)\n",
    "X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Model Training & Evaluation\n",
    "models = {\n",
    "    'Linear Regression': LinearRegression(),\n",
    "    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),\n",
    "    'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),\n",
    "    'Extra Trees': ExtraTreesRegressor(n_estimators=100, random_state=42)\n",
    "}\n",
    "\n",
    "results = []\n",
    "for name, model in models.items():\n",
    "    model.fit(X_train, y_train)\n",
    "    preds = model.predict(X_test)\n",
    "    mae = mean_absolute_error(y_test, preds)\n",
    "    mse = mean_squared_error(y_test, preds)\n",
    "    rmse = np.sqrt(mse)\n",
    "    r2 = r2_score(y_test, preds)\n",
    "    results.append({'Model': name, 'MAE': mae, 'MSE': mse, 'RMSE': rmse, 'R2': r2})\n",
    "\n",
    "results_df = pd.DataFrame(results)\n",
    "print(results_df.sort_values(by='R2', ascending=False))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Save Best Model\n",
    "best_model = RandomForestRegressor(n_estimators=100, random_state=42)\n",
    "best_model.fit(X_scaled, y)\n",
    "joblib.dump(best_model, '../models/carbon_model.pkl')\n",
    "joblib.dump(scaler, '../models/scaler.pkl')\n",
    "joblib.dump(label_encoders, '../models/label_encoders.pkl')\n",
    "print('Saved model artifacts successfully.')"
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

nb_path = os.path.join(NOTEBOOKS_DIR, "carbon_emission_training.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=2)

print(f"Jupyter notebook saved at: {nb_path}")
