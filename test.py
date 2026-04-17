import os
from stego import enroll_user, verify_user, regenerate_template, AUTH_DIR, TEMPLATE_ENC
from iris_key import CASIA_IRIS_DIR, generate_iris_code

# 1. Setup paths for same-eye samples (Group 004_L has HD ~0.008)
img_a = os.path.join(CASIA_IRIS_DIR, "004", "L", "1'.jpg")
img_b = os.path.join(CASIA_IRIS_DIR, "004", "L", "1.jpg.jpg")
img_wrong = os.path.join(CASIA_IRIS_DIR, "001", "R", "2.jpg")

print("--- Secure Biometric Test ---")

# Step 1: Enroll
print("\n[1] Enrolling user...")
enroll_user(img_a)
print(f"Files created in {AUTH_DIR}: {os.listdir(AUTH_DIR)}")

# Step 2: Verify Match
print("\n[2] Testing Match (Same Eye, different image):")
verify_user(img_b)

# Step 3: Verify Fail
print("\n[3] Testing Rejection (Different Eye):")
verify_user(img_wrong)

# Step 4: Template Regeneration (Cancelable Biometric)
print("\n[4] Rotating Salt (Regenerating Template):")
code = generate_iris_code(img_a)
regenerate_template(code)
print("Template updated with new salt. Previous match still works:")
verify_user(img_b)
