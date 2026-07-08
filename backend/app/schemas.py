from typing import Any, Literal

from pydantic import BaseModel, Field


AnalyzeMode = Literal["paper_only", "with_detected_resources", "with_extra_materials"]
AnalysisDomain = Literal[
    "auto",
    "computer_science",
    "physics",
    "mathematics",
    "chemistry",
    "biology",
    "medicine",
    "economics",
    "social_science",
    "engineering",
    "humanities",
    "general",
]
Difficulty = Literal["low", "medium", "high"]


class DetectedResource(BaseModel):
    type: str
    url: str = ""
    confidence: float = Field(ge=0, le=1)
    note: str | None = None


class PaperBasicInfo(BaseModel):
    title: str
    abstract: str
    sections: list[str] = []
    page_count: int


class DocumentAnalysisMeta(BaseModel):
    document_type: str
    domain: str
    is_academic_paper: bool
    confidence: float = Field(ge=0, le=1)
    signals: list[str] = []
    warnings: list[str] = []
    guidance: str


class UploadPaperResponse(BaseModel):
    paper_id: str
    title: str
    abstract: str
    detected_resources: list[DetectedResource]
    has_code_resource: bool
    paper_info: PaperBasicInfo
    document_hint: DocumentAnalysisMeta


class ExtraMaterialItem(BaseModel):
    filename: str
    content_type: str
    parsed: bool
    message: str


class UploadExtraResponse(BaseModel):
    paper_id: str
    uploaded: list[ExtraMaterialItem]


class AnalyzeRequest(BaseModel):
    paper_id: str
    mode: AnalyzeMode = "paper_only"
    analysis_domain: AnalysisDomain = "auto"


class StructuredSummary(BaseModel):
    background: str
    problem: str
    motivation: str
    contribution: list[str]
    method_overview: str
    experiment_overview: str
    conclusion: str
    limitations: str
    reproduction_difficulty: Difficulty
    suggested_reading_order: list[str]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class MethodFlow(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class FormulaExplanation(BaseModel):
    formula: str
    location_hint: str
    variables: dict[str, str]
    plain_explanation: str
    role_in_method: str


class ExperimentSettings(BaseModel):
    datasets: list[str]
    models: list[str]
    baselines: list[str]
    metrics: list[str]
    training_details: str
    hardware: str
    hyperparameters: dict[str, Any]
    evaluation_protocol: str


class DatasetEntry(BaseModel):
    name: str
    usage: str
    split: str


class ModelEntry(BaseModel):
    name: str
    role: str
    description: str


class BaselineEntry(BaseModel):
    name: str
    reason: str


class EntityTables(BaseModel):
    datasets: list[DatasetEntry]
    models: list[ModelEntry]
    baselines: list[BaselineEntry]


class RelatedWorkGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ChecklistItem(BaseModel):
    step_id: str
    title: str
    description: str
    required_files: list[str]
    expected_output: str
    difficulty: Difficulty
    status: Literal["pending", "done"] = "pending"


class RepoGuide(BaseModel):
    available: bool
    message: str | None = None
    repo_summary: str | None = None
    important_files: list[str] = []
    entry_points: list[str] = []
    dependency_files: list[str] = []
    training_scripts: list[str] = []
    evaluation_scripts: list[str] = []
    config_files: list[str] = []
    likely_reproduction_commands: list[str] = []
    risks: list[str] = []


class AnalysisResult(BaseModel):
    metadata: DocumentAnalysisMeta
    structured_summary: StructuredSummary
    method_flow: MethodFlow
    formulas: list[FormulaExplanation]
    experiment_settings: ExperimentSettings
    entity_tables: EntityTables
    related_work_graph: RelatedWorkGraph
    reproduction_checklist: list[ChecklistItem]
    repo_guide: RepoGuide


class AnalyzeResponse(BaseModel):
    paper_id: str
    analysis: AnalysisResult
