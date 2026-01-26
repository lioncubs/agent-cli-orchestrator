import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { GitBranch } from 'lucide-react'

export default function Delegation() {
  const navigate = useNavigate()
  const [repoName, setRepoName] = useState('')
  const [baseBranch, setBaseBranch] = useState('')
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState('')

  const { data: repositories } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.getRepositories(),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.createSession({
      type: 'delegation',
      repo_name: repoName,
      base_branch: baseBranch || undefined,
      initial_prompt: prompt,
    }),
    onSuccess: (data) => {
      navigate(`/sessions/${data.id}`)
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create delegation')
    },
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError('')
    createMutation.mutate()
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Start Delegation</h1>
        <p className="text-muted-foreground">
          Create a new delegation session to make code changes
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive text-destructive rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="repo" className="block text-sm font-medium mb-2">
              Repository *
            </label>
            <select
              id="repo"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              required
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
            >
              <option value="">Select a repository</option>
              {repositories?.map((repo: any) => (
                <option key={repo.name} value={repo.name}>
                  {repo.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="branch" className="block text-sm font-medium mb-2">
              Base Branch (optional)
            </label>
            <input
              id="branch"
              type="text"
              value={baseBranch}
              onChange={(e) => setBaseBranch(e.target.value)}
              placeholder="main"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Leave empty to use the repository's default branch
            </p>
          </div>

          <div>
            <label htmlFor="prompt" className="block text-sm font-medium mb-2">
              Initial Prompt *
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
              rows={6}
              placeholder="Describe the changes you want to make..."
              className="w-full px-4 py-3 border rounded-lg resize-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <GitBranch className="h-5 w-5" />
              {createMutation.isPending ? 'Creating...' : 'Start Delegation'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/sessions')}
              className="px-6 py-3 border rounded-lg hover:bg-muted transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Tips for Delegations</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Be specific about the changes you want</li>
          <li>• Mention file names and locations when relevant</li>
          <li>• Break complex tasks into smaller delegations</li>
          <li>• Review changes before committing</li>
        </ul>
      </div>
    </div>
  )
}
