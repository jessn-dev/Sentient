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
  ClockIcon
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
  const [selectedItem, setSelectedItem] = useState<PerformanceItem | null>(null);
  const [graphData, setGraphData] = useState<any[]>([]);
  const [loadingGraph, setLoadingGraph] = useState(false);

  // Fetch Data
  useEffect(() => {
    const fetchData = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { router.push('/login'); return; }

      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist/performance`, {
          headers: { "Authorization": `Bearer ${session.access_token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setItems(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error(error);
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

      // We always want to show the graph up to end_date, even if in future (it will just show data up to today)
      const fetchEnd = isFinal ? (selectedItem.finalized_date || selectedItem.end_date) : selectedItem.end_date;

      const endDateObj = new Date(fetchEnd);
      endDateObj.setDate(endDateObj.getDate() + 1); // +1 buffer
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

  // Calc Avg Precision (Only count Completed/Finalized items)
  const completedItems = items.filter(i => i.accuracy_score > 0);
  const avg = completedItems.length > 0
    ? (completedItems.reduce((a,b) => a + b.accuracy_score, 0) / completedItems.length).toFixed(1)
    : "0.0";

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 font-sans selection:bg-indigo-500/30 pb-20 relative overflow-hidden">

      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[128px] pointer-events-none" />

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
                                <th className="p-5 border-b border-white/5">Timeline</th>
                                <th className="p-5 border-b border-white/5">Entry</th>
                                <th className="p-5 border-b border-white/5">Target</th>
                                <th className="p-5 border-b border-white/5">Final</th>
                                <th className="p-5 border-b border-white/5">Accuracy Score</th>
                                <th className="p-5 border-b border-white/5 text-right">Analyze</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {items.map((i) => {
                                const isFinal = i.final_price !== null && i.final_price > 0;
                                const isPending = i.accuracy_score === 0;

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
                                                    <div className="text-[10px] text-slate-500 uppercase font-medium">{isFinal ? 'Completed' : 'Tracking'}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-5">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] text-slate-500 uppercase">Start</span>
                                                    <span className="text-xs text-slate-300 font-mono">{i.created_at.split('T')[0]}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] text-slate-500 uppercase">End</span>
                                                    <span className="text-xs text-indigo-300 font-mono">{i.end_date}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-5 font-mono text-slate-400 text-sm">${i.initial_price.toFixed(2)}</td>
                                        <td className="p-5 font-mono text-indigo-400 font-bold text-sm">${i.target_price.toFixed(2)}</td>
                                        <td className="p-5 font-mono text-white text-sm">
                                            {isFinal ? `$${i.final_price?.toFixed(2)}` : <span className="text-slate-600 italic">Pending</span>}
                                        </td>
                                        <td className="p-5">
                                            {isPending ? (
                                                <div className="flex items-center gap-2 text-slate-500 text-xs">
                                                    <ClockIcon className="h-3 w-3" /> In Progress
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-3">
                                                    <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full ${i.accuracy_score > 90 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                                                            style={{ width: `${i.accuracy_score}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs font-bold font-mono text-white">
                                                        {i.accuracy_score.toFixed(1)}%
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-5 text-right">
                                            <button
                                                onClick={() => setSelectedItem(i)}
                                                className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider text-slate-400 border border-slate-700 hover:text-white hover:border-indigo-500 hover:bg-indigo-500/10 transition-all flex items-center gap-2 ml-auto"
                                            >
                                                <ChartBarIcon className="h-3 w-3" /> Graph
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
                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                  {selectedItem.symbol} Performance
                </h2>
                <button onClick={() => setSelectedItem(null)} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                  <XMarkIcon className="h-5 w-5 text-slate-500 hover:text-white" />
                </button>
            </div>
            <div className="p-8 h-[400px] bg-[#151921] flex items-center justify-center">
              {loadingGraph ? <div className="text-slate-500 animate-pulse">Loading Data...</div> : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={graphData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{fontSize:10}} />
                    <YAxis domain={['auto','auto']} stroke="#64748b" tick={{fontSize:10}} />
                    <Tooltip contentStyle={{backgroundColor:'#0B0E14', borderColor:'#1e293b'}} />
                    <ReferenceLine y={selectedItem.target_price} label="Target" stroke="#ef4444" strokeDasharray="3 3" />
                    <ReferenceLine x={selectedItem.end_date} stroke="#64748b" label="End Date" />
                    <Line type="monotone" dataKey="price" stroke="#6366f1" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}