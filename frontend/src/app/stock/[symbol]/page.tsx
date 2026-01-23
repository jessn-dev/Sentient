"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import PredictionResult from "@/components/PredictionResult"; // Reusing the component
import { AdvancedRealTimeChart } from "react-ts-tradingview-widgets";
import { ArrowLeftIcon } from "@heroicons/react/24/solid";

export default function StockDetailsPage() {
  const { symbol } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!symbol) return;

    // Fetch fresh prediction data
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: symbol, days: 7 })
    })
    .then(res => res.json())
    .then(data => {
        if (data.detail) throw new Error(data.detail);
        setData(data);
        setLoading(false);
    })
    .catch(err => {
        setError("Failed to load stock data.");
        setLoading(false);
    });
  }, [symbol]);

  if (loading) return <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">Loading Analysis...</div>;
  if (error) return <div className="min-h-screen bg-[#020617] text-red-400 flex items-center justify-center font-bold">{error}</div>;

  return (
    <main className="min-h-screen bg-[#020617] text-white p-6 pb-24">
       <div className="max-w-7xl mx-auto">
          {/* NAV */}
          <Link href="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-8 font-bold text-sm uppercase transition-colors">
             <ArrowLeftIcon className="h-4 w-4"/> Back to Dashboard
          </Link>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

             {/* LEFT: PREDICTION CARD (Detailed) */}
             <div className="lg:col-span-1">
                <div className="sticky top-6">
                   <h1 className="text-4xl font-black mb-1">{data.symbol}</h1>
                   <h2 className="text-xl text-slate-500 font-bold mb-6">{data.company_name}</h2>

                   <PredictionResult
                      data={data}
                      detailed={true} // <--- Enables Technicals/Sentiment/Liquidity
                      onSaveSuccess={() => {}}
                   />
                </div>
             </div>

             {/* RIGHT: CHART */}
             <div className="lg:col-span-2 min-h-[600px] bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                <AdvancedRealTimeChart
                   theme="dark"
                   symbol={data.tv_symbol || `NASDAQ:${data.symbol}`}
                   autosize
                   hide_side_toolbar={false}
                />
             </div>
          </div>
       </div>
    </main>
  );
}