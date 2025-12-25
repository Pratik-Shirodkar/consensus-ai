import CommitteeRoom from './CommitteeRoom'
import TradingChart from './TradingChart'
import StatusBar from './StatusBar'
import ControlPanel from './ControlPanel'
import './Dashboard.css'

function Dashboard({ isConnected, messages, status, onStart, onStop, onTrigger }) {
    const isRunning = status?.status === 'running'

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">
                        <span className="logo-icon">🧠</span>
                        Consensus AI
                    </h1>
                    <span className="tagline">Multi-Agent Investment Committee</span>
                </div>
                <div className="header-right">
                    <StatusIndicator connected={isConnected} running={isRunning} />
                    <span className="symbol-badge">BTC/USDT</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="dashboard-main">
                {/* Left Panel - Chart */}
                <section className="panel chart-panel glass">
                    <div className="panel-header">
                        <h2>📈 Market View</h2>
                        <div className="panel-badge">Live</div>
                    </div>
                    <TradingChart />
                </section>

                {/* Right Panel - Committee Room */}
                <section className="panel committee-panel glass">
                    <div className="panel-header">
                        <h2>🏛️ Committee Room</h2>
                        <div className="message-count">{messages.length} messages</div>
                    </div>
                    <CommitteeRoom messages={messages} />
                </section>
            </main>

            {/* Bottom Bar */}
            <footer className="dashboard-footer">
                <StatusBar status={status} />
                <ControlPanel
                    isRunning={isRunning}
                    onStart={onStart}
                    onStop={onStop}
                    onTrigger={onTrigger}
                />
            </footer>
        </div>
    )
}

function StatusIndicator({ connected, running }) {
    return (
        <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            <span className="status-text">
                {connected ? (running ? 'Trading' : 'Connected') : 'Disconnected'}
            </span>
        </div>
    )
}

export default Dashboard
