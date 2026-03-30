from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResearchArticleResponse(BaseModel):
    """Schema for research article API responses"""

    id: int
    source: str
    title: str
    url: str
    ai_summary_short: Optional[str]
    keywords: Optional[str]
    relevance_score: int
    created_at: datetime
    published_at: Optional[datetime]
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ResearchSessionResponse(BaseModel):
    """Schema for research session API responses"""

    id: int
    session_date: datetime
    articles_collected: int
    articles_summarized: int
    execution_time_seconds: Optional[int]
    status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ResearchStatsResponse(BaseModel):
    """Daily research statistics"""

    total_articles: int
    summarized_count: int
    average_relevance_score: float
    top_keywords: list[str]
    latest_session_date: Optional[datetime]
    articles_today: int
