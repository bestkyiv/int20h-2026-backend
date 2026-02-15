"""Team creation and concurrency tests.

Tests team-related workflows, business rules, and concurrency scenarios.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.db.models import Team, Participant
from tests.builders import FormBuilder


# ========================================
# Team Creation Tests
# ========================================


@pytest.mark.asyncio
async def test_create_team_as_leader(
    client: AsyncClient, session: AsyncSession, category_factory
):
    """Team leader can create new team."""
    category = await category_factory()

    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_team("NewTeam", is_leader=True)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "створили" in result["message"].lower()

    # Verify team created in DB
    stmt = select(Team).where(Team.team_name == "NewTeam")
    db_result = await session.execute(stmt)
    team = db_result.scalars().first()

    assert team is not None
    assert team.team_name == "NewTeam"
    assert team.category_id == category.id


@pytest.mark.asyncio
async def test_join_existing_team(
    client: AsyncClient, session: AsyncSession, category_factory, team_factory
):
    """Non-leader can join existing team."""
    category = await category_factory()
    team = await team_factory(team_name="ExistingTeam", category_id=category.id)

    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_team("ExistingTeam", is_leader=False)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "приєдналися" in result["message"].lower()

    # Verify participant joined team
    stmt = select(Participant).where(Participant.email == "test@example.com")
    db_result = await session.execute(stmt)
    participant = db_result.scalars().first()

    assert participant is not None
    assert participant.team_id == team.id
    assert participant.team_leader is False


@pytest.mark.asyncio
async def test_leader_joining_existing_team_forced_non_leader(
    client: AsyncClient, session: AsyncSession, category_factory, team_factory
):
    """Leader attempting to join existing team is forced to non-leader."""
    category = await category_factory()
    await team_factory(team_name="TeamA", category_id=category.id)

    payload = (
        FormBuilder()
        .with_category(category.id)
        .with_team("TeamA", is_leader=True)  # Try to join as leader
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200

    # Should join as non-leader
    stmt = select(Participant).where(Participant.email == "test@example.com")
    db_result = await session.execute(stmt)
    participant = db_result.scalars().first()

    assert participant is not None
    assert participant.team_leader is False


@pytest.mark.asyncio
async def test_multiple_members_join_same_team(
    client: AsyncClient, session: AsyncSession, category_factory, team_factory
):
    """Multiple participants can join the same team."""
    category = await category_factory()
    team = await team_factory(team_name="PopularTeam", category_id=category.id)

    # Member 1
    payload1 = (
        FormBuilder()
        .with_email("member1@example.com")
        .with_telegram("@member1")
        .with_category(category.id)
        .with_team("PopularTeam", is_leader=False)
        .build()
    )
    r1 = await client.post("/form/", json=payload1)
    assert r1.status_code == 200

    # Member 2
    payload2 = (
        FormBuilder()
        .with_email("member2@example.com")
        .with_telegram("@member2")
        .with_category(category.id)
        .with_team("PopularTeam", is_leader=False)
        .build()
    )
    r2 = await client.post("/form/", json=payload2)
    assert r2.status_code == 200

    # Member 3
    payload3 = (
        FormBuilder()
        .with_email("member3@example.com")
        .with_telegram("@member3")
        .with_category(category.id)
        .with_team("PopularTeam", is_leader=False)
        .build()
    )
    r3 = await client.post("/form/", json=payload3)
    assert r3.status_code == 200

    # Verify all joined team
    stmt = select(Participant).where(Participant.team_id == team.id)
    db_result = await session.execute(stmt)
    members = db_result.scalars().all()

    assert len(members) == 3


@pytest.mark.asyncio
async def test_same_team_name_different_categories_allowed(
    client: AsyncClient, session: AsyncSession, category_factory
):
    """Same team name in different categories should be allowed."""
    cat1 = await category_factory(name="Backend")
    cat2 = await category_factory(name="Frontend")

    # Create team in category 1
    payload1 = (
        FormBuilder()
        .with_email("leader1@example.com")
        .with_telegram("@leader1")
        .with_category(cat1.id)
        .with_team("TeamName", is_leader=True)
        .build()
    )
    r1 = await client.post("/form/", json=payload1)
    assert r1.status_code == 200

    # Create team with same name in category 2
    payload2 = (
        FormBuilder()
        .with_email("leader2@example.com")
        .with_telegram("@leader2")
        .with_category(cat2.id)
        .with_team("TeamName", is_leader=True)
        .build()
    )
    r2 = await client.post("/form/", json=payload2)
    assert r2.status_code == 200

    # Verify both teams exist
    stmt = select(Team).where(Team.team_name == "TeamName")
    db_result = await session.execute(stmt)
    teams = db_result.scalars().all()

    assert len(teams) == 2
    assert {t.category_id for t in teams} == {cat1.id, cat2.id}


# ========================================
# Team Validation Tests
# ========================================


@pytest.mark.asyncio
async def test_team_different_category_error(
    client: AsyncClient, session: AsyncSession, category_factory, team_factory
):
    """Trying to join a team that doesn't exist in your category should fail."""
    cat1 = await category_factory(name="Backend")
    cat2 = await category_factory(name="Frontend")

    # Create team in category 1
    await team_factory(team_name="BackendTeam", category_id=cat1.id)

    # Try to join from category 2 (team doesn't exist in cat2)
    payload = (
        FormBuilder()
        .with_category(cat2.id)
        .with_team("BackendTeam", is_leader=False)
        .build()
    )

    response = await client.post("/form/", json=payload)
    assert response.status_code == 400

    error = response.json()
    # Should fail because team doesn't exist in cat2 and user is not a leader
    assert "тімлід" in error["detail"].lower()


# ========================================
# Concurrency/Race Condition Tests
# ========================================


@pytest.mark.asyncio
async def test_concurrent_team_creation_same_name_category(
    client: AsyncClient, session: AsyncSession, category_factory
):
    """Concurrent team creation with same name+category should handle gracefully."""
    category = await category_factory()

    # Simulate two leaders trying to create same team
    # In real concurrency, one would get IntegrityError
    # Here we test sequential behavior

    payload1 = (
        FormBuilder()
        .with_email("leader1@example.com")
        .with_telegram("@leader1")
        .with_category(category.id)
        .with_team("RaceTeam", is_leader=True)
        .build()
    )

    payload2 = (
        FormBuilder()
        .with_email("leader2@example.com")
        .with_telegram("@leader2")
        .with_category(category.id)
        .with_team("RaceTeam", is_leader=True)
        .build()
    )

    # First creation succeeds
    r1 = await client.post("/form/", json=payload1)
    assert r1.status_code == 200

    # Second attempt joins as member (existing team found)
    r2 = await client.post("/form/", json=payload2)
    assert r2.status_code == 200

    result2 = r2.json()
    # Second leader would join existing team
    assert "приєдналися" in result2["message"].lower()


@pytest.mark.asyncio
async def test_concurrent_duplicate_email_handled(
    client: AsyncClient, session: AsyncSession, category_factory
):
    """Concurrent submissions with duplicate email should be caught."""
    category = await category_factory()

    payload = (
        FormBuilder().with_email("race@example.com").with_category(category.id).build()
    )

    # First submission
    r1 = await client.post("/form/", json=payload)
    assert r1.status_code == 200

    # Second submission (simulated race)
    # Change telegram to pass initial validation
    payload["telegram"] = "@different"
    r2 = await client.post("/form/", json=payload)

    # Should catch duplicate email
    assert r2.status_code == 400
    assert "email" in r2.json()["detail"].lower()


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_team_with_no_members_allowed(
    session: AsyncSession, category_factory, team_factory
):
    """Team can exist without members (created but no one joined)."""
    category = await category_factory()
    team = await team_factory(team_name="EmptyTeam", category_id=category.id)

    # Verify team exists with no members
    stmt = select(Participant).where(Participant.team_id == team.id)
    db_result = await session.execute(stmt)
    members = db_result.scalars().all()

    assert len(members) == 0


@pytest.mark.asyncio
async def test_participant_without_team_allowed(
    client: AsyncClient, session: AsyncSession, category_factory
):
    """Participant without team should be allowed."""
    category = await category_factory()

    payload = FormBuilder().with_category(category.id).without_team().build()

    response = await client.post("/form/", json=payload)
    assert response.status_code == 200

    # Verify participant has no team
    stmt = select(Participant).where(Participant.email == "test@example.com")
    db_result = await session.execute(stmt)
    participant = db_result.scalars().first()

    assert participant is not None
    assert participant.team_id is None
    assert participant.team_leader is False
