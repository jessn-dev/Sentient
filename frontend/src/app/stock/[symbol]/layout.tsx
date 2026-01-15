import StockSubNav from '@/components/StockSubNav';
import { ReactNode } from 'react';

// Layouts are Server Components by default, so we can use async/await
export default async function StockLayout({
                                              children,
                                              params,
                                          }: {
    children: ReactNode;
    params: Promise<{ symbol: string }>; // Type is a Promise now
}) {
    // 1. Await the params
    const { symbol } = await params;

    return (
        <div className="min-h-screen bg-[#0f172a]">
            <div className="bg-[#0f172a] border-b border-slate-800 py-6 px-4">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-3xl font-bold text-slate-100">{symbol}</h1>
                </div>
            </div>

            {/* Pass the unwrapped symbol to the client component */}
            <StockSubNav symbol={symbol} />

            <div className="max-w-7xl mx-auto px-4 pb-12">
                {children}
            </div>
        </div>
    );
}