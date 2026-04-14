from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import (
    Column,
    Index,
    DateTime,
    BigInteger,
    Text,
    UniqueConstraint,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

SQLModel.metadata.naming_convention = naming_convention


def utc_now():
    return datetime.now(timezone.utc)


# 1. Use Enums for fixed choices to prevent typos ("Online" vs "online")
class ParticipationFormat(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"  # If sender cancels it


class InvitationType(str, Enum):
    INVITE = "invite"  # Team invites User
    REQUEST = "request"  # User requests to join Team


class TelegramReasonNotInvited(str, Enum):
    UNRESOLVABLE_USERNAME = (
        "unresolvable_username"  # handle could not be resolved via get_input_entity
    )
    PRIVACY_RESTRICTED = "privacy_restricted"  # UserPrivacyRestrictedError
    NOT_MUTUAL_CONTACT = "not_mutual_contact"  # UserNotMutualContactError
    FLOOD_WAIT_EXHAUSTED = "flood_wait_exhausted"  # FloodWaitError after all retries
    MISCELLANEOUS = "miscellaneous"  # any other unexpected error


class TeamInvitation(SQLModel, table=True):
    __tablename__ = "team_invitations"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)

    type: InvitationType

    sender_id: int  # The Participant ID who created this (Leader or User)
    receiver_id: int  # The Participant ID who receives this (User or Leader)
    team_id: int  # The Team ID

    status: InvitationStatus = Field(default=InvitationStatus.PENDING)
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


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
    category: Optional["Category"] = Relationship(back_populates="teams")

    members: List["Participant"] = Relationship(back_populates="team")

    final_location: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), onupdate=utc_now),
    )


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    task_file_id: Optional[str] = Field(default=None)
    teams: List["Team"] = Relationship(back_populates="category")
    participants: List["Participant"] = Relationship(back_populates="category")


class PendingBroadcast(SQLModel, table=True):
    """Queues a broadcast document delivery for a participant who had no telegram_chat_id
    at the time the broadcast ran.  The record is consumed and deleted the first
    time the participant activates the bot (i.e. when ChatIdCaptureMiddleware
    successfully sets their telegram_chat_id)."""

    __tablename__ = "pending_broadcasts"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "category_id",
            name="uix_pending_broadcast_participant_category",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    participant_id: int = Field(foreign_key="participants.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class TeamSubmission(SQLModel, table=True):
    __tablename__ = "team_submissions"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id", index=True)

    submission_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB(), "postgresql")),
    )

    is_passed: Optional[bool] = None

    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), onupdate=utc_now),
    )


class Participant(SQLModel, table=True):
    __tablename__ = "participants"  # type: ignore

    __table_args__ = (
        Index(
            "ix_participants_skills_embedding",
            "skills_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"skills_embedding": "vector_cosine_ops"},
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Personal / Contact
    full_name: str = Field(index=True)
    email: str = Field(unique=True)
    telegram: str = Field(unique=True)
    telegram_chat_id: Optional[int] = Field(
        default=None, sa_type=BigInteger, index=True
    )
    phone: str

    is_student: bool
    study_year: Optional[int] = None

    # University Reference
    university_id: Optional[int] = Field(foreign_key="universities.id", default=None)
    university: Optional[University] = Relationship(back_populates="participants")

    # Hackathon Logic
    category_id: int = Field(foreign_key="categories.id")
    category: Optional[Category] = Relationship(back_populates="participants")
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

    # Profile Information
    bio: Optional[str] = None

    # Skills
    skills_text: Optional[str] = None
    skills_embedding: List[float] = Field(default=None, sa_column=Column(Vector(768)))

    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), onupdate=utc_now),
    )

    is_telegram_group_member: bool = Field(default=False)
    is_telegram_final_group_member: bool = Field(
        default=False
    )  # Only True if they were successfully invited
    is_withdraw: bool = Field(default=False)

    telegram_reason_not_invited: Optional[TelegramReasonNotInvited] = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                TelegramReasonNotInvited,
                values_callable=lambda x: [e.value for e in x],
                create_type=False,
            ),
            nullable=True,
        ),
    )
    misc_reason_not_invited: Optional[str] = None


class CategoryMentorshipConfig(SQLModel, table=True):
    """Per-category mentorship configuration stored in the database.

    Simple scalars are real columns (easy SQL UPDATE).
    Nested/complex structures are JSON TEXT columns.
    """

    __tablename__ = "category_mentorship_configs"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.id", unique=True)
    group_chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    session_duration: int  # minutes per session
    session_gap: int  # minutes gap between sessions
    min_session_count: int = 0  # legacy, kept for backward compat
    max_session_count: int = 0  # legacy, kept for backward compat
    assignment_type: str = "whatever"  # legacy, kept for backward compat
    schedule_json: str = Field(
        sa_column=Column(Text, nullable=False)
    )  # JSON list of {"start": "HH:MM", "end": "HH:MM"}
    whatever_config_json: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )  # legacy, kept for backward compat
    strict_config_json: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )  # legacy, kept for backward compat
    helper_group_chat_id: Optional[int] = Field(
        default=None, sa_column=Column(BigInteger, nullable=True)
    )


class Mentor(SQLModel, table=True):
    """A mentor available for mentorship sessions in a specific category."""

    __tablename__ = "mentors"  # type: ignore
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_handle: str = Field(index=True, unique=True)
    display_name: str
    category_id: int = Field(foreign_key="categories.id")
    participation_format: str = Field(default="offline")  # "online" | "offline"
    mentor_group: Optional[str] = Field(default=None)  # maps to a group in YAML config
    default_meeting_link: Optional[str] = Field(default=None)


class MentorshipSession(SQLModel, table=True):
    """A booked mentorship session between a mentor and a team."""

    __tablename__ = "mentorship_sessions"  # type: ignore
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    mentor_id: int = Field(foreign_key="mentors.id")
    team_id: int = Field(foreign_key="teams.id")
    slot_start: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    slot_end: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    meeting_link: Optional[str] = Field(default=None)
    reminder_sent: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class ActivatedGroup(SQLModel, table=True):
    """Tracks which Telegram group chat is activated for which team."""

    __tablename__ = "activated_groups"  # type: ignore
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id", unique=True)
    chat_id: int = Field(sa_column=Column(BigInteger, unique=True, nullable=False))
    activated_by: int = Field(sa_column=Column(BigInteger, nullable=False))
    activated_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class GroupTopic(SQLModel, table=True):
    """Maps a team to a forum topic in the mentor supergroup."""

    __tablename__ = "group_topics"  # type: ignore
    __table_args__ = (
        UniqueConstraint("mentor_group_chat_id", "team_id"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id")
    mentor_group_chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    thread_id: int = Field()  # forum topic message_thread_id
    topic_name: str = Field()
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class ForwardedMessage(SQLModel, table=True):
    """Tracks message pairs for cross-group edit/delete sync."""

    __tablename__ = "forwarded_messages"  # type: ignore
    __table_args__ = (
        Index("ix_fwd_source", "source_chat_id", "source_message_id"),
        Index("ix_fwd_target", "target_chat_id", "target_message_id"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    source_chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    source_message_id: int = Field()
    target_chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    target_message_id: int = Field()
    direction: str = Field()  # "ask", "reply", "send"
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class Helper(SQLModel, table=True):
    """A helper available to support mentorship sessions."""

    __tablename__ = "helpers"  # type: ignore
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(
        sa_column=Column(BigInteger, unique=True, nullable=False)
    )
    telegram_handle: Optional[str] = Field(default=None, index=True, unique=True)
    display_name: str
    default_meeting_link: Optional[str] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class HelperAvailabilitySlot(SQLModel, table=True):
    """Helper availability represented in slot granularity."""

    __tablename__ = "helper_availability_slots"  # type: ignore
    __table_args__ = (
        UniqueConstraint("helper_id", "slot_start", "slot_end"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    helper_id: int = Field(foreign_key="helpers.id")
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    slot_start: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    slot_end: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class SessionHelperAssignment(SQLModel, table=True):
    """Assignment of a helper to a mentorship session."""

    __tablename__ = "session_helper_assignments"  # type: ignore
    __table_args__ = (
        UniqueConstraint("session_id"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="mentorship_sessions.id")
    helper_id: int = Field(foreign_key="helpers.id")
    status: str = Field(default="assigned")  # assigned | swapped | released
    assigned_by: Optional[int] = Field(
        default=None, sa_column=Column(BigInteger, nullable=True)
    )
    assigned_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class MentorAvailabilitySlot(SQLModel, table=True):
    """One mentor-level long availability interval for the mentorship day."""

    __tablename__ = "mentor_availability_slots"  # type: ignore
    __table_args__ = (
        UniqueConstraint("mentor_id"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mentor_id: int = Field(foreign_key="mentors.id")
    slot_start: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    slot_end: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )


class MentorHelperLink(SQLModel, table=True):
    """Many-to-many mapping of mentors to supporting helpers."""

    __tablename__ = "mentor_helper_links"  # type: ignore
    __table_args__ = (
        UniqueConstraint("mentor_id", "helper_id"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mentor_id: int = Field(foreign_key="mentors.id")
    helper_id: int = Field(foreign_key="helpers.id")
    created_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
