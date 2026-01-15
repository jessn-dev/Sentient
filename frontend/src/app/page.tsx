'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import TrendingCard from '@/components/TrendingCard';
import MarketStatus from '@/components/MarketStatus';
import { timeAgo } from '@/lib/utils';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';

interface NewsItem {
  title: string;
  publisher: string;
  link: string;
  published: number;
  thumbnail?: string;
  related_ticker: string;
  change_percent: number;
}

// Helper to fetch batch trending data
async function getBatchQuotes(symbols: string[]) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/quotes?symbols=${symbols.join(',')}`);
  return res.json();
}

export default function HomePage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [trendingData, setTrendingData] = useState<any>({});
  const router = useRouter();

  useEffect(() => {
    // 1. Fetch News
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/news/MARKET`)
        .then(res => res.json())
        .then(setNews)
        .catch(console.error);

    // 2. Fetch Trending Data
    const HOT_TICKERS = ['NVDA', 'TSLA', 'AAPL', 'AMD', 'MSFT', 'AMZN'];
    getBatchQuotes(HOT_TICKERS).then(setTrendingData).catch(console.error);
  }, []);

  const handleSearch = (symbol: string) => {
    router.push(`/stock/${symbol}`);
  };

  return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-12">

        {/* 1. HERO SECTION (Cleaned Up) */}
        <div className="text-center space-y-4 pt-4">
          <MarketStatus />
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-100 tracking-tight">
            Market<span className="text-blue-500">Mind</span> AI
          </h1>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            Stay ahead with AI-powered forecasts, real-time market data, and breaking news analysis.
          </p>
          {/* Search Bar Removed (Using Navbar) */}
        </div>

        {/* 2. TRENDING SECTION */}
        <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 delay-100 w-full">
          <div className="flex items-center justify-between mb-4 px-1">
            <h3 className="font-bold text-xl text-slate-200 flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              Trending Now
            </h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {['NVDA', 'TSLA', 'AAPL', 'AMD', 'MSFT', 'AMZN'].map((sym) => (
                <div key={sym} onClick={() => handleSearch(sym)} className="cursor-pointer">
                  <TrendingCard symbol={sym} data={trendingData[sym]} />
                </div>
            ))}
          </div>
        </div>

        {/* 3. NEWS SECTION */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-slate-200 border-l-4 border-blue-500 pl-3">
            Latest Market News
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {news.map((item, i) => (
                <a
                    key={i}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group block bg-[#1e293b] border border-slate-700 rounded-xl overflow-hidden hover:border-blue-500/50 transition-all duration-300 flex flex-col h-full hover:shadow-lg hover:shadow-blue-900/10"
                >
                  {/* Top Bar: Live Ticker Impact */}
                  <div className="px-5 py-3 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                   <span className="text-xs font-bold text-slate-300 bg-slate-700 px-2 py-0.5 rounded">
                     {item.related_ticker}
                   </span>
                      <span className={`text-xs font-mono font-medium ${item.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                     {item.change_percent > 0 ? '+' : ''}{item.change_percent}%
                   </span>
                    </div>
                    <span className="text-xs text-slate-500 font-medium">
                  {timeAgo(item.published)}
                </span>
                  </div>

                  <div className="p-5 flex flex-col flex-1">
                    <h3 className="font-bold text-slate-100 leading-snug mb-3 group-hover:text-blue-400 transition-colors line-clamp-3">
                      {item.title}
                    </h3>

                    <div className="mt-auto pt-2 flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                     {item.publisher}
                   </span>
                    </div>
                  </div>
                </a>
            ))}
          </div>
        </div>
      </div>
  );
}