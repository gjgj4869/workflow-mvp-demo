import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Form,
  Input,
  Switch,
  Spin,
  Tabs,
  Empty,
} from 'antd';
import {
  EditOutlined,
  RocketOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { workflowApi, taskApi, jobApi, type Workflow, type Task } from '@/services/api';
import TaskList from '@/components/TaskList';
import TaskEditor from '@/components/TaskEditor';
import TaskGraph from '@/components/TaskGraph';
import dayjs from 'dayjs';

function WorkflowDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isTaskEditorOpen, setIsTaskEditorOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>();
  const [form] = Form.useForm();

  // Fetch workflow
  const { data: workflow, isLoading: workflowLoading } = useQuery({
    queryKey: ['workflow', id],
    queryFn: () => workflowApi.get(id!),
    enabled: !!id,
  });

  // Fetch tasks
  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', id],
    queryFn: () => taskApi.list(id!),
    enabled: !!id,
  });

  // Update workflow mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      workflowApi.update(id, data),
    onSuccess: () => {
      message.success('Workflow updated successfully');
      queryClient.invalidateQueries({ queryKey: ['workflow', id] });
      setIsEditModalOpen(false);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to update workflow');
    },
  });

  // Deploy workflow mutation
  const deployMutation = useMutation({
    mutationFn: workflowApi.deploy,
    onSuccess: (data) => {
      message.success(`Workflow deployed! DAG ID: ${data.dag_id}`);
      queryClient.invalidateQueries({ queryKey: ['workflow', id] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to deploy workflow');
    },
  });

  // Trigger workflow mutation
  const triggerMutation = useMutation({
    mutationFn: jobApi.trigger,
    onSuccess: (data) => {
      message.success(`Workflow triggered! Job Run ID: ${data.id}`);
      navigate('/jobs');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to trigger workflow');
    },
  });

  const handleEdit = () => {
    form.setFieldsValue(workflow);
    setIsEditModalOpen(true);
  };

  const handleUpdate = (values: any) => {
    if (id) {
      updateMutation.mutate({ id, data: values });
    }
  };

  const handleDeploy = () => {
    if (!tasks || tasks.length === 0) {
      message.warning('Please add at least one task before deploying');
      return;
    }
    if (id) {
      deployMutation.mutate(id);
    }
  };

  const handleTrigger = () => {
    if (!workflow?.is_active) {
      message.warning('Please activate the workflow before triggering');
      return;
    }
    if (id) {
      triggerMutation.mutate(id);
    }
  };

  const handleAddTask = () => {
    setEditingTask(undefined);
    setIsTaskEditorOpen(true);
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setIsTaskEditorOpen(true);
  };

  const handleTaskEditorClose = () => {
    setIsTaskEditorOpen(false);
    setEditingTask(undefined);
  };

  if (workflowLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <Card>
        <Empty description="Workflow not found" />
      </Card>
    );
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/workflows')}
        style={{ marginBottom: 16 }}
      >
        Back to Workflows
      </Button>

      <Card
        title={workflow.name}
        extra={
          <Space>
            <Button icon={<EditOutlined />} onClick={handleEdit}>
              Edit
            </Button>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={handleDeploy}
              loading={deployMutation.isPending}
            >
              Deploy
            </Button>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleTrigger}
              loading={triggerMutation.isPending}
              disabled={!workflow.is_active}
            >
              Trigger
            </Button>
          </Space>
        }
      >
        <Descriptions column={2} bordered>
          <Descriptions.Item label="Status">
            <Tag color={workflow.is_active ? 'green' : 'default'}>
              {workflow.is_active ? 'Active' : 'Inactive'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Schedule">
            {workflow.schedule || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {workflow.description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {dayjs(workflow.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="Last Updated">
            {dayjs(workflow.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="Tasks"
        style={{ marginTop: 16 }}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddTask}
          >
            Add Task
          </Button>
        }
      >
        <Tabs
          items={[
            {
              key: 'list',
              label: 'List View',
              children: (
                <TaskList
                  tasks={tasks || []}
                  loading={tasksLoading}
                  onEdit={handleEditTask}
                  workflowId={id!}
                />
              ),
            },
            {
              key: 'graph',
              label: 'Graph View',
              children: (
                <TaskGraph
                  tasks={tasks || []}
                  onTaskClick={handleEditTask}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* Edit Workflow Modal */}
      <Modal
        title="Edit Workflow"
        open={isEditModalOpen}
        onCancel={() => setIsEditModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={updateMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdate}
        >
          <Form.Item
            label="Workflow Name"
            name="name"
            rules={[{ required: true, message: 'Please enter workflow name' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item
            label="Schedule"
            name="schedule"
            help="Cron expression or preset (@daily, @hourly, @weekly)"
          >
            <Input />
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

      {/* Task Editor Modal */}
      {isTaskEditorOpen && (
        <TaskEditor
          workflowId={id!}
          task={editingTask}
          tasks={tasks || []}
          open={isTaskEditorOpen}
          onClose={handleTaskEditorClose}
        />
      )}
    </div>
  );
}

export default WorkflowDetailPage;
