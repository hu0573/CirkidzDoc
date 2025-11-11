import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { TemplateDetailPanel } from './components/TemplateDetailPanel'
import { TemplateList } from './components/TemplateList'
import { TaskCenter } from './components/TaskCenter'
import { downloadFile, ApiError } from './lib/apiClient'
import {
  fetchFormats,
  fetchTaskStatus,
  fetchTemplateDetail,
  fetchTemplates,
  submitRenderTask,
} from './lib/api'
import type { RenderRequestPayload, TaskStatus, TemplateDetail } from './lib/types'
import './App.css'

type TaskMap = Record<string, RenderRequestPayload>

function pickErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return '发生未知错误，请稍后重试。'
}

function useTaskPolling(taskId: string | null) {
  return useQuery({
    queryKey: ['taskStatus', taskId],
    queryFn: () => fetchTaskStatus(taskId!),
    enabled: Boolean(taskId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 2000
      if (data.status === 'succeeded' || data.status === 'failed') return false
      return 2000
    },
    refetchIntervalInBackground: true,
  })
}

function App() {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [taskHistory, setTaskHistory] = useState<TaskStatus[]>([])
  const [taskPayloadMap, setTaskPayloadMap] = useState<TaskMap>({})
  const [uiError, setUiError] = useState<string | null>(null)

  const templatesQuery = useQuery({
    queryKey: ['templates'],
    queryFn: fetchTemplates,
  })

  const formatsQuery = useQuery({
    queryKey: ['formats'],
    queryFn: fetchFormats,
  })

  const templateDetailQuery = useQuery({
    queryKey: ['template', selectedTemplateId],
    queryFn: () => fetchTemplateDetail(selectedTemplateId!),
    enabled: Boolean(selectedTemplateId),
  })

  const taskStatusQuery = useTaskPolling(activeTaskId)

  const renderMutation = useMutation({
    mutationFn: submitRenderTask,
    onMutate: () => {
      setUiError(null)
    },
    onSuccess: (response, variables) => {
      setActiveTaskId(response.task_id)
      setTaskPayloadMap((prev) => ({
        ...prev,
        [response.task_id]: variables,
      }))
      setTaskHistory((prev) => prev.filter((item) => item.task_id !== response.task_id))
    },
    onError: (error: unknown) => {
      setUiError(pickErrorMessage(error))
    },
  })

  useEffect(() => {
    if (!templatesQuery.data?.length || selectedTemplateId) {
      return
    }
    setSelectedTemplateId(templatesQuery.data[0].id)
  }, [templatesQuery.data, selectedTemplateId])

  useEffect(() => {
    if (!taskStatusQuery.data) {
      return
    }
    const current = taskStatusQuery.data
    if (current.status === 'succeeded' || current.status === 'failed') {
      setTaskHistory((prev) => {
        const filtered = prev.filter((task) => task.task_id !== current.task_id)
        return [current, ...filtered].slice(0, 10)
      })
      if (current.status === 'failed' && current.error) {
        setUiError(current.error)
      }
    }
  }, [taskStatusQuery.data])

  const handleRender = async (payload: RenderRequestPayload) => {
    await renderMutation.mutateAsync(payload)
  }

  const handleDownload = async (result: TaskStatus['results'][number], task: TaskStatus) => {
    try {
      await downloadFile(result.download_url, `${task.task_id}.${result.format}`)
    } catch (error) {
      setUiError(pickErrorMessage(error))
    }
  }

  const handleRetry = async (task: TaskStatus) => {
    const payload = taskPayloadMap[task.task_id]
    if (!payload) {
      setUiError('未找到原始任务参数，请重新填写表单后重试。')
      return
    }
    await renderMutation.mutateAsync(payload)
  }

  const resetHistory = () => {
    setTaskHistory([])
    setUiError(null)
  }

  const templates = templatesQuery.data ?? []
  const templateDetail: TemplateDetail | undefined = templateDetailQuery.data
  const formats = formatsQuery.data?.formats ?? []

  const isSubmitting = renderMutation.isPending
  const isPolling = taskStatusQuery.isFetching
  const activeTask = taskStatusQuery.data

  const templateLoadError = templatesQuery.error ? pickErrorMessage(templatesQuery.error) : null
  const templateDetailError = templateDetailQuery.error
    ? pickErrorMessage(templateDetailQuery.error)
    : null

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">文档模板填充控制台</h1>
            <p className="text-sm text-slate-500">
              选择模板、填写字段并提交渲染任务，支持多格式输出与结果下载。
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>后端 API 地址</span>
            <code className="rounded bg-slate-100 px-2 py-1">
              {import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'}
            </code>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        {uiError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">{uiError}</div>
        ) : null}

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-[2.2fr,3fr]">
          <div className="flex flex-col gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-base font-semibold text-slate-900">模板列表</h2>
              <TemplateList
                templates={templates}
                selectedId={selectedTemplateId}
                onSelect={(id) => {
                  setSelectedTemplateId(id)
                  setUiError(null)
                }}
                isLoading={templatesQuery.isLoading}
                error={templatesQuery.error ? templateLoadError : null}
              />
            </div>
            {templateDetailError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                模板详情加载失败：{templateDetailError}
              </div>
            ) : null}
          </div>
          <TemplateDetailPanel
            template={templateDetail}
            onSubmit={handleRender}
            isSubmitting={isSubmitting}
            formatCatalog={formats}
          />
        </section>

        <TaskCenter
          activeTask={activeTask}
          history={taskHistory}
          isPolling={isPolling}
          onDownload={handleDownload}
          onRetry={handleRetry}
          onClear={resetHistory}
        />
      </main>
    </div>
  )
}

export default App
