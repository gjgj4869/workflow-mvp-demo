import { useEffect, useState } from 'react';
import { Modal, Form, Input, InputNumber, Select, message, Radio, Space } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import Editor from '@monaco-editor/react';
import { taskApi, type Task, type TaskCreate, type TaskUpdate } from '@/services/api';

interface TaskEditorProps {
  workflowId: string;
  task?: Task;
  tasks: Task[];
  open: boolean;
  onClose: () => void;
}

const defaultPythonCode = `# Write your Python code here
# You have access to the 'context' variable for XCom operations

print("Task started")

# Example: Push data to XCom
# context["ti"].xcom_push(key="result", value="some_value")

# Example: Pull data from XCom
# data = context["ti"].xcom_pull(task_ids="previous_task", key="result")

print("Task completed")
`;

function TaskEditor({ workflowId, task, tasks, open, onClose }: TaskEditorProps) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [pythonCode, setPythonCode] = useState(task?.python_callable || defaultPythonCode);
  const [executionMode, setExecutionMode] = useState<'inline' | 'git'>(
    task?.execution_mode === 'git' ? 'git' : 'inline'
  );

  useEffect(() => {
    if (task) {
      form.setFieldsValue({
        name: task.name,
        git_repository: task.git_repository,
        git_branch: task.git_branch || 'main',
        script_path: task.script_path,
        function_name: task.function_name,
        docker_image: task.docker_image || 'python:3.9-slim',
        dependencies: task.dependencies,
        retry_count: task.retry_count,
        retry_delay: task.retry_delay,
      });
      setPythonCode(task.python_callable || defaultPythonCode);
      setExecutionMode(task.execution_mode === 'git' ? 'git' : 'inline');
    } else {
      form.resetFields();
      setPythonCode(defaultPythonCode);
      setExecutionMode('inline');
    }
  }, [task, form]);

  // Create task mutation
  const createMutation = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => {
      message.success('Task created successfully');
      queryClient.invalidateQueries({ queryKey: ['tasks', workflowId] });
      onClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to create task');
    },
  });

  // Update task mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdate }) =>
      taskApi.update(id, data),
    onSuccess: () => {
      message.success('Task updated successfully');
      queryClient.invalidateQueries({ queryKey: ['tasks', workflowId] });
      onClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to update task');
    },
  });

  const handleSubmit = async (values: any) => {
    let taskData: any;

    if (executionMode === 'inline') {
      // Inline code mode
      taskData = {
        ...values,
        execution_mode: 'inline',
        python_callable: pythonCode,
        git_repository: undefined,
        git_branch: undefined,
        script_path: undefined,
        function_name: undefined,
        params: {},
      };
    } else {
      // Git mode
      taskData = {
        ...values,
        execution_mode: 'git',
        python_callable: undefined,
        params: {},
      };
    }

    if (task) {
      // Update existing task
      updateMutation.mutate({
        id: task.id,
        data: taskData,
      });
    } else {
      // Create new task
      const createData: TaskCreate = {
        workflow_id: workflowId,
        ...taskData,
      };
      createMutation.mutate(createData);
    }
  };

  // Filter out current task from dependency options
  const availableTasks = task
    ? tasks.filter((t) => t.id !== task.id)
    : tasks;

  return (
    <Modal
      title={task ? 'Edit Task' : 'Create New Task'}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      width={900}
      styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          git_branch: 'main',
          docker_image: 'python:3.9-slim',
          retry_count: 2,
          retry_delay: 300,
          dependencies: [],
        }}
      >
        <Form.Item
          label="Task Name"
          name="name"
          rules={[
            { required: true, message: 'Please enter task name' },
            {
              pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
              message: 'Task name must start with a letter and contain only letters, numbers, and underscores',
            },
          ]}
        >
          <Input placeholder="e.g., data_preprocessing" />
        </Form.Item>

        <Form.Item label="Execution Mode" required>
          <Radio.Group
            value={executionMode}
            onChange={(e) => setExecutionMode(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="inline">Inline Code</Radio.Button>
            <Radio.Button value="git">Git Repository</Radio.Button>
          </Radio.Group>
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            {executionMode === 'inline'
              ? 'Write Python code directly in the editor below'
              : 'Reference a Python function from a Git repository'}
          </div>
        </Form.Item>

        {executionMode === 'inline' ? (
          <Form.Item label="Python Code" required>
            <div style={{ border: '1px solid #d9d9d9', borderRadius: '4px' }}>
              <Editor
                height="300px"
                defaultLanguage="python"
                value={pythonCode}
                onChange={(value) => setPythonCode(value || '')}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                }}
              />
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              Tip: Use <code>context["ti"].xcom_push()</code> and <code>context["ti"].xcom_pull()</code> to share data between tasks
            </div>
          </Form.Item>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item
              label="Git Repository URL"
              name="git_repository"
              rules={[{ required: true, message: 'Please enter Git repository URL' }]}
              help="URL of the Git repository (e.g., https://github.com/org/ml-pipeline.git)"
            >
              <Input placeholder="https://github.com/org/ml-pipeline.git" />
            </Form.Item>

            <Form.Item
              label="Git Branch"
              name="git_branch"
              rules={[{ required: true, message: 'Please enter Git branch' }]}
              help="Branch name to checkout"
            >
              <Input placeholder="main" />
            </Form.Item>

            <Form.Item
              label="Git Commit SHA (Optional)"
              name="git_commit_sha"
              help="Specific commit SHA for reproducibility. Leave empty to use latest from branch."
            >
              <Input placeholder="e.g., a1b2c3d4e5f6..." maxLength={40} />
            </Form.Item>

            <Form.Item
              label="Script Path"
              name="script_path"
              rules={[{ required: true, message: 'Please enter script path' }]}
              help="Path to Python script in Git repository (e.g., src/train.py)"
            >
              <Input placeholder="src/train.py" />
            </Form.Item>

            <Form.Item
              label="Function Name"
              name="function_name"
              rules={[{ required: true, message: 'Please enter function name' }]}
              help="Function name to execute from the script"
            >
              <Input placeholder="train_model" />
            </Form.Item>
          </Space>
        )}

        <Form.Item
          label="Docker Image"
          name="docker_image"
          rules={[{ required: true, message: 'Please select Docker image' }]}
          help="Docker image to use for task execution"
        >
          <Select placeholder="Select Docker image">
            <Select.Option value="python:3.8-slim">Python 3.8 (Slim)</Select.Option>
            <Select.Option value="python:3.9-slim">Python 3.9 (Slim)</Select.Option>
            <Select.Option value="python:3.10-slim">Python 3.10 (Slim)</Select.Option>
            <Select.Option value="python:3.11-slim">Python 3.11 (Slim)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Upstream Tasks (Dependencies)"
          name="dependencies"
          help="Select tasks that must complete before this task runs"
        >
          <Select
            mode="multiple"
            placeholder="Select upstream tasks"
            options={availableTasks.map((t) => ({
              label: t.name,
              value: t.name,
            }))}
          />
        </Form.Item>

        <Form.Item
          label="Retry Count"
          name="retry_count"
          help="Number of times to retry on failure"
        >
          <InputNumber min={0} max={10} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="Retry Delay (seconds)"
          name="retry_delay"
          help="Delay between retry attempts"
        >
          <InputNumber min={0} max={3600} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export default TaskEditor;
