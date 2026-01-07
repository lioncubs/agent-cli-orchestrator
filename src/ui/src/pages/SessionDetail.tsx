import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { formatDate } from '../lib/utils'
import { ArrowLeft, GitCommit, Trash2 } from 'lucide-react'
import { useState } from 'react'

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [continuePrompt, setContinuePrompt] = useState('')

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', id],
    queryFn: () => apiClient.getSession(id!),
    enabled: !!id,
  })

  const continueMutation = useMutation({
    mutationFn: (prompt: string) => apiClient.continueSession(id!, prompt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session', id] })
      setContinuePrompt('')
    },
  })

  const commitMutation = useMutation({
    mutationFn: () => apiClient.commitSession(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session', id] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteSession(id!),
    onSuccess: () => {
      navigate('/sessions')
    },
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading session...</div>
  }

  if (!session) {
    return <div className="text-center py-12">Session not found</div>
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/sessions')}
          className="p-2 hover:bg-muted rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-3xl font-bold">Session Details</h1>
      </div>

      {/* Session Info */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                session.type === 'delegation' 
                  ? 'bg-blue-100 text-blue-700'
                  : session.type === 'research'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {session.type}
              </span>
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                session.status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {session.status}
              </span>
            </div>
            <h2 className="text-xl font-semibold">{session.repo_name}</h2>
            {session.base_branch && (
              <p className="text-sm text-muted-foreground mt-1">
                Branch: {session.base_branch}
                {session.session_branch && ` → ${session.session_branch}`}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            {session.type === 'delegation' && session.status === 'active' && (
              <>
                <button
                  onClick={() => commitMutation.mutate()}
                  disabled={commitMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  <GitCommit className="h-4 w-4" />
                  Commit Changes
                </button>
              </>
            )}
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="p-2 hover:bg-destructive hover:text-destructive-foreground rounded-lg transition-colors"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="text-sm text-muted-foreground space-y-1">
          <p>Created: {formatDate(session.created_at)}</p>
          <p>Last Activity: {formatDate(session.last_activity_at)}</p>
          {session.files_changed && session.files_changed.length > 0 && (
            <p>Files Changed: {session.files_changed.length}</p>
          )}
        </div>
      </div>

      {/* Conversation */}
      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Conversation</h2>
        {session.turns && session.turns.length > 0 ? (
          <div className="space-y-4">
            {session.turns.map((turn: any) => (
              <div key={turn.id} className="border-l-4 border-primary pl-4 py-2">
                <p className="font-medium mb-2">Prompt:</p>
                <p className="text-sm mb-3">{turn.prompt}</p>
                <p className="font-medium mb-2">Response:</p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{turn.response_summary || turn.response}</p>
                <p className="text-xs text-muted-foreground mt-2">{formatDate(turn.timestamp)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No conversation yet</p>
        )}

        {/* Continue Session */}
        {session.status === 'active' && (
          <div className="mt-6">
            <textarea
              value={continuePrompt}
              onChange={(e) => setContinuePrompt(e.target.value)}
              placeholder="Continue the conversation..."
              className="w-full px-4 py-3 border rounded-lg resize-none focus:ring-2 focus:ring-primary"
              rows={3}
            />
            <button
              onClick={() => continueMutation.mutate(continuePrompt)}
              disabled={!continuePrompt.trim() || continueMutation.isPending}
              className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {continueMutation.isPending ? 'Sending...' : 'Send'}
            </button>
          </div>
        )}
      </div>

      {/* Files Changed */}
      {session.files_changed && session.files_changed.length > 0 && (
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Files Changed</h2>
          <ul className="space-y-2">
            {session.files_changed.map((file: string, index: number) => (
              <li key={index} className="text-sm font-mono bg-muted px-3 py-2 rounded">
                {file}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
