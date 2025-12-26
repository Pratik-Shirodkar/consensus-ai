import { useState, useEffect } from 'react'
import './SymbolSelector.css'

const SYMBOL_ICONS = {
    'cmt_btcusdt': { icon: '₿', name: 'BTC', color: '#f7931a' },
    'cmt_ethusdt': { icon: 'Ξ', name: 'ETH', color: '#627eea' },
    'cmt_solusdt': { icon: '◎', name: 'SOL', color: '#14f195' },
    'cmt_dogeusdt': { icon: '🐕', name: 'DOGE', color: '#c2a633' },
    'cmt_xrpusdt': { icon: '✕', name: 'XRP', color: '#23292f' },
    'cmt_adausdt': { icon: '₳', name: 'ADA', color: '#0033ad' },
    'cmt_bnbusdt': { icon: '◆', name: 'BNB', color: '#f3ba2f' },
    'cmt_ltcusdt': { icon: 'Ł', name: 'LTC', color: '#bfbbbb' },
}

function SymbolSelector({ currentSymbol, onSymbolChange }) {
    const [symbols, setSymbols] = useState([])
    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        fetch('/api/symbols')
            .then(res => res.json())
            .then(data => setSymbols(data.symbols || []))
            .catch(err => console.error('Failed to fetch symbols:', err))
    }, [])

    const current = SYMBOL_ICONS[currentSymbol] || { icon: '●', name: currentSymbol?.split('_')[1]?.toUpperCase() || 'BTC', color: '#7c3aed' }

    return (
        <div className="symbol-selector">
            <button
                className="symbol-button"
                onClick={() => setIsOpen(!isOpen)}
                style={{ '--symbol-color': current.color }}
            >
                <span className="symbol-icon">{current.icon}</span>
                <span className="symbol-name">{current.name}/USDT</span>
                <span className="dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
            </button>

            {isOpen && (
                <div className="symbol-dropdown">
                    {symbols.map(symbol => {
                        const info = SYMBOL_ICONS[symbol] || { icon: '●', name: symbol, color: '#666' }
                        return (
                            <button
                                key={symbol}
                                className={`symbol-option ${symbol === currentSymbol ? 'active' : ''}`}
                                onClick={() => {
                                    onSymbolChange(symbol)
                                    setIsOpen(false)
                                }}
                                style={{ '--symbol-color': info.color }}
                            >
                                <span className="symbol-icon">{info.icon}</span>
                                <span className="symbol-name">{info.name}/USDT</span>
                            </button>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export default SymbolSelector
