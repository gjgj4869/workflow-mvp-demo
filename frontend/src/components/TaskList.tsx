import { useState } from 'react';
import { Table, Button, Space, Tag, Popconfirm, message, Tooltip, Modal, Spin } from 'antd';
import { EditOutlined, DeleteOutlined, GithubOutlined, CodeOutlined, EyeOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import Editor from '@monaco-editor/react';
import { taskApi, type Task } from '@/services/api';

interface TaskListProps {
  tasks: Task[];
  loading: boolean;
  onEdit: (task: Task) => void;
  workflowId: string;
}

function TaskList({ tasks, loading, onEdit, workflowId }: TaskListProps) {
  const queryClient = useQueryClient();
  const [codeViewModal, setCodeViewModal] = useState<{
    visible: boolean;
    task: Task | null;
    code: string;
    loading: boolean;
  }>({
    visible: false,
    task: null,
    code: '',
    loading: false,
  });

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

  const handleViewCode = async (task: Task) => {
    setCodeViewModal({ visible: true, task, code: '', loading: true });

    try {
      if (task.execution_mode === 'inline') {
        // Inline 모드: python_callable 직접 표시
        setCodeViewModal({
          visible: true,
          task,
          code: task.python_callable || '# No code available',
          loading: false,
        });
      } else if (task.execution_mode === 'git') {
        // Git 모드: GitHub에서 코드 가져오기
        const { git_repository, git_branch, git_commit_sha, script_path } = task;

        if (!git_repository || !script_path) {
          throw new Error('Git repository or script path is missing');
        }

        // GitHub URL 파싱 (https://github.com/owner/repo.git -> owner/repo)
        const repoMatch = git_repository.match(/github\.com[\/:](.+?)(?:\.git)?$/);
        if (!repoMatch) {
          throw new Error('Invalid GitHub repository URL');
        }
        const repoPath = repoMatch[1];

        // GitHub Raw URL 생성
        const ref = git_commit_sha || git_branch || 'main';
        const rawUrl = `https://raw.githubusercontent.com/${repoPath}/${ref}/${script_path}`;

        const response = await fetch(rawUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch code: ${response.statusText}`);
        }

        const code = await response.text();
        setCodeViewModal({ visible: true, task, code, loading: false });
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to load code');
      setCodeViewModal({ visible: false, task: null, code: '', loading: false });
    }
  };

  const handleEditorMount = (editor: any) => {
    const task = codeViewModal.task;
    if (!task || task.execution_mode !== 'git' || !task.function_name) {
      return;
    }

    // 함수 정의 라인 찾기 (def function_name(): 또는 def function_name()로 시작)
    const code = codeViewModal.code;
    const lines = code.split('\n');
    const functionPattern = new RegExp(`^\\s*def\\s+${task.function_name}\\s*\\(`);

    let functionStartLine = -1;
    let functionEndLine = -1;

    for (let i = 0; i < lines.length; i++) {
      if (functionPattern.test(lines[i])) {
        functionStartLine = i + 1; // Monaco Editor는 1-based indexing

        // 함수 끝 찾기: 다음 def 또는 class가 나오거나 파일 끝까지
        for (let j = i + 1; j < lines.length; j++) {
          const line = lines[j];
          // 들여쓰기가 없는 def 또는 class를 만나면 함수 끝
          if (/^(def|class)\s+/.test(line)) {
            functionEndLine = j;
            break;
          }
        }

        // 함수 끝을 못 찾으면 파일 끝까지
        if (functionEndLine === -1) {
          functionEndLine = lines.length;
        }

        break;
      }
    }

    if (functionStartLine > 0) {
      // 함수 위치로 스크롤
      editor.revealLineInCenter(functionStartLine);

      // 함수 전체 하이라이트
      editor.deltaDecorations([], [
        {
          range: {
            startLineNumber: functionStartLine,
            startColumn: 1,
            endLineNumber: functionEndLine,
            endColumn: 1,
          },
          options: {
            isWholeLine: true,
            className: 'highlighted-function',
            glyphMarginClassName: 'highlighted-function-glyph',
          },
        },
      ]);

      // CSS 스타일 동적 추가
      const style = document.createElement('style');
      style.innerHTML = `
        .highlighted-function {
          background-color: rgba(255, 215, 0, 0.15) !important;
          border-left: 3px solid #ffa500;
        }
        .highlighted-function-glyph {
          background-color: #ffa500;
          width: 3px !important;
        }
      `;
      document.head.appendChild(style);
    }
  };

  const handleCloseCodeView = () => {
    setCodeViewModal({ visible: false, task: null, code: '', loading: false });
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
      title: 'Source',
      key: 'source',
      render: (_: any, record: Task) => {
        if (record.execution_mode === 'git') {
          return (
            <div style={{ fontSize: '12px' }}>
              <div style={{ marginBottom: '4px' }}>
                <Tag color="blue" icon={<GithubOutlined />}>
                  {record.git_repository?.split('/').pop()?.replace('.git', '') || 'Repository'}
                </Tag>
                {record.git_branch && (
                  <Tag color="green">branch: {record.git_branch}</Tag>
                )}
              </div>
              {record.git_commit_sha && (
                <div style={{ marginBottom: '4px' }}>
                  <Tag color="orange">SHA: {record.git_commit_sha.substring(0, 8)}</Tag>
                </div>
              )}
              <div style={{ color: '#666' }}>
                <code>{record.script_path}</code> → <strong>{record.function_name}()</strong>
              </div>
            </div>
          );
        }
        return <Tag color="cyan">Inline Python Code</Tag>;
      },
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
            icon={<EyeOutlined />}
            onClick={() => handleViewCode(record)}
          >
            View Code
          </Button>
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
    <>
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
      />

      <Modal
        title={
          <Space>
            {codeViewModal.task?.execution_mode === 'git' ? (
              <GithubOutlined style={{ color: '#1890ff' }} />
            ) : (
              <CodeOutlined style={{ color: '#52c41a' }} />
            )}
            <span>
              Task Source Code: {codeViewModal.task?.name}
              {codeViewModal.task?.function_name && (
                <span style={{ color: '#666', fontWeight: 'normal' }}>
                  {' → '}
                  <code style={{ color: '#d46b08' }}>{codeViewModal.task.function_name}()</code>
                </span>
              )}
            </span>
          </Space>
        }
        open={codeViewModal.visible}
        onCancel={handleCloseCodeView}
        footer={[
          <Button key="close" onClick={handleCloseCodeView}>
            Close
          </Button>,
        ]}
        width={900}
        styles={{ body: { padding: 0 } }}
      >
        {codeViewModal.loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="Loading code..." />
          </div>
        ) : (
          <div>
            {codeViewModal.task?.execution_mode === 'git' && (
              <div style={{ padding: '12px 16px', backgroundColor: '#f5f5f5', borderBottom: '1px solid #d9d9d9' }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <Tag color="blue" icon={<GithubOutlined />}>
                      {codeViewModal.task.git_repository?.split('/').pop()?.replace('.git', '')}
                    </Tag>
                    {codeViewModal.task.git_branch && (
                      <Tag color="green">branch: {codeViewModal.task.git_branch}</Tag>
                    )}
                    {codeViewModal.task.git_commit_sha && (
                      <Tag color="orange">SHA: {codeViewModal.task.git_commit_sha.substring(0, 8)}</Tag>
                    )}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    <code>{codeViewModal.task.script_path}</code>
                  </div>
                </Space>
              </div>
            )}
            <Editor
              height="500px"
              defaultLanguage="python"
              value={codeViewModal.code}
              theme="vs-light"
              onMount={handleEditorMount}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                glyphMargin: true,
              }}
            />
          </div>
        )}
      </Modal>
    </>
  );
}

export default TaskList;
