const API_BASE = import.meta.env.VITE_API_URL || ''

export class PrinterService {
  async print(reportRef: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/api/print-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_ref: reportRef }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(body.detail || 'Print failed')
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const printWindow = window.open(url)
    if (printWindow) {
      printWindow.onload = () => { printWindow.print() }
    }
    setTimeout(() => URL.revokeObjectURL(url), 1500)
    return { success: true, message: 'PDF sent to printer' }
  }

  async downloadPdf(reportRef: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/api/print-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_ref: reportRef }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(body.detail || 'PDF generation failed')
    }
    return res.blob()
  }

  async status(): Promise<{ available: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/api/admin/printer/status`)
    if (!res.ok) return { available: false, message: 'Printer unavailable' }
    return res.json()
  }
}
