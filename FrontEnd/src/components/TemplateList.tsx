import type { TemplateSummary } from '../lib/types'

interface TemplateListProps {
  templates?: TemplateSummary[]
  selectedId?: string | null
  onSelect: (templateId: string) => void
  onEdit?: (templateId: string) => void
  onDelete?: (templateId: string, templateName: string) => void
  deletingId?: string | null
  isLoading?: boolean
  error?: string | null
}

export function TemplateList({
  templates,
  selectedId,
  onSelect,
  onEdit,
  onDelete,
  deletingId,
  isLoading,
  error,
}: TemplateListProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        Loading template list...
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 shadow-sm">
        Failed to load template list: {error}
      </div>
    )
  }

  if (!templates?.length) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        No templates available. Please import them in the backend first.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {templates.map((template) => {
        const isActive = template.id === selectedId
        const handleActivate = () => onSelect(template.id)
        const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            handleActivate()
          }
        }
        return (
          <div
            key={template.id}
            className={[
              'group flex flex-col gap-3 rounded-xl border p-4 text-left transition-shadow',
              isActive
                ? 'border-blue-500 bg-blue-50 shadow-lg'
                : 'border-slate-200 bg-white hover:shadow-md',
            ].join(' ')}
            role="button"
            tabIndex={0}
            onClick={handleActivate}
            onKeyDown={handleKeyDown}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{template.name}</h3>
                <p className="text-xs text-slate-500">{template.entry}</p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={[
                    'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium',
                    isActive ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600',
                  ].join(' ')}
                >
                  {template.field_count} fields
                </span>
                {onEdit ? (
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation()
                      onEdit(template.id)
                    }}
                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-blue-400 hover:text-blue-600"
                    aria-label="Edit template metadata"
                    title="Edit template"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="h-4 w-4"
                    >
                      <path d="M13.586 3.586a2 2 0 0 1 2.828 2.828l-.587.586-2.828-2.828.587-.586zM12.172 5 4 13.172V16h2.828L15 7.828 12.172 5z" />
                    </svg>
                  </button>
                ) : null}
                {onDelete ? (
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation()
                      onDelete(template.id, template.name)
                    }}
                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-red-400 hover:text-red-600"
                    aria-label="Delete template"
                    title="Delete template"
                    disabled={deletingId === template.id}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="h-4 w-4"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8.5 2a1.5 1.5 0 0 0-1.415 1H5a.75.75 0 0 0 0 1.5h10a.75.75 0 0 0 0-1.5h-2.085A1.5 1.5 0 0 0 11.5 2h-3zm-3 4.5a.5.5 0 0 1 .5.5v8.25A1.75 1.75 0 0 0 7.75 17h4.5A1.75 1.75 0 0 0 14 15.25V7a.5.5 0 0 1 1 0v8.25A3.25 3.25 0 0 1 11.75 18.5h-4.5A3.25 3.25 0 0 1 4 15.25V7a.5.5 0 0 1 .5-.5zm4 0a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-1 0v-8a.5.5 0 0 1 .5-.5zm2.5.5a.5.5 0 0 1 1 0v8a.5.5 0 0 1-1 0v-8z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                ) : null}
              </div>
            </div>
            <p className="line-clamp-3 text-sm text-slate-600">
              {template.description ?? 'No description available.'}
            </p>
          </div>
        )
      })}
    </div>
  )
}

