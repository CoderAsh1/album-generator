import React, { useState, useRef } from 'react'
import { 
  FolderUp, 
  Sparkles, 
  FileDown, 
  CheckCircle2, 
  Loader2, 
  BookOpen, 
  Layers, 
  ArrowRight,
  RefreshCw,
  AlertCircle
} from 'lucide-react'

export default function App() {
  const [stage, setStage] = useState('idle') // 'idle' | 'uploading' | 'processing' | 'generating_pdf' | 'completed' | 'error'
  const [progressText, setProgressText] = useState('')
  const [spreadCount, setSpreadCount] = useState(0)
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState(null)
  const [pdfFilename, setPdfFilename] = useState('')
  const [spreadPreviews, setSpreadPreviews] = useState([])
  const [errorMessage, setErrorMessage] = useState('')

  const fileInputRef = useRef(null)

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    setStage('uploading')
    setErrorMessage('')
    setProgressText(`Uploading ${files.length} photos across event folders...`)

    const formData = new FormData()
    files.forEach((file) => {
      const relPath = file.webkitRelativePath || file.name
      formData.append('files', file)
      formData.append('relative_paths', relPath)
    })

    try {
      // Step 1: Upload photos
      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })
      if (!uploadRes.ok) throw new Error('Failed to upload photos')
      const uploadData = await uploadRes.json()

      // Step 2: Process spreads (10800x3600 @ 300 DPI)
      setStage('processing')
      setProgressText('Composing 10,800 × 3,600 px @ 300 DPI panoramic spreads...')
      
      const genRes = await fetch('/api/generate-album?theme_id=royal_blue_gold', {
        method: 'POST',
      })
      if (!genRes.ok) throw new Error('Failed to generate album spreads')
      const genData = await genRes.json()
      
      const spreads = genData.spreads || []
      setSpreadCount(spreads.length)
      setSpreadPreviews(spreads.map(s => s.preview_url).filter(Boolean))

      // Step 3: Export 300 DPI PDF
      setStage('generating_pdf')
      setProgressText(`Compiling ${spreads.length} spreads into print-ready 300 DPI PDF...`)

      const pdfRes = await fetch('/api/export-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ album_title: "Wedding Photobook (10800x3600 300DPI)" })
      })
      if (!pdfRes.ok) throw new Error('Failed to generate PDF')
      const pdfData = await pdfRes.json()

      // Step 4: Auto-download PDF
      setStage('completed')
      setProgressText('300 DPI Print PDF generated! Downloading now...')
      setPdfDownloadUrl(pdfData.download_url)
      setPdfFilename(pdfData.pdf_filename)

      // Trigger automatic browser download
      const downloadLink = document.createElement('a')
      downloadLink.href = pdfData.download_url
      downloadLink.download = pdfData.pdf_filename || 'wedding_album_300dpi.pdf'
      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)

    } catch (err) {
      console.error(err)
      setStage('error')
      setErrorMessage(err.message || 'An error occurred during album processing')
    }
  }

  const handleDemoRun = async () => {
    setStage('processing')
    setErrorMessage('')
    setProgressText('Loading demo wedding events (001 - Haldi, 002 - Wedding)...')

    try {
      const demoRes = await fetch('/api/sample-demo', { method: 'POST' })
      if (!demoRes.ok) throw new Error('Failed to load demo')
      const demoData = await demoRes.json()

      const spreads = demoData.spreads || []
      setSpreadCount(spreads.length)
      setSpreadPreviews(spreads.map(s => s.preview_url).filter(Boolean))

      setStage('generating_pdf')
      setProgressText('Compiling 10,800 × 3,600 px spreads into 300 DPI PDF...')

      const pdfRes = await fetch('/api/export-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!pdfRes.ok) throw new Error('Failed to export PDF')
      const pdfData = await pdfRes.json()

      setStage('completed')
      setProgressText('PDF ready! Automatic download triggered.')
      setPdfDownloadUrl(pdfData.download_url)
      setPdfFilename(pdfData.pdf_filename)

      const downloadLink = document.createElement('a')
      downloadLink.href = pdfData.download_url
      downloadLink.download = pdfData.pdf_filename || 'wedding_album_300dpi.pdf'
      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)
    } catch (err) {
      console.error(err)
      setStage('error')
      setErrorMessage(err.message || 'Demo generation failed')
    }
  }

  const handleReset = () => {
    setStage('idle')
    setProgressText('')
    setPdfDownloadUrl(null)
    setSpreadPreviews([])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const isWorking = stage === 'uploading' || stage === 'processing' || stage === 'generating_pdf'

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col items-center justify-center p-6 relative selection:bg-gold-500 selection:text-black">
      {/* Background glow accents */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-r from-gold-600/10 via-amber-500/10 to-gold-600/10 blur-[120px] pointer-events-none rounded-full"></div>

      <div className="w-full max-w-2xl z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-gold-400 via-gold-500 to-gold-700 shadow-xl shadow-gold-900/30 mb-4">
            <BookOpen className="w-7 h-7 text-slate-950 stroke-[2.2]" />
          </div>
          <h1 className="text-2xl md:text-3xl font-serif font-bold tracking-wide gold-gradient-text">
            ALBUM MAKER
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1 font-sans">
            Ultra High-Resolution <span className="text-gold-400 font-semibold">10,800 × 3,600 px @ 300 DPI</span> Wedding Photobook
          </p>
        </div>

        {/* Main Card */}
        <div className="glass-panel rounded-2xl p-8 shadow-2xl border border-slate-800/80 backdrop-blur-xl relative overflow-hidden">
          
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            webkitdirectory="true"
            directory="true"
            multiple
            className="hidden"
          />

          {stage === 'idle' && (
            <div className="flex flex-col items-center text-center">
              {/* Big Upload Area */}
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="w-full border-2 border-dashed border-gold-500/40 hover:border-gold-400 hover:bg-gold-500/5 transition-all duration-200 rounded-2xl p-10 cursor-pointer flex flex-col items-center justify-center group"
              >
                <div className="w-16 h-16 rounded-full bg-slate-900/90 border border-gold-500/30 flex items-center justify-center mb-4 group-hover:scale-110 transition duration-200 shadow-lg shadow-black/40">
                  <FolderUp className="w-8 h-8 text-gold-400" />
                </div>
                
                <h3 className="text-base font-semibold text-slate-100 mb-1">
                  Click to Upload Event Folders
                </h3>
                <p className="text-xs text-slate-400 max-w-sm mb-4">
                  Select folders like <span className="text-gold-400 font-mono">001 - haldi</span>, <span className="text-gold-400 font-mono">002 - wedding</span>
                </p>

                <div className="px-6 py-3 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-slate-950 text-xs font-bold transition shadow-lg shadow-gold-600/30 flex items-center gap-2 group-hover:shadow-gold-500/40">
                  <FolderUp className="w-4 h-4" />
                  <span>Select Folders & Auto-Generate</span>
                </div>
              </div>

              {/* Quick Demo Option */}
              <div className="mt-6 flex items-center gap-2 text-xs text-slate-500">
                <span>Or test immediately:</span>
                <button
                  onClick={handleDemoRun}
                  className="text-gold-400 hover:text-gold-300 font-medium underline underline-offset-4 flex items-center gap-1 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Run Demo (Haldi + Wedding)</span>
                </button>
              </div>
            </div>
          )}

          {/* Processing State */}
          {isWorking && (
            <div className="py-8 flex flex-col items-center text-center">
              <div className="relative mb-6">
                <div className="w-20 h-20 rounded-full bg-slate-900 border border-gold-500/30 flex items-center justify-center">
                  <Loader2 className="w-10 h-10 text-gold-400 animate-spin" />
                </div>
                <div className="absolute inset-0 rounded-full border-2 border-gold-500/20 animate-ping pointer-events-none"></div>
              </div>

              <h3 className="text-base font-semibold text-slate-100 mb-1">
                {stage === 'uploading' && 'Uploading Photos...'}
                {stage === 'processing' && 'Rendering 300 DPI Spreads...'}
                {stage === 'generating_pdf' && 'Compiling Print-Ready PDF...'}
              </h3>
              
              <p className="text-xs text-gold-300 font-mono mt-1 mb-6">
                {progressText}
              </p>

              {/* Multi-step progress indicator */}
              <div className="w-full max-w-md bg-slate-900/90 rounded-full h-2 overflow-hidden border border-slate-800">
                <div 
                  className="h-full bg-gradient-to-r from-gold-500 to-gold-400 transition-all duration-500 rounded-full"
                  style={{
                    width: stage === 'uploading' ? '30%' : stage === 'processing' ? '70%' : '95%'
                  }}
                ></div>
              </div>

              <div className="mt-4 text-[11px] text-slate-500 font-mono">
                Pixels: 10,800 × 3,600 &bull; 300 DPI &bull; Pure Quality
              </div>
            </div>
          )}

          {/* Completed / Auto Download State */}
          {stage === 'completed' && (
            <div className="py-6 flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center mb-4 text-emerald-400 shadow-xl shadow-emerald-950/50">
                <CheckCircle2 className="w-9 h-9 stroke-[2.2]" />
              </div>

              <h3 className="text-lg font-bold text-slate-100 mb-1">
                Your 300 DPI Wedding Album is Ready!
              </h3>
              <p className="text-xs text-emerald-400 mb-6">
                PDF download has started automatically.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
                {pdfDownloadUrl && (
                  <a
                    href={pdfDownloadUrl}
                    download={pdfFilename}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-slate-950 text-xs font-bold transition shadow-lg shadow-gold-600/30 flex items-center gap-2"
                  >
                    <FileDown className="w-4 h-4" />
                    <span>Download PDF Again</span>
                  </a>
                )}
                <button
                  onClick={handleReset}
                  className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition border border-slate-700 flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Create Another Album</span>
                </button>
              </div>

              {/* Spread Previews */}
              {spreadPreviews.length > 0 && (
                <div className="w-full border-t border-slate-800/80 pt-4 mt-2">
                  <div className="text-[11px] font-semibold text-slate-400 mb-3 flex items-center justify-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-gold-400" />
                    <span>Generated Spreads ({spreadPreviews.length})</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {spreadPreviews.map((url, i) => (
                      <div key={i} className="aspect-[3/1] rounded-lg overflow-hidden border border-slate-800 bg-slate-950 shadow-md">
                        <img src={url} alt={`Spread ${i+1}`} className="w-full h-full object-cover" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error State */}
          {stage === 'error' && (
            <div className="py-6 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-full bg-red-950/80 border border-red-500/40 flex items-center justify-center mb-3 text-red-400">
                <AlertCircle className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-red-200 mb-1">
                Processing Error
              </h3>
              <p className="text-xs text-slate-400 mb-6 max-w-md">
                {errorMessage}
              </p>
              <button
                onClick={handleReset}
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition border border-slate-700"
              >
                Try Again
              </button>
            </div>
          )}

        </div>

        {/* Footer info specs */}
        <div className="flex items-center justify-between text-[11px] text-slate-500 px-3 mt-4">
          <span>Format: 36" × 12" Flush Mount</span>
          <span>10800 × 3600 &bull; 300 DPI</span>
          <span>Cloud AI: gpt-image-2-image-to-image</span>
        </div>
      </div>
    </div>
  )
}
