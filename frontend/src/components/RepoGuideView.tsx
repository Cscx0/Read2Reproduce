import { AlertTriangle, CheckCircle2, Terminal } from "lucide-react";
import { RepoGuide } from "../api";

interface RepoGuideViewProps {
  guide: RepoGuide;
}

function RepoGuideView({ guide }: RepoGuideViewProps) {
  if (!guide.available) {
    return (
      <div className="empty-state">
        <AlertTriangle size={24} />
        <h3>暂无可读取仓库</h3>
        <p>{guide.message || "论文中未检测到代码仓库，建议上传补充材料或手动提供仓库链接。"}</p>
      </div>
    );
  }

  return (
    <div className="repo-guide">
      <section className="summary-block wide">
        <h3>Repo Summary</h3>
        <p>{guide.repo_summary}</p>
      </section>
      <GuideList title="Important Files" values={guide.important_files} />
      <GuideList title="Entry Points" values={guide.entry_points} />
      <GuideList title="Dependency Files" values={guide.dependency_files} />
      <GuideList title="Training Scripts" values={guide.training_scripts} />
      <GuideList title="Evaluation Scripts" values={guide.evaluation_scripts} />
      <GuideList title="Config Files" values={guide.config_files} />
      <section className="summary-block wide">
        <h3>Likely Commands</h3>
        <div className="command-list">
          {guide.likely_reproduction_commands.map((command) => (
            <code key={command}>
              <Terminal size={14} />
              {command}
            </code>
          ))}
        </div>
      </section>
      <section className="summary-block wide">
        <h3>Risks</h3>
        <ul className="clean-list">
          {guide.risks.map((risk) => (
            <li key={risk}>{risk}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function GuideList({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="summary-block">
      <h3>{title}</h3>
      <div className="file-list">
        {values.map((value) => (
          <span key={value}>
            <CheckCircle2 size={14} />
            {value}
          </span>
        ))}
      </div>
    </section>
  );
}

export default RepoGuideView;

