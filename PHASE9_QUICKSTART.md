# Phase 9 Dashboard - Quick Start Guide

## For Developers

### Running the Dashboard Locally

#### Option 1: Development Mode (Recommended)

Best for active development with hot reload:

```bash
# Terminal 1: Start the backend
cd /home/runner/work/agent-cli-orchestrator/agent-cli-orchestrator
python main.py

# Terminal 2: Start the frontend dev server
cd frontend
npm install
npm run dev
```

Access:
- Frontend dev server: http://localhost:3000
- Backend API: http://localhost:8000
- API requests are proxied from frontend to backend

Features:
- ✅ Hot Module Replacement (HMR)
- ✅ Fast refresh
- ✅ Source maps
- ✅ Type checking

#### Option 2: Production Mode

Best for testing the production build:

```bash
# Build the frontend
cd frontend
npm run build

# Start the backend (serves the built frontend)
cd ..
python main.py
```

Access:
- Dashboard: http://localhost:8000/dashboard
- API: http://localhost:8000

### Making Changes

#### Adding a New Page

1. Create the page component in `frontend/src/pages/MyPage.tsx`:
```typescript
export function MyPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">My Page</h1>
      {/* Your content */}
    </div>
  );
}
```

2. Add the route in `frontend/src/App.tsx`:
```typescript
import { MyPage } from './pages/MyPage';

// In the Routes component:
<Route path="mypage" element={<MyPage />} />
```

3. Add navigation in `frontend/src/components/Layout.tsx`:
```typescript
const navigation = [
  // ... existing items
  { name: 'My Page', href: '/mypage', icon: YourIcon },
];
```

#### Adding API Calls

1. Define types in `frontend/src/types/api.ts`:
```typescript
export interface MyData {
  id: string;
  name: string;
}
```

2. Add method to API client in `frontend/src/api/client.ts`:
```typescript
async getMyData(): Promise<MyData[]> {
  const { data } = await this.client.get('/my-endpoint');
  return data;
}
```

3. Use in component with React Query:
```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

const { data, isLoading } = useQuery({
  queryKey: ['my-data'],
  queryFn: () => apiClient.getMyData(),
});
```

### Testing

```bash
cd frontend

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm test -- --coverage
```

### Building for Production

```bash
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Output will be in dist/
```

### Styling with Tailwind

Use Tailwind utility classes:

```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h2 className="text-xl font-semibold text-gray-900">Title</h2>
  <p className="text-gray-600 mt-2">Description</p>
</div>
```

Custom classes are defined in `frontend/src/index.css`:
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.card` - Card container
- `.input-field` - Input field

### Common Tasks

#### Update Dependencies
```bash
cd frontend
npm update
```

#### Check for Outdated Packages
```bash
npm outdated
```

#### Format Code
```bash
npm run lint
```

#### Preview Production Build
```bash
npm run build
npm run preview
```

## For End Users

### Accessing the Dashboard

1. Ensure the backend is running:
   ```bash
   python main.py
   ```

2. Open your browser to:
   ```
   http://localhost:8000/dashboard
   ```

3. Navigate using the sidebar menu

### Features

- **Dashboard**: Overview of system status
- **Repositories**: View and manage configured repositories
- **Branches**: List branches and switch between them
- **Copilot**: Execute AI prompts with real-time streaming
- **Activity**: Monitor system activities and logs
- **Security**: View security features and audit logs

### Tips

- The activity log auto-refreshes every 5 seconds
- Use the streaming option in Copilot for real-time output
- Click on activity entries to expand details
- The dashboard is fully responsive - works on mobile too!

## Troubleshooting

### Frontend won't start

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### API requests fail

1. Check backend is running on port 8000
2. Check CORS configuration in `config.yaml`
3. Verify `VITE_API_URL` in `.env.development`

### Build fails

```bash
# Check TypeScript errors
npm run build

# If TypeScript errors, check the types
# Common issues:
# - Missing type imports
# - Incorrect API response types
# - Unused variables
```

### Styles not applying

```bash
# Rebuild Tailwind
cd frontend
rm -rf dist
npm run build
```

## Performance

### Production Build
- Initial load: ~105KB (gzipped)
- Subsequent pages: < 10KB (code splitting)
- Time to Interactive: < 2s on 3G

### Optimization Tips
- Images should be < 100KB
- Use code splitting for large components
- Enable compression in production
- Use React.lazy for route-based splitting

## Security

### Development
- CORS allows localhost:3000
- No authentication required (configurable)
- Rate limiting: 60 requests/minute

### Production
- Update CORS to production domain
- Enable authentication
- Use HTTPS/TLS
- Review rate limits

## Resources

- [React Documentation](https://react.dev)
- [React Router](https://reactrouter.com)
- [TanStack Query](https://tanstack.com/query)
- [Tailwind CSS](https://tailwindcss.com)
- [Vite Documentation](https://vitejs.dev)
- [Vitest](https://vitest.dev)

## Support

For issues or questions:
1. Check the documentation
2. Review the code comments
3. Check browser console for errors
4. Review network tab for API errors
5. Open an issue on GitHub
