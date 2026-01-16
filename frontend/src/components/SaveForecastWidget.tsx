'use client';

import { useState, useEffect } from 'react';
import { Save, AlertTriangle, X, Check, Trash2 } from 'lucide-react';

interface Props {
    symbol: string;
    currentPrice: number;
    predictedPrice: number;
    confidence: number;
    targetDate: string; // ISO date from AI response
}

export default function SaveForecastWidget({ symbol, currentPrice, predictedPrice, confidence, targetDate }: Props) {
    const [savedList, setSavedList] = useState<any[]>([]);
    const [showConfirm, setShowConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const USER_ID = "guest_user";

    // Fetch List
    const refreshList = async () => {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/predict/user/${USER_ID}`);
        if (res.ok) setSavedList(await res.json());
    };

    useEffect(() => { refreshList(); }, []);

    // Save Function (Recursive for overwrite)
    const handleSave = async (forceOverwrite = false) => {
        setLoading(true);
        setMsg('');
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/predict/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: USER_ID,
                    symbol,
                    current_price: currentPrice,
                    predicted_price: predictedPrice,
                    confidence_score: confidence,
                    target_date: targetDate,
                    overwrite: forceOverwrite
                }),
            });

            if (res.status === 409) {
                // Conflict detected -> Show Modal
                setShowConfirm(true);
                setLoading(false);
                return;
            }

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail);
            }

            // Success
            setShowConfirm(false);
            setMsg('Forecast saved successfully!');
            refreshList();
        } catch (err: any) {
            setMsg(`Error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">

            {/* 1. SAVE BUTTON CARD */}
            <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-6 shadow-lg">
                <h3 className="text-lg font-bold text-slate-100 mb-2">Track this Prediction</h3>
                <p className="text-sm text-slate-400 mb-4">
                    Save this AI forecast to your dashboard to verify its accuracy in 7 days.
                </p>

                <button
                    onClick={() => handleSave(false)}
                    disabled={loading}
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-lg font-bold transition-all disabled:opacity-50"
                >
                    <Save className="h-5 w-5" />
                    {loading ? 'Saving...' : 'Save Prediction'}
                </button>

                {msg && <div className="mt-3 text-sm text-emerald-400 text-center">{msg}</div>}
            </div>

            {/* 2. OVERWRITE MODAL (Conditional) */}
            {showConfirm && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1e293b] border border-slate-600 rounded-xl p-6 max-w-md w-full shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center gap-3 text-amber-400 mb-4">
                            <AlertTriangle className="h-6 w-6" />
                            <h3 className="text-lg font-bold">Existing Forecast Found</h3>
                        </div>
                        <p className="text-slate-300 mb-6">
                            You already have an active tracking for <span className="font-bold text-white">{symbol}</span>.
                            Do you want to delete the old one and replace it with this new forecast?
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowConfirm(false)}
                                className="flex-1 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleSave(true)} // Force Overwrite
                                className="flex-1 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold"
                            >
                                Replace It
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 3. SAVED LIST (Mini Dashboard) */}
            <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-6">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Your Active Forecasts</h4>
                {savedList.length === 0 && <div className="text-slate-500 text-sm italic">No active forecasts.</div>}

                <div className="space-y-3">
                    {savedList.map((item) => (
                        <div key={item.id} className="bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex justify-between items-center">
                            <div>
                                <div className="font-bold text-slate-200">{item.symbol}</div>
                                <div className="text-xs text-slate-400">Target: ${item.predicted_price.toFixed(2)}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-xs text-blue-400 font-mono">
                                    {new Date(item.target_date).toLocaleDateString()}
                                </div>
                                <div className="text-[10px] text-slate-500">Validation Date</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

        </div>
    );
}