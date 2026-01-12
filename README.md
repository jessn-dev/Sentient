# Sentient 🚀
> AI-Powered Stock Prediction & Market Sentiment Analysis Platform.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.14-yellow.svg)
![Next.js](https://img.shields.io/badge/next.js-16.1-black.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)

**Sentient** is a microservices-based application that forecasts stock prices 7 days into the future using Facebook Prophet and analyzes market sentiment using FinBERT. It is architected to run entirely on **Free Tier** infrastructure.

---

## 🏗 Architecture

The system follows a **Microservices** pattern, separating the UI, Calculation Engine, and Persistence layers.

```mermaid
graph TD
    %% --- STYLING ---
    classDef frontend fill:#000000,stroke:#fff,stroke-width:2px,color:#fff;
    classDef backend fill:#2D3748,stroke:#4FD1C5,stroke-width:2px,color:#fff;
    classDef db fill:#2C5282,stroke:#fff,stroke-width:2px,color:#fff;
    classDef external fill:#E2E8F0,stroke:#2D3748,stroke-width:1px,color:#000;
    classDef automation fill:#9B2C2C,stroke:#F687B3,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    User((👤 User))

    %% --- FRONTEND (VERCEL) ---
    subgraph Client_Side ["Frontend Layer - Vercel"]
        NextJS[Next.js 16.1.1<br/>React 19 + ShadCN UI]:::frontend
    end

    %% --- BACKEND (RENDER) ---
    subgraph Server_Side ["Backend Layer - Render Docker"]
        FastAPI[FastAPI<br/>Python 3.14.2]:::backend
        Prophet[Facebook Prophet - Forecasting Engine]:::backend
        Cache[Sentiment Cache - Logic]:::backend
    end

    %% --- DATABASE (TURSO) ---
    subgraph Storage ["Persistence Layer - Turso"]
        Turso[(LibSQL / Turso<br/>Distributed SQLite)]:::db
    end

    %% --- AUTOMATION (GITHUB) ---
    subgraph Worker ["Automation Layer - GitHub Actions"]
        Action[Daily Cron Job<br/>6:00 AM UTC]:::automation
        Script[Headless Script<br/>Python 3.14]:::automation
    end

    %% --- EXTERNAL APIS ---
    subgraph External ["External APIs"]
        Yahoo[Yahoo Finance - yfinance]:::external
        HF[Hugging Face API - FinBERT Sentiment]:::external
        Gmail[Gmail SMTP - Email Alerts]:::external
    end

    %% --- CONNECTIONS ---
    User -->|HTTPS| NextJS
    NextJS -->|JSON / REST| FastAPI
    
    FastAPI -->|Read/Write| Turso
    FastAPI -->|Load Data| Prophet
    FastAPI -->|Fetch News| Yahoo
    FastAPI -->|Analyze Text| HF
    
    Action -->|Triggers| Script
    Script -->|Read Watchlist| Turso
    Script -->|Fetch Price| Yahoo
    Script -->|Send Alert| Gmail
