import { useEffect, useState } from 'react'
import { useForm, type RegisterOptions } from 'react-hook-form'

import type {
  FieldSchema,
  OutputFormat,
  RenderRequestPayload,
  TemplateDetail,
  TemplateMetadata,
} from '../lib/types'
import { OutputFormatSelector } from './OutputFormatSelector'

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

const unsupportedFieldTypes = ['richtext']

function buildValidationMessage(field: FieldSchema, fallback: string) {
  return field.validation?.message ?? `${field.label}${fallback}`
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
  const allowedFormats = metadata?.options?.allowed_outputs ?? []
  const pdfCapabilities = metadata?.options?.pdf

  const { register, handleSubmit, reset, setError, clearErrors, formState } = useForm<FormValues>({
    mode: 'onBlur',
  })
  const { errors, isSubmitting: formSubmitting } = formState

  const [selectedFormats, setSelectedFormats] = useState<string[]>([])
  const [formatsError, setFormatsError] = useState<string | null>(null)
  const [fileStates, setFileStates] = useState<Record<string, FileState>>({})
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!metadata) {
      reset({})
      setSelectedFormats([])
      setFormatsError(null)
      setFileStates({})
      setFileErrors({})
      return
    }

    const defaultValues: FormValues = {}
    metadata.fields.forEach((field) => {
      if (field.type === 'boolean') {
        defaultValues[field.name] = field.default ?? false
      } else if (field.type === 'number' && typeof field.default === 'number') {
        defaultValues[field.name] = field.default
      } else if (field.type === 'date' && typeof field.default === 'string') {
        defaultValues[field.name] = field.default.substring(0, 10)
      } else if (field.default !== undefined && field.default !== null) {
        defaultValues[field.name] = field.default
      } else {
        defaultValues[field.name] = ''
      }
    })
    reset(defaultValues)
    const outputs = metadata.options?.allowed_outputs ?? []
    setSelectedFormats(outputs.length > 0 ? [outputs[0]] : [])
    setFormatsError(null)
    setFileStates({})
    setFileErrors({})
  }, [metadata, reset])

  const buildRegisterOptions = (field: FieldSchema): RegisterOptions =>
    Object.assign(
      {},
      field.required
        ? {
            required: `${field.label} is required`,
          }
        : {},
      field.validation?.pattern
        ? (() => {
            try {
              return {
                pattern: {
                  value: new RegExp(field.validation?.pattern),
                  message: buildValidationMessage(field, ' has an invalid format'),
                },
              }
            } catch {
              return {}
            }
          })()
        : {},
      typeof field.validation?.min_length === 'number'
        ? {
            minLength: {
              value: field.validation.min_length,
              message: buildValidationMessage(field, ` must be at least ${field.validation.min_length} characters long`),
            },
          }
        : {},
      typeof field.validation?.max_length === 'number'
        ? {
            maxLength: {
              value: field.validation.max_length,
              message: buildValidationMessage(field, ` must be at most ${field.validation.max_length} characters long`),
            },
          }
        : {},
      typeof field.validation?.minimum === 'number'
        ? {
            min: {
              value: field.validation.minimum,
              message: buildValidationMessage(field, ` cannot be less than ${field.validation.minimum}`),
            },
          }
        : {},
      typeof field.validation?.maximum === 'number'
        ? {
            max: {
              value: field.validation.maximum,
              message: buildValidationMessage(field, ` cannot be greater than ${field.validation.maximum}`),
            },
          }
        : {},
      field.type === 'number'
        ? {
            setValueAs: (value: unknown) =>
              value === '' || value === null ? undefined : Number(value),
          }
        : {},
    )

  const handleFileChange = async (field: FieldSchema, fileList: FileList | null) => {
    const file = fileList?.[0]
    if (!file) {
      setFileStates((prev) => {
        const next = { ...prev }
        delete next[field.name]
        return next
      })
      if (field.required) {
        setFileErrors((prev) => ({
          ...prev,
          [field.name]: `${field.label} is required`,
        }))
      }
      return
    }

    if (file.size > 20 * 1024 * 1024) {
      setFileErrors((prev) => ({
        ...prev,
        [field.name]: `${field.label} is too large. Please keep the file within 20MB.`,
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
  }

  const submit = handleSubmit(async (values) => {
    if (!metadata) {
      return
    }
    if (!selectedFormats.length) {
      setFormatsError('Please select at least one output format.')
      return
    }
    setFormatsError(null)

    let hasFileError = false
    const data: Record<string, unknown> = {}

    for (const field of fields) {
      if (field.type === 'file') {
        const state = fileStates[field.name]
        if (!state?.base64) {
          if (field.required) {
            setFileErrors((prev) => ({
              ...prev,
              [field.name]: `${field.label} is required`,
            }))
            hasFileError = true
          }
          continue
        }
        data[field.name] = state.base64
        continue
      }

      if (unsupportedFieldTypes.includes(field.type)) {
        continue
      }

      const value = values[field.name]

      if (value === undefined || value === null || value === '') {
        if (field.required) {
          setError(field.name, { type: 'required', message: `${field.label} is required` })
          hasFileError = true
        }
        continue
      }

      if (field.type === 'number') {
        data[field.name] = Number(value)
      } else if (field.type === 'boolean') {
        data[field.name] = Boolean(value)
      } else {
        data[field.name] = value
      }
    }

    if (hasFileError) {
      return
    }

    const payload: RenderRequestPayload = {
      template_id: metadata.id,
      data,
      formats: selectedFormats,
    }

    if (selectedFormats.includes('pdf') && pdfCapabilities) {
      const pdfOptions: Record<string, unknown> = {}
      if (pdfCapabilities.allow_flatten) {
        if (values.__pdf_flatten) {
          pdfOptions.flatten = true
        }
      }
      if (pdfCapabilities.allow_pdfa) {
        if (values.__pdf_pdfa) {
          pdfOptions.pdfa = true
        }
      }
      if (pdfCapabilities.allow_password) {
        const password = (values.__pdf_password as string)?.trim()
        if (password) {
          pdfOptions.password = password
        }
      }
      if (Object.keys(pdfOptions).length > 0) {
        payload.options = { pdf: pdfOptions }
      }
    }

    await onSubmit(payload)
  })

  const renderField = (field: FieldSchema) => {
    const commonLabel = (
      <div className="flex flex-col">
        <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
          {field.label}
          {field.required ? <span className="ml-1 text-red-500">*</span> : null}
        </label>
        {field.description ? (
          <span className="text-xs text-slate-500">{field.description}</span>
        ) : null}
      </div>
    )

    const errorMessage = errors[field.name]?.message?.toString() ?? fileErrors[field.name]

    switch (field.type) {
      case 'string':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <input
              id={field.name}
              type="text"
              placeholder={field.placeholder ?? undefined}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'number':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <input
              id={field.name}
              type="number"
              placeholder={field.placeholder ?? undefined}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'boolean':
        return (
          <div key={field.name} className="flex items-start gap-3 rounded-lg border border-slate-200 px-3 py-3">
            <input
              id={field.name}
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            />
            <div>
              <label htmlFor={field.name} className="text-sm font-medium text-slate-900">
                {field.label}
              </label>
              {field.description ? (
                <p className="text-xs text-slate-500">{field.description}</p>
              ) : null}
              {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
            </div>
          </div>
        )
      case 'date':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <input
              id={field.name}
              type="date"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'enum':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <select
              id={field.name}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            >
              <option value="">{field.placeholder ?? 'Please select'}</option>
              {field.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'textarea':
      case 'richtext':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <textarea
              id={field.name}
              rows={field.type === 'richtext' ? 6 : 4}
              placeholder={field.placeholder ?? undefined}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              {...register(field.name, buildRegisterOptions(field))}
            />
            {errorMessage ? <p className="text-xs text-red-600">{errorMessage}</p> : null}
          </div>
        )
      case 'file':
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
            <input
              id={field.name}
              type="file"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isSubmitting}
              onChange={(event) => void handleFileChange(field, event.target.files)}
            />
            <p className="text-xs text-slate-500">
              Files are submitted as Base64. Please ensure the file size is reasonable.
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
      default:
        return (
          <div key={field.name} className="space-y-1">
            {commonLabel}
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
      <div className="flex flex-col gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{metadata.name}</h2>
            <p className="text-sm text-slate-500">{metadata.description ?? 'No template description available.'}</p>
          </div>
          {metadata.version ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
              v{metadata.version}
            </span>
          ) : null}
        </div>
        {metadata.preview ? (
          <img
            src={metadata.preview}
            alt={`${metadata.name} preview`}
            className="max-h-48 w-full rounded-lg border border-slate-200 object-cover"
            onError={(event) => {
              const target = event.target as HTMLImageElement
              target.style.display = 'none'
            }}
          />
        ) : null}
      </div>

      <section className="space-y-4">
        <h3 className="text-base font-semibold text-slate-900">Field Input</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{fields.map((field) => renderField(field))}</div>
      </section>

      <section className="space-y-4">
        <h3 className="text-base font-semibold text-slate-900">Output Formats</h3>
        <OutputFormatSelector
          formats={allowedFormats}
          selected={selectedFormats}
          onChange={(next) => {
            setSelectedFormats(next)
            setFormatsError(null)
          }}
          formatCatalog={formatCatalog}
          disabled={isSubmitting}
          error={formatsError}
        />
        {selectedFormats.includes('pdf') && pdfCapabilities ? (
          <div className="space-y-3 rounded-lg border border-blue-100 bg-blue-50 p-4">
            <h4 className="text-sm font-semibold text-blue-800">Advanced PDF Options</h4>
            {pdfCapabilities.allow_flatten ? (
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  disabled={isSubmitting}
                  {...register('__pdf_flatten')}
                />
                Flatten form fields
              </label>
            ) : null}
            {pdfCapabilities.allow_pdfa ? (
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  disabled={isSubmitting}
                  {...register('__pdf_pdfa')}
                />
                Export as PDF/A
              </label>
            ) : null}
            {pdfCapabilities.allow_password ? (
              <div className="space-y-1">
                <label htmlFor="__pdf_password" className="text-sm font-medium text-slate-800">
                  Set access password
                </label>
                <input
                  id="__pdf_password"
                  type="password"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  placeholder="Leave blank to skip the password"
                  disabled={isSubmitting}
                  {...register('__pdf_password', {
                    minLength: { value: 6, message: 'Password must be at least 6 characters.' },
                  })}
                />
                {errors.__pdf_password?.message ? (
                  <p className="text-xs text-red-600">{errors.__pdf_password.message.toString()}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <div className="mt-auto flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
        <button
          type="button"
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:border-slate-300 hover:text-slate-800"
          onClick={() => {
            reset()
            setSelectedFormats(allowedFormats.length > 0 ? [allowedFormats[0]] : [])
            setFileStates({})
            setFileErrors({})
            clearErrors()
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

