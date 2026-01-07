import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import { formatRelativeTime } from '../lib/utils'
import { Filter } from 'lucide-react'

export default function Sessions() {
  const [searchParams, setSearchParams] = useSearchParams()
  const typeFilter = searchParams.get('type') || 'all'
  const statusFilter = searchParams.get('status') || 'all'

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions', typeFilter, statusFilter],
    queryFn: () => apiClient.getSessions({
      ...(typeFilter !== 'all' && { type: typeFilter }),
      ...(statusFilter !== 'all' && { status: statusFilter }),
    }),
  })

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Sessions</h1>

      {/* Filters */}
      <div className="bg-card border rounded-lg p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Filters:</span>
          </div>

          <select
            value={typeFilter}
            onChange={(e) => {
              const params = new URLSearchParams(searchParams)
              if (e.target.value === 'all') {
                params.delete('type')
              } else {
                params.set('type', e.target.value)
              }
              setSearchParams(params)
            }}
            className="px-3 py-1.5 border rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="query">Query</option>
            <option value="research">Research</option>
            <option value="delegation">Delegation</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => {
              const params = new URLSearchParams(searchParams)
              if (e.target.value === 'all') {
                params.delete('status')
              } else {
                params.set('status', e.target.value)
              }
              setSearchParams(params)
            }}
            className="px-3 py-1.5 border rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="committed">Committed</option>
            <option value="pr_created">PR Created</option>
          </select>
        </div>
      </div>

      {/* Sessions List */}
      <div className="bg-card border rounded-lg">
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading sessions...</div>
        ) : !sessions || sessions.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No sessions found. Adjust filters or start a new session.
          </div>
        ) : (
          <div className="divide-y">
            {sessions.map((session: any) => (
              <Link
                key={session.id}
                to={`/sessions/${session.id}`}
                className="block p-6 hover:bg-muted transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
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
                          : session.status === 'completed'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {session.status}
                      </span>
                    </div>
                    <p className="font-semibold text-lg">{session.repo_name}</p>
                    {session.base_branch && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Branch: {session.base_branch}
                        {session.session_branch && ` → ${session.session_branch}`}
                      </p>
                    )}
                    <p className="text-sm text-muted-foreground mt-1">
                      {session.turns?.length || 0} turn{session.turns?.length !== 1 ? 's' : ''}
                      {session.files_changed && ` • ${session.files_changed.length} file${session.files_changed.length !== 1 ? 's' : ''} changed`}
                    </p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {formatRelativeTime(session.last_activity_at)}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
