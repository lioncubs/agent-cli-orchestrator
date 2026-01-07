import { useAuthStore } from '../store/authStore'
import { User } from 'lucide-react'

export default function Settings() {
  const user = useAuthStore((state) => state.user)

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      {/* User Profile */}
      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <User className="h-5 w-5" />
          User Profile
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Display Name
            </label>
            <p className="font-medium">{user?.display_name || 'Not set'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Email
            </label>
            <p className="font-medium">{user?.email || 'Not set'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Permission Tier
            </label>
            <p className="font-medium">{user?.permission_tier || 'read-only'}</p>
          </div>
        </div>
      </div>

      {/* Coming Soon Sections */}
      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">GitHub Copilot PAT</h2>
        <p className="text-muted-foreground mb-4">
          Manage your GitHub Copilot Personal Access Token for authenticated delegations
        </p>
        <p className="text-sm text-muted-foreground italic">Coming soon</p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Git Identity</h2>
        <p className="text-muted-foreground mb-4">
          Configure your Git identity for commits and delegations
        </p>
        <p className="text-sm text-muted-foreground italic">Coming soon</p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Preferences</h2>
        <p className="text-muted-foreground mb-4">
          Customize your experience with theme, notifications, and default settings
        </p>
        <p className="text-sm text-muted-foreground italic">Coming soon</p>
      </div>
    </div>
  )
}
