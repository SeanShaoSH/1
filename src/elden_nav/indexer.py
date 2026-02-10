from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from .models import FrameSample


@dataclass
class IndexedSample:
    sample: FrameSample
    descriptors: np.ndarray


@dataclass
class FeatureIndex:
    items: list[IndexedSample]

    def save(self, output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, input_path: str | Path) -> "FeatureIndex":
        with Path(input_path).open("rb") as f:
            data = pickle.load(f)
        if not isinstance(data, FeatureIndex):
            raise ValueError("Invalid index file: object is not FeatureIndex")
        return data


def read_samples_from_csv(metadata_csv: str | Path) -> list[FrameSample]:
    df = pd.read_csv(metadata_csv)
    required = {"image_path", "x", "y", "label"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Metadata missing required columns: {sorted(missing)}")

    samples: list[FrameSample] = []
    for row in df.to_dict(orient="records"):
        samples.append(
            FrameSample(
                image_path=str(row["image_path"]),
                x=float(row["x"]),
                y=float(row["y"]),
                label=str(row["label"]),
            )
        )
    return samples


def extract_orb_descriptors(image_path: str | Path) -> np.ndarray:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Image not found or unreadable: {image_path}")

    orb = cv2.ORB_create(nfeatures=2000)
    _kps, descriptors = orb.detectAndCompute(image, None)
    if descriptors is None:
        return np.empty((0, 32), dtype=np.uint8)
    return descriptors


def build_index(metadata_csv: str | Path) -> FeatureIndex:
    samples = read_samples_from_csv(metadata_csv)
    items: list[IndexedSample] = []

    for sample in samples:
        descriptors = extract_orb_descriptors(sample.image_path)
        items.append(IndexedSample(sample=sample, descriptors=descriptors))

    return FeatureIndex(items=items)
