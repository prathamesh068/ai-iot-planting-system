# AI + IoT Planting System — Software Documentation

## 1. Overview

The AI + IoT Planting System is a smart agriculture software platform that combines Internet of Things devices, cloud storage, artificial intelligence, and a web dashboard to monitor plant health and automate basic care tasks.

The project is designed to run mainly on a Raspberry Pi or similar device connected to environmental sensors and actuators. It collects live data such as temperature, humidity, soil moisture, and light level, captures an image of the plant, sends that information to Google Gemini for analysis, stores the results in Supabase, and displays them through a frontend dashboard.

---

## 2. Main Objectives

This software aims to:

- monitor environmental and soil conditions in real time
- detect possible plant health issues through AI analysis
- automate actions such as watering and airflow control
- store historical readings for future review
- provide a live dashboard for users to observe and control the system remotely

---

## 3. High-Level Architecture

The system is divided into three major parts:

### A. Backend
The backend handles all device-side operations:

- reads sensors
- captures images from the camera
- runs AI analysis
- controls actuators such as fan and pump
- writes data to Supabase
- listens for remote commands from the dashboard

### B. Frontend
The frontend is a web dashboard that:

- shows live and historical sensor data
- visualizes trends using charts
- displays AI analysis results
- shows device heartbeat and status
- sends commands to trigger a new reading cycle

### C. Cloud and Database Layer
Supabase is used as the central cloud platform for:

- relational database storage
- image storage bucket
- realtime communication between device and dashboard

---

## 4. Repository Structure

### Root files

- run.py — minimal entry point that starts the backend
- README.md — installation and usage guide
- TODO.md — frontend and UI upgrade notes
- requirements.txt — Python dependencies for desktop or general environments
- requirements.pi.txt — Python dependencies for Raspberry Pi deployment
- db_mock.py — utility to back up, populate, and restore mock database data
- backup.json — backup storage used by the mock-data tool
- DB_MOCK_README.md — usage notes for database mock operations

### Backend folder

The backend folder contains the core business logic of the project.

#### Important files

- backend/main.py — main startup logic for the backend
- backend/system.py — orchestrates a complete plant-monitoring cycle
- backend/cli.py — parses command-line arguments such as mock mode and pin settings
- backend/config.py — loads environment variables and application settings
- backend/contracts.py — abstract interfaces for GPIO, sensors, camera, storage, and AI
- backend/factories.py — builds the correct real or mock service implementations
- backend/logger.py — custom logging utility for structured terminal output
- backend/command_listener.py — realtime Supabase listener for dashboard-triggered commands

### Backend services folder

This folder contains modular service implementations.

- actuator_service.py — controls fan and pump behavior
- ai_service.py — sends image and sensor data to Gemini and normalizes the response
- camera_service.py — captures images from a webcam or provides mock image behavior
- gpio_service.py — manages GPIO pins and relay interactions
- sensor_service.py — reads DHT, light, and soil sensors
- supabase_service.py — uploads images and stores cycle data in Supabase

### Supabase folder

- backend/supabase/schema.sql — SQL schema for tables, indexes, policies, and public storage bucket

### Frontend folder

The frontend is a React and TypeScript dashboard built with Vite.

#### Important frontend files

- frontend/src/App.tsx — main UI layout and dashboard composition
- frontend/src/hooks/useSupabaseData.ts — fetches dashboard data and sends control broadcasts
- frontend/src/hooks/useDeviceHeartbeat.ts — tracks whether the backend device is live
- frontend/src/lib/supabase.ts — initializes the Supabase client
- frontend/src/types/index.ts — TypeScript interfaces for frontend data models

#### Components

- AboutPage.tsx — project summary and team/about information
- AIAnalysisCard.tsx — renders prompt, response, and TODO items from AI analysis
- ChartCard.tsx — reusable chart component for multiple visualizations
- DataTable.tsx — displays readings, actions, disease data, and image preview

### Scripts folder

- install_pi_autostart.sh — creates a systemd service so the backend starts automatically on Raspberry Pi boot

---

## 5. Backend Execution Flow

The backend runs one full monitoring cycle through the SmartPlantSystem class.

### Step-by-step cycle

1. Start the program through run.py
2. Parse hardware and runtime arguments in the CLI
3. Load application settings from environment variables
4. Build services using either real hardware or mock implementations
5. Turn off actuators initially for safety
6. Capture a plant image using the camera
7. Read temperature and humidity from DHT sensors
8. Read light level from the LDR sensor
9. Read soil moisture values from multiple soil sensors
10. Upload the captured image to Supabase Storage
11. Send the image and sensor readings to Gemini AI
12. Receive plant identification, disease analysis, and recommended actions
13. Apply actuator behavior such as fan or pump activation
14. Save the full cycle to the database

This approach keeps one plant reading cycle complete, traceable, and easy to visualize later.

---

## 6. Sensor and Hardware Logic

The system supports both real and mock operation.

### Real mode
In real mode, the software attempts to use:

- Raspberry Pi GPIO access
- DHT11 temperature and humidity sensors
- soil moisture sensors
- LDR light sensor
- webcam through OpenCV

### Mock mode
In mock mode, the system:

- generates fake sensor readings
- creates placeholder image files
- avoids real hardware dependencies
- allows safe development and testing on non-Raspberry Pi machines

This design makes the project portable for both development and deployment.

---

## 7. AI Analysis Logic

The AI layer is implemented in the backend AI service.

Its responsibilities include:

- building a structured prompt using sensor data
- attaching the plant image
- sending the request to Google Gemini
- forcing JSON output through a defined schema
- normalizing the response for stable downstream usage

### AI output contains

- plant name and confidence
- disease name and confidence
- explanation or reason
- environment summary
- TODO actions with priority levels
- recommendation flags for airflow, watering, and temperature control

If the AI response fails or credentials are missing, the system falls back to a default or mock result.

---

## 8. Actuator Control

The software currently supports two automated outputs:

- fan relay
- water pump relay

The actuator controller decides actions based on AI recommendations and environmental conditions.

### Example rules

- if the AI recommends airflow or temperature is too high, the fan is turned on
- if the AI recommends watering and soil is mostly dry, the pump is activated for a fixed duration

This makes the system capable of simple autonomous plant care.

---

## 9. Database Design

The project uses Supabase PostgreSQL with a relational design.

### Main tables

#### plant_cycles
Stores the master record for each monitoring event.

Fields include:
- cycle ID
- capture timestamp
- image URL

#### sensor_readings
Stores sensor measurements linked to a cycle.

Fields include:
- temperature
- humidity
- light state
- soil summary
- per-sensor arrays
- soil wetness percentage

#### ai_analyses
Stores AI-generated output linked to a cycle.

Fields include:
- plant name
- disease name
- confidence
- TODO list
- recommendations
- prompt markdown
- response markdown

#### actuator_actions
Stores what the system physically did for that cycle.

Fields include:
- action description

This separation makes the data clean, scalable, and easy to query.

---

## 10. Realtime Communication

The system includes a realtime command channel through Supabase.

### How it works

- the frontend broadcasts a control event such as start_reading
- the backend command listener subscribes to that channel
- when the event is received, a new monitoring cycle starts
- the backend also emits heartbeat messages to tell the dashboard that the device is alive and whether it is currently running

This creates a lightweight remote-control mechanism without needing a separate custom API server.

---

## 11. Frontend Dashboard Behavior

The frontend is responsible for presenting information to the user in a simple and visual way.

### Dashboard features

- dark and light mode UI
- temperature and humidity charts
- soil wetness history
- light and soil distribution charts
- action count and disease count charts
- data table for recent cycles
- latest AI prompt and response viewer
- device live status indicator
- start button to trigger a reading cycle

The dashboard reads directly from Supabase using the public frontend client.

---

## 12. Mock Data Utility

The repository includes a database mock tool to make demo and testing easier.

### Supported commands

- backup — save current Supabase records to a JSON file
- populate — clear current data and insert 200 realistic mock entries
- restore — restore the backed-up original data

This helps developers preview charts and dashboard behavior without relying on real hardware runs.

---

## 13. Deployment Support

The project includes a shell script for Raspberry Pi deployment.

The script:

- creates a systemd service
- points to the project virtual environment
- starts the backend in command-listener mode
- enables auto-start on device boot

This allows the system to run continuously as a plant-monitoring service.

---

## 14. Key Technologies Used

### Backend

- Python 3
- OpenCV
- Adafruit Blinka and DHT libraries
- Supabase Python client
- Google Gemini API
- python-dotenv

### Frontend

- React 18
- TypeScript
- Vite
- Ant Design
- Recharts
- Supabase JavaScript client
- Tailwind CSS

### Infrastructure

- Supabase PostgreSQL
- Supabase Realtime
- Supabase Storage
- Raspberry Pi and GPIO-compatible hardware

---

## 15. Software Summary

In summary, this repository implements a smart plant monitoring and automation platform. It combines IoT sensing, AI-based plant health analysis, cloud data storage, and a responsive dashboard into one integrated system.

It is suitable for academic projects, smart agriculture demonstrations, and prototype automation systems where plant conditions must be observed and acted on automatically.
