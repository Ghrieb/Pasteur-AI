const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext

export class SpeakerService {
  private ctx: AudioContext | null = null

  private getCtx(): AudioContext {
    if (!this.ctx) this.ctx = new AudioCtx()
    if (this.ctx.state === 'suspended') this.ctx.resume()
    return this.ctx
  }

  beep(frequency = 1000, duration = 200, type: OscillatorType = 'sine') {
    const ctx = this.getCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = type
    osc.frequency.value = frequency
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration / 1000)
    osc.connect(gain).connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + duration / 1000)
  }

  success() {
    this.beep(1200, 150)
    setTimeout(() => this.beep(1500, 200), 180)
  }

  error() {
    this.beep(300, 400, 'sawtooth')
  }

  scanComplete() {
    this.beep(800, 100)
    setTimeout(() => this.beep(1000, 100), 120)
    setTimeout(() => this.beep(1200, 200), 240)
  }

  destroy() {
    this.ctx?.close()
    this.ctx = null
  }
}
