export interface Session {
  id: string
  type: 'query' | 'research' | 'delegation'
  status: string
  repo_name: string
  user_id: string
  created_at: string
  last_activity_at: string
  base_branch?: string
  session_branch?: string
  worktree_path?: string
  turns: Turn[]
  files_changed?: string[]
  pr_url?: string
}

export interface Turn {
  id: number
  prompt: string
  response: string
  response_summary: string
  files_analyzed: string[]
  files_changed: string[]
  timestamp: string
}

export interface Repository {
  name: string
  path: string
  platform?: string
  default_branch?: string
}

export interface ResearchArtifact {
  research_id: string
  repo_name: string
  base_branch: string
  created_at: string
  user_id: string
  summary: string
  findings: ResearchFinding[]
  recommendations: string[]
  relevant_files: string[]
}

export interface ResearchFinding {
  file: string
  lines?: string
  note: string
  code_snippet?: string
}
