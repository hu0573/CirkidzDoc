import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'

import type {
  FieldSchema,
  OutputFormat,
  RenderRequestPayload,
  TemplateDetail,
  TemplateMetadata,
} from '../lib/types'

interface TemplateDetailPanelProps {
  template?: TemplateDetail
  onSubmit: (payload: RenderRequestPayload) => Promise<void> | void
  isSubmitting?: boolean
  formatCatalog?: OutputFormat[]
}

type FormValues = Record<string, unknown>

interface FileState {
  file?: File
  base64?: string
}

const unsupportedFieldTypes = new Set(['richtext'])
const visibleFormatSet = new Set(['docx', 'pdf'])

function formatFieldLabel(field: FieldSchema): string {
  const segments = field.name
    .split('_')
    .map((part) => part.trim())
    .filter(Boolean)
  if (!segments.length) {
    return field.name
  }
  return segments
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

async function readFileAsBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunkSize = 0x8000
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize)
    binary += String.fromCharCode(...chunk)
  }
  return `data:${file.type || 'application/octet-stream'};base64,${btoa(binary)}`
}

export function TemplateDetailPanel({
  template,
  onSubmit,
  isSubmitting,
  formatCatalog,
}: TemplateDetailPanelProps) {
  const metadata: TemplateMetadata | undefined = template?.template
  const fields = metadata?.fields ?? []
  const templateEntry = metadata?.entry?.toLowerCase() ?? ''

  const systemFormats = useMemo(() => {
    if (!metadata) {
      return []
    }
    if (templateEntry.endsWith('.pdf')) {
      return ['pdf']
    }
    const catalogFormats =
      formatCatalog
        ?.map((item) => item.id.toLowerCase())
        .filter((value, index, self) => self.indexOf(value) === index) ?? []
    if (catalogFormats.length) {
      return catalogFormats
    }
    return ['docx']
  }, [formatCatalog, metadata, templateEntry])

  const availableFormats = useMemo(() => {
    if (!systemFormats.length) {
      return []
    }
    const filtered = systemFormats.filter((fmt) => visibleFormatSet.has(fmt))
    if (filtered.length) {
      return filtered
    }

    if (templateEntry.endsWith('.pdf')) {
      return ['pdf']
    }

    return ['docx']
  }, [systemFormats, templateEntry])

  const formatOptions = useMemo(() => {
    if (!availableFormats.length) {
      return []
    }

    return availableFormats.map((fmt) => {
      const match = formatCatalog?.find((item) => item.id.toLowerCase() === fmt)
      return {
        id: fmt,
        label: match?.label ?? fmt.toUpperCase(),
      }
    })
  }, [availableFormats, formatCatalog])

  const { register, handleSubmit, reset, setError, clearErrors, formState } = useForm<FormValues>({
    mode: 'onBlur',
  })
  const { errors, isSubmitting: formSubmitting } = formState

  const [fileStates, setFileStates] = useState<Record<string, FileState>>({})
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({})
  const [selectedFormats, setSelectedFormats] = useState<string[]>([])
  const [formatsError, setFormatsError] = useState<string | null>(null)

  const buildDefaultValues = (source: FieldSchema[]): FormValues => {
    const defaults: FormValues = {}
    source.forEach((field) => {
      defaults[field.name] = field.type === 'boolean' ? false : ''
    })
    return defaults
  }

  useEffect(() => {
    if (!metadata) {
      reset({})
      setFileStates({})
      setFileErrors({})
      setSelectedFormats([])
      setFormatsError(null)
      return
    }

    reset(buildDefaultValues(metadata.fields))
    setFileStates({})
    setFileErrors({})
    if (availableFormats.length) {
      setSelectedFormats(availableFormats)
    } else {
      setSelectedFormats(['docx'])
    }
    setFormatsError(null)
  }, [availableFormats, metadata, reset])

  const handleFileChange = async (field: FieldSchema, fileList: FileList | null) => {
    const label = formatFieldLabel(field)
    const file = fileList?.[0]
    if (!file) {
      setFileStates((prev) => {
        const next = { ...prev }
        delete next[field.name]
        return next
      })
      setFileErrors((prev) => ({
        ...prev,
        [field.name]: `${label} is required`,
      }))
      return
    }

    if (file.size > 20 * 1024 * 1024) {
      setFileErrors((prev) => ({
        ...prev,
        [field.name]: `${label} is too large. Please keep the file within 20MB.`,
      }))
      return
    }

    const base64 = await readFileAsBase64(file)
    setFileStates((prev) => ({
      ...prev,
      [field.name]: { file, base64 },
    }))
    setFileErrors((prev) => {
      const next = { ...prev }
      delete next[field.name]
      return next
    })
    clearErrors(field.name)
  }

  const submit = handleSubmit(async (values) => {
    if (!metadata) {
      return
    }

    const formats = selectedFormats.length
      ? selectedFormats
      : availableFormats.length
        ? availableFormats
        : ['docx']

    if (!formats.length) {
      setFormatsError('Select at least one output format.')
      return
    }

    const data: Record<string, unknown> = {}
    let hasError = false

    for (const field of fields) {
      if (unsupportedFieldTypes.has(field.type)) {
        continue
      }

      const label = formatFieldLabel(field)

      if (field.type === 'file') {
        const state = fileStates[field.name]
        if (!state?.base64) {
          setFileErrors((prev) => ({
            ...prev,
            [field.name]: `${label} is required`,
          }))
          hasError = true
          continue
        }
        data[field.name] = state.base64
        continue
      }

      const value = values[field.name]

      if (field.type === 'boolean') {
        data[field.name] = Boolean(value)
        continue
      }

      if (value === undefined || value === null || value === '') {
        setError(field.name, { type: 'required', message: `${label} is required` })
        hasError = true
        continue
      }

      if (field.type === 'number' || field.type === 'integer') {
        const numericValue = typeof value === 'number' ? value : Number(value)
        if (Number.isNaN(numericValue)) {
          setError(field.name, { type: 'pattern', message: `${label} must be a number` })
          hasError = true
          continue
        }
        if (field.type === 'integer' && !Number.isInteger(numericValue)) {
          setError(field.name, { type: 'pattern', message: `${label} must be an integer` })
          hasError = true
          continue
        }
        data[field.name] = numericValue
        continue
      }

      data[field.name] = value
    }

    if (hasError) {
      return
    }

    const payload: RenderRequestPayload = {
      template_id: metadata.id,
      data,
      formats,
    }

    await onSubmit(payload)
  })

  const renderField = (field: FieldSchema) => {
    const label = formatFieldLabel(field)
    const errorMessage = errors[field.name]?.message?.toString() ?? fileErrors[field.name]

    switch (field.type) {
      case 'number':
      case 'integer':
        return (
          <div key={field.name} className="space-y-1">
            <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
              {label}
              <span className="ml-1 text-red-500">*</span>
            </label>
            <input
              id={field.name}
              type="number"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              step={field.type === 'integer' ? '1' : 'any'}
              {...register(field.name)}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'boolean':
        return (
          <div key={field.name} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-3">
            <input
              id={field.name}
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              disabled={isSubmitting}
              {...register(field.name)}
            />
            <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
              {label}
            </label>
          </div>
        )
      case 'date':
      case 'datetime':
        return (
          <div key={field.name} className="space-y-1">
            <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
              {label}
              <span className="ml-1 text-red-500">*</span>
            </label>
            <input
              id={field.name}
              type={field.type === 'datetime' ? 'datetime-local' : 'date'}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name)}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'file':
        return (
          <div key={field.name} className="space-y-1">
            <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
              {label}
              <span className="ml-1 text-red-500">*</span>
            </label>
            <input
              id={field.name}
              type="file"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              onChange={(event) => void handleFileChange(field, event.target.files)}
            />
            <p className="text-xs text-slate-500">
              Files are submitted as Base64. Please ensure the file size is within 20MB.
            </p>
            {fileStates[field.name]?.file ? (
              <p className="text-xs text-slate-500">
                Selected: {fileStates[field.name]?.file?.name} (
                {Math.round((fileStates[field.name]?.file?.size ?? 0) / 1024)} KB)
              </p>
            ) : null}
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'string':
      case 'textarea':
      case 'enum':
      case 'email':
      case 'phone':
        return (
          <div key={field.name} className="space-y-1">
            <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
              {label}
              <span className="ml-1 text-red-500">*</span>
            </label>
            {field.type === 'textarea' ? (
              <textarea
                id={field.name}
                rows={4}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                disabled={isSubmitting}
                {...register(field.name)}
              />
            ) : (
              <input
                id={field.name}
                type={field.type === 'email' ? 'email' : field.type === 'phone' ? 'tel' : 'text'}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                disabled={isSubmitting}
                {...register(field.name)}
              />
            )}
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      default:
        return (
          <div key={field.name} className="space-y-1">
            <label className="text-sm font-medium text-slate-900">{label}</label>
            <p className="rounded-lg border border-yellow-200 bg-yellow-50 px-3 py-2 text-xs text-yellow-700">
              Field type {field.type} is not supported yet. Please contact the team to extend the frontend component.
            </p>
          </div>
        )
    }
  }

  if (!metadata) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white">
        <p className="text-sm text-slate-500">Select a template on the left to configure the fields.</p>
      </div>
    )
  }

  return (
    <form
      className="flex h-full flex-col gap-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      onSubmit={submit}
    >
      <div className="flex flex-col gap-2 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{metadata.name}</h2>
          <p className="text-sm text-slate-500">{metadata.description ?? 'No template description available.'}</p>
        </div>
        <p className="text-xs text-slate-500">
          Entry file: <span className="font-mono">{metadata.entry}</span>
        </p>
      </div>

      <section className="space-y-4">
        <h3 className="text-base font-semibold text-slate-900">Field Input</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{fields.map((field) => renderField(field))}</div>
      </section>

      <section className="space-y-3">
        <h3 className="text-base font-semibold text-slate-900">Output Formats</h3>
        {formatOptions.length ? (
          <div className="flex flex-wrap gap-2">
            {formatOptions.map((format) => {
              const isActive = selectedFormats.includes(format.id)
              return (
                <button
                  key={format.id}
                  type="button"
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-blue-200 ${
                    isActive
                      ? 'border border-blue-600 bg-blue-600 text-white shadow-sm'
                      : 'border border-slate-200 bg-white text-slate-600 hover:border-blue-400 hover:text-blue-600'
                  } ${isSubmitting ? 'cursor-not-allowed opacity-60' : ''}`}
                  onClick={() => {
                    if (isSubmitting) {
                      return
                    }
                    setFormatsError(null)
                    setSelectedFormats((prev) => {
                      if (prev.includes(format.id)) {
                        return prev.filter((item) => item !== format.id)
                      }
                      return [...prev, format.id]
                    })
                  }}
                  disabled={isSubmitting}
                >
                  {format.label}
                </button>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No format information available. The system will default to DOCX export.
          </p>
        )}
        {formatsError ? <p className="text-xs text-red-600">{formatsError}</p> : null}
      </section>

      <div className="mt-auto flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
        <button
          type="button"
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:border-slate-300 hover:text-slate-800"
          onClick={() => {
            if (metadata) {
              reset(buildDefaultValues(fields))
            } else {
              reset({})
            }
            setFileStates({})
            setFileErrors({})
            clearErrors()
            if (availableFormats.length) {
              setSelectedFormats(availableFormats)
            } else {
              setSelectedFormats(['docx'])
            }
            setFormatsError(null)
          }}
          disabled={isSubmitting}
        >
          Reset
        </button>
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
          disabled={isSubmitting}
        >
          {isSubmitting || formSubmitting ? 'Submitting...' : 'Submit Render Task'}
        </button>
      </div>
    </form>
  )
}

