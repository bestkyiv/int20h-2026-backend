from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

SQLModel.metadata.naming_convention = naming_convention


# 1. Use Enums for fixed choices to prevent typos ("Online" vs "online")
class ParticipationFormat(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


# 2. Inherit from SQLModel with table=True
class University(SQLModel, table=True):
    __tablename__ = "universities"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    city: Optional[str] = None

    # Relationships
    participants: List["Participant"] = Relationship(back_populates="university")


class Team(SQLModel, table=True):
    __tablename__ = "teams"  # type: ignore
    __table_args__ = (
        UniqueConstraint("team_name", "category_id", name="uix_team_name_category"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str = Field(index=True)

    category_id: int = Field(foreign_key="categories.id", index=True)

    members: List["Participant"] = Relationship(back_populates="team")


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class Participant(SQLModel, table=True):
    __tablename__ = "participants"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)

    # Personal / Contact
    full_name: str = Field(index=True)
    email: str = Field(unique=True)
    telegram: str = Field(unique=True)
    phone: str

    is_student: bool
    study_year: Optional[int] = None

    # University Reference
    university_id: Optional[int] = Field(foreign_key="universities.id", default=None)
    university: Optional[University] = Relationship(back_populates="participants")

    # Hackathon Logic
    category_id: int = Field(foreign_key="categories.id")
    participation_format: ParticipationFormat

    team_leader: bool = Field(default=False)
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id")
    team: Optional[Team] = Relationship(back_populates="members")

    # Work / Career
    wants_job: bool
    job_description: Optional[str] = None
    cv_url: Optional[str] = None
    linkedin: Optional[str] = None
    work_consent: bool

    # Meta
    source: str
    comment: Optional[str] = None

    # Legal
    personal_data_consent: bool

    # Skills
    skills_text: Optional[str] = None
