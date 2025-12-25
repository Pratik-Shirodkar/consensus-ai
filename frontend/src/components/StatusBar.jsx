import './StatusBar.css'

function StatusBar({ status }) {
    if (!status) {
        return (
            <div className="status-bar">
                <span className="status-loading">Loading...</span>
            </div>
        )
    }

    const { trading, debate } = status

    return (
        <div className="status-bar">
            <div className="status-group">
                <div className="stat">
                    <span className="stat-label">Account</span>
                    <span className="stat-value">${trading?.account_balance?.toLocaleString() || '10,000'}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Total P&L</span>
                    <span className={`stat-value ${trading?.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                        {trading?.total_pnl >= 0 ? '+' : ''}${trading?.total_pnl?.toFixed(2) || '0.00'}
                    </span>
                </div>
                <div className="stat">
                    <span className="stat-label">Win Rate</span>
                    <span className="stat-value">{trading?.win_rate?.toFixed(1) || '0.0'}%</span>
                </div>
            </div>

            <div className="status-divider"></div>

            <div className="status-group">
                <div className="stat">
                    <span className="stat-label">Debates</span>
                    <span className="stat-value">{debate?.total_debates || 0}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Trades</span>
                    <span className="stat-value">{trading?.total_trades || 0}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Exposure</span>
                    <span className={`stat-value ${trading?.total_exposure_pct > 50 ? 'warning' : ''}`}>
                        {trading?.total_exposure_pct?.toFixed(1) || '0.0'}%
                    </span>
                </div>
            </div>
        </div>
    )
}

export default StatusBar
