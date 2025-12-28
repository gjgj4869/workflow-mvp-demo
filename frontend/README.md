# MLOps Workflow Frontend

Modern React-based frontend for the MLOps Workflow Management System.

## Features

- **Workflow Management**: Create, edit, and manage ML workflows
- **Task Editor**: Visual task creation with Monaco code editor for Python
- **Dependency Graph**: Visualize task dependencies using React Flow
- **Job Monitoring**: Real-time monitoring of workflow executions
- **Log Viewer**: View task execution logs in real-time
- **Dashboard**: Statistics and health monitoring

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing
- **TanStack Query** (React Query) - Server state management
- **Ant Design** - UI component library
- **React Flow** - Task dependency visualization
- **Monaco Editor** - Code editor for Python tasks
- **Axios** - HTTP client
- **Day.js** - Date formatting

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on http://localhost:8000

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` if your backend is running on a different port:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:3000

### 4. Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── TaskList.tsx     # Task list table
│   │   ├── TaskGraph.tsx    # Task dependency graph
│   │   ├── TaskEditor.tsx   # Task creation/edit modal
│   │   └── LogViewer.tsx    # Job log viewer
│   ├── pages/               # Page components
│   │   ├── WorkflowsPage.tsx      # Workflows list
│   │   ├── WorkflowDetailPage.tsx # Workflow details & tasks
│   │   └── JobsPage.tsx           # Job runs monitoring
│   ├── services/            # API clients
│   │   └── api.ts           # Backend API client
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies
```

## Usage

### Creating a Workflow

1. Navigate to **Workflows** page
2. Click **New Workflow** button
3. Fill in workflow details:
   - Name (required)
   - Description
   - Schedule (cron expression or @daily, @hourly, etc.)
   - Active status
4. Click **OK** to create

### Adding Tasks to Workflow

1. Open a workflow from the list
2. Click **Add Task** button
3. Configure task:
   - **Task Name**: Unique identifier (e.g., `data_preprocessing`)
   - **Python Code**: Write task logic using Monaco editor
   - **Dependencies**: Select upstream tasks
   - **Retry Settings**: Configure retry count and delay
4. Click **OK** to save

### Python Code Editor Tips

The Monaco editor provides:
- Syntax highlighting for Python
- Auto-completion
- Code formatting
- Error detection

**Available context variables:**
```python
# Access XCom for inter-task communication
context["ti"].xcom_push(key="result", value=data)
data = context["ti"].xcom_pull(task_ids="previous_task", key="result")

# Access execution date
execution_date = context["execution_date"]
```

### Deploying and Running Workflows

1. **Deploy**: Click **Deploy** button to generate Airflow DAG
2. Wait 30 seconds for Airflow to detect the DAG
3. **Trigger**: Click **Trigger** button to start execution
4. Navigate to **Jobs** page to monitor progress

### Monitoring Job Execution

The Jobs page shows:
- All workflow executions
- Real-time status updates (auto-refreshes every 5 seconds)
- Execution statistics
- Success/failure rates

**View Logs:**
1. Click **View Logs** button on any job run
2. Select task from tabs
3. View execution logs in terminal-style viewer

## API Integration

The frontend communicates with the backend API defined in `src/services/api.ts`.

**API Endpoints:**
- `GET /api/v1/workflows/` - List workflows
- `POST /api/v1/workflows/` - Create workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/deploy` - Deploy to Airflow
- `GET /api/v1/tasks/` - List tasks
- `POST /api/v1/tasks/` - Create task
- `POST /api/v1/jobs/trigger/{workflow_id}` - Trigger workflow
- `GET /api/v1/jobs/` - List job runs
- `GET /api/v1/jobs/{id}/logs/{task_name}` - Get task logs

## Component Documentation

### WorkflowsPage

Lists all workflows with filtering and CRUD operations.

**Features:**
- Workflow table with name, description, schedule, status
- Create new workflow modal
- Edit/delete actions
- Navigation to workflow details

### WorkflowDetailPage

Displays workflow details and manages tasks.

**Features:**
- Workflow information display
- Task list and graph views (tabs)
- Add/edit/delete tasks
- Deploy and trigger workflow
- Navigation back to workflow list

### TaskEditor

Modal for creating and editing tasks.

**Features:**
- Monaco code editor for Python
- Dependency selection (multi-select)
- Retry configuration
- Form validation

### TaskGraph

Visualizes task dependencies using React Flow.

**Features:**
- Automatic layout of task nodes
- Dependency edges with arrows
- Click to edit task
- Zoom and pan controls
- Minimap for navigation

### JobsPage

Monitors workflow executions.

**Features:**
- Job run table with status, duration, timestamps
- Status filtering
- Real-time updates (polling)
- Statistics cards
- Log viewer modal

### LogViewer

Displays task execution logs.

**Features:**
- Tabbed interface for multiple tasks
- Terminal-style log display
- Auto-fetching of logs

## Development

### Code Style

This project uses ESLint and TypeScript for code quality.

```bash
npm run lint
```

### Type Checking

TypeScript is configured with strict mode. Check types:

```bash
npx tsc --noEmit
```

### API Mocking

For development without the backend, you can mock API responses using Mock Service Worker (MSW) or similar tools.

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, you can specify a different port:

```bash
npm run dev -- --port 3001
```

### API Connection Issues

1. Verify backend is running on http://localhost:8000
2. Check CORS settings in backend
3. Check `.env` file configuration
4. Open browser console for error details

### Build Errors

Clear node_modules and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
```

## Future Enhancements

- [ ] WebSocket for real-time job updates
- [ ] Advanced filtering and search
- [ ] Workflow templates
- [ ] Workflow versioning
- [ ] User authentication and authorization
- [ ] Dark mode theme
- [ ] Export workflow as YAML/JSON
- [ ] Drag-and-drop task dependency editor

## Contributing

1. Create a feature branch
2. Make your changes
3. Run linting and type checking
4. Submit a pull request

## License

MIT License
