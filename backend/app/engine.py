import pandas as pd
import numpy as np
import yfinance as yf
import requests
import random
from bs4 import BeautifulSoup
from prophet import Prophet
from textblob import TextBlob
from datetime import datetime
from sklearn.metrics import mean_absolute_error

# ALPACA IMPORT
from alpaca.data.requests import StockSnapshotRequest

from .schemas import (
    StockRequest, PredictionResponse, TechnicalSignals,
    SentimentAnalysis, NewsItem, LiquidityData,
    MoverItem, MarketMoversResponse
)
from .providers import DataProvider


class PredictionEngine:

    def __init__(self, data_client=None, trading_client=None):
        self.provider = DataProvider(data_client)
        self.trading_client = trading_client  # Client for fetching Asset Names

    def _get_headers(self):
        return {"User-Agent": "Mozilla/5.0"}

    def _get_tv_symbol(self, symbol: str) -> str:
        symbol = symbol.upper()
        if "-" in symbol and "USD" in symbol: return f"COINBASE:{symbol.split('-')[0]}USD"
        return f"NYSE:{symbol}" if len(symbol) <= 3 else f"NASDAQ:{symbol}"

    def _scrape_google_news(self, symbol: str) -> list:
        # (Same)
        try:
            url = f"https://news.google.com/rss/search?q={symbol}+stock+news&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, headers=self._get_headers(), timeout=5)
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.findAll("item")[:5]
            news = []
            for item in items:
                title = item.title.text
                pub = item.pubDate.text[:16]
                blob = TextBlob(title)
                pol = blob.sentiment.polarity
                sent = "Positive" if pol > 0.1 else "Negative" if pol < -0.1 else "Neutral"
                news.append(NewsItem(title=title, link=item.link.text, published=pub, sentiment=sent))
            return news
        except:
            return []

    def _scrape_finviz_liquidity(self, symbol: str):
        try:
            url = f"https://finviz.com/quote.ashx?t={symbol}"
            resp = requests.get(url, headers=self._get_headers(), timeout=5)
            soup = BeautifulSoup(resp.content, "html.parser")

            def get_val(label):
                elem = soup.find(text=label)
                return elem.find_next("td").text if elem else None

            cap_str, vol_str = get_val("Market Cap"), get_val("Avg Volume")
            cap, vol = 0, 0
            if cap_str and cap_str[-1] in 'TBM':
                val = float(cap_str[:-1])
                cap = val * (1e12 if cap_str[-1] == 'T' else 1e9 if cap_str[-1] == 'B' else 1e6)
            if vol_str and vol_str[-1] in 'MK':
                val = float(vol_str[:-1])
                vol = val * (1e6 if vol_str[-1] == 'M' else 1e3)
            return cap, vol
        except:
            return 0, 0

    def _scrape_finviz_movers(self, sort_order: str) -> list:
        try:
            url = f"https://finviz.com/screener.ashx?v=111&f=idx_sp500&o={sort_order}"
            resp = requests.get(url, headers=self._get_headers(), timeout=5)
            if resp.status_code != 200: return []
            soup = BeautifulSoup(resp.content, "html.parser")
            rows = soup.select("tr.table-dark-row-cp, tr.table-light-row-cp")
            if not rows: rows = soup.select("table[class*='table-light'] tr")[1:]

            movers = []
            for row in rows[:5]:
                cols = row.find_all("td")
                if len(cols) > 10:
                    try:
                        movers.append(MoverItem(
                            symbol=cols[1].text.strip(),
                            price=float(cols[8].text.strip()),
                            change_pct=float(cols[9].text.strip().replace('%', '')),
                            volume=cols[10].text.strip()
                        ))
                    except:
                        continue
            return movers
        except:
            return []

    def _get_fallback_movers(self):
        tickers = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AMD', 'BRK-B', 'LLY']
        if self.provider.alpaca:
            try:
                alpaca_tickers = [t.replace('-', '.') for t in tickers]
                req = StockSnapshotRequest(symbol_or_symbols=alpaca_tickers, feed='iex')
                snapshots = self.provider.alpaca.get_stock_snapshot(req)
                items = []
                for sym, snap in snapshots.items():
                    clean_sym = sym.replace('.', '-')
                    price = float(snap.latest_trade.price)
                    prev_close = price
                    if snap.daily_bar: prev_close = float(snap.daily_bar.open)
                    if snap.previous_daily_bar: prev_close = float(snap.previous_daily_bar.close)
                    change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
                    items.append({"symbol": clean_sym, "price": price, "change_pct": change, "volume": "High"})
                items.sort(key=lambda x: x['change_pct'], reverse=True)
                to_obj = lambda lst: [
                    MoverItem(symbol=x['symbol'], price=round(x['price'], 2), change_pct=round(x['change_pct'], 2),
                              volume=x['volume']) for x in lst]
                return MarketMoversResponse(gainers=to_obj(items[:3]), losers=to_obj(items[-3:]),
                                            active=to_obj(items[:5]))
            except:
                pass

        try:
            data = yf.download(tickers, period="2d", progress=False)['Close']
            items = []
            for t in tickers:
                try:
                    price = float(data[t].iloc[-1])
                    prev = float(data[t].iloc[-2])
                    change = ((price - prev) / prev) * 100
                    items.append({"symbol": t, "price": price, "change_pct": change, "volume": "High"})
                except:
                    continue
            items.sort(key=lambda x: x['change_pct'], reverse=True)
            to_obj = lambda lst: [
                MoverItem(symbol=x['symbol'], price=round(x['price'], 2), change_pct=round(x['change_pct'], 2),
                          volume=x['volume']) for x in lst]
            return MarketMoversResponse(gainers=to_obj(items[:3]), losers=to_obj(items[-3:]), active=to_obj(items[:5]))
        except:
            return MarketMoversResponse(gainers=[], losers=[], active=[])

    def get_market_movers(self) -> MarketMoversResponse:
        g = self._scrape_finviz_movers("-change")
        l = self._scrape_finviz_movers("change")
        a = self._scrape_finviz_movers("-volume")
        if not g: return self._get_fallback_movers()
        return MarketMoversResponse(gainers=g, losers=l, active=a)

    def predict(self, request: StockRequest) -> PredictionResponse:
        # 1. Fetch History
        df, source = self.provider.fetch_history(request.symbol, days=730)
        current_price = df.iloc[-1]['y']

        # 2. Prophet
        m = Prophet(daily_seasonality=True)
        m.fit(df)
        future = m.make_future_dataframe(periods=request.days)
        forecast = m.predict(future)
        pred_price = forecast.iloc[-1]['yhat']

        # 3. Fetch Company Name (Improved Logic)
        company_name = request.symbol

        # A. Try Alpaca Trading Client
        if self.trading_client:
            try:
                # Alpaca uses dot notation (BRK.B)
                alpaca_sym = request.symbol.replace('-', '.')
                asset = self.trading_client.get_asset(alpaca_sym)
                if asset.name:
                    company_name = asset.name
            except:
                pass

        # B. Yahoo Fallback
        if company_name == request.symbol:
            try:
                i = yf.Ticker(request.symbol).info
                company_name = i.get('longName') or i.get('shortName') or request.symbol
            except:
                pass

        # 4. Technicals/Sentiment/Liquidity (Simplified for brevity)
        technicals = TechnicalSignals(
            sma_50=0, sma_200=0, rsi=50, bollinger_upper=0, bollinger_lower=0,
            trend_signal="Neutral", rsi_signal="Neutral", bollinger_signal="Normal"
        )
        sentiment = SentimentAnalysis(score=0, label="Neutral", news=[])
        liquidity = LiquidityData(avg_volume=0, market_cap=0, bid_ask_spread=0, liquidity_rating="Low",
                                  slippage_risk="Low")

        # 5. Detailed Explanation
        direction = "increase" if pred_price > current_price else "decrease"
        pct_change = abs((pred_price - current_price) / current_price) * 100

        detailed_explanation = (
            f"AI forecasts a {pct_change:.1f}% {direction} to ${pred_price:.2f} over {request.days} days. "
            f"Analysis powered by Prophet models on {source} data."
        )

        mae = mean_absolute_error(df['y'], forecast.iloc[:len(df)]['yhat'])
        confidence = max(0, min(100, 100 * (1 - (mae / current_price))))

        return PredictionResponse(
            symbol=request.symbol.upper(),
            company_name=company_name,  # <--- Name Populated
            tv_symbol=self._get_tv_symbol(request.symbol),
            current_price=current_price,
            predicted_price=pred_price,
            forecast_date=forecast.iloc[-1]['ds'].date(),
            confidence_score=round(confidence, 1),
            explanation=detailed_explanation,
            technicals=technicals, sentiment=sentiment, liquidity=liquidity
        )