"""Test data builders for creating test fixtures with fluent API."""

from typing import Optional
from src.db.models import Participant, ParticipationFormat


class FormBuilder:
    """Fluent builder for creating Form test data.

    Provides a clean interface for constructing valid and invalid form payloads
    for testing domain validation and API endpoints.

    Example:
        >>> form_data = (FormBuilder()
        ...     .with_full_name("Test User")
        ...     .with_email("test@example.com")
        ...     .as_student(university_id=1, study_year=3)
        ...     .with_team("TeamName", is_leader=True)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with minimal valid defaults."""
        self._data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "telegram": "@testuser",
            "phone": "+380501234567",
            "is_student": False,
            "study_year": None,
            "university_id": None,
            "category_id": 1,
            "skills": ["Python"],
            "format": "online",
            "has_team": False,
            "team_leader": False,
            "team_name": "",
            "wants_job": False,
            "job_description": "",
            "cv": "",
            "linkedin": "",
            "work_consent": False,
            "source": "test",
            "otherSource": None,
            "comment": None,
            "personal_data_consent": True,
        }

    def with_full_name(self, full_name: str) -> "FormBuilder":
        """Set full name."""
        self._data["full_name"] = full_name
        return self

    def with_email(self, email: str) -> "FormBuilder":
        """Set email address."""
        self._data["email"] = email
        return self

    def with_telegram(self, telegram: str) -> "FormBuilder":
        """Set telegram handle."""
        self._data["telegram"] = telegram
        return self

    def with_phone(self, phone: str) -> "FormBuilder":
        """Set phone number."""
        self._data["phone"] = phone
        return self

    def as_student(self, university_id: int, study_year: int) -> "FormBuilder":
        """Configure as student with university and study year."""
        self._data["is_student"] = True
        self._data["university_id"] = university_id
        self._data["study_year"] = study_year
        return self

    def as_non_student(self) -> "FormBuilder":
        """Configure as non-student."""
        self._data["is_student"] = False
        self._data["university_id"] = None
        self._data["study_year"] = None
        return self

    def with_category(self, category_id: int) -> "FormBuilder":
        """Set category ID."""
        self._data["category_id"] = category_id
        return self

    def with_skills(self, skills: list[str]) -> "FormBuilder":
        """Set skills list."""
        self._data["skills"] = skills
        return self

    def with_format(self, format: str) -> "FormBuilder":
        """Set participation format (online/offline)."""
        self._data["format"] = format
        return self

    def with_team(self, team_name: str, is_leader: bool = False) -> "FormBuilder":
        """Configure team participation."""
        self._data["has_team"] = True
        self._data["team_name"] = team_name
        self._data["team_leader"] = is_leader
        return self

    def without_team(self) -> "FormBuilder":
        """Configure without team."""
        self._data["has_team"] = False
        self._data["team_name"] = ""
        self._data["team_leader"] = False
        return self

    def seeking_job(
        self,
        cv_url: str,
        linkedin_url: str = "",
        job_description: str = "",
        work_consent: bool = True,
    ) -> "FormBuilder":
        """Configure as job seeker with CV and optional LinkedIn."""
        self._data["wants_job"] = True
        self._data["cv"] = cv_url
        self._data["linkedin"] = linkedin_url
        self._data["job_description"] = job_description
        self._data["work_consent"] = work_consent
        return self

    def with_cv(self, cv_url: str, work_consent: bool = False) -> "FormBuilder":
        """Set CV URL and work consent."""
        self._data["cv"] = cv_url
        self._data["work_consent"] = work_consent
        return self

    def with_linkedin(
        self, linkedin_url: str, work_consent: bool = False
    ) -> "FormBuilder":
        """Set LinkedIn URL and work consent."""
        self._data["linkedin"] = linkedin_url
        self._data["work_consent"] = work_consent
        return self

    def with_source(
        self, source: str, other_source: Optional[str] = None
    ) -> "FormBuilder":
        """Set event source and optional other source."""
        self._data["source"] = source
        self._data["otherSource"] = other_source
        return self

    def with_comment(self, comment: Optional[str]) -> "FormBuilder":
        """Set comment."""
        self._data["comment"] = comment
        return self

    def with_personal_data_consent(self, consent: bool = True) -> "FormBuilder":
        """Set personal data consent."""
        self._data["personal_data_consent"] = consent
        return self

    def with_field(self, field_name: str, value) -> "FormBuilder":
        """Set arbitrary field (for testing invalid values)."""
        self._data[field_name] = value
        return self

    def build(self) -> dict:
        """Return the constructed form data as dictionary."""
        return self._data.copy()


class ParticipantBuilder:
    """Fluent builder for creating Participant test data.

    Provides a clean interface for constructing Participant instances with
    various configurations for testing database interactions and business logic.

    Example:
        >>> participant = (ParticipantBuilder()
        ...     .with_full_name("Test User")
        ...     .with_email("test@example.com")
        ...     .with_telegram("@testuser")
        ...     .with_category(1)
        ...     .with_team(2)
        ...     .build()
        ... )
    """

    def __init__(self):
        """Initialize builder with minimal valid defaults."""
        self._data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "telegram": "@testuser",
            "phone": "+380501234567",
            "is_student": False,
            "study_year": None,
            "university_id": None,
            "category_id": 1,
            "team_id": None,
            "team_leader": False,
            "wants_job": False,
            "job_description": "",
            "participation_format": ParticipationFormat.ONLINE,
            "work_consent": False,
            "source": "test",
            "comment": None,
            "personal_data_consent": True,
        }

    def with_full_name(self, full_name: str) -> "ParticipantBuilder":
        """Set full name."""
        self._data["full_name"] = full_name
        return self

    def with_email(self, email: str) -> "ParticipantBuilder":
        """Set email address."""
        self._data["email"] = email
        return self

    def with_telegram(self, telegram: str) -> "ParticipantBuilder":
        """Set telegram handle."""
        self._data["telegram"] = telegram
        return self

    def with_phone(self, phone: str) -> "ParticipantBuilder":
        """Set phone number."""
        self._data["phone"] = phone
        return self

    def as_student(self, university_id: int, study_year: int) -> "ParticipantBuilder":
        """Configure as student with university and study year."""
        self._data["is_student"] = True
        self._data["university_id"] = university_id
        self._data["study_year"] = study_year
        return self

    def with_team(
        self, team_name: str, is_leader: bool = False
    ) -> "ParticipantBuilder":
        """Configure team participation."""
        self._data["team_name"] = team_name
        self._data["team_leader"] = is_leader
        return self

    def with_category(self, category_id: int) -> "ParticipantBuilder":
        """Set category ID."""
        self._data["category_id"] = category_id
        return self

    def build(self) -> dict:
        """Return the constructed form data as dictionary."""
        return self._data.copy()
