import { ArrowRight } from "lucide-react";
import { GraphEdge, GraphNode } from "../api";

interface MethodFlowViewProps {
  flow: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

function MethodFlowView({ flow }: MethodFlowViewProps) {
  const edgeLookup = new Map(flow.edges.map((edge) => [`${edge.source}-${edge.target}`, edge.label]));

  return (
    <div className="method-flow">
      <div className="flow-row-large">
        {flow.nodes.map((node, index) => {
          const next = flow.nodes[index + 1];
          const label = next ? edgeLookup.get(`${node.id}-${next.id}`) : null;
          return (
            <div className="flow-node-wrap" key={node.id}>
              <div className="flow-node">
                <span>{node.type || "step"}</span>
                <strong>{node.label}</strong>
              </div>
              {next && (
                <div className="flow-arrow">
                  <ArrowRight size={22} />
                  {label && <small>{label}</small>}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="edge-list">
        {flow.edges.map((edge) => (
          <div key={`${edge.source}-${edge.target}-${edge.label}`}>
            <span>{labelFor(flow.nodes, edge.source)}</span>
            <ArrowRight size={14} />
            <span>{labelFor(flow.nodes, edge.target)}</span>
            {edge.label && <b>{edge.label}</b>}
          </div>
        ))}
      </div>
    </div>
  );
}

function labelFor(nodes: GraphNode[], id: string) {
  return nodes.find((node) => node.id === id)?.label ?? id;
}

export default MethodFlowView;

