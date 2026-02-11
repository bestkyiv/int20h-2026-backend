import asyncio
import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

# SQLModel / SQLAlchemy Async Imports
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlalchemy.ext.asyncio import async_sessionmaker

load_dotenv()

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# Import your model
from src.db.models import Participant

# Initialize Client
client = genai.Client()


def extract_embedding(result: types.EmbedContentResponse):
    if not result.embeddings:
        return None
    emb0 = result.embeddings[0]
    return emb0.values


async def get_gemini_embedding(
    text: str, dimension: int = 768
) -> Optional[List[float]]:
    """
    Async wrapper for the Gemini embedding call.
    Uses client.aio for non-blocking I/O.
    """
    try:
        # Note the usage of client.aio here
        result = await client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY", output_dimensionality=dimension
            ),
        )
        return extract_embedding(result)
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return None


def get_async_db_url(url: str) -> str:
    """
    SQLAlchemy Async engines require async drivers.
    Common fix: swap 'postgresql://' with 'postgresql+asyncpg://'
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def process_participant(
    session, p: Participant, sem: asyncio.Semaphore, dry_run: bool
) -> bool:
    """
    Process a single participant with a semaphore for concurrency control.
    Returns True if updated, False otherwise.
    """
    async with sem:  # Limits how many of these run at the exact same time
        print(f"Processing {p.id}...")
        assert p.skills_text is not None

        emb = await get_gemini_embedding(p.skills_text)

        if not emb:
            print(f" -> {p.id}: No embedding returned.")
            return False

        p.skills_embedding = emb
        if not dry_run:
            session.add(p)
        return True


async def main(dry_run: bool = False, batch_size: int = 20, concurrency: int = 10):
    raw_url = "postgresql://int_backend:password@localhost:5432/int_backend"

    # Ensure URL is async-compatible (convert if user provided non-async URL)
    database_url = get_async_db_url(raw_url)

    # Create Async Engine
    engine = create_async_engine(database_url, echo=False)

    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        # 1. Fetch all participants to process
        # We use await session.exec(...) for async queries
        # Use SQLAlchemy `is_not` / `is_` for NULL comparisons
        statement = select(Participant).where(
            Participant.skills_text.is_not(None), Participant.skills_embedding.is_(None)
        )
        result = await session.execute(statement)
        to_process = result.scalars().all()

        print(f"Found {len(to_process)} participants to process")

        # 2. Process in batches to avoid holding too many objects in memory/transactions
        # We use a Semaphore to control API concurrency (rate limiting)
        sem = asyncio.Semaphore(concurrency)
        total_updated = 0

        # Chunk the list into batches
        for i in range(0, len(to_process), batch_size):
            batch = to_process[i : i + batch_size]
            print(f"--- Starting batch {i} to {i+len(batch)} ---")

            # Create async tasks for this batch
            tasks = [process_participant(session, p, sem, dry_run) for p in batch]

            # Run tasks concurrently and wait for all in this batch to finish
            results = await asyncio.gather(*tasks)

            # Count successes
            updated_in_batch = sum(results)
            total_updated += updated_in_batch

            # Commit the batch
            if not dry_run and updated_in_batch > 0:
                await session.commit()
                print(f" -> Committed batch. Total updated so far: {total_updated}")

    print(f"Done. Updated {total_updated} participants")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not commit changes")
    parser.add_argument(
        "--batch-size", type=int, default=50, help="DB commit batch size"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Max concurrent API calls"
    )
    args = parser.parse_args()

    # Run the async main loop
    asyncio.run(
        main(
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            concurrency=args.concurrency,
        )
    )
