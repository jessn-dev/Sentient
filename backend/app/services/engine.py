import pandas as pd
import requests
import logging
from bs4 import BeautifulSoup
from prophet import Prophet
from textblob import TextBlob
from sklearn.metrics import mean_absolute_error
import yfinance as yf

from alpaca.data.requests import StockSnapshotRequest
from app.schemas import (
    StockRequest, PredictionResponse, TechnicalSignals,
    SentimentAnalysis, NewsItem, LiquidityData,
    MoverItem, MarketMoversResponse,
    RealTimeMarketData, OptionStats, FundHolder
)
from .providers import DataProvider

logger = logging.getLogger(__name__)

# ✅ CONFIG: The specific tickers to track for Market Movers
MOVERS_WATCHLIST = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AMD', 'BRK-B', 'LLY']


class PredictionEngine:

    def __init__(self, data_client=None, trading_client=None):
        self.provider = DataProvider(data_client)
        self.trading_client = trading_client

    def _get_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://finviz.com/"
        }

    def _get_tv_symbol(self, symbol: str) -> str:
        symbol = symbol.upper()
        if "-" in symbol and "USD" in symbol: return f"COINBASE:{symbol.split('-')[0]}USD"
        return f"NYSE:{symbol}" if len(symbol) <= 3 else f"NASDAQ:{symbol}"

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
        except Exception as e:
            logger.warning(f"⚠️ Google News Scrape failed for {symbol}: {e}")
            return []

    def _fetch_market_data_unified(self) -> list[MoverItem]:
        """
        Attempts to fetch mover data for the specific watchlist.
        Priority: Finviz Scrape -> YFinance Fallback.
        """
        items = []

        # --- STRATEGY 1: Finviz Scrape (Preferred for real-time volume/change) ---
        try:
            # Construct URL for specific tickers
            tickers_param = ",".join(MOVERS_WATCHLIST)
            url = f"https://finviz.com/screener.ashx?v=111&t={tickers_param}"

            logger.info(f"🕷️ Scraping Finviz Watchlist: {url}")
            resp = requests.get(url, headers=self._get_headers(), timeout=8)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")

                # ✅ FIX: Combine rows instead of short-circuiting with 'or'
                rows = soup.find_all("tr", class_="table-dark-row-cp") + \
                       soup.find_all("tr", class_="table-light-row-cp")

                # Fallback selectors if specific classes fail
                if not rows:
                    rows = soup.select("tr.styled-row")

                # Final fallback: generic table scraping
                if not rows:
                    screener = soup.find("div", id="screener-content")
                    if screener:
                        rows = [r for r in screener.find_all("tr") if len(r.find_all("td")) > 10]

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > 10:
                        try:
                            # Finviz Columns (v=111): 1=Symbol, 8=Price, 9=Change%, 10=Volume
                            symbol = cols[1].text.strip()
                            price = float(cols[8].text.strip())
                            change_pct = float(cols[9].text.strip().replace('%', ''))

                            # Handle Volume (e.g., "20.5M")
                            vol_str = cols[10].text.strip()
                            if 'M' in vol_str:
                                volume = float(vol_str.replace('M', '')) * 1_000_000
                            elif 'B' in vol_str:
                                volume = float(vol_str.replace('B', '')) * 1_000_000_000
                            else:
                                volume = float(vol_str.replace(',', ''))

                            items.append(MoverItem(
                                symbol=symbol,
                                price=price,
                                change_pct=change_pct,
                                volume=cols[10].text.strip()  # Keep string format for display
                            ))
                        except Exception:
                            continue

            if items:
                logger.info(f"✅ Finviz Success: Retrieved {len(items)} tickers")
                return items

        except Exception as e:
            logger.warning(f"⚠️ Finviz Failed: {e}")

        # --- STRATEGY 2: YFinance Fallback ---
        logger.info("🔄 Switching to YFinance Fallback...")
        try:
            data = yf.download(MOVERS_WATCHLIST, period="2d", progress=False)['Close']

            # If only one ticker, yfinance returns a Series, not DataFrame
            is_series = isinstance(data, pd.Series)

            for t in MOVERS_WATCHLIST:
                try:
                    # Handle single vs multi-column response
                    if is_series and t == MOVERS_WATCHLIST[0]:
                        price = float(data.iloc[-1])
                        prev = float(data.iloc[-2])
                    elif t in data:
                        price = float(data[t].iloc[-1])
                        prev = float(data[t].iloc[-2])
                    else:
                        continue

                    change = ((price - prev) / prev) * 100
                    items.append(MoverItem(
                        symbol=t,
                        price=round(price, 2),
                        change_pct=round(change, 2),
                        volume="High"  # YF Close data doesn't imply volume easily without extra calls
                    ))
                except:
                    continue
            return items
        except Exception as e:
            logger.error(f"❌ YFinance Fallback Failed: {e}")
            return []

    def get_market_movers(self) -> MarketMoversResponse:
        """
        Orchestrates the fetching and sorting of market movers.
        """
        # 1. Fetch All Data (Unified)
        all_movers = self._fetch_market_data_unified()

        if not all_movers:
            return MarketMoversResponse(gainers=[], losers=[], active=[])

        # 2. Sort In-Memory (No extra API calls)
        # Gainers: Highest % Change
        gainers = sorted(all_movers, key=lambda x: x.change_pct, reverse=True)[:3]

        # Losers: Lowest % Change
        losers = sorted(all_movers, key=lambda x: x.change_pct, reverse=False)[:3]

        # Active: For Finviz, we sort by parsed volume. For YF, we just take top tickers.
        try:
            # Helper to parse volume string back to float for sorting
            def parse_vol(v_str):
                if v_str == "High": return 0
                v = v_str.replace(',', '')
                if 'M' in v: return float(v.replace('M', '')) * 1_000_000
                if 'B' in v: return float(v.replace('B', '')) * 1_000_000_000
                return float(v)

            active = sorted(all_movers, key=lambda x: parse_vol(x.volume), reverse=True)[:5]
        except:
            active = all_movers[:5]

        return MarketMoversResponse(gainers=gainers, losers=losers, active=active)

    def predict(self, request: StockRequest) -> PredictionResponse:
        logger.info(f"🧠 Engine: Starting analysis for {request.symbol} ({request.days} days)")

        # 1. Fetch History
        df, source = self.provider.fetch_history(request.symbol, days=730)
        current_price = df.iloc[-1]['y']

        # 2. Prophet
        try:
            m = Prophet(daily_seasonality=True)
            m.fit(df)
            future = m.make_future_dataframe(periods=request.days)
            forecast = m.predict(future)
            pred_price = forecast.iloc[-1]['yhat']
        except Exception as e:
            logger.error(f"❌ Prophet Model Failed: {e}")
            raise e

        # 3. Fetch Company Name
        company_name = request.symbol
        if self.trading_client:
            try:
                alpaca_sym = request.symbol.replace('-', '.')
                asset = self.trading_client.get_asset(alpaca_sym)
                if asset.name: company_name = asset.name
            except:
                pass

        if company_name == request.symbol:
            try:
                i = yf.Ticker(request.symbol).info
                company_name = i.get('longName') or i.get('shortName') or request.symbol
            except:
                pass

        # 4. Mock Technicals (Placeholders)
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

        logger.info(f"✅ Analysis Complete: {request.symbol} -> {pred_price:.2f} (Conf: {confidence:.1f}%)")

        return PredictionResponse(
            symbol=request.symbol.upper(),
            company_name=company_name,
            tv_symbol=self._get_tv_symbol(request.symbol),
            current_price=current_price,
            predicted_price=pred_price,
            forecast_date=forecast.iloc[-1]['ds'].date(),
            confidence_score=round(confidence, 1),
            explanation=detailed_explanation,
            technicals=technicals, sentiment=sentiment, liquidity=liquidity
        )

    def fetch_real_time_data(self, symbol: str) -> RealTimeMarketData:
        logger.info(f"📊 MarketData: Fetching Real-Time Stats for {symbol}...")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 1. Basic Stats
            mkt_cap = info.get('marketCap', 0)
            short_float = info.get('shortPercentOfFloat', 0) * 100 if info.get('shortPercentOfFloat') else 0.0
            inst_own = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0.0

            # 2. Options Data (Put/Call Ratio)
            opt_stats = None
            try:
                exp_dates = ticker.options
                if exp_dates:
                    nearest = exp_dates[0]
                    chain = ticker.option_chain(nearest)
                    calls = chain.calls
                    puts = chain.puts

                    call_vol = calls['volume'].sum() if not calls.empty else 0
                    put_vol = puts['volume'].sum() if not puts.empty else 0

                    # Avoid division by zero
                    pc_ratio = round(put_vol / call_vol, 2) if call_vol > 0 else 0.0

                    # Estimate IV (Average of ATM options)
                    iv = 0.0
                    if not calls.empty:
                        iv = calls['impliedVolatility'].mean() * 100  # Avg IV

                    opt_stats = OptionStats(
                        put_call_ratio=pc_ratio,
                        total_call_vol=int(call_vol),
                        total_put_vol=int(put_vol),
                        implied_volatility=round(iv, 2),
                        nearest_expiry=nearest
                    )
                    logger.info(f"   🎯 Options: P/C Ratio {pc_ratio} | Vol: {call_vol}C / {put_vol}P")
            except Exception as e:
                logger.warning(f"   ⚠️ Options Data Failed: {e}")

            # 3. Fund Flows (Institutional Holders)
            holders = []
            try:
                # yfinance returns a dataframe for institutional_holders
                inst_holders = ticker.institutional_holders
                if inst_holders is not None and not inst_holders.empty:
                    for _, row in inst_holders.head(5).iterrows():
                        holders.append(FundHolder(
                            holder=row.get('Holder', 'Unknown'),
                            shares=int(row.get('Shares', 0)),
                            date_reported=str(row.get('Date Reported', '')),
                            percent_out=float(row.get('% Out', 0)) * 100 if row.get('% Out') else 0.0
                        ))
                logger.info(f"   🏦 Fund Flows: Found {len(holders)} major holders")
            except Exception as e:
                logger.warning(f"   ⚠️ Fund Flow Data Failed: {e}")

            return RealTimeMarketData(
                symbol=symbol,
                market_cap=mkt_cap,
                short_float=round(short_float, 2),
                institutional_ownership=round(inst_own, 2),
                options_sentiment=opt_stats,
                top_holders=holders
            )

        except Exception as e:
            logger.error(f"❌ MarketData Fetch Fatal Error: {e}")
            # Return empty/safe object on crash
            return RealTimeMarketData(
                symbol=symbol, market_cap=0, short_float=0,
                institutional_ownership=0, options_sentiment=None, top_holders=[]
            )