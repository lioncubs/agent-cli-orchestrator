import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
  Repository,
  Branch,
  Worktree,
  CopilotSession,
  ActivityLog,
  PromptRequest,
  PromptResponse,
  SecuritySummary,
  ApiError
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.data?.detail) {
          throw new Error(error.response.data.detail);
        }
        throw error;
      }
    );
  }

  // Repository endpoints
  async listRepositories(): Promise<{ repositories: Repository[]; count: number }> {
    const { data } = await this.client.get('/repos');
    return data;
  }

  async getRepository(repoName?: string): Promise<{ repository: string; configured_name: string; path: string }> {
    const { data } = await this.client.get('/repo', {
      params: { repo_name: repoName },
    });
    return data;
  }

  // Branch endpoints
  async getCurrentBranch(repoName?: string): Promise<{ branch: string; repository: string }> {
    const { data } = await this.client.get('/branch/current', {
      params: { repo_name: repoName },
    });
    return data;
  }

  async listBranches(repoName?: string): Promise<{ branches: Branch[]; count: { total: number; local: number; remote: number } }> {
    const { data } = await this.client.get('/branches', {
      params: { repo_name: repoName },
    });
    return data;
  }

  async selectBranch(branch: string, repoName?: string): Promise<any> {
    const { data } = await this.client.post('/branch/select', {
      branch,
      repo_name: repoName,
    });
    return data;
  }

  // Worktree endpoints
  async listWorktrees(repoName?: string): Promise<{ worktrees: Worktree[]; count: number }> {
    const { data } = await this.client.get('/worktrees', {
      params: { repo_name: repoName },
    });
    return data;
  }

  async createWorktree(path: string, branch: string, createBranch = false, repoName?: string): Promise<any> {
    const { data } = await this.client.post('/worktree/create', {
      path,
      branch,
      create_branch: createBranch,
      repo_name: repoName,
    });
    return data;
  }

  // Copilot endpoints
  async executePrompt(request: PromptRequest): Promise<PromptResponse> {
    const { data } = await this.client.post('/prompt', request);
    return data;
  }

  async executePromptAsync(request: PromptRequest): Promise<PromptResponse> {
    const { data } = await this.client.post('/prompt/async', request);
    return data;
  }

  async listCopilotSessions(): Promise<{ sessions: CopilotSession[]; count: number }> {
    const { data } = await this.client.get('/copilot/sessions');
    return data;
  }

  // Activity logs
  async listLogs(limit?: number): Promise<{ logs: ActivityLog[]; count: number }> {
    const { data } = await this.client.get('/logs', {
      params: { limit },
    });
    return data;
  }

  async listCopilotLogs(limit = 20): Promise<{ logs: any[]; count: number; total_files: number }> {
    const { data } = await this.client.get('/logs/copilot', {
      params: { limit },
    });
    return data;
  }

  // Security
  async getSecuritySummary(): Promise<SecuritySummary> {
    const { data } = await this.client.get('/security/summary');
    return data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const { data } = await this.client.get('/health');
    return data;
  }

  // Streaming endpoint (returns EventSource for SSE)
  createStreamingPrompt(request: PromptRequest): EventSource {
    const params = new URLSearchParams();
    Object.entries(request).forEach(([key, value]) => {
      params.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
    });
    
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return new EventSource(`${baseURL}/prompt/stream?${params.toString()}`);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
