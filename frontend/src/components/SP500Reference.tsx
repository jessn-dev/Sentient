"use client";

const SP500_SAMPLE = [
    { symbol: "AAPL", name: "Apple Inc." },
    { symbol: "MSFT", name: "Microsoft Corp." },
    { symbol: "NVDA", name: "NVIDIA Corp." },
    { symbol: "AMZN", name: "Amazon.com" },
    { symbol: "META", name: "Meta Platforms" },
    { symbol: "GOOGL", name: "Alphabet Inc." },
    { symbol: "TSLA", name: "Tesla Inc." },
    { symbol: "BRK.B", name: "Berkshire Hathaway" },
    { symbol: "LLY", name: "Eli Lilly" },
    { symbol: "AVGO", name: "Broadcom" },
    { symbol: "JPM", name: "JPMorgan Chase" },
    { symbol: "V", name: "Visa Inc." },
    { symbol: "XOM", name: "Exxon Mobil" },
    { symbol: "UNH", name: "UnitedHealth" },
    { symbol: "MA", name: "Mastercard" },
    { symbol: "PG", name: "Procter & Gamble" },
    { symbol: "JNJ", name: "Johnson & Johnson" },
    { symbol: "HD", name: "Home Depot" },
    { symbol: "COST", name: "Costco" },
    { symbol: "ABBV", name: "AbbVie" },
    { symbol: "AMD", name: "Adv. Micro Devices" },
    { symbol: "NFLX", name: "Netflix" },
    { symbol: "KO", name: "Coca-Cola" },
    { symbol: "PEP", name: "PepsiCo" },
    { symbol: "DIS", name: "Walt Disney" },
    { symbol: "CSCO", name: "Cisco Systems" },
    { symbol: "INTC", name: "Intel Corp." },
    { symbol: "VZ", name: "Verizon" },
    { symbol: "PFE", name: "Pfizer" },
    { symbol: "WMT", name: "Walmart" },
];

export default function SP500Reference() {
    return (
        <div className="flex flex-col h-full bg-slate-900 border-t border-slate-800">
            <div className="p-4 border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-10">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">
                    S&P 500 Reference
                </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                {SP500_SAMPLE.map((stock) => (
                    <div
                        key={stock.symbol}
                        className="flex items-center justify-between p-2 hover:bg-slate-800 rounded-lg group cursor-default transition-colors"
                    >
            <span className="font-bold text-sm text-blue-400 group-hover:text-blue-300">
              {stock.symbol}
            </span>
                        <span className="text-xs text-slate-500 font-medium truncate max-w-[120px] text-right">
              {stock.name}
            </span>
                    </div>
                ))}
                <div className="text-center py-4 text-[10px] text-slate-600 uppercase font-bold">
                    + 470 More
                </div>
            </div>
        </div>
    );
}