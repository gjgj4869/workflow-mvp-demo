# Frontend Setup Guide

Complete guide to setting up and running the React frontend for MLOps Workflow Manager.

## Quick Start

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.example .env

# 4. Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## Prerequisites

### Required

- **Node.js** 18.0.0 or higher
- **npm** 9.0.0 or higher (comes with Node.js)

### Optional

- **yarn** or **pnpm** (alternative package managers)

### Check Prerequisites

```bash
node --version  # Should be 18.0.0+
npm --version   # Should be 9.0.0+
```

### Install Node.js

**Windows:**
- Download from https://nodejs.org/
- Run installer and follow prompts

**macOS:**
```bash
brew install node
```

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

---

## Installation Steps

### 1. Navigate to Frontend Directory

```bash
cd workflow-mvp-demo/frontend
```

### 2. Install Dependencies

This will install all required packages from `package.json`.

```bash
npm install
```

**Expected output:**
```
added 1247 packages, and audited 1248 packages in 45s
```

**If you encounter errors:**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### 3. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` if backend is on different host/port:

```env
VITE_API_URL=http://localhost:8000
```

### 4. Verify Installation

Check that all dependencies are installed:

```bash
npm list --depth=0
```

---

## Running the Frontend

### Development Mode

Start the development server with hot reload:

```bash
npm run dev
```

**Output:**
```
  VITE v5.0.11  ready in 423 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Access the application:**
- Open browser to http://localhost:3000
- Changes to source files will auto-reload

### Production Build

Build optimized production bundle:

```bash
npm run build
```

**Output files in `dist/` directory:**
```
dist/
├── assets/
│   ├── index-[hash].js
│   └── index-[hash].css
└── index.html
```

### Preview Production Build

Test the production build locally:

```bash
npm run preview
```

Access at http://localhost:4173

---

## Using the Frontend

### 1. Workflows Page

**Create a New Workflow:**

1. Click **"New Workflow"** button
2. Fill in the form:
   ```
   Name: ml_training_pipeline
   Description: Train ML model on daily data
   Schedule: @daily
   Active: ✓ (checked)
   ```
3. Click **OK**

**Manage Workflows:**
- **Edit**: Click workflow name or Edit button
- **Delete**: Click Delete button (confirmation required)
- **View Details**: Click workflow name

### 2. Workflow Detail Page

**Add Tasks:**

1. Click **"Add Task"** button
2. Configure task:
   - **Name**: `data_preprocessing`
   - **Python Code**:
     ```python
     import pandas as pd
     print("Loading data...")
     df = pd.read_csv("/data/input.csv")
     print(f"Data shape: {df.shape}")
     context["ti"].xcom_push(key="data", value=df.to_dict())
     ```
   - **Dependencies**: (none for first task)
   - **Retry Count**: 2
   - **Retry Delay**: 300

3. Click **OK**

**Add Dependent Task:**

1. Click **"Add Task"** again
2. Configure:
   - **Name**: `model_training`
   - **Python Code**:
     ```python
     from sklearn.ensemble import RandomForestClassifier
     data = context["ti"].xcom_pull(task_ids="data_preprocessing", key="data")
     print(f"Training model with {len(data)} samples")
     model = RandomForestClassifier()
     # Training logic here
     ```
   - **Dependencies**: ✓ data_preprocessing
   - **Retry Count**: 1

**View Task Graph:**

Switch to **Graph View** tab to visualize dependencies:
- Nodes represent tasks
- Arrows show dependencies
- Click nodes to edit tasks

**Deploy Workflow:**

1. Click **"Deploy"** button
2. Wait for success message
3. DAG file created in Airflow

**Trigger Execution:**

1. Click **"Trigger"** button
2. Redirected to Jobs page
3. Monitor execution progress

### 3. Jobs Page

**Monitor Executions:**

- **Status Icons**:
  - 🟢 Success
  - 🔴 Failed
  - 🔵 Running
  - ⏱️ Queued

- **Auto-refresh**: Updates every 5 seconds

**Filter by Status:**

Use the dropdown to filter:
- All
- Success
- Failed
- Running
- Queued

**View Logs:**

1. Click **"View Logs"** button
2. Modal opens with tabs for each task
3. Click task tab to view logs
4. Logs displayed in terminal style

**Statistics Cards:**
- **Total Runs**: All-time job executions
- **Recent (24h)**: Jobs in last 24 hours
- **Success Rate**: Percentage of successful runs
- **Active Workflows**: Currently active workflows

---

## Features

### Monaco Code Editor

**Python code editing with:**
- Syntax highlighting
- Auto-completion
- Error detection
- Line numbers
- Code folding
- Search/replace (Ctrl+F)

**Keyboard shortcuts:**
- `Ctrl+S`: Save (via form submit)
- `Ctrl+F`: Find
- `Ctrl+H`: Replace
- `Alt+Shift+F`: Format code

### Task Dependency Graph

**React Flow visualization:**
- Drag to pan
- Scroll to zoom
- Click nodes to edit
- Minimap for navigation
- Auto-layout of nodes

### Real-time Updates

**Jobs page auto-refreshes:**
- Job list: Every 5 seconds
- Stats: Every 10 seconds
- Manual refresh: Click browser refresh

---

## Configuration

### Change API URL

Edit `frontend/.env`:

```env
VITE_API_URL=http://your-backend:8000
```

Restart dev server after changes.

### Change Port

```bash
npm run dev -- --port 3001
```

Or edit `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3001,
  },
})
```

### Proxy Configuration

The Vite config proxies `/api` requests to backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

---

## Troubleshooting

### Port 3000 Already in Use

**Error:**
```
Port 3000 is in use, trying another one...
```

**Solution:**
1. Kill process using port 3000:
   ```bash
   # Windows
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F

   # macOS/Linux
   lsof -ti:3000 | xargs kill -9
   ```

2. Or use different port:
   ```bash
   npm run dev -- --port 3001
   ```

### Cannot Connect to Backend

**Error in browser console:**
```
Network Error
or
CORS policy error
```

**Solution:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check `.env` file:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. Verify CORS settings in backend (`backend/app/main.py`):
   ```python
   allow_origins=["http://localhost:3000"]
   ```

### Dependencies Installation Fails

**Error:**
```
npm ERR! code ERESOLVE
```

**Solution:**
```bash
# Use legacy peer deps
npm install --legacy-peer-deps

# Or force
npm install --force
```

### Build Fails

**Error:**
```
TypeScript error in ...
```

**Solution:**
1. Check TypeScript version:
   ```bash
   npx tsc --version
   ```

2. Clear TypeScript cache:
   ```bash
   rm -rf node_modules/.cache
   ```

3. Reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

### Page is Blank

**Symptoms:**
- White screen
- No errors in console

**Solution:**
1. Check browser console for errors
2. Verify backend is accessible
3. Hard refresh: `Ctrl+Shift+R`
4. Clear browser cache

---

## Development Tips

### Hot Reload

Changes to source files auto-reload. If not working:

```bash
# Restart dev server
npm run dev
```

### Component Development

Create new components in `src/components/`:

```typescript
// src/components/MyComponent.tsx
import { Button } from 'antd';

function MyComponent() {
  return <Button>Click me</Button>;
}

export default MyComponent;
```

### API Integration

Add new API endpoints in `src/services/api.ts`:

```typescript
export const myApi = {
  list: async (): Promise<MyType[]> => {
    const response = await apiClient.get('/api/v1/my-endpoint');
    return response.data;
  },
};
```

Use with React Query:

```typescript
import { useQuery } from '@tanstack/react-query';
import { myApi } from '@/services/api';

function MyComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-data'],
    queryFn: myApi.list,
  });

  if (isLoading) return <Spin />;
  return <div>{data?.map(...)}</div>;
}
```

---

## Production Deployment

### Build for Production

```bash
npm run build
```

### Deploy Static Files

**Option 1: Nginx**

```nginx
server {
  listen 80;
  server_name your-domain.com;

  root /path/to/frontend/dist;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api {
    proxy_pass http://backend:8000;
  }
}
```

**Option 2: Docker**

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**Option 3: Serve**

```bash
npm install -g serve
serve -s dist -l 3000
```

---

## Support

For issues or questions:
- Check **frontend/README.md** for detailed documentation
- Review **TEST_RESULTS.md** for working examples
- Open issue on GitHub repository

---

## Next Steps

After frontend is running:

1. ✅ Access http://localhost:3000
2. ✅ Create your first workflow
3. ✅ Add tasks with Python code
4. ✅ Deploy and trigger workflow
5. ✅ Monitor execution in Jobs page
6. ✅ View task logs

Happy workflow building! 🚀
