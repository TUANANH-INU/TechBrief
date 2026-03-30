import asyncio
import logging
import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.database_models import ResearchArticle, ResearchSession
from src.models.schemas import ResearchArticleResponse, ResearchSessionResponse, ResearchStatsResponse
from src.services.news_aggregator import news_aggregator
from src.services.ollama_service import ollama_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    ollama_healthy = ollama_service.check_health_sync()
    return {"status": "ok", "timestamp": datetime.utcnow(), "ollama": "healthy" if ollama_healthy else "unhealthy"}


@router.get("/articles", response_model=List[ResearchArticleResponse])
async def get_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get latest research articles"""
    articles = db.query(ResearchArticle).order_by(ResearchArticle.created_at.desc()).offset(skip).limit(limit).all()

    return articles


@router.get("/articles/processed", response_model=List[ResearchArticleResponse])
async def get_processed_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get processed articles with summaries"""
    articles = (
        db.query(ResearchArticle)
        .filter(ResearchArticle.ai_summary != None)
        .order_by(ResearchArticle.processed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return articles


@router.get("/articles/today", response_model=List[ResearchArticleResponse])
async def get_today_articles(db: Session = Depends(get_db)):
    """Get articles from today"""
    today = datetime.utcnow().date()

    articles = (
        db.query(ResearchArticle)
        .filter(func.date(ResearchArticle.created_at) == today)
        .order_by(ResearchArticle.created_at.desc())
        .all()
    )

    return articles


@router.get("/articles/{article_id}", response_model=ResearchArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get specific article"""
    article = db.query(ResearchArticle).filter(ResearchArticle.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.get("/stats", response_model=ResearchStatsResponse)
async def get_research_stats(db: Session = Depends(get_db)):
    """Get research statistics"""
    total = db.query(func.count(ResearchArticle.id)).scalar()
    summarized = db.query(func.count(ResearchArticle.id)).filter(ResearchArticle.ai_summary != None).scalar()

    avg_score = db.query(func.avg(ResearchArticle.relevance_score)).scalar() or 0

    today = datetime.utcnow().date()
    today_count = (
        db.query(func.count(ResearchArticle.id)).filter(func.date(ResearchArticle.created_at) == today).scalar()
    )

    # Get top keywords
    keywords_raw = db.query(ResearchArticle.keywords).filter(ResearchArticle.keywords != None).all()

    top_keywords = []
    if keywords_raw:
        keyword_list = []
        for kw_tuple in keywords_raw:
            if kw_tuple[0]:
                keyword_list.extend([k.strip() for k in kw_tuple[0].split(",")])

        # Count occurrences
        from collections import Counter

        keyword_counts = Counter(keyword_list)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(5)]

    latest_session = db.query(ResearchSession).order_by(ResearchSession.session_date.desc()).first()

    return ResearchStatsResponse(
        total_articles=total or 0,
        summarized_count=summarized or 0,
        average_relevance_score=float(avg_score),
        top_keywords=top_keywords,
        latest_session_date=latest_session.session_date if latest_session else None,
        articles_today=today_count or 0,
    )


@router.post("/run-research")
async def run_research(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger research aggregation manually"""
    session = ResearchSession(status="running")
    db.add(session)
    db.commit()

    background_tasks.add_task(execute_research, session.id, db)

    return {"message": "Research execution started", "session_id": session.id, "status": "running"}


@router.get("/sessions", response_model=List[ResearchSessionResponse])
async def get_sessions(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get research sessions"""
    sessions = db.query(ResearchSession).order_by(ResearchSession.session_date.desc()).offset(skip).limit(limit).all()

    return sessions


@router.post("/send-test-slack")
async def send_test_slack(skill: str = "FastAPI", db: Session = Depends(get_db)):
    """Send a test Slack message with sample articles"""
    from src.config import settings
    from src.services.skills import skill_rotation
    from src.services.slack_service import slack_service

    if not settings.slack_enabled or not settings.slack_webhook_url:
        raise HTTPException(status_code=400, detail="Slack is not enabled")

    # Get recent processed articles
    articles = (
        db.query(ResearchArticle)
        .filter(ResearchArticle.ai_summary != None)
        .order_by(ResearchArticle.processed_at.desc())
        .limit(10)
        .all()
    )

    if not articles:
        raise HTTPException(status_code=404, detail="No processed articles found")

    # Filter by skill
    skill_articles = skill_rotation.filter_articles_by_skill(articles, skill)

    if not skill_articles:
        skill_articles = articles  # Fall back to all articles if none match skill

    # Send test report
    success = slack_service.send_daily_report(skill, skill_articles, 15)

    if success:
        return {"message": "Test Slack message sent successfully", "skill": skill, "article_count": len(skill_articles)}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Slack message")


def execute_research(session_id: int, db: Session):
    """Background task to execute research"""

    try:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()

        if not session:
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
        logger.info(f"✓ Research session {session_id} completed in {execution_time}s")

    except Exception as e:
        logger.error(f"Research execution failed: {e}")
        session.status = "failed"
        session.error_message = str(e)
        db.commit()
