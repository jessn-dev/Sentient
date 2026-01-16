'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Prediction {
    id: number;
    symbol: string;
    prediction_type: string;
    start_price: number;
    target_date: string; // ISO string
    status: string;
    is_correct?: boolean;
}

export default function UserPredictionCard({ symbol }: { symbol: string }) {
    const [predictions, setPredictions] = useState<Prediction[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Hardcoded user for MVP - in real app, get from auth context
    const USER_ID = "guest_user";

    // Fetch Predictions
    const fetchPredictions = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/predict/user/${USER_ID}`);
            const data = await res.json();
            setPredictions(data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchPredictions();
    }, []);

    // Submit Vote
    const handleVote = async (direction: 'UP' | 'DOWN') => {
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/predict/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: USER_ID, symbol, direction }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to submit");
            }

            await fetchPredictions(); // Refresh list
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Helper to calculate time remaining
    const getDaysRemaining = (targetDate: string) => {
        const target = new Date(targetDate).getTime();
        const now = new Date().getTime();
        const diff = target - now;

        if (diff <= 0) return "Validating...";

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        return `${days}d ${hours}h remaining`;
    };

    return (
        <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-6 shadow-lg">

            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-bold text-slate-100">Make Your Call</h3>
                    <p className="text-sm text-slate-400">Predict {symbol}'s price in 7 days.</p>
                </div>
                <div className="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-400 border border-slate-700">
                    Max 3 Active
                </div>
            </div>

            {/* Voting Buttons */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <button
                    onClick={() => handleVote('UP')}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-emerald-900/30 hover:bg-emerald-900/50 border border-emerald-700/50 text-emerald-400 py-3 rounded-lg font-bold transition-all disabled:opacity-50"
                >
                    <TrendingUp className="h-5 w-5" />
                    Bullish
                </button>
                <button
                    onClick={() => handleVote('DOWN')}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-rose-900/30 hover:bg-rose-900/50 border border-rose-700/50 text-rose-400 py-3 rounded-lg font-bold transition-all disabled:opacity-50"
                >
                    <TrendingDown className="h-5 w-5" />
                    Bearish
                </button>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded text-red-300 text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                </div>
            )}

            {/* Active Predictions List */}
            <div className="space-y-3">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Your Predictions</h4>

                {predictions.length === 0 && (
                    <div className="text-slate-500 text-sm italic text-center py-2">No active predictions found.</div>
                )}

                {predictions.map((pred) => (
                    <div key={pred.id} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 flex justify-between items-center">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <span className="font-bold text-slate-200">{pred.symbol}</span>
                                <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                                    pred.prediction_type === 'BULLISH'
                                        ? 'bg-emerald-500/20 text-emerald-400'
                                        : 'bg-rose-500/20 text-rose-400'
                                }`}>
                  {pred.prediction_type}
                </span>
                            </div>
                            <div className="text-xs text-slate-400">
                                Entry: ${pred.start_price.toFixed(2)}
                            </div>
                        </div>

                        {/* Status / Timer */}
                        <div className="text-right">
                            {pred.status === 'ACTIVE' ? (
                                <div className="flex items-center gap-1.5 text-xs text-blue-400 font-mono">
                                    <Clock className="h-3 w-3" />
                                    {getDaysRemaining(pred.target_date)}
                                </div>
                            ) : (
                                <div className={`flex items-center gap-1.5 text-xs font-bold ${pred.is_correct ? 'text-green-400' : 'text-red-400'}`}>
                                    {pred.is_correct ? (
                                        <><CheckCircle className="h-3 w-3" /> Correct</>
                                    ) : (
                                        <><XCircle className="h-3 w-3" /> Incorrect</>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}