import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from utils.prediction import prediction_engine
from utils.llm_recommender import generate_llm_recommendations

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    return dict(user_name=session.get('user_name'), user_id=session.get('user_id'))

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            conn.close()
            flash("Email address is already registered.", "warning")
            return render_template('register.html')

        hashed_pwd = generate_password_hash(password)
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     (name, email, hashed_pwd))
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    total_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    avg_co2 = conn.execute("SELECT AVG(predicted_emission) FROM predictions").fetchone()[0] or 0.0
    avg_score = conn.execute("SELECT AVG(environmental_score) FROM predictions").fetchone()[0] or 0.0
    
    highest_loc_row = conn.execute("SELECT district, place, predicted_emission FROM predictions ORDER BY predicted_emission DESC LIMIT 1").fetchone()
    lowest_loc_row = conn.execute("SELECT district, place, predicted_emission FROM predictions ORDER BY predicted_emission ASC LIMIT 1").fetchone()
    
    highest_loc = f"{highest_loc_row['district']} ({highest_loc_row['place']})" if highest_loc_row else "N/A"
    lowest_loc = f"{lowest_loc_row['district']} ({lowest_loc_row['place']})" if lowest_loc_row else "N/A"
    
    recent_preds = conn.execute("""
        SELECT p.*, u.name as user_name FROM predictions p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.timestamp DESC LIMIT 5
    """).fetchall()

    conn.close()

    metrics = {
        "total_predictions": total_preds,
        "avg_emission": round(avg_co2, 1),
        "avg_score": int(round(avg_score)),
        "highest_loc": highest_loc,
        "lowest_loc": lowest_loc
    }

    return render_template('dashboard.html', metrics=metrics, recent_predictions=recent_preds)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    conn = get_db_connection()
    districts = conn.execute("SELECT DISTINCT district FROM locations ORDER BY district").fetchall()
    district_names = [d['district'] for d in districts]

    if request.method == 'POST':
        try:
            district = request.form.get('district')
            place = request.form.get('place')
            area_type = request.form.get('area_type')

            pop_density = float(request.form.get('population_density', 0))
            elec_kwh = float(request.form.get('electricity_kwh', 0))
            petrol_l = float(request.form.get('petrol_liters', 0))
            diesel_l = float(request.form.get('diesel_liters', 0))
            lpg_kg = float(request.form.get('lpg_kg', 0))
            pub_trans_km = float(request.form.get('public_transport_km', 0))
            waste_kg = float(request.form.get('waste_generated_kg', 0))
            solar_kwh = float(request.form.get('solar_energy_kwh', 0))
            tree_cover = float(request.form.get('tree_cover_percent', 0))
            aqi = float(request.form.get('aqi', 0))
            region_ef = float(request.form.get('region_emission_factor', 0.82))

            if any(val < 0 for val in [pop_density, elec_kwh, petrol_l, diesel_l, lpg_kg, pub_trans_km, waste_kg, solar_kwh, tree_cover, aqi]):
                flash("Negative values are not permitted in consumption parameters.", "danger")
                conn.close()
                return render_template('prediction.html', districts=district_names)

            input_dict = {
                "District": district,
                "Place": place,
                "Area_Type": area_type,
                "Population_Density": pop_density,
                "Electricity_kWh": elec_kwh,
                "Petrol_Liters": petrol_l,
                "Diesel_Liters": diesel_l,
                "LPG_kg": lpg_kg,
                "Public_Transport_km": pub_trans_km,
                "Waste_Generated_kg": waste_kg,
                "Solar_Energy_kWh": solar_kwh,
                "Tree_Cover_Percent": tree_cover,
                "AQI": aqi,
                "Region_Emission_Factor": region_ef
            }

            res = prediction_engine.predict(input_dict)

            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO predictions (
                user_id, district, place, area_type, population_density, electricity_kwh,
                petrol_liters, diesel_liters, lpg_kg, public_transport_km, waste_generated_kg,
                solar_energy_kwh, tree_cover_percent, aqi, predicted_emission,
                environmental_score, emission_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['user_id'], district, place, area_type, pop_density, elec_kwh,
                petrol_l, diesel_l, lpg_kg, pub_trans_km, waste_kg,
                solar_kwh, tree_cover, aqi, res["predicted_emission"],
                res["environmental_score"], res["emission_category"]
            ))
            pred_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return redirect(url_for('result', pred_id=pred_id))

        except Exception as e:
            conn.close()
            flash(f"Error executing prediction: {str(e)}", "danger")
            return render_template('prediction.html', districts=district_names)

    conn.close()
    return render_template('prediction.html', districts=district_names)

@app.route('/result/<int:pred_id>')
@login_required
def result(pred_id):
    conn = get_db_connection()
    pred = conn.execute("""
        SELECT p.*, u.name as user_name, l.latitude, l.longitude 
        FROM predictions p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN locations l ON p.district = l.district AND p.place = l.place
        WHERE p.id = ?
    """, (pred_id,)).fetchone()
    conn.close()

    if not pred:
        flash("Prediction record not found.", "warning")
        return redirect(url_for('history'))

    input_dict = {
        "District": pred['district'],
        "Place": pred['place'],
        "Area_Type": pred['area_type'],
        "Population_Density": pred['population_density'],
        "Electricity_kWh": pred['electricity_kwh'],
        "Petrol_Liters": pred['petrol_liters'],
        "Diesel_Liters": pred['diesel_liters'],
        "LPG_kg": pred['lpg_kg'],
        "Public_Transport_km": pred['public_transport_km'],
        "Waste_Generated_kg": pred['waste_generated_kg'],
        "Solar_Energy_kWh": pred['solar_energy_kwh'],
        "Tree_Cover_Percent": pred['tree_cover_percent'],
        "AQI": pred['aqi'],
        "Region_Emission_Factor": 0.82
    }

    res = prediction_engine.predict(input_dict)

    return render_template('result.html', pred=pred, result_data=res)

@app.route('/history')
@login_required
def history():
    district_filter = request.args.get('district', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()

    conn = get_db_connection()
    query = "SELECT p.*, u.name as user_name FROM predictions p LEFT JOIN users u ON p.user_id = u.id WHERE 1=1"
    params = []

    if district_filter:
        query += " AND p.district = ?"
        params.append(district_filter)
        
    if category_filter:
        query += " AND p.emission_category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (p.district LIKE ? OR p.place LIKE ? OR u.name LIKE ?)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])

    query += " ORDER BY p.timestamp DESC"
    predictions = conn.execute(query, params).fetchall()

    districts = conn.execute("SELECT DISTINCT district FROM locations ORDER BY district").fetchall()
    conn.close()

    return render_template('history.html', predictions=predictions, districts=districts,
                           selected_district=district_filter, selected_category=category_filter,
                           search_query=search_query)

@app.route('/map')
@login_required
def map_view():
    return render_template('map.html')

@app.route('/about')
def about():
    return render_template('about.html')

# --- API ENDPOINTS ---

@app.route('/api/llm-recommendation/<int:pred_id>')
def api_llm_recommendation(pred_id):
    conn = get_db_connection()
    pred = conn.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,)).fetchone()
    conn.close()

    if not pred:
        return jsonify({"error": "Prediction record not found"}), 404

    input_dict = {
        "District": pred['district'],
        "Place": pred['place'],
        "Area_Type": pred['area_type'],
        "Population_Density": pred['population_density'],
        "Electricity_kWh": pred['electricity_kwh'],
        "Petrol_Liters": pred['petrol_liters'],
        "Diesel_Liters": pred['diesel_liters'],
        "LPG_kg": pred['lpg_kg'],
        "Public_Transport_km": pred['public_transport_km'],
        "Waste_Generated_kg": pred['waste_generated_kg'],
        "Solar_Energy_kWh": pred['solar_energy_kwh'],
        "Tree_Cover_Percent": pred['tree_cover_percent'],
        "AQI": pred['aqi'],
        "Region_Emission_Factor": 0.82
    }

    pred_res = {
        "predicted_emission": pred['predicted_emission'],
        "emission_category": pred['emission_category'],
        "environmental_score": pred['environmental_score'],
        "tree_offset": prediction_engine.calculate_tree_offset(pred['predicted_emission'])
    }

    llm_output = generate_llm_recommendations(input_dict, pred_res)
    return jsonify(llm_output)

@app.route('/get_places/<district>')
def get_places(district):
    conn = get_db_connection()
    rows = conn.execute("SELECT place, area_type FROM locations WHERE district = ? ORDER BY place", (district,)).fetchall()
    conn.close()
    places = [{"place": r['place'], "area_type": r['area_type']} for r in rows]
    return jsonify(places)

@app.route('/api/predictions')
def api_predictions():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM predictions ORDER BY timestamp DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/district-summary')
def api_district_summary():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT district, COUNT(*) as count, AVG(predicted_emission) as avg_emission, AVG(environmental_score) as avg_score
        FROM predictions GROUP BY district ORDER BY avg_emission DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/map-data')
def api_map_data():
    conn = get_db_connection()
    query = """
        SELECT l.district, l.place, l.latitude, l.longitude, l.area_type,
               p.predicted_emission, p.environmental_score, p.emission_category, p.timestamp
        FROM locations l
        LEFT JOIN (
            SELECT p1.* FROM predictions p1
            INNER JOIN (
                SELECT district, place, MAX(timestamp) as max_ts
                FROM predictions GROUP BY district, place
            ) p2 ON p1.district = p2.district AND p1.place = p2.place AND p1.timestamp = p2.max_ts
        ) p ON l.district = p.district AND l.place = p.place
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    data = []
    for r in rows:
        emission = r['predicted_emission'] if r['predicted_emission'] is not None else 180.0
        score = r['environmental_score'] if r['environmental_score'] is not None else 75
        category = r['emission_category'] if r['emission_category'] is not None else "Moderate"

        data.append({
            "district": r['district'],
            "place": r['place'],
            "latitude": r['latitude'],
            "longitude": r['longitude'],
            "area_type": r['area_type'],
            "emission": round(float(emission), 1),
            "score": int(score),
            "category": category
        })

    return jsonify(data)

if __name__ == '__main__':
    print("Starting AI Carbon Emission Monitoring System on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
