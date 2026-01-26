import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { GitBranch, FolderGit2, MessageSquare, Activity as ActivityIcon } from 'lucide-react';

export function Dashboard() {
  const { data: repos } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.listRepositories(),
  });

  const { data: currentBranch } = useQuery({
    queryKey: ['current-branch'],
    queryFn: () => apiClient.getCurrentBranch(),
  });

  const { data: worktrees } = useQuery({
    queryKey: ['worktrees'],
    queryFn: () => apiClient.listWorktrees(),
  });

  const { data: logs } = useQuery({
    queryKey: ['logs'],
    queryFn: () => apiClient.listLogs(10),
  });

  const stats = [
    {
      name: 'Repositories',
      value: repos?.count || 0,
      icon: FolderGit2,
      color: 'bg-blue-500',
    },
    {
      name: 'Current Branch',
      value: currentBranch?.branch || '-',
      icon: GitBranch,
      color: 'bg-green-500',
    },
    {
      name: 'Worktrees',
      value: worktrees?.count || 0,
      icon: FolderGit2,
      color: 'bg-purple-500',
    },
    {
      name: 'Recent Activities',
      value: logs?.count || 0,
      icon: ActivityIcon,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome to Agent CLI Orchestrator - Your multi-CLI orchestration system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`rounded-lg p-3 ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link
            to="/copilot"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <MessageSquare className="mr-2 h-5 w-5 text-primary-600" />
            <span className="font-medium">New Copilot Prompt</span>
          </Link>
          <Link
            to="/branches"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <GitBranch className="mr-2 h-5 w-5 text-primary-600" />
            <span className="font-medium">Switch Branch</span>
          </Link>
          <Link
            to="/repositories"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FolderGit2 className="mr-2 h-5 w-5 text-primary-600" />
            <span className="font-medium">Manage Repos</span>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        {logs?.logs && logs.logs.length > 0 ? (
          <div className="space-y-2">
            {logs.logs.slice(0, 5).map((log, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    log.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900">{log.action}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  log.status === 'success' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {log.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No recent activity</p>
        )}
      </div>
    </div>
  );
}
