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

**On Windows / Linux (development):**

```bash
python3 -m venv .venv
```

**On Raspberry Pi:**

```bash
python3 -m venv venv --system-site-packages
```

> **Note:** The `--system-site-packages` flag is required on Raspberry Pi because `opencv-python` (and `numpy`) are installed at the **system level** via `apt` (`libopencv-dev`, `python3-opencv`) and are not available inside a standard isolated venv. This flag allows the venv to access those system-installed packages.

### 3. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

**Raspberry Pi:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

**On Windows / Linux (development):**

```bash
pip install -r requirements.txt
```

**On Raspberry Pi (full hardware deployment):**

First, install the required system-level packages via `apt`:

```bash
sudo apt update && sudo apt install -y \
  python3-dev \
  python3-pip \
  python3-venv \
  libgpiod-dev \
  swig \
  libatlas-base-dev \
  libopencv-dev
```

> **Note:** `python3-dev` and `swig` are required to build `RPi.GPIO` and `lgpio` from source.  
> `libatlas-base-dev` is needed for `numpy` on ARM.  
> `libopencv-dev` is needed for `opencv-python` on ARM.

Then install Python packages:

```bash
pip install -r requirements.pi.txt
```

Alternatively, you can install the GPIO packages directly via `apt` (no build step needed):

```bash
sudo apt install -y python3-rpi.gpio python3-lgpio
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
DRIVE_FOLDER_ID=your_google_drive_folder_id
SPREADSHEET_ID=your_google_spreadsheet_id
MOCK=false
```

Set `MOCK=true` for local development without hardware, camera, or cloud APIs.

---

## 🚀 Running the System

```bash
python3 run.py
```

### Local run without components (mock mode)

```bash
python3 run.py --mock
```

You can also enable mock mode from environment:

```bash
export MOCK=true
python3 run.py
```

### Optional arguments:

| Argument          | Default               | Description                               |
| ----------------- | --------------------- | ----------------------------------------- |
| `--dht-pin`       | `4`                   | BCM pin for DHT11 sensor                  |
| `--ldr-pin`       | `20`                  | BCM pin for LDR light sensor              |
| `--soil-pins`     | `5 6 13 19 26 21`     | BCM pins for soil moisture sensors        |
| `--fan-pin`       | `27`                  | BCM pin for fan relay                     |
| `--pump-pin`      | `17`                  | BCM pin for water pump relay              |
| `--pump-duration` | `5`                   | Seconds to keep pump ON during watering   |
| `--mock`          | `false`               | Use mock services (no hardware/cloud)     |

**Example:**

```bash
python3 run.py --dht-pin 4 --ldr-pin 17 --soil-pins 27 28 29 30 31 --fan-pin 22 --pump-pin 23
```

---

## 🗂️ Project Structure

```
ai-iot-planting-system/
├── run.py                # Thin launcher for backend
├── backend/
│   ├── main.py           # Backend entrypoint
│   ├── system.py         # Orchestrates one full cycle
│   ├── cli.py            # Argument parser
│   ├── config.py         # Env + app settings
│   ├── contracts.py      # Base interfaces
│   ├── factories.py      # MOCK/REAL service assembly
│   └── services/
│       ├── gpio_service.py
│       ├── sensor_service.py
│       ├── camera_service.py
│       ├── google_service.py
│       ├── ai_service.py
│       └── actuator_service.py
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
