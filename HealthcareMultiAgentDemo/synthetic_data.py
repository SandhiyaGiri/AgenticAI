import sqlite3
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import json

# Initialize Faker
fake = Faker()

# Configuration
NUM_USERS = 100
DATABASE_NAME = "synthetic_health_data.db"

# Define realistic data distributions
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
]

DIETARY_CATEGORIES = ["Standard", "Vegetarian", "Vegan"]

MEDICAL_CONDITIONS = [
    "Type 1 Diabetes", "Type 2 Diabetes", "Hypertension", 
    "High Cholesterol", "Obesity", "Pre-diabetes", "None"
]

# CGM ranges based on medical conditions (mg/dL)
CGM_RANGES = {
    "Type 1 Diabetes": (80, 250),
    "Type 2 Diabetes": (90, 220),
    "Pre-diabetes": (85, 180),
    "None": (70, 140),
    "default": (80, 160)
}

def create_database():
    """Create SQLite database with proper schema"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            city TEXT NOT NULL,
            dietary_category TEXT NOT NULL,
            medical_conditions TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create health_metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_metrics (
            metric_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            cgm_reading REAL NOT NULL,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            heart_rate INTEGER,
            weight_kg REAL,
            recorded_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    return conn

def generate_medical_conditions():
    """Generate realistic medical condition combinations"""
    # 30% have no conditions
    if random.random() < 0.3:
        return ["None"]
    
    conditions = []
    
    # Primary diabetes conditions (mutually exclusive)
    diabetes_chance = random.random()
    if diabetes_chance < 0.08:  # 8% Type 1
        conditions.append("Type 1 Diabetes")
    elif diabetes_chance < 0.25:  # 17% Type 2
        conditions.append("Type 2 Diabetes")
    elif diabetes_chance < 0.35:  # 10% Pre-diabetes
        conditions.append("Pre-diabetes")
    
    # Secondary conditions (can co-occur)
    if random.random() < 0.25:
        conditions.append("Hypertension")
    if random.random() < 0.20:
        conditions.append("High Cholesterol")
    if random.random() < 0.15:
        conditions.append("Obesity")
    
    return conditions if conditions else ["None"]

def get_cgm_range(medical_conditions):
    """Get appropriate CGM range based on medical conditions"""
    for condition in medical_conditions:
        if condition in CGM_RANGES:
            return CGM_RANGES[condition]
    return CGM_RANGES["default"]

def generate_blood_pressure(medical_conditions, age):
    """Generate realistic blood pressure based on conditions and age"""
    has_hypertension = "Hypertension" in medical_conditions
    
    if has_hypertension:
        # Hypertensive ranges
        systolic = random.randint(140, 180)
        diastolic = random.randint(90, 110)
    else:
        # Normal ranges, slightly higher with age
        age_factor = max(0, (age - 20) * 0.5)
        systolic = random.randint(110, 130) + int(age_factor)
        diastolic = random.randint(70, 85) + int(age_factor * 0.3)
    
    return systolic, diastolic

def generate_weight(age, medical_conditions):
    """Generate realistic weight based on age and conditions"""
    base_weight = random.uniform(55, 85)  # Base weight in kg
    
    # Age factor
    age_factor = max(0, (age - 25) * 0.2)
    
    # Obesity condition
    if "Obesity" in medical_conditions:
        obesity_factor = random.uniform(15, 35)
    else:
        obesity_factor = 0
    
    return round(base_weight + age_factor + obesity_factor, 1)

def generate_user_data():
    """Generate synthetic user data"""
    users = []
    
    # Ensure roughly equal distribution of dietary categories
    dietary_dist = []
    for category in DIETARY_CATEGORIES:
        dietary_dist.extend([category] * (NUM_USERS // 3))
    
    # Add remaining slots
    remaining = NUM_USERS - len(dietary_dist)
    dietary_dist.extend(random.choices(DIETARY_CATEGORIES, k=remaining))
    
    # Shuffle to randomize
    random.shuffle(dietary_dist)
    
    for i in range(NUM_USERS):
        user_id = str(uuid.uuid4())
        name = fake.name()
        age = random.randint(18, 85)
        city = random.choice(CITIES)
        dietary_category = dietary_dist[i]
        medical_conditions = generate_medical_conditions()
        
        users.append({
            'user_id': user_id,
            'name': name,
            'age': age,
            'city': city,
            'dietary_category': dietary_category,
            'medical_conditions': json.dumps(medical_conditions)
        })
    
    return users

def generate_health_metrics(users):
    """Generate health metrics for each user"""
    metrics = []
    
    for user in users:
        user_id = user['user_id']
        age = user['age']
        medical_conditions = json.loads(user['medical_conditions'])
        
        # Generate 1-5 health records per user over the past 6 months
        num_records = random.randint(1, 5)
        
        for _ in range(num_records):
            metric_id = str(uuid.uuid4())
            
            # CGM reading based on medical conditions
            cgm_min, cgm_max = get_cgm_range(medical_conditions)
            cgm_reading = round(random.uniform(cgm_min, cgm_max), 1)
            
            # Blood pressure
            systolic, diastolic = generate_blood_pressure(medical_conditions, age)
            
            # Heart rate (affected by age and conditions)
            base_hr = random.randint(60, 100)
            if "Type 1 Diabetes" in medical_conditions:
                base_hr += random.randint(-5, 15)
            heart_rate = max(50, min(120, base_hr))
            
            # Weight
            weight = generate_weight(age, medical_conditions)
            
            # Random timestamp in the past 6 months
            days_ago = random.randint(0, 180)
            recorded_at = datetime.now() - timedelta(days=days_ago)
            
            metrics.append({
                'metric_id': metric_id,
                'user_id': user_id,
                'cgm_reading': cgm_reading,
                'blood_pressure_systolic': systolic,
                'blood_pressure_diastolic': diastolic,
                'heart_rate': heart_rate,
                'weight_kg': weight,
                'recorded_at': recorded_at.isoformat()
            })
    
    return metrics

def insert_data(conn, users, metrics):
    """Insert generated data into database"""
    cursor = conn.cursor()
    
    # Insert users
    cursor.executemany('''
        INSERT INTO users (user_id, name, age, city, dietary_category, medical_conditions)
        VALUES (:user_id, :name, :age, :city, :dietary_category, :medical_conditions)
    ''', users)
    
    # Insert health metrics
    cursor.executemany('''
        INSERT INTO health_metrics 
        (metric_id, user_id, cgm_reading, blood_pressure_systolic, 
         blood_pressure_diastolic, heart_rate, weight_kg, recorded_at)
        VALUES (:metric_id, :user_id, :cgm_reading, :blood_pressure_systolic,
                :blood_pressure_diastolic, :heart_rate, :weight_kg, :recorded_at)
    ''', metrics)
    
    conn.commit()

def validate_data(conn):
    """Validate data consistency and print statistics"""
    cursor = conn.cursor()
    
    print("=== Dataset Validation Report ===\n")
    
    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Total Users: {user_count}")
    
    cursor.execute("SELECT COUNT(*) FROM health_metrics")
    metrics_count = cursor.fetchone()[0]
    print(f"Total Health Metrics: {metrics_count}")
    
    # City distribution
    print("\n--- City Distribution ---")
    cursor.execute("SELECT city, COUNT(*) FROM users GROUP BY city ORDER BY COUNT(*) DESC")
    for city, count in cursor.fetchall():
        print(f"{city}: {count} users")
    
    # Dietary category distribution
    print("\n--- Dietary Category Distribution ---")
    cursor.execute("SELECT dietary_category, COUNT(*) FROM users GROUP BY dietary_category")
    for category, count in cursor.fetchall():
        print(f"{category}: {count} users")
    
    # Medical conditions analysis
    print("\n--- Medical Conditions Analysis ---")
    cursor.execute("SELECT medical_conditions FROM users")
    condition_counts = {}
    for (conditions_json,) in cursor.fetchall():
        conditions = json.loads(conditions_json)
        for condition in conditions:
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
    
    for condition, count in sorted(condition_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{condition}: {count} users")
    
    # CGM validation for diabetes patients
    print("\n--- CGM Range Validation ---")
    cursor.execute('''
        SELECT u.medical_conditions, 
               MIN(h.cgm_reading) as min_cgm,
               MAX(h.cgm_reading) as max_cgm,
               AVG(h.cgm_reading) as avg_cgm,
               COUNT(h.cgm_reading) as readings_count
        FROM users u
        JOIN health_metrics h ON u.user_id = h.user_id
        GROUP BY u.medical_conditions
    ''')
    
    for conditions_json, min_cgm, max_cgm, avg_cgm, count in cursor.fetchall():
        conditions = json.loads(conditions_json)
        condition_str = ", ".join(conditions)
        print(f"{condition_str}: CGM range {min_cgm:.1f}-{max_cgm:.1f} mg/dL (avg: {avg_cgm:.1f}, {count} readings)")

def main():
    """Main execution function"""
    print("Generating synthetic health dataset...")
    
    # Set random seed for reproducibility
    random.seed(42)
    Faker.seed(42)
    
    # Create database
    conn = create_database()
    
    # Generate data
    print("Generating user data...")
    users = generate_user_data()
    
    print("Generating health metrics...")
    metrics = generate_health_metrics(users)
    
    # Insert data
    print("Inserting data into database...")
    insert_data(conn, users, metrics)
    
    # Validate and report
    validate_data(conn)
    
    print(f"\nDataset successfully created: {DATABASE_NAME}")
    print("Database contains users and health_metrics tables with realistic, validated data.")
    
    conn.close()

if __name__ == "__main__":
    main()
