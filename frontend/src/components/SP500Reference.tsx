"use client";
import { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon, ChartBarIcon } from "@heroicons/react/24/solid";

const SP500_SYMBOLS = [
  "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK.B", "LLY", "AVGO",
  "JPM", "XOM", "UNH", "V", "PG", "MA", "COST", "JNJ", "HD", "MRK",
  "ABBV", "CVX", "BAC", "AMD", "PEP", "KO", "NFLX", "WMT", "ADBE", "CRM",
  "TMO", "MCD", "CSCO", "ACN", "LIN", "ABT", "DHR", "ORCL", "DIS", "CAT",
  "INTC", "VZ", "CMCSA", "INTU", "QCOM", "IBM", "AMGN", "PFE", "TXN", "NOW"
];

export default function SP500Reference({ onSelect }: { onSelect: (sym: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  // Show only top 10 if not expanded
  const displayed = expanded ? SP500_SYMBOLS : SP500_SYMBOLS.slice(0, 10);

  return (
    <div className="bg-[#151921] rounded-xl overflow-hidden">
      <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
           <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
           S&P 500 Quick List
        </h3>
        <span className="text-[10px] bg-white/5 px-2 py-0.5 rounded text-slate-500 font-mono">
            {expanded ? "ALL" : "TOP 10"}
        </span>
      </div>

      <div className="max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        <div className="grid grid-cols-1 divide-y divide-white/5">
          {displayed.map((sym, i) => (
            <button
              key={sym}
              onClick={() => onSelect(sym)}
              className="group flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-600 w-4">{i + 1}</span>
                <span className="text-sm font-bold text-slate-300 group-hover:text-white transition-colors">{sym}</span>
              </div>
              <ChartBarIcon className="h-4 w-4 text-slate-600 group-hover:text-indigo-400 transition-colors opacity-0 group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </div>

      {/* FOOTER BUTTON */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full py-3 flex items-center justify-center gap-2 text-xs font-bold text-slate-400 hover:text-white hover:bg-white/5 transition-colors border-t border-white/5 uppercase tracking-wider"
      >
        {expanded ? (
            <>Show Less <ChevronUpIcon className="h-3 w-3" /></>
        ) : (
            <>View All {SP500_SYMBOLS.length} <ChevronDownIcon className="h-3 w-3" /></>
        )}
      </button>
    </div>
  );
}