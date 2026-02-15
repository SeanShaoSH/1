from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .indexer import FeatureIndex, extract_orb_descriptors
from .models import MatchResult


@dataclass
class CoordinateEstimate:
    x: float
    y: float
    confidence: float


class ScreenNavigator:
    """Estimate map coordinates from a gameplay frame via feature matching."""

    def __init__(self, index: FeatureIndex):
        self.index = index
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def _score_descriptors(self, query: np.ndarray, target: np.ndarray) -> float:
        if len(query) == 0 or len(target) == 0:
            return 0.0

        knn_matches = self.matcher.knnMatch(query, target, k=2)

        good = 0
        for pair in knn_matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good += 1

        norm = min(len(query), len(target))
        if norm == 0:
            return 0.0
        return float(good / norm)

    def locate_from_descriptors(
        self,
        query_descriptors: np.ndarray,
        top_k: int = 5,
    ) -> tuple[CoordinateEstimate, list[MatchResult]]:
        scores: list[MatchResult] = []
        for item in self.index.items:
            score = self._score_descriptors(query_descriptors, item.descriptors)
            scores.append(MatchResult(sample=item.sample, score=score))

        scores.sort(key=lambda m: m.score, reverse=True)
        selected = scores[: max(1, top_k)]

        weights = np.array([max(m.score, 1e-6) for m in selected], dtype=np.float64)
        xs = np.array([m.sample.x for m in selected], dtype=np.float64)
        ys = np.array([m.sample.y for m in selected], dtype=np.float64)

        x = float(np.average(xs, weights=weights))
        y = float(np.average(ys, weights=weights))

        top_score = selected[0].score if selected else 0.0
        mean_score = float(np.mean([m.score for m in selected])) if selected else 0.0
        confidence = float(min(1.0, 0.65 * top_score + 0.35 * mean_score))

        return CoordinateEstimate(x=x, y=y, confidence=confidence), selected

    def locate(self, image_path: str, top_k: int = 5) -> tuple[CoordinateEstimate, list[MatchResult]]:
        desc = extract_orb_descriptors(image_path)
        return self.locate_from_descriptors(desc, top_k=top_k)
