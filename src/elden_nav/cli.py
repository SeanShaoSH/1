from __future__ import annotations

import argparse
import json

from .indexer import FeatureIndex, build_index
from .navigator import ScreenNavigator


def cmd_build_index(args: argparse.Namespace) -> int:
    index = build_index(args.metadata)
    index.save(args.output)
    print(f"Index saved: {args.output} (samples={len(index.items)})")
    return 0


def cmd_locate(args: argparse.Namespace) -> int:
    index = FeatureIndex.load(args.index)
    nav = ScreenNavigator(index)
    estimate, matches = nav.locate(args.image, top_k=args.top_k)

    payload = {
        "input_image": args.image,
        "estimated": {
            "x": estimate.x,
            "y": estimate.y,
            "confidence": estimate.confidence,
        },
        "matches": [
            {
                "sample_label": m.sample.label,
                "sample_coord": [m.sample.x, m.sample.y],
                "score": m.score,
            }
            for m in matches
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Elden Ring map navigator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("build-index", help="Build feature index from sample metadata CSV")
    p_index.add_argument("--metadata", required=True, help="CSV with columns: image_path,x,y,label")
    p_index.add_argument("--output", required=True, help="Output index path (.pkl)")
    p_index.set_defaults(func=cmd_build_index)

    p_locate = sub.add_parser("locate", help="Estimate coordinates from screenshot")
    p_locate.add_argument("--index", required=True, help="Input index file (.pkl)")
    p_locate.add_argument("--image", required=True, help="Gameplay screenshot path")
    p_locate.add_argument("--top-k", type=int, default=5, help="Top K matches for coordinate fusion")
    p_locate.set_defaults(func=cmd_locate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
