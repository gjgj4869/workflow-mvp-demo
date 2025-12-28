import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, Spin, Alert, Empty } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { jobApi, taskApi } from '@/services/api';

interface LogViewerProps {
  jobRunId: string;
  workflowId: string;
}

function LogViewer({ jobRunId, workflowId }: LogViewerProps) {
  const [activeTab, setActiveTab] = useState<string>('');

  // Fetch tasks for this workflow
  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', workflowId],
    queryFn: () => taskApi.list(workflowId),
  });

  // Set first task as active tab when tasks are loaded
  useEffect(() => {
    if (tasks && tasks.length > 0 && !activeTab) {
      setActiveTab(tasks[0].name);
    }
  }, [tasks, activeTab]);

  if (tasksLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return <Empty description="No tasks found for this workflow" />;
  }

  return (
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      items={tasks.map((task) => ({
        key: task.name,
        label: (
          <span>
            <FileTextOutlined />
            {task.name}
          </span>
        ),
        children: <TaskLogContent jobRunId={jobRunId} taskName={task.name} />,
      }))}
    />
  );
}

interface TaskLogContentProps {
  jobRunId: string;
  taskName: string;
}

function TaskLogContent({ jobRunId, taskName }: TaskLogContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', jobRunId, taskName],
    queryFn: () => jobApi.getLogs(jobRunId, taskName),
    retry: 1,
  });

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Failed to load logs"
        description={(error as any).response?.data?.detail || 'An error occurred while fetching logs'}
        type="error"
        showIcon
      />
    );
  }

  if (!data || !data.logs) {
    return <Empty description="No logs available for this task" />;
  }

  return (
    <div
      style={{
        backgroundColor: '#1e1e1e',
        color: '#d4d4d4',
        padding: '16px',
        borderRadius: '4px',
        fontFamily: 'Consolas, Monaco, "Courier New", monospace',
        fontSize: '13px',
        lineHeight: '1.6',
        maxHeight: '500px',
        overflowY: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {data.logs}
    </div>
  );
}

export default LogViewer;
