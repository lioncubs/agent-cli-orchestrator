import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Send, Loader2, X } from 'lucide-react';
import type { StreamEvent } from '../types/api';

export function Copilot() {
  const [prompt, setPrompt] = useState('');
  const [streamingOutput, setStreamingOutput] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  const { data: repos } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.listRepositories(),
  });

  const { data: sessions } = useQuery({
    queryKey: ['copilot-sessions'],
    queryFn: () => apiClient.listCopilotSessions(),
  });

  const executePromptMutation = useMutation({
    mutationFn: (data: { prompt: string; repo_name?: string }) =>
      apiClient.executePromptAsync({
        prompt: data.prompt,
        repo_name: data.repo_name,
        show_full_output: true,
      }),
    onSuccess: (data) => {
      setStreamingOutput((prev) => [
        ...prev,
        `\n✅ Prompt executed successfully`,
        JSON.stringify(data.output, null, 2),
      ]);
    },
    onError: (error: Error) => {
      setStreamingOutput((prev) => [
        ...prev,
        `\n❌ Error: ${error.message}`,
      ]);
    },
  });

  const handleStreamingPrompt = () => {
    if (!prompt.trim()) return;

    setStreamingOutput([`🚀 Executing: ${prompt}\n`]);
    setIsStreaming(true);

    try {
      const eventSource = apiClient.createStreamingPrompt({
        prompt: prompt.trim(),
        repo_name: selectedRepo || undefined,
      });

      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data: StreamEvent = JSON.parse(event.data);
          
          switch (data.type) {
            case 'start':
              setStreamingOutput((prev) => [...prev, '⏳ Starting...']);
              break;
            case 'stdout':
              setStreamingOutput((prev) => [...prev, data.data || '']);
              break;
            case 'stderr':
              setStreamingOutput((prev) => [...prev, `⚠️ ${data.data}`]);
              break;
            case 'complete':
              setStreamingOutput((prev) => [...prev, '\n✅ Completed']);
              setIsStreaming(false);
              eventSource.close();
              break;
            case 'error':
              setStreamingOutput((prev) => [...prev, `\n❌ Error: ${data.message}`]);
              setIsStreaming(false);
              eventSource.close();
              break;
          }
        } catch (error) {
          console.error('Failed to parse event:', error);
        }
      };

      eventSource.onerror = () => {
        setStreamingOutput((prev) => [...prev, '\n❌ Connection error']);
        setIsStreaming(false);
        eventSource.close();
      };
    } catch (error: any) {
      setStreamingOutput((prev) => [...prev, `\n❌ Error: ${error.message}`]);
      setIsStreaming(false);
    }
  };

  const handleStandardPrompt = () => {
    if (!prompt.trim()) return;

    setStreamingOutput([`🚀 Executing: ${prompt}\n⏳ Processing...`]);
    executePromptMutation.mutate({
      prompt: prompt.trim(),
      repo_name: selectedRepo || undefined,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (useStreaming) {
      handleStreamingPrompt();
    } else {
      handleStandardPrompt();
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setIsStreaming(false);
      setStreamingOutput((prev) => [...prev, '\n⚠️ Stopped by user']);
    }
  };

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamingOutput]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">GitHub Copilot CLI</h1>
        <p className="mt-2 text-gray-600">
          Execute AI-powered prompts using GitHub Copilot CLI
        </p>
      </div>

      {/* Configuration */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repository
            </label>
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="input-field"
            >
              <option value="">Default</option>
              {repos?.repositories.map((repo) => (
                <option key={repo.name} value={repo.name}>
                  {repo.name} {repo.default ? '(default)' : ''}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Use streaming output</span>
            </label>
          </div>
        </div>
      </div>

      {/* Prompt Input */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Prompt
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your Copilot prompt here... (e.g., 'How do I reverse a string in Python?')"
              rows={4}
              className="input-field"
              disabled={isStreaming}
            />
          </div>
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <button
                type="submit"
                disabled={isStreaming || !prompt.trim() || executePromptMutation.isPending}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {(isStreaming || executePromptMutation.isPending) ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Execute
                  </>
                )}
              </button>
              {isStreaming && (
                <button
                  type="button"
                  onClick={handleStop}
                  className="btn-secondary flex items-center"
                >
                  <X className="mr-2 h-4 w-4" />
                  Stop
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                setPrompt('');
                setStreamingOutput([]);
              }}
              className="text-sm text-gray-600 hover:text-gray-900"
              disabled={isStreaming}
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Output */}
      {streamingOutput.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Output</h2>
          <div
            ref={outputRef}
            className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-y-auto max-h-96"
          >
            {streamingOutput.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap">
                {line}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Sessions */}
      {sessions && sessions.sessions && sessions.sessions.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Active Sessions</h2>
          <div className="space-y-2">
            {sessions.sessions.map((session) => (
              <div
                key={session.session_id}
                className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-mono text-sm text-gray-900">{session.session_id}</p>
                  <p className="text-xs text-gray-500">
                    {session.prompt_count} prompt(s) | Last used: {new Date(session.last_used_at || session.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
