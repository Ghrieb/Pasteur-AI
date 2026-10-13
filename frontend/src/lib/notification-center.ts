import { eventBus, type EventLevel } from './event-bus'

export interface Notification {
  id: string
  level: EventLevel
  message: string
  timestamp: Date
  source?: string
}

type NotificationListener = (n: Notification) => void

class NotificationCenter {
  private listeners: Set<NotificationListener> = new Set()
  private history: Notification[] = []
  private maxHistory = 200

  private emit(n: Notification) {
    this.history.push(n)
    if (this.history.length > this.maxHistory) this.history.shift()
    this.listeners.forEach((fn) => fn(n))
    eventBus.emit({ type: 'notification', payload: { level: n.level, message: n.message, source: n.source } })
  }

  onNotification(fn: NotificationListener) {
    this.listeners.add(fn)
    return () => this.listeners.delete(fn)
  }

  success(message: string, source?: string) {
    this.emit({ id: this.id(), level: 'success', message, timestamp: new Date(), source })
  }

  warning(message: string, source?: string) {
    this.emit({ id: this.id(), level: 'warning', message, timestamp: new Date(), source })
  }

  error(message: string, source?: string) {
    this.emit({ id: this.id(), level: 'error', message, timestamp: new Date(), source })
  }

  info(message: string, source?: string) {
    this.emit({ id: this.id(), level: 'info', message, timestamp: new Date(), source })
  }

  getHistory(): Notification[] {
    return [...this.history]
  }

  private id(): string {
    return `ntf_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`
  }
}

export const notificationCenter = new NotificationCenter()
