"""
Ground Truth Data Loader.

Loads crop-type ground truth points for the pilot command area from one of:
  1. A user-supplied CSV/GeoJSON (the preferred, real-data path)
  2. ICRISAT / Bhuvan / FASAL-style public sample sets (where openly downloadable)
  3. A documented, clearly-labeled SYNTHETIC fallback for demo continuity if no
     real data is available in time — synthetic samples must be tagged
     is_synthetic=True end-to-end so accuracy numbers can be reported honestly.

This module never silently substitutes synthetic data without logging it loudly
and flagging it in the returned metadata, because a hackathon demo that reports
"87% accuracy" on synthetic ground truth without disclosure is a credibility risk
with ISRO judges.
"""
from __future__ import annotations
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np
from loguru import logger


@dataclass
class GroundTruthPoint:
    latitude: float
    longitude: float
    crop_type: str
    observation_date: str
    source: str                 # "field_survey" | "fasal" | "icrisat" | "synthetic"
    is_synthetic: bool = False
    confidence: float = 1.0


@dataclass
class GroundTruthDataset:
    points: List[GroundTruthPoint] = field(default_factory=list)
    pilot_area_name: str = ""
    synthetic_fraction: float = 0.0

    def summary(self) -> dict:
        n = len(self.points)
        n_synth = sum(1 for p in self.points if p.is_synthetic)
        by_crop = {}
        for p in self.points:
            by_crop[p.crop_type] = by_crop.get(p.crop_type, 0) + 1
        return {
            "pilot_area": self.pilot_area_name,
            "total_points": n,
            "synthetic_points": n_synth,
            "synthetic_fraction": round(n_synth / n, 3) if n else 0.0,
            "class_distribution": by_crop,
        }


class GroundTruthLoader:
    """
    Resolves ground truth for a named pilot area, in priority order:
    real CSV/GeoJSON > documented public source > synthetic fallback.
    """

    REQUIRED_CSV_COLUMNS = {"latitude", "longitude", "crop_type", "observation_date"}

    def __init__(self, pilot_area_name: str, data_dir: Path = Path("./data/ground_truth")):
        self.pilot_area_name = pilot_area_name
        self.data_dir = Path(data_dir)

    def load(self, min_points_per_class: int = 30) -> GroundTruthDataset:
        real_path = self.data_dir / f"{self.pilot_area_name}.csv"
        if real_path.exists():
            logger.info(f"Loading REAL ground truth from {real_path}")
            return self._load_csv(real_path)

        logger.warning(
            f"No real ground truth file found at {real_path}. "
            f"Falling back to SYNTHETIC ground truth for {self.pilot_area_name}. "
            f"This MUST be disclosed in any accuracy claim made from this run."
        )
        return self._generate_synthetic(min_points_per_class)

    def _load_csv(self, path: Path) -> GroundTruthDataset:
        points: List[GroundTruthPoint] = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = self.REQUIRED_CSV_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"Ground truth CSV missing columns: {missing}")
            for row in reader:
                points.append(GroundTruthPoint(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    crop_type=row["crop_type"].strip(),
                    observation_date=row["observation_date"],
                    source=row.get("source", "field_survey"),
                    is_synthetic=False,
                    confidence=float(row.get("confidence", 1.0)),
                ))
        ds = GroundTruthDataset(points=points, pilot_area_name=self.pilot_area_name)
        logger.info(f"Loaded {len(points)} real ground truth points: {ds.summary()}")
        return ds

    def _generate_synthetic(self, min_points_per_class: int) -> GroundTruthDataset:
        """
        Generates spatially-jittered synthetic points around a pilot bounding box,
        using crop priors plausible for the pilot region. Every point is tagged
        is_synthetic=True and source='synthetic' — these must propagate into any
        model_run / accuracy report downstream (see Section 6 validation_service.py).
        """
        rng = np.random.default_rng(42)
        crop_classes = [
            "Wheat", "Rice/Paddy", "Cotton", "Sugarcane", "Maize",
            "Soybean", "Groundnut", "Mustard/Rapeseed", "Vegetables", "Fallow/Barren",
        ]
        # Placeholder bounding box for Chambal command area, Madhya Pradesh —
        # REPLACE with the real pilot area bbox before final submission.
        lat_range = (26.0, 26.6)
        lon_range = (77.8, 78.6)

        points: List[GroundTruthPoint] = []
        for crop in crop_classes:
            for _ in range(min_points_per_class):
                points.append(GroundTruthPoint(
                    latitude=float(rng.uniform(*lat_range)),
                    longitude=float(rng.uniform(*lon_range)),
                    crop_type=crop,
                    observation_date="2025-11-15",
                    source="synthetic",
                    is_synthetic=True,
                    confidence=0.5,
                ))
        ds = GroundTruthDataset(
            points=points,
            pilot_area_name=self.pilot_area_name,
            synthetic_fraction=1.0,
        )
        logger.warning(f"Generated SYNTHETIC ground truth: {ds.summary()}")
        return ds

    def export_geojson(self, dataset: GroundTruthDataset, out_path: Path) -> None:
        features = [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
            "properties": {
                "crop_type": p.crop_type,
                "observation_date": p.observation_date,
                "source": p.source,
                "is_synthetic": p.is_synthetic,
                "confidence": p.confidence,
            },
        } for p in dataset.points]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
        logger.info(f"Exported {len(features)} points to {out_path}")
