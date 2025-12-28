import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { type Task } from '@/services/api';
import { Empty } from 'antd';

interface TaskGraphProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
}

function TaskGraph({ tasks, onTaskClick }: TaskGraphProps) {
  // Convert tasks to nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (tasks.length === 0) {
      return { nodes: [], edges: [] };
    }

    // Create nodes
    const nodes: Node[] = tasks.map((task, index) => {
      // Simple grid layout
      const row = Math.floor(index / 3);
      const col = index % 3;

      return {
        id: task.name,
        type: 'default',
        data: {
          label: (
            <div>
              <strong>{task.name}</strong>
              <br />
              <small>Retries: {task.retry_count}</small>
            </div>
          ),
        },
        position: {
          x: col * 250,
          y: row * 150,
        },
      };
    });

    // Create edges from dependencies
    const edges: Edge[] = [];
    tasks.forEach((task) => {
      if (task.dependencies && task.dependencies.length > 0) {
        task.dependencies.forEach((dep) => {
          edges.push({
            id: `${dep}-${task.name}`,
            source: dep,
            target: task.name,
            animated: true,
            style: { stroke: '#1890ff' },
          });
        });
      }
    });

    return { nodes, edges };
  }, [tasks]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const task = tasks.find((t) => t.name === node.id);
      if (task && onTaskClick) {
        onTaskClick(task);
      }
    },
    [tasks, onTaskClick]
  );

  if (tasks.length === 0) {
    return (
      <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Empty description="No tasks to display" />
      </div>
    );
  }

  return (
    <div style={{ height: 500 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}

export default TaskGraph;
