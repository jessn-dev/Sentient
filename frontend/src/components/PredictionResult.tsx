"use client";
import { useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabaseClient";
import {
  BookmarkIcon,
  ChartBarSquareIcon,
  CpuChipIcon,
  MegaphoneIcon,
  BanknotesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UserIcon
} from "@heroicons/react/24/solid";

export default function PredictionResult({ data, onSaveSuccess, detailed = false }: any) {
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState("idle");
  const [showOverwriteModal, setShowOverwriteModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [existingDate, setExistingDate] = useState("");

  const isBullish = data.predicted_price > data.current_price;

  // ✅ FIX: Fallback to symbol if company_name is missing/null
  const displayName = data.company_name || data.symbol;

  const handleTrackClick = async () => {
    setSaving(true);
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      setShowLoginModal(true);
      setSaving(false);
      return;
    }

    const token = session.access_token;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist/performance`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const list = await res.json();
      const found = list.find((item: any) => item.symbol === data.symbol);

      if (found) {
        setExistingDate(found.created_at);
        setShowOverwriteModal(true);
        setSaving(false);
      } else {
        await executeSave(token);
      }
    } catch (e) {
      await executeSave(token);
    }
  };

  const executeSave = async (token: string) => {
    setSaving(true);
    setShowOverwriteModal(false);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist`, {
         method: "POST",
         headers: {
           "Content-Type": "application/json",
           "Authorization": `Bearer ${token}`
         },
         body: JSON.stringify({
           symbol: data.symbol,
           initial_price: data.current_price,
           target_price: data.predicted_price,
           end_date: data.forecast_date
         })
      });
      setSaveStatus("success");
      if (onSaveSuccess) onSaveSuccess();
      setTimeout(() => setSaveStatus("idle"), 3000);
    } catch (error) {
      console.error(error);
      alert("Failed to save prediction.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={`w-full bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden relative ${detailed ? 'border-0 bg-transparent' : ''}`}>

      {/* HEADER: Only show in Summary View (Homepage) */}
      {!detailed && (
        <div className="bg-slate-950/50 p-6 flex justify-between items-start border-b border-slate-800">
          <div>
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              {data.symbol}
              <span className="text-[10px] bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded border border-blue-800">AI</span>
            </h2>
            {/* ✅ FIX: Name Display */}
            <p className="text-sm text-slate-400 font-medium mt-1">{displayName}</p>
          </div>

          <div className="flex gap-2">
             {/* ✅ FIX: Details Link */}
             <Link
               href={`/stock/${data.symbol}`}
               className="px-4 py-2 bg-slate-800 rounded-lg text-sm font-bold text-slate-300 flex gap-2 hover:bg-slate-700 transition-colors items-center"
             >
                <ChartBarSquareIcon className="h-4 w-4"/> Details
             </Link>

             <button
               onClick={handleTrackClick}
               disabled={saving || saveStatus === "success"}
               className={`px-4 py-2 rounded-lg text-sm font-bold text-white flex gap-2 transition-colors items-center ${saveStatus === 'success' ? 'bg-green-600' : 'bg-blue-600 hover:bg-blue-500'}`}
             >
                {saveStatus === 'success' ? <CheckCircleIcon className="h-4 w-4"/> : <BookmarkIcon className="h-4 w-4"/>}
                {saveStatus === 'success' ? 'Tracked' : 'Track'}
             </button>
          </div>
        </div>
      )}

      {/* BODY CONTENT */}
      <div className={`${detailed ? 'space-y-8' : 'p-6 space-y-6'}`}>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-5 bg-slate-950 rounded-xl border border-slate-800 text-center">
             <span className="text-xs font-bold text-slate-500 uppercase">Current</span>
             <div className="text-3xl font-black text-white">${data.current_price.toFixed(2)}</div>
          </div>
          <div className={`p-5 rounded-xl border text-center ${isBullish ? 'bg-green-900/20 border-green-900' : 'bg-red-900/20 border-red-900'}`}>
             <span className={`text-xs font-bold uppercase ${isBullish ? 'text-green-400' : 'text-red-400'}`}>Target</span>
             <div className={`text-3xl font-black ${isBullish ? 'text-green-400' : 'text-red-400'}`}>${data.predicted_price.toFixed(2)}</div>
          </div>
        </div>

        <div className="p-4 bg-blue-900/10 border border-blue-900/30 rounded-xl text-sm text-blue-200 italic">
          "{data.explanation}"
        </div>

        {/* DETAILED VIEW SECTIONS */}
        {detailed && (
          <>
            {/* Technicals */}
            {data.technicals && (
              <div className="space-y-3 pt-4 border-t border-slate-800">
                 <div className="flex gap-2 text-slate-400"><CpuChipIcon className="h-4 w-4"/> <span className="text-xs font-black uppercase">Technicals</span></div>
                 <div className="grid gap-2">
                    <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800"><span className="text-xs font-bold text-slate-400">Trend</span><span className="text-sm font-bold text-white">{data.technicals.trend_signal}</span></div>
                    <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800"><span className="text-xs font-bold text-slate-400">RSI</span><span className="text-sm font-bold text-white">{data.technicals.rsi}</span></div>
                    <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800"><span className="text-xs font-bold text-slate-400">Bollinger</span><span className="text-sm font-bold text-white">{data.technicals.bollinger_signal}</span></div>
                 </div>
              </div>
            )}
            {/* Liquidity */}
            {data.liquidity && (
               <div className="space-y-3 pt-4 border-t border-slate-800">
                 <div className="flex gap-2 text-slate-400"><BanknotesIcon className="h-4 w-4"/> <span className="text-xs font-black uppercase">Liquidity</span></div>
                 <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800"><div className="text-[10px] text-slate-500 font-bold uppercase">Rating</div><div className="text-sm font-bold text-white">{data.liquidity.liquidity_rating}</div></div>
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800"><div className="text-[10px] text-slate-500 font-bold uppercase">Risk</div><div className="text-sm font-bold text-white">{data.liquidity.slippage_risk}</div></div>
                 </div>
               </div>
            )}
            {/* News */}
            {data.sentiment && (
              <div className="space-y-3 pt-4 border-t border-slate-800">
                 <div className="flex gap-2 text-slate-400"><MegaphoneIcon className="h-4 w-4"/> <span className="text-xs font-black uppercase">News Sentiment</span></div>
                 <div className="space-y-2">
                    {data.sentiment.news.map((n: any, i: number) => (
                       <a key={i} href={n.link} target="_blank" className="block p-3 bg-slate-950 rounded-lg border border-slate-800 hover:border-blue-500 transition-colors">
                          <div className="text-xs font-bold text-slate-300 truncate">{n.title}</div>
                          <div className={`text-[10px] mt-1 font-bold ${n.sentiment==='Positive'?'text-green-500':n.sentiment==='Negative'?'text-red-500':'text-slate-500'}`}>{n.sentiment}</div>
                       </a>
                    ))}
                 </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* OVERWRITE MODAL */}
      {showOverwriteModal && (
        <div className="absolute inset-0 z-50 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-2xl shadow-2xl max-w-sm w-full text-center">
            <div className="mx-auto w-12 h-12 bg-yellow-500/20 rounded-full flex items-center justify-center mb-4">
               <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Prediction Exists</h3>
            <p className="text-sm text-slate-400 mb-6">
              You are already tracking <strong>{data.symbol}</strong> since <span className="text-white font-mono">{existingDate}</span>.
            </p>
            <div className="grid grid-cols-2 gap-3">
               <button onClick={() => setShowOverwriteModal(false)} className="px-4 py-2 rounded-lg font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 text-sm">Cancel</button>
               <button onClick={async () => { const { data: { session } } = await supabase.auth.getSession(); if (session) await executeSave(session.access_token); }} className="px-4 py-2 rounded-lg font-bold text-white bg-red-600 hover:bg-red-500 text-sm">Overwrite</button>
            </div>
          </div>
        </div>
      )}

      {/* LOGIN MODAL */}
      {showLoginModal && (
        <div className="absolute inset-0 z-50 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-2xl shadow-2xl max-w-sm w-full text-center">
            <div className="mx-auto w-12 h-12 bg-blue-600/20 rounded-full flex items-center justify-center mb-4">
               <UserIcon className="h-6 w-6 text-blue-500" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Account Required</h3>
            <p className="text-sm text-slate-400 mb-6">Please login to track predictions.</p>
            <div className="grid grid-cols-2 gap-3">
               <Link href="/login" className="px-4 py-2 rounded-lg font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 text-sm flex items-center justify-center">Log In</Link>
               <Link href="/signup" className="px-4 py-2 rounded-lg font-bold text-white bg-blue-600 hover:bg-blue-500 text-sm flex items-center justify-center">Sign Up</Link>
            </div>
            <button onClick={() => setShowLoginModal(false)} className="mt-4 text-xs text-slate-500 hover:text-white underline">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}