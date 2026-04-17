import argparse
import os
import statistics
import sys

from iris_key import (
    CASIA_IRIS_DIR,
    discover_casia_iris_images,
    generate_iris_code,
    hamming_distance,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Pairwise Hamming distance between iris binary codes "
            "for every image under CASIA-Iris."
        )
    )
    parser.add_argument(
        "--root",
        type=str,
        default=CASIA_IRIS_DIR,
        help=f"Dataset root (default: {CASIA_IRIS_DIR})",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        metavar="N",
        help="Only use the first N discovered images (after sort).",
    )
    args = parser.parse_args()

    paths = discover_casia_iris_images(args.root)
    if args.max_images is not None:
        paths = paths[: args.max_images]

    if len(paths) < 2:
        print(
            "Need at least two images to compare. Found:",
            len(paths),
            file=sys.stderr,
        )
        sys.exit(1)

    codes: list[tuple[str, str]] = []
    for path in paths:
        try:
            rel = os.path.relpath(path, args.root)
        except ValueError:
            rel = path
        code = generate_iris_code(path)
        codes.append((rel, code))

    print("Pairwise Hamming distance (proportion of differing bits)")
    print("---------------------------------------------------------")

    distances: list[float] = []
    per_image_distances: dict[str, list[float]] = {
        name: [] for name, _ in codes
    }
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            d = hamming_distance(codes[i][1], codes[j][1])
            distances.append(d)
            per_image_distances[codes[i][0]].append(d)
            per_image_distances[codes[j][0]].append(d)
            print(
                codes[i][0],
                "vs",
                codes[j][0],
                "->",
                round(d, 4),
            )

    n_pairs = len(distances)
    d_min = min(distances)
    d_max = max(distances)
    d_avg = statistics.fmean(distances)
    # Pairwise distances are rational with denominator len(code) (e.g. 1024 bits).
    print("---------------------------------------------------------")
    print(
        f"Images: {len(codes)}  Pairs: {n_pairs}\n"
        f"min Hamming distance: {d_min:.3f}\n"
        f"max Hamming distance: {d_max:.3f}\n"
        f"average Hamming distance: {d_avg:.3f}",
    )
    print("---------------------------------------------------------")
    print("Per-image min / max / average Hamming distance")
    print("---------------------------------------------------------")
    for name, ds in per_image_distances.items():
        print(
            f"{name}: "
            f"min={min(ds):.3f}  "
            f"max={max(ds):.3f}  "
            f"average={statistics.fmean(ds):.3f}"
        )


if __name__ == "__main__":
    main()
