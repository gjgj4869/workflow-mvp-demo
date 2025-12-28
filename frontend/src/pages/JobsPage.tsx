import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Select,
  Statistic,
  Row,
  Col,
  Modal,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { jobApi, workflowApi, monitoringApi, type JobRun } from '@/services/api';
import LogViewer from '@/components/LogViewer';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(duration);
dayjs.extend(relativeTime);

function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [selectedJobRun, setSelectedJobRun] = useState<JobRun | undefined>();
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);

  // Fetch jobs
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: () => jobApi.list({ status_filter: statusFilter, limit: 100 }),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Fetch workflows for mapping
  const { data: workflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: workflowApi.list,
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: monitoringApi.stats,
    refetchInterval: 10000,
  });

  const getWorkflowName = (workflowId: string) => {
    const workflow = workflows?.find((w) => w.id === workflowId);
    return workflow?.name || workflowId;
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getStatusTag = (status: string) => {
    const statusLower = status.toLowerCase();
    const colorMap: Record<string, string> = {
      success: 'success',
      failed: 'error',
      running: 'processing',
      queued: 'default',
    };
    return (
      <Tag icon={getStatusIcon(status)} color={colorMap[statusLower] || 'default'}>
        {status.toUpperCase()}
      </Tag>
    );
  };

  const calculateDuration = (startedAt?: string, endedAt?: string) => {
    if (!startedAt) return '-';
    const start = dayjs(startedAt);
    const end = endedAt ? dayjs(endedAt) : dayjs();
    const diff = end.diff(start);
    return dayjs.duration(diff).format('HH:mm:ss');
  };

  const handleViewLogs = (jobRun: JobRun) => {
    setSelectedJobRun(jobRun);
    setIsLogModalOpen(true);
  };

  const columns = [
    {
      title: 'Workflow',
      dataIndex: 'workflow_id',
      key: 'workflow_id',
      render: (workflowId: string) => (
        <strong>{getWorkflowName(workflowId)}</strong>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Triggered By',
      dataIndex: 'triggered_by',
      key: 'triggered_by',
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date?: string) =>
        date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_: any, record: JobRun) =>
        calculateDuration(record.started_at, record.ended_at),
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
      render: (_: any, record: JobRun) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewLogs(record)}
        >
          View Logs
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Runs"
              value={stats?.job_runs.total || 0}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Recent (24h)"
              value={stats?.job_runs.recent_24h || 0}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={stats?.job_runs.success_rate || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Workflows"
              value={stats?.workflows.active || 0}
              prefix={<SyncOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Job Runs"
        extra={
          <Space>
            <span>Filter by status:</span>
            <Select
              style={{ width: 120 }}
              placeholder="All"
              allowClear
              onChange={setStatusFilter}
              options={[
                { label: 'Success', value: 'success' },
                { label: 'Failed', value: 'failed' },
                { label: 'Running', value: 'running' },
                { label: 'Queued', value: 'queued' },
              ]}
            />
          </Space>
        }
      >
        <Table
          dataSource={jobsData?.job_runs}
          columns={columns}
          rowKey="id"
          loading={jobsLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} job runs`,
          }}
        />
      </Card>

      {/* Log Viewer Modal */}
      {selectedJobRun && (
        <Modal
          title={`Job Logs - ${getWorkflowName(selectedJobRun.workflow_id)}`}
          open={isLogModalOpen}
          onCancel={() => {
            setIsLogModalOpen(false);
            setSelectedJobRun(undefined);
          }}
          footer={null}
          width={1000}
          styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
        >
          <LogViewer jobRunId={selectedJobRun.id} workflowId={selectedJobRun.workflow_id} />
        </Modal>
      )}
    </div>
  );
}

export default JobsPage;
