import { useAuthStore } from '../store/authStore'

const API_BASE = '/api'

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = useAuthStore.getState().token
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || 'Request failed')
    }

    return response.json()
  }

  // Authentication
  async login(email: string, password: string) {
    return this.request<{ user: any; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email: string, password: string, display_name: string) {
    return this.request<{ user: any; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name }),
    })
  }

  async getMe() {
    return this.request<any>('/auth/me')
  }

  // Sessions
  async getSessions(filters?: any) {
    const params = new URLSearchParams(filters)
    return this.request<any[]>(`/sessions?${params}`)
  }

  async getSession(id: string) {
    return this.request<any>(`/sessions/${id}`)
  }

  async createSession(data: any) {
    return this.request<any>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async continueSession(id: string, prompt: string) {
    return this.request<any>(`/sessions/${id}/continue`, {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    })
  }

  async commitSession(id: string, message?: string) {
    return this.request<any>(`/sessions/${id}/commit`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  }

  async createPR(id: string, title: string, body: string, draft: boolean = false) {
    return this.request<any>(`/sessions/${id}/pr`, {
      method: 'POST',
      body: JSON.stringify({ title, body, draft }),
    })
  }

  async deleteSession(id: string) {
    return this.request<void>(`/sessions/${id}`, {
      method: 'DELETE',
    })
  }

  // Repositories
  async getRepositories() {
    return this.request<any[]>('/repos')
  }

  async getRepository(name: string) {
    return this.request<any>(`/repos/${name}`)
  }

  // Research
  async getResearch(filters?: any) {
    const params = new URLSearchParams(filters)
    return this.request<any[]>(`/research?${params}`)
  }

  async getResearchArtifact(id: string) {
    return this.request<any>(`/research/${id}`)
  }

  async deleteResearch(id: string) {
    return this.request<void>(`/research/${id}`, {
      method: 'DELETE',
    })
  }

  // Query
  async executeQuery(repo_name: string, prompt: string) {
    return this.request<any>('/query', {
      method: 'POST',
      body: JSON.stringify({ repo_name, prompt }),
    })
  }
}

export const apiClient = new ApiClient()
