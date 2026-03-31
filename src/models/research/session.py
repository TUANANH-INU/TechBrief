from typing import Optional

from sqlalchemy.orm import Session

from src.models.database_models import ResearchSession


def get_research_session_by_id(db: Session, session_id: int) -> tuple[Optional[ResearchSession], str]:
    try:
        session_info = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session_info:
            return None, "Research session not found"
        return session_info, ""
    except Exception as e:
        return None, f"Error fetching research session by ID: {str(e)}"


def get_latest_research_session(db: Session) -> tuple[Optional[ResearchSession], str]:
    try:
        session_info = db.query(ResearchSession).order_by(ResearchSession.session_date.desc()).first()
        if not session_info:
            return None, "No research sessions found"
        return session_info, ""
    except Exception as e:
        return None, f"Error fetching latest research session: {str(e)}"


def get_research_sessions_paginated(db: Session, skip: int = 0, limit: int = 20) -> tuple[list[ResearchSession], str]:
    try:
        sessions = db.query(ResearchSession).order_by(ResearchSession.session_date.desc()).offset(skip).limit(limit).all()
        return sessions, ""
    except Exception as e:
        return [], f"Error fetching research sessions: {str(e)}"
