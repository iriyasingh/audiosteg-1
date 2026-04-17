import os
import cv2
import numpy as np
from iris_key import CASIA_IRIS_DIR, discover_casia_iris_images, generate_iris_code, hamming_distance

def get_group(path):
    parts = path.split(os.sep)
    try:
        base_idx = parts.index("CASIA-Iris")
        person = parts[base_idx + 1]
        eye = parts[base_idx + 2]
        return f"{person}_{eye}"
    except (ValueError, IndexError):
        return None

def analyze_all_distances():
    image_paths = discover_casia_iris_images(CASIA_IRIS_DIR)
    n = len(image_paths)
    
    codes = {}
    for p in image_paths:
        codes[p] = generate_iris_code(p)
        
    intra_distances = []
    inter_distances = []
    
    intra_pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = image_paths[i], image_paths[j]
            hd = hamming_distance(codes[p1], codes[p2])
            
            g1 = get_group(p1)
            g2 = get_group(p2)
            
            if g1 and g2 and g1 == g2:
                intra_distances.append(hd)
                intra_pairs.append((g1, os.path.basename(p1), os.path.basename(p2), hd))
            else:
                inter_distances.append(hd)
                
    print("# Hamming Distance Analysis Report")
    print("\n## Intra-eye Distances (Same Eye, Different Image)")
    print("| Group | Image 1 | Image 2 | Hamming Distance |")
    print("|-------|---------|---------|------------------|")
    for group, i1, i2, hd in sorted(intra_pairs, key=lambda x: x[3]):
        print(f"| {group} | {i1} | {i2} | {hd:.4f} |")
        
    print("\n## Statistics")
    if intra_distances:
        print(f"**Intra-eye**: min={min(intra_distances):.4f}, max={max(intra_distances):.4f}, avg={np.mean(intra_distances):.4f}")
    if inter_distances:
        print(f"**Inter-eye**: min={min(inter_distances):.4f}, max={max(inter_distances):.4f}, avg={np.mean(inter_distances):.4f}")
        
    # Suggested threshold is usually halfway between the means
    if intra_distances and inter_distances:
        threshold = (np.mean(intra_distances) + np.mean(inter_distances)) / 2
        print(f"\n**Suggested Threshold**: {threshold:.4f}")

if __name__ == "__main__":
    analyze_all_distances()
