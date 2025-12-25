import './AgentMessage.css'

function AgentMessage({ message }) {
    const { agent, emoji, message: content, confidence, timestamp } = message

    const agentClass = agent.toLowerCase().replace(' ', '-')

    // Format timestamp
    const time = timestamp
        ? new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        })
        : ''

    return (
        <div className={`agent-message ${agentClass} animate-slide-in`}>
            <div className="message-header">
                <div className="agent-info">
                    <span className="agent-emoji">{emoji}</span>
                    <span className="agent-name">{agent}</span>
                    {confidence !== null && confidence !== undefined && (
                        <span className="confidence-badge">
                            {Math.round(confidence * 100)}% confident
                        </span>
                    )}
                </div>
                <span className="message-time">{time}</span>
            </div>
            <div className="message-content">
                <FormattedContent content={content} />
            </div>
        </div>
    )
}

function FormattedContent({ content }) {
    // Simple markdown-like formatting
    if (!content) return null

    // Split into lines and format
    const lines = content.split('\n')

    return (
        <div className="formatted-content">
            {lines.map((line, i) => {
                // Bold headers with **
                if (line.startsWith('**') && line.endsWith('**')) {
                    return <strong key={i}>{line.replace(/\*\*/g, '')}</strong>
                }
                // Bullet points
                if (line.startsWith('- ')) {
                    return <div key={i} className="bullet-point">• {line.slice(2)}</div>
                }
                // Empty lines
                if (line.trim() === '') {
                    return <br key={i} />
                }
                // Regular text
                return <span key={i}>{line}</span>
            })}
        </div>
    )
}

export default AgentMessage
