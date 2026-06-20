import smtplib
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.db import models

class AlertService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """Sends email alert using SMTP. Falls back to console log if unconfigured."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"[MOCK EMAIL ALERT] To: {to_email} | Subject: {subject} | Body: {body}")
            return True
            
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = settings.EMAILS_FROM_EMAIL
            msg['To'] = to_email
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False

    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """Sends SMS alert via mock Twilio API wrapper."""
        print(f"[MOCK SMS ALERT] To: {phone_number} | Msg: {message}")
        return True

    @staticmethod
    def send_whatsapp(phone_number: str, message: str) -> bool:
        """Sends WhatsApp message via mock Twilio WhatsApp API wrapper."""
        print(f"[MOCK WHATSAPP ALERT] To: whatsapp:{phone_number} | Msg: {message}")
        return True

    @staticmethod
    def process_field_alerts(db: Session, field_id: int) -> int:
        """
        Scans recent moisture stress, water deficit and canal status records for a field.
        Creates and dispatches alerts if thresholds are exceeded.
        """
        # Fetch field details
        field = db.query(models.Field).filter(models.Field.id == field_id).first()
        if not field:
            return 0
            
        alerts_triggered = 0
        
        # 1. Check Moisture Stress
        latest_stress = db.query(models.SoilMoistureTimeSeries).filter(
            models.SoilMoistureTimeSeries.field_id == field_id
        ).order_by(models.SoilMoistureTimeSeries.timestamp.desc()).first()
        
        if latest_stress and latest_stress.stress_level in ["Severe Stress", "Critical Stress"]:
            # Check if alert was already triggered today
            existing_alert = db.query(models.Alert).filter(
                models.Alert.field_id == field_id,
                models.Alert.trigger_type == "moisture_stress",
                models.Alert.sent_at >= datetime.utcnow().date()
            ).first()
            
            if not existing_alert:
                msg = f"Alert: Field '{field.name}' in village '{field.village}' is experiencing '{latest_stress.stress_level}' (Score: {latest_stress.stress_score:.2f}). Immediate irrigation is recommended."
                
                db_alert = models.Alert(
                    field_id=field_id,
                    trigger_type="moisture_stress",
                    severity="critical" if latest_stress.stress_level == "Critical Stress" else "warning",
                    message=msg
                )
                db.add(db_alert)
                alerts_triggered += 1
                
                # Dispatch alerts
                AlertService.send_email("farmer@agrisense.ai", "AgriSense Stress Alert", msg)
                AlertService.send_sms("+919876543210", msg)
                AlertService.send_whatsapp("+919876543210", msg)
                
        # 2. Check Water Deficit
        latest_deficit = db.query(models.WaterDeficitTimeSeries).filter(
            models.WaterDeficitTimeSeries.field_id == field_id
        ).order_by(models.WaterDeficitTimeSeries.timestamp.desc()).first()
        
        if latest_deficit and latest_deficit.water_deficit > 8.0: # Exceeds 8mm daily deficit
            existing_alert = db.query(models.Alert).filter(
                models.Alert.field_id == field_id,
                models.Alert.trigger_type == "water_deficit",
                models.Alert.sent_at >= datetime.utcnow().date()
            ).first()
            
            if not existing_alert:
                msg = f"Alert: Water deficit on field '{field.name}' has reached {latest_deficit.water_deficit:.1f} mm/day. Net crop requirement is {latest_deficit.net_water_requirement:.1f} mm."
                
                db_alert = models.Alert(
                    field_id=field_id,
                    trigger_type="water_deficit",
                    severity="warning",
                    message=msg
                )
                db.add(db_alert)
                alerts_triggered += 1
                
                # Dispatch alert
                AlertService.send_sms("+919876543210", msg)
                
        db.commit()
        return alerts_triggered
