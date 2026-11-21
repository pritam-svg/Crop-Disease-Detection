"""Evaluate an existing YOLO model on a labeled validation dataset.

Example: python evaluate_model.py --data data.yaml --weights best.pt
Does not retrain or overwrite model weights.
"""
import argparse
import json
from pathlib import Path
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Evaluate AgroVision YOLO using real labeled data")
    parser.add_argument("--data", required=True, help="Ultralytics dataset YAML path")
    parser.add_argument("--weights", default="best.pt", help="Trained YOLO weights")
    parser.add_argument("--split", default="val", choices=("val", "test"))
    parser.add_argument("--output", default="instance/model_evaluation.json")
    args = parser.parse_args()
    if not Path(args.data).is_file():
        parser.error("Dataset YAML does not exist: " + args.data)
    if not Path(args.weights).is_file():
        parser.error("Weights do not exist: " + args.weights)
    model = YOLO(args.weights)
    metrics = model.val(data=args.data, split=args.split, plots=True)
    result = {
        "dataset": str(Path(args.data).resolve()), "split": args.split,
        "precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
        "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map),
        "note": "Measured on labeled validation data; not a guarantee for field images."
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Saved metrics to", target)

if __name__ == "__main__":
    main()
