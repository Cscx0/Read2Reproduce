from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    PrerequisiteTermsRequest,
    PrerequisiteTermsResponse,
    UploadExtraResponse,
    UploadPaperResponse,
)
from app.services.document_classifier import classify_document
from app.services.github_analyzer import analyze_detected_resources
from app.services.llm_client import get_llm_status, probe_llm
from app.services.paper_analyzer import analyze_paper
from app.services.pdf_parser import ParsedPaper, parse_pdf
from app.services.prerequisite_extractor import extract_prerequisite_terms
from app.services.resource_detector import detect_resources, has_code_resource


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PAPERS: dict[str, dict] = {}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/llm-health")
def llm_health(check_remote: bool = False) -> dict:
    if check_remote:
        return probe_llm()
    return get_llm_status()


@app.post("/api/upload-paper", response_model=UploadPaperResponse)
async def upload_paper(file: UploadFile = File(...)) -> UploadPaperResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 文件。")

    paper_id = str(uuid4())
    file_path = settings.upload_dir / f"{paper_id}_{_safe_filename(file.filename)}"
    content = await file.read()
    file_path.write_bytes(content)

    try:
        parsed = parse_pdf(file_path)
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"PDF 解析失败：{exc}") from exc

    resources = detect_resources(parsed.full_text)
    document_hint = classify_document(parsed)
    PAPERS[paper_id] = {
        "paper_id": paper_id,
        "file_path": str(file_path),
        "parsed": parsed,
        "detected_resources": [resource.model_dump() for resource in resources],
        "document_hint": document_hint.model_dump(),
        "extra_materials": [],
    }

    return UploadPaperResponse(
        paper_id=paper_id,
        title=parsed.title,
        abstract=parsed.abstract,
        detected_resources=resources,
        has_code_resource=has_code_resource(resources),
        paper_info={
            "title": parsed.title,
            "abstract": parsed.abstract,
            "sections": parsed.sections,
            "page_count": parsed.page_count,
        },
        document_hint=document_hint.model_dump(),
    )


@app.post("/api/upload-extra", response_model=UploadExtraResponse)
async def upload_extra(
    paper_id: str = Form(...),
    files: list[UploadFile] = File(...),
) -> UploadExtraResponse:
    record = PAPERS.get(paper_id)
    if not record:
        raise HTTPException(status_code=404, detail="paper_id 不存在，请先上传论文。")

    uploaded = []
    extra_dir = settings.upload_dir / paper_id / "extra"
    extra_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        filename = _safe_filename(file.filename or "extra")
        suffix = Path(filename).suffix.lower()
        target = extra_dir / filename
        content = await file.read()
        target.write_bytes(content)

        parsed_text = ""
        parsed = False
        message = "已保存。"
        if suffix in {".txt", ".md"}:
            parsed_text = content.decode("utf-8", errors="ignore")
            parsed = True
            message = "已读取文本内容。"
        elif suffix == ".pdf":
            parsed_pdf = parse_pdf(target)
            parsed_text = parsed_pdf.full_text
            parsed = True
            message = "已按 PDF 解析。"
        elif suffix == ".zip":
            message = "ZIP 已保存，MVP 阶段暂不解压解析。"
        else:
            message = "文件已保存，但当前类型暂不解析。"

        record["extra_materials"].append(
            {
                "filename": filename,
                "path": str(target),
                "content_type": file.content_type or "application/octet-stream",
                "text": parsed_text[:30000],
                "parsed": parsed,
            }
        )
        uploaded.append(
            {
                "filename": filename,
                "content_type": file.content_type or "application/octet-stream",
                "parsed": parsed,
                "message": message,
            }
        )

    return UploadExtraResponse(paper_id=paper_id, uploaded=uploaded)


@app.post("/api/prerequisite-terms", response_model=PrerequisiteTermsResponse)
async def prerequisite_terms(request: PrerequisiteTermsRequest) -> PrerequisiteTermsResponse:
    record = PAPERS.get(request.paper_id)
    if not record:
        raise HTTPException(status_code=404, detail="paper_id 不存在，请先上传论文。")

    selected_domain = _effective_domain(request.analysis_domain, record)
    terms = extract_prerequisite_terms(
        parsed_paper=record["parsed"],
        domain=selected_domain,
        knowledge_level=request.knowledge_level,
    )
    return PrerequisiteTermsResponse(
        paper_id=request.paper_id,
        analysis_domain=selected_domain,
        knowledge_level=request.knowledge_level,
        terms=terms,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    record = PAPERS.get(request.paper_id)
    if not record:
        raise HTTPException(status_code=404, detail="paper_id 不存在，请先上传论文。")

    selected_domain = _effective_domain(request.analysis_domain, record)

    repo_context = {}
    if request.mode == "with_detected_resources" and selected_domain == "computer_science":
        repo_context = await analyze_detected_resources(
            [resource for resource in _resource_models(record["detected_resources"])]
        )

    analysis = analyze_paper(
        parsed_paper=record["parsed"],
        detected_resources=record["detected_resources"],
        mode=request.mode,
        extra_materials=record["extra_materials"],
        repo_context=repo_context,
        analysis_domain=request.analysis_domain,
        knowledge_profile=request.knowledge_profile.model_dump() if request.knowledge_profile else None,
    )
    return AnalyzeResponse(paper_id=request.paper_id, analysis=analysis)


def _effective_domain(analysis_domain: str, record: dict) -> str:
    selected_domain = analysis_domain
    if selected_domain == "auto":
        selected_domain = str(record.get("document_hint", {}).get("domain") or "general")
    return selected_domain if selected_domain not in {"unknown", "non_academic", ""} else "general"


def _resource_models(resources: list[dict]):
    from app.schemas import DetectedResource

    return [DetectedResource.model_validate(resource) for resource in resources]


def _safe_filename(filename: str) -> str:
    keep = []
    for char in filename:
        if char.isalnum() or char in {".", "-", "_"}:
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep)[:160] or "upload"
