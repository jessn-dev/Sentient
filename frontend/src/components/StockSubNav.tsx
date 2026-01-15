'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
    { name: 'Overview', path: '' },      // Root: Company Info & Live Stats
    { name: 'Forecast', path: 'forecast' }, // NEW: The AI Prediction & Chart
    { name: 'News', path: 'news' },
    { name: 'Financials', path: 'financials' },
];

export default function StockSubNav({ symbol }: { symbol: string }) {
    const pathname = usePathname();
    const baseUrl = `/stock/${symbol}`;

    return (
        <div className="border-b border-slate-700 bg-[#0f172a] mb-6 overflow-x-auto">
            <div className="flex space-x-8 px-4 max-w-7xl mx-auto">
                {TABS.map((tab) => {
                    const href = tab.path ? `${baseUrl}/${tab.path}` : baseUrl;
                    // Logic: "Overview" is active only on exact match
                    const isActive = tab.path
                        ? pathname.includes(tab.path)
                        : pathname === baseUrl;

                    return (
                        <Link
                            key={tab.name}
                            href={href}
                            className={`
                whitespace-nowrap py-4 px-1 border-b-2 text-sm font-medium transition-colors
                ${isActive
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'}
              `}
                        >
                            {tab.name}
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}