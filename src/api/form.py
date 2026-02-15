from fastapi import APIRouter, Depends, HTTPException


from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Form
from src.db.core import get_session
from src.db.models import Participant, Team, University, Category

from src.logging_singleton import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/form/")
async def submit_form(form: Form, session: AsyncSession = Depends(get_session)):
    # Check if user already exists
    stmt_check_user = select(Participant).where(
        (Participant.email == form.email) | (Participant.telegram == form.telegram)
    )
    result_user = await session.execute(stmt_check_user)
    existing_user = result_user.scalars().first()

    if existing_user:
        if existing_user.email == form.email:
            logger.warning(
                "Registration failed: email already registered: %s", form.email
            )
            raise HTTPException(
                status_code=400, detail="Користувач з таким email вже зареєстрований"
            )
        if existing_user.telegram == form.telegram:
            logger.warning(
                "Registration failed: telegram already registered: %s", form.telegram
            )
            raise HTTPException(
                status_code=400, detail="Користувач з таким telegram вже зареєстрований"
            )

    # 2. Validate Foreign Keys (University & Category)
    # These checks ensure we don't get generic 500 errors for bad IDs
    if form.university_id is not None:
        university = await session.get(University, form.university_id)
        if not university:
            logger.warning(
                "Registration failed: university not found id=%s email=%s",
                form.university_id,
                form.email,
            )
            raise HTTPException(
                status_code=400, detail="Вказаний університет не знайдено"
            )

    category = await session.get(Category, form.category_id)
    if not category:
        logger.warning(
            "Registration failed: category not found id=%s email=%s",
            form.category_id,
            form.email,
        )
        raise HTTPException(status_code=400, detail="Вказана категорія не знайдена")

    # 3. Prepare Participant
    participant = Participant(
        full_name=form.full_name,
        email=form.email,
        telegram=form.telegram,
        study_year=form.study_year,
        phone=form.phone,
        university_id=form.university_id,
        category_id=form.category_id,
        participation_format=form.format,  # type: ignore
        team_leader=form.team_leader,
        wants_job=form.wants_job,
        job_description=form.job_description,
        cv_url=form.cv,
        linkedin=form.linkedin,
        work_consent=form.work_consent,
        source=(str(form.otherSource) if form.source == "otherSocial" else form.source),
        comment=form.comment,
        is_student=form.is_student,
        personal_data_consent=form.personal_data_consent,
        skills_text=",".join(form.skills) if form.skills else "",
    )

    success_message = "Form submitted successfully"

    # 4. Handle Team Logic
    if form.has_team:
        team_name = form.team_name
        if not team_name:
            logger.warning(
                "Registration failed: has_team is True but no team_name provided. email=%s",
                form.email,
            )
            raise HTTPException(
                status_code=400, detail="Ви повинні вказати назву команди"
            )

        # Check existing team (in same category)
        stmt_team = select(Team).where(
            (Team.team_name == team_name) & (Team.category_id == form.category_id)
        )
        result_team = await session.execute(stmt_team)
        existing_team = result_team.scalars().first()

        if existing_team:
            # Join existing
            participant.team_id = existing_team.id
            participant.team_leader = False  # Force false if joining
            success_message = "Ви успішно приєдналися до команди"

        else:
            # Create new team
            if not form.team_leader:
                logger.warning(
                    "Registration failed: attempt to create team without team_leader. team_name=%s email=%s",
                    team_name,
                    form.email,
                )
                raise HTTPException(
                    status_code=400, detail="Команду має створювати тімлід"
                )

            new_team = Team(team_name=team_name, category_id=form.category_id)
            session.add(new_team)
            # We let SQLAlchemy resolve the relationship ID upon commit/flush
            participant.team = new_team
            success_message = "Ви успішно створили команду"

    session.add(participant)

    # 5. Commit
    # Since we pre-validated everything, a failure here is likely a rare race condition.
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        logger.exception(
            "IntegrityError while saving participant/team: email=%s telegram=%s error=%s",
            form.email,
            form.telegram,
            e,
        )
        raise HTTPException(
            status_code=400,
            detail="Помилка збереження даних. Можливо, команда або користувач були створені одночасно з іншим запитом. Будь ласка, спробуйте ще раз.",
        )

    return {"message": success_message, "data": form.model_dump()}
