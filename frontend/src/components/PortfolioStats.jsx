import { useState, useEffect } from 'react'
import './PortfolioStats.css'

function PortfolioStats() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await fetch('/api/status')
                const data = await res.json()
                if (data.trading) {
                    setStats(data.trading)
                }
                setLoading(false)
            } catch (e) {
                console.error('Error fetching stats:', e)
                setLoading(false)
            }
        }
        fetchStats()
        const interval = setInterval(fetchStats, 10000) // Refresh every 10s
        return () => clearInterval(interval)
    }, [])

    if (loading) {
        return <div className="portfolio-loading">Loading stats...</div>
    }

    if (!stats) {
        return <div className="portfolio-empty">No trading data available</div>
    }

    const winRate = stats.win_rate || 0
    const totalPnl = stats.total_pnl || 0
    const balance = stats.account_balance || 10000
    const pnlPct = ((balance - 10000) / 10000) * 100

    return (
        <div className="portfolio-stats">
            <div className="stat-row">
                <StatCard
                    icon="💰"
                    label="Account Balance"
                    value={`$${balance.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
                    trend={pnlPct >= 0 ? 'up' : 'down'}
                    trendValue={`${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`}
                />
                <StatCard
                    icon="📊"
                    label="Total Trades"
                    value={stats.total_trades || 0}
                />
                <StatCard
                    icon="🎯"
                    label="Win Rate"
                    value={`${winRate.toFixed(1)}%`}
                    trend={winRate >= 50 ? 'up' : winRate > 0 ? 'down' : null}
                />
                <StatCard
                    icon={totalPnl >= 0 ? "📈" : "📉"}
                    label="Total P&L"
                    value={`${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`}
                    trend={totalPnl >= 0 ? 'up' : 'down'}
                />
            </div>

            <div className="stat-row">
                <StatCard
                    icon="🎰"
                    label="Winning Trades"
                    value={stats.winning_trades || 0}
                    className="mini"
                />
                <StatCard
                    icon="📂"
                    label="Open Positions"
                    value={stats.open_positions || 0}
                    className="mini"
                />
                <StatCard
                    icon="⚡"
                    label="Exposure"
                    value={`${(stats.total_exposure_pct || 0).toFixed(1)}%`}
                    className="mini"
                    trend={(stats.total_exposure_pct || 0) > 80 ? 'down' : null}
                />
            </div>
        </div>
    )
}

function StatCard({ icon, label, value, trend, trendValue, className = '' }) {
    return (
        <div className={`stat-card ${className}`}>
            <div className="stat-header">
                <span className="stat-icon">{icon}</span>
                <span className="stat-label">{label}</span>
            </div>
            <div className="stat-content">
                <span className="stat-value">{value}</span>
                {trend && (
                    <span className={`stat-trend ${trend}`}>
                        {trendValue || (trend === 'up' ? '↑' : '↓')}
                    </span>
                )}
            </div>
        </div>
    )
}

export default PortfolioStats
