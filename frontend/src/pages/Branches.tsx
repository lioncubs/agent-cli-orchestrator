import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { GitBranch, Check, Loader2 } from 'lucide-react';

export function Branches() {
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const queryClient = useQueryClient();

  const { data: repos } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.listRepositories(),
  });

  const { data: branchesData, isLoading } = useQuery({
    queryKey: ['branches', selectedRepo],
    queryFn: () => apiClient.listBranches(selectedRepo || undefined),
  });

  const { data: currentBranch } = useQuery({
    queryKey: ['current-branch', selectedRepo],
    queryFn: () => apiClient.getCurrentBranch(selectedRepo || undefined),
  });

  const switchBranchMutation = useMutation({
    mutationFn: (branch: string) => 
      apiClient.selectBranch(branch, selectedRepo || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-branch'] });
      queryClient.invalidateQueries({ queryKey: ['branches'] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Branches</h1>
        <p className="mt-2 text-gray-600">
          View and manage Git branches
        </p>
      </div>

      {/* Repository Selector */}
      {repos && repos.repositories.length > 1 && (
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Repository
          </label>
          <select
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            className="input-field max-w-md"
          >
            <option value="">Default</option>
            {repos.repositories.map((repo) => (
              <option key={repo.name} value={repo.name}>
                {repo.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Current Branch */}
      {currentBranch && (
        <div className="card bg-primary-50 border-2 border-primary-200">
          <div className="flex items-center">
            <GitBranch className="h-5 w-5 text-primary-600 mr-2" />
            <p className="text-sm text-primary-900">
              Current branch: <span className="font-semibold">{currentBranch.branch}</span>
            </p>
          </div>
        </div>
      )}

      {/* Branches List */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">
          All Branches
          {branchesData && (
            <span className="text-sm font-normal text-gray-500 ml-2">
              ({branchesData.count.local} local, {branchesData.count.remote} remote)
            </span>
          )}
        </h2>

        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-600" />
            <p className="mt-2 text-gray-600">Loading branches...</p>
          </div>
        ) : branchesData?.branches && branchesData.branches.length > 0 ? (
          <div className="space-y-2">
            {branchesData.branches.map((branch) => {
              const isCurrent = branch.name === currentBranch?.branch;
              const isLocal = branch.type === 'local';
              
              return (
                <div
                  key={branch.name}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    isCurrent ? 'bg-primary-50' : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    {isCurrent && <Check className="h-5 w-5 text-primary-600" />}
                    <div>
                      <p className={`font-medium ${isCurrent ? 'text-primary-900' : 'text-gray-900'}`}>
                        {branch.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {isLocal ? 'Local' : 'Remote'}
                      </p>
                    </div>
                  </div>
                  {isLocal && !isCurrent && (
                    <button
                      onClick={() => switchBranchMutation.mutate(branch.name)}
                      disabled={switchBranchMutation.isPending}
                      className="btn-secondary text-sm py-1 px-3 disabled:opacity-50"
                    >
                      {switchBranchMutation.isPending ? 'Switching...' : 'Switch'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <GitBranch className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-600">No branches found</p>
          </div>
        )}
      </div>
    </div>
  );
}
