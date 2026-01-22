"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeftIcon, TrophyIcon, LockClosedIcon, ChartBarIcon, XMarkIcon, CalendarDaysIcon } from "@heroicons/react/24/solid";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceDot } from 'recharts';

interface PerformanceItem {
    id: number;
    symbol: string;
    initial_price: number;
    target_price: number;
    current_price: number;
    final_price: number | null;
    created_at: string;
    end_date: string;
    finalized_date?: string; // New Field
    accuracy_score: number;
    status: string;
}

export default function AccuracyPage() {
    const [items, setItems] = useState<PerformanceItem[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal State
    const [selectedItem, setSelectedItem] = useState<PerformanceItem | null>(null);
    const [graphData, setGraphData] = useState<any[]>([]);
    const [loadingGraph, setLoadingGraph] = useState(false);

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist/performance`)
            .then(r => r.json())
            .then(data => {
                setItems(data);
                setLoading(false);
            });
    }, []);

    // Fetch Graph Data
    useEffect(() => {
        if (selectedItem) {
            setLoadingGraph(true);
            const isFinal = selectedItem.final_price !== null;
            const today = new Date().toISOString().split('T')[0];

            // If finalized_date exists (weekend adjustment), use that. Otherwise use end_date.
            const fetchEnd = isFinal
                ? (selectedItem.finalized_date || selectedItem.end_date)
                : today;

            // Add 1 day buffer for API
            const endDateObj = new Date(fetchEnd);
            endDateObj.setDate(endDateObj.getDate() + 1);
            const endStr = endDateObj.toISOString().split('T')[0];

            fetch(`${process.env.NEXT_PUBLIC_API_URL}/history/${selectedItem.symbol}?start=${selectedItem.created_at}&end=${endStr}`)
                .then(r => r.json())
                .then(data => {
                    setGraphData(data);
                    setLoadingGraph(false);
                });
        }
    }, [selectedItem]);

    const avg = items.length > 0 ? (items.reduce((a,b)=>a+b.accuracy_score,0)/items.length).toFixed(1) : "0.0";

    return (
        <main className="min-h-screen bg-[#020617] text-white p-8 relative">
            <div className="max-w-6xl mx-auto mb-10 flex justify-between items-center">
                <div>
                    <Link href="/" className="flex items-center gap-2 text-slate-400 mb-4 text-xs uppercase font-bold hover:text-white transition-colors"><ArrowLeftIcon className="h-4 w-4"/> Return to Dashboard</Link>
                    <h1 className="text-4xl font-black flex items-center gap-3">Prediction Tracker <TrophyIcon className="h-8 w-8 text-yellow-500"/></h1>
                    <p className="text-slate-500 mt-2">Historical performance of your 7-day AI forecasts.</p>
                </div>
                <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-center"><div className="text-xs font-bold text-slate-500 uppercase">Avg Precision</div><div className="text-4xl font-black text-blue-400">{avg}%</div></div>
            </div>

            <div className="max-w-6xl mx-auto bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
                {loading ? <div className="p-12 text-center text-slate-500 animate-pulse">Analyzing historical data...</div> : (
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-950 text-xs font-bold uppercase text-slate-500">
                        <tr>
                            <th className="p-4">Symbol</th>
                            <th className="p-4">Start Price</th>
                            <th className="p-4">Target</th>
                            <th className="p-4">Result Price</th>
                            <th className="p-4">End Date</th>
                            <th className="p-4">Accuracy</th>
                            <th className="p-4 text-right">Actions</th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                        {items.map(i => {
                            const isFinal = i.final_price !== null && i.final_price > 0;
                            // Check if weekend adjustment happened
                            const isWeekendAdj = i.finalized_date && i.finalized_date !== i.end_date;

                            return (
                                <tr key={i.id} className={`hover:bg-slate-800/30 transition-colors ${isFinal ? 'opacity-70 grayscale-[0.3]' : ''}`}>
                                    <td className="p-4 font-black flex items-center gap-2">
                                        {i.symbol}
                                        {isFinal && <LockClosedIcon className="h-3 w-3 text-slate-500" title="Finalized" />}
                                    </td>
                                    <td className="p-4 font-mono text-slate-400">${i.initial_price.toFixed(2)}</td>
                                    <td className="p-4 font-mono text-blue-400 font-bold">${i.target_price.toFixed(2)}</td>
                                    <td className="p-4 font-mono text-white">
                                        ${i.current_price.toFixed(2)}
                                        {isFinal && <span className="ml-2 text-[10px] text-slate-500 uppercase font-bold">(Final)</span>}
                                    </td>
                                    <td className="p-4 text-xs font-bold text-slate-500 flex flex-col">
                                        <span>{i.end_date}</span>
                                        {isWeekendAdj && (
                                            <span className="text-[10px] text-orange-400 flex items-center gap-1 mt-0.5" title={`Closed on weekend. Finalized on ${i.finalized_date}`}>
                             <CalendarDaysIcon className="h-3 w-3"/> Weekend Adj.
                           </span>
                                        )}
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                <div className={`h-full ${i.accuracy_score > 90 ? 'bg-green-500' : 'bg-blue-500'}`} style={{width: `${i.accuracy_score}%`}}/>
                                            </div>
                                            <span className="text-xs font-bold">{i.accuracy_score}%</span>
                                        </div>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button onClick={() => setSelectedItem(i)} className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-bold text-white flex items-center gap-2 ml-auto transition-colors">
                                            <ChartBarIcon className="h-3 w-3" /> View Graph
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                        </tbody>
                    </table>
                )}
            </div>

            {/* 4XL MODAL */}
            {selectedItem && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl relative">

                        {/* Modal Header */}
                        <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-950">
                            <div>
                                <h2 className="text-2xl font-black text-white flex items-center gap-3">
                                    {selectedItem.symbol} Performance
                                    <span className={`px-2 py-0.5 text-xs rounded uppercase ${selectedItem.status.includes('SUCCESS') ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                    {selectedItem.status}
                  </span>
                                </h2>
                                <p className="text-slate-400 text-sm mt-1">
                                    Prediction Window: <span className="text-white font-mono">{selectedItem.created_at}</span> to <span className="text-white font-mono">{selectedItem.end_date}</span>
                                </p>
                                {selectedItem.finalized_date && selectedItem.finalized_date !== selectedItem.end_date && (
                                    <p className="text-orange-400 text-xs mt-1 font-bold flex items-center gap-1">
                                        <CalendarDaysIcon className="h-3 w-3"/>
                                        Market closed on target date. Result taken on next open: {selectedItem.finalized_date}
                                    </p>
                                )}
                            </div>
                            <button onClick={() => setSelectedItem(null)} className="p-2 hover:bg-slate-800 rounded-full transition-colors">
                                <XMarkIcon className="h-6 w-6 text-slate-400 hover:text-white" />
                            </button>
                        </div>

                        {/* Modal Content (Graph) */}
                        <div className="p-8 h-[500px] bg-slate-900">
                            {loadingGraph ? (
                                <div className="h-full flex items-center justify-center text-slate-500 animate-pulse">Loading Chart Data...</div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={graphData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 12}} />
                                        <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{fontSize: 12}} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff' }} itemStyle={{ color: '#fff' }} />

                                        {/* Visual Reference Lines */}
                                        <ReferenceLine y={selectedItem.target_price} label="Target" stroke="red" strokeDasharray="3 3" />
                                        <ReferenceLine x={selectedItem.end_date} stroke="gray" strokeDasharray="3 3" label={{ value: 'Target Date', position: 'insideTopLeft', fill: 'gray', fontSize: 10 }} />

                                        {/* Special Dot for Weekend Adjustment */}
                                        {selectedItem.finalized_date && selectedItem.finalized_date !== selectedItem.end_date && (
                                            <ReferenceDot
                                                x={selectedItem.finalized_date}
                                                y={selectedItem.final_price || 0}
                                                r={6}
                                                fill="#fb923c"
                                                stroke="white"
                                                label={{ value: 'Adj. Result', position: 'top', fill: '#fb923c', fontSize: 10, fontWeight: 'bold' }}
                                            />
                                        )}

                                        <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 8 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-between text-xs text-slate-500 font-mono">
                            <span>Start: ${selectedItem.initial_price.toFixed(2)}</span>
                            <span>Target: ${selectedItem.target_price.toFixed(2)}</span>
                            <span>Current: ${selectedItem.current_price.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}