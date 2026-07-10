import { useState } from "react";
import {
  AlertTriangle,
  Beaker,
  Binary,
  BookOpen,
  CheckSquare,
  FileSearch,
  FunctionSquare,
  GitFork,
  Network,
  Table2
} from "lucide-react";
import { AnalysisResult, DocumentAnalysisMeta, KnowledgeAdaptation } from "../api";
import { documentTypeLabel, domainLabel } from "../documentMeta";
import ChecklistView from "./ChecklistView";
import ExperimentTable from "./ExperimentTable";
import FormulaCard from "./FormulaCard";
import MethodFlowView from "./MethodFlowView";
import RelatedWorkGraph from "./RelatedWorkGraph";
import RepoGuideView from "./RepoGuideView";
import SummaryCard from "./SummaryCard";

interface AnalysisDashboardProps {
  analysis: AnalysisResult;
}

const tabs = [
  { id: "summary", label: "结构化总结", icon: BookOpen },
  { id: "flow", label: "方法流程", icon: GitFork },
  { id: "formulas", label: "关键公式", icon: FunctionSquare },
  { id: "experiments", label: "实验设置", icon: Beaker },
  { id: "tables", label: "实体表格", icon: Table2 },
  { id: "related", label: "相关工作图", icon: Network },
  { id: "checklist", label: "复现 Checklist", icon: CheckSquare },
  { id: "repo", label: "仓库阅读", icon: Binary }
] as const;

type TabId = (typeof tabs)[number]["id"];

function AnalysisDashboard({ analysis }: AnalysisDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const meta = analysis.metadata;

  return (
    <section className="analysis-section">
      <div className="analysis-title">
        <div>
          <p className="section-kicker">Step 3</p>
          <h2>复现分析结果</h2>
        </div>
        <span className={`difficulty-pill ${analysis.structured_summary.reproduction_difficulty}`}>
          {analysis.structured_summary.reproduction_difficulty}
        </span>
      </div>

      <DocumentMetaPanel meta={meta} />
      {analysis.knowledge_adaptation && <KnowledgeAdaptationPanel profile={analysis.knowledge_adaptation} />}

      <div className="tab-strip" role="tablist" aria-label="Analysis tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              className={activeTab === tab.id ? "tab-button active" : "tab-button"}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              aria-selected={activeTab === tab.id}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="tab-panel">
        {activeTab === "summary" && <SummaryCard summary={analysis.structured_summary} />}
        {activeTab === "flow" && <MethodFlowView flow={analysis.method_flow} />}
        {activeTab === "formulas" && <FormulaCard formulas={analysis.formulas} />}
        {activeTab === "experiments" && (
          <ExperimentTable
            settings={analysis.experiment_settings}
            tables={analysis.entity_tables}
            view="settings"
            metadata={meta}
          />
        )}
        {activeTab === "tables" && (
          <ExperimentTable
            settings={analysis.experiment_settings}
            tables={analysis.entity_tables}
            view="tables"
            metadata={meta}
          />
        )}
        {activeTab === "related" && <RelatedWorkGraph graph={analysis.related_work_graph} />}
        {activeTab === "checklist" && <ChecklistView items={analysis.reproduction_checklist} />}
        {activeTab === "repo" && <RepoGuideView guide={analysis.repo_guide} />}
      </div>
    </section>
  );
}

function KnowledgeAdaptationPanel({ profile }: { profile: KnowledgeAdaptation }) {
  const levelLabel = {
    beginner: "入门",
    intermediate: "有基础",
    advanced: "熟悉"
  }[profile.level];

  return (
    <div className="knowledge-adaptation-panel">
      <div className="document-meta-main">
        <BookOpen size={18} />
        <div>
          <strong>已按“{levelLabel}”知识水平调整讲解</strong>
          <span>{profile.explanation_strategy}</span>
        </div>
      </div>
      <div className="knowledge-adaptation-tags">
        {profile.known_terms.slice(0, 6).map((term) => (
          <span className="known" key={`known-${term}`}>
            已掌握：{term}
          </span>
        ))}
        {profile.unknown_terms.slice(0, 6).map((term) => (
          <span className="unknown" key={`unknown-${term}`}>
            待补齐：{term}
          </span>
        ))}
      </div>
    </div>
  );
}

function DocumentMetaPanel({ meta }: { meta: DocumentAnalysisMeta }) {
  const confidence = Math.round(meta.confidence * 100);
  const warning = meta.warnings[0] ?? (!meta.is_academic_paper ? "当前材料不适合作为论文复现分析。" : null);

  return (
    <div className={`document-meta-panel ${meta.is_academic_paper ? "" : "warning"}`}>
      <div className="document-meta-main">
        {meta.is_academic_paper ? <FileSearch size={18} /> : <AlertTriangle size={18} />}
        <div>
          <strong>{meta.is_academic_paper ? "已识别为学术材料" : "未识别为有效论文"}</strong>
          <span>{meta.guidance}</span>
        </div>
      </div>
      <div className="document-meta-tags">
        <span>{documentTypeLabel(meta.document_type)}</span>
        <span>{domainLabel(meta.domain)}</span>
        <span>{confidence}%</span>
      </div>
      {warning && <p>{warning}</p>}
    </div>
  );
}

export default AnalysisDashboard;
