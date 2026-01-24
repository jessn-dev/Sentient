import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CpuChipIcon,
  BookmarkIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from "@heroicons/react/24/solid";
import { useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabaseClient";

interface PredictionData {
  symbol: string;
  company_name?: string; // ✅ Added to interface
  initial_price?: number | string;
  current_price?: number | string;
  target_price?: number | string;
  predicted_price?: number | string;
  end_date?: string;
  forecast_date?: string;
  explanation?: string;
}

export default function PredictionResult({
  data,
  onSaveSuccess
}: {
  data: PredictionData,
  onSaveSuccess: () => void
}) {
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error' | 'exists'>('idle');
  const [errorMessage, setErrorMessage] = useState("");

  const rawTarget = data.predicted_price ?? data.target_price;
  const rawCurrent = data.current_price ?? data.initial_price;
  const rawDate   = data.forecast_date ?? data.end_date ?? new Date().toISOString();

  const targetPrice = Number(rawTarget);
  const currentPrice = Number(rawCurrent);

  if (isNaN(targetPrice) || targetPrice === 0 || isNaN(currentPrice) || currentPrice === 0) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm font-mono space-y-2">
        <div className="font-bold flex items-center gap-2">⚠️ DATA ERROR: Missing Price Data</div>
        <div>Symbol: {data.symbol}</div>
        <div>Expected 'predicted_price': {String(rawTarget)}</div>
      </div>
    );
  }

  const diff = targetPrice - currentPrice;
  const percentChange = (diff / currentPrice) * 100;
  const isBullish = diff >= 0;

  const fmtMoney = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);

  const handleSave = async () => {
    setSaving(true);
    setSaveStatus('idle');
    setErrorMessage("");

    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        setSaveStatus('error');
        setErrorMessage("Please log in first.");
        setSaving(false);
        return;
    }

    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${session.access_token}`
            },
            body: JSON.stringify({
                symbol: data.symbol,
                initial_price: currentPrice,
                target_price: targetPrice,
                end_date: rawDate
            }),
        });

        // ✅ Handle "Already Exists" specifically
        // If your backend returns 200 even for duplicates, we check the text.
        // If it returns 400/409, the !response.ok block catches it.
        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            // Check if backend sent a specific success status or just 200 OK
            if (result.status === "exists" || result.message?.includes("already")) {
                 setSaveStatus('exists');
            } else {
                 setSaveStatus('success');
                 setTimeout(onSaveSuccess, 1500); // Wait a bit before clearing to show success state
            }
        } else {
            // Check if it was a duplicate error from the backend
            if (response.status === 409 || result.detail?.includes("already")) {
                setSaveStatus('exists');
            } else {
                setSaveStatus('error');
                setErrorMessage("Failed to save.");
            }
        }
    } catch (e) {
        console.error(e);
        setSaveStatus('error');
        setErrorMessage("Connection failed.");
    }
    setSaving(false);
  };

  return (
    <div className="w-full bg-[#151921] border border-white/10 rounded-xl overflow-hidden shadow-2xl animate-in slide-in-from-bottom-2">

      {/* HEADER */}
      <div className="p-6 border-b border-white/5 flex flex-col md:flex-row justify-between md:items-center gap-4 bg-white/[0.02]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <ChartBarIcon className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-3">
                <h2 className="text-3xl font-black text-white tracking-tight">{data.symbol}</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500 text-white uppercase tracking-wider shadow-lg shadow-indigo-500/20">
                    AI Forecast
                </span>
            </div>
            {/* ✅ COMPANY NAME RESTORED */}
            <p className="text-sm text-slate-400 font-medium mt-1 truncate max-w-[250px] md:max-w-md">
                {data.company_name || "Common Stock"} • 7-Day Model
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-3">
                <Link
                    href={`/stock/${data.symbol}`}
                    className="px-4 py-2 rounded-lg bg-[#0B0E14] border border-white/10 text-slate-300 text-xs font-bold uppercase tracking-wider hover:bg-white/5 hover:text-white transition-all flex items-center gap-2"
                >
                    <ChartBarIcon className="h-4 w-4" /> Details
                </Link>

                <button
                    onClick={handleSave}
                    disabled={saving || saveStatus === 'success' || saveStatus === 'exists'}
                    className={`px-6 py-2 rounded-lg text-white text-xs font-bold uppercase tracking-wider shadow-lg transition-all flex items-center gap-2 disabled:opacity-80 disabled:cursor-not-allowed ${
                        saveStatus === 'success' ? 'bg-emerald-600' :
                        saveStatus === 'exists' ? 'bg-amber-600' :
                        saveStatus === 'error' ? 'bg-rose-600' :
                        'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20'
                    }`}
                >
                {saving ? (
                    <span className="animate-pulse">Saving...</span>
                ) : saveStatus === 'success' ? (
                    <><CheckCircleIcon className="h-4 w-4" /> Tracked</>
                ) : saveStatus === 'exists' ? (
                    <><BookmarkIcon className="h-4 w-4" /> Tracking</>
                ) : saveStatus === 'error' ? (
                    <><ExclamationCircleIcon className="h-4 w-4" /> Retry</>
                ) : (
                    <><BookmarkIcon className="h-4 w-4" /> Track Prediction</>
                )}
                </button>
            </div>

            {/* Error / Status Text Feedback */}
            {saveStatus === 'exists' && (
                <span className="text-[10px] text-amber-400 font-medium animate-in fade-in">
                    ⚠️ Already in watchlist
                </span>
            )}
            {saveStatus === 'error' && (
                <span className="text-[10px] text-rose-400 font-medium animate-in fade-in">
                    {errorMessage}
                </span>
            )}
        </div>
      </div>

      {/* STATS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/5">
        <div className="p-8 flex flex-col justify-center items-center relative group">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Current Price</span>
            <div className="text-4xl font-mono font-medium text-white group-hover:text-slate-200 transition-colors">
                {fmtMoney(currentPrice)}
            </div>
            <div className="mt-4 flex items-center gap-2 text-xs text-slate-500 bg-white/5 px-3 py-1 rounded-full border border-white/5">
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse"></span>
                Live Market Data
            </div>
        </div>

        <div className="p-8 flex flex-col justify-center items-center relative overflow-hidden">
            <div className={`absolute inset-0 opacity-10 blur-3xl ${isBullish ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">AI Target ({rawDate.split('-').slice(1).join('/')})</span>
            <div className={`text-5xl font-mono font-bold tracking-tighter flex items-center gap-3 ${isBullish ? 'text-emerald-400' : 'text-rose-400'}`}>
                {fmtMoney(targetPrice)}
                {isBullish ? <ArrowTrendingUpIcon className="h-8 w-8 opacity-50"/> : <ArrowTrendingDownIcon className="h-8 w-8 opacity-50"/>}
            </div>
            <div className={`mt-4 px-4 py-1.5 rounded-full border text-sm font-bold font-mono ${
                isBullish 
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}>
                {isBullish ? '+' : ''}{percentChange.toFixed(2)}% {isBullish ? 'Upside' : 'Downside'}
            </div>
        </div>
      </div>

      {/* FOOTER ANALYSIS */}
      <div className="p-6 bg-[#0B0E14]/50 border-t border-white/5">
        <div className="flex items-start gap-4">
            <CpuChipIcon className="h-6 w-6 text-indigo-500 mt-1 shrink-0" />
            <div>
                <h4 className="text-sm font-bold text-white mb-1">Sentient AI Analysis</h4>
                <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">
                    {data.explanation ? data.explanation : (
                        <>
                        Our Prophet model projects a <span className={isBullish ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                        {Math.abs(percentChange).toFixed(1)}% {isBullish ? "increase" : "decrease"}
                        </span> to <span className="text-slate-200 font-mono font-medium">{fmtMoney(targetPrice)}</span> by <span className="text-slate-200 font-medium">{new Date(rawDate).toLocaleDateString()}</span>.
                        </>
                    )}
                </p>
            </div>
        </div>
      </div>
    </div>
  );
}