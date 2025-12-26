/**
 * NotificationService - Browser push notifications for trade events
 */

class NotificationService {
    constructor() {
        this.permission = 'default'
        this.enabled = false
    }

    async requestPermission() {
        if (!('Notification' in window)) {
            console.log('Browser does not support notifications')
            return false
        }

        try {
            const permission = await Notification.requestPermission()
            this.permission = permission
            this.enabled = permission === 'granted'
            return this.enabled
        } catch (error) {
            console.error('Error requesting notification permission:', error)
            return false
        }
    }

    showNotification(title, options = {}) {
        if (!this.enabled) return

        const notification = new Notification(title, {
            icon: '🧠',
            badge: '🧠',
            ...options
        })

        // Auto close after 5 seconds
        setTimeout(() => notification.close(), 5000)

        return notification
    }

    // Trade execution notification
    notifyTradeExecuted(trade) {
        const isProfit = trade.pnl && trade.pnl > 0
        const symbol = trade.symbol?.replace('cmt_', '').toUpperCase()

        this.showNotification(`Trade Executed: ${symbol}`, {
            body: `${trade.action} ${trade.side} @ $${trade.price?.toLocaleString()}\n${trade.pnl ? (isProfit ? '✅ Profit: +' : '❌ Loss: ') + trade.pnl.toFixed(2) : ''}`,
            tag: `trade-${trade.id}`,
            requireInteraction: false
        })
    }

    // Debate decision notification
    notifyDebateDecision(decision) {
        this.showNotification('🏛️ Committee Decision', {
            body: `Action: ${decision.action}\nConfidence: ${(decision.confidence * 100).toFixed(0)}%`,
            tag: 'debate-decision'
        })
    }

    // Alert notification
    notifyAlert(message, type = 'info') {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        }

        this.showNotification(`${icons[type] || '📢'} Alert`, {
            body: message,
            tag: 'alert'
        })
    }
}

// Singleton instance
const notificationService = new NotificationService()

export default notificationService
