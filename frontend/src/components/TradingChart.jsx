import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import './TradingChart.css'

function TradingChart() {
    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)

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

        // Generate sample data (in real app, fetch from WEEX)
        const now = Math.floor(Date.now() / 1000)
        const data = generateSampleData(now)
        candleSeries.setData(data)

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

        const volumeData = data.map(d => ({
            time: d.time,
            value: Math.random() * 1000 + 500,
            color: d.close >= d.open ? 'rgba(0, 212, 170, 0.3)' : 'rgba(255, 107, 107, 0.3)',
        }))
        volumeSeries.setData(volumeData)

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

        return () => {
            window.removeEventListener('resize', handleResize)
            chart.remove()
        }
    }, [])

    return (
        <div className="trading-chart" ref={chartContainerRef} />
    )
}

// Generate sample candlestick data
function generateSampleData(endTime) {
    const data = []
    let basePrice = 42000 + Math.random() * 1000
    const interval = 300 // 5 minutes

    for (let i = 100; i >= 0; i--) {
        const time = endTime - i * interval
        const volatility = 0.002

        const open = basePrice
        const change = (Math.random() - 0.48) * volatility * basePrice
        const high = open + Math.abs(change) + Math.random() * 50
        const low = open - Math.abs(change) - Math.random() * 50
        const close = open + change

        data.push({
            time,
            open,
            high: Math.max(open, close, high),
            low: Math.min(open, close, low),
            close,
        })

        basePrice = close
    }

    return data
}

export default TradingChart
