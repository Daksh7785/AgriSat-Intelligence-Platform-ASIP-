"""Farmer/officer feedback API."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from app.services.feedback_loop_service import FeedbackLoopService
from app.dependencies import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackSubmission(BaseModel):
    field_id: str
    advisory_id: str
    feedback_type: Literal["followed", "not_followed", "outcome_seemed_wrong", "crop_correction"]
    submitted_by_role: Literal["farmer", "officer"]
    note: Optional[str] = None
    corrected_crop_type: Optional[str] = None


@router.post("/submit")
async def submit_feedback(submission: FeedbackSubmission, db=Depends(get_db)):
    service = FeedbackLoopService(db)
    return await service.submit_feedback(
        submission.field_id, submission.advisory_id, submission.feedback_type,
        submission.submitted_by_role, submission.note, submission.corrected_crop_type,
    )


@router.get("/review-queue")
async def get_review_queue(db=Depends(get_db)):
    """Combined model-uncertainty + farmer-feedback active learning queue."""
    service = FeedbackLoopService(db)
    return await service.get_review_queue()
