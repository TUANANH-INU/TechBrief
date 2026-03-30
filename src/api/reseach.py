import asyncio
import logging
import time

from sqlalchemy.orm import Session

from src.models.research import session as session_db
from src.services.news_aggregator import news_aggregator

logger = logging.getLogger(__name__)


def execute_research(session_id: int, db: Session):
    """Background task to execute research"""

    try:
        session, error = session_db.get_research_session_by_id(db, session_id)
        if error:
            logger.error(f"Error fetching research session: {error}")
            return

        start_time = time.time()

        # Run async aggregation in event loop
        async def run_aggregation():
            return await news_aggregator.aggregate_daily(db)

        aggregate_count = asyncio.run(run_aggregation())
        session.articles_collected = aggregate_count

        # Run async processing in event loop
        async def run_processing():
            return await news_aggregator.process_articles_with_ai(db)

        process_count = asyncio.run(run_processing())
        session.articles_summarized = process_count

        execution_time = int(time.time() - start_time)
        session.execution_time_seconds = execution_time
        session.status = "completed"

        db.commit()
        logger.info(f"Research session {session_id} completed in {execution_time}s")

    except Exception as e:
        logger.error(f"Research execution failed: {e}")
        session.status = "failed"
        session.error_message = str(e)
        db.commit()
