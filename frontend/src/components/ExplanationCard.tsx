import { Bot } from 'lucide-react';

export default function ExplanationCard({ text }: { text: string }) {
    return (
        // CHANGED: Blue-50 -> Slate-800/50, Text-Blue-900 -> Text-Slate-200
        <div className="bg-slate-800/50 border border-blue-500/20 rounded-xl p-6 mt-6 flex gap-4">
            <div className="shrink-0">
                <div className="h-10 w-10 bg-blue-900/30 rounded-full flex items-center justify-center border border-blue-500/30">
                    <Bot className="h-5 w-5 text-blue-400" />
                </div>
            </div>
            <div>
                <h4 className="text-sm font-semibold text-blue-400 mb-1">AI Market Analysis</h4>
                <p className="text-slate-300 leading-relaxed text-sm">
                    {text}
                </p>
            </div>
        </div>
    );
}