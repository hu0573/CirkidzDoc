import { useState, type ChangeEvent } from 'react'

interface TemplateUploadPanelProps {
  onUpload: (file: File) => Promise<void>
  isUploading?: boolean
}

export function TemplateUploadPanel({ onUpload, isUploading }: TemplateUploadPanelProps) {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    setLocalError(null)
    setSelectedFileName(file.name)

    try {
      await onUpload(file)
      setSelectedFileName(null)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed. Please try again later.'
      setLocalError(message)
    } finally {
      // Allow users to pick the same file again if needed
      event.target.value = ''
    }
  }

  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">Upload Template</h2>
      <p className="mt-2 text-sm text-slate-500">
        Pick a DOCX template file. The system will create a template directory and extract <code>{'{{placeholder}}'}</code> variables to build the metadata.
      </p>

      <label
        className={`mt-4 inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 ${
          isUploading ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
        }`}
      >
        <input
          type="file"
          accept=".docx"
          className="sr-only"
          disabled={isUploading}
          onChange={(event) => void handleFileChange(event)}
        />
        <span>{isUploading ? 'Uploading…' : 'Choose DOCX File'}</span>
      </label>

      {selectedFileName ? (
        <p className="mt-3 text-xs text-slate-500">Selected file: {selectedFileName}</p>
      ) : null}

      {localError ? <p className="mt-2 text-xs text-red-600">{localError}</p> : null}

      <p className="mt-4 text-xs text-slate-400">
        After a successful upload, the new template appears at the top of the list so you can edit fields or start rendering immediately.
      </p>
    </div>
  )
}
