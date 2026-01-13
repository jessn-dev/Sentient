'use client';

import { useState } from 'react';
import { fetchPrediction, PredictionResponse } from '@/lib/api';
import StockForm from '@/components/StockForm';
import PredictionChart from '@/components/PredictionChart';
import ExplanationCard from '@/components/ExplanationCard';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (symbol: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchPrediction(symbol);
      setData(result);
    } catch (err: any) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
      <main className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-5xl mx-auto space-y-8">

          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Market<span className="text-blue-600">Mind</span> AI</h1>
            <p className="text-gray-500">Prophet 1.2 Powered Stock Forecasting</p>
          </div>

          {/* Input Section */}
          <div className="flex justify-center">
            <StockForm onSearch={handleSearch} isLoading={loading} />
          </div>

          {/* Error State */}
          {error && (
              <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-200 text-center">
                {error}
              </div>
          )}

          {/* Results Section */}
          {data && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                {/* Stats Card */}
                <div className="md:col-span-1 space-y-4">
                  <div className="bg-white p-6 rounded-xl shadow-sm border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-500">Forecast (7d)</span>
                      {data.price_movement === 'BULLISH' ?
                          <TrendingUp className="text-green-500 h-5 w-5" /> :
                          <TrendingDown className="text-red-500 h-5 w-5" />
                      }
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                      {data.price_movement}
                    </div>
                    <div className={`text-sm font-medium ${data.price_movement === 'BULLISH' ? 'text-green-600' : 'text-red-600'}`}>
                      {data.growth_percentage}% Expected Growth
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-xl shadow-sm border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-500">Confidence</span>
                      <Activity className="text-blue-500 h-5 w-5" />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {(data.confidence_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-sm text-gray-400">Model Certainty</div>
                  </div>
                </div>

                {/* Chart Card */}
                <div className="md:col-span-2">
                  <PredictionChart data={data} />
                </div>
                {/* Explanation here */}
                <ExplanationCard text={data.explanation} />

              </div>
          )}
        </div>
      </main>
  );
}