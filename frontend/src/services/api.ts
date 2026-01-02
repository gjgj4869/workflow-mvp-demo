import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  schedule?: string;
  is_active: boolean;
  is_paused_in_airflow?: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  schedule?: string;
  is_active: boolean;
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  schedule?: string;
  is_active?: boolean;
}

export interface Task {
  id: string;
  workflow_id: string;
  name: string;
  execution_mode: string;
  python_callable?: string;
  git_repository?: string;
  git_branch?: string;
  git_commit_sha?: string;
  script_path?: string;
  function_name?: string;
  docker_image: string;
  params: Record<string, any>;
  dependencies: string[];
  retry_count: number;
  retry_delay: number;
  created_at: string;
}

export interface TaskCreate {
  workflow_id: string;
  name: string;
  execution_mode: string;
  python_callable?: string;
  git_repository?: string;
  git_branch?: string;
  git_commit_sha?: string;
  script_path?: string;
  function_name?: string;
  docker_image?: string;
  params?: Record<string, any>;
  dependencies?: string[];
  retry_count?: number;
  retry_delay?: number;
}

export interface TaskUpdate {
  name?: string;
  execution_mode?: string;
  python_callable?: string;
  git_repository?: string;
  git_branch?: string;
  git_commit_sha?: string;
  script_path?: string;
  function_name?: string;
  docker_image?: string;
  params?: Record<string, any>;
  dependencies?: string[];
  retry_count?: number;
  retry_delay?: number;
}

export interface JobRun {
  id: string;
  workflow_id: string;
  dag_run_id: string;
  status: string;
  triggered_by: string;
  started_at?: string;
  ended_at?: string;
  logs: Record<string, any>;
  created_at: string;
}

export interface JobRunList {
  total: number;
  job_runs: JobRun[];
  page: number;
  page_size: number;
}

export interface Stats {
  workflows: {
    total: number;
    active: number;
    inactive: number;
  };
  job_runs: {
    total: number;
    recent_24h: number;
    by_status: Record<string, number>;
    success_rate: number;
  };
}

// Workflow API
export const workflowApi = {
  list: async (): Promise<Workflow[]> => {
    const response = await apiClient.get('/api/v1/workflows/');
    return response.data.workflows || [];
  },

  get: async (id: string): Promise<Workflow> => {
    const response = await apiClient.get(`/api/v1/workflows/${id}`);
    return response.data;
  },

  create: async (data: WorkflowCreate): Promise<Workflow> => {
    const response = await apiClient.post('/api/v1/workflows/', data);
    return response.data;
  },

  update: async (id: string, data: WorkflowUpdate): Promise<Workflow> => {
    const response = await apiClient.put(`/api/v1/workflows/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/workflows/${id}`);
  },

  deploy: async (id: string): Promise<{ message: string; dag_id: string; dag_file: string }> => {
    const response = await apiClient.post(`/api/v1/workflows/${id}/deploy`);
    return response.data;
  },

  pause: async (id: string): Promise<{ message: string; dag_id: string }> => {
    const response = await apiClient.post(`/api/v1/workflows/${id}/pause`);
    return response.data;
  },

  unpause: async (id: string): Promise<{ message: string; dag_id: string }> => {
    const response = await apiClient.post(`/api/v1/workflows/${id}/unpause`);
    return response.data;
  },

  unpauseAllActive: async (): Promise<{ message: string; success_count: number; failed_count: number }> => {
    const response = await apiClient.post('/api/v1/workflows/unpause-all-active');
    return response.data;
  },
};

// Task API
export const taskApi = {
  list: async (workflowId: string): Promise<Task[]> => {
    const response = await apiClient.get(`/api/v1/workflows/${workflowId}/tasks`);
    return response.data.tasks || [];
  },

  get: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/api/v1/tasks/${id}`);
    return response.data;
  },

  create: async (data: TaskCreate): Promise<Task> => {
    const response = await apiClient.post('/api/v1/tasks/', data);
    return response.data;
  },

  update: async (id: string, data: TaskUpdate): Promise<Task> => {
    const response = await apiClient.put(`/api/v1/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/tasks/${id}`);
  },
};

// Job API
export const jobApi = {
  list: async (params?: {
    workflow_id?: string;
    status_filter?: string;
    skip?: number;
    limit?: number;
  }): Promise<JobRunList> => {
    const response = await apiClient.get('/api/v1/jobs/', { params });
    return response.data;
  },

  get: async (id: string): Promise<JobRun> => {
    const response = await apiClient.get(`/api/v1/jobs/${id}`);
    return response.data;
  },

  trigger: async (workflowId: string): Promise<JobRun> => {
    const response = await apiClient.post(`/api/v1/jobs/trigger/${workflowId}`);
    return response.data;
  },

  getLogs: async (jobRunId: string, taskName: string): Promise<{ task_name: string; logs: string }> => {
    const response = await apiClient.get(`/api/v1/jobs/${jobRunId}/logs/${taskName}`);
    return response.data;
  },
};

// Monitoring API
export const monitoringApi = {
  stats: async (): Promise<Stats> => {
    const response = await apiClient.get('/api/v1/monitoring/stats');
    return response.data;
  },

  health: async (): Promise<{
    status: string;
    components: Record<string, string>;
  }> => {
    const response = await apiClient.get('/api/v1/monitoring/health');
    return response.data;
  },
};

export default apiClient;
