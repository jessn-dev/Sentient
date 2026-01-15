export default function StatsGrid({ data }: { data: any }) {
    const stats = [
        { label: 'Market Cap', value: data.market_cap ? `$${(data.market_cap / 1e9).toFixed(2)}B` : 'N/A' },
        { label: 'P/E Ratio', value: data.pe_ratio?.toFixed(2) || 'N/A' },
        { label: 'Volume', value: data.volume?.toLocaleString() || 'N/A' },
        { label: '52W High', value: data.fifty_two_week_high ? `$${data.fifty_two_week_high}` : 'N/A' },
        { label: '52W Low', value: data.fifty_two_week_low ? `$${data.fifty_two_week_low}` : 'N/A' },
        { label: 'Open', value: `$${data.open_price}` },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {stats.map((stat) => (
                // CHANGED: bg-white -> bg-[#1e293b], border-gray-100 -> border-slate-700
                <div key={stat.label} className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 shadow-sm">
                    <div className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">
                        {stat.label}
                    </div>
                    <div className="text-slate-100 text-lg font-semibold">
                        {stat.value}
                    </div>
                </div>
            ))}
        </div>
    );
}