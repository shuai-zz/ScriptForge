import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface CharacterItem {
  id: string;
  name: string;
  role_type: string;
}

interface RelationshipItem {
  id: string;
  source_character_id: string;
  target_character_id: string;
  type: string;
  intensity: number;
}

interface CharacterGraphProps {
  characters: CharacterItem[];
  relationships: RelationshipItem[];
}

const ROLE_NODE_COLORS: Record<string, string> = {
  protagonist: "#d4a853",
  antagonist: "#e5534b",
  supporting: "#5b8c85",
  minor: "#5c5a66",
};

function CharacterNode({ data }: { data: { name: string; role_type: string } }) {
  const color = ROLE_NODE_COLORS[data.role_type] || ROLE_NODE_COLORS.minor;
  return (
    <div
      className="rounded-lg border px-4 py-2 text-center shadow-md"
      style={{
        borderColor: color,
        backgroundColor: `${color}20`,
        minWidth: 100,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color }} />
      <div className="text-sm font-medium" style={{ color }}>
        {data.name}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </div>
  );
}

const nodeTypes = { character: CharacterNode };

export default function CharacterGraph({ characters, relationships }: CharacterGraphProps) {
  const nodes: Node[] = useMemo(() => {
    const count = characters.length;
    const radius = Math.max(200, count * 60);
    const centerX = 400;
    const centerY = 300;

    return characters.map((c, i) => {
      const angle = (2 * Math.PI * i) / Math.max(count, 1) - Math.PI / 2;
      return {
        id: c.id,
        type: "character",
        position: {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        },
        data: { name: c.name, role_type: c.role_type },
      };
    });
  }, [characters]);

  const edges: Edge[] = useMemo(() => {
    return relationships.map((r) => ({
      id: r.id,
      source: r.source_character_id,
      target: r.target_character_id,
      label: `${r.type} (${r.intensity})`,
      animated: r.intensity >= 4,
      style: {
        stroke: r.intensity >= 4 ? "#d4a853" : "#5c5a66",
        strokeWidth: Math.max(1, r.intensity / 2),
      },
      labelStyle: {
        fill: "#9895a0",
        fontSize: 10,
      },
    }));
  }, [relationships]);

  return (
    <div className="flex-1" style={{ background: "#0b0b12" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#5c5a66" gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => ROLE_NODE_COLORS[(node.data as any)?.role_type] || "#5c5a66"}
          maskColor="rgba(11, 11, 18, 0.8)"
          className="bg-surface"
        />
      </ReactFlow>
    </div>
  );
}
