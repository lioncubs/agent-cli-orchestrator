// API Types
export interface Repository {
  name: string;
  path: string;
  default: boolean;
  worktrees_path?: string;
}

export interface Branch {
  name: string;
  type: 'local' | 'remote';
  current?: boolean;
}

export interface Worktree {
  path: string;
  branch: string;
  head?: string;
  bare?: boolean;
  detached?: boolean;
}

export interface CopilotSession {
  session_id: string;
  created_at: string;
  last_used_at?: string;
  prompt_count: number;
}

export interface ActivityLog {
  timestamp: string;
  action: string;
  status: string;
  payload: Record<string, any>;
  result: Record<string, any>;
}

export interface PromptRequest {
  prompt: string;
  options?: {
    branch?: string;
    worktree?: string;
    session_id?: string;
  };
  repo_name?: string;
  show_full_output?: boolean;
}

export interface PromptResponse {
  status: string;
  output?: any;
  prompt: string;
  log_file?: string;
  full_stdout?: string;
  full_stderr?: string;
}

export interface StreamEvent {
  type: 'start' | 'stdout' | 'stderr' | 'complete' | 'error';
  data?: string;
  message?: string;
}

export interface ApiError {
  detail: string;
}

export interface SecuritySummary {
  status: string;
  summary: {
    total_events: number;
    by_event_type: Record<string, number>;
    by_severity: Record<string, number>;
    recent_critical_or_errors: ActivityLog[];
  };
  security_features: {
    password_hashing: string;
    api_key_hashing: string;
    rate_limiting: string;
    security_headers: string;
    cors: string;
    input_validation: string;
    audit_logging: string;
  };
}
