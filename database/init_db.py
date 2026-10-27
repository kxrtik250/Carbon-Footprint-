import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "carbon_emission.db")

os.makedirs(DB_DIR, exist_ok=True)

# 10 Districts and 50 Places in Tamil Nadu with accurate coordinates
LOCATION_SEED_DATA = [
    # Chennai
    ("Chennai", "Adyar", 13.0067, 80.2572, "Urban"),
    ("Chennai", "Anna Nagar", 13.0850, 80.2101, "Urban"),
    ("Chennai", "Guindy", 13.0067, 80.2020, "Urban"),
    ("Chennai", "Velachery", 12.9815, 80.2180, "Urban"),
    ("Chennai", "T. Nagar", 13.0418, 80.2341, "Urban"),
    # Coimbatore
    ("Coimbatore", "Gandhipuram", 11.0168, 76.9558, "Urban"),
    ("Coimbatore", "Peelamedu", 11.0284, 77.0007, "Industrial"),
    ("Coimbatore", "RS Puram", 11.0084, 76.9490, "Urban"),
    ("Coimbatore", "Saravanampatti", 11.0800, 76.9930, "Semi-Urban"),
    ("Coimbatore", "Singanallur", 10.9980, 77.0300, "Industrial"),
    # Madurai
    ("Madurai", "Mattuthavani", 9.9472, 78.1561, "Semi-Urban"),
    ("Madurai", "Goripalayam", 9.9290, 78.1250, "Urban"),
    ("Madurai", "Simmakkal", 9.9230, 78.1180, "Urban"),
    ("Madurai", "Thiruparankundram", 9.8820, 78.0710, "Semi-Urban"),
    ("Madurai", "Anna Nagar", 9.9180, 78.1460, "Urban"),
    # Tiruchirappalli
    ("Tiruchirappalli", "Srirangam", 10.8622, 78.6946, "Semi-Urban"),
    ("Tiruchirappalli", "Thillai Nagar", 10.8250, 78.6850, "Urban"),
    ("Tiruchirappalli", "Cantonment", 10.8060, 78.6880, "Urban"),
    ("Tiruchirappalli", "K.K. Nagar", 10.7850, 78.6960, "Semi-Urban"),
    ("Tiruchirappalli", "Chatram", 10.8340, 78.6910, "Urban"),
    # Salem
    ("Salem", "Hasthampatti", 11.6740, 78.1630, "Semi-Urban"),
    ("Salem", "Fairlands", 11.6710, 78.1420, "Urban"),
    ("Salem", "Suramangalam", 11.6850, 78.1200, "Industrial"),
    ("Salem", "Ammapet", 11.6540, 78.1800, "Industrial"),
    ("Salem", "Shevapet", 11.6450, 78.1400, "Urban"),
    # Tirunelveli
    ("Tirunelveli", "Palayamkottai", 8.7139, 77.7340, "Semi-Urban"),
    ("Tirunelveli", "Junction", 8.7290, 77.7000, "Urban"),
    ("Tirunelveli", "Melapalayam", 8.7010, 77.7120, "Semi-Urban"),
    ("Tirunelveli", "Vannarpettai", 8.7240, 77.7260, "Urban"),
    ("Tirunelveli", "Pettai", 8.7400, 77.6700, "Industrial"),
    # Erode
    ("Erode", "Perundurai", 11.2750, 77.5830, "Industrial"),
    ("Erode", "Collectorate", 11.3360, 77.7180, "Urban"),
    ("Erode", "BPS", 11.3410, 77.7270, "Urban"),
    ("Erode", "Thindal", 11.3200, 77.6780, "Semi-Urban"),
    ("Erode", "Surampatti", 11.3280, 77.7100, "Industrial"),
    # Vellore
    ("Vellore", "Sathuvachari", 12.9350, 79.1600, "Semi-Urban"),
    ("Vellore", "Katpadi", 12.9750, 79.1350, "Urban"),
    ("Vellore", "Gandhi Nagar", 12.9550, 79.1450, "Urban"),
    ("Vellore", "Thorapadi", 12.8950, 79.1200, "Rural"),
    ("Vellore", "Bagayam", 12.8750, 79.1300, "Semi-Urban"),
    # Thanjavur
    ("Thanjavur", "Old Bus Stand", 10.7870, 79.1370, "Urban"),
    ("Thanjavur", "Medical College Road", 10.7600, 79.1150, "Semi-Urban"),
    ("Thanjavur", "Vallam", 10.7100, 79.0560, "Rural"),
    ("Thanjavur", "Karanthai", 10.8010, 79.1450, "Semi-Urban"),
    ("Thanjavur", "Punnainallur", 10.7750, 79.1850, "Rural"),
    # Kanchipuram
    ("Kanchipuram", "Little Kanchipuram", 12.8250, 79.7150, "Semi-Urban"),
    ("Kanchipuram", "Big Kanchipuram", 12.8380, 79.7000, "Urban"),
    ("Kanchipuram", "Enathur", 12.8650, 79.7280, "Rural"),
    ("Kanchipuram", "Collectorate", 12.8310, 79.6950, "Urban"),
    ("Kanchipuram", "Orikkai", 12.8050, 79.7020, "Semi-Urban")
]

INITIAL_PREDICTIONS = [
    (1, "Chennai", "Adyar", "Urban", 18500, 850, 120, 80, 28, 450, 65, 120, 12, 142, 590.5, 41, "Very High", "2026-08-15 10:30:00"),
    (1, "Coimbatore", "RS Puram", "Urban", 12000, 450, 60, 40, 18, 220, 35, 180, 22, 95, 295.2, 70, "Moderate", "2026-08-16 11:15:00"),
    (1, "Madurai", "Thiruparankundram", "Semi-Urban", 6500, 280, 35, 20, 12, 150, 22, 100, 32, 75, 178.4, 82, "Moderate", "2026-08-16 14:20:00"),
    (1, "Thanjavur", "Vallam", "Rural", 2200, 140, 20, 10, 8, 80, 12, 220, 48, 52, 92.1, 91, "Low", "2026-08-17 09:00:00"),
    (1, "Salem", "Ammapet", "Industrial", 11500, 1450, 180, 260, 45, 180, 120, 50, 8, 210, 940.8, 6, "Very High", "2026-08-17 12:45:00"),
    (1, "Tiruchirappalli", "Srirangam", "Semi-Urban", 5800, 320, 40, 25, 15, 190, 28, 140, 28, 82, 212.6, 79, "Moderate", "2026-08-17 14:10:00"),
    (1, "Erode", "Perundurai", "Industrial", 9200, 980, 110, 190, 32, 160, 85, 90, 14, 175, 680.3, 32, "High", "2026-08-17 15:30:00")
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Locations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district TEXT NOT NULL,
        place TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        area_type TEXT NOT NULL,
        UNIQUE(district, place)
    );
    """)
    
    # 3. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        district TEXT NOT NULL,
        place TEXT NOT NULL,
        area_type TEXT NOT NULL,
        population_density REAL NOT NULL,
        electricity_kwh REAL NOT NULL,
        petrol_liters REAL NOT NULL,
        diesel_liters REAL NOT NULL,
        lpg_kg REAL NOT NULL,
        public_transport_km REAL NOT NULL,
        waste_generated_kg REAL NOT NULL,
        solar_energy_kwh REAL NOT NULL,
        tree_cover_percent REAL NOT NULL,
        aqi REAL NOT NULL,
        predicted_emission REAL NOT NULL,
        environmental_score INTEGER NOT NULL,
        emission_category TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)
    
    # Seed Demo User if not exists
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@carbon.ai",))
    if not cursor.fetchone():
        hashed_pwd = generate_password_hash("admin123")
        cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                       ("Eco Admin", "demo@carbon.ai", hashed_pwd))
        print("Demo user created: demo@carbon.ai / admin123")
        
    # Seed Locations
    for district, place, lat, lon, area in LOCATION_SEED_DATA:
        cursor.execute("""
        INSERT OR REPLACE INTO locations (district, place, latitude, longitude, area_type)
        VALUES (?, ?, ?, ?, ?)
        """, (district, place, lat, lon, area))
        
    # Seed Initial Predictions if predictions table empty
    cursor.execute("SELECT COUNT(*) FROM predictions")
    if cursor.fetchone()[0] == 0:
        for user_id, district, place, area, pop_den, elec, pet, dies, lpg, pub, waste, solar, tree, aqi, pred_co2, score, cat, ts in INITIAL_PREDICTIONS:
            cursor.execute("""
            INSERT INTO predictions (
                user_id, district, place, area_type, population_density, electricity_kwh,
                petrol_liters, diesel_liters, lpg_kg, public_transport_km, waste_generated_kg,
                solar_energy_kwh, tree_cover_percent, aqi, predicted_emission,
                environmental_score, emission_category, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, district, place, area, pop_den, elec, pet, dies, lpg, pub, waste, solar, tree, aqi, pred_co2, score, cat, ts))
        print("Seeded initial historical prediction records.")
        
    conn.commit()
    conn.close()
    print("Database carbon_emission.db initialized successfully.")

if __name__ == "__main__":
    init_db()
