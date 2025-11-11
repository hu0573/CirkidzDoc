import type { TemplateSummary } from '../lib/types'

interface TemplateListProps {
  templates?: TemplateSummary[]
  selectedId?: string | null
  onSelect: (templateId: string) => void
  isLoading?: boolean
  error?: string | null
}

export function TemplateList({ templates, selectedId, onSelect, isLoading, error }: TemplateListProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        正在加载模板列表...
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 shadow-sm">
        加载模板列表失败：{error}
      </div>
    )
  }

  if (!templates?.length) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        暂无可用模板，请先在后端导入。
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {templates.map((template) => {
        const isActive = template.id === selectedId
        return (
          <button
            key={template.id}
            type="button"
            onClick={() => onSelect(template.id)}
            className={[
              'group flex flex-col gap-3 rounded-xl border p-4 text-left transition-shadow',
              isActive
                ? 'border-blue-500 bg-blue-50 shadow-lg'
                : 'border-slate-200 bg-white hover:shadow-md',
            ].join(' ')}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{template.name}</h3>
                {template.version ? (
                  <p className="text-xs text-slate-500">版本 {template.version}</p>
                ) : null}
              </div>
              <span
                className={[
                  'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium',
                  isActive ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600',
                ].join(' ')}
              >
                {template.field_count} 个字段
              </span>
            </div>
            <p className="line-clamp-3 text-sm text-slate-600">{template.description ?? '暂无描述'}</p>
            {template.allowed_outputs.length ? (
              <div className="flex flex-wrap gap-1">
                {template.allowed_outputs.map((format) => (
                  <span
                    key={format}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-600"
                  >
                    {format}
                  </span>
                ))}
              </div>
            ) : null}
          </button>
        )
      })}
    </div>
  )
}

