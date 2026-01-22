"use client";

import { useState, useEffect } from "react";
import {
    ArrowTrendingUpIcon,
    ArrowTrendingDownIcon,
    BoltIcon
} from "@heroicons/react/24/solid";

interface MoverItem {
    symbol: string;
    price: number;
    change_pct: number;
    volume: string;
}

interface MoversData {
    gainers: MoverItem[];
    losers: MoverItem[];
    active: MoverItem[];
}

export default function MarketMovers() {
    const [data, setData] = useState<MoversData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"gainers" | "losers" | "active">("active");

    useEffect(() => {
        const fetchMovers = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/market/movers`);
                if (res.ok) setData(await res.json());
            } catch (e) {
                console.error("Failed to fetch movers", e);
            } finally {
                setLoading(false);
            }
        };
        fetchMovers();
    }, []);

    const getList = () => {
        if (!data) return [];
        return data[activeTab];
    };

    if (loading) return (
        <div className="h-[45%] bg-slate-900/50 border-b border-slate-800 flex items-center justify-center">
            <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="h-[45%] flex flex-col bg-slate-900/50 border-b border-slate-800 overflow-hidden">

            {/* Header / Tabs */}
            <div className="flex border-b border-slate-800 bg-slate-950/30">
                <button
                    onClick={() => setActiveTab("active")}
                    className={`flex-1 py-3 text-[10px] font-black uppercase tracking-wider flex items-center justify-center gap-1 transition-colors ${activeTab === 'active' ? 'text-blue-400 bg-blue-900/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    <BoltIcon className="h-3 w-3" /> Active
                </button>
                <button
                    onClick={() => setActiveTab("gainers")}
                    className={`flex-1 py-3 text-[10px] font-black uppercase tracking-wider flex items-center justify-center gap-1 transition-colors ${activeTab === 'gainers' ? 'text-green-400 bg-green-900/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    <ArrowTrendingUpIcon className="h-3 w-3" /> Gainers
                </button>
                <button
                    onClick={() => setActiveTab("losers")}
                    className={`flex-1 py-3 text-[10px] font-black uppercase tracking-wider flex items-center justify-center gap-1 transition-colors ${activeTab === 'losers' ? 'text-red-400 bg-red-900/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    <ArrowTrendingDownIcon className="h-3 w-3" /> Losers
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
                <div className="px-3 py-2 flex justify-between text-[10px] font-bold text-slate-600 uppercase">
                    <span>Symbol</span>
                    <div className="flex gap-4">
                        <span>Price</span>
                        <span className="w-12 text-right">Chg%</span>
                    </div>
                </div>

                {getList().map((item) => (
                    <div key={item.symbol} className="flex items-center justify-between p-3 hover:bg-slate-800/50 rounded-lg group transition-colors cursor-default">
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-slate-200">{item.symbol}</span>
                        </div>
                        <div className="text-right flex items-center gap-4">
                            <span className="text-xs font-mono text-slate-400">${item.price.toFixed(2)}</span>
                            <span className={`w-12 text-xs font-bold ${item.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {item.change_pct > 0 ? '+' : ''}{item.change_pct}%
                 </span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="py-1 bg-slate-950 text-center border-t border-slate-800">
                <span className="text-[9px] text-slate-600 font-bold uppercase tracking-widest">S&P 500 Data • Delayed 15m</span>
            </div>
        </div>
    );
}