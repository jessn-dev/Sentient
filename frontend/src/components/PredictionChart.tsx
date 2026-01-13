'use client';

import { PredictionResponse } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function PredictionChart({ data }: { data: PredictionResponse }) {
    const chartData = [
        { name: 'Current', price: data.current_price },
        { name: '7-Day Forecast', price: data.predicted_price_7d },
    ];

    const isBullish = data.price_movement === 'BULLISH';
    const color = isBullish ? '#22c55e' : '#ef4444'; // Green vs Red

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border h-[400px] w-full">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Price Forecast</h3>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                    <XAxis dataKey="name" />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip
                        // FIX: Changed 'value: number' to 'value: any' to handle Recharts types
                        formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Price']}
                        contentStyle={{ backgroundColor: '#fff', borderRadius: '8px' }}
                    />
                    <Bar dataKey="price" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={index === 1 ? color : '#3b82f6'} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}