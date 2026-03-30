"""Skill rotation system for daily research focus"""

import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

# List of AI backend engineering skills to rotate through
SKILLS = [
    "FastAPI",
    "Kubernetes",
    "Docker",
    "PostgreSQL",
    "Redis",
    "GraphQL",
    "Microservices",
    "AWS",
    "GCP",
    "Azure",
    "Terraform",
    "CI/CD",
    "Monitoring",
    "Optimization",
    "Security",
]


class SkillRotation:
    """Manages daily skill rotation for research focus"""

    @staticmethod
    def get_today_skill() -> str:
        """
        Get today's skill based on day of year

        Returns:
            The skill to focus on today
        """
        day_of_year = datetime.utcnow().timetuple().tm_yday
        skill_index = (day_of_year - 1) % len(SKILLS)
        skill = SKILLS[skill_index]
        logger.info(f"👨‍💻 Today's skill: {skill} (day {day_of_year} of year)")
        return skill

    @staticmethod
    def get_all_skills() -> List[str]:
        """Get all available skills"""
        return SKILLS

    @staticmethod
    def filter_articles_by_skill(articles: List, skill: str) -> List:
        """
        Filter articles by relevance to skill

        Args:
            articles: List of ResearchArticle objects
            skill: Skill to filter by

        Returns:
            Filtered articles
        """
        filtered = []

        for article in articles:
            # Check if skill is mentioned in title, keywords, or summary
            content_to_check = f"{article.title} {article.keywords or ''} {article.ai_summary or ''}".lower()
            if skill.lower() in content_to_check:
                filtered.append(article)

        logger.info(f"Filtered {len(filtered)} articles for skill: {skill}")
        return filtered if filtered else articles  # Return all if none match


# Global instance
skill_rotation = SkillRotation()
