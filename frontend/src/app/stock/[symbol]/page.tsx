"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import PredictionResult from "@/components/PredictionResult";
import {
  ArrowLeftIcon,
  ChatBubbleBottomCenterTextIcon,
  NewspaperIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ScaleIcon,                // Lawsuit Icon
  ExclamationTriangleIcon,  // Warning Icon
  BanknotesIcon,            // Fund Flow Icon
  ChartBarIcon,             // Options Icon
  ArrowTopRightOnSquareIcon
} from "@heroicons/react/24/solid";
import dynamic from "next/dynamic";

// --- DYNAMIC IMPORTS ---
const AdvancedRealTimeChart = dynamic(
  () => import("react-ts-tradingview-widgets").then((mod) => mod.AdvancedRealTimeChart),
  { ssr: false }
);

const CompanyProfile = dynamic(
  () => import("react-ts-tradingview-widgets").then((mod) => mod.CompanyProfile),
  { ssr: false }
);

export default function StockDetailsPage() {
  const params = useParams();
  const symbol = typeof params.symbol === 'string' ? params.symbol.toUpperCase() : "AAPL";

  const [session, setSession] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [marketData, setMarketData] = useState<any>(null); // ✅ Real-Time Market Data
  const [messages, setMessages] = useState<any[]>([]);     // ✅ Sentiment Messages
  const [loading, setLoading] = useState(true);
  const [sentimentTab, setSentimentTab] = useState<"informative" | "emotional">("informative");

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    fetchData(symbol);
  }, [symbol]);

  const fetchData = async (sym: string) => {
    setLoading(true);
    try {
      // 1. Fetch AI Prediction
      const predRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: sym, days: 7 }),
      });
      if (predRes.ok) setPrediction(await predRes.json());

      // 2. Fetch Deep Sentiment (News + Social + Legal + Macro)
      const sentRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/sentiment/${sym}`);
      if (sentRes.ok) {
        const sentData = await sentRes.json();
        setMessages(sentData.messages || []);
      }

      // 3. Fetch Market Depth (Options + Fund Flows)
      const mktRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/market/data/${sym}`);
      if (mktRes.ok) setMarketData(await mktRes.json());

    } catch (e) {
      console.error("Data Load Error:", e);
    }
    setLoading(false);
  };

  // --- HELPERS ---
  const formatNumber = (num: number) => {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + "B";
    if (num >= 1e6) return (num / 1e6).toFixed(2) + "M";
    return num.toLocaleString();
  };

  const informativeMsgs = messages.filter(m => m.type === "informative");
  const emotionalMsgs = messages.filter(m => m.type === "emotional");

  const posCount = messages.filter(m => m.sentiment === "positive").length;
  const negCount = messages.filter(m => m.sentiment === "negative").length;
  const totalMsgs = messages.length || 1;
  const sentimentScore = Math.round((posCount / totalMsgs) * 100);

  // Check for Lawsuits
  const hasLegalTrouble = messages.some(m => m.is_lawsuit);

  if (loading) return (
    <div className="min-h-screen bg-[#0B0E14] text-white flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <div className="text-sm font-bold uppercase tracking-widest text-slate-500">Scanning Market Intelligence...</div>
    </div>
  );

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 font-sans selection:bg-indigo-500/30 pb-20">

      {/* HEADER */}
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-[#0B0E14]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex justify-between items-center py-4 px-6">
            <div className="flex items-center gap-4">
               <Link href="/" className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                  <ArrowLeftIcon className="h-5 w-5" />
               </Link>
               <h1 className="text-xl font-bold tracking-tight text-white leading-none">
                 {symbol} <span className="text-indigo-500">ANALYSIS</span>
               </h1>
            </div>

            <div className="flex items-center gap-4">
              {session ? (
                  <button className="text-xs font-bold text-rose-400 hover:text-rose-300 uppercase tracking-widest">Sign Out</button>
              ) : (
                  <Link href="/login" className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-bold transition-all shadow-lg shadow-indigo-500/20 uppercase tracking-wider">
                    Get Access
                  </Link>
              )}
            </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 p-6 lg:pt-8">

        {/* LEFT COLUMN (Charts & Data) */}
        <div className="lg:col-span-8 flex flex-col gap-8">

            {/* TRADINGVIEW CHART */}
            <div className="h-[500px] w-full bg-[#151921] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
               <AdvancedRealTimeChart
                  symbol={symbol}
                  theme="dark"
                  autosize
                  hide_side_toolbar={false}
                  enable_publishing={false}
                  allow_symbol_change={false}
               />
            </div>

            {/* PREDICTION CARD */}
            {prediction && (
                <PredictionResult
                   data={prediction}
                   detailed={true}
                   onSaveSuccess={() => {}}
                />
            )}

            {/* ✅ MARKET DEPTH SECTION (Options & Funds) */}
            {marketData && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                  {/* OPTIONS SENTIMENT CARD */}
                  <div className="bg-[#151921] border border-white/10 rounded-xl p-6 shadow-xl">
                      <h3 className="text-white font-bold flex items-center gap-2 mb-4">
                          <ChartBarIcon className="h-5 w-5 text-indigo-500"/> Options Flow
                      </h3>
                      {marketData.options_sentiment ? (
                          <div className="space-y-4">
                              <div className="flex justify-between text-xs text-slate-400 uppercase tracking-wider font-bold">
                                  <span>Calls (Bullish)</span>
                                  <span>Puts (Bearish)</span>
                              </div>
                              {/* Visual Bar */}
                              <div className="h-4 bg-slate-800 rounded-full flex overflow-hidden">
                                  <div
                                    style={{ width: `${(marketData.options_sentiment.total_call_vol / (marketData.options_sentiment.total_call_vol + marketData.options_sentiment.total_put_vol)) * 100}%` }}
                                    className="bg-emerald-500 h-full"
                                  ></div>
                                  <div className="bg-rose-500 h-full flex-1"></div>
                              </div>
                              <div className="flex justify-between text-sm font-mono text-white">
                                  <span>{formatNumber(marketData.options_sentiment.total_call_vol)}</span>
                                  <span>{formatNumber(marketData.options_sentiment.total_put_vol)}</span>
                              </div>
                              <div className="pt-4 border-t border-white/5 grid grid-cols-2 gap-4">
                                  <div>
                                      <p className="text-[10px] text-slate-500 uppercase">Put/Call Ratio</p>
                                      <p className={`text-lg font-bold ${marketData.options_sentiment.put_call_ratio > 1 ? 'text-rose-400' : 'text-emerald-400'}`}>
                                          {marketData.options_sentiment.put_call_ratio}
                                      </p>
                                  </div>
                                  <div>
                                      <p className="text-[10px] text-slate-500 uppercase">Implied Volatility</p>
                                      <p className="text-lg font-bold text-indigo-400">{marketData.options_sentiment.implied_volatility}%</p>
                                  </div>
                              </div>
                          </div>
                      ) : (
                          <p className="text-slate-500 text-sm">Options data unavailable for {symbol}.</p>
                      )}
                  </div>

                  {/* FUND FLOW CARD */}
                  <div className="bg-[#151921] border border-white/10 rounded-xl p-6 shadow-xl">
                      <h3 className="text-white font-bold flex items-center gap-2 mb-4">
                          <BanknotesIcon className="h-5 w-5 text-emerald-500"/> Institutional Money
                      </h3>
                      <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                                <p className="text-[10px] text-slate-500 uppercase">Inst. Ownership</p>
                                <p className="text-lg font-bold text-white">{marketData.institutional_ownership}%</p>
                          </div>
                          <div>
                                <p className="text-[10px] text-slate-500 uppercase">Short Interest</p>
                                <p className="text-lg font-bold text-amber-400">{marketData.short_float}%</p>
                          </div>
                      </div>
                      <div className="space-y-2">
                          <p className="text-[10px] text-slate-500 uppercase font-bold">Top Holders</p>
                          {marketData.top_holders.length > 0 ? (
                            marketData.top_holders.slice(0, 3).map((h: any, i: number) => (
                                <div key={i} className="flex justify-between text-xs text-slate-300 border-b border-white/5 pb-1 last:border-0">
                                    <span className="truncate w-32" title={h.holder}>{h.holder}</span>
                                    <span className="font-mono text-emerald-400">{formatNumber(h.shares)}</span>
                                </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-500 italic">No holder data available.</p>
                          )}
                      </div>
                  </div>
              </div>
            )}

            {/* ✅ SENTIMENT DASHBOARD */}
            <div className="bg-[#151921] border border-white/10 rounded-xl overflow-hidden shadow-2xl">

                {/* ALERT BANNER */}
                {hasLegalTrouble && (
                   <div className="bg-rose-500/10 border-b border-rose-500/20 p-4 flex items-center gap-3 animate-pulse">
                      <ExclamationTriangleIcon className="h-5 w-5 text-rose-500" />
                      <div>
                        <h4 className="text-rose-400 font-bold text-sm uppercase tracking-wider">Legal Risk Detected</h4>
                        <p className="text-rose-400/80 text-xs">AI has detected active litigation or fraud allegations in recent news.</p>
                      </div>
                   </div>
                )}

                <div className="p-6 border-b border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <ChatBubbleBottomCenterTextIcon className="h-5 w-5 text-indigo-500" />
                            AI Sentiment Engine
                        </h3>
                        <p className="text-sm text-slate-400 mt-1">
                            Scanned {messages.length} recent articles & signals
                        </p>
                    </div>

                    {/* Sentiment Badge */}
                    <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-lg border border-white/5">
                        <div className="text-right">
                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Bullish Score</div>
                            <div className={`text-xl font-mono font-bold ${sentimentScore > 50 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {sentimentScore}%
                            </div>
                        </div>
                        <div className={`h-10 w-1 rounded-full ${sentimentScore > 50 ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                    </div>
                </div>

                {/* DISTRIBUTION BAR */}
                <div className="px-6 py-6 border-b border-white/5">
                    <div className="flex justify-between text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
                        <span className="text-rose-400 flex items-center gap-1"><ArrowTrendingDownIcon className="h-3 w-3" /> Negative ({negCount})</span>
                        <span className="text-emerald-400 flex items-center gap-1">Positive ({posCount}) <ArrowTrendingUpIcon className="h-3 w-3" /></span>
                    </div>
                    <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden flex">
                        <div style={{ width: `${100 - sentimentScore}%` }} className="h-full bg-rose-500 transition-all duration-1000"></div>
                        <div style={{ width: `${sentimentScore}%` }} className="h-full bg-emerald-500 transition-all duration-1000"></div>
                    </div>
                </div>

                {/* TABS & MESSAGES */}
                <div className="p-6">
                    <div className="flex gap-4 mb-6">
                        <button
                            onClick={() => setSentimentTab("informative")}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all border ${sentimentTab === 'informative' ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-[#0B0E14] border-white/10 text-slate-400 hover:text-white'}`}
                        >
                            <div className="flex items-center justify-center gap-2"><NewspaperIcon className="h-4 w-4" /> Informative</div>
                        </button>
                        <button
                            onClick={() => setSentimentTab("emotional")}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all border ${sentimentTab === 'emotional' ? 'bg-amber-600 border-amber-500 text-white shadow-lg shadow-amber-500/20' : 'bg-[#0B0E14] border-white/10 text-slate-400 hover:text-white'}`}
                        >
                            <div className="flex items-center justify-center gap-2"><FireIcon className="h-4 w-4" /> Emotional / Hype</div>
                        </button>
                    </div>

                    <div className="space-y-3">
                        {(sentimentTab === 'informative' ? informativeMsgs : emotionalMsgs).map((msg, i) => (
                            <div key={i} className={`p-4 border rounded-lg transition-colors group ${msg.is_lawsuit ? 'bg-rose-950/10 border-rose-500/30 hover:border-rose-500/50' : 'bg-[#0B0E14] border-white/5 hover:border-white/10'}`}>
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex gap-2">
                                        {/* Law Badge */}
                                        {msg.is_lawsuit && (
                                            <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider bg-rose-500 text-white border-rose-500 flex items-center gap-1">
                                                <ScaleIcon className="h-3 w-3"/> Litigation
                                            </span>
                                        )}
                                        {/* Sentiment Badge */}
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${msg.sentiment === 'positive' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : msg.sentiment === 'negative' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-slate-500/10 text-slate-400 border-slate-500/20'}`}>
                                            {msg.sentiment}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                                            {msg.source}
                                        </span>
                                        <a href={msg.url} target="_blank" rel="noopener noreferrer" className="text-slate-600 hover:text-indigo-400 transition-colors">
                                            <ArrowTopRightOnSquareIcon className="h-3 w-3" />
                                        </a>
                                    </div>
                                </div>
                                <p className="text-sm text-slate-300 leading-relaxed group-hover:text-white transition-colors line-clamp-2">
                                    "{msg.text}"
                                </p>
                            </div>
                        ))}
                        {(sentimentTab === 'informative' ? informativeMsgs : emotionalMsgs).length === 0 && (
                            <div className="text-center py-8 text-slate-500 text-xs italic">No recent messages in this category.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>

        {/* RIGHT COLUMN (Company Profile) */}
        <div className="lg:col-span-4 space-y-8">
            <div className="sticky top-24">
                <div className="bg-[#151921] border border-white/10 rounded-xl overflow-hidden shadow-lg mb-8">
                    <CompanyProfile
                        symbol={symbol}
                        colorTheme="dark"
                        height={400}
                        width="100%"
                        isTransparent={true}
                    />
                </div>

                {!session && (
                    <div className="p-6 bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border border-indigo-500/20 rounded-xl text-center">
                        <div className="text-white font-bold mb-2">Unlock Deep Data</div>
                        <p className="text-xs text-slate-400 mb-4">Sign in to track your portfolio.</p>
                        <Link href="/login" className="block w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all">
                            Log In
                        </Link>
                    </div>
                )}
            </div>
        </div>
      </div>
    </main>
  );
}