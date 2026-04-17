import os

import argparse

import cv2
import hashlib
import numpy as np

# Default dataset folder next to this package (e.g. CASIA-Iris/001/1.jpg).
CASIA_IRIS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "CASIA-Iris",
)

THRESHOLD = 0.2519


def discover_casia_iris_images(root_dir=None):
    """List image paths under the CASIA-Iris tree (jpg/jpeg/png/bmp)."""
    root_dir = root_dir if root_dir is not None else CASIA_IRIS_DIR
    paths = []
    if not os.path.isdir(root_dir):
        return paths
    for dirpath, _, filenames in os.walk(root_dir):
        for name in sorted(filenames):
            lower = name.lower()
            if lower.endswith((".jpg", ".jpeg", ".png", ".bmp")):
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


def generate_iris_code(image_path, verbose=True):
    filename = os.path.basename(image_path)
    img = cv2.imread(image_path, 0)

    if img is None:
        raise ValueError(f"Image not found: {image_path}")

    # Standardize initial size
    img = cv2.resize(img, (128, 128))
    img = cv2.equalizeHist(img)

    # Task 1: Preprocessing Debug Logs
    if verbose:
        print(
            f"[DEBUG] {filename} | "
            f"size={img.shape} | "
            f"min={img.min()} | "
            f"max={img.max()}"
        )

    # LBP(P=16, R=2) on a 32x8 grid = 4096 bits
    P, R = 16, 2
    grid_w, grid_h = 32, 8
    small = cv2.resize(img, (grid_w, grid_h))
    
    angles = np.linspace(0, 2 * np.pi, P, endpoint=False)
    dx = R * np.cos(angles)
    dy = -R * np.sin(angles) # OpenCV y-axis is down
    
    lbp_bits = []
    
    for r in range(grid_h):
        for c in range(grid_w):
            center_val = small[r, c]
            
            # Sample 16 points around the center
            for p in range(P):
                nr = r + dy[p]
                nc = c + dx[p]
                
                # Bilinear Interpolation with horizontal wrap-around
                r0 = int(np.floor(nr))
                r1 = np.clip(r0 + 1, 0, grid_h - 1)
                r0 = np.clip(r0, 0, grid_h - 1)
                
                c0 = int(np.floor(nc)) % grid_w
                c1 = (c0 + 1) % grid_w
                
                dr = nr - np.floor(nr)
                dc = nc - np.floor(nc)
                
                v00 = small[r0, c0]
                v01 = small[r0, c1]
                v10 = small[r1, c0]
                v11 = small[r1, c1]
                
                val = (1-dr)*(1-dc)*v00 + dr*(1-dc)*v10 + (1-dr)*dc*v01 + dr*dc*v11
                
                # Compare to center
                lbp_bits.append('1' if val >= center_val else '0')

    code_str = "".join(lbp_bits)
    
    # Validation
    code_len = len(code_str)
    ones_count = code_str.count('1')
    density = ones_count / code_len

    if verbose:
        print(
            f"[DEBUG] LBP(16,2) | length={code_len} | "
            f"ones={ones_count} | density={density:.2f}"
        )

    if verbose and (density < 0.05 or density > 0.95):
        print("[WARNING] Low-information iris code detected")

    return code_str


def hamming_distance(code1, code2, verbose=True):
    """
    Calculate Hamming distance with rotation compensation.
    Optimized for speed using numpy bitwise operations.
    """
    if len(code1) != len(code2):
        raise ValueError("Codes must be same length")

    n = len(code1)
    
    # Convert string codes to numpy arrays for bitwise comparison
    # We use ord(c) - 48 ('0' -> 0, '1' -> 1)
    a = np.frombuffer(code1.encode(), dtype=np.int8) - 48
    b = np.frombuffer(code2.encode(), dtype=np.int8) - 48

    min_hd = 1.0
    best_shift = 0
    max_shift = 8
    
    for shift in range(-max_shift, max_shift + 1):
        # Circular shift using numpy (much faster than string slicing)
        shifted_b = np.roll(b, shift)
        
        # Calculate bit differences
        diff = np.count_nonzero(a != shifted_b)
        hd = diff / n
        
        if hd < min_hd:
            min_hd = hd
            best_shift = shift

    if verbose:
        print(
            f"[DEBUG] Best shift={best_shift} | "
            f"HD={min_hd:.4f}"
        )
    
    return min_hd


def iris_code_to_key(code):

    block_size = 16

    stable_bits = ""

    for i in range(0, len(code), block_size):

        block = code[i:i + block_size]

        if block.count('1') > block.count('0'):
            stable_bits += '1'
        else:
            stable_bits += '0'

    key = hashlib.sha256(
        stable_bits.encode()
    ).hexdigest()

    return key


def generate_iris_key(image_path):
    """
    Deterministically derive an iris "key" from an iris image.

    This is based on `generate_iris_code()` followed by `iris_code_to_key()`.
    """
    code = generate_iris_code(image_path)
    return iris_code_to_key(code)


def _print_codes(max_images: int | None = None) -> None:
    image_paths = discover_casia_iris_images(CASIA_IRIS_DIR)
    if not image_paths:
        raise RuntimeError(
            f"No images found under CASIA_IRIS_DIR: {CASIA_IRIS_DIR}"
        )

    if max_images is not None:
        image_paths = image_paths[:max_images]

    for p in image_paths:
        rel = os.path.relpath(p, CASIA_IRIS_DIR)
        code = generate_iris_code(p)
        print(f"{rel} {code}")


def _print_keys(max_images: int | None = None) -> None:
    image_paths = discover_casia_iris_images(CASIA_IRIS_DIR)
    if not image_paths:
        raise RuntimeError(
            f"No images found under CASIA_IRIS_DIR: {CASIA_IRIS_DIR}"
        )

    if max_images is not None:
        image_paths = image_paths[:max_images]

    for p in image_paths:
        rel = os.path.relpath(p, CASIA_IRIS_DIR)
        key = generate_iris_key(p)
        print(f"{rel} {key}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate iris codes/keys from CASIA-Iris images."
    )
    parser.add_argument(
        "--print-codes",
        action="store_true",
        help="Print raw iris bitstrings (codes) for all samples.",
    )
    parser.add_argument(
        "--print-keys",
        action="store_true",
        help="Print derived iris keys for all discovered samples.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Limit printed samples for faster inspection.",
    )

    args = parser.parse_args()

    if args.print_codes:
        _print_codes(max_images=args.max_images)
    elif args.print_keys:
        _print_keys(max_images=args.max_images)
    else:
        parser.print_help()