'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react'; // <--- FIX: Import from 'react'
import { Search, TrendingUp } from 'lucide-react';

export default function Navbar() {
    const [query, setQuery] = useState('');
    const router = useRouter();

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/stock/${query.toUpperCase()}`);
            setQuery('');
        }
    };

    return (
        <nav className="sticky top-0 z-50 w-full bg-[#0f172a]/80 backdrop-blur-md border-b border-slate-800 shadow-lg">
            <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">

                {/* Logo */}
                <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                    <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30">
                        <TrendingUp className="h-6 w-6 text-blue-400" />
                    </div>
                    <span className="text-xl font-bold text-slate-100 hidden md:block tracking-tight">
            Market<span className="text-blue-400">Mind</span>
          </span>
                </Link>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="flex-1 max-w-md relative">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
                        <input
                            type="text"
                            placeholder="Search ticker (e.g. NVDA)..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5
                bg-slate-800/50
                border border-slate-700
                text-slate-100 placeholder-slate-500
                rounded-full
                focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50
                transition-all duration-300
                shadow-inner"
                        />
                    </div>
                </form>

                {/* User Icon */}
                <div className="w-9 h-9 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-xs font-bold text-blue-400 shadow-sm">
                    U
                </div>
            </div>
        </nav>
    );
}