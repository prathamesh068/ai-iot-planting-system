import os
import time
import json
import datetime
import subprocess
import atexit

import board
import adafruit_dht
import RPi.GPIO as GPIO
import google.generativeai as genai

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ===================== CONFIG =====================
IMAGE_PATH = "plant.jpg"

# Sensors
DHT_PIN = board.D4
LDR_PIN = 17
SOIL_PIN = 27

# Actuators
FAN_PIN = 22
PUMP_PIN = 23

# Google
DRIVE_FOLDER_ID = "1zowenxFUZXBXCvH5_A1MzbcNORQupNPA"
SPREADSHEET_ID = "1ns-4EP_eRR5WDlHlKTnPc-MXrRrKl_TP4LNPajDsb-0"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
GEMINI_API_KEY = "AIzaSyAj5aMQ2dXkaHBjDPMLTy87Dp-y1nq_Bxk"
genai.configure(api_key=GEMINI_API_KEY)


# ===================== GPIO MANAGER =====================
class GPIOManager:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(LDR_PIN, GPIO.IN)
        GPIO.setup(SOIL_PIN, GPIO.IN)

        GPIO.setup(FAN_PIN, GPIO.OUT)
        GPIO.setup(PUMP_PIN, GPIO.OUT)

        GPIO.output(FAN_PIN, GPIO.HIGH)
        GPIO.output(PUMP_PIN, GPIO.HIGH)

        atexit.register(self.cleanup)

    def fan_on(self):
        GPIO.output(FAN_PIN, GPIO.LOW)

    def fan_off(self):
        GPIO.output(FAN_PIN, GPIO.HIGH)

    def pump_on(self):
        GPIO.output(PUMP_PIN, GPIO.LOW)

    def pump_off(self):
        GPIO.output(PUMP_PIN, GPIO.HIGH)

    def cleanup(self):
        GPIO.output(FAN_PIN, GPIO.HIGH)
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        GPIO.cleanup()


# ===================== SENSOR MANAGER =====================
class SensorManager:
    def __init__(self):
        self.dht = adafruit_dht.DHT11(DHT_PIN)

    def read_dht(self):
        try:
            return self.dht.temperature, self.dht.humidity
        except RuntimeError:
            return None, None

    def read_light(self):
        return "DARK" if GPIO.input(LDR_PIN) == 1 else "BRIGHT"

    def read_soil(self):
        return "DRY" if GPIO.input(SOIL_PIN) == 1 else "WET"


# ===================== CAMERA =====================
class Camera:
    @staticmethod
    def capture():
        subprocess.run(
            ["rpicam-still", "-o", IMAGE_PATH, "--nopreview", "-t", "1000"],
            check=True
        )


# ===================== GOOGLE SERVICES =====================
class GoogleServices:
    def __init__(self):
        self.creds = self.authenticate()
        self.drive = build("drive", "v3", credentials=self.creds)
        self.sheets = build("sheets", "v4", credentials=self.creds)

    @staticmethod
    def authenticate():
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(
                    port=0, access_type="offline", prompt="consent"
                )

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return creds

    def upload_image(self, path):
        metadata = {
            "name": f"plant_{int(time.time())}.jpg",
            "parents": [DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(path, mimetype="image/jpeg")
        file = self.drive.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()

        return f"https://drive.google.com/file/d/{file['id']}/view"

    def log_to_sheet(self, row):
        body = {"values": [row]}
        self.sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="plant_readings!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()


# ===================== AI ANALYZER =====================
class PlantAI:
    PROMPT = """
You are an agricultural AI in an IoT system.

Sensor Data:
- Temperature: {temp} °C
- Humidity: {humidity} %
- Light: {light}
- Soil: {soil}

Rules:
- Soil is digital (DRY/WET)
- Light is digital (DARK/BRIGHT)
- Recommend watering ONLY if soil is DRY
- Recommend airflow if disease OR temperature > 30
- Reduce temperature ONLY if temperature > 30

Return ONLY valid JSON:

{{
  "disease": "string",
  "confidence": 0.0,
  "recommendation": {{
    "reduce_temperature": false,
    "water_plant": false,
    "increase_airflow": false
  }}
}}
"""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def analyze(self, temp, humidity, light, soil):
        with open(IMAGE_PATH, "rb") as f:
            image = f.read()

        content = [
            self.PROMPT.format(
                temp=temp,
                humidity=humidity,
                light=light,
                soil=soil
            ),
            {"mime_type": "image/jpeg", "data": image}
        ]

        try:
            response = self.model.generate_content(
                content,
                request_options={"timeout": 30}
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception:
            return {
                "disease": "unknown",
                "confidence": 0.0,
                "recommendation": {
                    "reduce_temperature": False,
                    "water_plant": False,
                    "increase_airflow": False
                }
            }


# ===================== ACTUATORS =====================
class ActuatorController:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio

    def apply(self, ai, temp, soil):
        actions = []
        rec = ai["recommendation"]

        if rec["increase_airflow"] or temp > 30:
            self.gpio.fan_on()
            actions.append("Fan ON")
        else:
            self.gpio.fan_off()

        if rec["water_plant"] and soil == "DRY":
            self.gpio.pump_on()
            time.sleep(5)
            self.gpio.pump_off()
            actions.append("Watered")

        return ", ".join(actions) or "None"


# ===================== SYSTEM =====================
class SmartPlantSystem:
    def __init__(self):
        self.gpio = GPIOManager()
        self.sensors = SensorManager()
        self.camera = Camera()
        self.google = GoogleServices()
        self.ai = PlantAI()
        self.actuators = ActuatorController(self.gpio)

    def run(self):
        # self.camera.capture()

        temp, hum = self.sensors.read_dht()
        if temp is None:
            print("DHT11 read failed")
            return

        light = self.sensors.read_light()
        soil = self.sensors.read_soil()

        image_url = self.google.upload_image(IMAGE_PATH)
        ai_result = self.ai.analyze(temp, hum, light, soil)
        actions = self.actuators.apply(ai_result, temp, soil)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            timestamp,
            temp,
            hum,
            light,
            soil,
            image_url,
            ai_result["disease"],
            ai_result["confidence"],
            actions
        ]

        self.google.log_to_sheet(row)

        print("Logged successfully")
        print(row)


# ===================== ENTRY =====================
if __name__ == "__main__":
    SmartPlantSystem().run()
