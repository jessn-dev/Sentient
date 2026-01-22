"use client";
import { useState, useEffect } from "react";
import PredictionResult from "@/components/PredictionResult";
import DashboardGrid from "@/components/DashboardGrid";
import MarketStatus from "@/components/MarketStatus";
import TradingViewWidget from "@/components/TradingViewWidget";
import MarketMovers from "@/components/MarketMovers";
import SP500Reference from "@/components/SP500Reference";
import { MagnifyingGlassIcon, ExclamationCircleIcon } from "@heroicons/react/24/outline";

export default function Home() {
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  const fetchPrediction = async (ticker: string) => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: ticker, days: 7 }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed");
      setData(await res.json());
    } catch(e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchPrediction("NVDA"); }, []);
  const handlePredict = (e: any) => { e.preventDefault(); if(symbol) fetchPrediction(symbol); };

  return (
      <main className="fixed inset-0 z-[100] bg-[#020617] text-white flex flex-col">
        <div className="w-full h-12 border-b border-slate-800 bg-slate-900 shrink-0"><TradingViewWidget type="ticker-tape" /></div>
        <div className="flex flex-1 overflow-hidden">
          <aside className="hidden md:block w-72 lg:w-96 shrink-0 border-r border-slate-800 bg-slate-900/50"><TradingViewWidget type="timeline" /></aside>

          <div className="flex-1 flex flex-col gap-8 p-6 lg:p-10 overflow-y-auto custom-scrollbar">
            <div className="w-full max-w-2xl mx-auto text-center mt-4">
              <h1 className="text-5xl font-black mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">SentientAI</h1>
              <p className="text-slate-400 text-sm">Neural Forecasting for S&P 500</p>
              <form onSubmit={handlePredict} className="relative mt-8 shadow-2xl">
                <input type="text" value={symbol} onChange={(e)=>setSymbol(e.target.value.toUpperCase())} placeholder="Search Ticker..." className="w-full bg-slate-800/80 border border-slate-700 py-4 pl-12 pr-32 rounded-2xl outline-none focus:ring-2 focus:ring-blue-600 text-lg" />
                <MagnifyingGlassIcon className="h-6 w-6 absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <button type="submit" disabled={loading} className="absolute right-2 top-2 bottom-2 bg-blue-600 px-6 rounded-xl font-bold text-xs uppercase">{loading ? "..." : "Predict"}</button>
              </form>
              {error && <div className="mt-4 p-4 bg-red-900/20 border border-red-900/50 rounded-xl text-red-400 font-bold flex gap-2 justify-center"><ExclamationCircleIcon className="h-5 w-5"/>{error}</div>}
            </div>
            <div className="w-full pb-20 space-y-10">
              {loading ? <div className="h-[300px] bg-slate-900/50 rounded-xl animate-pulse border border-slate-800"/> : data && <PredictionResult data={data} onSaveSuccess={()=>setRefresh(r=>r+1)} />}
              <DashboardGrid refreshTrigger={refresh} />
            </div>
          </div>

          <aside className="w-full lg:w-80 shrink-0 border-l border-slate-800 bg-slate-900/30 flex flex-col">
            <MarketStatus />
            <MarketMovers />
            <div className="flex-1 overflow-hidden"><SP500Reference /></div>
          </aside>
        </div>
      </main>
  );
}