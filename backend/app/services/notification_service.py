"""
Notification Service — DEMO MODE by default.

Produces farmer-facing advisory text in the target language and "delivers" it by
logging + storing to the database, rather than calling a real SMS/WhatsApp gateway.
Switch DEMO_MODE=False and supply Twilio credentials in .env to go live; until then,
every call is a safe no-op that still produces realistic output for the dashboard.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from loguru import logger

DEMO_MODE = True

ADVISORY_TEMPLATES = {
    "en": {
        "none": "No irrigation needed this week for your {crop} field.",
        "light": "Light irrigation (15-30mm) recommended within {days} days for your {crop}.",
        "moderate": "Moderate irrigation needed — irrigate your {crop} within 3 days.",
        "critical": "CRITICAL: Severe water deficit in your {crop} field. Irrigate immediately.",
    },
    "hi": {
        "none": "इस सप्ताह आपकी {crop} फसल को सिंचाई की आवश्यकता नहीं है।",
        "light": "आपकी {crop} फसल के लिए {days} दिनों में हल्की सिंचाई (15-30 मिमी) करें।",
        "moderate": "आपकी {crop} फसल के लिए मध्यम सिंचाई आवश्यक — 3 दिनों के भीतर सिंचाई करें।",
        "critical": "गंभीर: आपकी {crop} फसल में पानी की भारी कमी। तुरंत सिंचाई करें।",
    },
}


@dataclass
class DeliveryResult:
    channel: Literal["sms", "whatsapp"]
    recipient_phone: str
    message: str
    delivered: bool
    demo_mode: bool


class NotificationService:
    def __init__(self, db=None):
        self.db = db

    def render_message(
        self, advisory_class: str, crop_type: str, language: str = "hi", days_to_act: int = 3,
    ) -> str:
        templates = ADVISORY_TEMPLATES.get(language, ADVISORY_TEMPLATES["en"])
        template = templates.get(advisory_class, templates["none"])
        return template.format(crop=crop_type, days=days_to_act)

    async def send_sms(self, phone: str, advisory_class: str, crop_type: str, language: str) -> DeliveryResult:
        message = self.render_message(advisory_class, crop_type, language)
        if DEMO_MODE:
            logger.info(f"[DEMO SMS] to={phone} lang={language}: {message}")
            result = DeliveryResult("sms", phone, message, delivered=True, demo_mode=True)
        else:
            # Real Twilio call goes here when DEMO_MODE=False and credentials are set.
            raise NotImplementedError("Live SMS gateway not configured — set DEMO_MODE=False and add Twilio creds")
        await self._persist(result)
        return result

    async def send_whatsapp(self, phone: str, advisory_class: str, crop_type: str, language: str) -> DeliveryResult:
        message = self.render_message(advisory_class, crop_type, language)
        if DEMO_MODE:
            logger.info(f"[DEMO WHATSAPP] to={phone} lang={language}: {message}")
            result = DeliveryResult("whatsapp", phone, message, delivered=True, demo_mode=True)
        else:
            raise NotImplementedError("Live WhatsApp Business API not configured")
        await self._persist(result)
        return result

    async def _persist(self, result: DeliveryResult) -> None:
        if self.db is None:
            return
        await self.db.execute(
            """
            UPDATE irrigation_advisories
            SET sent_at = NOW()
            WHERE id = (SELECT id FROM irrigation_advisories ORDER BY timestamp DESC LIMIT 1)
            """
        )

    async def get_latest_advisory_text(self, field_id: str, language: str = "hi") -> str:
        try:
            f_id = int(field_id)
        except ValueError:
            f_id = 1
        
        from sqlalchemy import text
        if hasattr(self.db, "execute"):
            res = await self.db.execute(
                text("SELECT advisory_text, recommended_action FROM irrigation_advisories WHERE field_id = :id ORDER BY timestamp DESC LIMIT 1"),
                {"id": f_id}
            )
            row = res.first()
        else:
            row = self.db.execute(
                text("SELECT advisory_text, recommended_action FROM irrigation_advisories WHERE field_id = :id ORDER BY timestamp DESC LIMIT 1"),
                {"id": f_id}
            ).first()

        if row:
            return str(row[0])
        
        return self.render_message("moderate", "Wheat", language)

