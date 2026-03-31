"""Task scheduler for daily research runs"""

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.models.database import SessionLocal
from src.models.database_models import ResearchSession
from src.models.research import article as article_db
from src.services.news_aggregator import news_aggregator
from src.services.skills import skill_rotation
from src.services.slack_service import slack_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_research_job():
    """Daily research job"""
    db = SessionLocal()
    try:
        logger.info("🔄 Starting scheduled research job...")

        session = ResearchSession(status="running")
        db.add(session)
        db.commit()

        start_time = time.time()

        # Get today's skill
        today_skill = skill_rotation.get_today_skill()

        # Aggregate
        aggregate_count = news_aggregator.aggregate_daily(db)
        session.articles_collected = aggregate_count

        # Process with AI
        process_count = news_aggregator.process_articles_with_ai(db)
        session.articles_summarized = process_count

        execution_time = int(time.time() - start_time)
        session.execution_time_seconds = execution_time
        session.status = "completed"
        session.skill_focus = today_skill

        db.commit()
        logger.info(f"✅ Research job completed in {execution_time}s")
        logger.info(f"   - Articles collected: {aggregate_count}")
        logger.info(f"   - Articles processed: {process_count}")
        logger.info(f"   - Skill focus: {today_skill}")

        # Send to Slack if enabled
        if settings.slack_enabled and settings.slack_webhook_url:

            # Get processed articles for today
            processed_articles, error = article_db.get_processed_articles_paginated(db, limit=10)
            if error:
                logger.error(f"Error fetching processed articles for Slack report: {error}")
                processed_articles = []

            # Filter by skill
            skill_articles = skill_rotation.filter_articles_by_skill(processed_articles, today_skill)
            if skill_articles:
                slack_service.send_daily_report(today_skill, skill_articles, execution_time)
                logger.info(f"Slack report sent for {today_skill}")

    except Exception as e:
        logger.error(f"Research job failed: {e}", exc_info=True)
        try:
            session.status = "failed"
            session.error_message = str(e)
            db.commit()
        except Exception as db_e:
            logger.error(f"Failed to update session status: {db_e}", exc_info=True)
            pass
    finally:
        db.close()


def start_scheduler():
    """Start background scheduler"""
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled")
        return

    if scheduler.running:
        logger.info("Scheduler already running")
        return

    # Schedule daily research at configured time
    scheduler.add_job(
        scheduled_research_job,
        CronTrigger(hour=settings.research_schedule_hour, minute=settings.research_schedule_minute),
        id="daily_research",
        name="Daily Research Aggregation",
        replace_existing=True,
        misfire_grace_time=300,  # Allow 5 minutes grace for missed scheduled time
    )

    scheduler.start()
    logger.info(f"Scheduler started - Daily research at {settings.research_schedule_hour:02d}:{settings.research_schedule_minute:02d}")


def stop_scheduler():
    """Stop background scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
