"""
Canal Command Boundary Refinement.

Compares the OFFICIAL command-area boundary polygon against the SAR-detected
actually-irrigated extent (inferred from a seasonal VH backscatter wetness/ponding
signature) for the same period, and flags discrepancy zones — areas inside the
official boundary that show no irrigation signature, and areas outside it that do.

This does not attempt full boundary REDRAWING (that needs cartographic review by
the irrigation department) — it produces a discrepancy report an officer can act on.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger


@dataclass
class BoundaryDiscrepancy:
    inside_boundary_not_irrigated_pct: float
    outside_boundary_but_irrigated_pct: float
    discrepancy_map: np.ndarray   # H x W: 0=match, 1=inside-not-irrigated, 2=outside-irrigated
    flagged_for_review: bool


def detect_irrigated_extent(vh_backscatter_db: np.ndarray, wetness_thresh_db: float = -14.0) -> np.ndarray:
    """Lower VH backscatter during the irrigation season is associated with surface
    wetness/ponding (especially in paddy systems); this is a coarse proxy, not a
    calibrated soil-moisture retrieval — sufficient for boundary-level QA, not for
    field-level water accounting."""
    return vh_backscatter_db <= wetness_thresh_db


def compute_boundary_discrepancy(
    official_boundary_mask: np.ndarray,   # H x W boolean
    vh_backscatter_db: np.ndarray,        # H x W
    discrepancy_review_thresh_pct: float = 10.0,
) -> BoundaryDiscrepancy:
    irrigated_extent = detect_irrigated_extent(vh_backscatter_db)

    inside_not_irrigated = official_boundary_mask & ~irrigated_extent
    outside_but_irrigated = ~official_boundary_mask & irrigated_extent

    inside_total = max(official_boundary_mask.sum(), 1)
    outside_total = max((~official_boundary_mask).sum(), 1)

    inside_not_irrigated_pct = 100 * inside_not_irrigated.sum() / inside_total
    outside_irrigated_pct = 100 * outside_but_irrigated.sum() / outside_total

    discrepancy_map = np.zeros(official_boundary_mask.shape, dtype=np.int8)
    discrepancy_map[inside_not_irrigated] = 1
    discrepancy_map[outside_but_irrigated] = 2

    flagged = (inside_not_irrigated_pct > discrepancy_review_thresh_pct or
               outside_irrigated_pct > discrepancy_review_thresh_pct)

    if flagged:
        logger.warning(
            f"Command area boundary discrepancy flagged: "
            f"{inside_not_irrigated_pct:.1f}% inside-not-irrigated, "
            f"{outside_irrigated_pct:.1f}% outside-but-irrigated"
        )

    return BoundaryDiscrepancy(
        inside_boundary_not_irrigated_pct=round(inside_not_irrigated_pct, 1),
        outside_boundary_but_irrigated_pct=round(outside_irrigated_pct, 1),
        discrepancy_map=discrepancy_map,
        flagged_for_review=flagged,
    )
