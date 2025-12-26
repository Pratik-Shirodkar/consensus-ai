import { useState, useEffect } from 'react'
import './TradeHistory.css'

function TradeHistory({ trades = [] }) {
    const [localTrades, setLocalTrades] = useState(trades)
    const [filter, setFilter] = useState('all') // all, wins, losses

    // Fetch trade history from API
    useEffect(() => {
        const fetchTrades = async () => {
            try {
                const res = await fetch('/api/trades?limit=50')
                const data = await res.json()
                if (data.trades) {
                    setLocalTrades(data.trades)
                }
            } catch (e) {
                console.error('Error fetching trades:', e)
            }
        }
        fetchTrades()
        const interval = setInterval(fetchTrades, 30000) // Refresh every 30s
        return () => clearInterval(interval)
    }, [])

    const filteredTrades = localTrades.filter(trade => {
        if (filter === 'wins') return trade.pnl && trade.pnl > 0
        if (filter === 'losses') return trade.pnl && trade.pnl < 0
        return true
    })

    const formatTime = (timestamp) => {
        const date = new Date(timestamp)
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    const formatDate = (timestamp) => {
        const date = new Date(timestamp)
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }

    return (
        <div className="trade-history">
            <div className="trade-filters">
                <button
                    className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                    onClick={() => setFilter('all')}
                >
                    All ({localTrades.length})
                </button>
                <button
                    className={`filter-btn wins ${filter === 'wins' ? 'active' : ''}`}
                    onClick={() => setFilter('wins')}
                >
                    Wins
                </button>
                <button
                    className={`filter-btn losses ${filter === 'losses' ? 'active' : ''}`}
                    onClick={() => setFilter('losses')}
                >
                    Losses
                </button>
            </div>

            <div className="trades-list">
                {filteredTrades.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">📊</span>
                        <p>No trades yet</p>
                        <span className="empty-hint">Trades will appear here when executed</span>
                    </div>
                ) : (
                    filteredTrades.slice().reverse().map((trade, idx) => (
                        <div key={trade.id || idx} className={`trade-item ${trade.pnl > 0 ? 'profit' : trade.pnl < 0 ? 'loss' : ''}`}>
                            <div className="trade-left">
                                <span className={`trade-side ${trade.side}`}>
                                    {trade.action === 'CLOSE' ? '📤' : trade.side === 'BUY' ? '📈' : '📉'}
                                </span>
                                <div className="trade-info">
                                    <span className="trade-symbol">{trade.symbol?.replace('cmt_', '').toUpperCase()}</span>
                                    <span className="trade-action">{trade.action || trade.side}</span>
                                </div>
                            </div>
                            <div className="trade-center">
                                <span className="trade-size">{trade.size?.toFixed(6)}</span>
                                <span className="trade-price">@ ${trade.price?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                            </div>
                            <div className="trade-right">
                                {trade.pnl !== undefined && trade.pnl !== null ? (
                                    <span className={`trade-pnl ${trade.pnl >= 0 ? 'positive' : 'negative'}`}>
                                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl_pct?.toFixed(2)}%
                                    </span>
                                ) : (
                                    <span className="trade-pnl pending">Open</span>
                                )}
                                <span className="trade-time">
                                    {formatDate(trade.executed_at)} {formatTime(trade.executed_at)}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default TradeHistory
