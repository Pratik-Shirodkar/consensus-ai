import { useEffect, useRef } from 'react'
import AgentMessage from './AgentMessage'
import './CommitteeRoom.css'

function CommitteeRoom({ messages }) {
    const containerRef = useRef(null)

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight
        }
    }, [messages])

    if (messages.length === 0) {
        return (
            <div className="committee-room">
                <div className="empty-state">
                    <div className="empty-icon">🏛️</div>
                    <h3>Committee Room</h3>
                    <p>The agents are analyzing the market...</p>
                    <p className="hint">Start a trading session to see the debate</p>
                </div>
            </div>
        )
    }

    return (
        <div className="committee-room" ref={containerRef}>
            <div className="messages-container">
                {messages.map((msg, index) => (
                    <AgentMessage key={index} message={msg} />
                ))}
            </div>
        </div>
    )
}

export default CommitteeRoom
