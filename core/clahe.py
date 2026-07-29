import cv2
import numpy as np


def clahe_enhance(
    crop_bgr: np.ndarray, clip_limit: float = 2.0, tile_grid_size: int = 8
) -> np.ndarray:
    if crop_bgr.size == 0:
        return crop_bgr
    lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size)
    )
    L_enhanced = clahe.apply(L)
    merged = cv2.merge([L_enhanced, A, B])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
