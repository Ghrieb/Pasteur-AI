import { eventBus } from './event-bus'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/logs'

export type LogEntry = {
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
  source?: string
}

type LogListener = (entry: LogEntry) => void

class WsLogs {
  private ws: WebSocket | null = null
  private listeners: Set<LogListener> = new Set()
  private history: LogEntry[] = []
  private maxHistory = 500
  private reconnectAttempts = 0
  private maxReconnect = 5
  private reconnectDelay = 2000

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    try {
      this.ws = new WebSocket(WS_URL)
      this.ws.onmessage = (msg) => {
        try {
          const entry: LogEntry = JSON.parse(msg.data)
          this.history.push(entry)
          if (this.history.length > this.maxHistory) this.history.shift()
          this.listeners.forEach((fn) => fn(entry))
          eventBus.emit({
            type: 'notification',
            payload: { level: entry.level, message: entry.message, source: entry.source || 'system' },
          })
        } catch {
          /* ignore malformed messages */
        }
      }
      this.ws.onclose = () => {
        this.reconnectAttempts++
        if (this.reconnectAttempts <= this.maxReconnect) {
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts)
        }
      }
      this.ws.onerror = () => { this.ws?.close() }
    } catch {
      /* connection failed */
    }
  }

  disconnect() {
    this.ws?.close()
    this.ws = null
  }

  onLog(fn: LogListener) {
    this.listeners.add(fn)
    return () => this.listeners.delete(fn)
  }

  getHistory(): LogEntry[] {
    return [...this.history]
  }
}

export const wsLogs = new WsLogs()
