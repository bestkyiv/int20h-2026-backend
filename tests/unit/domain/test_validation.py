"""Comprehensive domain model validation tests.

Tests all field boundaries, cross-field constraints, and edge cases
for the Form model and related validation logic.
"""

import pytest
from pydantic import ValidationError

from src.domain.models import Form, normalize_phone_number
from tests.builders import FormBuilder


# ========================================
# Phone Number Normalization Tests
# ========================================


def test_normalize_phone_ok():
    """Valid phone number should be normalized to E164 format."""
    assert normalize_phone_number("+380501234567") == "+380501234567"


def test_normalize_phone_invalid_raises():
    """Invalid phone number should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid phone number"):
        normalize_phone_number("not-a-phone")


@pytest.mark.parametrize(
    "phone",
    [
        "",  # Empty string
        "123",  # Too short
        "abcdefghijk",  # Letters
        "+1",  # Too short with +
        # Note: "++380501234567" is actually valid - phonenumbers library normalizes it
    ],
)
def test_normalize_phone_invalid_formats(phone):
    """Various invalid phone formats should raise ValueError."""
    with pytest.raises(ValueError):
        normalize_phone_number(phone)


# ========================================
# Field Length Boundary Tests
# ========================================


@pytest.mark.parametrize(
    "full_name,should_pass",
    [
        ("AB", True),  # Min length = 2
        ("A", False),  # Below min
        ("", False),  # Empty
        ("A" * 100, True),  # Max length = 100
        ("A" * 101, False),  # Above max
        ("Test User", True),  # Normal case
    ],
)
def test_full_name_length_boundaries(full_name, should_pass):
    """Test full_name min_length=2, max_length=100."""
    builder = FormBuilder().with_full_name(full_name)

    if should_pass:
        form = Form(**builder.build())
        assert form.full_name == full_name
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "full_name" in str(exc_info.value)


@pytest.mark.parametrize(
    "email,should_pass",
    [
        ("a@b.co", True),  # Short valid email
        ("test@example.com", True),  # Normal email
        ("e" * 88 + "@example.com", True),  # Max length = 100 (88 + 12)
        ("e" * 89 + "@example.com", False),  # Above max (101 chars)
        ("invalid-email", False),  # No @
        ("@example.com", False),  # No local part
        ("test@", False),  # No domain
        ("test test@example.com", False),  # Space in email
    ],
)
def test_email_validation(email, should_pass):
    """Test email max_length=100 and EmailStr format validation."""
    builder = FormBuilder().with_email(email)

    if should_pass:
        form = Form(**builder.build())
        assert form.email == email
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "email" in str(exc_info.value)


@pytest.mark.parametrize(
    "telegram,should_pass",
    [
        ("@", True),  # Min length = 1
        ("", False),  # Empty
        ("@user", True),  # Normal
        ("t" * 100, True),  # Max length = 100
        ("t" * 101, False),  # Above max
        ("@testuser123", True),  # With numbers
    ],
)
def test_telegram_length_boundaries(telegram, should_pass):
    """Test telegram min_length=1, max_length=100."""
    builder = FormBuilder().with_telegram(telegram)

    if should_pass:
        form = Form(**builder.build())
        assert form.telegram == telegram
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "telegram" in str(exc_info.value)


@pytest.mark.parametrize(
    "phone,should_pass",
    [
        ("+380501234567", True),  # Valid phone
        ("+1234567890" + "0" * 89, False),  # Above max_length=100 after normalization
    ],
)
def test_phone_length_boundaries(phone, should_pass):
    """Test phone max_length=100 (after normalization)."""
    builder = FormBuilder().with_phone(phone)

    if should_pass:
        form = Form(**builder.build())
        assert form.phone is not None
    else:
        with pytest.raises((ValidationError, ValueError)):
            Form(**builder.build())


@pytest.mark.parametrize(
    "team_name,should_pass",
    [
        ("", True),  # Empty when has_team=False
        ("Team", True),  # Normal
        ("T" * 100, True),  # Max length = 100
        ("T" * 101, False),  # Above max
        ("Команда 🚀", True),  # Unicode/emoji
    ],
)
def test_team_name_length_boundaries(team_name, should_pass):
    """Test team_name max_length=100."""
    builder = FormBuilder().with_field("team_name", team_name)

    if should_pass:
        form = Form(**builder.build())
        assert form.team_name == team_name
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "team_name" in str(exc_info.value)


@pytest.mark.parametrize(
    "job_description,should_pass",
    [
        ("", True),  # Empty
        ("Looking for a job", True),  # Normal
        ("D" * 2000, True),  # Max length = 2000
        ("D" * 2001, False),  # Above max
    ],
)
def test_job_description_length_boundaries(job_description, should_pass):
    """Test job_description max_length=2000."""
    builder = FormBuilder().with_field("job_description", job_description)

    if should_pass:
        form = Form(**builder.build())
        assert form.job_description == job_description
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "job_description" in str(exc_info.value)


@pytest.mark.parametrize(
    "source,should_pass",
    [
        ("x", True),  # Min length = 1
        ("", False),  # Empty
        ("test", True),  # Normal
        ("s" * 100, True),  # Max length = 100
        ("s" * 101, False),  # Above max
    ],
)
def test_source_length_boundaries(source, should_pass):
    """Test source min_length=1, max_length=100."""
    builder = FormBuilder().with_source(source)

    if should_pass:
        form = Form(**builder.build())
        assert form.source == source
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "source" in str(exc_info.value)


@pytest.mark.parametrize(
    "comment,should_pass",
    [
        (None, True),  # Null allowed
        ("", True),  # Empty
        ("Some comment", True),  # Normal
        ("C" * 2000, True),  # Max length = 2000
        ("C" * 2001, False),  # Above max
    ],
)
def test_comment_length_boundaries(comment, should_pass):
    """Test comment max_length=2000."""
    builder = FormBuilder().with_comment(comment)

    if should_pass:
        form = Form(**builder.build())
        assert form.comment == comment
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "comment" in str(exc_info.value)


@pytest.mark.parametrize(
    "skills,should_pass",
    [
        ([], True),  # Empty list allowed
        (["Python"], True),  # Single skill
        (["Python", "JavaScript", "Go"], True),  # Multiple skills
        (["S" * 100], True),  # Max skill length = 100
        (["S" * 101], False),  # Skill above max
        (["Python", "S" * 101], False),  # One skill above max
    ],
)
def test_skills_length_boundaries(skills, should_pass):
    """Test skills list with max_length=100 per skill."""
    builder = FormBuilder().with_skills(skills)

    if should_pass:
        form = Form(**builder.build())
        assert form.skills == skills
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "skills" in str(exc_info.value)


# ========================================
# Enum Field Tests
# ========================================


@pytest.mark.parametrize(
    "study_year,is_student,should_pass",
    [
        (1, True, True),  # Valid year 1
        (7, True, True),  # Valid year 7 (graduated)
        (0, True, False),  # Below min
        (8, True, False),  # Above max
        (None, False, True),  # None for non-student
    ],
)
def test_study_year_enum_boundaries(study_year, is_student, should_pass):
    """Test StudyYear enum values (1-7)."""
    builder = FormBuilder()
    if is_student:
        builder = builder.as_student(university_id=1, study_year=study_year)
    else:
        builder = builder.as_non_student()

    if should_pass:
        form = Form(**builder.build())
        assert form.study_year == study_year
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "study_year" in str(exc_info.value)


@pytest.mark.parametrize(
    "format,should_pass",
    [
        ("online", True),
        ("offline", True),
        ("hybrid", False),  # Invalid
        ("", False),  # Empty
        ("ONLINE", False),  # Wrong case
    ],
)
def test_format_enum_validation(format, should_pass):
    """Test ParticipationFormat enum validation."""
    builder = FormBuilder().with_format(format)

    if should_pass:
        form = Form(**builder.build())
        assert form.format == format
    else:
        with pytest.raises(ValidationError) as exc_info:
            Form(**builder.build())
        assert "format" in str(exc_info.value)


# ========================================
# Cross-Field Validation Tests
# ========================================


def test_wants_job_requires_cv():
    """wants_job=True requires non-empty cv URL."""
    builder = FormBuilder().with_field("wants_job", True).with_field("cv", "")

    with pytest.raises(ValidationError, match="надайте посилання на CV"):
        Form(**builder.build())


def test_wants_job_with_valid_cv_succeeds():
    """wants_job=True with valid cv should succeed."""
    builder = FormBuilder().seeking_job("https://example.com/cv.pdf")
    form = Form(**builder.build())
    assert form.wants_job is True
    assert form.cv == "https://example.com/cv.pdf"


def test_cv_without_work_consent_fails():
    """CV provided without work_consent should fail."""
    builder = FormBuilder().with_cv("https://example.com/cv.pdf", work_consent=False)

    with pytest.raises(ValidationError, match="згоду на обробку даних"):
        Form(**builder.build())


def test_linkedin_without_work_consent_fails():
    """LinkedIn provided without work_consent should fail."""
    builder = FormBuilder().with_linkedin(
        "https://linkedin.com/in/user", work_consent=False
    )

    with pytest.raises(ValidationError, match="згоду на обробку даних"):
        Form(**builder.build())


def test_cv_and_linkedin_with_work_consent_succeeds():
    """CV and LinkedIn with work_consent should succeed."""
    builder = (
        FormBuilder()
        .with_cv("https://example.com/cv.pdf", work_consent=True)
        .with_linkedin("https://linkedin.com/in/user", work_consent=True)
    )
    form = Form(**builder.build())
    assert form.cv == "https://example.com/cv.pdf"
    assert form.linkedin == "https://linkedin.com/in/user"
    assert form.work_consent is True


@pytest.mark.parametrize(
    "cv_url", ["ftp://example.com/cv.pdf", "//invalid", "mailto:user@example.com"]
)
def test_invalid_cv_url_scheme_fails(cv_url):
    """CV with invalid URL scheme should fail."""
    builder = FormBuilder().seeking_job(cv_url)

    with pytest.raises(ValidationError, match="http:// або https://"):
        Form(**builder.build())


@pytest.mark.parametrize(
    "linkedin_url", ["ftp://x.com", "//invalid", "ssh://linkedin.com"]
)
def test_invalid_linkedin_url_scheme_fails(linkedin_url):
    """LinkedIn with invalid URL scheme should fail."""
    builder = FormBuilder().with_linkedin(linkedin_url, work_consent=True)

    with pytest.raises(ValidationError, match="http:// або https://"):
        Form(**builder.build())


@pytest.mark.parametrize(
    "source,other_source,should_pass",
    [
        ("other", "Friend", True),
        ("other", None, False),
        ("other", "", False),
        ("otherSocial", "Reddit", True),
        ("otherSocial", None, False),
        ("facebook", None, True),  # Not "other" or "otherSocial"
    ],
)
def test_source_other_requires_other_source(source, other_source, should_pass):
    """source='other'/'otherSocial' requires otherSource."""
    builder = FormBuilder().with_source(source, other_source)

    if should_pass:
        form = Form(**builder.build())
        assert form.source == source
        assert form.otherSource == other_source
    else:
        with pytest.raises(ValidationError, match="вкажіть джерело"):
            Form(**builder.build())


def test_is_student_requires_university_id():
    """is_student=True requires university_id."""
    builder = (
        FormBuilder()
        .with_field("is_student", True)
        .with_field("university_id", None)
        .with_field("study_year", 3)
    )

    with pytest.raises(ValidationError, match="вкажіть ваш університет"):
        Form(**builder.build())


def test_is_student_requires_study_year():
    """is_student=True requires study_year."""
    builder = (
        FormBuilder()
        .with_field("is_student", True)
        .with_field("university_id", 1)
        .with_field("study_year", None)
    )

    with pytest.raises(ValidationError, match="вкажіть ваш курс"):
        Form(**builder.build())


def test_is_student_with_both_fields_succeeds():
    """is_student=True with university_id and study_year should succeed."""
    builder = FormBuilder().as_student(university_id=1, study_year=3)
    form = Form(**builder.build())
    assert form.is_student is True
    assert form.university_id == 1
    assert form.study_year == 3


def test_non_student_without_university_succeeds():
    """is_student=False without university_id/study_year should succeed."""
    builder = FormBuilder().as_non_student()
    form = Form(**builder.build())
    assert form.is_student is False
    assert form.university_id is None
    assert form.study_year is None


def test_non_student_with_university_allowed():
    """is_student=False with university_id provided (edge case)."""
    # This tests whether the model allows university_id for non-students
    # Adjust expectation based on actual business rules
    builder = (
        FormBuilder()
        .with_field("is_student", False)
        .with_field("university_id", 1)
        .with_field("study_year", None)
    )
    # Expected: should pass (no validation preventing this)
    form = Form(**builder.build())
    assert form.is_student is False
    assert form.university_id == 1


# ========================================
# Personal Data Consent Tests
# ========================================


def test_personal_data_consent_must_be_true():
    """personal_data_consent must be Literal[True]."""
    builder = FormBuilder().with_personal_data_consent(False)

    with pytest.raises(ValidationError) as exc_info:
        Form(**builder.build())
    assert "personal_data_consent" in str(exc_info.value)


def test_personal_data_consent_none_fails():
    """personal_data_consent=None should fail."""
    builder = FormBuilder().with_field("personal_data_consent", None)

    with pytest.raises(ValidationError) as exc_info:
        Form(**builder.build())
    assert "personal_data_consent" in str(exc_info.value)


def test_personal_data_consent_true_succeeds():
    """personal_data_consent=True should succeed."""
    builder = FormBuilder().with_personal_data_consent(True)
    form = Form(**builder.build())
    assert form.personal_data_consent is True


# ========================================
# String Stripping Tests
# ========================================


def test_string_fields_are_stripped():
    """String fields should have whitespace stripped (str_strip_whitespace=True)."""
    builder = (
        FormBuilder()
        .with_full_name("  Test User  ")
        .with_email("  test@example.com  ")
        .with_telegram("  @user  ")
    )
    form = Form(**builder.build())
    assert form.full_name == "Test User"
    assert form.email == "test@example.com"
    assert form.telegram == "@user"


# ========================================
# Edge Cases
# ========================================


def test_maximum_length_all_fields():
    """Form with all fields at maximum length should succeed."""
    builder = (
        FormBuilder()
        .with_full_name("A" * 100)
        .with_email("e" * 88 + "@example.com")  # 88 + 12 = 100 chars
        .with_telegram("t" * 100)
        .with_team("T" * 100, is_leader=True)
        .with_field("job_description", "D" * 2000)
        .with_source("s" * 100, None)
        .with_comment("C" * 2000)
        .with_skills(["S" * 100])
    )
    form = Form(**builder.build())
    assert len(form.full_name) == 100
    assert len(form.telegram) == 100


def test_empty_optional_strings():
    """Empty strings for optional fields should be allowed."""
    builder = (
        FormBuilder()
        .with_field("cv", "")
        .with_field("linkedin", "")
        .with_field("job_description", "")
        .with_comment("")
    )
    form = Form(**builder.build())
    assert form.cv == ""
    assert form.linkedin == ""
    assert form.job_description == ""
    assert form.comment == ""
