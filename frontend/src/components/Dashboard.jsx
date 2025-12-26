import { useState } from 'react'
import CommitteeRoom from './CommitteeRoom'
import TradingChart from './TradingChart'
import StatusBar from './StatusBar'
import ControlPanel from './ControlPanel'
import SymbolSelector from './SymbolSelector'
import DemoToggle from './DemoToggle'
import TradeHistory from './TradeHistory'
import PortfolioStats from './PortfolioStats'
import './Dashboard.css'

function Dashboard({
    isConnected,
    messages,
    status,
    onStart,
    onStop,
    onTrigger,
    currentSymbol,
    onSymbolChange,
    demoMode,
    onDemoToggle
}) {
    const isRunning = status?.status === 'running'
    const [activeTab, setActiveTab] = useState('debate') // debate, trades, stats

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
                    <DemoToggle demoMode={demoMode} onToggle={onDemoToggle} />
                    <StatusIndicator connected={isConnected} running={isRunning} />
                    <SymbolSelector currentSymbol={currentSymbol} onSymbolChange={onSymbolChange} />
                </div>
            </header>

            {/* Main Content */}
            <main className="dashboard-main">
                {/* Left Panel - Chart */}
                <section className="panel chart-panel glass">
                    <div className="panel-header">
                        <h2>📈 Market View</h2>
                        <div className="panel-badges">
                            <div className="panel-badge">Live</div>
                            {demoMode && <div className="panel-badge demo">Demo</div>}
                        </div>
                    </div>
                    <TradingChart symbol={currentSymbol} />
                </section>

                {/* Right Panel - Tabbed Content */}
                <section className="panel right-panel glass">
                    {/* Tabs */}
                    <div className="panel-tabs">
                        <button
                            className={`tab-btn ${activeTab === 'debate' ? 'active' : ''}`}
                            onClick={() => setActiveTab('debate')}
                        >
                            🏛️ Committee
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'trades' ? 'active' : ''}`}
                            onClick={() => setActiveTab('trades')}
                        >
                            📊 Trades
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
                            onClick={() => setActiveTab('stats')}
                        >
                            📈 Analytics
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="tab-content">
                        {activeTab === 'debate' && (
                            <>
                                <div className="tab-header">
                                    <span className="message-count">{messages.length} messages</span>
                                </div>
                                <CommitteeRoom messages={messages} />
                            </>
                        )}
                        {activeTab === 'trades' && <TradeHistory />}
                        {activeTab === 'stats' && <PortfolioStats />}
                    </div>
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
