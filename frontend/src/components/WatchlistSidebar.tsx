'use client';

import { useState, useEffect } from 'react';
import { X, Plus, TrendingUp, Menu, RefreshCw } from 'lucide-react';

interface Props {
    onSelect: (symbol: string) => void;
    isOpen: boolean;
    toggleSidebar: () => void;
}

interface MiniQuote {
    price: number;
    change_percent: number;
}

const DEFAULT_WATCHLIST = ['NVDA', 'SPY', 'QQQ', 'AMD'];

export default function WatchlistSidebar({ onSelect, isOpen, toggleSidebar }: Props) {
    const [watchlist, setWatchlist] = useState<string[]>([]);
    const [quotes, setQuotes] = useState<Record<string, MiniQuote>>({});
    const [newTicker, setNewTicker] = useState('');
    const [isMounted, setIsMounted] = useState(false);

    // 1. Initialize List
    useEffect(() => {
        setIsMounted(true);
        const saved = localStorage.getItem('stock_watchlist');
        setWatchlist(saved ? JSON.parse(saved) : DEFAULT_WATCHLIST);
    }, []);

    // 2. Fetch Data Logic
    const fetchQuotes = async () => {
        if (watchlist.length === 0) return;
        try {
            const query = watchlist.join(',');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/quotes?symbols=${query}`);
            const data = await res.json();
            setQuotes(data);
        } catch (e) {
            console.error("Watchlist fetch error", e);
        }
    };

    // 3. Auto-Fetch on mount & changes
    useEffect(() => {
        if (!isMounted) return;
        localStorage.setItem('stock_watchlist', JSON.stringify(watchlist));
        fetchQuotes();
        const interval = setInterval(fetchQuotes, 30000); // Update every 30s
        return () => clearInterval(interval);
    }, [watchlist, isMounted]);

    const addTicker = (e: React.FormEvent) => {
        e.preventDefault();
        const symbol = newTicker.trim().toUpperCase();
        if (symbol && !watchlist.includes(symbol)) {
            setWatchlist([...watchlist, symbol]);
            setNewTicker('');
        }
    };

    const removeTicker = (symbol: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setWatchlist(watchlist.filter((t) => t !== symbol));
    };

    if (!isMounted) return null;

    return (
        <>
            {!isOpen && (
                <button onClick={toggleSidebar} className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md border md:hidden">
                    <Menu className="h-6 w-6 text-gray-700" />
                </button>
            )}

            <aside className={`fixed top-0 left-0 h-full bg-white border-r z-40 transition-transform duration-300 w-72 ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:relative flex flex-col`}>
                <div className="p-5 border-b flex items-center justify-between bg-gray-50">
                    <h2 className="font-bold text-gray-800 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-blue-600" /> Watchlist
                    </h2>
                    <button onClick={toggleSidebar} className="md:hidden"><X className="h-5 w-5" /></button>
                </div>

                <div className="p-4 flex-1 overflow-y-auto">
                    <form onSubmit={addTicker} className="mb-4 relative">
                        <input
                            type="text"
                            value={newTicker}
                            onChange={(e) => setNewTicker(e.target.value)}
                            placeholder="Add Symbol..."
                            className="w-full pl-3 pr-8 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none uppercase"
                        />
                        <button type="submit" className="absolute right-2 top-2 p-0.5 text-blue-600 hover:bg-blue-50 rounded"><Plus className="h-4 w-4" /></button>
                    </form>

                    <div className="space-y-1">
                        {watchlist.map((symbol) => {
                            const q = quotes[symbol];
                            const isUp = q?.change_percent >= 0;

                            return (
                                <div key={symbol} onClick={() => onSelect(symbol)} className="group flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors border border-transparent hover:border-gray-200">
                                    <div>
                                        <div className="font-bold text-gray-900">{symbol}</div>
                                        <div className="text-xs text-gray-500">US Equity</div>
                                    </div>
                                    <div className="text-right">
                                        {q ? (
                                            <>
                                                <div className="font-medium text-gray-900">${q.price.toFixed(2)}</div>
                                                <div className={`text-xs font-semibold ${isUp ? 'text-green-600' : 'text-red-600'}`}>
                                                    {isUp ? '+' : ''}{q.change_percent}%
                                                </div>
                                            </>
                                        ) : (
                                            <div className="h-4 w-12 bg-gray-200 rounded animate-pulse" />
                                        )}
                                    </div>
                                    <button onClick={(e) => removeTicker(symbol, e)} className="hidden group-hover:block absolute right-2 text-gray-400 hover:text-red-500"><X className="h-4 w-4" /></button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </aside>
        </>
    );
}