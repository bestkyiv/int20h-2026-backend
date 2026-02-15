from enum import Enum, IntEnum
from pydantic import (
    AfterValidator,
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    model_validator,
)
from typing import Annotated, Literal
import phonenumbers
import logging

logger = logging.getLogger(__name__)


class StudyYear(IntEnum):
    YEAR_1 = 1
    YEAR_2 = 2
    YEAR_3 = 3
    YEAR_4 = 4
    YEAR_5 = 5
    YEAR_6 = 6
    GRADUATED = 7

    def __str__(self):
        if self <= 4:
            return f"{self.value} курс"
        elif self == 5:
            return "1 магістр"
        elif self == 6:
            return "2 магістр"
        else:
            return "Закінчив"


def normalize_phone_number(number: str) -> str:
    try:
        parsed_number = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Invalid phone number: {e}")

    if not phonenumbers.is_possible_number(parsed_number):
        raise ValueError("Invalid phone number")
    return phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.E164
    )


NormalizedPhone = Annotated[str, AfterValidator(normalize_phone_number)]


class ParticipationFormat(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Form(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Annotated[
        str,
        Field(
            description="The full name of the user",
            min_length=2,
            max_length=100,
        ),
    ]

    email: Annotated[
        EmailStr,
        Field(
            description="The email address of the user",
            max_length=100,
        ),
    ]

    telegram: Annotated[
        str,
        Field(
            description="The Telegram handle of the user",
            min_length=1,
            max_length=100,
        ),
    ]

    phone: Annotated[
        NormalizedPhone,
        Field(description="The phone number of the user", max_length=100),
    ]

    is_student: Annotated[
        bool, Field(description="Whether the user is a student or not")
    ]

    university_id: Annotated[
        int | None, Field(default=None, description="The ID of the user's university")
    ]

    study_year: Annotated[
        StudyYear | None, Field(description="The current year of study of the user")
    ]

    category_id: Annotated[
        int, Field(description="The category of interest for the user")
    ]

    skills: Annotated[
        list[Annotated[str, Field(max_length=100)]],
        Field(description="List of skills the user has"),
    ]

    format: Annotated[
        ParticipationFormat,
        Field(description="The preferred format of participation for the user"),
    ]

    has_team: Annotated[bool, Field(description="Whether the user has a team or not")]

    team_leader: Annotated[
        bool, Field(description="Whether the user is the team lead or not")
    ]

    team_name: Annotated[
        str,
        Field(description="The name of the user's team", max_length=100),
    ]

    wants_job: Annotated[
        bool, Field(description="Whether the user is looking for a job or not")
    ]

    job_description: Annotated[
        str,
        Field(
            description="Description of the job the user is looking for",
            max_length=2000,
        ),
    ]

    cv: Annotated[
        str,
        Field(description="URL to the user's CV file", max_length=100),
    ]
    linkedin: Annotated[
        str,
        Field(description="URL to the user's LinkedIn profile", max_length=100),
    ]
    work_consent: Annotated[
        bool, Field(description="Whether the user consents to work terms")
    ]

    source: Annotated[
        str,
        Field(
            description="How the user heard about the event",
            min_length=1,
            max_length=100,
        ),
    ]

    otherSource: Annotated[
        str | None,
        Field(description="Other source if applicable", max_length=100),
    ]

    comment: Annotated[
        str | None,
        Field(description="Additional comments from the user", max_length=2000),
    ]

    personal_data_consent: Annotated[
        Literal[True], Field(description="Consent for personal data processing")
    ]

    @model_validator(mode="after")
    def validate_cross_field_constraints(self):
        """Validate cross-field constraints as per frontend validation."""
        # If CV or LinkedIn provided, require workConsent
        if (self.cv and self.cv.strip()) or (self.linkedin and self.linkedin.strip()):
            if not self.work_consent:
                logger.warning(
                    "Validation failed: CV/LinkedIn provided without work_consent for email=%s",
                    self.email,
                )
                raise ValueError(
                    "Потрібно надати згоду на обробку даних для передачі CV/LinkedIn."
                )

        # If wantsCV (wants_job), require cv
        if self.wants_job:
            if not self.cv or not self.cv.strip():
                logger.warning(
                    "Validation failed: wants_job=True but no cv provided for email=%s",
                    self.email,
                )
                raise ValueError("Будь ласка, надайте посилання на CV.")
            # Validate CV URL format
            try:
                from urllib.parse import urlparse

                parsed = urlparse(self.cv)
                if parsed.scheme not in ("http", "https"):
                    logger.warning(
                        "Validation failed: cv has invalid scheme for email=%s, url=%s",
                        self.email,
                        self.cv,
                    )
                    raise ValueError(
                        "Посилання на CV має починатися з http:// або https://."
                    )
            except ValueError:
                raise
            except Exception as e:
                logger.warning(
                    "Validation failed: cv url parsing error for email=%s, error=%s",
                    self.email,
                    e,
                )
                raise ValueError("Будь ласка, вкажіть коректне посилання на CV.")

        # If LinkedIn provided, validate URL format
        if self.linkedin and self.linkedin.strip():
            try:
                from urllib.parse import urlparse

                parsed = urlparse(self.linkedin)
                if parsed.scheme not in ("http", "https"):
                    logger.warning(
                        "Validation failed: linkedin has invalid scheme for email=%s, url=%s",
                        self.email,
                        self.linkedin,
                    )
                    raise ValueError(
                        "Посилання на LinkedIn має починатися з http:// або https://."
                    )
            except ValueError:
                raise
            except Exception as e:
                logger.warning(
                    "Validation failed: linkedin url parsing error for email=%s, error=%s",
                    self.email,
                    e,
                )
                raise ValueError("Будь ласка, вкажіть коректне посилання на LinkedIn.")

        # If source is "other" or "otherSocial", require otherSource
        if self.source in ("other", "otherSocial"):
            if not self.otherSource or not self.otherSource.strip():
                logger.warning(
                    "Validation failed: source=%s but no otherSource provided for email=%s",
                    self.source,
                    self.email,
                )
                raise ValueError("Будь ласка, вкажіть джерело, якщо обрали 'Other'.")

        if self.is_student:
            if self.university_id is None:
                logger.warning(
                    "Validation failed: is_student=True but no university_id for email=%s",
                    self.email,
                )
                raise ValueError("Будь ласка, вкажіть ваш університет.")
            if self.study_year is None:
                logger.warning(
                    "Validation failed: is_student=True but no study_year for email=%s",
                    self.email,
                )
                raise ValueError("Будь ласка, вкажіть ваш курс навчання.")
        return self
