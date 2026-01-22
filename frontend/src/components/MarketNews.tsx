"use client";

import { useEffect, useState } from "react";
import { NewspaperIcon } from "@heroicons/react/24/outline";

export default function MarketNews() {
    const [news, setNews] = useState([]);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        async function fetchNews() {
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                const res = await fetch(`${API_URL}/news/MARKET`);
                if (res.ok) {
                    const data = await res.json();
                    setNews(data.slice(0, 5));
                }
            } catch (e) {
                console.error("News Fetch Failed", e);
            }
        }
        fetchNews();
    }, []);

    // Hydration Shield: Show a loading state instead of null to prevent layout shift
    if (!mounted) {
        return <div className="mt-12 w-full max-w-4xl animate-pulse bg-gray-100 dark:bg-gray-800 h-64 rounded-xl" />;
    }

    if (news.length === 0) return null;

    return (
        <div className="mt-12 w-full max-w-4xl">
            <h3 className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-400 mb-6">
                <NewspaperIcon className="h-5 w-5" />
                Market Intelligence Feed
            </h3>
            <div className="space-y-4">
                {news.map((item: any, i: number) => (
                    <a
                        key={i}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-blue-500 transition-all shadow-sm"
                    >
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-[10px] font-bold text-blue-500 uppercase">{item.source}</span>
                            <span className="text-[10px] text-gray-400">Latest</span>
                        </div>
                        <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 leading-tight">
                            {item.headline}
                        </h4>
                    </a>
                ))}
            </div>
        </div>
    );
}