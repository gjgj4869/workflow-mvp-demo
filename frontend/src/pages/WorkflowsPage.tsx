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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RocketOutlined,
  StopOutlined,
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

  const handleCreate = async (values: WorkflowCreate) => {
    createMutation.mutate(values);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalOpen(true)}
          >
            New Workflow
          </Button>
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
