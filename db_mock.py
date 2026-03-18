#!/usr/bin/env python3
"""
Database mock data utility.

Usage:
    python db_mock.py backup      # Save current data to backup.json
    python db_mock.py populate    # Delete all data and insert 200 mock records
    python db_mock.py restore     # Restore data from backup.json
"""

import sys
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
from dotenv import load_dotenv

# Load environment
load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("❌ Error: supabase not installed. Run: pip install supabase")
    sys.exit(1)


def get_supabase_client():
    """Create and return Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
        sys.exit(1)
    
    return create_client(url, key)


def backup_data():
    """Backup all current data to backup.json"""
    print("💾 Backing up current data...")
    
    supabase = get_supabase_client()
    backup = {}
    
    try:
        # Fetch all records from each table
        cycles_resp = supabase.table("plant_cycles").select("*").execute()
        backup["plant_cycles"] = cycles_resp.data or []
        
        sensor_resp = supabase.table("sensor_readings").select("*").execute()
        backup["sensor_readings"] = sensor_resp.data or []
        
        ai_resp = supabase.table("ai_analyses").select("*").execute()
        backup["ai_analyses"] = ai_resp.data or []
        
        actuator_resp = supabase.table("actuator_actions").select("*").execute()
        backup["actuator_actions"] = actuator_resp.data or []
        
        # Save to file
        with open("backup.json", "w") as f:
            json.dump(backup, f, indent=2, default=str)
        
        total = sum(len(v) for v in backup.values())
        print(f"✅ Backed up {total} records to backup.json")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)


def clear_data():
    """Delete all data from tables (careful!)"""
    print("⚠️  Clearing all data from database...")
    
    supabase = get_supabase_client()
    
    try:
        # Order matters: delete dependent tables first
        supabase.table("actuator_actions").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("ai_analyses").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("sensor_readings").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("plant_cycles").delete().gt("created_at", "1900-01-01").execute()
        
        print("✅ All data cleared")
        
    except Exception as e:
        print(f"❌ Clear failed: {e}")
        sys.exit(1)


def populate_mock_data():
    """Generate and insert 200 mock records"""
    print("🌿 Generating 200 mock records...")
    
    supabase = get_supabase_client()
    
    # Diseases and plants for variety
    diseases = ["No disease found", "Leaf spot", "Powdery mildew", "Root rot", "Blight", "Leaf curl"]
    plants = ["Tomato", "Lettuce", "Basil", "Spinach", "Pepper", "Cucumber"]
    light_states = ["BRIGHT", "DARK"]
    
    try:
        for i in range(200):
            # Create a time spread over the last 200 hours
            hours_ago = 200 - i
            captured_at = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
            
            # Insert plant cycle
            cycle_payload = {
                "captured_at": captured_at,
                "image_url": f"https://mock.local/supabase/plant_{i:03d}.jpg",
            }
            cycle_resp = supabase.table("plant_cycles").insert(cycle_payload).execute()
            cycle_id = cycle_resp.data[0]["id"]
            
            # Sensor readings - realistic ranges
            temp = round(20 + random.gauss(5, 2), 1)  # 15-30°C
            hum = round(50 + random.gauss(10, 5), 1)  # 40-70%
            soil_readings = ["WET" if random.random() > 0.4 else "DRY" for _ in range(6)]
            wet_count = soil_readings.count("WET")
            soil_wetness_pct = round(wet_count / len(soil_readings) * 100, 1)
            
            sensor_payload = {
                "cycle_id": cycle_id,
                "temp_c": temp,
                "humidity_pct": hum,
                "light_state": random.choice(light_states),
                "soil_summary": f"{6-wet_count}/6 DRY",
                "soil_majority": "DRY" if wet_count <= 3 else "WET",
                "temp_readings": [round(temp + random.gauss(0, 0.5), 1)],
                "hum_readings": [round(hum + random.gauss(0, 1), 1)],
                "soil_readings": soil_readings,
                "soil_wetness_pct": soil_wetness_pct,
            }
            supabase.table("sensor_readings").insert(sensor_payload).execute()
            
            # AI Analysis
            disease = random.choice(diseases)
            plant = random.choice(plants)
            confidence = round(random.uniform(0.7, 0.99), 2)
            
            ai_payload = {
                "cycle_id": cycle_id,
                "disease": disease,
                "plant": plant,
                "confidence": confidence,
                "recommendation": {
                    "reduce_temperature": temp > 28,
                    "water_plant": wet_count <= 2,
                    "increase_airflow": disease != "No disease found" or temp > 30,
                },
                "prompt_markdown": f"Analyze plant for {plant}",
                "response_markdown": json.dumps({"status": "analyzed", "plant": plant}),
            }
            supabase.table("ai_analyses").insert(ai_payload).execute()
            
            # Actuator Actions
            actions = "None"
            if wet_count <= 2:
                actions = "Watered (5s)"
            elif temp > 28:
                actions = "Fan ON"
            
            actuator_payload = {
                "cycle_id": cycle_id,
                "actions": actions,
            }
            supabase.table("actuator_actions").insert(actuator_payload).execute()
            
            if (i + 1) % 50 == 0:
                print(f"  ✓ Inserted {i + 1}/200 records")
        
        print("✅ Successfully inserted 200 mock records")
        
    except Exception as e:
        print(f"❌ Populate failed: {e}")
        sys.exit(1)


def restore_data():
    """Restore data from backup.json"""
    if not os.path.exists("backup.json"):
        print("❌ Error: backup.json not found")
        sys.exit(1)
    
    print("📥 Restoring data from backup...")
    
    supabase = get_supabase_client()
    
    try:
        # Load backup
        with open("backup.json", "r") as f:
            backup = json.load(f)
        
        # Clear current data
        supabase.table("actuator_actions").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("ai_analyses").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("sensor_readings").delete().gt("created_at", "1900-01-01").execute()
        supabase.table("plant_cycles").delete().gt("created_at", "1900-01-01").execute()
        
        # Restore each table
        if backup.get("plant_cycles"):
            supabase.table("plant_cycles").insert(backup["plant_cycles"]).execute()
            print(f"  ✓ Restored {len(backup['plant_cycles'])} plant_cycles")
        
        if backup.get("sensor_readings"):
            supabase.table("sensor_readings").insert(backup["sensor_readings"]).execute()
            print(f"  ✓ Restored {len(backup['sensor_readings'])} sensor_readings")
        
        if backup.get("ai_analyses"):
            supabase.table("ai_analyses").insert(backup["ai_analyses"]).execute()
            print(f"  ✓ Restored {len(backup['ai_analyses'])} ai_analyses")
        
        if backup.get("actuator_actions"):
            supabase.table("actuator_actions").insert(backup["actuator_actions"]).execute()
            print(f"  ✓ Restored {len(backup['actuator_actions'])} actuator_actions")
        
        total = sum(len(v) for v in backup.values())
        print(f"✅ Restored {total} records from backup.json")
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_data()
    elif command == "populate":
        print("⚠️  This will DELETE all current data and insert 200 mock records")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled")
            sys.exit(0)
        
        backup_data()  # Auto-backup before populating
        clear_data()
        populate_mock_data()
        print("\n✅ Ready to preview! Run: python db_mock.py restore")
    elif command == "restore":
        print("⚠️  This will DELETE all current data and restore from backup.json")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled")
            sys.exit(0)
        restore_data()
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
