import { useState } from "react";
import { Check, Circle } from "lucide-react";
import { ChecklistItem } from "../api";

interface ChecklistViewProps {
  items: ChecklistItem[];
}

function ChecklistView({ items }: ChecklistViewProps) {
  const [localItems, setLocalItems] = useState(items);

  const toggleItem = (stepId: string) => {
    setLocalItems((current) =>
      current.map((item) =>
        item.step_id === stepId ? { ...item, status: item.status === "done" ? "pending" : "done" } : item
      )
    );
  };

  const doneCount = localItems.filter((item) => item.status === "done").length;

  return (
    <div className="checklist-view">
      <div className="progress-line">
        <span>
          {doneCount}/{localItems.length} completed
        </span>
        <div>
          <i style={{ width: `${(doneCount / Math.max(localItems.length, 1)) * 100}%` }} />
        </div>
      </div>
      <div className="checklist-list">
        {localItems.map((item) => (
          <button
            className={`checklist-item ${item.status === "done" ? "done" : ""}`}
            key={item.step_id}
            onClick={() => toggleItem(item.step_id)}
          >
            <span className="check-icon">{item.status === "done" ? <Check size={18} /> : <Circle size={18} />}</span>
            <span className="check-content">
              <strong>{item.title}</strong>
              <span>{item.description}</span>
              <small>{item.expected_output}</small>
              <em>{item.required_files.join(", ") || "No required files"}</em>
            </span>
            <b className={`difficulty-pill ${item.difficulty}`}>{item.difficulty}</b>
          </button>
        ))}
      </div>
    </div>
  );
}

export default ChecklistView;

