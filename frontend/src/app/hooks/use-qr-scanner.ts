import { useEffect, useRef, useState, useCallback } from 'react'
import jsQR from 'jsqr'
import { eventBus } from '../../lib/event-bus'
import { sessionManager } from '../../lib/session-manager'
import { SpeakerService } from '../../lib/devices/speaker'

export function useQrScanner(options?: { reportPattern?: RegExp }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const speaker = useRef(new SpeakerService())
  const scanning = useRef(false)
  const rafId = useRef(0)
  const [status, setStatus] = useState<'idle' | 'scanning' | 'detected' | 'error'>('idle')
  const [detectedCode, setDetectedCode] = useState<string | null>(null)
  const [rawData, setRawData] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const pattern = options?.reportPattern || /(?:\/r\/)(\d+)/

  const decode = useCallback(() => {
    if (!scanning.current) return
    const video = videoRef.current
    if (!video || video.readyState < 2) {
      rafId.current = requestAnimationFrame(decode)
      return
    }

    const c = document.createElement('canvas')
    c.width = video.videoWidth
    c.height = video.videoHeight
    const ctx = c.getContext('2d', { willReadFrequently: true })
    if (!ctx) { rafId.current = requestAnimationFrame(decode); return }

    ctx.drawImage(video, 0, 0)
    const imageData = ctx.getImageData(0, 0, c.width, c.height)
    const code = jsQR(imageData.data, imageData.width, imageData.height)

    if (code?.data) {
      const match = code.data.match(pattern)
      const ref = match?.[1] || code.data
      scanning.current = false
      setDetectedCode(ref)
      setRawData(code.data)
      setStatus('detected')
      speaker.current.success()
      const session = sessionManager.getCurrent() || sessionManager.start()
      eventBus.emit({ type: 'qr:detected', payload: { reportRef: ref, rawUrl: code.data, sessionId: session.id } })
      return
    }

    rafId.current = requestAnimationFrame(decode)
  }, [pattern])

  const start = useCallback(async () => {
    const video = videoRef.current
    if (!video) { setErrorMsg('Video element not found'); setStatus('error'); return }

    if (!navigator.mediaDevices?.getUserMedia) {
      setErrorMsg('API caméra non supportée. Utilisez HTTPS ou localhost.')
      setStatus('error')
      return
    }

    if (window.location.protocol === 'file:') {
      setErrorMsg('La caméra ne fonctionne pas en mode fichier (file://). Utilisez http://localhost.')
      setStatus('error')
      return
    }

    setStatus('scanning')
    setDetectedCode(null)
    setErrorMsg('')

    try {
      let stream: MediaStream
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        })
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        })
      }
      streamRef.current = stream
      video.srcObject = stream
      await video.play()
      scanning.current = true
      rafId.current = requestAnimationFrame(decode)
    } catch (err) {
      const msg = String(err)
      if (msg.includes('NotAllowedError')) {
        setErrorMsg('Permission caméra refusée. Autorisez la caméra dans les paramètres du navigateur.')
      } else if (msg.includes('NotFoundError')) {
        setErrorMsg('Aucune caméra trouvée sur cet appareil.')
      } else if (msg.includes('NotReadableError')) {
        setErrorMsg('Caméra utilisée par une autre application.')
      } else if (msg.includes('OverconstrainedError')) {
        setErrorMsg('Caméra arrière non trouvée. Vérifiez votre matériel.')
      } else if (window.location.protocol === 'http:' && window.location.hostname !== 'localhost') {
        setErrorMsg('HTTPS requis pour la caméra (sauf localhost).')
      } else {
        setErrorMsg(`Erreur caméra: ${msg.slice(0, 120)}`)
      }
      setStatus('error')
    }
  }, [decode])

  const stop = useCallback(() => {
    scanning.current = false
    cancelAnimationFrame(rafId.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setStatus('idle')
  }, [])

  const reset = useCallback(() => {
    stop()
    setDetectedCode(null)
    setErrorMsg('')
    setStatus('idle')
  }, [stop])

  useEffect(() => {
    return () => { stop(); speaker.current.destroy() }
  }, [stop])

  return { videoRef, status, detectedCode, rawData, errorMsg, start, stop, reset }
}
