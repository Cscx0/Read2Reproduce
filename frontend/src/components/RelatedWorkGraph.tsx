import { ArrowRight, Network } from "lucide-react";
import { GraphEdge, GraphNode } from "../api";

interface RelatedWorkGraphProps {
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

function RelatedWorkGraph({ graph }: RelatedWorkGraphProps) {
  return (
    <div className="related-work">
      <div className="node-cloud">
        {graph.nodes.map((node) => (
          <div className="related-node" key={node.id}>
            <Network size={15} />
            <strong>{node.label}</strong>
            {node.type && <span>{node.type}</span>}
          </div>
        ))}
      </div>
      <div className="relation-list">
        {graph.edges.map((edge) => (
          <RelationRow edge={edge} nodes={graph.nodes} key={`${edge.source}-${edge.target}-${edge.label}`} />
        ))}
      </div>
    </div>
  );
}

function RelationRow({ edge, nodes }: { edge: GraphEdge; nodes: GraphNode[] }) {
  return (
    <div className="relation-row">
      <span>{labelFor(nodes, edge.source)}</span>
      <ArrowRight size={15} />
      <span>{labelFor(nodes, edge.target)}</span>
      {edge.label && <b>{edge.label}</b>}
    </div>
  );
}

function labelFor(nodes: GraphNode[], id: string) {
  return nodes.find((node) => node.id === id)?.label ?? id;
}

export default RelatedWorkGraph;

