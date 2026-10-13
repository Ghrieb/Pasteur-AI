export type EventLevel = 'info' | 'success' | 'warning' | 'error'

export type AppEvent =
  | { type: 'session:started'; payload: { sessionId: string } }
  | { type: 'session:ended'; payload: { sessionId: string; reason: string } }
  | { type: 'session:updated'; payload: { sessionId: string; status: string } }
  | { type: 'language:changed'; payload: { language: string } }
  | { type: 'theme:changed'; payload: { theme: string } }
  | { type: 'qr:detected'; payload: { reportRef: string; sessionId: string } }
  | { type: 'pdf:downloading'; payload: { reportRef: string } }
  | { type: 'pdf:downloaded'; payload: { reportRef: string; path: string } }
  | { type: 'report:parsing'; payload: { reportRef: string } }
  | { type: 'report:parsed'; payload: { reportRef: string; testCount: number } }
  | { type: 'ai:interpreting'; payload: { reportRef: string } }
  | { type: 'ai:interpreted'; payload: { reportRef: string } }
  | { type: 'dashboard:ready'; payload: { reportRef: string; sessionId: string } }
  | { type: 'notification'; payload: { level: EventLevel; message: string; source?: string } }
  | { type: 'device:error'; payload: { device: string; error: string } }
  | { type: 'device:status'; payload: { device: string; status: string } }
  | { type: 'admin:unlocked'; payload: unknown }
  | { type: 'admin:locked'; payload: unknown }
  | { type: 'voice:toggled'; payload: { enabled: boolean } }
  | { type: 'kiosk:exit'; payload: unknown }

type Listener = (event: AppEvent) => void

class EventBus {
  private listeners: Map<string, Set<Listener>> = new Map()
  private history: AppEvent[] = []
  private maxHistory = 500

  on<E extends AppEvent['type']>(type: E, fn: (event: Extract<AppEvent, { type: E }>) => void): () => void
  on(type: string, fn: Listener): () => void
  on(type: string, fn: Listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(fn)
    return () => { this.listeners.get(type)?.delete(fn) }
  }

  emit(event: AppEvent) {
    this.history.push(event)
    if (this.history.length > this.maxHistory) this.history.shift()
    this.listeners.get(event.type)?.forEach((fn) => fn(event))
    this.listeners.get('*')?.forEach((fn) => fn(event))
  }

  getHistory(): AppEvent[] {
    return [...this.history]
  }

  clearHistory() {
    this.history = []
  }
}

export const eventBus = new EventBus()
export type { AppEvent as AppEventType }
