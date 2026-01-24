"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import {
  ArrowLeftIcon,
  TrophyIcon,
  LockClosedIcon,
  ChartBarIcon,
  XMarkIcon,
  CalendarDaysIcon,
  ClockIcon,
  CheckBadgeIcon
} from "@heroicons/react/24/solid";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceDot
} from 'recharts';

interface PerformanceItem {
  id: number;
  symbol: string;
  initial_price: number;
  target_price: number;
  current_price: number;
  final_price: number | null;
  created_at: string;
  end_date: string;
  finalized_date?: string;
  accuracy_score: number;
  status: string;
}

export default function AccuracyPage() {
  const [items, setItems] = useState<PerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Modal State
  const [selectedItem, setSelectedItem] = useState<PerformanceItem | null>(null);
  const [graphData, setGraphData] = useState<any[]>([]);
  const [loadingGraph, setLoadingGraph] = useState(false);

  // 1. FETCH DATA WITH AUTH
  useEffect(() => {
    const fetchData = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/login');
        return;
      }

      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist/performance`, {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setItems(data);
          } else {
            setItems([]);
          }
        }
      } catch (error) {
        console.error("Network error:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  // Fetch Graph Data
  useEffect(() => {
    if (selectedItem) {
      setLoadingGraph(true);
      const isFinal = selectedItem.final_price !== null && selectedItem.final_price > 0;
      const today = new Date().toISOString().split('T')[0];

      const fetchEnd = isFinal
        ? (selectedItem.finalized_date || selectedItem.end_date)
        : today;

      const endDateObj = new Date(fetchEnd);
      endDateObj.setDate(endDateObj.getDate() + 1);
      const endStr = endDateObj.toISOString().split('T')[0];

      fetch(`${process.env.NEXT_PUBLIC_API_URL}/history/${selectedItem.symbol}?start=${selectedItem.created_at}&end=${endStr}`)
        .then(r => r.json())
        .then(data => {
          setGraphData(Array.isArray(data) ? data : []);
          setLoadingGraph(false);
        })
        .catch(() => {
          setGraphData([]);
          setLoadingGraph(false);
        });
    }
  }, [selectedItem]);

  const avg = items.length > 0 ? (items.reduce((a,b)=>a+b.accuracy_score,0)/items.length).toFixed(1) : "0.0";

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 font-sans selection:bg-indigo-500/30 pb-20 relative overflow-hidden">

      {/* Background Decor */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[128px] pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-[#0B0E14]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex justify-between items-center py-4 px-6">
            <div className="flex items-center gap-4">
               <Link href="/" className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                  <ArrowLeftIcon className="h-5 w-5" />
               </Link>
               <h1 className="text-xl font-bold tracking-tight text-white leading-none">
                 PREDICTION <span className="text-indigo-500">ACCURACY</span>
               </h1>
            </div>

            <div className="flex items-center gap-4">
                <div className="text-right">
                    <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Avg Precision</p>
                    <p className="text-xl font-mono font-bold text-emerald-400">{avg}%</p>
                </div>
                <div className="h-8 w-8 bg-indigo-500/20 rounded-full flex items-center justify-center border border-indigo-500/30">
                    <TrophyIcon className="h-4 w-4 text-indigo-400" />
                </div>
            </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6 lg:pt-8 relative z-10">
        <div className="bg-[#151921] border border-white/10 rounded-xl overflow-hidden shadow-2xl">

            {loading ? (
                <div className="p-12 text-center flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-sm font-bold uppercase tracking-widest text-slate-500">Loading Portfolio...</div>
                </div>
            ) : items.length === 0 ? (
                <div className="p-20 text-center">
                    <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6">
                        <ClockIcon className="h-8 w-8 text-slate-600" />
                    </div>
                    <h3 className="text-lg font-bold text-white mb-2">No Predictions Yet</h3>
                    <p className="text-slate-400 text-sm mb-6">Start tracking stocks to see AI performance history.</p>
                    <Link href="/" className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all">
                        Track a Stock
                    </Link>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-[#0B0E14] text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                            <tr>
                                <th className="p-5 border-b border-white/5">Asset</th>
                                <th className="p-5 border-b border-white/5">Entry</th>
                                <th className="p-5 border-b border-white/5">Target</th>
                                <th className="p-5 border-b border-white/5">Current / Final</th>
                                <th className="p-5 border-b border-white/5">Timeline</th>
                                <th className="p-5 border-b border-white/5">Accuracy Score</th>
                                <th className="p-5 border-b border-white/5 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {items.map((i) => {
                                const isFinal = i.final_price !== null && i.final_price > 0;
                                const isWeekendAdj = i.finalized_date && i.finalized_date !== i.end_date;
                                const isSuccess = i.accuracy_score > 90;

                                return (
                                    <tr key={i.id} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="p-5">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold ${isFinal ? 'bg-slate-800 text-slate-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                                                    {i.symbol.substring(0,1)}
                                                </div>
                                                <div>
                                                    <div className="text-sm font-bold text-white flex items-center gap-2">
                                                        {i.symbol}
                                                        {isFinal && <LockClosedIcon className="h-3 w-3 text-slate-500" title="Finalized" />}
                                                    </div>
                                                    <div className="text-[10px] text-slate-500 uppercase font-medium">{isFinal ? 'Completed' : 'Active'}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-5 font-mono text-slate-400 text-sm">${i.initial_price.toFixed(2)}</td>
                                        <td className="p-5 font-mono text-indigo-400 font-bold text-sm">${i.target_price.toFixed(2)}</td>
                                        <td className="p-5 font-mono text-white text-sm">
                                            ${i.current_price.toFixed(2)}
                                            {isFinal && <span className="ml-2 text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-bold uppercase">FINAL</span>}
                                        </td>
                                        <td className="p-5">
                                            <div className="flex flex-col">
                                                <span className="text-xs text-slate-300 font-medium">{i.end_date}</span>
                                                {isWeekendAdj && (
                                                    <span className="text-[10px] text-amber-500/80 flex items-center gap-1 mt-1 font-medium">
                                                        <CalendarDaysIcon className="h-3 w-3" /> Wknd Adj.
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="p-5">
                                            <div className="flex items-center gap-3">
                                                <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full transition-all duration-500 ${isSuccess ? 'bg-emerald-500' : i.accuracy_score > 70 ? 'bg-indigo-500' : 'bg-rose-500'}`}
                                                        style={{ width: `${i.accuracy_score}%` }}
                                                    />
                                                </div>
                                                <span className={`text-xs font-bold font-mono ${isSuccess ? 'text-emerald-400' : 'text-slate-400'}`}>
                                                    {i.accuracy_score.toFixed(1)}%
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-5 text-right">
                                            <button
                                                onClick={() => setSelectedItem(i)}
                                                className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider text-slate-400 border border-slate-700 hover:text-white hover:border-indigo-500 hover:bg-indigo-500/10 transition-all flex items-center gap-2 ml-auto"
                                            >
                                                <ChartBarIcon className="h-3 w-3" /> Analyze
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
      </div>

      {/* GRAPH MODAL */}
      {selectedItem && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="bg-[#151921] border border-white/10 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl relative">

            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-[#0B0E14]">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                  {selectedItem.symbol} Performance
                  <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider ${selectedItem.accuracy_score > 90 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'}`}>
                    {selectedItem.accuracy_score > 90 ? 'High Accuracy' : 'Tracking'}
                  </span>
                </h2>
                <p className="text-slate-400 text-xs mt-1">
                  Prediction Window: <span className="text-indigo-400 font-mono">{selectedItem.created_at}</span> to <span className="text-indigo-400 font-mono">{selectedItem.end_date}</span>
                </p>
              </div>
              <button onClick={() => setSelectedItem(null)} className="p-2 hover:bg-white/5 rounded-full transition-colors group">
                <XMarkIcon className="h-5 w-5 text-slate-500 group-hover:text-white" />
              </button>
            </div>

            <div className="p-8 h-[400px] bg-[#151921] flex items-center justify-center relative">
              {loadingGraph ? (
                <div className="text-slate-500 animate-pulse text-xs font-bold uppercase tracking-widest">Loading Chart Data...</div>
              ) : graphData.length > 0 && graphData[0].message ? (
                 <div className="text-center">
                    <div className="mb-4 flex justify-center">
                       <div className="h-12 w-12 bg-slate-800 rounded-full flex items-center justify-center">
                          <ClockIcon className="h-6 w-6 text-slate-500" />
                       </div>
                    </div>
                    <h3 className="text-sm font-bold text-white mb-1 uppercase tracking-wide">Prediction Pending</h3>
                    <p className="text-slate-500 text-xs max-w-xs mx-auto">
                       Price history graph will become available as we collect daily closing data.
                    </p>
                 </div>
              ) : graphData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={graphData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 10}} tickLine={false} axisLine={false} />
                    <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{fontSize: 10}} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0B0E14', borderColor: '#1e293b', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: '#fff', fontSize: '12px' }}
                        cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '4 4' }}
                    />
                    <ReferenceLine y={selectedItem.target_price} label={{ value: 'TARGET', fill: '#ef4444', fontSize: 10, position: 'right' }} stroke="#ef4444" strokeDasharray="3 3" />
                    <ReferenceLine x={selectedItem.end_date} stroke="#64748b" strokeDasharray="3 3" />

                    {selectedItem.finalized_date && selectedItem.finalized_date !== selectedItem.end_date && (
                       <ReferenceDot
                          x={selectedItem.finalized_date}
                          y={selectedItem.final_price || 0}
                          r={4}
                          fill="#f59e0b"
                          stroke="none"
                       />
                    )}

                    <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#6366f1', strokeWidth: 0 }}
                        activeDot={{ r: 6, fill: '#818cf8', stroke: '#fff', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-slate-500 text-xs italic">No price history available.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}