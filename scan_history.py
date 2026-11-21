"""Local SQLite scan history for AgroVision. No third-party dependencies."""
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "scan_history.sqlite3")

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scanned_at TEXT NOT NULL,
        image_path TEXT NOT NULL,
        output_path TEXT NOT NULL,
        xai_path TEXT,
        health_status TEXT NOT NULL,
        disease_counts TEXT NOT NULL
    )""")
    columns = {row[1] for row in db.execute("PRAGMA table_info(scans)")}
    if "detections" not in columns:
        db.execute("ALTER TABLE scans ADD COLUMN detections TEXT NOT NULL DEFAULT '[]'")
    return db

def save_scan(image_path, output_path, xai_path, health_status, disease_counts, detections=None):
    with connect() as db:
        db.execute("""INSERT INTO scans
            (scanned_at, image_path, output_path, xai_path, health_status, disease_counts, detections)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(), image_path, output_path,
             xai_path, health_status, json.dumps(disease_counts), json.dumps(detections or [])))

def get_dashboard_data():
    with connect() as db:
        rows = db.execute("SELECT * FROM scans ORDER BY id DESC").fetchall()
    scans = []
    diseases = Counter()
    days = Counter()
    statuses = Counter()
    for row in rows:
        counts = json.loads(row["disease_counts"])
        statuses[row["health_status"]] += 1
        for name, count in counts.items():
            if name.lower() not in ("healthy", "background"):
                diseases[name] += count
        date = row["scanned_at"][:10]
        days[date] += 1
        detections = json.loads(row["detections"] or "[]")
        confidences = [d["confidence"] for d in detections if isinstance(d.get("confidence"), (int, float))]
        scans.append(dict(row) | {"counts": counts, "detections_list": detections,
                                 "avg_confidence": round(sum(confidences) / len(confidences) * 100, 1) if confidences else None,
                                 "date": date,
                                 "detected": ", ".join(name for name, n in counts.items() if n > 0) or "No class detected"})
    today = datetime.now(timezone.utc).date()
    trend = [{"date": (today - timedelta(days=i)).isoformat(),
              "count": days[(today - timedelta(days=i)).isoformat()]}
             for i in range(6, -1, -1)]
    total = len(scans)
    all_confidences = [d["confidence"] for scan in scans for d in scan["detections_list"] if isinstance(d.get("confidence"), (int, float))]
    return {"total_detections": sum(sum(scan["counts"].values()) for scan in scans),
            "avg_confidence": round(sum(all_confidences) / len(all_confidences) * 100, 1) if all_confidences else None,
            "scans": scans, "total": total, "healthy": statuses["healthy"],
            "diseased": statuses["disease"], "inconclusive": statuses["inconclusive"],
            "healthy_pct": round(statuses["healthy"] / total * 100) if total else 0,
            "diseases": diseases.most_common(), "trend": trend, "recent": scans[:12]}
