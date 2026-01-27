import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { GitBranch, Check, Loader2, AlertCircle, AlertTriangle, FileWarning, X } from 'lucide-react';

interface SwitchError {
  message: string;
  details?: {
    error: string;
    type: 'dirty_working_tree' | 'branch_error';
    branch: string;
  };
}

export function Branches() {
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [switchError, setSwitchError] = useState<SwitchError | null>(null);
  const [pendingBranch, setPendingBranch] = useState<string | null>(null);
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

  const { data: gitStatus } = useQuery({
    queryKey: ['git-status', selectedRepo],
    queryFn: () => apiClient.getGitStatus(selectedRepo || undefined),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const switchBranchMutation = useMutation({
    mutationFn: ({ branch, force }: { branch: string; force?: boolean }) => 
      apiClient.selectBranch(branch, selectedRepo || undefined, force),
    onSuccess: () => {
      setSwitchError(null);
      setPendingBranch(null);
      queryClient.invalidateQueries({ queryKey: ['current-branch'] });
      queryClient.invalidateQueries({ queryKey: ['branches'] });
      queryClient.invalidateQueries({ queryKey: ['git-status'] });
    },
    onError: (error: Error & { details?: any }) => {
      setSwitchError({
        message: error.message,
        details: error.details,
      });
    },
  });

  const handleSwitchBranch = (branch: string, force: boolean = false) => {
    setPendingBranch(branch);
    setSwitchError(null);
    switchBranchMutation.mutate({ branch, force });
  };

  const dismissError = () => {
    setSwitchError(null);
    setPendingBranch(null);
  };

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

      {/* Git Status Warning */}
      {gitStatus && !gitStatus.is_clean && (
        <div className="card bg-yellow-50 border-2 border-yellow-200">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-900">
                Working tree has uncommitted changes
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                Branch switching is disabled until changes are committed or stashed.
              </p>
              <div className="mt-2 text-xs text-yellow-800 space-y-1">
                {gitStatus.counts.modified > 0 && (
                  <p><FileWarning className="inline h-3 w-3 mr-1" />{gitStatus.counts.modified} modified file(s)</p>
                )}
                {gitStatus.counts.staged > 0 && (
                  <p><Check className="inline h-3 w-3 mr-1" />{gitStatus.counts.staged} staged file(s)</p>
                )}
                {gitStatus.counts.conflicts > 0 && (
                  <p><AlertCircle className="inline h-3 w-3 mr-1" />{gitStatus.counts.conflicts} conflict(s)</p>
                )}
              </div>
              {gitStatus.suggestions && gitStatus.suggestions.length > 0 && (
                <div className="mt-3 p-2 bg-yellow-100 rounded text-xs text-yellow-900">
                  <p className="font-medium">Suggestions:</p>
                  <ul className="list-disc list-inside mt-1 space-y-0.5">
                    {gitStatus.suggestions.map((suggestion, i) => (
                      <li key={i}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Switch Error Modal */}
      {switchError && (
        <div className="card bg-red-50 border-2 border-red-200">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">
                  Failed to switch to branch '{pendingBranch}'
                </p>
                <pre className="mt-2 text-xs text-red-800 whitespace-pre-wrap font-mono bg-red-100 p-3 rounded overflow-x-auto">
                  {switchError.message}
                </pre>
                {switchError.details?.type === 'dirty_working_tree' && (
                  <div className="mt-3 flex space-x-2">
                    <button
                      onClick={() => handleSwitchBranch(pendingBranch!, true)}
                      className="btn-secondary text-xs py-1 px-2 bg-red-100 hover:bg-red-200 text-red-800 border-red-300"
                    >
                      Force Switch (Discard Changes)
                    </button>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={dismissError}
              className="text-red-500 hover:text-red-700 p-1"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Current Branch */}
      {currentBranch && (
        <div className="card bg-primary-50 border-2 border-primary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <GitBranch className="h-5 w-5 text-primary-600 mr-2" />
              <p className="text-sm text-primary-900">
                Current branch: <span className="font-semibold">{currentBranch.branch}</span>
              </p>
            </div>
            {gitStatus?.is_clean && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                Clean
              </span>
            )}
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
              const canSwitch = gitStatus?.is_clean ?? true;
              const isSwitching = switchBranchMutation.isPending && pendingBranch === branch.name;
              
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
                      onClick={() => handleSwitchBranch(branch.name)}
                      disabled={switchBranchMutation.isPending || !canSwitch}
                      className={`btn-secondary text-sm py-1 px-3 disabled:opacity-50 ${
                        !canSwitch ? 'cursor-not-allowed' : ''
                      }`}
                      title={!canSwitch ? 'Commit or stash changes before switching branches' : ''}
                    >
                      {isSwitching ? 'Switching...' : 'Switch'}
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
