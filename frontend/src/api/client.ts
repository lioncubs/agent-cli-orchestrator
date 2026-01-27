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

// Extended error type for branch switching
export interface BranchSwitchError {
  error: string;
  type: 'dirty_working_tree' | 'branch_error';
  branch: string;
}

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
        // Preserve structured error data for branch switching
        const detail = error.response?.data?.detail;
        if (detail && typeof detail === 'object') {
          const detailObj = detail as { error?: string; type?: string; branch?: string };
          const customError = new Error(detailObj.error || 'Unknown error');
          (customError as any).details = detailObj;
          throw customError;
        }
        if (detail && typeof detail === 'string') {
          throw new Error(detail);
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

  // Git status endpoint
  async getGitStatus(repoName?: string): Promise<{
    status: string;
    branch: string;
    is_clean: boolean;
    can_switch_branch: boolean;
    details: {
      modified: string[];
      staged: string[];
      untracked: string[];
      conflicts: string[];
    };
    counts: {
      modified: number;
      staged: number;
      untracked: number;
      conflicts: number;
    };
    suggestions?: string[];
  }> {
    const { data } = await this.client.get('/git/status', {
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

  async selectBranch(branch: string, repoName?: string, force: boolean = false): Promise<{
    status: string;
    branch: string;
    message: string;
    was_switch_needed?: boolean;
    previous_branch?: string;
  }> {
    const { data } = await this.client.post('/branch/select', {
      branch,
      repo_name: repoName,
      force,
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

  // Streaming endpoint (uses fetch with POST and ReadableStream)
  async createStreamingPrompt(request: PromptRequest): Promise<Response> {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    const response = await fetch(`${baseURL}/prompt/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Streaming request failed with status ${response.status}`);
    }

    return response;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
