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

from .schemas import (
    StockRequest, PredictionResponse, TechnicalSignals,
    SentimentAnalysis, NewsItem, LiquidityData,
    MoverItem, MarketMoversResponse
)
from .providers import DataProvider

class PredictionEngine:

    def __init__(self, alpaca_client=None):
        self.provider = DataProvider(alpaca_client)

    def _get_headers(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
        ]
        return {"User-Agent": random.choice(user_agents)}

    def _get_tv_symbol(self, symbol: str) -> str:
        symbol = symbol.upper()
        if "-" in symbol and "USD" in symbol: return f"COINBASE:{symbol.split('-')[0]}USD"
        return f"NYSE:{symbol}" if len(symbol) <= 3 else f"NASDAQ:{symbol}"

    # --- SCRAPERS ---
    def _scrape_google_news(self, symbol: str) -> list:
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
        except: return []

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
                cap = val * (1e12 if cap_str[-1]=='T' else 1e9 if cap_str[-1]=='B' else 1e6)
            if vol_str and vol_str[-1] in 'MK':
                val = float(vol_str[:-1])
                vol = val * (1e6 if vol_str[-1]=='M' else 1e3)
            return cap, vol
        except: return 0, 0

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
                            change_pct=float(cols[9].text.strip().replace('%','')),
                            volume=cols[10].text.strip()
                        ))
                    except: continue
            return movers
        except: return []

    def _get_fallback_movers(self):
        tickers = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AMD', 'BRK-B', 'LLY']
        if self.provider.alpaca:
            print("🔌 [MOVERS] Fetching Fallback Movers from Alpaca...")
            try:
                alpaca_tickers = [t.replace('-', '.') for t in tickers]
                snapshots = self.provider.alpaca.get_snapshots(alpaca_tickers)
                items = []
                for sym, snap in snapshots.items():
                    clean_sym = sym.replace('.', '-')
                    price = float(snap.latest_trade.price)
                    prev_close = float(snap.daily_bar.c) if snap.daily_bar else price
                    if snap.prev_daily_bar: prev_close = float(snap.prev_daily_bar.c)
                    change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
                    items.append({"symbol": clean_sym, "price": price, "change_pct": change, "volume": "High"})
                items.sort(key=lambda x: x['change_pct'], reverse=True)
                to_obj = lambda lst: [MoverItem(symbol=x['symbol'], price=round(x['price'],2), change_pct=round(x['change_pct'],2), volume=x['volume']) for x in lst]
                return MarketMoversResponse(gainers=to_obj(items[:3]), losers=to_obj(items[-3:]), active=to_obj(items[:5]))
            except: pass

        try:
            data = yf.download(tickers, period="2d", progress=False)['Close']
            items = []
            for t in tickers:
                try:
                    price = float(data[t].iloc[-1])
                    prev = float(data[t].iloc[-2])
                    change = ((price - prev)/prev)*100
                    items.append({"symbol": t, "price": price, "change_pct": change, "volume": "High"})
                except: continue
            items.sort(key=lambda x: x['change_pct'], reverse=True)
            to_obj = lambda lst: [MoverItem(symbol=x['symbol'], price=round(x['price'],2), change_pct=round(x['change_pct'],2), volume=x['volume']) for x in lst]
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

        # 3. Technicals
        combined = pd.concat([df['y'], forecast.iloc[-len(df):]['yhat']], ignore_index=True)
        sma_50 = combined.rolling(50).mean().iloc[-1]
        sma_200 = combined.rolling(200).mean().iloc[-1]
        delta = combined.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        sma_20 = combined.rolling(20).mean().iloc[-1]
        std_20 = combined.rolling(20).std().iloc[-1]
        upper, lower = sma_20 + (std_20*2), sma_20 - (std_20*2)
        trend = "Bullish" if current_price > sma_50 else "Bearish"
        if current_price > sma_50 and sma_50 > sma_200: trend = "Strong Uptrend"

        technicals = TechnicalSignals(
            sma_50=round(sma_50,2), sma_200=round(sma_200,2), rsi=round(rsi,2),
            bollinger_upper=round(upper,2), bollinger_lower=round(lower,2),
            trend_signal=trend,
            rsi_signal="Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral",
            bollinger_signal="Breakout" if current_price>=upper else "Breakdown" if current_price<=lower else "Normal"
        )

        # 4. Sentiment
        sent_news = []
        try:
            yf_news = yf.Ticker(request.symbol).news
            for n in yf_news[:5]:
                blob = TextBlob(n['title'])
                pub = datetime.fromtimestamp(n['providerPublishTime']).strftime('%Y-%m-%d')
                sent_news.append(NewsItem(title=n['title'], link=n['link'], published=pub, sentiment="Positive" if blob.sentiment.polarity>0.1 else "Negative" if blob.sentiment.polarity<-0.1 else "Neutral"))
        except: pass
        if not sent_news: sent_news = self._scrape_google_news(request.symbol)
        score = sum([0.5 if n.sentiment=="Positive" else -0.5 if n.sentiment=="Negative" else 0 for n in sent_news]) / max(1, len(sent_news))
        sentiment = SentimentAnalysis(score=round(score,2), label="Bullish" if score>0.1 else "Bearish" if score<-0.1 else "Neutral", news=sent_news)

        # 5. Liquidity & Company Name (UPDATED)
        vol, cap, spread = 0, 0, 0
        company_name = request.symbol # Default

        # --- STRATEGY: TRY ALPACA NAME FIRST ---
        if self.provider.alpaca:
            try:
                # Alpaca asset endpoint is instant and not rate-limited
                asset = self.provider.alpaca.get_asset(request.symbol.replace('-', '.'))
                company_name = asset.name
            except Exception as e:
                print(f"Alpaca Name Fetch Error: {e}")

        # --- FALLBACK: TRY YAHOO IF ALPACA FAILED ---
        if company_name == request.symbol:
            try:
                # We skip .info if we know Yahoo is blocking us, but try one last time
                i = yf.Ticker(request.symbol).info
                company_name = i.get('longName') or i.get('shortName') or request.symbol
                vol, cap = i.get('averageVolume10days',0), i.get('marketCap',0)
                bid, ask = i.get('bid',0), i.get('ask',0)
                if ask and bid: spread = round(((ask-bid)/ask)*100, 4)
            except: pass

        if vol == 0: cap, vol = self._scrape_finviz_liquidity(request.symbol)

        liquidity = LiquidityData(
            avg_volume=vol, market_cap=cap, bid_ask_spread=spread if spread>0 else None,
            liquidity_rating="High (Institutional)" if cap > 10e9 and vol > 1e6 else "Low (Illiquid)",
            slippage_risk="Low" if vol > 500000 else "High"
        )

        mae = mean_absolute_error(df['y'], forecast.iloc[:len(df)]['yhat'])
        confidence = max(0, min(100, 100 * (1 - (mae/current_price))))

        return PredictionResponse(
            symbol=request.symbol.upper(),
            company_name=company_name,
            tv_symbol=self._get_tv_symbol(request.symbol),
            current_price=current_price,
            predicted_price=pred_price,
            forecast_date=forecast.iloc[-1]['ds'].date(),
            confidence_score=round(confidence, 1),
            explanation=f"Forecast based on {len(df)} days of data from {source}.",
            technicals=technicals, sentiment=sentiment, liquidity=liquidity
        )