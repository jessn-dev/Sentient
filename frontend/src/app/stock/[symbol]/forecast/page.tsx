'use client';

import { useEffect, useState, use } from 'react'; // <--- Import 'use'
import { fetchPrediction, PredictionResponse } from '@/lib/api';
import PredictionChart from '@/components/PredictionChart';
import ExplanationCard from '@/components/ExplanationCard';
import { TrendingUp, Activity } from 'lucide-react';

export default function ForecastPage({ params }: { params: Promise<{ symbol: string }> }) {
    // 1. Unwrap params
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

    // ... (keep the rest of your return statement the same) ...
    if (loading) return <div className="text-slate-400 p-8">Running Prophet AI Models...</div>;
    if (error) return <div className="text-red-400 p-8">Error: {error}</div>;
    if (!data) return null;

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
            {/* ... existing JSX ... */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#1e293b] border border-slate-700 p-6 rounded-xl shadow-lg">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 font-medium text-sm">7-Day Price Target</span>
                        <TrendingUp className={`h-5 w-5 ${data.predicted_price_7d > data.current_price ? 'text-green-400' : 'text-red-400'}`} />
                    </div>
                    <div className="text-3xl font-bold text-slate-100">
                        ${data.predicted_price_7d.toFixed(2)}
                    </div>
                    <div className={`text-sm mt-1 ${data.predicted_price_7d > data.current_price ? 'text-green-400' : 'text-red-400'}`}>
                        {((data.predicted_price_7d - data.current_price) / data.current_price * 100).toFixed(2)}% implied move
                    </div>
                </div>

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

            <div className="bg-[#1e293b] border border-slate-700 p-6 rounded-xl shadow-lg">
                <h3 className="text-lg font-bold text-slate-100 mb-4">Prophet Model Visualization</h3>
                <PredictionChart data={data} />
            </div>

            <ExplanationCard text={data.explanation} />
        </div>
    );
}