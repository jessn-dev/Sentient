'use client';

import { PredictionResponse } from '@/lib/api';
// import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function PredictionChart({ data }: { data: PredictionResponse }) {
    const chartData = [
        { name: 'Current', price: data.current_price },
        { name: '7-Day Forecast', price: data.predicted_price },
    ];

    const isBullish = data.price_movement === 'BULLISH';
    const color = isBullish ? '#22c55e' : '#ef4444'; // Green vs Red

    return (
        <div className="bg-[#1e1e1e] p-6 rounded-xl border border-gray-800 h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="name" stroke="#666" />
                    <YAxis domain={['auto', 'auto']} stroke="#666" />
                    <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} />
                    <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#22c55e"
                        fillOpacity={1}
                        fill="url(#colorPrice)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}