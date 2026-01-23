"use client";
import { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/solid";

// Top 30 Weights (Always Visible)
const TOP_30 = [
    { symbol: "AAPL", name: "Apple Inc." }, { symbol: "MSFT", name: "Microsoft Corp." },
    { symbol: "NVDA", name: "NVIDIA Corp." }, { symbol: "AMZN", name: "Amazon.com" },
    { symbol: "META", name: "Meta Platforms" }, { symbol: "GOOGL", name: "Alphabet Inc." },
    { symbol: "TSLA", name: "Tesla Inc." }, { symbol: "BRK.B", name: "Berkshire Hathaway" },
    { symbol: "LLY", name: "Eli Lilly" }, { symbol: "AVGO", name: "Broadcom" },
    { symbol: "JPM", name: "JPMorgan Chase" }, { symbol: "V", name: "Visa Inc." },
    { symbol: "XOM", name: "Exxon Mobil" }, { symbol: "UNH", name: "UnitedHealth" },
    { symbol: "MA", name: "Mastercard" }, { symbol: "PG", name: "Procter & Gamble" },
    { symbol: "JNJ", name: "Johnson & Johnson" }, { symbol: "HD", name: "Home Depot" },
    { symbol: "COST", name: "Costco" }, { symbol: "ABBV", name: "AbbVie" },
    { symbol: "AMD", name: "Adv. Micro Devices" }, { symbol: "NFLX", name: "Netflix" },
    { symbol: "KO", name: "Coca-Cola" }, { symbol: "PEP", name: "PepsiCo" },
    { symbol: "DIS", name: "Walt Disney" }, { symbol: "CSCO", name: "Cisco Systems" },
    { symbol: "INTC", name: "Intel Corp." }, { symbol: "VZ", name: "Verizon" },
    { symbol: "PFE", name: "Pfizer" }, { symbol: "WMT", name: "Walmart" },
];

// Expanded List (Simulated for Demo - In prod this could be fetched)
const FULL_LIST = [
    ...TOP_30,
    { symbol: "T", name: "AT&T Inc." }, { symbol: "BA", name: "Boeing Co." },
    { symbol: "IBM", name: "IBM" }, { symbol: "GE", name: "General Electric" },
    { symbol: "F", name: "Ford Motor" }, { symbol: "GM", name: "General Motors" },
    { symbol: "CAT", name: "Caterpillar" }, { symbol: "MMM", name: "3M Company" },
    { symbol: "CVX", name: "Chevron" }, { symbol: "GS", name: "Goldman Sachs" },
    { symbol: "MS", name: "Morgan Stanley" }, { symbol: "C", name: "Citigroup" },
    { symbol: "WFC", name: "Wells Fargo" }, { symbol: "BAC", name: "Bank of America" },
    { symbol: "USB", name: "US Bancorp" }, { symbol: "AXP", name: "American Express" },
    { symbol: "BLK", name: "BlackRock" }, { symbol: "SPGI", name: "S&P Global" },
    { symbol: "MCD", name: "McDonald's" }, { symbol: "SBUX", name: "Starbucks" },
    { symbol: "NKE", name: "Nike" }, { symbol: "LULU", name: "Lululemon" },
    { symbol: "TGT", name: "Target" }, { symbol: "LOW", name: "Lowe's" },
    { symbol: "TJX", name: "TJX Companies" }, { symbol: "BKNG", name: "Booking Holdings" },
    { symbol: "UBER", name: "Uber Tech" }, { symbol: "ABNB", name: "Airbnb" },
    { symbol: "MAR", name: "Marriott" }, { symbol: "HLT", name: "Hilton" },
    // ... (This list would normally fetch from your API)
];

interface Props {
  onSelect: (symbol: string) => void;
}

export default function SP500Reference({ onSelect }: Props) {
    const [expanded, setExpanded] = useState(false);
    const visibleList = expanded ? FULL_LIST : TOP_30;

    return (
        <div className="flex flex-col bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden h-full max-h-[800px]">
            <div className="p-4 border-b border-slate-800 bg-slate-950">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">
                    S&P 500 Reference
                </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                {visibleList.map((stock) => (
                    <button
                        key={stock.symbol}
                        onClick={() => onSelect(stock.symbol)}
                        className="w-full flex items-center justify-between p-2 hover:bg-slate-800 rounded-lg group transition-colors text-left"
                    >
                        <span className="font-bold text-sm text-blue-400 group-hover:text-blue-300">
                          {stock.symbol}
                        </span>
                        <span className="text-xs text-slate-500 font-medium truncate max-w-[120px] text-right group-hover:text-slate-400">
                          {stock.name}
                        </span>
                    </button>
                ))}
            </div>

            {/* EXPAND BUTTON (Now Functional) */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="p-3 border-t border-slate-800 bg-slate-950 hover:bg-slate-900 transition-colors text-[10px] font-bold uppercase text-slate-400 flex items-center justify-center gap-2"
            >
                {expanded ? (
                    <>Show Less <ChevronUpIcon className="h-3 w-3"/></>
                ) : (
                    <>+ Load All Constituents <ChevronDownIcon className="h-3 w-3"/></>
                )}
            </button>
        </div>
    );
}