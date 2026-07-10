import { useState } from "react";
import { Activity, CheckCircle2, FileSearch, GitBranch, UploadCloud } from "lucide-react";
import {
  analyzePaper,
  AnalyzeMode,
  AnalysisDomain,
  AnalysisResult,
  KnowledgeProfile,
  uploadExtra,
  UploadPaperResponse
} from "./api";
import AnalysisDashboard from "./components/AnalysisDashboard";
import ResourceDecisionPanel from "./components/ResourceDecisionPanel";
import UploadPanel from "./components/UploadPanel";

type Stage = "upload" | "decision" | "analysis";

const flowSteps = [
  { key: "upload", label: "上传论文", icon: UploadCloud },
  { key: "decision", label: "方向与知识", icon: GitBranch },
  { key: "analysis", label: "复现分析", icon: FileSearch }
];

function App() {
  const [stage, setStage] = useState<Stage>("upload");
  const [paper, setPaper] = useState<UploadPaperResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUploaded = (response: UploadPaperResponse) => {
    setPaper(response);
    setAnalysis(null);
    setError(null);
    setStage("decision");
  };

  const handleAnalyze = async (
    mode: AnalyzeMode,
    analysisDomain: AnalysisDomain,
    knowledgeProfile: KnowledgeProfile
  ) => {
    if (!paper) return;
    setLoadingAnalysis(true);
    setError(null);
    try {
      const response = await analyzePaper(paper.paper_id, mode, analysisDomain, knowledgeProfile);
      setAnalysis(response.analysis);
      setStage("analysis");
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleUploadExtraAndAnalyze = async (
    files: FileList | File[],
    analysisDomain: AnalysisDomain,
    knowledgeProfile: KnowledgeProfile
  ) => {
    if (!paper) return;
    setLoadingAnalysis(true);
    setError(null);
    try {
      await uploadExtra(paper.paper_id, files);
      const response = await analyzePaper(paper.paper_id, "with_extra_materials", analysisDomain, knowledgeProfile);
      setAnalysis(response.analysis);
      setStage("analysis");
    } catch (err) {
      setError(err instanceof Error ? err.message : "补充材料上传或分析失败");
    } finally {
      setLoadingAnalysis(false);
    }
  };

  return (
    <main className="app-shell">
      <section className="app-header">
        <div>
          <p className="eyebrow">Research Reproduction MVP</p>
          <h1>Read2Reproduce</h1>
          <p className="subtitle">From Paper Reading to Reproducible Research</p>
          <p className="cn-copy">面向本科生科研入门的论文阅读与实验复现辅助平台。</p>
        </div>
        <div className="status-panel">
          <Activity size={18} />
          <span>Mock-first workflow</span>
        </div>
      </section>

      <nav className="flow-nav" aria-label="Workflow">
        {flowSteps.map((step, index) => {
          const Icon = step.icon;
          const currentIndex = flowSteps.findIndex((item) => item.key === stage);
          const isDone = index < currentIndex;
          const isActive = step.key === stage;
          return (
            <div className={`flow-step ${isActive ? "active" : ""} ${isDone ? "done" : ""}`} key={step.key}>
              {isDone ? <CheckCircle2 size={18} /> : <Icon size={18} />}
              <span>{step.label}</span>
            </div>
          );
        })}
      </nav>

      <section className="workspace-grid">
        <UploadPanel onUploaded={handleUploaded} paper={paper} />
        {paper && (
          <ResourceDecisionPanel
            paper={paper}
            loading={loadingAnalysis}
            onAnalyze={handleAnalyze}
            onUploadExtraAndAnalyze={handleUploadExtraAndAnalyze}
          />
        )}
      </section>

      {error && <div className="error-banner">{error}</div>}

      {analysis && <AnalysisDashboard analysis={analysis} />}
    </main>
  );
}

export default App;
