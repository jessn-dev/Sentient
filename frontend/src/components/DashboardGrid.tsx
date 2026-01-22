"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChartBarIcon } from "@heroicons/react/24/outline";

interface WatchlistItem {
    id: number;
    symbol: string;
    target_price: number;
    end_date: string;
}

export default function DashboardGrid({ refreshTrigger }: { refreshTrigger: number }) {
    const [items, setItems] = useState<WatchlistItem[]>([]);

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/watchlist/performance`)
            .then(r => r.json())
            .then(setItems)
            .catch(console.error);
    }, [refreshTrigger]);

    return (
        <div className="w-full">
            <div className="flex justify-between items-end mb-6">
                <div>
                    <h2 className="text-2xl font-black text-white mb-1">Your Watchlist</h2>
                    <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">Active Forecasts</p>
                </div>

                {/* NEW BUTTON */}
                <Link
                    href="/accuracy"
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-all text-xs font-bold uppercase tracking-wider group border border-slate-700 hover:border-blue-500/50"
                >
                    <ChartBarIcon className="h-4 w-4 text-blue-500 group-hover:text-blue-400" />
                    View Accuracy
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {items.length === 0 ? (
                    <div className="col-span-full p-8 text-center border border-dashed border-slate-800 rounded-2xl text-slate-600 font-medium">
                        No active forecasts. Search a stock to add one.
                    </div>
                ) : (
                    items.map((item) => (
                        <div key={item.id} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-blue-600/50 transition-colors group relative">
                            <div className="flex justify-between items-start mb-3">
                                <span className="text-xl font-black text-white">{item.symbol}</span>
                                <span className="text-[10px] font-mono text-slate-500">{item.end_date}</span>
                            </div>
                            <div className="flex items-end gap-2">
                                <div className="text-2xl font-bold text-blue-400">${item.target_price.toFixed(2)}</div>
                                <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">Target</div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}