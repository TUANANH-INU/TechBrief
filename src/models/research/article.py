from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.database_models import ResearchArticle


def get_research_article_by_url(db: Session, link: str) -> tuple[Optional[ResearchArticle], str]:
    existing = db.query(ResearchArticle).filter(ResearchArticle.url == link).first()
    if not existing:
        return None, "Article not found"
    return existing, ""


def get_unprocessed_articles(db: Session, limit: int = 20) -> tuple[List[ResearchArticle], str]:
    articles = db.query(ResearchArticle).filter(ResearchArticle.ai_summary == None).order_by(ResearchArticle.created_at.asc()).limit(limit).all()
    if not articles:
        return [], "No unprocessed articles found"
    return articles, ""


def calculate_summarized_articles_for_date(db: Session, today: float) -> tuple[int, str]:
    articles = db.query(func.count(ResearchArticle.id)).filter(func.date(ResearchArticle.created_at) == today).scalar()
    if not articles:
        return 0, "No summarized articles found"
    return articles, ""


def calculate_total_articles(db: Session) -> tuple[int, str]:
    total = db.query(func.count(ResearchArticle.id)).scalar()
    return total, ""


def calculate_summarized_articles(db: Session) -> tuple[int, str]:
    total = db.query(func.count(ResearchArticle.id)).filter(ResearchArticle.ai_summary_short != None).scalar()
    return total, ""


def calculate_average_relevance_score(db: Session) -> tuple[float, str]:
    score = db.query(func.avg(ResearchArticle.relevance_score)).scalar()
    return score, ""


def get_articles_paginated(db: Session, skip: int = 0, limit: int = 20) -> tuple[List[ResearchArticle], str]:
    articles = db.query(ResearchArticle).order_by(ResearchArticle.created_at.desc()).offset(skip).limit(limit).all()
    if not articles:
        return [], "No articles found"
    return articles, ""


def get_processed_articles_paginated(db: Session, skip: int = 0, limit: int = 20) -> tuple[List[ResearchArticle], str]:
    articles = (
        db.query(ResearchArticle)
        .filter(ResearchArticle.ai_summary != None)
        .order_by(ResearchArticle.processed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    if not articles:
        return [], "No processed articles found"
    return articles, ""


def get_today_articles(db: Session, today: float) -> tuple[List[ResearchArticle], str]:
    articles = db.query(ResearchArticle).filter(func.date(ResearchArticle.created_at) == today).order_by(ResearchArticle.created_at.desc()).all()
    if not articles:
        return [], "No articles found for today"
    return articles, ""


def get_article_by_id(db: Session, article_id: int) -> tuple[Optional[ResearchArticle], str]:
    article = db.query(ResearchArticle).filter(ResearchArticle.id == article_id).first()
    if not article:
        return None, "Article not found"
    return article, ""


def get_top_keywords(db: Session, limit: int = 10) -> tuple[List[str], str]:
    article_keywords = db.query(ResearchArticle.keywords).filter(ResearchArticle.keywords != None).all()
    if not article_keywords:
        return [], "No keywords found"
    return article_keywords, ""


def get_recent_summarized_articles(db: Session, limit: int = 5) -> tuple[List[ResearchArticle], str]:
    articles = (
        db.query(ResearchArticle).filter(ResearchArticle.ai_summary_short != None).order_by(ResearchArticle.created_at.desc()).limit(limit).all()
    )
    if not articles:
        return [], "No recent summarized articles found"
    return articles, ""
