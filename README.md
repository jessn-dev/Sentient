
## License

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.14-yellow.svg)
![Next.js](https://img.shields.io/badge/next.js-16.1-black.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)

# Sentient AI

Sentient AI is a full-stack financial intelligence platform designed to provide AI-powered stock market predictions, real-time market data analysis, and portfolio tracking. The system leverages machine learning (Prophet) for price forecasting and integrates with real-time financial data providers to offer actionable insights.

## Authors Note

- [@jessengolab](https://www.linkedin.com/in/jessengolab/)

I started this side project to gain insight into AI, ML, and Stock Forecasting ("between you and me, I still don't know anything about it 😄") and to fuel my passion for creating. If you are an engineer of any kind, I know you know the feeling. I've been putting this project off for some time now. Heck, I'm still wondering which features to add; it's titillating to think that a project I started might give someone a new idea. If this project might interest you, drop some stars ⭐⭐⭐. I would appreciate it 😄



## Features

Market Intelligence:

- Market Movers: Real-time tracking of top gainers, losers, and most active stocks.

- Stock History: Interactive charts with historical candle data.

AI Predictions:

- Price Forecasting: Generates 7-day price forecasts using the Prophet model.

- Deep Analysis: Provides AI-generated explanations for predicted trends.

Smart Watchlist:

- Performance Tracking: Monitors saved predictions against live market data.

- Accuracy Scoring: Automatically calculates and updates prediction accuracy (e.g., "Target Hit 🎯", "Off Track ⚠️").

Automated Maintenance:

- Validation: Scheduled tasks verify active predictions against daily closing prices.

- Cleanup: Automated removal of stale or "zombie" predictions.

## 🏗️ System Architecture

The application follows a modern Monorepo structure separating the backend services from the frontend user interface.

- Backend: FastAPI (Python) serving RESTful endpoints.

- Frontend: Next.js (TypeScript/React) for the user dashboard.

- Database: PostgreSQL (via Supabase) accessed using SQLModel (ORM).

External APIs:

- Alpaca Markets: Real-time stock prices and historical data.

- Upstash (QStash): Serverless scheduling for automated background tasks.

- Supabase Auth: User authentication and management.

## 🛠️ Tech Stack

Backend (/backend)
- Framework: FastAPI
- ORM: SQLModel (SQLAlchemy wrapper)
- Data Analysis: Pandas, yfinance, Prophet
- Testing: Pytest, TestClient

Frontend (/frontend)
- Framework: Next.js (App Router)
- Language: TypeScript
- Styling: Tailwind CSS
- State/Data: React Server Components (RSC) & Client Hooks

## Getting Started

Prerequisites
- Python 3.12+
- Node.js 18+
- Supabase Account
- Alpaca Markets Account (Free Tier)

Clone the project

```bash
  git clone https://link-to-project
```

Environment Variables

```bash
ALPACA_KEY=your_alpaca_key
ALPACA_SECRET=your_alpaca_secret
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
QSTASH_CURRENT_SIGNING_KEY=your_qstash_key
```

Installation

1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

🧪 Testing
The project uses a robust testing strategy with Integration Tests for the backend, ensuring API reliability and database integrity.

```bash
cd backend
python -m pytest
```
- Framework: pytest
- Strategy: Uses an in-memory SQLite database to isolate tests from production data.
- Coverage: Mocks external services (Supabase, Alpaca) to test business logic without hitting external APIs.

📊 Quality Assurance
Code quality is monitored via SonarQube Cloud with a CI-based analysis pipeline.
- Backend: Python coverage via pytest-cov (coverage.xml).
- Frontend: TypeScript coverage via lcov (lcov.info).

## ⚡ Smart Wake-Up Strategy (Cost Optimization)

To stay within Render's Free Tier limits (750 hours/month) while avoiding painful 50+ second "cold starts," I implemented a hybrid wake-up strategy.

### The Problem:

- Cold Starts: Render spins down free services after 15 minutes of inactivity. The next request can take nearly a minute to load.

- Usage Limits: Keeping the service alive 24/7 uses ~720 hours/month, leaving no margin for error.

The Solution: I used a Hybrid Approach combining a custom Python script with GitHub Actions to "pre-warm" the server only during business hours.

1. The Waker Script (backend/wake_up.py):

- A zero-dependency Python script using urllib.

- Implements Retry Logic to handle the initial timeout common during cold starts.

- Treats HTTP 404/500 as "Success" (proof the container is awake) to avoid unnecessary retries.

2. The Scheduler (GitHub Actions):

- Runs wake_up.py automatically at 8:00 AM UTC, Mon-Fri.

- Ensures the API is hot and ready before the developer starts working, but allows it to sleep at night to save resources.

Usage: The workflow is defined in .github/workflows/wake_up.yml and requires the NEXT_PUBLIC_API_URL secret.
## API Endpoints

|  Method | Endpoint  |  Description |
|---|---|---|
| GET  | /market/movers   |  Get top market movers (gainers/losers). |
| POST | /predict  | Generate a new stock price prediction.  |
| POST  |  /watchlist | Add a prediction to the user's watchlist.  |
| GET  |  /watchlist/performance |  Get accuracy stats for tracked stocks. |
| POST  |  /scheduler/validate |  Trigger validation of active predictions (Admin). |

## Lessons Learned

1. Reliable Integration Testing
One of the biggest challenges was ensuring the backend was robust without hitting the production database during tests.

- Solution: I implemented a custom client fixture in conftest.py that utilizes FastAPI's dependency_overrides.

- Outcome: By swapping the production Postgres session with an in-memory SQLite instance (sqlite://), we achieved fast, isolated integration tests that verify the full request lifecycle without risking data corruption.

2. Monorepo Quality Assurance
Managing code quality for both Python (Backend) and TypeScript (Frontend) in a single repository required a specialized setup.

- Solution: I configured SonarQube with a modular structure using sonar.modules=backend,frontend in the sonar-project.properties file.

- Outcome: This allowed us to apply distinct quality gates and coverage parsers (coverage.xml for Python, lcov.info for TS) to each part of the stack independently.

3. Resilient Data Fetching
Reliance on a single financial data provider can lead to failures if rate limits are hit or APIs go down.

- Solution: I built a hybrid fetching strategy in main.py. The system primarily attempts to fetch real-time data from Alpaca Markets but seamlessly falls back to Yahoo Finance (yfinance) if the primary source fails or returns missing data.

4. Serverless Automation
Instead of maintaining a perpetually running server for cron jobs (which is costly and prone to downtime), we decoupled the scheduling logic.

- Solution: I integrated Upstash (QStash) to trigger our /scheduler/validate and /scheduler/cleanup endpoints via webhooks.

- Outcome: This reduced infrastructure costs and ensured that prediction validation happens reliably via secure, signature-verified HTTP requests (Upstash-Signature).		


## FAQ

#### Why do my tests fail with "Not authenticated"?

Your API routes use Depends(get_current_user). In conftest.py, we use app.dependency_overrides to swap this dependency with a mock function that returns a fake user_id. If a test fails with 401, check if you accidentally cleared overrides or didn't use the client fixture.

#### Why does the chart sometimes show "Invalid environment" errors in the console?

This is a TradingView widget issue in Next.js. It happens when the script tries to access window during Server-Side Rendering (SSR). We fixed this by using dynamic(() => import(...), { ssr: false }) to force the widget to load only on the client.

#### My "Market Movers" aren't updating in real-time. Why?

The backend caches prices for 300 seconds (5 minutes) in PRICE_CACHE to preserve Alpaca API credits. To see faster updates, lower CACHE_TTL in main.py, but be mindful of rate limits.

#### I enabled "Automatic Analysis" in SonarQube, but it failed. Why?

Automatic Analysis doesn't support our Monorepo structure (Backend + Frontend folders) or importing external coverage reports (coverage.xml). You must keep "Automatic Analysis" OFF and rely on the GitHub Actions pipeline.

#### How do I clear "zombie" predictions that didn't hit their target?

Trigger the /scheduler/cleanup endpoint. In production, QStash hits this automatically. Locally, you can run the "Cleanup Zombies" request from your Postman collection.

#### What happens if Alpaca is down?

The system is designed to fallback. In get_live_prices, if Alpaca fails to return a price, the code automatically attempts to fetch the data from yfinance (Yahoo Finance) as a backup.
		
		
		
		
		