# Agent CLI Orchestrator - React UI

This is the modern React dashboard UI for the Agent CLI Orchestrator.

## Technology Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v6** - Client-side routing
- **React Query** - Server state management
- **Zustand** - Client state management
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd src/ui
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The dev server will run on `http://localhost:3000` and proxy API requests to the FastAPI backend at `http://localhost:8000`.

### Building for Production

Build the production bundle:

```bash
npm run build
```

The built files will be output to the `dist/` directory and automatically served by the FastAPI application.

### Testing

Run unit tests:

```bash
npm test
```

Run tests with UI:

```bash
npm run test:ui
```

Generate coverage report:

```bash
npm run test:coverage
```

### Code Quality

Type checking:

```bash
npm run type-check
```

Linting:

```bash
npm run lint
```

## Project Structure

```
src/ui/
├── src/
│   ├── api/           # API client and HTTP utilities
│   ├── components/    # Reusable React components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions
│   ├── pages/         # Page components (routes)
│   ├── store/         # Zustand state stores
│   ├── types/         # TypeScript type definitions
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Application entry point
│   └── index.css      # Global styles
├── public/            # Static assets
├── dist/              # Build output (git-ignored)
├── index.html         # HTML template
├── package.json       # Dependencies and scripts
├── tsconfig.json      # TypeScript configuration
├── vite.config.ts     # Vite configuration
└── tailwind.config.js # Tailwind CSS configuration
```

## Pages

- **Login** (`/login`) - User authentication
- **Register** (`/register`) - New user registration
- **Dashboard** (`/`) - Main dashboard with activity overview
- **Sessions** (`/sessions`) - List and filter sessions
- **Session Detail** (`/sessions/:id`) - View session details and conversation
- **Delegation** (`/delegate`) - Start new delegation wizard
- **Research** (`/research`) - Browse research artifacts
- **Repositories** (`/repos`) - Manage repositories
- **Settings** (`/settings`) - User preferences and configuration

## State Management

### Server State (React Query)

- Caching and synchronizing server data
- Automatic background refetching
- Optimistic updates
- Pagination and infinite loading

### Client State (Zustand)

- User authentication state
- Global UI preferences
- Persisted to localStorage

## API Integration

The UI communicates with the FastAPI backend through a typed API client (`src/api/client.ts`).

All API calls:
- Include authentication tokens
- Handle errors consistently
- Redirect to login on 401 responses
- Use React Query for caching and state management

## Styling

The UI uses Tailwind CSS for styling with a custom design system:

- Responsive design (mobile-first)
- Dark mode support (planned)
- Accessible color contrasts
- Consistent spacing and typography

## Contributing

When adding new features:

1. Create components in `src/components/`
2. Add pages in `src/pages/`
3. Define types in `src/types/`
4. Update routes in `src/App.tsx`
5. Write tests alongside your code
6. Update this README if needed

## Deployment

The built UI is automatically served by the FastAPI application. After building:

1. The `dist/` directory contains the production build
2. FastAPI serves static assets from `/assets`
3. All routes fallback to `index.html` for client-side routing

## Future Enhancements

- [ ] Real-time updates via Server-Sent Events
- [ ] Dark mode toggle
- [ ] Keyboard shortcuts
- [ ] Comprehensive accessibility improvements
- [ ] Progressive Web App features
- [ ] Offline support
- [ ] Advanced filtering and search
- [ ] Drag-and-drop file uploads
