import json
import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings


logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """Raised when a configured LLM endpoint cannot return usable JSON."""


def analyze_with_llm(prompt: str, schema_name: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.active_api_key:
        logger.info("LLM API key is not configured; using mock analysis.")
        return mock_analysis(schema_name=schema_name, prompt=prompt)

    try:
        return _call_chat_completion(prompt, schema_name)
    except Exception as exc:
        if not settings.llm_mock_fallback:
            raise
        logger.warning("LLM call failed; using mock analysis. reason=%s", _safe_error(exc))
        return mock_analysis(schema_name=schema_name, prompt=prompt)


def get_llm_status() -> dict[str, Any]:
    settings = get_settings()
    endpoint = _chat_completion_url(settings.active_base_url)
    return {
        "configured": bool(settings.active_api_key),
        "model": settings.llm_model,
        "endpoint": _safe_endpoint(endpoint),
        "mock_fallback": settings.llm_mock_fallback,
        "response_format_json": settings.llm_response_format_json,
    }


def probe_llm() -> dict[str, Any]:
    status = get_llm_status()
    if not status["configured"]:
        return {**status, "ok": False, "remote_checked": False, "message": "LLM API key is not configured."}

    try:
        result = _call_chat_completion(
            prompt='请只返回严格 JSON：{"ok": true, "message": "pong"}',
            schema_name="llm_probe",
            temperature=0,
            max_tokens=120,
        )
    except Exception as exc:
        return {
            **status,
            "ok": False,
            "remote_checked": True,
            "message": "LLM endpoint check failed.",
            "error": _safe_error(exc),
        }

    return {
        **status,
        "ok": bool(result.get("ok")),
        "remote_checked": True,
        "message": str(result.get("message") or "LLM endpoint responded."),
    }


def _call_chat_completion(
    prompt: str,
    schema_name: str,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.active_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Read2Reproduce, a research reproduction assistant. "
                    "Return strict JSON only. Match the requested schema and use Chinese for explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if settings.llm_response_format_json:
        payload["response_format"] = {"type": "json_object"}

    data = _post_chat_completion(
        url=_chat_completion_url(settings.active_base_url),
        headers=headers,
        payload=payload,
        timeout=settings.llm_timeout_seconds,
    )

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("LLM response did not contain choices[0].message.content.") from exc

    parsed = _parse_json_object(content)
    if schema_name == "full_analysis" and "analysis" in parsed:
        if not isinstance(parsed["analysis"], dict):
            raise LLMClientError("LLM response field 'analysis' is not a JSON object.")
        return parsed["analysis"]
    return parsed


def _post_chat_completion(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    response = _post_json(url, headers, payload, timeout)
    if response.status_code in {400, 422} and "response_format" in payload:
        retry_payload = dict(payload)
        retry_payload.pop("response_format", None)
        logger.info("LLM endpoint rejected the first request; retrying without response_format.")
        response = _post_json(url, headers, retry_payload, timeout)

    _raise_for_status(response)
    try:
        data = response.json()
    except ValueError as exc:
        raise LLMClientError("LLM endpoint returned non-JSON HTTP response.") from exc
    if not isinstance(data, dict):
        raise LLMClientError("LLM endpoint response root is not a JSON object.")
    return data


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> httpx.Response:
    try:
        return httpx.post(url, headers=headers, json=payload, timeout=timeout)
    except httpx.HTTPError as exc:
        raise LLMClientError(f"LLM HTTP request failed: {_safe_error(exc)}") from exc


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body = response.text.replace("\n", " ").strip()[:800]
        raise LLMClientError(f"LLM HTTP {response.status_code}: {body}") from exc


def _chat_completion_url(base_url_or_endpoint: str) -> str:
    base = base_url_or_endpoint.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _parse_json_object(content: str) -> dict[str, Any]:
    text = _strip_code_fence(content)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = json.loads(_extract_json_substring(text))
    if not isinstance(parsed, dict):
        raise LLMClientError("LLM message content is not a JSON object.")
    return parsed


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip().startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_json_substring(text: str) -> str:
    starts = [index for index in (text.find("{"), text.find("[")) if index >= 0]
    if not starts:
        raise LLMClientError("LLM message content did not contain JSON.")

    start = min(starts)
    stack: list[str] = []
    in_string = False
    escape = False
    pairs = {"{": "}", "[": "]"}

    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
            if not stack:
                return text[start : index + 1]

    raise LLMClientError("LLM message content contained incomplete JSON.")


def _safe_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if not parsed.netloc:
        return endpoint
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _safe_error(exc: BaseException) -> str:
    settings = get_settings()
    message = str(exc)
    if settings.active_api_key:
        message = message.replace(settings.active_api_key, "<redacted>")
    return message[:1000]


def mock_analysis(schema_name: str = "full_analysis", prompt: str | None = None) -> dict[str, Any]:
    repo_available = bool(prompt and "Repo context available: True" in prompt)
    repo_failed = bool(prompt and "Repo context available: False" in prompt and "repo_url" in prompt)

    repo_guide = {
        "available": repo_available,
        "message": None if repo_available else "论文中未检测到可读取的代码仓库，建议上传补充材料或手动提供仓库链接。",
        "repo_summary": "仓库包含训练入口、评估脚本、配置文件和环境依赖，适合按 README 复现实验主流程。" if repo_available else None,
        "important_files": ["README.md", "requirements.txt", "configs/default.yaml", "train.py", "evaluate.py"] if repo_available else [],
        "entry_points": ["train.py", "evaluate.py"] if repo_available else [],
        "dependency_files": ["requirements.txt", "environment.yml"] if repo_available else [],
        "training_scripts": ["train.py", "scripts/run_train.sh"] if repo_available else [],
        "evaluation_scripts": ["evaluate.py", "scripts/run_eval.sh"] if repo_available else [],
        "config_files": ["configs/default.yaml"] if repo_available else [],
        "likely_reproduction_commands": [
            "conda env create -f environment.yml",
            "python train.py --config configs/default.yaml",
            "python evaluate.py --checkpoint outputs/best.ckpt",
        ]
        if repo_available
        else [],
        "risks": ["README 可能未标注论文使用的精确 commit。", "数据集下载和授权可能需要手动处理。"] if repo_available else [],
    }
    if repo_failed:
        repo_guide["message"] = "检测到仓库链接，但公开信息读取失败；当前结果已降级为基于论文内容的复现分析。"

    metadata = _classification_from_prompt(prompt)
    return {
        "metadata": metadata,
        **_mock_domain_pack(str(metadata.get("domain") or "unknown")),
        "repo_guide": repo_guide,
    }


def _classification_from_prompt(prompt: str | None) -> dict[str, Any]:
    default = {
        "document_type": "academic_like_document",
        "domain": "unknown",
        "is_academic_paper": True,
        "confidence": 0.5,
        "signals": ["未读取到显式分类，按通用科研论文处理。"],
        "warnings": [],
        "guidance": "避免默认套用单一学科模板。",
    }
    if not prompt:
        return default

    marker = "文档分类："
    start = prompt.find(marker)
    if start < 0:
        return default
    after_marker = prompt[start + len(marker) :]
    end = after_marker.find("\n\n检测到的资源：")
    snippet = after_marker[:end].strip() if end >= 0 else after_marker.strip()
    try:
        parsed = _parse_json_object(snippet)
    except Exception:
        return default
    return {**default, **parsed}


def _mock_domain_pack(domain: str) -> dict[str, Any]:
    if domain == "physics":
        return _physics_mock_pack()
    if domain == "mathematics":
        return _mathematics_mock_pack()
    if domain == "computer_science":
        return _computer_science_mock_pack()
    return _general_research_mock_pack(domain)


def _physics_mock_pack() -> dict[str, Any]:
    return {
        "structured_summary": {
            "background": "论文看起来属于物理学研究，核心背景通常围绕某类物理现象、理论模型或实验观测的解释。",
            "problem": "复现重点不是训练代码，而是确认物理假设、样品/装置、关键方程、测量量、单位和不确定度处理是否足够明确。",
            "motivation": "物理论文的可复现性依赖实验条件、仪器校准、数据处理流程和理论近似，任何一个细节缺失都可能改变结论。",
            "contribution": [
                "整理论文中的研究对象、物理机制和需要验证的核心假设。",
                "抽取关键方程、变量含义、单位和近似条件。",
                "把实验/观测/仿真流程拆成可核查步骤，并标出误差来源。",
            ],
            "method_overview": "建议按物理问题、理论模型、实验或仿真设置、数据处理、误差分析和结论验证来阅读。",
            "experiment_overview": "优先定位样品制备、仪器参数、测量条件、观测量、重复次数、拟合方法和不确定度估计。",
            "conclusion": "论文结论需要结合测量条件和理论假设理解，复现时应先复核关键曲线/表格，再尝试完整实验或仿真。",
            "limitations": "常见风险包括仪器校准细节不足、样品批次差异、单位换算、边界条件和误差传播描述不完整。",
            "reproduction_difficulty": "high",
            "suggested_reading_order": ["Abstract", "Introduction", "Theory / Model", "Experimental Setup", "Results", "Uncertainty / Appendix"],
        },
        "method_flow": {
            "nodes": [
                {"id": "question", "label": "物理问题", "type": "topic"},
                {"id": "model", "label": "理论模型/假设", "type": "model"},
                {"id": "setup", "label": "样品与装置", "type": "experiment"},
                {"id": "measurement", "label": "测量与数据处理", "type": "process"},
                {"id": "validation", "label": "误差与结论验证", "type": "metric"},
            ],
            "edges": [
                {"source": "question", "target": "model", "label": "formulate"},
                {"source": "model", "target": "setup", "label": "test"},
                {"source": "setup", "target": "measurement", "label": "observe"},
                {"source": "measurement", "target": "validation", "label": "fit / compare"},
            ],
        },
        "formulas": [
            {
                "formula": r"H = H_0 + H_{int}",
                "location_hint": "Theory / Model",
                "variables": {"H": "系统哈密顿量", "H_0": "未扰动项", "H_{int}": "相互作用或扰动项"},
                "plain_explanation": "物理系统通常被拆成基础行为和相互作用项，复现时要核对每一项的假设、单位和边界条件。",
                "role_in_method": "用于定位理论模型的核心设定。",
            }
        ],
        "experiment_settings": {
            "datasets": ["样品/观测数据", "关键曲线或谱图"],
            "models": ["理论模型", "拟合模型"],
            "baselines": ["已有理论预测", "空白/对照样品", "先前测量结果"],
            "metrics": ["观测量", "拟合残差", "不确定度", "显著性"],
            "training_details": "记录样品制备、测量温度/压力/场强、仪器校准、采样频率、数据清洗和拟合流程。",
            "hardware": "补充实验装置、探测器、光源、低温/真空系统或仿真计算环境。",
            "hyperparameters": {"temperature": "论文给定值", "field_strength": "论文给定值", "time_step_or_resolution": "论文给定值"},
            "evaluation_protocol": "复核关键图表和误差条，确认单位、边界条件、拟合区间和重复测量策略。",
        },
        "entity_tables": {
            "datasets": [{"name": "观测/实验数据", "usage": "验证物理模型", "split": "按测量条件或样品批次组织"}],
            "models": [{"name": "理论/拟合模型", "role": "proposed_or_tested", "description": "论文用于解释现象或拟合观测数据的物理模型。"}],
            "baselines": [{"name": "已有理论或对照测量", "reason": "用于判断新结果是否超出已知解释。"}],
        },
        "related_work_graph": {
            "nodes": [
                {"id": "phenomenon", "label": "目标物理现象", "type": "topic"},
                {"id": "prior", "label": "已有理论/测量", "type": "paper"},
                {"id": "model", "label": "本文模型或装置", "type": "method"},
            ],
            "edges": [
                {"source": "prior", "target": "phenomenon", "label": "explains"},
                {"source": "model", "target": "prior", "label": "compare_with"},
            ],
        },
        "reproduction_checklist": _domain_checklist(
            [
                ("确认物理对象和假设", "记录系统、边界条件、近似和变量单位。", ["Theory section"]),
                ("复核样品/装置/仿真条件", "整理实验装置、材料批次、校准条件或仿真参数。", ["Experimental Setup", "Appendix"]),
                ("重画关键图表", "用论文给出的数据或公式复核核心曲线、误差条和拟合区间。", ["Figures", "Tables"]),
                ("检查不确定度传播", "确认误差来源、重复测量次数和统计检验。", ["Results", "Supplementary Material"]),
            ]
        ),
    }


def _mathematics_mock_pack() -> dict[str, Any]:
    return {
        "structured_summary": {
            "background": "论文看起来属于数学或理论研究，重点在定义、定理、构造和证明结构。",
            "problem": "复现不应理解为运行实验，而是核对证明链条、关键引理、边界条件和例子。",
            "motivation": "数学论文的可验证性依赖符号定义一致、假设完整和推导步骤可追踪。",
            "contribution": ["梳理核心定义与定理。", "定位关键引理和证明依赖。", "列出可手算或可形式化验证的例子。"],
            "method_overview": "按定义、主定理、证明路线、关键构造、反例或应用来阅读。",
            "experiment_overview": "若论文无实验，应转为验证证明、复算例子和核对引用定理。",
            "conclusion": "结论需要建立在每个假设和证明步骤均成立的基础上。",
            "limitations": "风险包括符号约定不清、引用定理条件不满足、证明跳步和边界情形未覆盖。",
            "reproduction_difficulty": "medium",
            "suggested_reading_order": ["Abstract", "Definitions", "Main Theorems", "Proof Overview", "Key Lemmas", "Examples / Appendix"],
        },
        "method_flow": {
            "nodes": [
                {"id": "definitions", "label": "定义与假设", "type": "concept"},
                {"id": "lemmas", "label": "关键引理", "type": "proof"},
                {"id": "theorem", "label": "主定理", "type": "result"},
                {"id": "examples", "label": "例子/边界情形", "type": "validation"},
            ],
            "edges": [
                {"source": "definitions", "target": "lemmas", "label": "supports"},
                {"source": "lemmas", "target": "theorem", "label": "proves"},
                {"source": "theorem", "target": "examples", "label": "check"},
            ],
        },
        "formulas": [
            {
                "formula": r"\forall x \in X,\ P(x) \Rightarrow Q(x)",
                "location_hint": "Main theorem",
                "variables": {"X": "定义域或对象集合", "P(x)": "前提条件", "Q(x)": "需要证明的结论"},
                "plain_explanation": "复核时要确认每个对象是否满足前提，以及证明是否覆盖全部情形。",
                "role_in_method": "表示主命题的逻辑结构。",
            }
        ],
        "experiment_settings": {
            "datasets": ["例子或构造对象"],
            "models": ["定义体系", "主定理", "证明构造"],
            "baselines": ["已有定理", "经典结果", "反例"],
            "metrics": ["证明完整性", "假设覆盖", "边界情形"],
            "training_details": "不适用；应记录证明依赖、引用定理条件和可验证例子。",
            "hardware": "不适用。",
            "hyperparameters": {},
            "evaluation_protocol": "逐步检查定义、引理、主定理和例子，必要时用符号计算或形式化工具辅助。",
        },
        "entity_tables": {
            "datasets": [{"name": "例子/构造", "usage": "验证定理适用性", "split": "不适用"}],
            "models": [{"name": "主定理证明链", "role": "proposed", "description": "论文的核心理论贡献。"}],
            "baselines": [{"name": "已有定理", "reason": "作为证明依赖或比较对象。"}],
        },
        "related_work_graph": {
            "nodes": [
                {"id": "classic", "label": "经典结果", "type": "theorem"},
                {"id": "extension", "label": "本文推广", "type": "result"},
                {"id": "example", "label": "例子/应用", "type": "validation"},
            ],
            "edges": [
                {"source": "extension", "target": "classic", "label": "extends"},
                {"source": "example", "target": "extension", "label": "illustrates"},
            ],
        },
        "reproduction_checklist": _domain_checklist(
            [
                ("整理符号表", "列出所有定义、符号和假设。", ["Definitions"]),
                ("检查引用定理条件", "核对每个外部定理是否满足适用条件。", ["Related Work", "Proof"]),
                ("逐步复写证明", "补全跳步并标出关键引理依赖。", ["Proof sections"]),
                ("验证例子和边界情形", "复算论文中的例子或构造反例测试假设边界。", ["Examples", "Appendix"]),
            ]
        ),
    }


def _computer_science_mock_pack() -> dict[str, Any]:
    return _general_research_mock_pack("computer_science")


def _general_research_mock_pack(domain: str) -> dict[str, Any]:
    domain_label = "计算机科学" if domain == "computer_science" else "通用科研"
    return {
        "structured_summary": {
            "background": f"论文看起来属于{domain_label}场景，分析会优先依据论文实际术语，而不是强行套用某一学科模板。",
            "problem": "核心问题是如何识别研究对象、方法路径、证据来源和结论验证方式。",
            "motivation": "复现或核查研究结论需要先明确材料、数据、模型、流程、指标和限制条件。",
            "contribution": ["提取研究问题和核心贡献。", "梳理方法/实验/论证流程。", "形成可执行的复现或核查 checklist。"],
            "method_overview": "方法可以拆成研究对象、处理流程、核心模型或论证、结果验证和局限分析。",
            "experiment_overview": "根据学科语境提取数据/样本/材料、比较对象、评价指标、实验或推导流程。",
            "conclusion": "结论需要结合证据质量、评价协议和未披露细节一起判断。",
            "limitations": "局限可能包括材料不可得、参数缺失、样本信息不足、代码/数据未公开或论证细节不完整。",
            "reproduction_difficulty": "medium",
            "suggested_reading_order": ["Abstract", "Introduction", "Method / Theory", "Results / Evidence", "Discussion", "Appendix"],
        },
        "method_flow": {
            "nodes": [
                {"id": "question", "label": "研究问题", "type": "topic"},
                {"id": "materials", "label": "数据/材料/对象", "type": "data"},
                {"id": "method", "label": "方法或论证", "type": "method"},
                {"id": "evidence", "label": "结果证据", "type": "metric"},
            ],
            "edges": [
                {"source": "question", "target": "materials", "label": "requires"},
                {"source": "materials", "target": "method", "label": "processed_by"},
                {"source": "method", "target": "evidence", "label": "validated_by"},
            ],
        },
        "formulas": [
            {
                "formula": r"result = method(materials, assumptions)",
                "location_hint": "Method / Evidence",
                "variables": {"materials": "数据、样本、文本、材料或研究对象", "assumptions": "理论或实验假设", "result": "论文报告的结果"},
                "plain_explanation": "复现时要同时核对输入材料、方法步骤和假设条件。",
                "role_in_method": "作为跨学科核查流程的抽象表达。",
            }
        ],
        "experiment_settings": {
            "datasets": ["论文中的数据/材料/样本"],
            "models": ["论文中的方法、理论模型或分析框架"],
            "baselines": ["对照组、已有方法、已有理论或比较对象"],
            "metrics": ["论文报告的主要指标或证据标准"],
            "training_details": "根据论文实际学科记录实验、推导、仿真、编码或论证步骤。",
            "hardware": "记录仪器、实验环境、观测设施、计算环境或不适用。",
            "hyperparameters": {"关键参数": "从论文方法和附录提取"},
            "evaluation_protocol": "按论文同样的数据、材料、指标、统计检验或论证标准复核。",
        },
        "entity_tables": {
            "datasets": [{"name": "研究材料", "usage": "支撑论文主要结果", "split": "按论文说明"}],
            "models": [{"name": "论文方法/模型", "role": "proposed", "description": "论文用于得到结论的核心方法或论证框架。"}],
            "baselines": [{"name": "比较对象", "reason": "用于判断论文结论相对已有工作的增量。"}],
        },
        "related_work_graph": {
            "nodes": [
                {"id": "topic", "label": "研究主题", "type": "topic"},
                {"id": "prior", "label": "已有工作", "type": "paper"},
                {"id": "current", "label": "本文贡献", "type": "method"},
            ],
            "edges": [
                {"source": "prior", "target": "topic", "label": "studies"},
                {"source": "current", "target": "prior", "label": "extends_or_compares"},
            ],
        },
        "reproduction_checklist": _domain_checklist(
            [
                ("确认研究对象", "记录数据、样本、材料、文本或理论对象。", ["Method", "Appendix"]),
                ("整理核心流程", "把实验、推导、仿真或分析流程拆成可执行步骤。", ["Method"]),
                ("复核关键结果", "对照主要表格、图形、统计检验或论证结论。", ["Results"]),
                ("记录缺失信息", "列出材料、参数、代码、数据或引用依据中的缺口。", ["Supplementary Material"]),
            ]
        ),
    }


def _domain_checklist(items: list[tuple[str, str, list[str]]]) -> list[dict[str, Any]]:
    return [
        {
            "step_id": f"step-{index}",
            "title": title,
            "description": description,
            "required_files": required_files,
            "expected_output": "形成可核查的复现记录。",
            "difficulty": "medium" if index > 1 else "low",
            "status": "pending",
        }
        for index, (title, description, required_files) in enumerate(items, start=1)
    ]
