"use client";
import { useEffect, useRef, memo } from "react";

interface TradingViewWidgetProps {
    type: "symbol-overview" | "timeline" | "ticker-tape" | "hotlists";
    theme?: "light" | "dark";
    symbol?: string;
}

function TradingViewWidget({ type, theme = "dark", symbol = "NASDAQ:AAPL" }: TradingViewWidgetProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) return;
        containerRef.current.innerHTML = "";
        const script = document.createElement("script");
        script.type = "text/javascript";
        script.async = true;

        // Smart Resolution: If no exchange provided, guess based on length
        let resolved = symbol;
        if (!symbol.includes(":")) {
            resolved = symbol.length <= 3 ? `NYSE:${symbol}` : `NASDAQ:${symbol}`;
        }

        let config: any = {
            colorTheme: theme, dateRange: "12M", locale: "en", width: "100%", height: "100%",
            isTransparent: true, autosize: true
        };

        if (type === "symbol-overview") {
            script.src = "https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js";
            config = { ...config, symbols: [[resolved, resolved + "|1D"]], chartType: "area", showVolume: true };
        } else if (type === "ticker-tape") {
            script.src = "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js";
            config = { ...config, displayMode: "adaptive", symbols: [{ proName: "NASDAQ:AAPL", title: "Apple" }, { proName: "NASDAQ:NVDA", title: "NVIDIA" }, { proName: "NASDAQ:MSFT", title: "Microsoft" }] };
        } else if (type === "timeline") {
            script.src = "https://s3.tradingview.com/external-embedding/embed-widget-timeline.js";
            config = { ...config, feedMode: "market", market: "stock" };
        }

        script.innerHTML = JSON.stringify(config);
        containerRef.current.appendChild(script);
    }, [type, theme, symbol]);

    return <div className="tradingview-widget-container w-full h-full" ref={containerRef}><div className="tradingview-widget-container__widget w-full h-full"></div></div>;
}
export default memo(TradingViewWidget);