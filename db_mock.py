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
            
            todos = []
            if wet_count <= 2:
                todos.append(
                    {
                        "action": "Irrigate the plant",
                        "priority": "HIGH",
                        "reason": "Majority soil reading is DRY.",
                    }
                )
            if temp > 30:
                todos.append(
                    {
                        "action": "Reduce ambient temperature",
                        "priority": "HIGH",
                        "reason": "Temperature is above 30C.",
                    }
                )
                todos.append(
                    {
                        "action": "Increase airflow around the plant",
                        "priority": "MEDIUM",
                        "reason": "High temperature can stress plants.",
                    }
                )
            if disease != "No disease found":
                todos.append(
                    {
                        "action": "Inspect infected leaves and isolate affected area",
                        "priority": "HIGH",
                        "reason": "Visible disease symptoms require immediate containment.",
                    }
                )
            if not todos:
                todos.append(
                    {
                        "action": "Continue routine monitoring",
                        "priority": "LOW",
                        "reason": "No immediate intervention is required.",
                    }
                )

            disease_confidence = round(random.uniform(0.7, 0.99), 2)
            disease_reason = (
                "No visible lesions, spotting, or discoloration detected."
                if disease == "No disease found"
                else f"Visible symptoms consistent with {disease} observed on leaves."
            )

            light_state_for_record = sensor_payload["light_state"]
            soil_summary_for_record = sensor_payload["soil_summary"]

            prompt_markdown = (
                "You are an agricultural AI in an IoT system.\n\n"
                "Sensor Data:\n"
                f"- Temperature: {temp} C\n"
                f"- Humidity: {hum} %\n"
                f"- Light: {light_state_for_record}\n"
                f"- Soil Moisture: {soil_summary_for_record}\n\n"
                "Image Analysis Rules:\n"
                "- First detect plant. If unsure, return \"No plant detected\"\n"
                "- Only detect diseases relevant to the identified plant\n"
                "- If no disease is visible, return \"No disease found\"\n"
                "- Always provide a confidence score (0-100) for plant and disease separately\n\n"
                "Soil Rules:\n"
                "- Soil moisture is reported as \"X/Total DRY\" or \"X/Total WET\"\n"
                "- Recommend watering ONLY if the majority soil reading is DRY\n\n"
                "Environment Rules:\n"
                "- Recommend airflow if disease detected OR temperature > 30\n"
                "- Recommend temperature reduction ONLY if temperature > 30\n\n"
                "Response Rules:\n"
                "- All actions must be structured as TODO items with priority\n"
                "- Priority levels: HIGH, MEDIUM, LOW\n"
                "- HIGH -> immediate risk (disease, extreme heat, fully dry soil)\n"
                "- MEDIUM -> preventive care\n"
                "- LOW -> general optimization\n\n"
                "Output Format (STRICT JSON ONLY):\n\n"
                "{\n"
                "    \"plant\": {\"name\": \"<plant_name | No plant detected>\", \"confidence\": <0-100>},\n"
                "    \"disease\": {\"name\": \"<disease_name | No disease found>\", \"confidence\": <0-100>, \"reason\": \"<short visual justification>\"},\n"
                "    \"environment\": {\"temperature\": <temp>, \"humidity\": <humidity>, \"light\": \"<light>\", \"soil\": \"<soil>\"},\n"
                "    \"todos\": [{\"action\": \"<what to do>\", \"priority\": \"HIGH | MEDIUM | LOW\", \"reason\": \"<why>\"}]\n"
                "}\n\n"
                "Behavior Constraints:\n"
                "- Do NOT hallucinate diseases unrelated to the plant\n"
                "- If plant is unknown -> disease must be \"Unknown\"\n"
                "- If no disease -> no HIGH priority disease actions\n"
                "- Keep reasons short and technical (no storytelling)\n"
                "- Do NOT return anything except JSON"
            )

            ai_response_obj = {
                "plant": {
                    "name": plant,
                    "confidence": round(confidence * 100, 1),
                },
                "disease": {
                    "name": disease,
                    "confidence": round(disease_confidence * 100, 1),
                    "reason": disease_reason,
                },
                "environment": {
                    "temperature": temp,
                    "humidity": hum,
                    "light": light_state_for_record,
                    "soil": soil_summary_for_record,
                },
                "todos": todos,
            }
            response_markdown = f"```json\n{json.dumps(ai_response_obj, indent=2)}\n```"

            ai_payload = {
                "cycle_id": cycle_id,
                "disease": disease,
                "plant": plant,
                "confidence": confidence,
                "todos": todos,
                "recommendation": {
                    "reduce_temperature": temp > 28,
                    "water_plant": wet_count <= 2,
                    "increase_airflow": disease != "No disease found" or temp > 30,
                },
                "prompt_markdown": prompt_markdown,
                "response_markdown": response_markdown,
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
