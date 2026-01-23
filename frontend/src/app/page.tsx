"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabaseClient";
import PredictionResult from "@/components/PredictionResult";
import SP500Reference from "@/components/SP500Reference";
import {
  ArrowRightIcon,
  ArrowPathIcon,
  GlobeAmericasIcon,
  ClockIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from "@heroicons/react/24/solid";
import dynamic from "next/dynamic";
import { TickerTape, Timeline } from "react-ts-tradingview-widgets";

export default function Home() {
  const [symbol, setSymbol] = useState("");
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [movers, setMovers] = useState<any>(null);
  const [marketStatus, setMarketStatus] = useState({ isOpen: false, text: "MARKET CLOSED" });
  const [searchError, setSearchError] = useState("");

  // Guard for Client-Side Rendering
  const [isMounted, setIsMounted] = useState(false);

    // DYNAMICALLY IMPORT WIDGETS WITH SSR DISABLED
  const TickerTape = dynamic(
      () => import("react-ts-tradingview-widgets").then((mod) => mod.TickerTape),
    { ssr: false }
  );
  const Timeline = dynamic(
        () => import("react-ts-tradingview-widgets").then((mod) => mod.Timeline),
    { ssr: false }
  );

  useEffect(() => {
    setIsMounted(true);

    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => setSession(session));

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/market/movers`)
      .then(r => r.json())
      .then(data => setMovers(data))
      .catch(e => console.error("Movers error:", e));

    const checkMarket = () => {
      const now = new Date();
      const nyc = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
      const hour = nyc.getHours();
      const min = nyc.getMinutes();
      const day = nyc.getDay();

      const isOpen = day >= 1 && day <= 5 && (hour > 9 || (hour === 9 && min >= 30)) && hour < 16;

      const timeStr = nyc.toLocaleTimeString("en-US", {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
      });

      setMarketStatus({
          isOpen,
          text: isOpen ? `MARKET OPEN • ${timeStr} ET` : `MARKET CLOSED • ${timeStr} ET`
      });
    };

    checkMarket();
    const interval = setInterval(checkMarket, 60000);

    return () => {
      subscription.unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const handleLogout = async () => { await supabase.auth.signOut(); };

  const handlePredict = async (e?: React.FormEvent, overrideSymbol?: string) => {
    if (e) e.preventDefault();
    const target = overrideSymbol || symbol;

    setSearchError("");
    setPrediction(null);
    setSymbol(target);

    if (!target) return;
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: target, days: 7 }),
      });
      const data = await res.json();
      if (res.ok) setPrediction(data);
      else setSearchError("Symbol not found or not in S&P 500 coverage.");
    } catch (err) {
      setSearchError("Connection failed. Please try again.");
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-[#020617] text-white flex flex-col pt-16 relative overflow-x-hidden">

      {/* 1. TICKER TAPE (Restored S&P 500 Focus with VXX Fix) */}
      <div className="fixed top-0 left-0 w-full z-50 h-12 bg-black border-b border-slate-800">
         {isMounted && (
           <TickerTape colorTheme="dark" displayMode="compact" symbols={[
             {proName: "FOREXCOM:SPXUSD", title: "S&P 500 Index"},
             {proName: "AMEX:SPY", title: "SPDR S&P 500 ETF"},
             {proName: "AMEX:VXX", title: "VIX PROXY (VXX)"},
             {proName: "NASDAQ:AAPL", title: "Apple"},
             {proName: "NASDAQ:MSFT", title: "Microsoft"},
             {proName: "NASDAQ:NVDA", title: "Nvidia"},
             {proName: "NASDAQ:AMZN", title: "Amazon"},
             {proName: "NASDAQ:GOOGL", title: "Alphabet"},
             {proName: "NASDAQ:META", title: "Meta"},
             {proName: "NYSE:BRK.B", title: "Berkshire Hathaway"},
             {proName: "NYSE:JPM", title: "JPMorgan Chase"}
           ]}/>
         )}
      </div>

      <header className="w-full max-w-7xl mx-auto flex justify-between items-center py-6 px-6 mt-4">
        <div className="flex items-center gap-2">
           <div className={`w-3 h-3 rounded-full animate-pulse ${marketStatus.isOpen ? 'bg-green-500' : 'bg-red-500'}`}></div>
           <div className="flex flex-col">
             <h1 className="text-xl font-black tracking-tight text-white leading-none">SENTIENT</h1>
             <span className="text-[10px] font-bold text-slate-500 tracking-wider flex items-center gap-1">
               {marketStatus.text} <ClockIcon className="h-3 w-3"/>
             </span>
           </div>
        </div>

        <div className="flex items-center gap-6">
           {session ? (
             <>
               <Link href="/accuracy" className="text-sm font-bold text-slate-300 hover:text-white transition-colors">My Watchlist</Link>
               <button onClick={handleLogout} className="text-sm font-bold text-red-400 hover:text-red-300 transition-colors">Logout</button>
             </>
           ) : (
             <div className="flex gap-4">
               <Link href="/login" className="text-sm font-bold text-slate-300 hover:text-white transition-colors">Log In</Link>
               <Link href="/signup" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-bold transition-colors">Sign Up</Link>
             </div>
           )}
        </div>
      </header>

      <div className="flex-1 w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 p-6">
        <div className="lg:col-span-2 space-y-10">
          <div className="text-left mt-4">
            <h2 className="text-5xl font-black mb-4 bg-gradient-to-r from-white to-slate-500 bg-clip-text text-transparent">S&P 500 Intelligence.</h2>
          </div>
          <div className="relative max-w-xl">
             <form onSubmit={(e) => handlePredict(e)} className="relative group z-20">
              <div className="absolute inset-0 bg-blue-500/10 blur-xl rounded-full group-hover:bg-blue-500/20 transition-all duration-500"></div>
              <div className="relative flex items-center bg-slate-900/80 backdrop-blur-xl border border-slate-700 rounded-full p-2 pl-6 shadow-2xl transition-all focus-within:border-blue-500">
                <GlobeAmericasIcon className="h-6 w-6 text-slate-500 mr-3" />
                <input type="text" className="bg-transparent w-full text-white placeholder:text-slate-600 focus:outline-none font-bold tracking-wider uppercase" placeholder="SEARCH S&P 500 (e.g. MSFT)" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
                <button type="submit" disabled={loading} className="bg-white text-black p-3 rounded-full hover:bg-blue-50 transition-colors disabled:opacity-50">
                  {loading ? <ArrowPathIcon className="h-5 w-5 animate-spin"/> : <ArrowRightIcon className="h-5 w-5"/>}
                </button>
              </div>
            </form>
            {searchError && <div className="absolute top-full left-6 mt-3 text-red-400 text-sm font-bold flex items-center gap-2 animate-in slide-in-from-top-2"><span>⚠️</span> {searchError}</div>}
          </div>

          {prediction && <div className="w-full animate-in slide-in-from-bottom-4 duration-500"><PredictionResult data={prediction} onSaveSuccess={() => {}} /></div>}

          {movers && (
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
               <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase mb-3 flex items-center gap-2"><ArrowTrendingUpIcon className="h-4 w-4 text-green-500"/> Top Gainers</h3>
                  <div className="space-y-2">{movers.gainers?.slice(0,5).map((m: any) => (<div key={m.symbol} className="flex justify-between items-center text-xs"><span className="font-bold text-slate-300">{m.symbol}</span><span className="text-green-400 font-mono">+{m.change_pct.toFixed(2)}%</span></div>))}</div>
               </div>
               <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase mb-3 flex items-center gap-2"><ArrowTrendingDownIcon className="h-4 w-4 text-red-500"/> Top Losers</h3>
                  <div className="space-y-2">{movers.losers?.slice(0,5).map((m: any) => (<div key={m.symbol} className="flex justify-between items-center text-xs"><span className="font-bold text-slate-300">{m.symbol}</span><span className="text-red-400 font-mono">{m.change_pct.toFixed(2)}%</span></div>))}</div>
               </div>
               <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase mb-3 flex items-center gap-2"><FireIcon className="h-4 w-4 text-orange-500"/> Most Active</h3>
                  <div className="space-y-2">{movers.active?.slice(0,5).map((m: any) => (<div key={m.symbol} className="flex justify-between items-center text-xs"><span className="font-bold text-slate-300">{m.symbol}</span><span className="text-orange-400 font-mono">{(m.price).toFixed(2)}</span></div>))}</div>
               </div>
            </div>
          )}
        </div>

        <div className="hidden lg:flex flex-col gap-6 sticky top-24 h-screen max-h-[900px]">
           <div className="flex-1 min-h-[400px] border border-slate-800 rounded-xl overflow-hidden bg-slate-900/50">
             {isMounted && <Timeline colorTheme="dark" feedMode="market" market="stock" height="100%" width="100%" />}
           </div>
           <div className="flex-1 min-h-[400px]"><SP500Reference onSelect={(sym) => handlePredict(undefined, sym)} /></div>
        </div>
      </div>
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
         <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-blue-900/10 rounded-full blur-[120px]"></div>
         <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] bg-purple-900/05 rounded-full blur-[120px]"></div>
      </div>
    </main>
  );
}