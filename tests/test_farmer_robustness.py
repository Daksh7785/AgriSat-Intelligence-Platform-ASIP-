import pytest
import os
from pathlib import Path
from app.services.voice_advisory_service import VoiceAdvisoryService
from app.services.rain_aware_advisory_service import apply_rain_nudge
from app.services.feedback_loop_service import FeedbackLoopService


def test_voice_tts_generation(tmp_path):
    # Set output dir to temp path
    service = VoiceAdvisoryService(output_dir=tmp_path)
    
    text = "इस सप्ताह आपकी गेहूं फसल के लिए हल्की सिंचाई आवश्यक है।"
    res = service.generate(text, language="hi", advisory_id="test_field_1")
    
    assert Path(res.audio_path).exists()
    assert os.path.getsize(res.audio_path) > 0
    assert res.language == "hi"
    assert res.duration_estimate_seconds > 0.0


def test_rain_advisory_nudging():
    # 1. Moderate stress (irrigation requirement = 40mm) and 20mm rain expected -> downgrade to light, req=20mm
    res1 = apply_rain_nudge(advisory_class="moderate", irrigation_requirement_mm=40.0, forecast_rain_mm_next_3_days=20.0)
    assert res1.adjusted_advisory_class == "light"
    assert res1.adjusted_irrigation_requirement_mm == 20.0
    assert "consider deferring" in res1.nudge_message

    # 2. Critical stress and 20mm rain expected -> no downgrade (critical override)
    res2 = apply_rain_nudge(advisory_class="critical", irrigation_requirement_mm=40.0, forecast_rain_mm_next_3_days=20.0)
    assert res2.adjusted_advisory_class == "critical"
    assert res2.adjusted_irrigation_requirement_mm == 20.0
    assert "deficit is severe" in res2.nudge_message


@pytest.mark.asyncio
async def test_feedback_active_learning_threshold():
    # Create service with None DB (in-memory mode for unit testing)
    service = FeedbackLoopService(db=None, wrong_flag_threshold=2)
    
    # Submitting first feedback (does not queue, no DB)
    rec1 = await service.submit_feedback(
        field_id="12",
        advisory_id="101",
        feedback_type="outcome_seemed_wrong",
        submitted_by_role="farmer"
    )
    assert rec1.feedback_type == "outcome_seemed_wrong"
    assert rec1.field_id == "12"
