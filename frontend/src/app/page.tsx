"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabaseClient";
import PredictionResult from "@/components/PredictionResult";
import SP500Reference from "@/components/SP500Reference";
import {
  ArrowRightIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  SparklesIcon,
  ChartBarIcon
} from "@heroicons/react/24/solid";
import dynamic from "next/dynamic";

// --- WIDGET IMPORTS ---
const TickerTape = dynamic(
  () => import("react-ts-tradingview-widgets").then((mod) => mod.TickerTape),
  { ssr: false }
);

const Timeline = dynamic(
  () => import("react-ts-tradingview-widgets").then((mod) => mod.Timeline),
  { ssr: false }
);

const TICKER_SYMBOLS = [
  { proName: "FOREXCOM:SPXUSD", title: "S&P 500" },
  { proName: "AMEX:SPY", title: "SPY ETF" },
  { proName: "AMEX:VXX", title: "VIX PROXY" },
  { proName: "NASDAQ:AAPL", title: "Apple" },
  { proName: "NASDAQ:NVDA", title: "Nvidia" },
  { proName: "NASDAQ:MSFT", title: "Microsoft" }
];

const POPULAR_TICKERS = [
  "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX",
  "JPM", "BAC", "WMT", "DIS", "KO", "PEP", "XOM", "CVX", "PFE", "LLY", "AVGO"
];

export default function Home() {
  const [symbol, setSymbol] = useState("");
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [movers, setMovers] = useState<any>(null);
  const [marketStatus, setMarketStatus] = useState({ isOpen: false, text: "MARKET CLOSED" });
  const [searchError, setSearchError] = useState("");
  const [isMounted, setIsMounted] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    setIsMounted(true);

    const shuffled = [...POPULAR_TICKERS].sort(() => 0.5 - Math.random());
    setSuggestions(shuffled.slice(0, 3));

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
      const timeStr = nyc.toLocaleTimeString("en-US", { hour: 'numeric', minute: '2-digit', hour12: true });
      setMarketStatus({
          isOpen,
          text: isOpen ? `MARKET OPEN • ${timeStr} ET` : `MARKET CLOSED • ${timeStr} ET`
      });
    };
    checkMarket();
    const interval = setInterval(checkMarket, 60000);
    return () => { subscription.unsubscribe(); clearInterval(interval); };
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
      else setSearchError("Symbol not found or data unavailable.");
    } catch (err) {
      setSearchError("Connection failed. Please try again.");
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 flex flex-col pb-20 relative font-sans selection:bg-indigo-500/30">

      {/* HEADER (Sticky) */}
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-[#0B0E14]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex justify-between items-center py-4 px-6">
            <div className="flex items-center gap-3">
               <h1 className="text-xl font-bold tracking-tight text-white leading-none">
                 SENTIENT<span className="text-indigo-500">.</span>
               </h1>
            </div>

            <div className="flex items-center gap-6">
            {session ? (
                <>
                <Link href="/accuracy" className="text-xs font-medium text-slate-400 hover:text-white transition-colors uppercase tracking-widest">Watchlist</Link>
                <button onClick={handleLogout} className="text-xs font-medium text-rose-400 hover:text-rose-300 transition-colors uppercase tracking-widest">Sign Out</button>
                </>
            ) : (
                <div className="flex gap-4">
                  <Link href="/login" className="px-5 py-2 bg-[#151921] border border-white/10 hover:bg-white/5 hover:border-indigo-500/50 text-white rounded-md text-xs font-bold transition-all shadow-lg uppercase tracking-wider flex items-center justify-center">
                    Log In
                  </Link>
                  <Link href="/signup" className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-bold transition-all shadow-lg shadow-indigo-500/20 uppercase tracking-wider">
                    Get Access
                  </Link>
                </div>
            )}
            </div>
        </div>
      </header>

      {/* TICKER TAPE (Scrolls naturally, not sticky) */}
      {isMounted && (
        <div className="w-full h-12 border-b border-white/5 bg-[#0B0E14] z-10 relative">
           <TickerTape colorTheme="dark" displayMode="compact" symbols={TICKER_SYMBOLS} />
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="flex-1 w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 p-6 lg:pt-10 z-0">

        {/* LEFT COLUMN */}
        <div className="lg:col-span-8 flex flex-col gap-10">

          <div className="space-y-6">
            <h1 className="text-4xl lg:text-6xl font-medium tracking-tight text-white">
              <span className="text-slate-500">Market</span> <br />
              Intelligence.
            </h1>
            <p className="text-slate-400 max-w-lg text-lg leading-relaxed">
                AI-powered forecasting for the S&P 500. Real-time analysis, proprietary confidence scores, and institutional-grade data.
            </p>

            <div className="relative max-w-xl group">
             <form onSubmit={(e) => handlePredict(e)} className="relative z-20">
              <div className="relative flex items-center bg-[#151921] border border-white/10 rounded-xl p-2 pl-5 shadow-2xl transition-all focus-within:border-indigo-500/50 focus-within:ring-1 focus-within:ring-indigo-500/50">
                <MagnifyingGlassIcon className="h-5 w-5 text-slate-500 mr-3" />
                <input
                    type="text"
                    className="bg-transparent w-full text-white placeholder:text-slate-600 focus:outline-none font-medium tracking-wide uppercase text-sm h-10"
                    placeholder="Search Ticker (e.g. AAPL)"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                />
                <button type="submit" disabled={loading} className="bg-indigo-600 text-white w-10 h-10 rounded-lg flex items-center justify-center hover:bg-indigo-500 transition-all disabled:opacity-50 disabled:hover:bg-indigo-600">
                  {loading ? <ArrowPathIcon className="h-5 w-5 animate-spin"/> : <ArrowRightIcon className="h-4 w-4"/>}
                </button>
              </div>
            </form>
            {searchError && (
                <div className="absolute top-full left-0 mt-3 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-center gap-2 text-rose-400 text-sm">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500"></span> {searchError}
                </div>
            )}
          </div>
          </div>

          {/* MARKET DISCOVERY */}
          {!prediction && !loading && (
             <div className="space-y-5 animate-in fade-in duration-700">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <SparklesIcon className="h-4 w-4 text-indigo-400"/> Recommended Analysis
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                   {suggestions.map((s) => (
                      <button
                        key={s}
                        onClick={() => handlePredict(undefined, s)}
                        className="group relative flex items-center justify-between p-4 bg-[#11141d] border border-white/5 rounded-lg hover:border-indigo-500/30 hover:bg-white/5 transition-all overflow-hidden"
                      >
                         <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>

                         <div className="flex flex-col items-start gap-1 z-10">
                            <span className="text-lg font-bold text-white font-mono tracking-wider group-hover:text-indigo-300 transition-colors">
                                {s}
                            </span>
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-slate-500 bg-white/5 px-1.5 py-0.5 rounded border border-white/5 uppercase">US EQ</span>
                                <span className="text-[10px] font-medium text-slate-600 uppercase tracking-wider">Quick View</span>
                            </div>
                         </div>

                         <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/5 border border-white/5 group-hover:bg-indigo-500 group-hover:border-indigo-500 group-hover:text-white text-slate-500 transition-all z-10">
                            <ChartBarIcon className="h-4 w-4" />
                         </div>
                      </button>
                   ))}
                </div>
             </div>
          )}

          {/* PREDICTION RESULT */}
          {prediction && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <PredictionResult data={prediction} onSaveSuccess={() => {}} />
            </div>
          )}

          {/* MARKET PULSE */}
          {movers && (
            <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <span className="w-1 h-4 bg-indigo-500 rounded-full"></span> Market Pulse
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-[#151921] rounded-xl border border-white/5 p-5 hover:border-white/10 transition-colors">
                        <div className="flex items-center gap-2 mb-4 text-emerald-400">
                            <ArrowTrendingUpIcon className="h-4 w-4"/>
                            <span className="text-xs font-bold uppercase tracking-wider">Top Gainers</span>
                        </div>
                        <div className="space-y-3">
                            {movers.gainers?.slice(0,5).map((m: any) => (
                                <div key={m.symbol} className="flex justify-between items-center text-sm border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                    <span className="font-bold text-slate-200">{m.symbol}</span>
                                    <span className="text-emerald-400 font-mono">+{m.change_pct.toFixed(2)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="bg-[#151921] rounded-xl border border-white/5 p-5 hover:border-white/10 transition-colors">
                        <div className="flex items-center gap-2 mb-4 text-rose-400">
                            <ArrowTrendingDownIcon className="h-4 w-4"/>
                            <span className="text-xs font-bold uppercase tracking-wider">Top Losers</span>
                        </div>
                        <div className="space-y-3">
                            {movers.losers?.slice(0,5).map((m: any) => (
                                <div key={m.symbol} className="flex justify-between items-center text-sm border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                    <span className="font-bold text-slate-200">{m.symbol}</span>
                                    <span className="text-rose-400 font-mono">{m.change_pct.toFixed(2)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="bg-[#151921] rounded-xl border border-white/5 p-5 hover:border-white/10 transition-colors">
                        <div className="flex items-center gap-2 mb-4 text-amber-400">
                            <FireIcon className="h-4 w-4"/>
                            <span className="text-xs font-bold uppercase tracking-wider">Most Active</span>
                        </div>
                        <div className="space-y-3">
                            {movers.active?.slice(0,5).map((m: any) => (
                                <div key={m.symbol} className="flex justify-between items-center text-sm border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                    <span className="font-bold text-slate-200">{m.symbol}</span>
                                    <span className="text-slate-400 font-mono">${(m.price).toFixed(2)}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-4 space-y-6">
           <div className="sticky top-28 space-y-6">
                <div className="flex items-center justify-between bg-[#151921] border border-white/10 p-3 rounded-lg shadow-lg">
                     <span className="text-[10px] font-mono font-medium text-slate-400 tracking-wider uppercase">
                        Current Session
                     </span>
                     <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                        <div className={`w-2 h-2 rounded-full ${marketStatus.isOpen ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500'}`}></div>
                        <span className="text-[10px] font-mono font-bold text-slate-200 tracking-wider">
                            {marketStatus.text.split("•")[0]}
                        </span>
                    </div>
                </div>

                <div className="border border-white/10 rounded-xl overflow-hidden bg-[#151921] h-[500px] shadow-2xl">
                    {isMounted && <Timeline colorTheme="dark" feedMode="market" market="stock" height="100%" width="100%" />}
                </div>

                <div className="border border-white/10 rounded-xl bg-[#151921] p-1 shadow-lg">
                    {/* UPDATED COMPONENT */}
                    <SP500Reference onSelect={(sym) => handlePredict(undefined, sym)} />
                </div>
           </div>
        </div>
      </div>

      <div className="fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0B0E14] to-[#0B0E14] pointer-events-none"></div>
    </main>
  );
}