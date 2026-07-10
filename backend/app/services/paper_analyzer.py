import json
import logging
from typing import Any

from app.config import get_settings
from app.schemas import AnalysisResult
from app.services.document_classifier import DocumentClassification, apply_domain_choice, classify_document
from app.services.llm_client import analyze_with_llm, mock_analysis
from app.services.pdf_parser import ParsedPaper, extract_focus_chunks


logger = logging.getLogger(__name__)


def analyze_paper(
    parsed_paper: ParsedPaper,
    detected_resources: list[dict[str, Any]],
    mode: str,
    extra_materials: list[dict[str, Any]] | None = None,
    repo_context: dict[str, Any] | None = None,
    analysis_domain: str = "auto",
    knowledge_profile: dict[str, Any] | None = None,
) -> AnalysisResult:
    classification = apply_domain_choice(classify_document(parsed_paper), analysis_domain)
    normalized_knowledge_profile = _normalize_knowledge_profile(knowledge_profile)
    if not classification.is_academic_paper:
        return AnalysisResult.model_validate(_non_paper_analysis(classification, parsed_paper, normalized_knowledge_profile))

    effective_resources = _resources_for_domain(detected_resources, classification.domain)
    effective_repo_context = repo_context or {}
    if classification.domain != "computer_science":
        effective_repo_context = {}

    prompt = _build_prompt(
        parsed_paper,
        effective_resources,
        mode,
        extra_materials or [],
        effective_repo_context,
        classification,
        normalized_knowledge_profile,
    )
    raw = analyze_with_llm(prompt=prompt, schema_name="full_analysis")
    raw["metadata"] = classification.model_dump()
    raw["knowledge_adaptation"] = _knowledge_adaptation(normalized_knowledge_profile)

    if classification.domain != "computer_science":
        raw["repo_guide"] = {
            "available": False,
            "message": "当前选择的分析方向不是计算机科学，本次不进行代码仓库分析。",
            "repo_summary": None,
            "important_files": [],
            "entry_points": [],
            "dependency_files": [],
            "training_scripts": [],
            "evaluation_scripts": [],
            "config_files": [],
            "likely_reproduction_commands": [],
            "risks": [],
        }
    elif not effective_repo_context.get("available") and not _has_github(effective_resources):
        raw["repo_guide"] = {
            "available": False,
            "message": "论文中未检测到代码仓库，建议上传补充材料或手动提供仓库链接。",
            "repo_summary": None,
            "important_files": [],
            "entry_points": [],
            "dependency_files": [],
            "training_scripts": [],
            "evaluation_scripts": [],
            "config_files": [],
            "likely_reproduction_commands": [],
            "risks": [],
        }

    try:
        return AnalysisResult.model_validate(raw)
    except Exception as exc:
        if not get_settings().llm_mock_fallback:
            raise
        logger.warning("LLM analysis did not match AnalysisResult schema; using mock. reason=%s", _short_error(exc))
        fallback = mock_analysis(schema_name="full_analysis", prompt=prompt)
        fallback["knowledge_adaptation"] = _knowledge_adaptation(normalized_knowledge_profile)
        return AnalysisResult.model_validate(fallback)


def _build_prompt(
    parsed_paper: ParsedPaper,
    detected_resources: list[dict[str, Any]],
    mode: str,
    extra_materials: list[dict[str, Any]],
    repo_context: dict[str, Any],
    classification: DocumentClassification,
    knowledge_profile: dict[str, Any] | None = None,
) -> str:
    paper_context = extract_focus_chunks(parsed_paper)
    extra_context = "\n\n".join(
        f"### {item.get('filename', 'extra')}\n{(item.get('text') or '')[:4000]}"
        for item in extra_materials
        if item.get("text")
    )
    repo_available = bool(repo_context.get("available"))
    repo_brief = json.dumps(_trim_repo_context(repo_context), ensure_ascii=False, indent=2)
    resource_brief = json.dumps(detected_resources, ensure_ascii=False, indent=2)
    classification_brief = json.dumps(classification.model_dump(), ensure_ascii=False, indent=2)
    knowledge_brief = json.dumps(_normalize_knowledge_profile(knowledge_profile), ensure_ascii=False, indent=2)
    schema_contract = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False, indent=2)

    return f"""
请基于论文内容生成 Read2Reproduce 的结构化复现分析。输出必须是严格 JSON，字段必须包含：
knowledge_adaptation, structured_summary, method_flow, formulas, experiment_settings, entity_tables,
related_work_graph, reproduction_checklist, repo_guide。

输出规则：
1. 只返回一个 JSON object，不要输出 Markdown、解释文字或代码块。
2. 根对象必须直接匹配下面的 JSON Schema；不要包裹在 analysis、data 或 result 字段下。
3. 所有 required 字段都必须存在。论文未提供的信息请用空字符串、空数组或 null，不要省略字段。
4. reproduction_difficulty 只能是 low、medium、high 之一；checklist status 只能是 pending 或 done。
5. repo_guide 必须根据检测到的仓库/补充材料真实填写；没有仓库时 available=false 并说明原因。
6. 不要默认这是一篇计算机科学或机器学习论文。必须结合“文档分类”选择分析口径。
7. 字段名为了前端统一保留为 datasets/models/baselines/training_details，但语义需要跨学科适配：
   - datasets 可以是数据集、样本、观测数据、语料、档案、试剂/材料或案例。
   - models 可以是物理模型、理论模型、数学构造、统计模型、实验系统或算法模型。
   - baselines 可以是对照组、已有理论、先前测量、标准方法、比较对象或空数组。
   - training_details 应解释实验流程、推导流程、仿真流程、数据处理流程或训练流程。
   - hardware 应填写仪器、实验装置、观测设施、计算环境或“不适用/未说明”。
8. 如果分类显示为物理学，请重点分析物理问题、理论假设、关键方程、变量单位、样品/装置、观测量、误差/不确定度和可复现实验条件。
9. 如果分类显示为数学或人文学科，不要捏造实验、数据集或代码；复现 checklist 应转为验证证明、核对引用、复查推导或追溯材料。
10. 必须根据“用户知识画像”调整解释：known_terms 只需简洁带过；unknown_terms 要先用直白中文解释，再进入论文方法；level=beginner 时少用术语并给类比，level=intermediate 时解释关键连接，level=advanced 时可更紧凑并强调细节、假设和局限。

JSON Schema：
{schema_contract}

分析模式：{mode}
Repo context available: {repo_available}
用户知识画像：
{knowledge_brief}

文档分类：
{classification_brief}

检测到的资源：
{resource_brief}

仓库或项目页上下文：
{repo_brief}

补充材料摘要：
{extra_context[:8000] if extra_context else "无"}

论文高信号片段：
{paper_context}
""".strip()


def _trim_repo_context(repo_context: dict[str, Any]) -> dict[str, Any]:
    if not repo_context:
        return {}
    return {
        "available": repo_context.get("available"),
        "repo_url": repo_context.get("repo_url"),
        "message": repo_context.get("message"),
        "description": repo_context.get("description"),
        "important_files": repo_context.get("important_files", [])[:80],
        "dependency_files": repo_context.get("dependency_files", [])[:20],
        "config_files": repo_context.get("config_files", [])[:20],
        "readme": (repo_context.get("readme") or "")[:6000],
    }


def _has_github(resources: list[dict[str, Any]]) -> bool:
    return any(resource.get("type") == "github" for resource in resources)


def _resources_for_domain(resources: list[dict[str, Any]], domain: str) -> list[dict[str, Any]]:
    if domain == "computer_science":
        return resources
    code_resource_types = {"github", "gitlab", "huggingface", "code_repository", "code_mention"}
    return [resource for resource in resources if resource.get("type") not in code_resource_types]


def _normalize_knowledge_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    levels = {"beginner", "intermediate", "advanced"}
    profile = profile or {}
    level = str(profile.get("level") or "intermediate")
    if level not in levels:
        level = "intermediate"

    known_terms = _clean_terms(profile.get("known_terms", []))
    known_keys = {term.lower() for term in known_terms}
    unknown_terms = [term for term in _clean_terms(profile.get("unknown_terms", [])) if term.lower() not in known_keys]
    return {
        "level": level,
        "known_terms": known_terms,
        "unknown_terms": unknown_terms,
    }


def _clean_terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        term = str(item).strip()
        key = term.lower()
        if not term or key in seen:
            continue
        cleaned.append(term[:80])
        seen.add(key)
    return cleaned[:24]


def _knowledge_adaptation(profile: dict[str, Any]) -> dict[str, Any]:
    level = str(profile.get("level") or "intermediate")
    known_terms = _clean_terms(profile.get("known_terms", []))
    unknown_terms = _clean_terms(profile.get("unknown_terms", []))
    if level == "beginner":
        strategy = "按入门读者讲解：先补齐未知术语，用短句、类比和阅读顺序降低门槛，再解释论文贡献。"
    elif level == "advanced":
        strategy = "按熟悉读者讲解：跳过已掌握概念，重点放在论文细节、假设边界、复现风险和可核查证据。"
    else:
        strategy = "按有基础读者讲解：简要补齐未知术语，强调概念之间如何连接到方法、实验和结论。"
    if unknown_terms:
        strategy += f" 优先解释这些未知前置知识：{', '.join(unknown_terms[:8])}。"
    return {
        "level": level,
        "known_terms": known_terms,
        "unknown_terms": unknown_terms,
        "explanation_strategy": strategy,
    }


def _non_paper_analysis(
    classification: DocumentClassification,
    parsed_paper: ParsedPaper,
    knowledge_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = classification.model_dump()
    reason = classification.warnings[0] if classification.warnings else "当前 PDF 不像标准学术论文。"
    title = parsed_paper.title if parsed_paper.title != "Untitled Paper" else "未识别到可靠标题"
    text_size = len((parsed_paper.full_text or "").strip())
    is_empty = classification.document_type == "empty_or_unreadable"

    return {
        "metadata": metadata,
        "knowledge_adaptation": _knowledge_adaptation(_normalize_knowledge_profile(knowledge_profile)),
        "structured_summary": {
            "background": f"系统已读取上传文件，但分类结果为 {classification.document_type}，不是可直接复现分析的研究论文。",
            "problem": reason,
            "motivation": "与其套用论文模板生成看似完整但不可靠的分析，当前结果优先指出文件不适配的原因和下一步处理方式。",
            "contribution": [
                f"识别到的标题/首页线索：{title}。",
                f"可提取文本长度约 {text_size} 个字符。",
                "未识别到足够稳定的论文结构、研究问题、方法、实验或参考文献信号。",
            ],
            "method_overview": "当前没有可分析的研究方法。若这是扫描版论文，请先进行 OCR；若这是讲义、宣传页或玩笑文本，则不应生成复现实验方案。",
            "experiment_overview": "未检测到可复现实验、推导、观测或材料流程。",
            "conclusion": "建议重新上传真正的论文 PDF，或补充正文文本、DOI/arXiv 链接、实验材料和代码/数据说明。",
            "limitations": "当前判断基于 PDF 可提取文本和结构信号；图片型 PDF、低质量 OCR 或非常规排版可能被误判。",
            "reproduction_difficulty": "high" if is_empty else "medium",
            "suggested_reading_order": ["文件可读性检查", "确认是否为论文正文", "补充 OCR/正文文本", "重新发起分析"],
        },
        "method_flow": {
            "nodes": [
                {"id": "upload", "label": "上传 PDF", "type": "input"},
                {"id": "extract", "label": "文本提取", "type": "process"},
                {"id": "diagnose", "label": "论文适配性诊断", "type": "decision"},
                {"id": "next", "label": "补充材料或重新上传", "type": "action"},
            ],
            "edges": [
                {"source": "upload", "target": "extract", "label": "read"},
                {"source": "extract", "target": "diagnose", "label": "classify"},
                {"source": "diagnose", "target": "next", "label": "needs valid paper text"},
            ],
        },
        "formulas": [],
        "experiment_settings": {
            "datasets": [],
            "models": [],
            "baselines": [],
            "metrics": [],
            "training_details": "不适用：当前材料不是可复现实验或推导的论文正文。",
            "hardware": "不适用。",
            "hyperparameters": {},
            "evaluation_protocol": "先确认文件类型和文本可读性，再进行论文剖析。",
        },
        "entity_tables": {"datasets": [], "models": [], "baselines": []},
        "related_work_graph": {
            "nodes": [
                {"id": "document", "label": "当前 PDF", "type": classification.document_type},
                {"id": "signals", "label": "论文结构信号不足", "type": "diagnosis"},
                {"id": "paper", "label": "有效论文正文", "type": "target"},
            ],
            "edges": [
                {"source": "document", "target": "signals", "label": "classified_as"},
                {"source": "signals", "target": "paper", "label": "need"},
            ],
        },
        "reproduction_checklist": [
            {
                "step_id": "doc-check-1",
                "title": "确认 PDF 是否为论文正文",
                "description": "检查文件是否包含标题、摘要、研究问题、方法/实验/推导和参考文献。",
                "required_files": ["论文 PDF"],
                "expected_output": "确认当前文件是否适合复现分析。",
                "difficulty": "low",
                "status": "pending",
            },
            {
                "step_id": "doc-check-2",
                "title": "处理扫描件或图片型 PDF",
                "description": "如果文字无法复制，请先 OCR，或上传包含正文的文本/Markdown/PDF 补充材料。",
                "required_files": ["OCR 文本", "可复制文字的 PDF"],
                "expected_output": "系统可以提取到足够正文。",
                "difficulty": "medium",
                "status": "pending",
            },
            {
                "step_id": "doc-check-3",
                "title": "重新发起分析",
                "description": "上传有效论文后，再选择只分析论文、结合资源或结合补充材料的模式。",
                "required_files": ["有效论文", "可选补充材料"],
                "expected_output": "生成面向对应学科的复现分析。",
                "difficulty": "low",
                "status": "pending",
            },
        ],
        "repo_guide": {
            "available": False,
            "message": "当前材料不是可分析的论文正文，因此暂不读取或推断代码仓库。",
            "repo_summary": None,
            "important_files": [],
            "entry_points": [],
            "dependency_files": [],
            "training_scripts": [],
            "evaluation_scripts": [],
            "config_files": [],
            "likely_reproduction_commands": [],
            "risks": ["若这是恶搞文本或非论文材料，生成复现步骤会产生误导。"],
        },
    }


def _short_error(exc: BaseException) -> str:
    return str(exc).replace("\n", " ")[:600]
