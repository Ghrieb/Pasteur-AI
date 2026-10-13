import { eventBus } from './event-bus'

export interface SessionEvent {
  type: string
  timestamp: Date
  data?: Record<string, unknown>
}

export interface PatientSession {
  id: string
  startedAt: Date
  patientName?: string
  reportRef?: string
  status: 'idle' | 'scanning' | 'downloading' | 'parsing' | 'interpreting' | 'dashboard' | 'completed' | 'error'
  events: SessionEvent[]
  metadata: Record<string, unknown>
}

class SessionManager {
  private current: PatientSession | null = null
  private sessions: PatientSession[] = []

  private generateId(): string {
    const ts = Date.now().toString(36)
    const rnd = Math.random().toString(36).slice(2, 6)
    return `ses_${ts}${rnd}`
  }

  start(): PatientSession {
    if (this.current) this.end('new_session')
    const session: PatientSession = {
      id: this.generateId(),
      startedAt: new Date(),
      status: 'idle',
      events: [],
      metadata: {},
    }
    this.current = session
    this.sessions.push(session)
    this.addEvent('session:started')
    eventBus.emit({ type: 'session:started', payload: { sessionId: session.id } })
    return session
  }

  getCurrent(): PatientSession | null {
    return this.current
  }

  update(partial: Partial<PatientSession>) {
    if (!this.current) return
    Object.assign(this.current, partial)
    eventBus.emit({
      type: 'session:updated',
      payload: { sessionId: this.current.id, status: this.current.status },
    })
  }

  addEvent(type: string, data?: Record<string, unknown>) {
    if (!this.current) return
    this.current.events.push({ type, timestamp: new Date(), data })
  }

  end(reason = 'completed') {
    if (!this.current) return
    this.current.status = 'completed'
    this.addEvent('session:ended', { reason })
    eventBus.emit({
      type: 'session:ended',
      payload: { sessionId: this.current.id, reason },
    })
    this.current = null
  }

  getAll(): PatientSession[] {
    return [...this.sessions]
  }

  getRecent(limit = 10): PatientSession[] {
    return [...this.sessions].slice(-limit).reverse()
  }
}

export const sessionManager = new SessionManager()
