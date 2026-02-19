import os
import time
import json
import datetime
import subprocess
import atexit
import argparse
import board
import adafruit_dht
import RPi.GPIO as GPIO
import google.generativeai as genai

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import cv2

# ===================== LOAD ENV =====================
load_dotenv()

# ===================== CONFIG =====================
IMAGE_PATH = "plant.jpg"

# Google — loaded from .env
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

genai.configure(api_key=GEMINI_API_KEY)


# ===================== GPIO MANAGER =====================
class GPIOManager:
    def __init__(self, ldr_pin: int, soil_pins: list, fan_pin: int, pump_pin: int):
        self.ldr_pin = ldr_pin
        self.soil_pins = soil_pins
        self.fan_pin = fan_pin
        self.pump_pin = pump_pin

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.ldr_pin, GPIO.IN)
        for pin in self.soil_pins:
            GPIO.setup(pin, GPIO.IN)

        GPIO.setup(self.fan_pin,  GPIO.OUT)
        GPIO.setup(self.pump_pin, GPIO.OUT)

        GPIO.output(self.fan_pin,  GPIO.HIGH)
        GPIO.output(self.pump_pin, GPIO.HIGH)

        atexit.register(self.cleanup)

    def fan_on(self):
        GPIO.output(self.fan_pin, GPIO.LOW)

    def fan_off(self):
        GPIO.output(self.fan_pin, GPIO.HIGH)

    def pump_on(self):
        GPIO.output(self.pump_pin, GPIO.LOW)

    def pump_off(self):
        GPIO.output(self.pump_pin, GPIO.HIGH)

    def cleanup(self):
        GPIO.output(self.fan_pin,  GPIO.HIGH)
        GPIO.output(self.pump_pin, GPIO.HIGH)
        GPIO.cleanup()


# ===================== SENSOR MANAGER =====================
class SensorManager:
    def __init__(self, dht_pin, ldr_pin: int, soil_pins: list):
        self.dht = adafruit_dht.DHT11(dht_pin)
        self.ldr_pin = ldr_pin
        self.soil_pins = soil_pins

    def read_dht(self):
        try:
            return self.dht.temperature, self.dht.humidity
        except RuntimeError:
            return None, None

    def read_light(self):
        return "DARK" if GPIO.input(self.ldr_pin) == 1 else "BRIGHT"

    def read_soil(self):
        """
        Read all soil moisture sensors (any number).

        Returns:
            summary  (str) – e.g. "3/5 DRY"  (used for logging & AI prompt)
            majority (str) – "DRY" or "WET"   (used for actuator decisions)
        """
        readings = [
            "DRY" if GPIO.input(pin) == 1 else "WET"
            for pin in self.soil_pins
        ]

        total = len(readings)
        dry_count = readings.count("DRY")
        wet_count = readings.count("WET")

        majority = "DRY" if dry_count >= wet_count else "WET"
        majority_count = dry_count if majority == "DRY" else wet_count

        summary = f"{majority_count}/{total} {majority}"
        return summary, majority


# ===================== CAMERA =====================
class Camera:
    @staticmethod
    def capture():
        subprocess.run(
            ["rpicam-still", "-o", IMAGE_PATH, "--nopreview", "-t", "1000"],
            check=True
        )


class WebCamera:
    MAX_DEVICE_INDEX = 5
    MAX_WAIT_SECONDS = 10
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480

    @staticmethod
    def _is_black_frame(frame, mean_thresh=10, std_thresh=5):
        if frame is None:
            return True
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray.mean() < mean_thresh or gray.std() < std_thresh

    @staticmethod
    def find_camera_index():
        """
        Auto-detect the first available camera device index.

        Strategy:
          1. On Linux (Raspberry Pi): scan /dev/video* to collect candidate indices.
          2. Fallback: try indices 0 .. MAX_DEVICE_INDEX sequentially.

        Returns the integer index of the first working camera, or None if not found.
        """
        import glob

        candidates = []

        # --- Strategy 1: enumerate /dev/video* on Linux ---
        video_devices = sorted(glob.glob("/dev/video*"))
        for dev in video_devices:
            try:
                idx = int(dev.replace("/dev/video", ""))
                candidates.append(idx)
            except ValueError:
                pass

        # --- Strategy 2: fallback range if nothing found via /dev ---
        if not candidates:
            candidates = list(range(WebCamera.MAX_DEVICE_INDEX + 1))

        print(f"[WebCamera] Scanning device indices: {candidates}")

        for idx in candidates:
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap.release()
                continue

            # Try reading a test frame to confirm the device is usable
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                print(
                    f"[WebCamera] Found working camera at index {idx} (/dev/video{idx})")
                return idx

            print(
                f"[WebCamera] Index {idx} opened but could not read a frame — skipping.")

        print("[WebCamera] No working camera found.")
        return None

    @staticmethod
    def capture():
        device_index = WebCamera.find_camera_index()

        if device_index is None:
            print("[WebCamera] ERROR: No camera device detected. Capture aborted.")
            return False

        cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)

        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WebCamera.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WebCamera.FRAME_HEIGHT)

        if not cap.isOpened():
            cap.release()
            print(
                f"[WebCamera] ERROR: Could not reopen camera at index {device_index}.")
            return False

        time.sleep(2)

        start_time = time.time()
        success = False

        while time.time() - start_time < WebCamera.MAX_WAIT_SECONDS:
            ret, frame = cap.read()

            if not ret or frame is None:
                continue
            if WebCamera._is_black_frame(frame):
                continue

            cv2.imwrite(IMAGE_PATH, frame)
            success = True
            break

        cap.release()
        return success


# ===================== GOOGLE SERVICES =====================
class GoogleServices:
    def __init__(self):
        self.creds = self.authenticate()
        self.drive = build("drive",  "v3", credentials=self.creds)
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
- Soil Moisture: {soil}

Rules:
- Soil moisture is reported as "X/Total DRY" or "X/Total WET"
  (e.g. "3/5 DRY" means 3 out of 5 sensors read DRY — majority is DRY)
- Light is digital (DARK/BRIGHT)
- Recommend watering ONLY if the majority soil reading is DRY
- Recommend airflow if disease detected OR temperature > 30
- Reduce temperature ONLY if temperature > 30
- When no disease is found, set 'disease' to 'No disease found' and all flags to false
- When no plant is detected, set 'plant' to 'No plant detected'

Return ONLY valid JSON:

{{
  "disease": "string",
  "plant": "string",
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

    def analyze(self, temp, humidity, light, soil_summary):
        with open(IMAGE_PATH, "rb") as f:
            image = f.read()

        content = [
            self.PROMPT.format(
                temp=temp,
                humidity=humidity,
                light=light,
                soil=soil_summary
            ),
            {"mime_type": "image/jpeg", "data": image}
        ]

        try:
            response = self.model.generate_content(
                content,
                request_options={"timeout": 30}
            )
            print(response.text)
            text = response.text.replace(
                "```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(e)
            return {
                "disease": "unknown",
                "plant": "Unknown",
                "confidence": 0.0,
                "recommendation": {
                    "reduce_temperature": False,
                    "water_plant": False,
                    "increase_airflow": False
                }
            }


# ===================== ACTUATORS =====================
class ActuatorController:
    def __init__(self, gpio: GPIOManager, pump_duration: int = 5):
        self.gpio = gpio
        self.pump_duration = pump_duration

    def apply(self, ai_result, temp, soil_majority):
        actions = []
        rec = ai_result["recommendation"]

        if rec["increase_airflow"] or temp > 30:
            self.gpio.fan_on()
            actions.append("Fan ON")
        else:
            self.gpio.fan_off()

        if rec["water_plant"] and soil_majority == "DRY":
            self.gpio.pump_on()
            time.sleep(self.pump_duration)
            self.gpio.pump_off()
            actions.append(f"Watered ({self.pump_duration}s)")

        return ", ".join(actions) or "None"


# ===================== SYSTEM =====================
class SmartPlantSystem:
    def __init__(self, args):
        # Convert integer BCM pin → board.D{n} for the DHT library
        dht_board_pin = getattr(board, f"D{args.dht_pin}")

        self.gpio = GPIOManager(
            ldr_pin=args.ldr_pin,
            soil_pins=args.soil_pins,
            fan_pin=args.fan_pin,
            pump_pin=args.pump_pin,
        )
        self.sensors = SensorManager(
            dht_pin=dht_board_pin,
            ldr_pin=args.ldr_pin,
            soil_pins=args.soil_pins,
        )
        self.camera = Camera()
        self.webcamera = WebCamera()
        self.google = GoogleServices()
        self.ai = PlantAI()
        self.actuators = ActuatorController(
            self.gpio, pump_duration=args.pump_duration)

    def run(self):
        # Capture image
        if not self.webcamera.capture():
            print("WebCam Initialisation failed")
            return

        # Read sensors
        temp, hum = self.sensors.read_dht()
        if temp is None:
            print("DHT11 read failed")
            return

        light = self.sensors.read_light()
        soil_summary, soil_majority = self.sensors.read_soil()

        # Upload & analyse
        image_url = self.google.upload_image(IMAGE_PATH)
        ai_result = self.ai.analyze(temp, hum, light, soil_summary)
        actions = self.actuators.apply(ai_result, temp, soil_majority)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            timestamp,
            temp,
            hum,
            light,
            soil_summary,          # e.g. "3/5 DRY"
            image_url,
            ai_result["disease"],
            ai_result["confidence"],
            actions,
            ai_result["plant"]
        ]

        self.google.log_to_sheet(row)

        print("Logged successfully")
        print(row)


# ===================== ENTRY =====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI + IoT Smart Plant System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--dht-pin", type=int, default=7,
        help="BCM pin number for DHT11 temperature/humidity sensor"
    )
    parser.add_argument(
        "--ldr-pin", type=int, default=38,
        help="BCM pin number for LDR light sensor"
    )
    parser.add_argument(
        "--soil-pins", type=int, nargs="+",
        default=[29, 31, 33, 35, 37, 40],
        metavar="PIN",
        help="BCM pin numbers for soil moisture sensors (any number, e.g. --soil-pins 27 28 29)"
    )
    parser.add_argument(
        "--fan-pin", type=int, default=13,
        help="BCM pin number for fan relay"
    )
    parser.add_argument(
        "--pump-pin", type=int, default=11,
        help="BCM pin number for water pump relay"
    )
    parser.add_argument(
        "--pump-duration", type=int, default=5,
        help="Number of seconds the water pump stays ON when watering"
    )

    args = parser.parse_args()

    print(f"[CONFIG] DHT={args.dht_pin} | LDR={args.ldr_pin} | "
          f"Soil={args.soil_pins} | Fan={args.fan_pin} | "
          f"Pump={args.pump_pin} | PumpDuration={args.pump_duration}s")

    SmartPlantSystem(args).run()
