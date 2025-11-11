import { apiClient } from './apiClient'
import type {
  FormatsResponse,
  RenderRequestPayload,
  RenderResponse,
  TaskStatus,
  TemplateCreationResponse,
  TemplateDetail,
  TemplateSummary,
  TemplateUpdateRequest,
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

export async function uploadTemplate(file: File): Promise<TemplateCreationResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<TemplateCreationResponse>('/templates/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

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

export async function updateTemplateMetadata(
  templateId: string,
  payload: TemplateUpdateRequest,
): Promise<TemplateDetail> {
  const response = await apiClient.patch<TemplateDetail>(`/templates/${templateId}`, payload)
  return response.data
}

export async function deleteTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`/templates/${templateId}`)
}

