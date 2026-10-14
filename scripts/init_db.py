import os
from sqlalchemy import create_engine, text
from pymongo import MongoClient, ASCENDING, DESCENDING

# Use postgresql+psycopg2 to explicitly use psycopg2-binary
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql+psycopg2://postgres:postgres@localhost:5432/vehicle_health_db")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

def setup_databases():
    print("--- 1. Setting up PostgreSQL Schemas ---")
    engine = create_engine(POSTGRES_URI)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vehicle_types (
                    vehicle_type_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                );
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id VARCHAR(50) PRIMARY KEY,
                    vehicle_type_id VARCHAR(50) REFERENCES vehicle_types(vehicle_type_id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL
                );
                CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id VARCHAR(50) PRIMARY KEY,
                    vehicle_type_id VARCHAR(50) REFERENCES vehicle_types(vehicle_type_id) ON DELETE CASCADE,
                    dataset_id VARCHAR(50) REFERENCES datasets(dataset_id) ON DELETE SET NULL,
                    manufacturer VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS models (
                    model_id VARCHAR(50) PRIMARY KEY,
                    dataset_id VARCHAR(50) REFERENCES datasets(dataset_id) ON DELETE CASCADE,
                    model_name VARCHAR(100) NOT NULL,
                    architecture_type VARCHAR(50) NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    metrics JSONB,
                    trained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id SERIAL PRIMARY KEY,
                    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
                    model_id VARCHAR(50) REFERENCES models(model_id) ON DELETE CASCADE,
                    risk_score FLOAT NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
                    risk_category VARCHAR(20) NOT NULL,
                    confidence FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id SERIAL PRIMARY KEY,
                    prediction_id INT UNIQUE REFERENCES predictions(prediction_id) ON DELETE CASCADE,
                    explanation_text TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            conn.execute(text("""
                INSERT INTO vehicle_types (vehicle_type_id, name) VALUES 
                ('truck', 'Heavy Truck'), 
                ('aircraft', 'Aircraft Turbofan Engine'), 
                ('ev', 'Electric Vehicle')
                ON CONFLICT (vehicle_type_id) DO NOTHING;
                
                INSERT INTO datasets (dataset_id, vehicle_type_id, name) VALUES 
                ('scania_aps', 'truck', 'Scania APS Dataset'), 
                ('nasa_cmapss', 'aircraft', 'NASA C-MAPSS FD001'), 
                ('tum_ev', 'ev', 'TUM EV UDS Dataset')
                ON CONFLICT (dataset_id) DO NOTHING;
            """))
    print("PostgreSQL tables and seed records created.")

    print("\n--- 2. Setting up MongoDB Indexes ---")
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["vehicle_health_db"]
    telemetry_col = db["telemetry"]
    
    telemetry_col.create_index(
        [("vehicle_id", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_vehicle_time"
    )
    print("MongoDB indexes created.")

if __name__ == "__main__":
    try:
        setup_databases()
        print("\nDatabase initialization completed successfully!")
    except Exception as e:
        print(f"\nError initializing databases: {e}")
