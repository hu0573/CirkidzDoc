import { useEffect, useMemo, useState } from 'react'

import type { FieldType, TemplateMetadata, TemplateUpdateRequest } from '../lib/types'

interface TemplateMetadataEditorProps {
  template?: TemplateMetadata
  isOpen: boolean
  isSubmitting?: boolean
  onClose: () => void
  onSubmit: (payload: TemplateUpdateRequest) => Promise<void>
}

interface EditableField {
  name: string
  type: FieldType
}

const editableTypeOptions: Array<{ value: FieldType; label: string; disabled?: boolean }> = [
  { value: 'string', label: 'Text (single line)' },
  { value: 'textarea', label: 'Text (multi line)' },
  { value: 'number', label: 'Number (decimal)' },
  { value: 'integer', label: 'Number (integer)' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'date', label: 'Date' },
  { value: 'datetime', label: 'Date & time' },
  { value: 'boolean', label: 'Boolean' },
  { value: 'file', label: 'File (disabled)', disabled: true },
  { value: 'enum', label: 'Enum (deprecated)', disabled: true },
  { value: 'richtext', label: 'Rich text (unsupported)', disabled: true },
]

function findOptionLabel(value: FieldType) {
  return editableTypeOptions.find((option) => option.value === value)?.label ?? value
}

export function TemplateMetadataEditor({
  template,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
}: TemplateMetadataEditorProps) {
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [fields, setFields] = useState<EditableField[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) {
      return
    }

    if (!template) {
      setName('')
      setDescription('')
      setFields([])
      return
    }

    setName(template.name)
    setDescription(template.description ?? '')
    setFields(template.fields.map((field) => ({ name: field.name, type: field.type })))
  }, [isOpen, template])

  const isPristine = useMemo(() => {
    if (!template) {
      return true
    }
    const sameName = name === template.name
    const sameDescription = (description ?? '') === (template.description ?? '')
    const sameFields =
      fields.length === template.fields.length &&
      fields.every((field, index) => field.name === template.fields[index].name && field.type === template.fields[index].type)
    return sameName && sameDescription && sameFields
  }, [description, fields, name, template])

  if (!isOpen) {
    return null
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError(null)

    if (!template) {
      setFormError('Template metadata is not available.')
      return
    }

    if (!name.trim()) {
      setFormError('Template name is required.')
      return
    }

    if (fields.some((field) => !field.type)) {
      setFormError('Please choose a type for each field.')
      return
    }

    const payload: TemplateUpdateRequest = {
      name: name.trim(),
      description: description.trim(),
      fields: fields.map((field) => ({
        name: field.name,
        type: field.type,
      })),
    }

    await onSubmit(payload)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 px-4 py-6 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl rounded-xl border border-slate-200 bg-white shadow-2xl">
        <form onSubmit={handleSubmit} className="flex max-h-[85vh] flex-col overflow-hidden">
          <header className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Edit Template Metadata</h2>
              <p className="text-sm text-slate-500">Update the template name, description, and field types.</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-500 hover:border-slate-300 hover:text-slate-700"
              disabled={isSubmitting}
            >
              Close
            </button>
          </header>

          <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
            {formError ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">{formError}</div> : null}

            <section className="space-y-3">
              <label className="block text-sm font-medium text-slate-900">Template name</label>
              <input
                type="text"
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={name}
                onChange={(event) => setName(event.target.value)}
                disabled={isSubmitting}
              />
            </section>

            <section className="space-y-3">
              <label className="block text-sm font-medium text-slate-900">Description</label>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                disabled={isSubmitting}
              />
            </section>

            <section className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Field types</h3>
                <p className="text-xs text-slate-500">Currently only string-like inputs are fully supported. Revisit when richer components are available.</p>
              </div>
              <div className="space-y-3">
                {fields.map((field) => (
                  <div key={field.name} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{field.name}</p>
                        <p className="text-xs text-slate-500">Current type: {findOptionLabel(field.type)}</p>
                      </div>
                      <div className="md:w-1/2">
                        <label className="mb-1 block text-xs font-medium text-slate-500">Choose a new type</label>
                        <select
                          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                          value={field.type}
                          disabled={isSubmitting}
                          onChange={(event) => {
                            const value = event.target.value as FieldType
                            setFields((prev) =>
                              prev.map((item) => (item.name === field.name ? { ...item, type: value } : item)),
                            )
                          }}
                        >
                          {editableTypeOptions.map((option) => (
                            <option key={option.value} value={option.value} disabled={option.disabled}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <footer className="flex items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:border-slate-300 hover:text-slate-800"
              onClick={() => {
                if (!template) {
                  return
                }
                setName(template.name)
                setDescription(template.description ?? '')
                setFields(template.fields.map((field) => ({ name: field.name, type: field.type })))
                setFormError(null)
              }}
              disabled={isSubmitting || !template}
            >
              Reset
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
              disabled={isSubmitting || isPristine}
            >
              {isSubmitting ? 'Saving...' : 'Save changes'}
            </button>
          </footer>
        </form>
      </div>
    </div>
  )
}

