# Agent CLI Orchestrator - Frontend Dashboard

Modern React-based dashboard for the Agent CLI Orchestrator.

## Features

- **Dashboard**: Overview with quick stats and recent activity
- **Repositories**: Manage configured repositories
- **Branches**: View and switch Git branches
- **Copilot**: Execute GitHub Copilot CLI prompts with real-time streaming
- **Activity**: Monitor system activities and logs
- **Security**: View security features and audit logs

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query** - Server state management
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client
- **Vitest** - Unit testing
- **React Testing Library** - Component testing

## Development

### Prerequisites

- Node.js 20+
- npm 10+

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The development server will run on http://localhost:3000 and proxy API requests to the backend at http://localhost:8000.

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

The build output will be in the `dist/` directory, which the backend serves at `/dashboard`.

## Testing

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test -- --coverage
```

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API client
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   ├── types/        # TypeScript types
│   ├── test/         # Test utilities and tests
│   ├── App.tsx       # Main app component
│   └── main.tsx      # App entry point
├── public/           # Static assets
├── dist/             # Build output (gitignored)
└── package.json
```

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## API Integration

The frontend communicates with the backend REST API:

- `/repos` - Repository management
- `/branches` - Branch operations
- `/worktrees` - Worktree management
- `/prompt` - Copilot prompts (sync)
- `/prompt/async` - Copilot prompts (async)
- `/prompt/stream` - Copilot prompts (SSE streaming)
- `/logs` - Activity logs
- `/security/summary` - Security dashboard data

## Features

### Real-time Streaming

The Copilot page supports real-time streaming of CLI output using Server-Sent Events (SSE), providing immediate feedback as the Copilot CLI processes prompts.

### Responsive Design

The dashboard is fully responsive and works on desktop, tablet, and mobile devices.

### Type Safety

Full TypeScript coverage ensures type safety across the entire application.

### State Management

TanStack Query provides efficient server state management with automatic caching, background updates, and optimistic updates.
