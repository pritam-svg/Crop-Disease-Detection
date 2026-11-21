# AgroVision — Development Dashboard Guide

This document describes the additions on the `agrovision-development` branch of the user's fork. The original YOLO model and EigenCAM image processing remain in `app.py`.

## Local startup (Windows PowerShell)
```powershell
git switch agrovision-development
git pull origin agrovision-development
.\.venv\Scripts\Activate.ps1
python app.py
```
Open http://127.0.0.1:5000/dashboard.

## Pages
- `/`: rice leaf scanner (YOLO + EigenCAM)
- `/dashboard`: recorded scan counts, trends, confidence summaries and scan history
- `/dashboard/knowledge`: disease information reference
- `/dashboard/export.csv`: export local scan history
- `/dashboard/report/<scan_id>`: printable scan report (browser Print → Save as PDF)

## Storage
Scan history uses SQLite at `instance/scan_history.sqlite3`. It is intentionally excluded from Git. Back it up separately before reinstalling or deleting the project. Scan images are in `static/uploads/`. A scan is recorded after a successful image-processing run. Existing scans without saved per-object confidence remain valid.

## Languages
English, Bengali and Hindi selectors currently translate primary scanner labels and dashboard headings. Detailed disease guidance, reports and some secondary UI copy remain in English; full translation is ongoing.

## Validation (optional; requires labeled data)
```powershell
python evaluate_model.py --data path\to\data.yaml --weights best.pt --split val
```
This creates `instance/model_evaluation.json`, which the dashboard reads on the next refresh. YOLO may also save confusion-matrix and other plots in its validation output directory. The script does **not** retrain the model or fabricate accuracy figures. Dataset YAML must point to actual labeled images; no evaluation data is bundled by this script.

## Smoke-test checklist
1. Open scanner and dashboard without errors.
2. Upload one valid JPG/PNG and verify annotated output and optional EigenCAM.
3. Refresh dashboard and confirm total scan count increased by one.
4. Open scan report and check images and confidence values.
5. Export CSV and check header and record.
6. Switch language and dark mode.
7. Restart Flask and verify scan history persists.
8. Validate with a labeled dataset before quoting precision, recall or mAP in the final presentation.

## Architecture
```text
Browser → Flask app.py → YOLO best.pt → bounding boxes/classes
                     ↘ EigenCAM → explanation image
                     ↘ scan_history.py → SQLite → Dashboard/CSV/Reports
Labeled dataset → evaluate_model.py → evaluation JSON → Dashboard
```

**Important:** This system is an AI-assisted screening prototype, not a confirmed agricultural diagnosis. Detection confidence is not equivalent to calibrated probability or clinical certainty.
