import feedparser
import logging
# import praw  <-- DISABLED
from fredapi import Fred
import os
from textblob import TextBlob
import urllib.parse
from datetime import datetime

# Configure Logger
logger = logging.getLogger(__name__)

# Configure APIs
# REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
# REDDIT_SECRET = os.environ.get("REDDIT_SECRET")
FRED_API_KEY = os.environ.get("FRED_API_KEY")


class MarketIntelligence:
    # Keywords that trigger a "Lawsuit" flag
    LAWSUIT_KEYWORDS = [
        "lawsuit", "sue", "litigation", "class action",
        "settlement", "legal action", "fraud", "investigation",
        "subpoena", "allegation", "court", "trial"
    ]

    def __init__(self):
        self.reddit = None
        # DISABLED REDDIT INITIALIZATION
        # if REDDIT_CLIENT_ID:
        #     self.reddit = praw.Reddit(
        #         client_id=REDDIT_CLIENT_ID,
        #         client_secret=REDDIT_SECRET,
        #         user_agent="sentient-app/1.0"
        #     )

        self.fred = None
        if FRED_API_KEY:
            self.fred = Fred(api_key=FRED_API_KEY)
            logger.info("✅ [INTEL] FRED API Connected")
        else:
            logger.warning("⚠️ [INTEL] FRED API Key missing. Macro data will be empty.")

    def get_company_rss(self, symbol: str):
        """
        Dynamically builds an RSS feed for the company using Google News.
        """
        query = f"{symbol} Investor Relations"
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        logger.info(f"📰 Fetching RSS News for {symbol}...")
        return self.analyze_rss(rss_url, source_label="Google News (IR)")

    def analyze_rss(self, rss_url: str, source_label="RSS"):
        """Fetches and analyzes sentiment from the generated RSS feed"""
        try:
            feed = feedparser.parse(rss_url)
            results = []

            # Limit to top 5
            for entry in feed.entries[:5]:
                text_content = f"{entry.title}. {entry.description}" if hasattr(entry, 'description') else entry.title
                blob = TextBlob(text_content)
                text_lower = text_content.lower()

                # 1. Base Sentiment Analysis
                polarity = blob.sentiment.polarity
                if polarity > 0.1:
                    sent_label = "positive"
                elif polarity < -0.1:
                    sent_label = "negative"
                else:
                    sent_label = "neutral"

                # 2. Subjectivity Check (Informative vs Emotional)
                msg_type = "emotional" if blob.sentiment.subjectivity > 0.7 else "informative"

                # 3. ⚖️ LAWSUIT / LEGAL CHECK (Override)
                is_legal_trouble = any(kw in text_lower for kw in self.LAWSUIT_KEYWORDS)

                if is_legal_trouble:
                    sent_label = "negative"
                    msg_type = "informative"
                    logger.warning(f"⚖️ LEGAL ALERT DETECTED in article: {entry.title[:30]}...")

                results.append({
                    "id": entry.get("id", entry.link),
                    "text": entry.title,
                    "sentiment": sent_label,
                    "type": msg_type,
                    "source": source_label,
                    "url": entry.link,
                    "timestamp": entry.get("published", ""),
                    "is_lawsuit": is_legal_trouble
                })

            logger.info(f"   ✅ Parsed {len(results)} RSS articles")
            return results

        except Exception as e:
            logger.error(f"❌ RSS Parse Error: {e}")
            return []

    def analyze_reddit(self, ticker: str):
        """
        Scans r/stocks and r/wallstreetbets for ticker mentions.
        DISABLED: Returns empty list.
        """
        return []

    def get_macro_data(self):
        """Fetches key economic indicators from Federal Reserve (FRED)"""
        if not self.fred:
            return {}

        try:
            logger.info("🇺🇸 Fetching Macro Data from FRED...")

            # 1. We fetch the CPI series.
            # 2. We explicitly call .ffill() (Forward Fill) to fill any missing data points with the previous known value.
            # 3. We then calculate pct_change().
            # This satisfies the Pandas warning by explicitly handling the missing data "prior to calling pct_change".
            cpi_series = self.fred.get_series('CPIAUCSL')
            inflation_rate = cpi_series.ffill().pct_change(periods=12).iloc[-1] * 100

            data = {
                "gdp_growth": self.fred.get_series('GDP').iloc[-1],
                "inflation_rate": inflation_rate,
                "unemployment": self.fred.get_series('UNRATE').iloc[-1],
                "fed_funds_rate": self.fred.get_series('FEDFUNDS').iloc[-1]
            }
            logger.info("   ✅ Macro Data Retrieved")
            return data
        except Exception as e:
            logger.error(f"❌ FRED Data Error: {e}")
            return {}