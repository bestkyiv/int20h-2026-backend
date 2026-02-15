import pytest
from sqlmodel import select
from src.db import models as db_models


@pytest.mark.asyncio
async def test_team_create_and_join_workflow(
    client, session, category_factory, university_factory
):
    cat = await category_factory(name="Cat Workflow")
    uni = await university_factory(name="Uni Workflow")

    leader_payload = {
        "full_name": "Leader One",
        "email": "leader@example.com",
        "telegram": "@leader_1",
        "phone": "+380501234569",
        "is_student": True,
        "university_id": uni.id,
        "study_year": 2,
        "category_id": cat.id,
        "skills": ["Python"],
        "format": "online",
        "has_team": True,
        "team_leader": True,
        "team_name": "Awesome Team",
        "wants_job": False,
        "job_description": "",
        "cv": "",
        "linkedin": "",
        "work_consent": False,
        "source": "web",
        "otherSource": None,
        "comment": None,
        "personal_data_consent": True,
    }

    r1 = await client.post("/form/", json=leader_payload)
    assert r1.status_code == 200
    assert (
        "створили команду" in r1.json()["message"] or "створили" in r1.json()["message"]
    )

    member_payload = leader_payload.copy()
    member_payload.update(
        {
            "full_name": "Member Two",
            "email": "member@example.com",
            "telegram": "@member_2",
            "team_leader": False,
        }
    )

    r2 = await client.post("/form/", json=member_payload)
    assert r2.status_code == 200
    assert (
        "приєдналися до команди" in r2.json()["message"]
        or "приєдналися" in r2.json()["message"]
    )

    # verify DB: one team with two members
    stmt = select(db_models.Team).where(db_models.Team.team_name == "Awesome Team")
    q = await session.execute(stmt)
    team = q.scalars().first()
    assert team is not None

    # refresh team members
    stmt_m = select(db_models.Participant).where(
        db_models.Participant.team_id == team.id
    )
    q2 = await session.execute(stmt_m)
    members = q2.scalars().all()
    assert len(members) == 2
    assert any(m.team_leader for m in members)
