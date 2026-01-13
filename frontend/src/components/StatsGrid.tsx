import { PredictionResponse } from '@/lib/api';

const StatItem = ({ label, value }: { label: string; value: string }) => (
    <div className="flex justify-between py-3 border-b border-gray-800">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className="text-white font-medium">{value}</span>
    </div>
);

// Helper to format large numbers (e.g. 4.49T)
const formatCompact = (num?: number) => {
    if (!num) return '-';
    return Intl.NumberFormat('en-US', { notation: "compact", maximumFractionDigits: 2 }).format(num);
};

export default function StatsGrid({ data }: { data: PredictionResponse }) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-12 gap-y-2 mt-8 bg-[#1e1e1e] p-6 rounded-xl">
            <StatItem label="Open" value={data.open_price?.toFixed(2) || '-'} />
            <StatItem label="High" value={data.high_price?.toFixed(2) || '-'} />
            <StatItem label="Low" value={data.low_price?.toFixed(2) || '-'} />

            <StatItem label="Mkt cap" value={formatCompact(data.market_cap)} />
            <StatItem label="P/E ratio" value={data.pe_ratio?.toFixed(2) || '-'} />
            <StatItem label="Div yield" value={data.dividend_yield ? `${(data.dividend_yield * 100).toFixed(2)}%` : '-'} />

            <StatItem label="52-wk high" value={data.fifty_two_week_high?.toFixed(2) || '-'} />
            <StatItem label="52-wk low" value={data.fifty_two_week_low?.toFixed(2) || '-'} />
        </div>
    );
}