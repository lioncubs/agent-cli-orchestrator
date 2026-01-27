import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Shield, CheckCircle2, AlertCircle } from 'lucide-react';

export function Security() {
  const { data, isLoading } = useQuery({
    queryKey: ['security-summary'],
    queryFn: () => apiClient.getSecuritySummary(),
  });

  const features = data?.security_features ? [
    { name: 'Password Hashing', value: data.security_features.password_hashing },
    { name: 'API Key Hashing', value: data.security_features.api_key_hashing },
    { name: 'Rate Limiting', value: data.security_features.rate_limiting },
    { name: 'Security Headers', value: data.security_features.security_headers },
    { name: 'CORS', value: data.security_features.cors },
    { name: 'Input Validation', value: data.security_features.input_validation },
    { name: 'Audit Logging', value: data.security_features.audit_logging },
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Security features and audit logs
        </p>
      </div>

      {isLoading ? (
        <div className="card text-center py-12">
          <Shield className="mx-auto h-8 w-8 animate-pulse text-primary-600" />
          <p className="mt-2 text-gray-600">Loading security information...</p>
        </div>
      ) : (
        <>
          {/* Security Features */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Shield className="mr-2 h-5 w-5 text-primary-600" />
              Active Security Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {features.map((feature) => (
                <div
                  key={feature.name}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <span className="font-medium text-gray-900">{feature.name}</span>
                  </div>
                  <span className="text-sm text-gray-600">{feature.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Summary */}
          {data?.summary && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-2">Total Events</h3>
                <p className="text-3xl font-bold text-gray-900">{data.summary.total_events}</p>
              </div>
              
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-2">By Event Type</h3>
                <div className="space-y-1">
                  {Object.entries(data.summary.by_type || {}).slice(0, 3).map(([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-gray-700">{type}</span>
                      <span className="font-semibold">{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-2">By Severity</h3>
                <div className="space-y-1">
                  {Object.entries(data.summary.by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex justify-between text-sm">
                      <span className={`font-medium ${
                        severity === 'critical' || severity === 'error' ? 'text-red-600' :
                        severity === 'warning' ? 'text-yellow-600' : 'text-gray-700'
                      }`}>
                        {severity}
                      </span>
                      <span className="font-semibold">{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recent Critical Events */}
          {data?.summary?.recent_critical && data.summary.recent_critical.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <AlertCircle className="mr-2 h-5 w-5 text-red-600" />
                Recent Critical Events
              </h2>
              <div className="space-y-2">
                {data.summary.recent_critical.map((event, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-red-50 border border-red-200 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-red-900">{event.action}</p>
                        <p className="text-sm text-red-700 mt-1">
                          {new Date(event.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                        {event.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
