import os
import shutil

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")


def download():
    os.makedirs(DATASET_DIR, exist_ok=True)

    print("=" * 60)
    print("ARGUS — Dataset Downloader")
    print("=" * 60)
    print()
    print("This script downloads the Roboflow Hard Hat Workers dataset")
    print("for YOLOv8 training.")
    print()
    print("Prerequisites:")
    print("  1. A free Roboflow account (roboflow.com)")
    print("  2. Your Roboflow API key (Settings → API Key)")
    print()
    print("Steps:")
    print("  pip install roboflow")
    print(f"  python {os.path.relpath(__file__)}")
    print()
    print("The script will prompt for your API key and download")
    print("the dataset into training/dataset/.")
    print()
    print("Dataset reference:")
    print("  Roboflow Universe: 'Hard Hat Workers'")
    print("  7,035 images · 3 classes (helmet, head, person)")
    print("  YOLOv8 format · train/valid/test splits")
    print()
    print("Once downloaded, verify training/dataset/data.yaml exists,")
    print("then run: python training/train.py")
    print()

    use_roboflow = input("Download via Roboflow API? (y/n): ").strip().lower()

    if use_roboflow == "y":
        _download_via_roboflow()
    else:
        _manual_instructions()


def _download_via_roboflow():
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Installing roboflow package...")
        os.system("pip install roboflow")
        from roboflow import Roboflow

    api_key = input("Enter your Roboflow API key: ").strip()
    if not api_key:
        print("No API key provided. Use manual download instead.")
        _manual_instructions()
        return

    print("\nDownloading Hard Hat Workers dataset (v2)...")
    rf = Roboflow(api_key=api_key)
    project = rf.workspace("roboflow-58fyf").project("hard-hat-workers")
    dataset = project.version(2).download("yolov8", location=DATASET_DIR)

    print(f"\nDownload complete!")
    print(f"Dataset location: {DATASET_DIR}")
    print(f"data.yaml: {os.path.join(DATASET_DIR, 'data.yaml')}")

    data_yaml = os.path.join(DATASET_DIR, "data.yaml")
    if os.path.exists(os.path.join(DATASET_DIR, "data.yaml")):
        print("✓ Ready for training: python training/train.py")
    else:
        print("⚠ Could not verify data.yaml. Check the dataset folder.")


def _manual_instructions():
    print("\n--- Manual Download ---")
    print()
    print("1. Go to: https://universe.roboflow.com/roboflow-58fyf/hard-hat-workers")
    print("2. Click 'Download Dataset'")
    print("3. Format: YOLOv8")
    print("4. Extract the ZIP into training/dataset/")
    print("5. Confirm training/dataset/data.yaml exists")
    print("6. Run: python training/train.py")
    print()
    print("Expected structure:")
    print("  training/dataset/data.yaml")
    print("  training/dataset/train/")
    print("  training/dataset/valid/")
    print("  training/dataset/test/")


if __name__ == "__main__":
    download()
