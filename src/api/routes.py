import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.reseach import execute_research
from src.config import settings
from src.models.database import get_db
from src.models.database_models import ResearchSession
from src.models.research import article as article_db
from src.models.research import session as session_db
from src.models.schemas import ResearchArticleResponse, ResearchSessionResponse, ResearchStatsResponse
from src.services.ollama import ollama_service
from src.services.skills import skill_rotation
from src.services.slack_service import slack_service

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
    articles, error = article_db.get_articles_paginated(db, skip, limit)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return articles


@router.get("/articles/processed", response_model=List[ResearchArticleResponse])
async def get_processed_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get processed articles with summaries"""
    articles, error = article_db.get_processed_articles_paginated(db, skip, limit)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return articles


@router.get("/articles/today", response_model=List[ResearchArticleResponse])
async def get_today_articles(db: Session = Depends(get_db)):
    """Get articles from today"""
    today = datetime.utcnow().date()

    articles, error = article_db.get_today_articles(db, today)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return articles


@router.get("/articles/{article_id}", response_model=ResearchArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get specific article"""
    article, error = article_db.get_article_by_id(db, article_id)
    if error:
        raise HTTPException(status_code=404, detail=error)

    return article


@router.get("/stats", response_model=ResearchStatsResponse)
async def get_research_stats(db: Session = Depends(get_db)):
    """Get research statistics"""
    total, error = article_db.calculate_total_articles(db)
    if total is None or error:
        logger.warning(f"Error calculating total articles: {error}")
        total = 0

    summarized, error = article_db.calculate_summarized_articles(db)
    if summarized is None or error:
        logger.warning(f"Error calculating summarized articles: {error}")
        summarized = 0

    avg_score, error = article_db.calculate_average_relevance_score(db)
    if avg_score is None or error:
        logger.warning(f"Error calculating average relevance score: {error}")
        avg_score = 0.0

    today = datetime.utcnow().date()
    today_count, error = article_db.calculate_summarized_articles_for_date(db, today)
    if today_count is None or error:
        logger.warning(f"Error calculating today's summarized articles: {error}")
        today_count = 0

    # Get top keywords
    keywords_raw, error = article_db.get_top_keywords(db)
    if keywords_raw is None or error:
        logger.warning(f"Error fetching top keywords: {error}")
        keywords_raw = []

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

    latest_session, error = session_db.get_latest_research_session(db)
    if error:
        logger.warning(f"Error fetching latest research session: {error}")
        latest_session = None

    return ResearchStatsResponse(
        total_articles=total,
        summarized_count=summarized,
        average_relevance_score=float(avg_score),
        top_keywords=top_keywords,
        latest_session_date=latest_session.session_date if latest_session else None,
        articles_today=today_count,
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
    sessions, error = session_db.get_research_sessions_paginated(db, skip, limit)
    if error:
        raise HTTPException(status_code=404, detail=error)

    return sessions


@router.post("/send-slack")
async def send_test_slack(skill: str = "FastAPI", db: Session = Depends(get_db)):
    """Send a test Slack message with sample articles"""

    if not settings.slack_enabled or not settings.slack_webhook_url:
        raise HTTPException(status_code=400, detail="Slack is not enabled")

    # Get recent processed articles
    articles, error = article_db.get_processed_articles_paginated(db, skip=0, limit=10)
    if error:
        raise HTTPException(status_code=404, detail=error)

    # Filter by skill
    skill_articles = skill_rotation.filter_articles_by_skill(articles, skill)
    if not skill_articles:
        skill_articles = articles  # Fall back to all articles if none match skill

    # Send test report
    success = slack_service.send_daily_report(skill, skill_articles, 15)

    if success:
        return {"message": "Send Slack message successfully", "skill": skill, "article_count": len(skill_articles)}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Slack message")
