import numpy as np

from elden_nav.indexer import FeatureIndex, IndexedSample
from elden_nav.models import FrameSample
from elden_nav.navigator import ScreenNavigator


def _make_descriptor(seed: int, rows: int = 64) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(rows, 32), dtype=np.uint8)


def test_locate_from_descriptors_prefers_closest_visual_match():
    query = _make_descriptor(42)

    near = query.copy()
    # Add small noise: keep most rows unchanged
    near[:10] = _make_descriptor(100, 10)

    far = _make_descriptor(999)

    index = FeatureIndex(
        items=[
            IndexedSample(FrameSample("near.png", 100.0, 200.0, "near"), near),
            IndexedSample(FrameSample("far.png", 900.0, 800.0, "far"), far),
        ]
    )

    nav = ScreenNavigator(index)
    est, matches = nav.locate_from_descriptors(query, top_k=2)

    assert matches[0].sample.label == "near"
    assert est.x < 500
    assert est.y < 500
    assert 0.0 <= est.confidence <= 1.0
