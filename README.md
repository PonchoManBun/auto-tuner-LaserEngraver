# Auto-Tuner LaserEngraver

Automated parameter tuning for laser engraving using microscope feedback and Bayesian optimization.

## Overview

This system automatically discovers optimal laser engraving parameters for different materials by:
1. Running test engravings with varied parameters
2. Capturing microscope images of results
3. Analyzing quality via metrics and human feedback
4. Using Bayesian optimization to converge on optimal settings

## Parameters Tuned

| Parameter | Description |
|-----------|-------------|
| `feedRate_mm_min` | Engraving speed |
| `minPower_pct` | Minimum laser power |
| `quality` | LaserGRBL quality setting |
| `whiteClip` | White clipping threshold |
| `contrast` | Image contrast adjustment |
| `brightness` | Image brightness adjustment |

## Hardware

- **Laser:** Diode laser engraver (via LaserGRBL)
- **Motion:** Ender-3 / Marlin-based material handling
- **Microscope:** WA5202 USB microscope (fixed position)
- **Orchestration:** n8n workflows

## Quality Review Methods

### Phase 1
- **Reference Comparison** — Compare to golden reference image
- **Manual Scoring** — Human rates results 1-5
- **Metric-Based** — Automated contrast, sharpness, histogram analysis

### Phase 2 (with sufficient data)
- **ML-Based** — Trained model predicts quality scores

## Tuning Process

1. Define test image and microscope focus region
2. Set parameter ranges to explore
3. Run tuning session (10 iterations)
4. System uses Bayesian optimization to select next parameters
5. Best parameters saved as new `material_name` in Material_Selects

## Integration

- Integrates with existing `lasergrbl-runner` and `marlin-runner`
- Writes results to Google Sheets (`Material_Selects`)
- Runs within n8n production workflow

## Project Structure

```
auto-tuner-LaserEngraver/
├── src/
│   ├── optimizer/          # Bayesian optimization engine
│   ├── analysis/           # Image quality analysis
│   ├── microscope/         # Microscope capture integration
│   └── sheets/             # Material_Selects integration
├── test_images/            # Reference and test images
├── results/                # Tuning session results
└── docs/                   # Documentation
```

## Related Projects

- [automated-laser-engraving](https://github.com/PonchoManBun/automated-laser-engraving) — Main production system
- `lasergrbl-runner` — LaserGRBL control service
- `marlin-runner` — Material handling service
- `capture-runner` — Image capture service

---

*Part of the automated laser engraving system*
