import { eventBus } from './event-bus'

type Theme = 'dark' | 'light' | 'high-contrast'

class ThemeEngine {
  private current: Theme = 'dark'

  constructor() {
    const saved = localStorage.getItem('pasteur-theme') as Theme | null
    if (saved && ['dark', 'light', 'high-contrast'].includes(saved)) {
      this.current = saved
    }
    this.apply(this.current)
  }

  get(): Theme { return this.current }

  set(theme: Theme) {
    this.current = theme
    localStorage.setItem('pasteur-theme', theme)
    this.apply(theme)
    eventBus.emit({ type: 'theme:changed', payload: { theme } })
  }

  toggle() {
    const themes: Theme[] = ['dark', 'light', 'high-contrast']
    const idx = themes.indexOf(this.current)
    this.set(themes[(idx + 1) % themes.length])
  }

  private apply(theme: Theme) {
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.classList.remove('dark', 'light', 'high-contrast')
    document.documentElement.classList.add(theme)
  }
}

export const themeEngine = new ThemeEngine()
