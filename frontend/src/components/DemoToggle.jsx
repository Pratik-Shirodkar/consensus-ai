import { useState } from 'react'
import './DemoToggle.css'

function DemoToggle({ demoMode, onToggle }) {
    const [loading, setLoading] = useState(false)

    const handleToggle = async () => {
        setLoading(true)
        try {
            await onToggle()
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={`demo-toggle ${demoMode ? 'demo' : 'live'}`}>
            <div className="demo-status">
                <span className="demo-icon">{demoMode ? '🎮' : '🔴'}</span>
                <span className="demo-label">{demoMode ? 'DEMO' : 'LIVE'}</span>
            </div>
            <button
                className="toggle-button"
                onClick={handleToggle}
                disabled={loading}
            >
                <span className={`toggle-slider ${demoMode ? 'on' : 'off'}`}>
                    <span className="toggle-knob"></span>
                </span>
            </button>
        </div>
    )
}

export default DemoToggle
