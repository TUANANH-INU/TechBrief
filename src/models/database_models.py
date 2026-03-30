import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NewsSource(str, enum.Enum):
    """News source types"""

    HACKER_NEWS = "hacker_news"
    TECH_CRUNCH = "tech_crunch"
    MEDIUM = "medium"
    DEV_TO = "dev_to"
    GITHUB_TRENDING = "github_trending"


class ResearchArticle(Base):
    """Model for storing research articles and summaries"""

    __tablename__ = "research_articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    original_content = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_summary_short = Column(String(500), nullable=True)
    keywords = Column(String(500), nullable=True)
    relevance_score = Column(Integer, default=0)  # 0-100
    is_relevant = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ResearchArticle(id={self.id}, title={self.title[:50]}...)>"


class ResearchSession(Base):
    """Model for tracking daily research sessions"""

    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_date = Column(DateTime, default=datetime.utcnow)
    articles_collected = Column(Integer, default=0)
    articles_summarized = Column(Integer, default=0)
    execution_time_seconds = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    skill_focus = Column(String(100), nullable=True)  # Today's skill focus

    def __repr__(self):
        return f"<ResearchSession(id={self.id}, date={self.session_date}, status={self.status})>"
