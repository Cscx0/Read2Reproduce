import { ChangeEvent, useEffect, useState } from "react";
import {
  AlertTriangle,
  Atom,
  BookOpenCheck,
  Calculator,
  Code2,
  Dna,
  FileUp,
  FlaskConical,
  GitBranch,
  Landmark,
  Loader2,
  Play,
  ScrollText,
  SearchCode,
  Stethoscope,
  Users,
  Wrench
} from "lucide-react";
import { AnalysisDomain, AnalyzeMode, UploadPaperResponse } from "../api";
import { domainLabel } from "../documentMeta";

interface ResourceDecisionPanelProps {
  paper: UploadPaperResponse;
  loading: boolean;
  onAnalyze: (mode: AnalyzeMode, analysisDomain: AnalysisDomain) => void;
  onUploadExtraAndAnalyze: (files: FileList | File[], analysisDomain: AnalysisDomain) => void;
}

const domainOptions: Array<{ value: AnalysisDomain; label: string; icon: typeof BookOpenCheck }> = [
  { value: "computer_science", label: "计算机", icon: Code2 },
  { value: "physics", label: "物理", icon: Atom },
  { value: "mathematics", label: "数学", icon: Calculator },
  { value: "chemistry", label: "化学", icon: FlaskConical },
  { value: "biology", label: "生物", icon: Dna },
  { value: "medicine", label: "医学", icon: Stethoscope },
  { value: "economics", label: "经济", icon: Landmark },
  { value: "social_science", label: "社科", icon: Users },
  { value: "engineering", label: "工程", icon: Wrench },
  { value: "humanities", label: "人文", icon: ScrollText },
  { value: "general", label: "通用", icon: BookOpenCheck }
];

function ResourceDecisionPanel({
  paper,
  loading,
  onAnalyze,
  onUploadExtraAndAnalyze
}: ResourceDecisionPanelProps) {
  const [extraFiles, setExtraFiles] = useState<FileList | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<AnalysisDomain>(() => defaultDomain(paper.document_hint.domain));

  useEffect(() => {
    setSelectedDomain(defaultDomain(paper.document_hint.domain));
    setExtraFiles(null);
  }, [paper.paper_id, paper.document_hint.domain]);

  const handleExtraChange = (event: ChangeEvent<HTMLInputElement>) => {
    setExtraFiles(event.target.files);
  };

  const hasCode = paper.has_code_resource && selectedDomain === "computer_science";
  const isAcademic = paper.document_hint.is_academic_paper;
  const selectedLabel = domainLabel(selectedDomain);
  const recommended = defaultDomain(paper.document_hint.domain);

  return (
    <section className="panel decision-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Step 2</p>
          <h2>选择分析范围</h2>
        </div>
        {loading ? <Loader2 className="spin" size={20} /> : <SearchCode size={20} />}
      </div>

      <section className="domain-picker" aria-label="选择分析方向">
        <div className="domain-picker-heading">
          <strong>分析方向</strong>
          <span>默认：{domainLabel(recommended)}</span>
        </div>
        <div className="domain-grid">
          {domainOptions.map((option) => {
            const Icon = option.icon;
            const active = selectedDomain === option.value;
            return (
              <button
                className={active ? "domain-button active" : "domain-button"}
                key={option.value}
                onClick={() => setSelectedDomain(option.value)}
                type="button"
              >
                <Icon size={16} />
                <span>{option.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {!isAcademic ? (
        <>
          <p className="decision-copy warning-copy">
            <AlertTriangle size={16} />
            当前文件不像可复现分析所需的论文正文。可先查看诊断结果，或补充 OCR/正文材料后按{selectedLabel}方向分析。
          </p>
          <label className="extra-upload">
            <input type="file" multiple accept=".txt,.md,.pdf,.zip" onChange={handleExtraChange} />
            <FileUp size={18} />
            <span>{extraFiles?.length ? `${extraFiles.length} 个补充文件` : "上传补充资料"}</span>
          </label>
          <div className="button-row">
            <button
              className="primary-button"
              disabled={loading || !extraFiles?.length}
              onClick={() => extraFiles && onUploadExtraAndAnalyze(extraFiles, selectedDomain)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <FileUp size={16} />}
              结合补充资料分析
            </button>
            <button className="secondary-button" disabled={loading} onClick={() => onAnalyze("paper_only", selectedDomain)}>
              <Play size={16} />
              查看诊断结果
            </button>
          </div>
        </>
      ) : hasCode ? (
        <>
          <p className="decision-copy">已选择计算机科学方向，并检测到代码资源。可以结合仓库信息分析，也可以只基于论文正文。</p>
          <div className="resource-list">
            {paper.detected_resources.map((resource, index) => (
              <div className="resource-row" key={`${resource.type}-${resource.url}-${index}`}>
                <GitBranch size={16} />
                <div>
                  <strong>{resource.type}</strong>
                  <span>{resource.url || resource.note}</span>
                </div>
                <b>{Math.round(resource.confidence * 100)}%</b>
              </div>
            ))}
          </div>
          <div className="button-row">
            <button
              className="primary-button"
              disabled={loading}
              onClick={() => onAnalyze("with_detected_resources", selectedDomain)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <GitBranch size={16} />}
              结合仓库分析
            </button>
            <button className="secondary-button" disabled={loading} onClick={() => onAnalyze("paper_only", selectedDomain)}>
              <Play size={16} />
              只分析论文
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="decision-copy">
            将按{selectedLabel}方向分析。{selectedDomain === "computer_science" ? "未检测到明确代码资源。" : "该方向不需要代码仓库。"}
            你可以上传补充资料，或直接基于论文内容分析。
          </p>
          <label className="extra-upload">
            <input type="file" multiple accept=".txt,.md,.pdf,.zip" onChange={handleExtraChange} />
            <FileUp size={18} />
            <span>{extraFiles?.length ? `${extraFiles.length} 个补充文件` : "上传补充资料"}</span>
          </label>
          <div className="button-row">
            <button
              className="primary-button"
              disabled={loading || !extraFiles?.length}
              onClick={() => extraFiles && onUploadExtraAndAnalyze(extraFiles, selectedDomain)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <FileUp size={16} />}
              结合补充资料分析
            </button>
            <button className="secondary-button" disabled={loading} onClick={() => onAnalyze("paper_only", selectedDomain)}>
              <Play size={16} />
              直接分析论文
            </button>
          </div>
        </>
      )}
    </section>
  );
}

function defaultDomain(domain: string): AnalysisDomain {
  const values = new Set(domainOptions.map((option) => option.value));
  return values.has(domain as AnalysisDomain) ? (domain as AnalysisDomain) : "general";
}

export default ResourceDecisionPanel;
