'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';

interface Props {
    onSearch: (symbol: string) => void;
    isLoading: boolean;
}

export default function StockForm({ onSearch, isLoading }: Props) {
    const [symbol, setSymbol] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (symbol.trim()) onSearch(symbol);
    };

    return (
        <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-md">
            <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="Enter Ticker (e.g. AAPL, TSLA)"
                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black"
                    disabled={isLoading}
                />
            </div>
            <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
                {isLoading ? 'Analyzing...' : 'Predict'}
            </button>
        </form>
    );
}