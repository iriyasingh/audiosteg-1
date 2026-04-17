import os
import numpy as np
import wave
import random
import base64
import hashlib
import secrets
import hmac
from cryptography.fernet import Fernet
import json
import zlib

from iris_key import (
    generate_iris_code,
    hamming_distance,
    THRESHOLD
)

AUTH_DIR = "biometric_config"
TEMPLATE_ENC = os.path.join(AUTH_DIR, "template.enc")
TEMPLATE_HASH = os.path.join(AUTH_DIR, "template.hash")
SALT_PATH = os.path.join(AUTH_DIR, "salt.bin")
KEY_PATH = os.path.join(AUTH_DIR, "secret_key.bin")
# Redefining for backward compatibility if needed, but we use new paths
TEMPLATE_PATH = TEMPLATE_ENC 


def generate_salt(length=16):
    """Generate a cryptographically secure random salt."""
    return secrets.token_bytes(length)


def _derive_keystream(salt, length):
    """
    Derive a keystream of specified length for XOR encryption.
    Uses PBKDF2-HMAC-SHA256.
    """
    # We use a fixed 'password' for the biometric derivation, 
    # relying on the salt for individual eye uniqueness.
    return hashlib.pbkdf2_hmac(
        'sha256',
        b"biometric_derivation_password",
        salt,
        100000,
        dklen=length
    )


def save_template_secure(code):
    """
    Encrypt the iris code and save with integrity hash.
    - Result: template.enc, template.hash, salt.bin
    """
    if not os.path.exists(AUTH_DIR):
        os.makedirs(AUTH_DIR, exist_ok=True)

    salt = generate_salt()
    keystream = _derive_keystream(salt, len(code))

    # XOR Encryption (Stream Cipher)
    # code is a string of '0' and '1'
    encrypted = bytes([ord(c) ^ k for c, k in zip(code, keystream)])

    # Integrity Hash
    integrity_hash = hashlib.sha256(encrypted + salt).hexdigest()

    # Save files
    with open(TEMPLATE_ENC, "wb") as f:
        f.write(encrypted)
    with open(SALT_PATH, "wb") as f:
        f.write(salt)
    with open(TEMPLATE_HASH, "w") as f:
        f.write(integrity_hash)

    print("Template stored securely")


def verify_template_secure(new_code):
    """
    Verify a new iris code against the secure template.
    1. Verify file integrity (Template Hash)
    2. Decrypt template
    3. Calculate Hamming Distance
    """
    if not all(os.path.exists(p) for p in [TEMPLATE_ENC, SALT_PATH, TEMPLATE_HASH]):
        raise FileNotFoundError("Biometric data missing. Please enroll.")

    with open(TEMPLATE_ENC, "rb") as f:
        encrypted = f.read()
    with open(SALT_PATH, "rb") as f:
        salt = f.read()
    with open(TEMPLATE_HASH, "r") as f:
        stored_hash = f.read().strip()

    # Integrity Check using constant-time comparison
    current_hash = hashlib.sha256(encrypted + salt).hexdigest()
    if not hmac.compare_digest(current_hash, stored_hash):
        print("Security Alert: Template integrity check failed!")
        return False

    # Decrypt
    keystream = _derive_keystream(salt, len(encrypted))
    decrypted_code = "".join([chr(b ^ k) for b, k in zip(encrypted, keystream)])

    # Hamming Distance Check
    dist = hamming_distance(new_code, decrypted_code)

    print(f"[DEBUG] Threshold={THRESHOLD:.4f}")
    if dist < THRESHOLD:
        print("Authentication successful")
        return True
    else:
        print("Authentication failed")
        return False


def regenerate_template(code):
    """Generate new salt and re-save template."""
    save_template_secure(code)
    print("Template regenerated successfully")


def revoke_and_reenroll(iris_path):
    """Delete old template data and create new with same key."""
    for p in [TEMPLATE_ENC, TEMPLATE_HASH, SALT_PATH]:
        if os.path.exists(p):
            os.remove(p)
    print("Old template revoked")
    
    code = generate_iris_code(iris_path)
    save_template_secure(code)
    print("New template enrolled")


def enroll_user(iris_path, template_file=None, key_file=KEY_PATH):
    """Updated Enrollment calling save_template_secure."""
    code = generate_iris_code(iris_path)
    save_template_secure(code)

    # Key generation logic remains same but independent of template bits
    if not os.path.exists(key_file):
        random_bytes = secrets.token_bytes(32)
        key_base64 = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
        with open(key_file, "w") as f:
            f.write(key_base64)
    return True


def verify_user(iris_path, template_file=None):
    """Updated Verification calling verify_template_secure."""
    new_code = generate_iris_code(iris_path)
    return verify_template_secure(new_code)


def load_key(key_file=KEY_PATH):
    """
    Load the persistent key from file.
    """
    if not os.path.exists(key_file):
        raise FileNotFoundError("Key file not found.")

    with open(key_file, "r") as f:
        return f.read().strip().encode('utf-8')


def generate_key_from_auth(iris_path):
    """
    Helper to verify user and return the stored key.
    """
    if verify_user(iris_path):
        return load_key()
    else:
        raise PermissionError("Access Denied: Biometric authentication failed.")


def generate_key(iris_path):
    # This is kept for backward compatibility if needed, 
    # but the system now prefers load_key() after verify_user().
    return generate_key_from_auth(iris_path)


def encrypt_bytes(data, iris_path):
    if not verify_user(iris_path):
        raise PermissionError("Biometric authentication failed.")
    cipher = Fernet(load_key())
    return cipher.encrypt(data)


def decrypt_bytes(data, iris_path):
    if not verify_user(iris_path):
        raise PermissionError("Biometric authentication failed.")
    cipher = Fernet(load_key())
    return cipher.decrypt(data)


# Keep legacy aliases if needed
def encrypt_message(msg, iris_path):
    return encrypt_bytes(msg.encode(), iris_path).decode()


def decrypt_message(msg, iris_path):
    return decrypt_bytes(msg.encode(), iris_path).decode()


def bytes_to_bits(data):
    return ''.join(format(b, '08b') for b in data)


def bits_to_bytes(bits):
    if isinstance(bits, list):
        bits = ''.join(bits)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8) if i+8 <= len(bits))


PAYLOAD_TYPE_TEXT = 0
PAYLOAD_TYPE_FILE = 1

def prepare_payload(data, mode, filename=None):
    """Wrap data with metadata and optional compression."""
    type_byte = mode.to_bytes(1, byteorder='big')
    if mode == PAYLOAD_TYPE_FILE:
        compressed = zlib.compress(data)
        metadata = json.dumps({"filename": filename}).encode('utf-8')
        metadata_len = len(metadata).to_bytes(4, byteorder='big')
        return type_byte + metadata_len + metadata + compressed
    else:
        # Simple text or bytes
        return type_byte + data


def parse_payload(wrapped_data):
    """Unwrap payload and return (mode, data, filename)."""
    if len(wrapped_data) < 1:
        return None
    mode = int.from_bytes(wrapped_data[0:1], byteorder='big')
    if mode == PAYLOAD_TYPE_FILE:
        metadata_len = int.from_bytes(wrapped_data[1:5], byteorder='big')
        metadata = json.loads(wrapped_data[5:5+metadata_len].decode('utf-8'))
        compressed = wrapped_data[5+metadata_len:]
        data = zlib.decompress(compressed)
        return mode, data, metadata.get("filename")
    else:
        return mode, wrapped_data[1:], None


def _set_detail_parity(a, b, target_bit):
    """
    Force the parity of the Haar-detail coefficient (a - b) to target_bit.
    """
    detail = int(a) - int(b)
    current_bit = detail & 1
    if current_bit == target_bit:
        return a, b

    # Toggle parity by changing one sample by 1 with clipping safety.
    if b < np.int16(32767):
        b = np.int16(int(b) + 1)
    elif b > np.int16(-32768):
        b = np.int16(int(b) - 1)
    else:
        # Fallback to modifying the first sample.
        if a < np.int16(32767):
            a = np.int16(int(a) + 1)
        elif a > np.int16(-32768):
            a = np.int16(int(a) - 1)

    return a, b


def _get_detail_bit(a, b):
    """
    Read embedded bit from Haar-detail coefficient parity.
    """
    return str((int(a) - int(b)) & 1)


def embed_message(
    audio_file,
    payload_data,
    output_file,
    iris_path,
    mode=PAYLOAD_TYPE_TEXT,
    filename=None
):
    # Prepare and encrypt payload
    wrapped = prepare_payload(payload_data, mode, filename)
    encrypted = encrypt_bytes(wrapped, iris_path)

    with wave.open(audio_file, 'rb') as wav:
        params = wav.getparams()
        frames = wav.readframes(params.nframes)

    audio = np.frombuffer(frames, dtype=np.int16).copy()

    # Up-mix mono to stereo for double capacity
    if params.nchannels == 1:
        audio = np.repeat(audio, 2)
        params = params._replace(nchannels=2)

    usable_len = len(audio) - (len(audio) % 2)
    if usable_len < 2:
        raise ValueError("Audio too short")

    bits = bytes_to_bits(encrypted)

    length_bits = format(
        len(bits),
        '032b'
    )

    payload_bits = length_bits + bits

    pair_count = usable_len // 2

    if len(payload_bits) > pair_count:

        raise ValueError(
            f"Payload too large. Required: {len(payload_bits)} bits, Available: {pair_count} bits"
        )

    random.seed(
        generate_key(iris_path)
    )

    positions = list(range(pair_count))

    random.shuffle(positions)

    for i, bit in enumerate(payload_bits):

        pair_idx = positions[i]
        left = 2 * pair_idx
        right = left + 1
        a, b = audio[left], audio[right]
        audio[left], audio[right] = _set_detail_parity(
            a,
            b,
            int(bit)
        )

    with wave.open(
        output_file,
        'wb'
    ) as out:

        out.setparams(params)

        out.writeframes(
            audio.tobytes()
        )


def extract_message(
    stego_file,
    iris_path
):
    # Verify user before proceeding
    if not verify_user(iris_path):
        raise PermissionError("Biometric authentication failed. Cannot extract message.")

    with wave.open(
        stego_file,
        'rb'
    ) as wav:

        frames = wav.readframes(
            wav.getnframes()
        )

    audio = np.frombuffer(
        frames,
        dtype=np.int16
    )

    usable_len = len(audio) - (len(audio) % 2)
    if usable_len < 2:
        raise ValueError("Audio too short")

    random.seed(
        generate_key(iris_path)
    )

    pair_count = usable_len // 2
    positions = list(range(pair_count))

    random.shuffle(positions)

    length_bits = []

    for i in range(32):

        pair_idx = positions[i]
        left = 2 * pair_idx
        right = left + 1
        length_bits.append(_get_detail_bit(audio[left], audio[right]))

    bit_length = int(
        ''.join(length_bits),
        2
    )

    if (
        bit_length <= 0
        or 32 + bit_length > pair_count
    ):

        raise ValueError(
            "Invalid or corrupted message"
        )

    msg_bits = []

    for i in range(
        32,
        32 + bit_length
    ):

        pair_idx = positions[i]
        left = 2 * pair_idx
        right = left + 1
        msg_bits.append(_get_detail_bit(audio[left], audio[right]))

    encrypted_payload = bits_to_bytes(msg_bits)

    # Decrypt raw bytes
    decrypted_payload = decrypt_bytes(encrypted_payload, iris_path)

    # Parse payload structure
    return parse_payload(decrypted_payload)
