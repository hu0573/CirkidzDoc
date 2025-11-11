export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'enum'
  | 'file'
  | 'textarea'
  | 'richtext'

export interface FieldSchema {
  name: string
  type: FieldType
}

export interface TemplateMetadata {
  id: string
  name: string
  description?: string | null
  entry: string
  fields: FieldSchema[]
}

export interface TemplateSummary {
  id: string
  name: string
  description?: string | null
  entry: string
  field_count: number
}

export interface TemplateDetail {
  template: TemplateMetadata
}

export interface TemplateCreationResponse {
  template: TemplateMetadata
  metadata_path: string
  message: string
}

export interface OutputFormat {
  id: string
  label: string
  description?: string
}

export interface FormatsResponse {
  formats: OutputFormat[]
  advanced_options?: Record<string, unknown>
}

export type TaskStatusValue = 'queued' | 'processing' | 'succeeded' | 'failed'

export interface TaskResult {
  format: string
  download_url: string
  file_size?: number | null
  checksum?: string | null
  expires_at?: string | null
}

export interface TaskStatus {
  task_id: string
  status: TaskStatusValue
  progress: number
  results: TaskResult[]
  error?: string | null
}

export interface RenderResponse {
  task_id: string
  status: TaskStatusValue
  expires_at: string
}

export interface RenderRequestPayload {
  template_id: string
  data: Record<string, unknown>
  formats: string[]
  options?: Record<string, unknown>
}

