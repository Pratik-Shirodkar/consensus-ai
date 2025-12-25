import './ControlPanel.css'

function ControlPanel({ isRunning, onStart, onStop, onTrigger }) {
    return (
        <div className="control-panel">
            <button
                className="btn btn-outline trigger-btn"
                onClick={onTrigger}
                title="Trigger a single debate cycle"
            >
                ⚡ Trigger Debate
            </button>

            {isRunning ? (
                <button
                    className="btn btn-danger"
                    onClick={onStop}
                >
                    ⏹️ Stop Trading
                </button>
            ) : (
                <button
                    className="btn btn-success"
                    onClick={onStart}
                >
                    ▶️ Start Trading
                </button>
            )}
        </div>
    )
}

export default ControlPanel
