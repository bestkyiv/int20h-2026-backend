"""Database constraint and model tests.

Tests database-level constraints including unique constraints,
foreign keys, defaults, and nullability.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Participant, Team, University, Category, ParticipationFormat


# ========================================
# Unique Constraint Tests
# ========================================


@pytest.mark.asyncio
async def test_university_name_unique_constraint(session: AsyncSession):
    """Duplicate university names should violate unique constraint."""
    uni1 = University(name="KPI", city="Kyiv")
    session.add(uni1)
    await session.commit()

    # Try to add another with same name
    uni2 = University(name="KPI", city="Lviv")
    session.add(uni2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_category_name_unique_constraint(session: AsyncSession):
    """Duplicate category names should violate unique constraint."""
    cat1 = Category(name="Backend")
    session.add(cat1)
    await session.commit()

    # Try to add another with same name
    cat2 = Category(name="Backend")
    session.add(cat2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_participant_email_unique_constraint(
    session: AsyncSession, category_factory
):
    """Duplicate participant emails should violate unique constraint."""
    category = await category_factory()

    p1 = Participant(
        full_name="User 1",
        email="same@example.com",
        telegram="@user1",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p1)
    await session.commit()

    # Try to add another with same email
    p2 = Participant(
        full_name="User 2",
        email="same@example.com",  # Duplicate
        telegram="@user2",
        phone="+380501234568",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_participant_telegram_unique_constraint(
    session: AsyncSession, category_factory
):
    """Duplicate participant telegram handles should violate unique constraint."""
    category = await category_factory()

    p1 = Participant(
        full_name="User 1",
        email="user1@example.com",
        telegram="@samehandle",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p1)
    await session.commit()

    # Try to add another with same telegram
    p2 = Participant(
        full_name="User 2",
        email="user2@example.com",
        telegram="@samehandle",  # Duplicate
        phone="+380501234568",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_team_composite_unique_constraint(
    session: AsyncSession, category_factory
):
    """Duplicate team (name + category_id) should violate unique constraint."""
    cat1 = await category_factory(name="Backend")

    team1 = Team(team_name="TeamName", category_id=cat1.id)
    session.add(team1)
    await session.commit()

    # Try to add another with same name and category
    team2 = Team(team_name="TeamName", category_id=cat1.id)
    session.add(team2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_team_same_name_different_category_allowed(
    session: AsyncSession, category_factory
):
    """Same team name in different categories should be allowed."""
    cat1 = await category_factory(name="Backend")
    cat2 = await category_factory(name="Frontend")

    team1 = Team(team_name="TeamName", category_id=cat1.id)
    session.add(team1)
    await session.commit()

    # Add team with same name but different category
    team2 = Team(team_name="TeamName", category_id=cat2.id)
    session.add(team2)
    await session.commit()  # Should succeed

    assert team1.team_name == team2.team_name
    assert team1.category_id != team2.category_id


# ========================================
# Foreign Key Constraint Tests
# ========================================


@pytest.mark.asyncio
async def test_participant_invalid_category_fk(session: AsyncSession):
    """Participant with non-existent category_id should fail."""
    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        category_id=99999,  # Non-existent
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_participant_invalid_university_fk(
    session: AsyncSession, category_factory
):
    """Participant with non-existent university_id should fail."""
    category = await category_factory()

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=True,
        study_year=3,
        university_id=99999,  # Non-existent
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_participant_null_university_allowed_for_non_student(
    session: AsyncSession, category_factory
):
    """Participant with university_id=None should be allowed."""
    category = await category_factory()

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        university_id=None,
        study_year=None,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()  # Should succeed

    assert p.university_id is None
    assert p.study_year is None


@pytest.mark.asyncio
async def test_team_invalid_category_fk(session: AsyncSession):
    """Team with non-existent category_id should fail."""
    team = Team(team_name="Team", category_id=99999)
    session.add(team)

    with pytest.raises(IntegrityError):
        await session.commit()


# ========================================
# Relationship/Cascade Tests
# ========================================


@pytest.mark.asyncio
async def test_delete_team_participants_remain(
    session: AsyncSession, category_factory, team_factory
):
    """Deleting team should not cascade delete participants."""
    category = await category_factory()
    team = await team_factory(category_id=category.id)

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        team_id=team.id,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()

    participant_id = p.id

    # Delete team
    await session.delete(team)
    await session.commit()

    # Participant should still exist with team_id=None
    result = await session.get(Participant, participant_id)
    assert result is not None
    assert result.team_id is None


# ========================================
# Default Values Tests
# ========================================


@pytest.mark.asyncio
async def test_participant_team_leader_defaults_to_false(
    session: AsyncSession, category_factory
):
    """team_leader should default to False if not specified."""
    category = await category_factory()

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        # team_leader not specified
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()

    assert p.team_leader is False


# ========================================
# Enum Field Tests
# ========================================


@pytest.mark.asyncio
async def test_participation_format_enum_stored_correctly(
    session: AsyncSession, category_factory
):
    """ParticipationFormat enum should be stored as string."""
    category = await category_factory()

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.OFFLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()

    # Refresh from DB
    await session.refresh(p)
    assert p.participation_format == ParticipationFormat.OFFLINE


# ========================================
# Nullability Tests
# ========================================


@pytest.mark.asyncio
async def test_participant_optional_fields_can_be_null(
    session: AsyncSession, category_factory
):
    """Optional fields should accept None values."""
    category = await category_factory()

    p = Participant(
        full_name="User",
        email="user@example.com",
        telegram="@user",
        phone="+380501234567",
        is_student=False,
        university_id=None,
        study_year=None,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        team_id=None,
        wants_job=False,
        job_description=None,
        cv_url=None,
        linkedin=None,
        work_consent=False,
        source="test",
        comment=None,
        skills_text=None,
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()  # Should succeed

    assert p.university_id is None
    assert p.study_year is None
    assert p.comment is None


# ========================================
# Index Tests
# ========================================


@pytest.mark.asyncio
async def test_indexed_fields_can_be_queried_efficiently(
    session: AsyncSession, category_factory
):
    """Indexed fields (email, telegram) should support lookups."""
    category = await category_factory()

    p = Participant(
        full_name="Indexed User",
        email="indexed@example.com",
        telegram="@indexed",
        phone="+380501234567",
        is_student=False,
        category_id=category.id,
        participation_format=ParticipationFormat.ONLINE,
        team_leader=False,
        wants_job=False,
        work_consent=False,
        source="test",
        personal_data_consent=True,
    )
    session.add(p)
    await session.commit()

    # This test verifies the schema; actual performance testing would require
    # query plan analysis or large datasets
    from sqlmodel import select

    stmt = select(Participant).where(Participant.email == "indexed@example.com")
    result = await session.execute(stmt)
    found = result.scalars().first()

    assert found is not None
    assert found.email == "indexed@example.com"
