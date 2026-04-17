import os
import cv2
import numpy as np
from iris_key import CASIA_IRIS_DIR, discover_casia_iris_images, generate_iris_code, hamming_distance

def analyze_distances():
    images = discover_casia_iris_images(CASIA_IRIS_DIR)
    eye_groups = {}
    
    for path in images:
        parts = path.split(os.sep)
        try:
            base_idx = parts.index("CASIA-Iris")
            person = parts[base_idx + 1]
            eye = parts[base_idx + 2]
            group_id = f"{person}_{eye}"
            if group_id not in eye_groups:
                eye_groups[group_id] = []
            eye_groups[group_id].append(path)
        except (ValueError, IndexError):
            continue

    print(f"{'Eye Group':<15} | {'Pairs':<6} | {'Avg HD'}")
    print("-" * 35)

    all_intra_distances = []
    
    for group_id, paths in eye_groups.items():
        if len(paths) < 2:
            continue
        
        codes = [generate_iris_code(p) for p in paths]
        distances = []
        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                hd = hamming_distance(codes[i], codes[j])
                distances.append(hd)
                all_intra_distances.append(hd)
        
        avg_hd = sum(distances) / len(distances)
        print(f"{group_id:<15} | {len(distances):<6} | {avg_hd:.4f}")

    if all_intra_distances:
        overall_avg = sum(all_intra_distances) / len(all_intra_distances)
        print("-" * 35)
        print(f"Overall Intra-Eye Avg Distance: {overall_avg:.4f}")
    else:
        print("No pairs found.")

if __name__ == "__main__":
    analyze_distances()
