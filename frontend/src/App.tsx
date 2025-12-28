import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  ProjectOutlined,
  PlayCircleOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import WorkflowsPage from './pages/WorkflowsPage';
import WorkflowDetailPage from './pages/WorkflowDetailPage';
import JobsPage from './pages/JobsPage';

const { Header, Content } = Layout;

function App() {
  const location = useLocation();

  const menuItems = [
    {
      key: '/workflows',
      icon: <ProjectOutlined />,
      label: <Link to="/workflows">Workflows</Link>,
    },
    {
      key: '/jobs',
      icon: <PlayCircleOutlined />,
      label: <Link to="/jobs">Jobs</Link>,
    },
  ];

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="app-logo">
          <DashboardOutlined style={{ marginRight: 8 }} />
          MLOps Workflow Manager
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname.split('/')[1] ? `/${location.pathname.split('/')[1]}` : '/workflows']}
          items={menuItems}
          style={{ flex: 1, minWidth: 0, justifyContent: 'flex-end' }}
        />
      </Header>
      <Content className="app-content">
        <Routes>
          <Route path="/" element={<WorkflowsPage />} />
          <Route path="/workflows" element={<WorkflowsPage />} />
          <Route path="/workflows/:id" element={<WorkflowDetailPage />} />
          <Route path="/jobs" element={<JobsPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
