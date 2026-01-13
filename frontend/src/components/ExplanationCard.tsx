import { Bot } from 'lucide-react';

export default function ExplanationCard({ text }: { text: string }) {
    return (
        <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-6 mt-6 flex gap-4">
            <div className="shrink-0">
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Bot className="h-5 w-5 text-blue-600" />
                </div>
            </div>
            <div>
                <h4 className="text-sm font-semibold text-blue-900 mb-1">AI Market Analysis</h4>
                <p className="text-blue-800 leading-relaxed text-sm">
                    {text}
                </p>
            </div>
        </div>
    );
}