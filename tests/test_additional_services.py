"""Tests for ValidationService and NotificationService."""
import pytest
import numpy as np
from app.services.validation_service import ValidationService
from app.services.notification_service import NotificationService


def test_validation_evaluation():
    service = ValidationService()
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_pred = np.array([0, 1, 2, 0, 2, 1])
    class_names = ["Wheat", "Rice", "Cotton"]
    
    report = service.evaluate_classification(
        y_true=y_true,
        y_pred=y_pred,
        class_names=class_names,
        model_version="test-model-1.0",
        ground_truth_is_synthetic=True,
        synthetic_fraction=1.0
    )
    
    assert report.model_version == "test-model-1.0"
    assert report.overall_accuracy == pytest.approx(4/6)
    assert report.ground_truth_is_synthetic is True
    assert report.synthetic_fraction == 1.0
    assert "WARNING" in report.caveat


def test_validation_meets_target():
    service = ValidationService()
    y_true = np.array([0, 1, 2])
    y_pred = np.array([0, 1, 2])
    class_names = ["Wheat", "Rice", "Cotton"]
    
    report = service.evaluate_classification(
        y_true=y_true,
        y_pred=y_pred,
        class_names=class_names,
        model_version="test-model-1.0",
        ground_truth_is_synthetic=False
    )
    assert service.meets_target(report, min_oa=0.85, min_kappa=0.80) is True


@pytest.mark.anyio
async def test_notification_rendering():
    service = NotificationService()
    
    # Test message rendering in Hindi
    hi_msg = service.render_message("moderate", "गेहूं", language="hi")
    assert "मध्यम सिंचाई" in hi_msg
    assert "गेहूं" in hi_msg
    
    # Test message rendering in English
    en_msg = service.render_message("critical", "Wheat", language="en")
    assert "CRITICAL" in en_msg
    assert "Wheat" in en_msg
    
    # Test SMS/WhatsApp send in demo mode
    sms_res = await service.send_sms("+919876543210", "light", "Cotton", "en")
    assert sms_res.delivered is True
    assert sms_res.demo_mode is True
    
    wa_res = await service.send_whatsapp("+919876543210", "none", "Rice", "hi")
    assert wa_res.delivered is True
    assert wa_res.demo_mode is True
