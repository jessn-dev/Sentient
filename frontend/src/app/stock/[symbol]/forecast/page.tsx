'use client';

import { useEffect, useState, use } from 'react';
import { fetchPrediction, PredictionResponse } from '@/lib/api';
import PredictionChart from '@/components/PredictionChart';
import ExplanationCard from '@/components/ExplanationCard';
import SaveForecastWidget from '@/components/SaveForecastWidget';
import { TrendingUp, Activity } from 'lucide-react';

export default function ForecastPage({ params }: { params: Promise<{ symbol: string }> }) {
    // 1. Unwrap params (Next.js 15+ fix)
    const { symbol } = use(params);

    const [data, setData] = useState<PredictionResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchPrediction(symbol)
            .then(setData)
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [symbol]);

    if (loading) return <div className="text-slate-400 p-8">Running Prophet AI Models...</div>;
    if (error) return <div className="text-red-400 p-8">Error: {error}</div>;
    if (!data) return null;

    // Calculate 7 days from now for the target date
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 7);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">

            {/* 1. KEY METRICS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Price Target Card */}
                <div className="bg-[#1e293b] border border-slate-700 p-6 rounded-xl shadow-lg">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 font-medium text-sm">7-Day Price Target</span>
                        <TrendingUp className={`h-5 w-5 ${data.predicted_price > data.current_price ? 'text-green-400' : 'text-red-400'}`} />
                    </div>
                    <div className="text-3xl font-bold text-slate-100">
                        ${data.predicted_price.toFixed(2)}
                    </div>
                    <div className={`text-sm mt-1 ${data.predicted_price > data.current_price ? 'text-green-400' : 'text-red-400'}`}>
                        {((data.predicted_price - data.current_price) / data.current_price * 100).toFixed(2)}% implied move
                    </div>
                </div>

                {/* Confidence Card */}
                <div className="bg-[#1e293b] border border-slate-700 p-6 rounded-xl shadow-lg">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 font-medium text-sm">Model Confidence</span>
                        <Activity className="text-blue-400 h-5 w-5" />
                    </div>
                    <div className="text-3xl font-bold text-slate-100">
                        {(data.confidence_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-sm text-slate-500 mt-1">Based on historical volatility</div>
                </div>
            </div>

            {/* 2. MAIN LAYOUT (Chart + Save Widget) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: AI Chart & Explanation (Span 2) */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-[#1e293b] border border-slate-700 p-6 rounded-xl shadow-lg">
                        <h3 className="text-lg font-bold text-slate-100 mb-4">Prophet Model Visualization</h3>
                        <PredictionChart data={data} />
                    </div>
                    <ExplanationCard text={data.explanation} />
                </div>

                {/* Right Column: Save Widget (Span 1) */}
                <div className="lg:col-span-1">
                    <SaveForecastWidget
                        symbol={symbol}
                        currentPrice={data.current_price}
                        predictedPrice={data.predicted_price}
                        confidence={data.confidence_score}
                        targetDate={targetDate.toISOString()}
                    />
                </div>
            </div>
        </div>
    );
}