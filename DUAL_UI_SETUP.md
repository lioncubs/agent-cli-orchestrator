# Dual UI Setup - Legacy HTML and React SPA

This repository now supports **two user interfaces** that work side by side:

## 🎯 UI Routes

### Primary UI: React SPA
- **URL**: `/ui`
- **Description**: Modern React dashboard with TypeScript, Tailwind CSS, and comprehensive features
- **Status**: From PR #18 - requires build step
- **Features**: 
  - Full dashboard with authentication
  - Session management
  - Delegation wizard
  - Repository management
  - Research artifacts browser
  - Settings page

### Fallback UI: Legacy HTML
- **URL**: `/legacy-ui`
- **Description**: Simple, embedded HTML interface - no build required
- **Status**: Always available
- **Features**:
  - Copilot CLI prompts (sync, async, streaming)
  - Branch management
  - Worktree management
  - Activity logs
  - Direct API testing

## 🔄 How It Works

### When React UI is Built
1. Navigate to `/ui` → Serves the modern React dashboard
2. Static assets are served from `/assets`
3. SPA routing works for all `/ui/*` paths
4. Legacy UI remains accessible at `/legacy-ui`

### When React UI is NOT Built
1. Navigate to `/ui` → Shows instructions to build React UI
2. Provides a direct link to `/legacy-ui` as a fallback
3. Legacy UI works immediately without any build step

## 🛠️ Building the React UI

To enable the modern React dashboard:

```bash
cd src/ui
npm install
npm run build
```

The built files are served automatically by FastAPI from `src/ui/dist/`.

## 📝 Implementation Details

### FastAPI Routes
- `GET /ui` - Serves React SPA index.html (or fallback message)
- `GET /ui/{full_path:path}` - SPA fallback routing for React Router
- `GET /legacy-ui` - Serves embedded HTML interface
- `GET /assets/{path}` - Serves React static assets (JS, CSS, images)

### Code Changes
The implementation maintains backward compatibility by:
1. Keeping the original HTML UI code intact
2. Moving it from `/ui` to `/legacy-ui` route
3. Adding new React SPA routes at `/ui`
4. Mounting static file serving for React assets

## 🎨 Use Cases

### Use Legacy UI When:
- Quick testing without build setup
- Need simple interface for basic operations
- Building/deploying without Node.js
- Debugging API endpoints directly

### Use React UI When:
- Full-featured dashboard needed
- Better UX and modern interface required
- Working with sessions and delegations
- Managing multiple repositories

## 🚀 Deployment

### Production Deployment
1. Build React UI: `cd src/ui && npm run build`
2. Start FastAPI: `python main.py` or `uvicorn main:app`
3. Both UIs available immediately

### Development
- React UI: `cd src/ui && npm run dev` (runs on port 3000, proxies to :8000)
- FastAPI: `python main.py` (runs on port 8000)
- Legacy UI: Always available at http://localhost:8000/legacy-ui

## 📸 Screenshots

### React UI (Not Built Fallback)
Shows helpful instructions and link to legacy UI:

![React UI Not Built](https://github.com/user-attachments/assets/38a20e0c-ae8d-4e38-b2ad-0da9b54ce942)

### Legacy HTML UI
Simple, functional interface with all core features:

![Legacy HTML UI](https://github.com/user-attachments/assets/388aeea7-fe52-4a9f-a108-09fecf27a0f2)

## ✅ Benefits

1. **Backward Compatibility**: Existing users can continue using legacy UI
2. **Progressive Enhancement**: Modern UI when available, fallback when not
3. **Zero Breaking Changes**: All existing API endpoints unchanged
4. **Flexible Deployment**: Choose which UI to use based on needs
5. **No Build Required**: Legacy UI works out of the box

## 🔍 Technical Notes

- Both UIs share the same FastAPI backend and API endpoints
- No conflicts between the two interfaces
- Static file serving only activates when React UI is built
- Legacy UI is fully functional and independently maintained
- React UI build artifacts are ~1.3MB (optimized and code-split)
