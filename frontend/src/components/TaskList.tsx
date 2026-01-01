import { Table, Button, Space, Tag, Popconfirm, message, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, GithubOutlined, CodeOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { taskApi, type Task } from '@/services/api';

interface TaskListProps {
  tasks: Task[];
  loading: boolean;
  onEdit: (task: Task) => void;
  workflowId: string;
}

function TaskList({ tasks, loading, onEdit, workflowId }: TaskListProps) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => {
      message.success('Task deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['tasks', workflowId] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to delete task');
    },
  });

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const columns = [
    {
      title: 'Task Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Task) => (
        <Space>
          {record.script_path && record.function_name ? (
            <Tooltip title={`Git: ${record.script_path} → ${record.function_name}`}>
              <GithubOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
            </Tooltip>
          ) : (
            <Tooltip title="Inline Code">
              <CodeOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
            </Tooltip>
          )}
          <strong>{name}</strong>
        </Space>
      ),
    },
    {
      title: 'Dependencies',
      dataIndex: 'dependencies',
      key: 'dependencies',
      render: (dependencies: string[]) => (
        <>
          {dependencies.length > 0 ? (
            dependencies.map((dep) => (
              <Tag key={dep} color="blue">
                {dep}
              </Tag>
            ))
          ) : (
            <Tag>No dependencies</Tag>
          )}
        </>
      ),
    },
    {
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
    },
    {
      title: 'Retry Delay (s)',
      dataIndex: 'retry_delay',
      key: 'retry_delay',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Task) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => onEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete task"
            description="Are you sure you want to delete this task?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      dataSource={tasks}
      columns={columns}
      rowKey="id"
      loading={loading}
      pagination={false}
    />
  );
}

export default TaskList;
