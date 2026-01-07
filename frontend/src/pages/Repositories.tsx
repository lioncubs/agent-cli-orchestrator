import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { FolderGit2, ExternalLink } from 'lucide-react';

export function Repositories() {
  const { data, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.listRepositories(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Repositories</h1>
        <p className="mt-2 text-gray-600">
          Manage configured repositories
        </p>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent" />
            <p className="mt-2 text-gray-600">Loading repositories...</p>
          </div>
        ) : data?.repositories && data.repositories.length > 0 ? (
          <div className="space-y-4">
            {data.repositories.map((repo) => (
              <div
                key={repo.name}
                className="flex items-start justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start space-x-3">
                  <FolderGit2 className="h-6 w-6 text-primary-600 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {repo.name}
                      {repo.default && (
                        <span className="ml-2 px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">
                          Default
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">{repo.path}</p>
                    {repo.worktrees_path && (
                      <p className="text-xs text-gray-500 mt-1">
                        Worktrees: {repo.worktrees_path}
                      </p>
                    )}
                  </div>
                </div>
                <a
                  href={`/branches?repo=${repo.name}`}
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  View branches
                  <ExternalLink className="ml-1 h-4 w-4" />
                </a>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <FolderGit2 className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-600">No repositories configured</p>
          </div>
        )}
      </div>
    </div>
  );
}
