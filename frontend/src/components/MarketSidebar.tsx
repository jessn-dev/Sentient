"use client";

import { useEffect, useState } from "react";
import {
    ArrowTrendingUpIcon,
    ArrowTrendingDownIcon,
    BoltIcon,
    StarIcon
} from "@heroicons/react/24/outline";

interface StockItem {
    symbol: string;
    price: number;
    change_pct: number;
    is_up: boolean;
}

function StockRow({ symbol, price, change_pct, is_up }: StockItem) {
    return (
        <div className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0 hover:bg-slate-800/30 transition-colors px-2 rounded-md">
            <span className="font-bold text-sm text-blue-400">{symbol}</span>
            <div className="text-right">
                <div className="text-sm font-bold">${price.toFixed(2)}</div>
                <div className={`text-[10px] font-black ${is_up ? 'text-green-500' : 'text-red-500'}`}>
                    {is_up ? '+' : ''}{change_pct}%
                </div>
            </div>
        </div>
    );
}

function SidebarSection({ title, icon: Icon, stocks }: { title: string, icon: any, stocks: StockItem[] }) {
    if (!stocks || stocks.length === 0) return null;
    return (
        <div className="mb-4 bg-slate-900/50 rounded-xl p-4 border border-slate-800 shadow-sm">
            <h3 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">
                <Icon className="h-3.5 w-3.5" />
                {title}
            </h3>
            <div className="space-y-1">
                {stocks.map((s) => <StockRow key={s.symbol} {...s} />)}
            </div>
        </div>
    );
}

export default function MarketSidebar() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/market/movers`);
                if (res.ok) setData(await res.json());
            } catch (e) { console.error("Sidebar Fetch Failed", e); }
        };
        fetchData();
        const interval = setInterval(fetchData, 60000); // Live poll every minute
        return () => clearInterval(interval);
    }, []);

    return (
        <aside className="w-full lg:w-80 flex flex-col gap-1">
            {/* 1. Top Tickers (Now at the top below Status) */}
            <SidebarSection title="Top Tickers" icon={StarIcon} stocks={data?.top_tickers} />

            {/* 2. Top Gainers */}
            <SidebarSection title="Top Gainers" icon={ArrowTrendingUpIcon} stocks={data?.gainers} />

            {/* 3. Top Losers */}
            <SidebarSection title="Top Losers" icon={ArrowTrendingDownIcon} stocks={data?.losers} />

            {/* 4. Most Active (Replaced Pulse) */}
            <SidebarSection title="Most Active" icon={BoltIcon} stocks={data?.active} />

            {/* Timestamp */}
            {data?.last_updated && (
                <div className="text-[9px] text-center text-slate-600 font-bold uppercase tracking-tighter">
                    Live Data • S&P 500 Index Only
                </div>
            )}
        </aside>
    );
}