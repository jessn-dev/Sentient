"use client";

import { useEffect, useState } from "react";

export default function MarketStatus() {
    const [isOpen, setIsOpen] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [currentTime, setCurrentTime] = useState("");

    useEffect(() => {
        setMounted(true);
        const checkMarketStatus = () => {
            const now = new Date();
            setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' }));
            const day = now.getUTCDay();
            const hour = now.getUTCHours();
            const minute = now.getUTCMinutes();
            const timeInUTC = hour + minute / 60;
            // US Markets: Mon-Fri, 14:30 - 21:00 UTC
            setIsOpen(day >= 1 && day <= 5 && timeInUTC >= 14.5 && timeInUTC <= 21);
        };
        checkMarketStatus();
        const interval = setInterval(checkMarketStatus, 60000);
        return () => clearInterval(interval);
    }, []);

    if (!mounted) return <div className="h-[50px] w-full bg-slate-900 rounded-none border-b border-slate-800 animate-pulse" />;

    return (
        // FIX: Removed 'rounded-xl', 'mb-4', and added 'border-b' to make it look like a header
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
            <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${isOpen ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">
          US Market {isOpen ? 'Open' : 'Closed'}
        </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-gray-500">
        {currentTime}
      </span>
        </div>
    );
}