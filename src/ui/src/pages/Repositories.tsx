import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { FolderGit2 } from 'lucide-react'

export default function Repositories() {
  const { data: repositories, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.getRepositories(),
  })

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Repositories</h1>

      <div className="bg-card border rounded-lg">
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading repositories...</div>
        ) : !repositories || repositories.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No repositories configured. Add repositories in your config.yaml file.
          </div>
        ) : (
          <div className="divide-y">
            {repositories.map((repo: any) => (
              <div key={repo.name} className="p-6">
                <div className="flex items-start gap-4">
                  <FolderGit2 className="h-6 w-6 text-primary flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{repo.name}</h3>
                    {repo.path && (
                      <p className="text-sm text-muted-foreground font-mono mt-1">{repo.path}</p>
                    )}
                    <div className="flex gap-4 mt-2 text-sm">
                      {repo.default_branch && (
                        <span className="text-muted-foreground">
                          Default Branch: <span className="font-medium">{repo.default_branch}</span>
                        </span>
                      )}
                      {repo.platform && (
                        <span className="text-muted-foreground">
                          Platform: <span className="font-medium">{repo.platform}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
