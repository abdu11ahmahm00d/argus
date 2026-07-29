import os
from ultralytics import YOLO

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "runs", "detect", "train", "weights", "best.pt"
)
DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset", "data.yaml")


def validate():
    if not os.path.exists(MODEL_PATH):
        print(f"Trained model not found at: {MODEL_PATH}")
        print("Run train.py first.")
        return

    print(f"Loading model: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)

    print("Running validation...")
    results = model.val(
        data=DATASET_PATH,
        imgsz=640,
        batch=16,
        device=0,
    )

    print("\n=== Validation Results ===")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")
    print(f"Precision: {results.box.p:.4f}")
    print(f"Recall: {results.box.r:.4f}")

    per_class = results.box.ap_class_index
    for i, cls_id in enumerate(per_class):
        cls_name = results.names[cls_id] if hasattr(results, "names") else str(cls_id)
        print(f"  Class '{cls_name}': AP={results.box.ap[i]:.4f}")

    target_map = 0.75
    if results.box.map50 >= target_map:
        print(f"\n✓ mAP50 ({results.box.map50:.4f}) >= {target_map} — PASS")
    else:
        print(f"\n✗ mAP50 ({results.box.map50:.4f}) < {target_map} — WARNING")


if __name__ == "__main__":
    validate()
