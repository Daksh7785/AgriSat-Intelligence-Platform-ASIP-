from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User
from app.models.farmer import Farmer
from app.models.command_area import CommandArea
from app.models.field import Field
from app.models.satellite_acquisition import SatelliteAcquisition
from app.models.crop_classification import CropClassification
from app.models.phenology_record import PhenologyRecord
from app.models.stress_assessment import StressAssessment
from app.models.irrigation_advisory import IrrigationAdvisory, CommandAreaAdvisorySummary
from app.models.model_run import ModelRun, ActiveLearningQueueEntry
from app.models.advisory_feedback import AdvisoryFeedback
from app.models.audit_log import AuditLog, InsuranceEvidenceRecord
