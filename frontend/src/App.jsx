import { useState, useEffect, useCallback } from 'react'
import Dashboard from './components/Dashboard'

function App() {
    const [isConnected, setIsConnected] = useState(false)
    const [messages, setMessages] = useState([])
    const [status, setStatus] = useState(null)
    const [ws, setWs] = useState(null)

    // Connect to WebSocket
    useEffect(() => {
        const websocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/debate`)

        websocket.onopen = () => {
            console.log('WebSocket connected')
            setIsConnected(true)
        }

        websocket.onclose = () => {
            console.log('WebSocket disconnected')
            setIsConnected(false)
        }

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)

                if (data.type === 'debate_message') {
                    setMessages(prev => [...prev, data])
                } else if (data.type === 'status_update') {
                    setStatus(data)
                }
            } catch (e) {
                console.error('Error parsing message:', e)
            }
        }

        setWs(websocket)

        return () => {
            websocket.close()
        }
    }, [])

    // Fetch initial status
    useEffect(() => {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => setStatus(data))
            .catch(console.error)
    }, [])

    // Control functions
    const startTrading = useCallback(async () => {
        try {
            const res = await fetch('/api/start', { method: 'POST' })
            const data = await res.json()
            console.log('Started:', data)
        } catch (e) {
            console.error('Error starting:', e)
        }
    }, [])

    const stopTrading = useCallback(async () => {
        try {
            const res = await fetch('/api/stop', { method: 'POST' })
            const data = await res.json()
            console.log('Stopped:', data)
        } catch (e) {
            console.error('Error stopping:', e)
        }
    }, [])

    const triggerDebate = useCallback(async () => {
        try {
            const res = await fetch('/api/debate/trigger', { method: 'POST' })
            const data = await res.json()
            console.log('Debate triggered:', data)
        } catch (e) {
            console.error('Error triggering:', e)
        }
    }, [])

    return (
        <Dashboard
            isConnected={isConnected}
            messages={messages}
            status={status}
            onStart={startTrading}
            onStop={stopTrading}
            onTrigger={triggerDebate}
        />
    )
}

export default App
