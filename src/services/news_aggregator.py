"""News aggregation service"""

import logging
from datetime import datetime
from typing import List, Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from src.models.database_models import ResearchArticle
from src.services.ollama import ollama_service
from src.models.research import article as article_db 

logger = logging.getLogger(__name__)


class NewsAggregator:
    """Service for aggregating tech news from multiple sources"""

    # RSS feeds
    RSS_FEEDS = {
        "hacker_news": "https://news.ycombinator.com/rss",
        "medium": "https://medium.com/feed/tag/backend",
        "dev_to": "https://dev.to/api/articles?tags=backend",
    }

    @staticmethod
    async def fetch_from_hacker_news(db: Session, limit: int = 10) -> List[ResearchArticle]:
        """Fetch from Hacker News RSS"""
        articles = []
        try:
            feed = feedparser.parse(NewsAggregator.RSS_FEEDS["hacker_news"])

            for entry in feed.entries[:limit]:
                # Check if article already exists
                _, error = article_db.get_research_article_by_url(db, entry.link)
                if error:
                    logger.warning(f"Article already exists in DB: {entry.link}")
                    article = ResearchArticle(
                        source="hacker_news",
                        title=entry.title,
                        url=entry.link,
                        published_at=datetime(*entry.published_parsed[:6]) if entry.get("published_parsed") else None,
                    )
                    articles.append(article)
                    logger.info(f"Added HN article: {entry.title[:50]}...")
        except Exception as e:
            logger.error(f"Error fetching Hacker News: {e}")

        return articles

    @staticmethod
    async def fetch_from_medium(db: Session, limit: int = 10) -> List[ResearchArticle]:
        """Fetch from Medium"""
        articles = []
        try:
            feed = feedparser.parse(NewsAggregator.RSS_FEEDS["medium"])

            for entry in feed.entries[:limit]:
                _, error = article_db.get_research_article_by_url(db, link=entry.link)
                if error:
                    logger.warning(f"Article already exists in DB: {entry.link}")
                    article = ResearchArticle(
                        source="medium",
                        title=entry.title,
                        url=entry.link,
                        published_at=datetime(*entry.published_parsed[:6]) if entry.get("published_parsed") else None,
                    )
                    articles.append(article)
                    logger.info(f"Added Medium article: {entry.title[:50]}...")
        except Exception as e:
            logger.error(f"Error fetching Medium: {e}")

        return articles

    @staticmethod
    async def fetch_from_dev_to(db: Session, limit: int = 10) -> List[ResearchArticle]:
        """Fetch from Dev.to"""
        articles = []
        try:
            response = requests.get(f"{NewsAggregator.RSS_FEEDS['dev_to']}&limit={limit}", timeout=60)
            response.raise_for_status()

            data = response.json()

            for item in data[:limit]:
                _, error = article_db.get_research_article_by_url(db, link=item.get("url"))

                if error:
                    logger.warning(f"Article already exists in DB: {item.get('url')}")
                    article = ResearchArticle(
                        source="dev_to",
                        title=item.get("title", "No title"),
                        url=item.get("url", ""),
                        published_at=datetime.fromisoformat(item.get("published_at", "").replace("Z", "+00:00")),
                    )
                    articles.append(article)
                    logger.info(f"Added Dev.to article: {item.get('title', 'N/A')[:50]}...")
        except Exception as e:
            logger.error(f"Error fetching Dev.to: {e}")

        return articles

    @staticmethod
    async def fetch_article_content(url: str, timeout: int = 60) -> Optional[str]:
        """Fetch full article content from URL"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)

            # Truncate to first 2000 characters for processing
            return text[:2000] if len(text) > 0 else None
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None

    @staticmethod
    async def aggregate_daily(db: Session) -> int:
        """
        Run daily aggregation from all sources

        Returns:
            Number of new articles added
        """
        articles_to_add = []

        logger.info("Starting daily news aggregation...")

        # Fetch from all sources
        hn_articles = await NewsAggregator.fetch_from_hacker_news(db)
        articles_to_add.extend(hn_articles)

        medium_articles = await NewsAggregator.fetch_from_medium(db)
        articles_to_add.extend(medium_articles)

        dev_articles = await NewsAggregator.fetch_from_dev_to(db)
        articles_to_add.extend(dev_articles)

        # Add to database
        for article in articles_to_add:
            db.add(article)

        db.commit()
        logger.info(f"Aggregated {len(articles_to_add)} new articles")

        return len(articles_to_add)

    @staticmethod
    async def process_articles_with_ai(db: Session, limit: int = 20) -> int:
        """
        Process unprocessed articles with AI summarization

        Returns:
            Number of articles processed
        """
        # Get unprocessed articles
        processed_count = 0
        unprocessed, error = article_db.get_unprocessed_articles(db, limit)
        if error:
            logger.error(f"Error fetching unprocessed articles: {error}")
            return processed_count

        for article in unprocessed:
            try:
                # Fetch content
                content = await NewsAggregator.fetch_article_content(article.url)

                if content:
                    article.original_content = content

                    # Generate summary
                    summary = ollama_service.summarize_sync(content)
                    if summary:
                        article.ai_summary = summary
                        # Short version for API
                        article.ai_summary_short = summary[:200] + "..." if len(summary) > 200 else summary

                    # Extract keywords
                    keywords = ollama_service.extract_keywords_sync(content)
                    if keywords:
                        article.keywords = ", ".join(keywords)

                    article.processed_at = datetime.utcnow()

                    db.commit()
                    processed_count += 1
                    logger.info(f"Processed: {article.title[:50]}...")

            except Exception as e:
                logger.error(f"Error processing {article.title}: {e}")

        logger.info(f"Processed {processed_count} articles with AI")
        return processed_count


# Global instance
news_aggregator = NewsAggregator()
