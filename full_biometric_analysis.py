import os
import time
import random
import sys
import numpy as np
from iris_key import CASIA_IRIS_DIR, discover_casia_iris_images, generate_iris_code, hamming_distance, THRESHOLD

def get_eye_group(path):
    """Extract person_eye group from path (e.g., CASIA-Iris/001/L/1.jpg -> 001_L)."""
    parts = path.split(os.sep)
    try:
        idx = parts.index("CASIA-Iris")
        person = parts[idx + 1]
        eye = parts[idx + 2]
        return f"{person}_{eye}"
    except (ValueError, IndexError):
        return None

def run_comprehensive_analysis():
    print("[INIT] Initializing Streamlined Biometric Analysis...")
    log_file = open("biometric_analysis.log", "w")
    start_time = time.time()
    
    image_paths = discover_casia_iris_images(CASIA_IRIS_DIR)
    num_images = len(image_paths)
    print(f"[DATA] Total dataset size: {num_images} images.")
    
    if num_images < 2:
        print("[ERROR] Error: Not enough images for comparison.")
        return

    # 1. Pre-generate all iris codes
    print("[WAIT] Generating iris codes (Logs redirected to biometric_analysis.log)...")
    codes = {}
    for i, p in enumerate(image_paths):
        # Enable verbose only for the first 2 images to confirm pipeline
        v = (i < 2)
        if not v:
            # Manually capture logs for the file
            original_stdout = sys.stdout
            sys.stdout = log_file
            codes[p] = generate_iris_code(p, verbose=True)
            sys.stdout = original_stdout
        else:
            codes[p] = generate_iris_code(p, verbose=True)
    
    generation_time = time.time() - start_time
    print(f"[SUCCESS] Codes generated in {generation_time:.2f}s")
    
    # 2. Exhaustive Comparison
    intra_eye_distances = []
    inter_eye_distances = []
    
    # Store outliers for reporting
    false_rejects = [] # Same eye, distance > THRESHOLD
    false_accepts = [] # Different eye, distance < THRESHOLD
    
    total_pairs = num_images * (num_images - 1) // 2
    print(f"[PROCESS] Comparing {total_pairs} pairs...")
    comparison_start = time.time()
    
    count = 0
    for i in range(num_images):
        for j in range(i + 1, num_images):
            p1, p2 = image_paths[i], image_paths[j]
            
            # Redirect pair-wise logs to file
            original_stdout = sys.stdout
            sys.stdout = log_file
            
            hd = hamming_distance(codes[p1], codes[p2], verbose=True)
            
            group1 = get_eye_group(p1)
            group2 = get_eye_group(p2)
            
            is_same_eye = (group1 == group2) if group1 and group2 else False
            
            log_msg = f"Pair {p1} vs {p2} | Same: {is_same_eye} | HD: {hd:.4f}\n"
            log_file.write(log_msg)
            sys.stdout = original_stdout
            
            if is_same_eye:
                intra_eye_distances.append(hd)
                if hd >= THRESHOLD:
                    false_rejects.append((group1, os.path.basename(p1), os.path.basename(p2), hd))
            else:
                inter_eye_distances.append(hd)
                if hd < THRESHOLD:
                    false_accepts.append((group1, group2, os.path.basename(p1), os.path.basename(p2), hd))
            
            count += 1
            if count % 500 == 0:
                print(f"   Progress: {count}/{total_pairs} pairs compared...", end='\r')
                    
    comparison_time = time.time() - comparison_start
    log_file.close()
    print(f"\n[SUCCESS] Comparison finished in {comparison_time:.2f}s")
    
    # 3. reporting
    print(f"\n" + "="*50)
    print("BIOMETRIC PERFORMANCE REPORT")
    print("="*50)
    print(f"Total Images: {num_images}")
    print(f"Total Pairs Compared: {total_pairs}")
    print(f"Total Analysis Time: {time.time() - start_time:.2f}s")
    print("-" * 30)
    
    if intra_eye_distances:
        print(f"INTRA-EYE (Same Eye)")
        print(f"   Count: {len(intra_eye_distances)}")
        print(f"   Average HD: {np.mean(intra_eye_distances):.4f}")
        print(f"   Min: {np.min(intra_eye_distances):.4f}")
        print(f"   Max: {np.max(intra_eye_distances):.4f}")
        print(f"   Std Dev: {np.std(intra_eye_distances):.4f}")
    
    print("-" * 30)
    
    if inter_eye_distances:
        print(f"INTER-EYE (Different Eyes)")
        print(f"   Count: {len(inter_eye_distances)}")
        print(f"   Average HD: {np.mean(inter_eye_distances):.4f}")
        print(f"   Min: {np.min(inter_eye_distances):.4f}")
        print(f"   Max: {np.max(inter_eye_distances):.4f}")
        print(f"   Std Dev: {np.std(inter_eye_distances):.4f}")
    
    print("="*50)
    print(f"ANALYSIS AT THRESHOLD: {THRESHOLD}")
    print(f"[DEBUG] Threshold={THRESHOLD:.4f}")
    print("="*50)
    
    frr = (len(false_rejects) / len(intra_eye_distances) * 100) if intra_eye_distances else 0
    far = (len(false_accepts) / len(inter_eye_distances) * 100) if inter_eye_distances else 0
    
    print(f"False Rejection Rate (FRR): {frr:.2f}% ({len(false_rejects)} pairs)")
    print(f"False Acceptance Rate (FAR): {far:.2f}% ({len(false_accepts)} pairs)")
    print(f"[DEBUG] FAR={far/100:.4f} | FRR={frr/100:.4f}")
    
    if false_rejects:
        print("\nWARNING: FALSE REJECTS (Outliers):")
        for group, f1, f2, hd in sorted(false_rejects, key=lambda x: x[3], reverse=True)[:10]:
            print(f"   - Group {group}: {f1} vs {f2} | HD: {hd:.4f}")
        if len(false_rejects) > 10:
            print(f"     ... and {len(false_rejects) - 10} more.")

    if false_accepts:
        print("\nERROR: FALSE ACCEPTS (Security Risks):")
        for g1, g2, f1, f2, hd in sorted(false_accepts, key=lambda x: x[4])[:10]:
            print(f"   - {g1}:{f1} vs {g2}:{f2} | HD: {hd:.4f}")
        if len(false_accepts) > 10:
            print(f"     ... and {len(false_accepts) - 10} more.")

    # 4. Optimal Threshold Suggestion
    if intra_eye_distances and inter_eye_distances:
        suggested = (np.mean(intra_eye_distances) + np.mean(inter_eye_distances)) / 2
        print("\nOPTIMIZATION")
        print(f"   Suggested Optimal Threshold: {suggested:.4f}")

if __name__ == "__main__":
    run_comprehensive_analysis()
