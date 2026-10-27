# AI-Based Carbon Emission Prediction & Monitoring System

A complete, production-ready full-stack web application designed for predicting, monitoring, and visualizing carbon emissions across districts and places in Tamil Nadu, India. The application integrates a Machine Learning regression pipeline, SQLite database, Flask REST backend, interactive Leaflet.js + OpenStreetMap visualization, and real-time Chart.js analytics dashboard.

---

## Key Features

1. **Machine Learning Emission Prediction**:
   - Predicts carbon emissions ($kg CO_2/month$) based on 14 environmental and energy consumption parameters.
   - Evaluates Environmental Score (0 - 100) and tree offset requirement (trees/year).
   - Categorizes emission severity: `Low`, `Moderate`, `High`, `Very High`.

2. **Real Interactive Geolocation Map**:
   - Powered by **Leaflet.js + OpenStreetMap** (100% free, no Google Maps API or paid key required).
   - Includes color-coded markers matching emission categories with interactive popups.
   - Centers dynamically on selected prediction locations.

3. **Analytics Dashboard**:
   - Interactive metric cards tracking total predictions, average emissions, average environmental scores, and extreme emission locations.
   - 4 Chart.js visualization graphs:
     - Average Emission by District (Bar Chart)
     - Emission Category Distribution (Doughnut Chart)
     - Environmental Score Distribution (Polar Area Chart)
     - Historical Emission Trend (Line Chart)

4. **Dynamic Location Selection**:
   - District selection automatically populates Place dropdown via AJAX (`/get_places/<district>`).

5. **Explainability & Recommendation Engine**:
   - Provides feature contribution breakdowns detailing positive contributors (electricity, fuel, waste) vs offsets (solar energy, tree cover).
   - Generates input-driven environmental recommendations.

6. **Prediction History & Printable Reports**:
   - Searchable, filterable prediction history table backed by SQLite (`carbon_emission.db`).
   - Printable result certificates with `@media print` layout.

7. **User Authentication**:
   - Secure login & registration with password hashing (`werkzeug.security`) and Flask sessions.

---

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Leaflet.js (Map), Chart.js (Graphs)
- **Backend**: Python 3.11+, Flask, Jinja2
- **Machine Learning**: Scikit-Learn, Pandas, NumPy, Joblib
- **Database**: SQLite (`database/carbon_emission.db`)

The local SQLite database is created by `database/init_db.py` and is intentionally excluded from Git because it stores user accounts and prediction history.

---

## Project Structure

```text
carbon_emission_system/
│
├── app.py                         # Main Flask application & routes
├── config.py                      # Application configuration & parameters
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
│
├── database/
│   ├── carbon_emission.db         # SQLite database
│   └── init_db.py                 # Database creation & seeding script
│
├── models/
│   ├── carbon_model.pkl           # Trained ML model
│   ├── scaler.pkl                 # StandardScaler object
│   └── label_encoders.pkl         # LabelEncoders for categorical features
│
├── notebooks/
│   └── carbon_emission_training.ipynb # Notebook for ML training & comparison
│
├── dataset/
│   └── carbon_emission_dataset.csv    # 5,000-record Tamil Nadu dataset
│
├── templates/
│   ├── base.html                  # Jinja master layout
│   ├── login.html                 # Login page
│   ├── register.html              # Registration page
│   ├── dashboard.html             # Chart.js analytics dashboard
│   ├── prediction.html            # User input form
│   ├── result.html                # Prediction report page
│   ├── map.html                   # Leaflet map dashboard
│   ├── history.html               # Prediction history log
│   └── about.html                 # Methodology & guide
│
├── static/
│   ├── css/
│   │   └── style.css              # Custom Eco-Tech stylesheet
│   └── js/
│       ├── dashboard.js           # Chart.js analytics scripts
│       ├── map.js                 # Leaflet map rendering script
│       └── prediction.js          # Dynamic AJAX dropdown & form validator
│
└── utils/
    ├── preprocessing.py           # Feature encoding & scaling transformer
    └── prediction.py              # ML inference engine & scoring
```

---

## Quick Start & Installation

### 1. Prerequisite
Ensure Python 3.11+ is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Generate Models (If Needed)
```bash
# Run database seeding
python database/init_db.py

# Optional: Regenerate dataset & train models
python generate_dataset_and_models.py
```

### 4. Run Application
```bash
python app.py
```

The Flask server will start at:
`http://127.0.0.1:5000`

---

## Demo account

- **Email**: `demo@carbon.ai`
- **Password**: `admin123`

The demo account is created locally by the database initialization script. Change or remove it before deploying publicly.

---

## API Endpoints

- `GET /get_places/<district>`: Returns JSON array of places for selected district.
- `GET /api/predictions`: Returns JSON list of all predictions stored in SQLite.
- `GET /api/district-summary`: Returns JSON aggregated emission averages per district.
- `GET /api/map-data`: Returns JSON coordinates and prediction metrics for map pins.

---

## Map Implementation Details

The application uses **Leaflet.js + OpenStreetMap** tiles. No Google Maps API key or paid credit card registration is required. Geolocation coordinates (latitude & longitude) for 50 Tamil Nadu places across 10 districts are maintained in the SQLite `locations` database table.
