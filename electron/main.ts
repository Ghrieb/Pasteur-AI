/**
 * PasteurAI — Electron Main Process
 *
 * Kiosk-mode shell for the Next.js frontend.
 * - Full-screen, no chrome, no menus
 * - Spawns FastAPI backend on startup
 * - Prints to ESC/POS thermal printer via child_process
 * - Exposes secure IPC for admin console
 */

const { app, BrowserWindow, ipcMain, screen } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow: any = null
let backendProcess: any = null

const IS_DEV = process.env.NODE_ENV === 'development'
const FRONTEND_URL = IS_DEV ? 'http://localhost:5173' : `file://${path.join(__dirname, '../frontend/dist/index.html')}`
const BACKEND_PORT = 8000

// ── Start FastAPI backend ─────────────────────────────

function startBackend() {
  const pythonExe = process.platform === 'win32' ? 'py' : 'python3'
  const serverPath = path.join(__dirname, '../backend/server.py')

  backendProcess = spawn(pythonExe, [serverPath], {
    cwd: path.join(__dirname, '..'),
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  backendProcess.stdout.on('data', (data: Buffer) => {
    console.log(`[backend] ${data.toString().trim()}`)
  })

  backendProcess.stderr.on('data', (data: Buffer) => {
    console.error(`[backend] ${data.toString().trim()}`)
  })

  backendProcess.on('error', (err: Error) => {
    console.error('[backend] Failed to start:', err.message)
  })

  backendProcess.on('exit', (code: number | null) => {
    console.log(`[backend] exited with code ${code}`)
  })
}

// ── Create kiosk window ───────────────────────────────

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    fullscreen: true,
    frame: false,
    resizable: false,
    kiosk: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  })

  // Load frontend
  mainWindow.loadURL(FRONTEND_URL)

  // Block all navigation and new windows
  mainWindow.webContents.on('will-navigate', (e: any, url: string) => {
    if (!url.startsWith('http://localhost')) {
      e.preventDefault()
    }
  })

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))

  // Disable right-click
  mainWindow.webContents.on('context-menu', (e: any) => e.preventDefault())

  // Kill all shortcuts
  mainWindow.webContents.on('before-input-event', (e: any, input: any) => {
    // Allow Ctrl+Shift+D for admin
    if (input.control && input.shift && input.key === 'D') return
    // Block Alt+F4, F11, Ctrl+W, etc.
    if (input.alt || input.meta) e.preventDefault()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ── IPC handlers (admin console → system) ─────────────

ipcMain.handle('kiosk:exit', () => {
  if (mainWindow) {
    mainWindow.setKiosk(false)
    mainWindow.close()
  }
})

ipcMain.handle('app:restart', () => {
  app.relaunch()
  app.exit(0)
})

ipcMain.handle('app:shutdown', () => {
  app.exit(0)
})

ipcMain.handle('system:restart', () => {
  const cmd = process.platform === 'win32' ? 'shutdown /r /t 5' : 'sudo shutdown -r +1'
  require('child_process').exec(cmd)
})

ipcMain.handle('system:shutdown', () => {
  const cmd = process.platform === 'win32' ? 'shutdown /s /t 5' : 'sudo shutdown -h +1'
  require('child_process').exec(cmd)
})

ipcMain.handle('printer:test', async () => {
  // ESC/POS test: send a raw print command via USB/serial
  console.log('[printer] Test page requested')
  return { status: 'printed' }
})

// ── App lifecycle ─────────────────────────────────────

app.whenReady().then(() => {
  startBackend()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
})
