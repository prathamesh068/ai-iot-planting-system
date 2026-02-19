import os
import time
import json
import datetime
import subprocess

import board
import adafruit_dht
import RPi.GPIO as GPIO
import google.generativeai as genai


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================
# Hardware
DHT_DEVICE = adafruit_dht.DHT11(board.D4) # GPIO4
FAN_PIN = 17
WATER_PIN = 27

# Paths & IDs
IMAGE_PATH = 'image.jpg' #"/home/pi/plant.jpg"
DRIVE_FOLDER_ID = "1zowenxFUZXBXCvH5_A1MzbcNORQupNPA"
SPREADSHEET_ID = "1ns-4EP_eRR5WDlHlKTnPc-MXrRrKl_TP4LNPajDsb-0"
GEMINI_API_KEY = "AIzaSyAj5aMQ2dXkaHBjDPMLTy87Dp-y1nq_Bxk"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# ================= SETUP =================
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.setup(WATER_PIN, GPIO.OUT)

# Relays are often Active-Low (HIGH = OFF)
GPIO.output(FAN_PIN, GPIO.HIGH)
GPIO.output(WATER_PIN, GPIO.HIGH)

genai.configure(api_key=GEMINI_API_KEY)

# print("Available models:")
# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)

# ================= FUNCTIONS =================

prompt = """
I am an automated IoT system. 
Sensor Data: {temp}C, {humidity}% Humidity.

Analyze this plant image. 
You MUST return ONLY a JSON object with this exact structure, no extra text:

{{
  "disease": "Detected disease comma separated",
  "confidence": 0.95,
  "recommendation": {{
    "reduce_temperature": false,
    "water_plant": false,
    "increase_airflow": true
  }}
}}

Recommend whether to reduce temprature or water the soil of plant or increase airflow.
"""

def authenticate_google():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired. Refreshing...")
            creds.refresh(Request()) # THIS LINE makes it permanent/automated
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Use access_type='offline' to get the Refresh Token!
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def capture_image_legacy():
    # Uses the modern libcamera-still command
    subprocess.run(["libcamera-still", "-o", IMAGE_PATH, "--nopreview", "-t", "1000"])

def capture_image():
    # Changed from libcamera-still to rpicam-still
    subprocess.run([
        "rpicam-still", 
        "-o", IMAGE_PATH,
        "--nopreview",
        "-t", "1000"
    ])

def read_sensor():
    try:
        temp = DHT_DEVICE.temperature
        hum = DHT_DEVICE.humidity
        if temp is not None and hum is not None:
            return round(temp, 2), round(hum, 2)
    except RuntimeError as error:
        print(f"Sensor Reading Error: {error.args[0]}")
    return 0, 0

def upload_to_drive(service):
    file_metadata = {
        "name": f"plant_{int(time.time())}.jpg",
        "parents": [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(IMAGE_PATH, mimetype="image/jpeg")
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return f"https://drive.google.com/file/d/{file['id']}/view"


def analyze_with_gemini(image_path, temp, humidity):
    print("AI is analyzing plant health (Direct Byte Method)...")
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        contents = [
            prompt.format(temp=temp,humidity=humidity),
            {"mime_type": "image/jpeg", "data": image_data}
        ]

        # ADD THIS: 'request_options' forces a timeout so it doesn't hang forever
        response = model.generate_content(
            contents,
            request_options={"timeout": 30} 
        )
        
        print("Response received!")

        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)

    except Exception as e:
        print(f"\n[!] AI Error or Timeout: {e}")
        return None

def apply_actions(ai, temp, humidity):
    actions = []
    
    # 1. FAN LOGIC: Trigger if AI says reduce temp OR increase airflow
    # Use .get() to prevent crashing if the key is missing
    rec = ai.get("recommendation", {})
    
    if rec.get("reduce_temperature") or rec.get("increase_airflow") or temp > 30:
        GPIO.output(FAN_PIN, GPIO.LOW)  # Relay ON
        actions.append("Fan ON")
    else:
        GPIO.output(FAN_PIN, GPIO.HIGH) # Relay OFF
        
    # 2. PUMP LOGIC: Trigger if AI says water AND humidity is actually low
    if rec.get("water_plant") or humidity < 50:
        GPIO.output(WATER_PIN, GPIO.LOW)  # Relay ON
        time.sleep(5) 
        GPIO.output(WATER_PIN, GPIO.HIGH) # Relay OFF
        actions.append("Watered")

    return ", ".join(actions) if actions else "None"

def log_to_sheet(service, row):
    body = {"values": [row]}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="plant_readings!A1",
        valueInputOption="RAW",
	insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

# ================= MAIN =================

def main():
    try:
        creds = authenticate_google()
        drive_service = build("drive", "v3", credentials=creds)
        sheets_service = build("sheets", "v4", credentials=creds)

        print("Capturing data...")
        # capture_image()
        temp, hum = read_sensor()
        
        print(f"Temp: {temp}C, Hum: {hum}%")
        
        image_url = upload_to_drive(drive_service)
        ai_result = analyze_with_gemini(IMAGE_PATH, temp, hum)
        action_taken = apply_actions(ai_result, temp, hum)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, temp, hum, image_url, ai_result["disease"], ai_result["confidence"], action_taken]
        
        log_to_sheet(sheets_service, row)
        print("Success: Data logged to Sheets.")

    except Exception as e:
        print(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
