"""Serwisy aplikacyjne (SurveyService, EducationService...) - Faza 2+."""

from application.services.education_service import EducationService
from application.services.survey_service import SurveyService, SurveyValidationError

__all__ = ["SurveyService", "SurveyValidationError", "EducationService"]
