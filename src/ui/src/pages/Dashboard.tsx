import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import { formatRelativeTime } from '../lib/utils'
import { Activity, GitBranch, FileSearch, List as ListIcon } from 'lucide-react'

export default function Dashboard() {
  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions', 'recent'],
    queryFn: () => apiClient.getSessions({ limit: 5 }),
  })

  const { data: repositories } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.getRepositories(),
  })

  const activeSessions = sessions?.filter((s: any) => s.status === 'active') || []
  const recentSessions = sessions || []

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link
          to="/delegate"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:opacity-90 transition-opacity font-medium"
        >
          New Delegation
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Sessions</p>
              <p className="text-3xl font-bold mt-1">{activeSessions.length}</p>
            </div>
            <Activity className="h-8 w-8 text-primary" />
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Repositories</p>
              <p className="text-3xl font-bold mt-1">{repositories?.length || 0}</p>
            </div>
            <GitBranch className="h-8 w-8 text-primary" />
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Sessions</p>
              <p className="text-3xl font-bold mt-1">{sessions?.length || 0}</p>
            </div>
            <ListIcon className="h-8 w-8 text-primary" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/delegate"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-muted transition-colors"
          >
            <GitBranch className="h-6 w-6 text-primary" />
            <div>
              <p className="font-medium">Start Delegation</p>
              <p className="text-sm text-muted-foreground">Begin code changes</p>
            </div>
          </Link>

          <Link
            to="/sessions?type=research"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-muted transition-colors"
          >
            <FileSearch className="h-6 w-6 text-primary" />
            <div>
              <p className="font-medium">Start Research</p>
              <p className="text-sm text-muted-foreground">Analyze codebase</p>
            </div>
          </Link>

          <Link
            to="/sessions"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-muted transition-colors"
          >
            <ListIcon className="h-6 w-6 text-primary" />
            <div>
              <p className="font-medium">View Sessions</p>
              <p className="text-sm text-muted-foreground">See all activity</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Sessions</h2>
          <Link to="/sessions" className="text-sm text-primary hover:underline">
            View all
          </Link>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading sessions...</div>
        ) : recentSessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No sessions yet. Start a new delegation or research session to get started.
          </div>
        ) : (
          <div className="space-y-3">
            {recentSessions.map((session: any) => (
              <Link
                key={session.id}
                to={`/sessions/${session.id}`}
                className="block p-4 border rounded-lg hover:bg-muted transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
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
                    <p className="font-medium mt-2">{session.repo_name}</p>
                    {session.base_branch && (
                      <p className="text-sm text-muted-foreground">Branch: {session.base_branch}</p>
                    )}
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
