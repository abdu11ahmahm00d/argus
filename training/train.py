import os
from ultralytics import YOLO

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset", "data.yaml")
MODEL_OUTPUT = os.path.join(
    os.path.dirname(__file__), "runs", "detect", "train", "weights", "best.pt"
)


def train():
    print(f"Loading pretrained YOLOv8n...")
    model = YOLO("yolov8n.pt")

    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found at: {DATASET_PATH}")
        print("Place your dataset in training/dataset/ with data.yaml")
        return

    print(f"Starting training with dataset: {DATASET_PATH}")
    model.train(
        data=DATASET_PATH,
        epochs=50,
        imgsz=640,
        device=0,
        batch=16,
        workers=4,
        patience=10,
        augment=True,
        project=os.path.join(os.path.dirname(__file__), "runs"),
        name="train",
        exist_ok=True,
    )

    print(f"Training complete. Model saved to: {MODEL_OUTPUT}")
    print("Run validate.py to check performance.")


if __name__ == "__main__":
    train()
