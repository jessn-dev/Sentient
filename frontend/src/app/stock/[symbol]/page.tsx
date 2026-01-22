"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import PredictionResult from "@/components/PredictionResult";
import TradingViewWidget from "@/components/TradingViewWidget";
import { ArrowLeftIcon } from "@heroicons/react/24/solid";

export default function StockDetailsPage() {
    const params = useParams(); const router = useRouter();
    const symbol = (params.symbol as string).toUpperCase();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol, days: 7 })
        }).then(r => r.json()).then(d => { setData(d); setLoading(false); });
    }, [symbol]);

    return (
        <main className="fixed inset-0 z-[100] bg-[#020617] text-white flex overflow-hidden">
            <button onClick={() => router.push('/')} className="absolute top-4 left-4 z-50 p-2 bg-slate-800/80 hover:bg-blue-600 rounded-full border border-slate-700 backdrop-blur"><ArrowLeftIcon className="h-5 w-5 text-white" /></button>

            <div className="w-full lg:w-[600px] bg-[#020617] border-r border-slate-800 overflow-y-auto p-8 pt-20 custom-scrollbar shrink-0">
                <h1 className="text-6xl font-black mb-2">{symbol}</h1>
                <div className="mb-8 flex gap-2"><span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 text-[10px] font-bold uppercase border border-blue-900">SentientAI Analysis</span></div>
                {loading ? <div className="h-[400px] bg-slate-900/20 animate-pulse rounded-2xl border border-slate-800"/> : data && <PredictionResult data={data} detailed={true} />}
            </div>

            <div className="hidden lg:block flex-1 bg-slate-900 relative border-l border-slate-800">
                <TradingViewWidget type="symbol-overview" symbol={data?.tv_symbol || symbol} theme="dark" />
            </div>
        </main>
    );
}