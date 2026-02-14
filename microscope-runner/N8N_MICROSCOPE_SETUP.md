# n8n Microscope Capture Integration

## Overview

Add microscope capture to your engraving workflow for quality analysis and auto-tuning data collection.

## Workflow Flow

```
[LaserGRBL: Execute] → [Marlin: Move to Microscope] → [Microscope: Capture] → [Marlin: Discharge]
```

---

## Step 1: Add "Move to Microscope" Node

After the LaserGRBL execute node, add an HTTP Request:

| Setting | Value |
|---------|-------|
| **Name** | `Marlin: Move to Microscope` |
| **Method** | POST |
| **URL** | `http://host.docker.internal:8003/webhook/job` |

### Body (JSON):
```json
{
  "operation": "microscope",
  "job_number": "{{ $json.job_number }}"
}
```

### Options:
- **Timeout**: `60000` (60 sec)
- **Continue On Fail**: ON

---

## Step 2: Add "Microscope Capture" Node

After the Move to Microscope node:

| Setting | Value |
|---------|-------|
| **Name** | `Microscope: Capture` |
| **Method** | POST |
| **URL** | `http://host.docker.internal:8005/api/capture` |

### Body (JSON):
```json
{
  "job_number": "{{ $json.job_number }}",
  "material_name": "{{ $json.material_name }}",
  "parameters": {
    "feedRate_mm_min": {{ $json.feedRate_mm_min || 0 }},
    "minPower_pct": {{ $json.minPower_pct || 0 }},
    "maxPower_pct": {{ $json.maxPower_pct || 0 }},
    "quality": {{ $json.quality || 0 }},
    "whiteClip": {{ $json.whiteClip || 0 }},
    "contrast": {{ $json.contrast || 0 }},
    "brightness": {{ $json.brightness || 0 }}
  },
  "notes": "Production capture"
}
```

### Options:
- **Timeout**: `60000` (60 sec)
- **Continue On Fail**: ON

---

## Step 3: Connect Nodes

```
[LaserGRBL: Execute Back]
         ↓
[Marlin: Move to Microscope]
         ↓
[Microscope: Capture]
         ↓
[Marlin: Discharge]
```

---

## API Reference

### Marlin Runner (port 8003)

**Move to Microscope Position:**
```
POST http://host.docker.internal:8003/webhook/job
{
  "operation": "microscope",
  "job_number": "JOB123"
}
```

### Microscope Runner (port 8005)

**Capture Image:**
```
POST http://host.docker.internal:8005/api/capture
{
  "job_number": "JOB123",
  "material_name": "Black_Anodized_Aluminum_01",
  "parameters": { ... },
  "tuning_session_id": "optional",
  "iteration": 1,
  "notes": "optional notes"
}
```

**Response:**
```json
{
  "success": true,
  "job_number": "JOB123",
  "capture_id": "abc12345",
  "local_path": "F:\\...\\captures\\micro_JOB123_20260214.jpg",
  "filename": "micro_JOB123_20260214.jpg",
  "capture_timestamp": "2026-02-14T12:00:00.000Z",
  "resolution": [1920, 1080]
}
```

---

## Data Storage

### Local Files
`F:\dev\auto-tuner-LaserEngraver\microscope-runner\captures\`

### Google Sheets
**Sheet:** `Microscope_Captures` in your Purchase_Orders workbook

**Columns logged:**
- capture_id, timestamp, job_number, material_name
- image_local_path
- All laser parameters (feedRate, power, quality, etc.)
- Quality metrics (filled later by analysis)
- tuning_session_id, iteration, notes

---

## Testing

### Test Move to Microscope
```powershell
$body = '{"operation": "microscope", "job_number": "TEST"}'
Invoke-RestMethod -Uri http://localhost:8003/webhook/job -Method POST -Body $body -ContentType "application/json"
```

### Test Microscope Capture
```powershell
$body = '{"job_number": "TEST", "material_name": "Test_Material"}'
Invoke-RestMethod -Uri http://localhost:8005/api/capture -Method POST -Body $body -ContentType "application/json"
```

---

## Troubleshooting

### "Service is busy"
Another capture is in progress. Wait and retry.

### Camera not found
- Check microscope is plugged in
- Verify `CAMERA_INDEX=1` in `.env`
- Close Windows Camera app (exclusive access)

### Connection refused
- Check service is running
- Verify port (8003 for Marlin, 8005 for Microscope)

---

*Last updated: 2026-02-14*
