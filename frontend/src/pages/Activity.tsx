import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Activity as ActivityIcon, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export function Activity() {
  const [limit, setLimit] = useState(50);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['logs', limit],
    queryFn: () => apiClient.listLogs(limit),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Activity Log</h1>
          <p className="mt-2 text-gray-600">
            View recent system activities and operations
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="btn-secondary flex items-center"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Show entries
        </label>
        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="input-field max-w-xs"
        >
          <option value={10}>Last 10</option>
          <option value={50}>Last 50</option>
          <option value={100}>Last 100</option>
          <option value={200}>Last 200</option>
        </select>
      </div>

      {/* Activity List */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">
          Recent Activities
          {data && <span className="text-sm font-normal text-gray-500 ml-2">({data.count} total)</span>}
        </h2>

        {isLoading ? (
          <div className="text-center py-12">
            <ActivityIcon className="mx-auto h-8 w-8 animate-pulse text-primary-600" />
            <p className="mt-2 text-gray-600">Loading activities...</p>
          </div>
        ) : data?.logs && data.logs.length > 0 ? (
          <div className="space-y-2">
            {data.logs.map((log, idx) => (
              <div
                key={idx}
                className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      log.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{log.action}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          log.status === 'success' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {log.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                      
                      {/* Payload */}
                      {Object.keys(log.payload).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-900">
                            View details
                          </summary>
                          <pre className="mt-2 p-2 bg-gray-900 text-gray-100 text-xs rounded overflow-x-auto">
                            {JSON.stringify({ payload: log.payload, result: log.result }, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <ActivityIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-600">No activities recorded</p>
          </div>
        )}
      </div>
    </div>
  );
}
