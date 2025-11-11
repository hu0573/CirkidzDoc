export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'enum'
  | 'file'
  | 'textarea'
  | 'richtext'

export interface FieldOption {
  label: string
  value: string
}

export interface ValidationRule {
  pattern?: string
  min_length?: number
  max_length?: number
  minimum?: number
  maximum?: number
  message?: string
}

export interface FieldSchema {
  name: string
  label: string
  type: FieldType
  required?: boolean
  description?: string | null
  placeholder?: string | null
  default?: unknown
  options?: FieldOption[]
  validation?: ValidationRule | null
}

export interface PdfOptionCapabilities {
  allow_flatten?: boolean
  allow_pdfa?: boolean
  allow_password?: boolean
}

export interface TemplateOptions {
  allowed_outputs?: string[]
  pdf?: PdfOptionCapabilities | null
}

export interface TemplateMetadata {
  id: string
  name: string
  description?: string | null
  version?: string | null
  entry: string
  preview?: string | null
  fields: FieldSchema[]
  options?: TemplateOptions | null
}

export interface TemplateSummary {
  id: string
  name: string
  description?: string | null
  version?: string | null
  preview?: string | null
  field_count: number
  allowed_outputs: string[]
}

export interface TemplateDetail {
  template: TemplateMetadata
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

