/**
 * PasteurAI — Preload script
 *
 * Exposes selected Electron APIs to the renderer via contextBridge.
 * Only whitelisted functions are available — no full Node.js access.
 */

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('__ELECTRON__', true)

contextBridge.exposeInMainWorld('electronAPI', {
  // Kiosk
  exitKiosk: () => ipcRenderer.invoke('kiosk:exit'),
  restartApp: () => ipcRenderer.invoke('app:restart'),
  shutdownApp: () => ipcRenderer.invoke('app:shutdown'),
  restartSystem: () => ipcRenderer.invoke('system:restart'),
  shutdownSystem: () => ipcRenderer.invoke('system:shutdown'),

  // Printer
  testPrinter: () => ipcRenderer.invoke('printer:test'),

  // Info
  platform: process.platform,
  version: process.env.npm_package_version || '1.0.0',
})
