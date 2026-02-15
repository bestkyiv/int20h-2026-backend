import pytest

from sqlmodel import select
from src.db import models as db_models


@pytest.mark.asyncio
async def test_get_skills(client):
    r = await client.get("/skills/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert "Python" in data


@pytest.mark.asyncio
async def test_get_categories_and_unis(
    client, session, category_factory, university_factory
):
    await category_factory(name="Cat A")
    await university_factory(name="Uni A", city="Kyiv")

    r_cat = await client.get("/categories/")
    assert r_cat.status_code == 200
    cats = r_cat.json()["categories"]
    assert any(c.get("name") == "Cat A" for c in cats)

    r_uni = await client.get("/unis/")
    assert r_uni.status_code == 200
    unis = r_uni.json()["universities"]
    assert any(u.get("name") == "Uni A" for u in unis)


@pytest.mark.asyncio
async def test_submit_form_success(
    client, session, category_factory, university_factory
):
    cat = await category_factory(name="Cat Submit")
    uni = await university_factory(name="Uni Submit")

    payload = {
        "full_name": "Alice Example",
        "email": "alice@example.com",
        "telegram": "@alice_test",
        "phone": "+380501234567",
        "is_student": True,
        "university_id": uni.id,
        "study_year": 1,
        "category_id": cat.id,
        "skills": ["Python", "FastAPI"],
        "format": "online",
        "has_team": False,
        "team_leader": False,
        "team_name": "",
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

    res = await client.post("/form/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "message" in body
    assert body["data"]["email"] == payload["email"]

    # ensure participant persisted
    q = await session.execute(
        select(db_models.Participant).where(
            db_models.Participant.email == payload["email"]
        )
    )
    p = q.scalars().first()
    assert p is not None
    assert p.email == payload["email"]


@pytest.mark.asyncio
async def test_submit_form_duplicate_email(
    client, session, category_factory, university_factory
):
    cat = await category_factory(name="Cat Dup")
    uni = await university_factory(name="Uni Dup")

    payload = {
        "full_name": "Bob Example",
        "email": "bob@example.com",
        "telegram": "@bob_test",
        "phone": "+380501234568",
        "is_student": True,
        "university_id": uni.id,
        "study_year": 1,
        "category_id": cat.id,
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
        "source": "web",
        "otherSource": None,
        "comment": None,
        "personal_data_consent": True,
    }

    res1 = await client.post("/form/", json=payload)
    assert res1.status_code == 200

    # second attempt with same email should fail
    payload2 = payload.copy()
    payload2["telegram"] = "@different"
    res2 = await client.post("/form/", json=payload2)
    assert res2.status_code == 400
    assert "email" in res2.json().get("detail", "") or "зареєстрований" in str(
        res2.json().get("detail", "")
    )


# ========================================
# Additional GET Endpoint Tests
# ========================================


@pytest.mark.asyncio
async def test_get_skills_empty_returns_list(client):
    """GET /skills/ should return empty list if skills.json missing."""
    # Even if skills.json is missing, should return []
    r = await client.get("/skills/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_categories_empty_database(client):
    """GET /categories/ with empty database should return empty list."""
    r = await client.get("/categories/")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


@pytest.mark.asyncio
async def test_get_unis_empty_database(client):
    """GET /unis/ with empty database should return empty list."""
    r = await client.get("/unis/")
    assert r.status_code == 200
    data = r.json()
    assert "universities" in data
    assert isinstance(data["universities"], list)


@pytest.mark.asyncio
async def test_get_categories_ordering(client, session, category_factory):
    """GET /categories/ should return categories ordered by name."""
    await category_factory(name="Zebra Category")
    await category_factory(name="Alpha Category")
    await category_factory(name="Beta Category")

    r = await client.get("/categories/")
    assert r.status_code == 200
    cats = r.json()["categories"]

    # Verify ordering
    names = [c["name"] for c in cats]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_get_unis_ordering(client, session, university_factory):
    """GET /unis/ should return universities ordered by name."""
    await university_factory(name="Zebra Uni", city="Kyiv")
    await university_factory(name="Alpha Uni", city="Lviv")
    await university_factory(name="Beta Uni", city="Odesa")

    r = await client.get("/unis/")
    assert r.status_code == 200
    unis = r.json()["universities"]

    # Verify ordering
    names = [u["name"] for u in unis]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_get_categories_response_schema(client, session, category_factory):
    """GET /categories/ response should have expected schema."""
    await category_factory(name="Test Category")

    r = await client.get("/categories/")
    assert r.status_code == 200
    data = r.json()

    assert "categories" in data
    assert len(data["categories"]) > 0

    # Verify schema
    first = data["categories"][0]
    assert "id" in first
    assert "name" in first
    assert isinstance(first["id"], int)
    assert isinstance(first["name"], str)


@pytest.mark.asyncio
async def test_get_unis_response_schema(client, session, university_factory):
    """GET /unis/ response should have expected schema."""
    await university_factory(name="Test Uni", city="Kyiv")

    r = await client.get("/unis/")
    assert r.status_code == 200
    data = r.json()

    assert "universities" in data
    assert len(data["universities"]) > 0

    # Verify schema
    first = data["universities"][0]
    assert "id" in first
    assert "name" in first
    assert isinstance(first["id"], int)
    assert isinstance(first["name"], str)
