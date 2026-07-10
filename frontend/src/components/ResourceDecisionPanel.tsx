import { ChangeEvent, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Atom,
  BookOpenCheck,
  Calculator,
  CheckCircle2,
  Circle,
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
import {
  AnalysisDomain,
  AnalyzeMode,
  fetchPrerequisiteTerms,
  KnowledgeLevel,
  KnowledgeProfile,
  PrerequisiteTerm,
  UploadPaperResponse
} from "../api";
import { domainLabel } from "../documentMeta";

interface ResourceDecisionPanelProps {
  paper: UploadPaperResponse;
  loading: boolean;
  onAnalyze: (mode: AnalyzeMode, analysisDomain: AnalysisDomain, knowledgeProfile: KnowledgeProfile) => void;
  onUploadExtraAndAnalyze: (
    files: FileList | File[],
    analysisDomain: AnalysisDomain,
    knowledgeProfile: KnowledgeProfile
  ) => void;
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

const knowledgeLevelOptions: Array<{ value: KnowledgeLevel; label: string; description: string }> = [
  { value: "beginner", label: "入门", description: "希望先补基础概念，少一些默认术语。" },
  { value: "intermediate", label: "有基础", description: "了解一些领域语言，需要补关键连接。" },
  { value: "advanced", label: "熟悉", description: "概念不必展开太多，重点看假设和细节。" }
];

const difficultyLabels: Record<PrerequisiteTerm["difficulty"], string> = {
  low: "基础",
  medium: "进阶",
  high: "高阶"
};

function ResourceDecisionPanel({
  paper,
  loading,
  onAnalyze,
  onUploadExtraAndAnalyze
}: ResourceDecisionPanelProps) {
  const [extraFiles, setExtraFiles] = useState<FileList | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<AnalysisDomain>(() => defaultDomain(paper.document_hint.domain));
  const [knowledgeLevel, setKnowledgeLevel] = useState<KnowledgeLevel>("intermediate");
  const [terms, setTerms] = useState<PrerequisiteTerm[]>([]);
  const [knownTerms, setKnownTerms] = useState<Set<string>>(new Set());
  const [termsLoading, setTermsLoading] = useState(false);
  const [termsError, setTermsError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedDomain(defaultDomain(paper.document_hint.domain));
    setKnowledgeLevel("intermediate");
    setExtraFiles(null);
    setTerms([]);
    setKnownTerms(new Set());
    setTermsError(null);
  }, [paper.paper_id, paper.document_hint.domain]);

  useEffect(() => {
    let cancelled = false;
    setTermsLoading(true);
    setTermsError(null);
    fetchPrerequisiteTerms(paper.paper_id, selectedDomain, knowledgeLevel)
      .then((response) => {
        if (cancelled) return;
        setTerms(response.terms);
        setKnownTerms(defaultKnownTerms(response.terms, knowledgeLevel));
      })
      .catch((err) => {
        if (cancelled) return;
        setTerms([]);
        setKnownTerms(new Set());
        setTermsError(err instanceof Error ? err.message : "前置知识提取失败");
      })
      .finally(() => {
        if (!cancelled) setTermsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [paper.paper_id, selectedDomain, knowledgeLevel]);

  const handleExtraChange = (event: ChangeEvent<HTMLInputElement>) => {
    setExtraFiles(event.target.files);
  };

  const toggleKnownTerm = (term: string) => {
    setKnownTerms((current) => {
      const next = new Set(current);
      if (next.has(term)) {
        next.delete(term);
      } else {
        next.add(term);
      }
      return next;
    });
  };

  const knowledgeProfile = useMemo<KnowledgeProfile>(() => {
    const known = terms.filter((term) => knownTerms.has(term.term)).map((term) => term.term);
    const unknown = terms.filter((term) => !knownTerms.has(term.term)).map((term) => term.term);
    return {
      level: knowledgeLevel,
      known_terms: known,
      unknown_terms: unknown
    };
  }, [knowledgeLevel, knownTerms, terms]);

  const hasCode = paper.has_code_resource && selectedDomain === "computer_science";
  const isAcademic = paper.document_hint.is_academic_paper;
  const selectedLabel = domainLabel(selectedDomain);
  const recommended = defaultDomain(paper.document_hint.domain);
  const disableAnalyze = loading || termsLoading;

  return (
    <section className="panel decision-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Step 2</p>
          <h2>选择方向与知识准备</h2>
        </div>
        {loading || termsLoading ? <Loader2 className="spin" size={20} /> : <SearchCode size={20} />}
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

      <KnowledgePreparation
        knownTerms={knownTerms}
        knowledgeLevel={knowledgeLevel}
        loading={termsLoading}
        error={termsError}
        terms={terms}
        onLevelChange={setKnowledgeLevel}
        onToggleKnown={toggleKnownTerm}
      />

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
              disabled={disableAnalyze || !extraFiles?.length}
              onClick={() => extraFiles && onUploadExtraAndAnalyze(extraFiles, selectedDomain, knowledgeProfile)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <FileUp size={16} />}
              结合补充资料分析
            </button>
            <button
              className="secondary-button"
              disabled={disableAnalyze}
              onClick={() => onAnalyze("paper_only", selectedDomain, knowledgeProfile)}
            >
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
              disabled={disableAnalyze}
              onClick={() => onAnalyze("with_detected_resources", selectedDomain, knowledgeProfile)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <GitBranch size={16} />}
              结合仓库分析
            </button>
            <button
              className="secondary-button"
              disabled={disableAnalyze}
              onClick={() => onAnalyze("paper_only", selectedDomain, knowledgeProfile)}
            >
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
              disabled={disableAnalyze || !extraFiles?.length}
              onClick={() => extraFiles && onUploadExtraAndAnalyze(extraFiles, selectedDomain, knowledgeProfile)}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <FileUp size={16} />}
              结合补充资料分析
            </button>
            <button
              className="secondary-button"
              disabled={disableAnalyze}
              onClick={() => onAnalyze("paper_only", selectedDomain, knowledgeProfile)}
            >
              <Play size={16} />
              直接分析论文
            </button>
          </div>
        </>
      )}
    </section>
  );
}

function KnowledgePreparation({
  knownTerms,
  knowledgeLevel,
  loading,
  error,
  terms,
  onLevelChange,
  onToggleKnown
}: {
  knownTerms: Set<string>;
  knowledgeLevel: KnowledgeLevel;
  loading: boolean;
  error: string | null;
  terms: PrerequisiteTerm[];
  onLevelChange: (level: KnowledgeLevel) => void;
  onToggleKnown: (term: string) => void;
}) {
  return (
    <section className="knowledge-panel" aria-label="前置知识确认">
      <div className="knowledge-heading">
        <div>
          <strong>你的领域知识水平</strong>
          <span>agent 会按这份画像调整讲解深度</span>
        </div>
        <span>{terms.length ? `${knownTerms.size}/${terms.length} 已掌握` : "等待术语"}</span>
      </div>

      <div className="knowledge-level-grid">
        {knowledgeLevelOptions.map((option) => (
          <button
            className={knowledgeLevel === option.value ? "level-button active" : "level-button"}
            key={option.value}
            type="button"
            onClick={() => onLevelChange(option.value)}
          >
            <strong>{option.label}</strong>
            <span>{option.description}</span>
          </button>
        ))}
      </div>

      <div className="prerequisite-heading">
        <strong>论文前置知识词语</strong>
        <span>点一下表示“我知道”，未选会按“不熟”处理</span>
      </div>

      {loading ? (
        <p className="terms-status">
          <Loader2 className="spin" size={16} />
          正在从论文中提取前置术语…
        </p>
      ) : error ? (
        <p className="terms-status warning">
          <AlertTriangle size={16} />
          {error}，仍可继续分析。
        </p>
      ) : terms.length ? (
        <div className="term-grid">
          {terms.map((term) => {
            const known = knownTerms.has(term.term);
            return (
              <button
                aria-pressed={known}
                className={known ? "term-card known" : "term-card"}
                key={`${term.term}-${term.category}`}
                type="button"
                onClick={() => onToggleKnown(term.term)}
              >
                <span className="term-card-top">
                  <strong>{term.term}</strong>
                  <b className={`difficulty-pill ${term.difficulty}`}>{difficultyLabels[term.difficulty]}</b>
                </span>
                <small>{term.category}</small>
                <p>{term.why_it_matters}</p>
                <span className="term-known-state">
                  {known ? <CheckCircle2 size={15} /> : <Circle size={15} />}
                  {known ? "我知道" : "我还不熟"}
                </span>
              </button>
            );
          })}
        </div>
      ) : (
        <p className="terms-status">暂未抽取到稳定术语，agent 会按你的知识水平直接讲解。</p>
      )}
    </section>
  );
}

function defaultKnownTerms(terms: PrerequisiteTerm[], level: KnowledgeLevel): Set<string> {
  const knownDifficulties: Record<KnowledgeLevel, Array<PrerequisiteTerm["difficulty"]>> = {
    beginner: [],
    intermediate: ["low"],
    advanced: ["low", "medium"]
  };
  return new Set(
    terms.filter((term) => knownDifficulties[level].includes(term.difficulty)).map((term) => term.term)
  );
}

function defaultDomain(domain: string): AnalysisDomain {
  const values = new Set(domainOptions.map((option) => option.value));
  return values.has(domain as AnalysisDomain) ? (domain as AnalysisDomain) : "general";
}

export default ResourceDecisionPanel;
