"""API form validation tests.

Tests form submission endpoint with invalid inputs,
verifying proper error handling and Ukrainian error messages.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.builders import FormBuilder


# ========================================
# Form Validation - Field Errors
# ========================================


@pytest.mark.asyncio
async def test_submit_form_missing_required_fields(client: AsyncClient):
    """Missing required fields should return 422 validation error."""
    # Send incomplete payload
    payload = {"email": "test@example.com"}

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    # Verify error details include missing fields
    errors = response.json()
    assert "detail" in errors


@pytest.mark.asyncio
async def test_submit_form_invalid_email_format(client: AsyncClient):
    """Invalid email format should return validation error."""
    payload = FormBuilder().with_email("not-an-email").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    # Detail is now a string from custom error handler
    detail_str = str(errors.get("detail", ""))
    assert "email" in detail_str.lower()


@pytest.mark.asyncio
async def test_submit_form_string_too_long(client: AsyncClient):
    """String exceeding max_length should return validation error."""
    payload = FormBuilder().with_full_name("A" * 101).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_form_invalid_phone_number(client: AsyncClient):
    """Invalid phone number should return validation error."""
    payload = FormBuilder().with_phone("invalid-phone").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_form_invalid_enum_value(client: AsyncClient):
    """Invalid enum value for format should return validation error."""
    payload = FormBuilder().with_format("hybrid").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422


# ========================================
# Foreign Key Validation
# ========================================


@pytest.mark.asyncio
async def test_submit_form_nonexistent_university_id(
    client: AsyncClient, session: AsyncSession
):
    """Non-existent university_id should return 400 error."""
    payload = FormBuilder().as_student(university_id=99999, study_year=3).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    assert "університет" in error["detail"].lower()


@pytest.mark.asyncio
async def test_submit_form_nonexistent_category_id(
    client: AsyncClient, session: AsyncSession
):
    """Non-existent category_id should return 400 error."""
    payload = FormBuilder().with_category(99999).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    assert "категор" in error["detail"].lower()


# ========================================
# Duplicate User Detection
# ========================================


@pytest.mark.asyncio
async def test_submit_form_duplicate_email(
    client: AsyncClient, category_factory, session: AsyncSession
):
    """Duplicate email should return 400 error."""
    await category_factory()

    # First submission
    payload1 = FormBuilder().with_email("duplicate@example.com").build()
    response1 = await client.post("/form/", json=payload1)
    assert response1.status_code == 200

    # Second submission with same email
    payload2 = (
        FormBuilder()
        .with_email("duplicate@example.com")
        .with_telegram("@different")
        .build()
    )
    response2 = await client.post("/form/", json=payload2)
    assert response2.status_code == 400

    error = response2.json()
    assert "email" in error["detail"].lower()


@pytest.mark.asyncio
async def test_submit_form_duplicate_telegram(
    client: AsyncClient, category_factory, session: AsyncSession
):
    """Duplicate telegram handle should return 400 error."""
    await category_factory()

    # First submission
    payload1 = FormBuilder().with_telegram("@duplicate").build()
    response1 = await client.post("/form/", json=payload1)
    assert response1.status_code == 200

    # Second submission with same telegram
    payload2 = (
        FormBuilder()
        .with_telegram("@duplicate")
        .with_email("different@example.com")
        .build()
    )
    response2 = await client.post("/form/", json=payload2)
    assert response2.status_code == 400

    error = response2.json()
    assert "telegram" in error["detail"].lower()


# ========================================
# Team Creation/Joining Validation
# ========================================


@pytest.mark.asyncio
async def test_submit_form_has_team_without_team_name(
    client: AsyncClient, category_factory
):
    """has_team=True without team_name should return 400 error."""
    await category_factory()

    payload = (
        FormBuilder().with_field("has_team", True).with_field("team_name", "").build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    assert "назву команди" in error["detail"].lower()


@pytest.mark.asyncio
async def test_submit_form_create_team_without_leader(
    client: AsyncClient, category_factory
):
    """Creating team without team_leader=True should return 400 error."""
    await category_factory()

    payload = FormBuilder().with_team("NewTeam", is_leader=False).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    assert "тімлід" in error["detail"].lower()


@pytest.mark.asyncio
async def test_submit_form_team_same_name_different_category_fails(
    client: AsyncClient, category_factory, team_factory
):
    """Trying to join a team that doesn't exist in your category should fail."""
    cat1 = await category_factory()
    cat2 = await category_factory(name="Category 2")

    # Create team in category 1
    await team_factory(team_name="TeamName", category_id=cat1.id)

    # Try to join team with same name but different category (team doesn't exist in cat2)
    payload = (
        FormBuilder()
        .with_category(cat2.id)
        .with_team("TeamName", is_leader=False)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Should fail because team doesn't exist in cat2 and user is not a leader
    assert "тімлід" in error["detail"].lower()


@pytest.mark.asyncio
async def test_submit_form_join_existing_team_forces_non_leader(
    client: AsyncClient, category_factory, team_factory
):
    """Joining existing team should force team_leader=False."""
    category = await category_factory()
    await team_factory(category_id=category.id, team_name="ExistingTeam")

    # Try to join as leader
    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_team("ExistingTeam", is_leader=True)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200

    # Verify success message indicates joining, not creating
    result = response.json()
    assert "приєдналися" in result["message"].lower()


# ========================================
# Cross-Field Validation at API Level
# ========================================


@pytest.mark.asyncio
async def test_submit_form_wants_job_without_cv(client: AsyncClient, category_factory):
    """wants_job=True without cv should return validation error."""
    await category_factory()

    payload = FormBuilder().with_field("wants_job", True).with_field("cv", "").build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422  # Pydantic validation

    errors = response.json()
    assert "cv" in str(errors).lower()


@pytest.mark.asyncio
async def test_submit_form_cv_without_work_consent(
    client: AsyncClient, category_factory
):
    """CV provided without work_consent should return validation error."""
    await category_factory()

    payload = (
        FormBuilder().with_cv("https://example.com/cv.pdf", work_consent=False).build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 422

    errors = response.json()
    assert "згод" in str(errors).lower()


@pytest.mark.asyncio
async def test_submit_form_is_student_without_university(
    client: AsyncClient, category_factory
):
    """is_student=True without university_id should return validation error."""
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
    assert "університет" in str(errors).lower()


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_submit_form_non_student_registration(
    client: AsyncClient, category_factory
):
    """Non-student registration should succeed without university."""
    await category_factory()

    payload = FormBuilder().as_non_student().build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_form_empty_skills_list(client: AsyncClient, category_factory):
    """Empty skills list should be accepted."""
    await category_factory()

    payload = FormBuilder().with_skills([]).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_form_max_length_strings(client: AsyncClient, category_factory):
    """Form with maximum-length strings should succeed."""
    await category_factory()

    payload = (
        FormBuilder()
        .with_full_name("A" * 100)
        .with_telegram("t" * 100)
        .with_team("T" * 100, is_leader=True)
        .with_field("job_description", "D" * 2000)
        .with_source("s" * 100)
        .with_comment("C" * 2000)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_form_unicode_team_name(client: AsyncClient, category_factory):
    """Team name with unicode/emoji should be accepted."""
    await category_factory()

    payload = FormBuilder().with_team("Команда 🚀", is_leader=True).build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200
