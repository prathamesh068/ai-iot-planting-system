# Database Mock Data Utility

Generate mock data for previewing the dashboard without production data.

## Quick Start

### 1. Populate with Mock Data
```bash
python db_mock.py populate
```
- Automatically backs up your current data to `backup.json`
- Clears all database records
- Inserts 200 realistic mock records spanning 200 hours of history
- Ready to preview!

### 2. Restore Original Data
```bash
python db_mock.py restore
```
- Clears the mock data
- Restores everything from `backup.json`
- Back to original state

### 3. Manual Backup (Optional)
```bash
python db_mock.py backup
```
- Save current data to `backup.json`
- Useful before major changes

## What Gets Generated

**200 mock records** with:
- ✅ Realistic sensor readings (temps 15-30°C, humidity 40-70%, soil moisture)
- ✅ AI analyses with disease classifications, plants, confidence scores
- ✅ Actuator actions (watering, fan control)
- ✅ Time spread over 200 hours of history
- ✅ Multi-sensor readings arrays
- ✅ Soil wetness percentages

## Notes

- **The `populate` command auto-backs up** before clearing (safe!)
- **backup.json is never deleted** — you can recover anytime
- **No API calls to external services** — uses mock image URLs
- **Works with your .env configuration** — reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY

## Requirements

- Supabase client: `pip install supabase` (already in requirements.txt)
