import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  Table,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Switch,
  message,
  Popconfirm,
  Card,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RocketOutlined,
  StopOutlined,
  DownloadOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { workflowApi, type Workflow, type WorkflowCreate } from '@/services/api';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

function WorkflowsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  // Fetch workflows
  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: workflowApi.list,
    refetchInterval: 5000, // Auto-refresh every 5 seconds to sync with Airflow
  });

  // Create workflow mutation
  const createMutation = useMutation({
    mutationFn: workflowApi.create,
    onSuccess: () => {
      message.success('Workflow created successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setIsModalOpen(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to create workflow');
    },
  });

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: workflowApi.delete,
    onSuccess: () => {
      message.success('Workflow deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to delete workflow');
    },
  });

  // Pause workflow mutation
  const pauseMutation = useMutation({
    mutationFn: workflowApi.pause,
    onSuccess: () => {
      message.success('Workflow paused in Airflow');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to pause workflow');
    },
  });

  // Unpause workflow mutation
  const unpauseMutation = useMutation({
    mutationFn: workflowApi.unpause,
    onSuccess: () => {
      message.success('Workflow unpaused in Airflow');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to unpause workflow');
    },
  });

  // Unpause all active workflows mutation
  const unpauseAllMutation = useMutation({
    mutationFn: workflowApi.unpauseAllActive,
    onSuccess: (data) => {
      message.success(`Unpaused ${data.success_count} workflows successfully`);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to unpause workflows');
    },
  });

  const handleCreate = async (values: WorkflowCreate) => {
    createMutation.mutate(values);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const handleTogglePause = (workflow: Workflow) => {
    if (workflow.is_paused_in_airflow) {
      unpauseMutation.mutate(workflow.id);
    } else {
      pauseMutation.mutate(workflow.id);
    }
  };

  const handleExportYAML = async (workflow: Workflow) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/workflows/${workflow.id}/export-yaml`
      );

      if (!response.ok) {
        throw new Error('Failed to export workflow');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${workflow.name}.yaml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      message.success(`Workflow exported as ${workflow.name}.yaml`);
    } catch (error: any) {
      message.error(error.message || 'Failed to export workflow');
    }
  };

  const handleImportYAML = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/workflows/import-yaml`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to import workflow');
      }

      const result = await response.json();
      message.success(`Workflow "${result.name}" imported successfully`);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    } catch (error: any) {
      message.error(error.message || 'Failed to import workflow');
    }

    return false; // Prevent default upload behavior
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Workflow) => (
        <a onClick={() => navigate(`/workflows/${record.id}`)}>{name}</a>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Schedule',
      dataIndex: 'schedule',
      key: 'schedule',
      render: (schedule?: string) => schedule || '-',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'} icon={isActive ? <RocketOutlined /> : <StopOutlined />}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Airflow Status',
      dataIndex: 'is_paused_in_airflow',
      key: 'is_paused_in_airflow',
      render: (isPaused?: boolean, record?: Workflow) => {
        if (isPaused === null || isPaused === undefined) {
          return (
            <Tag color="default" icon={<QuestionCircleOutlined />}>
              Not Deployed
            </Tag>
          );
        }
        return (
          <Space>
            <Tag
              color={isPaused ? 'orange' : 'success'}
              icon={isPaused ? <PauseCircleOutlined /> : <CheckCircleOutlined />}
            >
              {isPaused ? 'Paused' : 'Running'}
            </Tag>
            <Button
              size="small"
              type={isPaused ? 'primary' : 'default'}
              icon={isPaused ? <CheckCircleOutlined /> : <PauseCircleOutlined />}
              onClick={() => record && handleTogglePause(record)}
              loading={pauseMutation.isPending || unpauseMutation.isPending}
            >
              {isPaused ? 'Unpause' : 'Pause'}
            </Button>
          </Space>
        );
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).fromNow(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Workflow) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/workflows/${record.id}`)}
          >
            Edit
          </Button>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleExportYAML(record)}
          >
            Export YAML
          </Button>
          <Popconfirm
            title="Delete workflow"
            description="Are you sure you want to delete this workflow?"
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
    <div>
      <Card
        title="Workflows"
        extra={
          <Space>
            <Button
              icon={<CheckCircleOutlined />}
              onClick={() => unpauseAllMutation.mutate()}
              loading={unpauseAllMutation.isPending}
            >
              Unpause All Active
            </Button>
            <Upload
              accept=".yaml,.yml"
              beforeUpload={handleImportYAML}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>
                Import YAML
              </Button>
            </Upload>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsModalOpen(true)}
            >
              New Workflow
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={workflows}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} workflows`,
          }}
        />
      </Card>

      <Modal
        title="Create New Workflow"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ is_active: true }}
        >
          <Form.Item
            label="Workflow Name"
            name="name"
            rules={[{ required: true, message: 'Please enter workflow name' }]}
          >
            <Input placeholder="e.g., ml_training_pipeline" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea
              rows={3}
              placeholder="Describe what this workflow does"
            />
          </Form.Item>

          <Form.Item
            label="Schedule"
            name="schedule"
            help="Cron expression or preset (@daily, @hourly, @weekly)"
          >
            <Input placeholder="e.g., @daily or 0 0 * * *" />
          </Form.Item>

          <Form.Item
            label="Active"
            name="is_active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default WorkflowsPage;
