'use client';

import { useEffect, useState, use } from 'react'; // <--- Import 'use'
import StatsGrid from '@/components/StatsGrid';
import { fetchPrediction } from '@/lib/api';

// params is now a Promise<{ symbol: string }>
export default function StockOverview({ params }: { params: Promise<{ symbol: string }> }) {
    // 1. Unwrap the params using React.use()
    const { symbol } = use(params);

    const [data, setData] = useState<any>(null);

    useEffect(() => {
        // Use the unwrapped 'symbol' variable
        fetchPrediction(symbol).then(setData).catch(console.error);
    }, [symbol]);

    if (!data) return <div className="h-64 animate-pulse bg-slate-800/50 rounded-xl" />;

    return (
        <div className="space-y-6">
            {/* Company Header */}
            <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-8 shadow-lg">
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                    <div>
                        <h2 className="text-3xl font-bold text-slate-100">{symbol}</h2>
                        <p className="text-slate-400 text-lg">U.S. Equity • Nasdaq</p>
                    </div>
                    <div className="text-right">
                        <div className="text-4xl font-bold text-slate-100">${data.current_price.toFixed(2)}</div>
                        <div className="text-emerald-400 font-medium">+0.00% (Live)</div>
                    </div>
                </div>
            </div>

            <h3 className="text-xl font-bold text-slate-200 mt-8">Key Statistics</h3>
            <StatsGrid data={data} />

            <div className="bg-blue-900/20 border border-blue-500/30 p-6 rounded-xl flex items-center justify-between">
                <div>
                    <h4 className="text-blue-400 font-bold text-lg">Want to see the future?</h4>
                    <p className="text-slate-400">View our AI-powered 7-day forecast model.</p>
                </div>
                <a href={`/stock/${symbol}/forecast`} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                    View Forecast
                </a>
            </div>
        </div>
    );
}