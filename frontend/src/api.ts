export type AnalyzeMode = "paper_only" | "with_detected_resources" | "with_extra_materials";
export type AnalysisDomain =
  | "auto"
  | "computer_science"
  | "physics"
  | "mathematics"
  | "chemistry"
  | "biology"
  | "medicine"
  | "economics"
  | "social_science"
  | "engineering"
  | "humanities"
  | "general";
export type Difficulty = "low" | "medium" | "high";

export interface DetectedResource {
  type: string;
  url: string;
  confidence: number;
  note?: string | null;
}

export interface PaperBasicInfo {
  title: string;
  abstract: string;
  sections: string[];
  page_count: number;
}

export interface UploadPaperResponse {
  paper_id: string;
  title: string;
  abstract: string;
  detected_resources: DetectedResource[];
  has_code_resource: boolean;
  paper_info: PaperBasicInfo;
  document_hint: DocumentAnalysisMeta;
}

export interface DocumentAnalysisMeta {
  document_type: string;
  domain: string;
  is_academic_paper: boolean;
  confidence: number;
  signals: string[];
  warnings: string[];
  guidance: string;
}

export interface StructuredSummary {
  background: string;
  problem: string;
  motivation: string;
  contribution: string[];
  method_overview: string;
  experiment_overview: string;
  conclusion: string;
  limitations: string;
  reproduction_difficulty: Difficulty;
  suggested_reading_order: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string | null;
}

export interface FormulaExplanation {
  formula: string;
  location_hint: string;
  variables: Record<string, string>;
  plain_explanation: string;
  role_in_method: string;
}

export interface ExperimentSettings {
  datasets: string[];
  models: string[];
  baselines: string[];
  metrics: string[];
  training_details: string;
  hardware: string;
  hyperparameters: Record<string, string>;
  evaluation_protocol: string;
}

export interface EntityTables {
  datasets: Array<{ name: string; usage: string; split: string }>;
  models: Array<{ name: string; role: string; description: string }>;
  baselines: Array<{ name: string; reason: string }>;
}

export interface ChecklistItem {
  step_id: string;
  title: string;
  description: string;
  required_files: string[];
  expected_output: string;
  difficulty: Difficulty;
  status: "pending" | "done";
}

export interface RepoGuide {
  available: boolean;
  message?: string | null;
  repo_summary?: string | null;
  important_files: string[];
  entry_points: string[];
  dependency_files: string[];
  training_scripts: string[];
  evaluation_scripts: string[];
  config_files: string[];
  likely_reproduction_commands: string[];
  risks: string[];
}

export interface AnalysisResult {
  metadata: DocumentAnalysisMeta;
  structured_summary: StructuredSummary;
  method_flow: { nodes: GraphNode[]; edges: GraphEdge[] };
  formulas: FormulaExplanation[];
  experiment_settings: ExperimentSettings;
  entity_tables: EntityTables;
  related_work_graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  reproduction_checklist: ChecklistItem[];
  repo_guide: RepoGuide;
}

export interface AnalyzeResponse {
  paper_id: string;
  analysis: AnalysisResult;
}

export interface UploadExtraResponse {
  paper_id: string;
  uploaded: Array<{ filename: string; content_type: string; parsed: boolean; message: string }>;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      // Keep the HTTP message.
    }
    throw new Error(message);
  }
  return response.json();
}

export async function uploadPaper(file: File): Promise<UploadPaperResponse> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE}/api/upload-paper`, {
    method: "POST",
    body
  });
  return parseResponse<UploadPaperResponse>(response);
}

export async function uploadExtra(paperId: string, files: FileList | File[]): Promise<UploadExtraResponse> {
  const body = new FormData();
  body.append("paper_id", paperId);
  Array.from(files).forEach((file) => body.append("files", file));
  const response = await fetch(`${API_BASE}/api/upload-extra`, {
    method: "POST",
    body
  });
  return parseResponse<UploadExtraResponse>(response);
}

export async function analyzePaper(
  paperId: string,
  mode: AnalyzeMode,
  analysisDomain: AnalysisDomain = "auto"
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paper_id: paperId, mode, analysis_domain: analysisDomain })
  });
  return parseResponse<AnalyzeResponse>(response);
}
