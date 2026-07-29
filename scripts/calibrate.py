import cv2
import yaml
import numpy as np
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

click_points = []
current_polygon_name = ""


def mouse_callback(event, x, y, flags, param):
    global click_points
    if event == cv2.EVENT_LBUTTONDOWN:
        click_points.append((x, y))
        print(f"  Point {len(click_points)}: ({x}, {y})")


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def save_zones(outer_zone, inner_zone):
    config = load_config()
    config["zones"] = {"outer_zone": outer_zone, "danger_zone": inner_zone}
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print("Zones saved to config.yaml")


def calibrate(source_url: str):
    global click_points, current_polygon_name
    cap = cv2.VideoCapture(source_url)
    if not cap.isOpened():
        print(f"Cannot open camera: {source_url}")
        return

    cv2.namedWindow("Calibrate")
    cv2.setMouseCallback("Calibrate", mouse_callback)

    outer_zone, inner_zone = [], []

    for polygon_name in [
        "OUTER tape square (safe zone)",
        "INNER tape square (danger zone)",
    ]:
        click_points = []
        current_polygon_name = polygon_name
        print(f"\n=== Click 4 corners of {polygon_name} ===")
        print("Left-click each corner. Press Enter when done. Press ESC to cancel.\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.resize(frame, (640, 480))

            for pt in click_points:
                cv2.circle(frame, pt, 4, (0, 255, 255), -1)
            if len(click_points) > 1:
                pts = np.array(click_points, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 255), 1)

            cv2.imshow("Calibrate", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 13 and len(click_points) == 4:  # Enter
                if polygon_name == "OUTER tape square (safe zone)":
                    outer_zone = list(click_points)
                else:
                    inner_zone = list(click_points)
                print(f"  {polygon_name}: {click_points}")
                break
            elif key == 27:  # ESC
                print("Calibration cancelled.")
                cap.release()
                cv2.destroyAllWindows()
                return

    cap.release()
    cv2.destroyAllWindows()

    save_zones(outer_zone, inner_zone)

    print("\n=== Verification ===")
    print(f"Outer zone: {outer_zone}")
    print(f"Danger zone: {inner_zone}")

    cap = cv2.VideoCapture(source_url)
    print("\nPress ESC to exit verification view.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (640, 480))
        overlay = frame.copy()

        if outer_zone:
            pts = np.array(outer_zone, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], (0, 255, 0))
            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
        if inner_zone:
            pts = np.array(inner_zone, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], (0, 0, 255))
            cv2.polylines(frame, [pts], True, (0, 0, 255), 2)

        display = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)
        cv2.imshow("Calibrate", display)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Calibration complete.")


if __name__ == "__main__":
    config = load_config()
    source = config["camera"]["source"]
    calibrate(source)
