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
    User -->|HTTPS| NextJS[Frontend (Next.js 16)]
    NextJS -->|JSON| FastAPI[Backend (FastAPI)]
    FastAPI -->|Read/Write| DB[(Turso / SQLite)]
    FastAPI -->|Inference| HF[Hugging Face (FinBERT)]
    FastAPI -->|Forecast| Prophet[Facebook Prophet]
    GitHub[GitHub Actions] -->|Cron 6AM| Script[Automation Bot]
    Script -->|Alerts| Email[Gmail SMTP]
