import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import './TradingChart.css'

function TradingChart({ symbol = 'cmt_btcusdt' }) {
    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)
    const candleSeriesRef = useRef(null)
    const volumeSeriesRef = useRef(null)
    const [lastPrice, setLastPrice] = useState(null)
    const [priceChange, setPriceChange] = useState(null)

    // Fetch candle data from API
    const fetchCandles = async () => {
        try {
            const res = await fetch(`/api/candles?symbol=${symbol}`)
            const data = await res.json()

            if (data.candles && data.candles.length > 0 && candleSeriesRef.current) {
                candleSeriesRef.current.setData(data.candles)

                // Update volume
                if (volumeSeriesRef.current) {
                    const volumeData = data.candles.map(c => ({
                        time: c.time,
                        value: c.volume || Math.random() * 1000 + 500,
                        color: c.close >= c.open ? 'rgba(0, 212, 170, 0.3)' : 'rgba(255, 107, 107, 0.3)',
                    }))
                    volumeSeriesRef.current.setData(volumeData)
                }

                // Update price display
                if (data.ticker) {
                    setLastPrice(data.ticker.last_price)
                    setPriceChange(data.ticker.change_pct_24h)
                }
            }
        } catch (e) {
            console.error('Error fetching candles:', e)
        }
    }

    useEffect(() => {
        if (!chartContainerRef.current) return

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#a0a0b0',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            crosshair: {
                mode: 1,
                vertLine: {
                    color: 'rgba(124, 58, 237, 0.5)',
                    labelBackgroundColor: '#7c3aed',
                },
                horzLine: {
                    color: 'rgba(124, 58, 237, 0.5)',
                    labelBackgroundColor: '#7c3aed',
                },
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
        })

        // Add candlestick series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#00d4aa',
            downColor: '#ff6b6b',
            borderUpColor: '#00d4aa',
            borderDownColor: '#ff6b6b',
            wickUpColor: '#00d4aa',
            wickDownColor: '#ff6b6b',
        })
        candleSeriesRef.current = candleSeries

        // Add volume series
        const volumeSeries = chart.addHistogramSeries({
            color: '#7c3aed',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        })
        volumeSeriesRef.current = volumeSeries

        // Fit content
        chart.timeScale().fitContent()

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                })
            }
        }

        window.addEventListener('resize', handleResize)
        handleResize()

        chartRef.current = chart

        // Fetch initial data
        fetchCandles()

        // Set up periodic refresh every 10 seconds
        const refreshInterval = setInterval(fetchCandles, 10000)

        return () => {
            clearInterval(refreshInterval)
            window.removeEventListener('resize', handleResize)
            chart.remove()
        }
    }, [symbol]) // Re-run when symbol changes

    return (
        <div className="trading-chart-container">
            {lastPrice && (
                <div className="price-display">
                    <span className="current-price">${lastPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    {priceChange !== null && (
                        <span className={`price-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
                            {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                        </span>
                    )}
                </div>
            )}
            <div className="trading-chart" ref={chartContainerRef} />
        </div>
    )
}

export default TradingChart
