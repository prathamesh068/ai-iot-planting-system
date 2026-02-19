# 🌱 AI + IoT Smart Plant System

An AI-powered IoT system that monitors plant health using sensors, captures images via camera, analyzes data with Google Gemini AI, and logs results to Google Sheets & Drive.

---

## 📋 Requirements

- Python 3.10+
- Raspberry Pi (for full hardware deployment) or any Linux/Windows machine (for development)
- Google Cloud credentials (`credentials.json`)
- Gemini API key

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai-iot-planting-system
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux / macOS / Raspberry Pi:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

**On Windows / Linux (development):**

```bash
pip install -r requirements.txt
```

**On Raspberry Pi (full hardware deployment):**

```bash
pip install -r requirements.pi.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
DRIVE_FOLDER_ID=your_google_drive_folder_id
SPREADSHEET_ID=your_google_spreadsheet_id
```

---

## 🚀 Running the System

```bash
python3 code.py
```

### Optional arguments:

| Argument      | Default          | Description                          |
| ------------- | ---------------- | ------------------------------------ |
| `--dht-pin`   | `4`              | BCM pin for DHT11 sensor             |
| `--ldr-pin`   | `17`             | BCM pin for LDR light sensor         |
| `--soil-pins` | `27 28 29 30 31` | BCM pins for 5 soil moisture sensors |
| `--fan-pin`   | `22`             | BCM pin for fan relay                |
| `--pump-pin`  | `23`             | BCM pin for water pump relay         |

**Example:**

```bash
python3 code.py --dht-pin 4 --ldr-pin 17 --soil-pins 27 28 29 30 31 --fan-pin 22 --pump-pin 23
```

---

## 🗂️ Project Structure

```
ai-iot-planting-system/
├── code.py               # Main application
├── requirements.txt      # Dependencies for Windows / Linux
├── requirements.pi.txt   # Dependencies for Raspberry Pi
├── .env                  # Environment variables (not committed)
├── credentials.json      # Google OAuth credentials (not committed)
├── token.json            # Auto-generated OAuth token (not committed)
└── README.md
```

---

## 📦 Dependencies

| Package                      | Purpose                                 |
| ---------------------------- | --------------------------------------- |
| `Adafruit-Blinka`            | GPIO board abstraction (`board` module) |
| `adafruit-circuitpython-dht` | DHT11 temperature/humidity sensor       |
| `RPi.GPIO` _(Pi only)_       | Raspberry Pi GPIO control               |
| `rpi-lgpio` _(Pi only)_      | Modern lgpio backend for RPi            |
| `google-generativeai`        | Gemini AI image & data analysis         |
| `google-api-python-client`   | Google Drive & Sheets API               |
| `google-auth`                | Google OAuth2 authentication            |
| `google-auth-oauthlib`       | OAuth2 flow for installed apps          |
| `opencv-python`              | Webcam image capture                    |
| `numpy`                      | Numerical operations                    |
| `python-dotenv`              | Load environment variables from `.env`  |
