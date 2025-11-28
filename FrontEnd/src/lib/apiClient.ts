import axios, { AxiosError } from 'axios'

export class ApiError extends Error {
  status?: number
  payload?: unknown

  constructor(message: string, status?: number, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

/**
 * Get the backend API base URL.
 * Priority:
 * 1. VITE_API_BASE_URL environment variable
 * 2. Fixed port 8001 on the same hostname
 */
function getDefaultBaseUrl(): string {
  // Use environment variable if set
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // Use current page hostname with fixed port 8001
  const hostname = window.location.hostname
  const protocol = window.location.protocol
  
  return `${protocol}//${hostname}:8001/api`
}

const defaultBaseUrl = getDefaultBaseUrl()

export const apiClient = axios.create({
  baseURL: defaultBaseUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const message =
        (error.response.data as { detail?: string })?.detail ??
        error.message ??
        'API call failed.'
      return Promise.reject(new ApiError(message, error.response.status, error.response.data))
    }

    if (error.request) {
      return Promise.reject(new ApiError('Unable to reach the backend service. Please check your network or service status.'))
    }

    return Promise.reject(new ApiError(error.message))
  },
)

export async function downloadFile(
  url: string,
  fallbackFilename: string,
): Promise<void> {
  const requestUrl = resolveRequestUrl(url)
  const response = await apiClient.get<ArrayBuffer>(requestUrl, {
    responseType: 'blob',
    baseURL: undefined,
  })

  const blob = new Blob([response.data])
  let filename = fallbackFilename

  const contentDisposition = response.headers['content-disposition']
  if (contentDisposition) {
    const match = /filename\*?=(?:UTF-8''|")?([^;"']+)/i.exec(contentDisposition)
    if (match && match[1]) {
      filename = decodeURIComponent(match[1].replace(/"/g, ''))
    }
  }

  const link = document.createElement('a')
  const href = window.URL.createObjectURL(blob)
  link.href = href
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(href)
}

function resolveRequestUrl(target: string): string {
  if (/^https?:\/\//i.test(target)) {
    return target
  }

  const base = apiClient.defaults.baseURL ?? defaultBaseUrl
  try {
    const baseUrl = new URL(base, window.location.origin)
    if (target.startsWith('/')) {
      return `${baseUrl.protocol}//${baseUrl.host}${target}`
    }
    return new URL(target, baseUrl).toString()
  } catch {
    return target
  }
}

