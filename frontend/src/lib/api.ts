const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PredictionResponse {
    symbol: string;
    current_price: number;
    predicted_price_7d: number;
    confidence_score: number;
    forecast_date: string;
    price_movement: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    growth_percentage: number;
    market_cap?: number;
    pe_ratio?: number;
    dividend_yield?: number;
    fifty_two_week_high?: number;
    fifty_two_week_low?: number;
    open_price?: number;
    high_price?: number;
    low_price?: number;
    volume?: number;
    explanation: string;
}

export async function fetchPrediction(symbol: string): Promise<PredictionResponse> {
    const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol.toUpperCase(), exchange: 'NASDAQ' }),
        cache: 'no-store', // Disable Next.js caching for real-time data
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to fetch prediction');
    }

    return res.json();
}