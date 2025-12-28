import { useEffect, useState } from 'react';
import { Modal, Form, Input, InputNumber, Select, message } from 'antd';
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

  useEffect(() => {
    if (task) {
      form.setFieldsValue({
        name: task.name,
        dependencies: task.dependencies,
        retry_count: task.retry_count,
        retry_delay: task.retry_delay,
      });
      setPythonCode(task.python_callable);
    } else {
      form.resetFields();
      setPythonCode(defaultPythonCode);
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
    const taskData = {
      ...values,
      python_callable: pythonCode,
      params: {},
    };

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
