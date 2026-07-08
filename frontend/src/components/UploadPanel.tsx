import { ChangeEvent, useState } from "react";
import { AlertTriangle, FileText, Link2, Loader2, UploadCloud } from "lucide-react";
import { uploadPaper, UploadPaperResponse } from "../api";
import { documentTypeLabel, domainLabel } from "../documentMeta";

interface UploadPanelProps {
  paper: UploadPaperResponse | null;
  onUploaded: (response: UploadPaperResponse) => void;
}

function UploadPanel({ paper, onUploaded }: UploadPanelProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const response = await uploadPaper(file);
      onUploaded(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Step 1</p>
          <h2>上传论文 PDF</h2>
        </div>
        {uploading ? <Loader2 className="spin" size={20} /> : <UploadCloud size={20} />}
      </div>

      <label className="drop-zone">
        <input type="file" accept="application/pdf,.pdf" onChange={handleFileChange} />
        <UploadCloud size={28} />
        <span>{uploading ? "正在解析 PDF" : "选择论文 PDF"}</span>
      </label>

      {error && <p className="inline-error">{error}</p>}

      {paper && (
        <div className="paper-preview">
          <div className="preview-title">
            <FileText size={18} />
            <strong>{paper.title}</strong>
          </div>
          <p>{paper.abstract || "未识别到摘要，仍可基于全文片段继续分析。"}</p>
          <div className="meta-row">
            <span>{paper.paper_info.page_count} pages</span>
            <span>{paper.paper_info.sections.length} sections</span>
            <span>{paper.detected_resources.length} resources</span>
          </div>
          <div className={`upload-hint ${paper.document_hint.is_academic_paper ? "" : "warning"}`}>
            {!paper.document_hint.is_academic_paper && <AlertTriangle size={15} />}
            <span>{documentTypeLabel(paper.document_hint.document_type)}</span>
            <span>{domainLabel(paper.document_hint.domain)}</span>
            <span>{Math.round(paper.document_hint.confidence * 100)}%</span>
          </div>
          {paper.document_hint.warnings[0] && <p className="hint-copy">{paper.document_hint.warnings[0]}</p>}
          {paper.detected_resources.length > 0 && (
            <div className="resource-list compact">
              {paper.detected_resources.slice(0, 4).map((resource, index) => (
                <div className="resource-chip" key={`${resource.type}-${resource.url}-${index}`}>
                  <Link2 size={14} />
                  <span>{resource.type}</span>
                  <b>{Math.round(resource.confidence * 100)}%</b>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default UploadPanel;
