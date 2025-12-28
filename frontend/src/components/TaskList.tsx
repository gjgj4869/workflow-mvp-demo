import { Table, Button, Space, Tag, Popconfirm, message } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
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
      render: (name: string) => <strong>{name}</strong>,
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
