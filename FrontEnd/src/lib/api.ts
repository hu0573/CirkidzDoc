import { apiClient } from './apiClient'
import type {
  FormatsResponse,
  RenderRequestPayload,
  RenderResponse,
  TaskStatus,
  TemplateDetail,
  TemplateSummary,
} from './types'

export async function fetchTemplates(): Promise<TemplateSummary[]> {
  const response = await apiClient.get<TemplateSummary[]>('/templates')
  return response.data
}

export async function fetchTemplateDetail(templateId: string): Promise<TemplateDetail> {
  const response = await apiClient.get<TemplateDetail>(`/templates/${templateId}`)
  return response.data
}

export async function fetchFormats(): Promise<FormatsResponse> {
  const response = await apiClient.get<FormatsResponse>('/formats')
  return response.data
}

export async function submitRenderTask(payload: RenderRequestPayload): Promise<RenderResponse> {
  const response = await apiClient.post<RenderResponse>('/templates/render', payload)
  return response.data
}

export async function fetchTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await apiClient.get<TaskStatus>(`/templates/tasks/${taskId}`)
  return response.data
}

