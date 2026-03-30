#!/usr/bin/env python3
"""CLI tool for TechBrief management"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import typer

from src.config import settings
from src.models.database import SessionLocal
from src.models.research import article as article_db
from src.services.news_aggregator import news_aggregator
from src.services.ollama import ollama_service
from src.services.slack_service import SlackService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def run_research(skill: Optional[str] = None):
    """Run research aggregation manually"""
    db = SessionLocal()
    try:
        logger.info("🔄 Starting manual research run...")

        if skill:
            logger.info(f"🎯 Focusing on skill: {skill}")

        # Run aggregation
        async def run_agg():
            return await news_aggregator.aggregate_daily(db, focus_skill=skill)

        count = asyncio.run(run_agg())
        logger.info(f"Collected {count} articles")

        # Run processing
        async def run_proc():
            return await news_aggregator.process_articles_with_ai(db)

        processed = asyncio.run(run_proc())
        logger.info(f"Processed {processed} articles with AI")

    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def test_slack(skill: str = "FastAPI"):
    """Send test Slack report"""
    db = SessionLocal()
    try:
        logger.info(f"� Testing Slack for skill: {skill}")

        # Get recent articles (limit to 5 for testing)
        articles, error = article_db.get_recent_summarized_articles(db, limit=5)
        if error:
            logger.error(f"Error fetching recent summarized articles: {error}")
            articles = []

        # Convert to dict format expected by slack service
        articles_data = []
        for article in articles:
            articles_data.append(
                {
                    "title": article.title,
                    "source": article.source,
                    "ai_summary_short": article.ai_summary_short,
                    "keywords": article.keywords,
                    "url": article.url,
                }
            )

        # Get basic stats
        total_articles, error = article_db.calculate_total_articles(db)
        if error:
            logger.error(f"Error calculating total articles: {error}")
            total_articles = 0

        summarized_count, error = article_db.calculate_summarized_articles(db)
        if error:
            logger.error(f"Error calculating summarized articles: {error}")
            summarized_count = 0

        stats = {
            "total_articles": total_articles,
            "summarized_count": summarized_count,
            "average_relevance_score": 75.0,  # Mock value for testing
            "articles_today": len(articles_data),
        }

        # Mock session info
        session_info = {
            "session_date": datetime.utcnow(),
            "execution_time_seconds": 45,
            "articles_collected": len(articles_data),
            "articles_summarized": len(articles_data),
            "status": "completed",
        }

        slack_service = SlackService()
        success = slack_service.send_daily_report(skill, articles_data, stats, session_info)

        if success:
            logger.info("✅ Test Slack message sent successfully")
        else:
            logger.warning("⚠️  Slack message not sent - configuration incomplete")
            logger.info("   Configure SLACK_WEBHOOK_URL in .env file:")
            logger.info("   - SLACK_ENABLED=true")
            logger.info("   - SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")

    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def check_health():
    """Check system health"""
    logger.info("🔍 Checking system health...")

    # Check Ollama
    ollama_ok = ollama_service.check_health_sync()
    logger.info(f"Ollama: {'✓' if ollama_ok else '✗'}")

    # Check database
    db = SessionLocal()
    try:
        db.execute("SELECT 1")
        logger.info("Database: ✓")
    except Exception as e:
        logger.error(f"Database: ✗ ({e})")
    finally:
        db.close()

    # Check email config
    email_configured = bool(settings.smtp_server and settings.email_recipients)
    logger.info(f"Email: {'✓' if email_configured else '✗'}")

    if not ollama_ok:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
