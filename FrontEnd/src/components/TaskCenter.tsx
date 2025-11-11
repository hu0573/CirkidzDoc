import type { TaskResult, TaskStatus } from '../lib/types'

interface TaskCenterProps {
  activeTask?: TaskStatus
  history: TaskStatus[]
  isPolling?: boolean
  onDownload: (result: TaskResult, task: TaskStatus) => Promise<void> | void
  onRetry: (task: TaskStatus) => Promise<void> | void
  onClear?: () => void
  error?: string | null
}

const statusColors: Record<
  TaskStatus['status'],
  { text: string; bg: string; border: string; label: string }
> = {
  queued: {
    text: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    label: '排队中',
  },
  processing: {
    text: 'text-blue-700',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    label: '处理中',
  },
  succeeded: {
    text: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    label: '已完成',
  },
  failed: {
    text: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    label: '已失败',
  },
}

function StatusTag({ status }: { status: TaskStatus['status'] }) {
  const palette = statusColors[status]
  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        palette.text,
        palette.bg,
        palette.border,
      ].join(' ')}
    >
      {palette.label}
    </span>
  )
}

function formatFileSize(size?: number | null) {
  if (!size) return null
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(2)} MB`
}

export function TaskCenter({
  activeTask,
  history,
  isPolling,
  onDownload,
  onRetry,
  onClear,
  error,
}: TaskCenterProps) {
  return (
    <div className="flex h-full flex-col gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">任务状态与下载</h3>
          <p className="text-xs text-slate-500">查看最近的任务执行情况，下载结果或发起重试。</p>
        </div>
        {onClear ? (
          <button
            type="button"
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-500 hover:border-slate-300 hover:text-slate-700"
            onClick={onClear}
          >
            清空历史
          </button>
        ) : null}
      </header>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">{error}</div>
      ) : null}

      <section className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-800">当前任务</h4>
        {activeTask ? (
          <div className="space-y-3 rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-800">任务 ID：{activeTask.task_id}</p>
                <p className="text-xs text-slate-500">实时刷新 {isPolling ? '中...' : ''}</p>
              </div>
              <StatusTag status={activeTask.status} />
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={[
                  'h-full rounded-full transition-all',
                  activeTask.status === 'succeeded'
                    ? 'bg-emerald-500'
                    : activeTask.status === 'failed'
                      ? 'bg-red-500'
                      : 'bg-blue-500',
                ].join(' ')}
                style={{ width: `${Math.max(activeTask.progress, activeTask.status === 'succeeded' ? 100 : 10)}%` }}
              />
            </div>
            {activeTask.error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                {activeTask.error}
              </div>
            ) : null}
            {activeTask.status === 'failed' ? (
              <div className="flex items-center justify-end">
                <button
                  type="button"
                  className="rounded-lg border border-blue-500 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50"
                  onClick={() => void onRetry(activeTask)}
                >
                  重试任务
                </button>
              </div>
            ) : null}
            {activeTask.status === 'succeeded' ? (
              <div className="space-y-2">
                <h5 className="text-sm font-semibold text-slate-700">生成文件</h5>
                <ul className="space-y-2">
                  {activeTask.results.map((result) => (
                    <li
                      key={`${activeTask.task_id}-${result.format}`}
                      className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    >
                      <div className="flex flex-col">
                        <span className="font-medium text-slate-800">
                          {result.format.toUpperCase()}
                          {result.expires_at ? (
                            <span className="ml-2 text-xs text-slate-400">
                              过期时间：{new Date(result.expires_at).toLocaleString()}
                            </span>
                          ) : null}
                        </span>
                        {result.file_size ? (
                          <span className="text-xs text-slate-500">
                            文件大小：{formatFileSize(result.file_size)}
                          </span>
                        ) : null}
                        {result.checksum ? (
                          <span className="text-[11px] text-slate-400">校验码：{result.checksum}</span>
                        ) : null}
                      </div>
                      <button
                        type="button"
                        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500"
                        onClick={() => void onDownload(result, activeTask)}
                      >
                        下载
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">
            暂无正在运行的任务
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-800">历史记录</h4>
        {history.length ? (
          <ul className="space-y-3">
            {history.map((task) => (
              <li key={task.task_id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-slate-800">任务 ID：{task.task_id}</span>
                    <span className="text-xs text-slate-500">
                      状态：{statusColors[task.status].label} · 进度 {task.progress}%
                    </span>
                    {task.error ? (
                      <span className="text-xs text-red-600">错误：{task.error}</span>
                    ) : null}
                  </div>
                  <StatusTag status={task.status} />
                </div>
                {task.results.length ? (
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {task.results.map((result) => (
                      <li key={`${task.task_id}-${result.format}`}>
                        <button
                          type="button"
                          className="rounded-lg border border-blue-400 px-3 py-1.5 text-xs font-semibold text-blue-600 hover:bg-blue-50"
                          onClick={() => void onDownload(result, task)}
                        >
                          下载 {result.format.toUpperCase()}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-xs text-slate-500">尚未生成文件。</p>
                )}
                {task.status === 'failed' ? (
                  <div className="mt-3 flex justify-end">
                    <button
                      type="button"
                      className="rounded-lg border border-blue-500 px-3 py-1.5 text-xs font-semibold text-blue-600 hover:bg-blue-50"
                      onClick={() => void onRetry(task)}
                    >
                      重试
                    </button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">
            尚无历史记录。
          </div>
        )}
      </section>
    </div>
  )
}

