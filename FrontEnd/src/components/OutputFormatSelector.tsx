import type { OutputFormat } from '../lib/types'

interface OutputFormatSelectorProps {
  formats: string[]
  selected: string[]
  onChange: (next: string[]) => void
  formatCatalog?: OutputFormat[]
  disabled?: boolean
  error?: string | null
}

function resolveLabel(id: string, catalog?: OutputFormat[]) {
  const match = catalog?.find((item) => item.id === id)
  return {
    label: match?.label ?? id.toUpperCase(),
    description: match?.description ?? '',
  }
}

export function OutputFormatSelector({
  formats,
  selected,
  onChange,
  formatCatalog,
  disabled,
  error,
}: OutputFormatSelectorProps) {
  const toggle = (formatId: string) => {
    if (selected.includes(formatId)) {
      onChange(selected.filter((item) => item !== formatId))
    } else {
      onChange([...selected, formatId])
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {formats.map((formatId) => {
          const { label, description } = resolveLabel(formatId, formatCatalog)
          const isChecked = selected.includes(formatId)
          return (
            <label
              key={formatId}
              className={[
                'flex cursor-pointer flex-col gap-1 rounded-lg border px-3 py-2 transition',
                isChecked ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-400',
                disabled ? 'cursor-not-allowed opacity-60' : '',
              ].join(' ')}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    checked={isChecked}
                    onChange={() => toggle(formatId)}
                    disabled={disabled}
                  />
                  <span className="text-sm font-semibold text-slate-900">{label}</span>
                </div>
                <span className="text-xs uppercase tracking-wide text-slate-500">{formatId}</span>
              </div>
              {description ? <p className="text-xs text-slate-500">{description}</p> : null}
            </label>
          )
        })}
      </div>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  )
}


