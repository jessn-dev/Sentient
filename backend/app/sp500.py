import pandas as pd
import requests
from io import StringIO
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache
_sp500_cache = {"data": set(), "expires": datetime.min}

def get_sp500_tickers():
    """
    Fetches the S&P 500 tickers from Wikipedia using a proper User-Agent.
    """
    global _sp500_cache
    now = datetime.now()

    # 1. Check Cache
    if now < _sp500_cache["expires"] and _sp500_cache["data"]:
        return _sp500_cache["data"]

    try:
        # 2. Fetch with Headers (Fixes 403 Forbidden)
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {
            "User-Agent": "SentientAI (Educational Project; contact@example.com)"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise error if 403/404

        # 3. Parse HTML
        # Wrap HTML string in StringIO because Pandas deprecates raw strings
        html_data = StringIO(response.text)
        tables = pd.read_html(html_data)
        df = tables[0]

        # 4. Extract Symbols
        tickers = set(df['Symbol'].tolist())

        # Add ETF equivalents
        tickers.add("SPY")
        tickers.add("IVV")
        tickers.add("VOO")

        # Update Cache
        _sp500_cache["data"] = tickers
        _sp500_cache["expires"] = now + timedelta(hours=24)

        print(f"✅ S&P 500 List Updated ({len(tickers)} symbols)")
        return tickers

    except Exception as e:
        print(f"⚠️ Failed to fetch S&P 500 list: {e}")
        # Fallback: If live fetch fails, allow LLY and others temporarily
        # Ideally, you'd load a local static CSV here as a backup
        fallback = {
            "SPY", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META",
            "TSLA", "AMD", "JPM", "V", "LLY", "AVGO", "WMT", "XOM"
        }
        return fallback

def is_sp500(symbol: str) -> bool:
    """Case-insensitive check."""
    valid_tickers = get_sp500_tickers()
    return symbol.upper() in valid_tickers