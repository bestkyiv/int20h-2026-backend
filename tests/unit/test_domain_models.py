import pytest
from pydantic import ValidationError

from domain.models import Form, normalize_phone_number


def test_normalize_phone_ok():
    assert normalize_phone_number("+380501234567") == "+380501234567"


def test_normalize_phone_invalid_raises():
    with pytest.raises(ValueError):
        normalize_phone_number("not-a-phone")


@pytest.mark.parametrize("linkedin", ["ftp://x.com", "//invalid"])
def test_invalid_linkedin_raises(linkedin):
    payload = {
        "full_name": "Test User",
        "email": "u@example.com",
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
        "linkedin": linkedin,
        "work_consent": False,
        "source": "test",
        "otherSource": None,
        "comment": None,
        "personal_data_consent": True,
    }

    with pytest.raises(ValidationError):
        Form(**payload)


def test_wants_job_requires_cv():
    payload = {
        "full_name": "Test User",
        "email": "u2@example.com",
        "telegram": "@testuser2",
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
        "wants_job": True,
        "job_description": "",
        "cv": "",  # missing CV
        "linkedin": "",
        "work_consent": False,
        "source": "test",
        "otherSource": None,
        "comment": None,
        "personal_data_consent": True,
    }

    with pytest.raises(ValidationError):
        Form(**payload)
