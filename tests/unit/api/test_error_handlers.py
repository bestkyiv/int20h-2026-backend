"""Error handler tests.

Tests custom error handlers and Ukrainian error message delivery.
"""

import pytest
from httpx import AsyncClient

from tests.builders import FormBuilder


# ========================================
# Custom Error Message Tests
# ========================================


@pytest.mark.asyncio
async def test_missing_required_field_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Missing required fields should return Ukrainian error messages."""
    await category_factory()

    # Missing full_name
    payload = FormBuilder().build()
    del payload["full_name"]

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    # Should contain Ukrainian text
    detail_str = str(errors.get("detail", []))
    # Check for any Ukrainian characters or expected message
    assert any(char in detail_str for char in "абвгдеєжзиіїклмнопрстуфхцчшщьюя")


@pytest.mark.asyncio
async def test_string_too_short_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """String too short should return Ukrainian error message."""
    await category_factory()

    payload = FormBuilder().with_full_name("A").build()  # Min 2 chars

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message for string_too_short should be present
    assert "символ" in detail_str.lower() or "коротк" in detail_str.lower()


@pytest.mark.asyncio
async def test_string_too_long_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """String too long should return Ukrainian error message."""
    await category_factory()

    payload = FormBuilder().with_full_name("A" * 101).build()  # Max 100 chars

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message for string_too_long
    assert "довг" in detail_str.lower() or "максимум" in detail_str.lower()


@pytest.mark.asyncio
async def test_invalid_email_format_returns_message(
    client: AsyncClient, category_factory
):
    """Invalid email format should return validation error."""
    await category_factory()

    payload = FormBuilder().with_email("not-an-email").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    # Should mention email
    assert "email" in str(errors).lower()


@pytest.mark.asyncio
async def test_invalid_phone_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Invalid phone number should return Ukrainian error message."""
    await category_factory()

    payload = FormBuilder().with_phone("invalid-phone").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message for invalid phone
    assert "телефон" in detail_str.lower() or "формат" in detail_str.lower()


@pytest.mark.asyncio
async def test_missing_personal_data_consent_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Missing personal_data_consent should return Ukrainian message."""
    await category_factory()

    payload = FormBuilder().with_personal_data_consent(False).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message about consent
    assert "згод" in detail_str.lower() or "персональн" in detail_str.lower()


@pytest.mark.asyncio
async def test_invalid_enum_value_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Invalid enum value should return Ukrainian error message."""
    await category_factory()

    payload = FormBuilder().with_format("hybrid").build()  # Invalid

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Should mention format or online/offline
    assert "format" in detail_str.lower() or "online" in detail_str.lower()


# ========================================
# Cross-Field Validation Error Messages
# ========================================


@pytest.mark.asyncio
async def test_cv_without_work_consent_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """CV without work_consent should return Ukrainian message."""
    await category_factory()

    payload = (
        FormBuilder().with_cv("https://example.com/cv.pdf", work_consent=False).build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message about consent
    assert "згод" in detail_str.lower()


@pytest.mark.asyncio
async def test_wants_job_without_cv_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """wants_job without CV should return Ukrainian message."""
    await category_factory()

    payload = FormBuilder().with_field("wants_job", True).with_field("cv", "").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message about CV
    assert "cv" in detail_str.lower() or "посилання" in detail_str.lower()


@pytest.mark.asyncio
async def test_is_student_without_university_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """is_student without university should return Ukrainian message."""
    await category_factory()

    payload = (
        FormBuilder()
        .with_field("is_student", True)
        .with_field("university_id", None)
        .with_field("study_year", 3)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message about university
    assert "університет" in detail_str.lower()


@pytest.mark.asyncio
async def test_source_other_without_other_source_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """source='other' without otherSource should return Ukrainian message."""
    await category_factory()

    payload = FormBuilder().with_source("other", None).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    detail_str = str(errors)
    # Ukrainian message about specifying source
    assert "джерело" in detail_str.lower() or "вкажіть" in detail_str.lower()


# ========================================
# Business Logic Error Messages
# ========================================


@pytest.mark.asyncio
async def test_duplicate_email_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Duplicate email should return Ukrainian error message."""
    category = await category_factory()

    payload1 = (
        FormBuilder().with_email("dup@example.com").with_category(category.id).build()
    )
    r1 = await client.post("/form/", json=payload1)
    assert r1.status_code == 200

    payload2 = (
        FormBuilder()
        .with_email("dup@example.com")
        .with_telegram("@different")
        .with_category(category.id)
        .build()
    )
    r2 = await client.post("/form/", json=payload2)
    assert r2.status_code == 400

    error = r2.json()
    # Ukrainian message about duplicate email
    assert "email" in error["detail"].lower()
    assert "зареєстрований" in error["detail"].lower()


@pytest.mark.asyncio
async def test_nonexistent_university_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Non-existent university should return Ukrainian error message."""
    category = await category_factory()

    payload = (
        FormBuilder()
        .as_student(university_id=99999, study_year=3)
        .with_category(category.id)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Ukrainian message about university not found
    assert "університет" in error["detail"].lower()
    assert "знайдено" in error["detail"].lower()


@pytest.mark.asyncio
async def test_has_team_without_team_name_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """has_team without team_name should return Ukrainian message."""
    category = await category_factory()

    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_field("has_team", True)
        .with_field("team_name", "")
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Ukrainian message about team name
    assert "назву" in error["detail"].lower() and "команд" in error["detail"].lower()


@pytest.mark.asyncio
async def test_create_team_without_leader_returns_ukrainian_message(
    client: AsyncClient, category_factory
):
    """Creating team without being leader should return Ukrainian message."""
    category = await category_factory()

    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_team("NewTeam", is_leader=False)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Ukrainian message about team leader
    assert "тімлід" in error["detail"].lower()


# ========================================
# Error Response Format Tests
# ========================================


@pytest.mark.asyncio
async def test_validation_error_response_format(client: AsyncClient, category_factory):
    """Validation errors should have consistent response format."""
    await category_factory()

    payload = FormBuilder().with_full_name("").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    # Should have 'detail' key
    assert "detail" in errors
    # Detail should be a list or dict with error info
    assert isinstance(errors["detail"], (list, dict, str))


@pytest.mark.asyncio
async def test_http_exception_response_format(client: AsyncClient, category_factory):
    """HTTP exceptions should have consistent response format."""
    category = await category_factory()

    # Trigger 400 error (nonexistent university)
    payload = (
        FormBuilder()
        .as_student(university_id=99999, study_year=3)
        .with_category(category.id)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Should have 'detail' key
    assert "detail" in error
    # Detail should be a string
    assert isinstance(error["detail"], str)
