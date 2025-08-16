from PIL import Image
import numpy as np
from matplotlib.colors import to_rgb
import time


def get_rgb(color):
    if isinstance(color, str):
        r,g,b = to_rgb(color)
        return np.array([int(r*255), int(g*255), int(b*255)], dtype=np.int16)
    return np.array(color, dtype=np.int16)

def get_rgb_from_name_or_tuple(color):
    if isinstance(color, str):
        rgb = to_rgb(color)
        return tuple(int(c * 255) for c in rgb)
    return color


def find_rightmost_endpoint(image_path, target_color, tolerance=150):
    tgt = get_rgb_from_name_or_tuple(target_color)                     # (3,)
    print(tgt)
    tol2 = tolerance * tolerance

    img = Image.open(image_path).convert("RGB")
    arr = np.asarray(img, dtype=np.int16)          # (H,W,3)

    # 各画素とターゲット色の二乗距離（√なし）
    diff = arr - tgt                               # (H,W,3)
    dist2 = np.sum(diff*diff, axis=2)              # (H,W)

    # しきい値以内 = 線の画素のマスク
    mask = dist2 <= tol2                           # (H,W) bool
    if not mask.any():
        return None

    # True の座標を一括取得
    ys, xs = np.where(mask)

    # 最も右（xが最大）のインデックスを取る
    k = np.argmax(xs)
    # k = np.argmin(xs)
    end = time.perf_counter() #計測開始
    return int(xs[k]), int(ys[k])

# 例
image_path = "test.png"
target_color = "red"
tolerance = 150
pt = find_rightmost_endpoint(image_path, target_color, tolerance)
print(pt)
