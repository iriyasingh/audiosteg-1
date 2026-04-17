import os

from iris_key import (
    CASIA_IRIS_DIR,
    discover_casia_iris_images,
    generate_iris_key,
    generate_iris_code,
)


def main() -> None:
    folder = CASIA_IRIS_DIR
    print("Checking CASIA-Iris dataset:", folder)

    image_paths = discover_casia_iris_images(folder)
    print("Images found:", len(image_paths))

    assert len(image_paths) > 0, (
        "No images found under CASIA-Iris. "
        "Expected .jpg/.png/.bmp files somewhere in the tree."
    )

    # If `MAX_IMAGES` is set, limit runtime; otherwise check everything.
    max_images_env = os.environ.get("MAX_IMAGES")
    if max_images_env:
        max_images = int(max_images_env)
        image_paths = image_paths[:max_images]
        print(f"Limiting to first {len(image_paths)} image(s) (MAX_IMAGES).")

    failures = []
    expected_len = 32 * 32  # 32x32 binary grid

    for path in image_paths:
        try:
            code1 = generate_iris_code(path)
            code2 = generate_iris_code(path)

            assert code1 == code2, f"Non-deterministic output for {path}"
            assert len(code1) == expected_len, f"Unexpected code length for {path}"
            assert set(code1).issubset({"0", "1"}), (
                f"Code contains non-binary chars for {path}"
            )

            key1 = generate_iris_key(path)
            key2 = generate_iris_key(path)
            assert key1 == key2, f"Non-deterministic iris key for {path}"
        except Exception as e:  # noqa: BLE001 - test script should report any issue
            failures.append((path, str(e)))

    if failures:
        print("Failures:")
        for path, msg in failures:
            print("-", path)
            print("  ", msg)
        raise AssertionError(f"{len(failures)} image(s) failed consistency checks")

    print(f"All {len(image_paths)} images passed consistency checks.")


if __name__ == "__main__":
    main()
