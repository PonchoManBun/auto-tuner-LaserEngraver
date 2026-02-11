# Microscope Runner

WA5202 USB microscope capture service for laser engraving quality analysis.

## Setup

```powershell
cd F:\dev\auto-tuner-LaserEngraver\microscope-runner
poetry install
```

## Configuration

Edit `.env` to set camera index:
- `CAMERA_INDEX=0` — First camera
- `CAMERA_INDEX=1` — Second camera (likely microscope if webcam is 0)

## Run

```powershell
poetry run python start_runner.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/camera/test` | GET | Test capture |
| `/api/capture` | POST | Capture image |
| `/api/camera/info` | GET | Camera info |

### POST /api/capture

```json
{
  "job_number": "TEST001",
  "parameter_set_id": "param_v1",
  "notes": "optional notes"
}
```

**Response:**
```json
{
  "success": true,
  "job_number": "TEST001",
  "local_path": "F:\\dev\\...\\micro_TEST001_param_v1_20260211.jpg",
  "filename": "micro_TEST001_param_v1_20260211.jpg",
  "capture_timestamp": "2026-02-11T17:00:00.000Z",
  "resolution": [1920, 1080]
}
```

## Port

Runs on port **8005** (capture-runner uses 8004)
