'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface QuoteData {
    symbol: string;
    price: number;
    change_percent: number;
    is_market_open: boolean;
}

interface Props {
    symbol: string;
    data?: QuoteData; // Data might be undefined while loading
}

export default function TrendingCard({ symbol, data }: Props) {
    // 1. Loading State (If data hasn't arrived from Home Page yet)
    if (!data) {
        return (
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm animate-pulse">
                <div className="flex justify-between items-start mb-2">
                    <div className="h-5 w-16 bg-gray-200 rounded"></div>
                    <div className="h-4 w-4 bg-gray-200 rounded-full"></div>
                </div>
                <div className="h-8 w-24 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 w-12 bg-gray-200 rounded"></div>
            </div>
        );
    }

    const isUp = data.change_percent >= 0;

    return (
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all cursor-pointer hover:-translate-y-1 h-full">
            <div className="flex justify-between items-start mb-2">
                <div className="font-bold text-gray-900 text-lg">{symbol}</div>
                {isUp ? (
                    <TrendingUp className="h-5 w-5 text-green-500" />
                ) : (
                    <TrendingDown className="h-5 w-5 text-red-500" />
                )}
            </div>

            {/* 2. Display Price (Safe Check) */}
            <div className="text-2xl font-bold text-gray-900">
                ${data.price?.toFixed(2) || '0.00'}
            </div>

            <div className={`text-sm font-medium ${isUp ? 'text-green-600' : 'text-red-600'}`}>
                {isUp ? '+' : ''}{data.change_percent?.toFixed(2)}%
            </div>
        </div>
    );
}