// src/components/MarketStatus.tsx
'use client';

import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

export default function MarketStatus() {
    const [status, setStatus] = useState({ isOpen: false, text: 'Loading...' });

    useEffect(() => {
        const updateStatus = () => {
            const now = new Date();
            // Force US Eastern Time
            const nyTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));

            const day = nyTime.getDay(); // 0=Sun, 6=Sat
            const hour = nyTime.getHours();
            const minute = nyTime.getMinutes();
            const totalMinutes = hour * 60 + minute;

            const MARKET_OPEN = 570;  // 9:30 AM
            const MARKET_CLOSE = 960; // 4:00 PM

            const isWeekday = day >= 1 && day <= 5;
            const isOpen = isWeekday && totalMinutes >= MARKET_OPEN && totalMinutes < MARKET_CLOSE;

            let text = '';

            if (isOpen) {
                // Calculate time to close
                const minsToClose = MARKET_CLOSE - totalMinutes;
                const h = Math.floor(minsToClose / 60);
                const m = minsToClose % 60;
                text = `U.S. Markets Open (Closes in ${h}h ${m}m)`;
            } else {
                // Calculate time to open
                let minsToOpen = 0;

                if (isWeekday && totalMinutes < MARKET_OPEN) {
                    // Same day pre-market
                    minsToOpen = MARKET_OPEN - totalMinutes;
                    const h = Math.floor(minsToOpen / 60);
                    const m = minsToOpen % 60;
                    text = `U.S. Markets Closed (Opens in ${h}h ${m}m)`;
                } else {
                    // After hours or weekend
                    text = 'U.S. Markets Closed';
                }
            }

            setStatus({ isOpen, text });
        };

        updateStatus();
        const timer = setInterval(updateStatus, 60000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className={`
      inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border shadow-sm
      ${status.isOpen
            ? 'bg-green-50 text-green-700 border-green-200'
            : 'bg-gray-50 text-gray-600 border-gray-200'}
    `}>
            <div className="relative flex h-2.5 w-2.5">
                {status.isOpen && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${status.isOpen ? 'bg-green-500' : 'bg-gray-400'}`}></span>
            </div>
            <Clock className="h-3.5 w-3.5" />
            <span>{status.text}</span>
        </div>
    );
}