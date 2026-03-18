# AI + IoT Smart Plant System

An AI-powered IoT system that monitors plant health using sensors, captures images, analyzes plant condition with Gemini, writes each run to multiple Supabase tables, and powers a serverless frontend dashboard from Supabase.

## Architecture

- Backend
  - Captures image and sensor data
  - Runs AI analysis using Gemini
  - Uploads captured image to Supabase Storage
  - Can listen for Supabase realtime broadcast commands (`start_reading`) to start frequent runs
  - Writes one cycle across relational tables:
    - plant_cycles
    - sensor_readings
    - ai_analyses
    - actuator_actions
- Frontend
  - Uses Supabase JS client with anon key
  - Reads latest cycles directly from Supabase (no custom API server)
  - Broadcasts control commands over Supabase realtime from the dashboard button
  - Renders charts, table, and latest AI prompt/response

## Requirements

- Python 3.10+
- Node.js 18+ (for frontend)
- Raspberry Pi for full hardware deployment (optional for local mock/dev)
- Supabase project
- Gemini API key

## Backend Setup

### 1. Clone and create environment

```bash
git clone <your-repo-url>
cd ai-iot-planting-system
python3 -m venv .venv
```

Activate:

- Windows

```bash
.venv\Scripts\activate
```

- Linux/macOS

```bash
source .venv/bin/activate
```

### 2. Install Python dependencies

- Windows/Linux

```bash
pip install -r requirements.txt
```

- Raspberry Pi

```bash
pip install -r requirements.pi.txt
```

### 3. Configure environment

Copy .env.example to .env and set values:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=plant-images
SUPABASE_COMMAND_CHANNEL=plant-control
MOCK=false
```

Notes:

- SUPABASE_SERVICE_ROLE_KEY is required for backend writes.
- Keep service role key only on backend/device, never in frontend.
- Set MOCK=true for local runs without hardware/cloud dependencies.

### 4. Create Supabase schema

Run SQL from:

- backend/supabase/schema.sql

This creates all required tables, indexes, read policies, and the storage bucket policy.

### 5. Run backend

```bash
python3 run.py
```

Command listener mode (waits for UI broadcast and starts frequent cycles):

```bash
python3 run.py --listen-commands
```

Mock mode:

```bash
python3 run.py --mock
```

## Frontend Setup

### 1. Install frontend dependencies

```bash
cd frontend
pnpm install
```

### 2. Configure frontend environment

Copy frontend/.env.example to frontend/.env and set values:

```env
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_SUPABASE_CONTROL_CHANNEL=plant-control
```

Use the dashboard `Start Reading` button to broadcast `start_reading`; backend listener mode will then start periodic runs.

### 3. Run frontend

```bash
pnpm dev
```

Build:

```bash
pnpm build
```

## Optional CLI Arguments

| Argument                   | Default         | Description                                                                |
| -------------------------- | --------------- | -------------------------------------------------------------------------- |
| --dht-pins                 | 4               | BCM pin(s) for DHT11 sensor(s)                                             |
| --ldr-pin                  | 20              | BCM pin for LDR light sensor                                               |
| --soil-pins                | 5 6 13 19 26 21 | BCM pins for soil moisture sensors                                         |
| --fan-pin                  | 27              | BCM pin for fan relay                                                      |
| --pump-pin                 | 17              | BCM pin for water pump relay                                               |
| --pump-duration            | 5               | Seconds to keep pump ON during watering                                    |
| --mock                     | false           | Use mock services                                                          |
| --listen-commands          | false           | Listen on Supabase realtime control channel for `start_reading` commands  |
| --command-channel          | env/default     | Override realtime channel (falls back to `SUPABASE_COMMAND_CHANNEL`)       |
| --command-default-interval | 60              | Fallback frequent-reading interval in seconds when command has no interval |

## Project Structure

```text
ai-iot-planting-system/
├── run.py
├── backend/
│   ├── main.py
│   ├── system.py
│   ├── cli.py
│   ├── config.py
│   ├── contracts.py
│   ├── factories.py
│   ├── supabase/
│   │   └── schema.sql
│   └── services/
│       ├── gpio_service.py
│       ├── sensor_service.py
│       ├── camera_service.py
│       ├── supabase_service.py
│       ├── ai_service.py
│       └── actuator_service.py
├── frontend/
│   ├── .env.example
│   ├── package.json
│   └── src/
│       ├── lib/supabase.ts
│       └── hooks/useSupabaseData.ts
├── requirements.txt
├── requirements.pi.txt
└── README.md
```

## Core Dependencies

- google-genai: AI analysis
- supabase (Python): backend database/storage writes
- @supabase/supabase-js: frontend serverless reads
- opencv-python: camera capture
- python-dotenv: environment variable loading
