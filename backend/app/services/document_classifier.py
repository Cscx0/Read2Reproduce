import math
import re
from collections import Counter
from dataclasses import dataclass, replace

from app.services.pdf_parser import ParsedPaper


DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "computer_science": [
        "algorithm",
        "neural",
        "machine learning",
        "deep learning",
        "dataset",
        "baseline",
        "training",
        "inference",
        "transformer",
        "accuracy",
        "f1",
        "gpu",
        "repository",
        "代码",
        "算法",
        "神经网络",
        "数据集",
        "训练",
        "基线",
    ],
    "physics": [
        "quantum",
        "photon",
        "electron",
        "hamiltonian",
        "lattice",
        "superconduct",
        "relativity",
        "thermodynamic",
        "scattering",
        "spectroscopy",
        "fermion",
        "boson",
        "spin",
        "magnetic",
        "cosmology",
        "plasma",
        "particle",
        "semiconductor",
        "phonon",
        "wavefunction",
        "maxwell",
        "ising",
        "量子",
        "光子",
        "电子",
        "哈密顿",
        "晶格",
        "超导",
        "相对论",
        "热力学",
        "散射",
        "光谱",
        "自旋",
        "磁",
        "宇宙学",
        "等离子",
        "粒子",
    ],
    "mathematics": [
        "theorem",
        "lemma",
        "proof",
        "corollary",
        "manifold",
        "algebra",
        "topology",
        "operator",
        "conjecture",
        "证明",
        "定理",
        "引理",
        "推论",
        "流形",
        "代数",
        "拓扑",
    ],
    "chemistry": [
        "synthesis",
        "catalyst",
        "reaction",
        "molecule",
        "polymer",
        "spectra",
        "nmr",
        "chromatography",
        "electrochemical",
        "化学",
        "合成",
        "催化",
        "反应",
        "分子",
        "聚合物",
    ],
    "biology": [
        "gene",
        "protein",
        "cell",
        "genome",
        "enzyme",
        "organism",
        "mutation",
        "expression",
        "assay",
        "基因",
        "蛋白",
        "细胞",
        "基因组",
        "酶",
        "突变",
    ],
    "medicine": [
        "patient",
        "clinical",
        "trial",
        "diagnosis",
        "therapy",
        "cohort",
        "placebo",
        "survival",
        "病例",
        "临床",
        "患者",
        "诊断",
        "治疗",
        "队列",
    ],
    "economics": [
        "market",
        "policy",
        "regression",
        "inflation",
        "welfare",
        "trade",
        "labor",
        "elasticity",
        "经济",
        "市场",
        "政策",
        "回归",
        "通胀",
        "贸易",
    ],
    "social_science": [
        "survey",
        "interview",
        "participant",
        "qualitative",
        "questionnaire",
        "ethnograph",
        "社会",
        "访谈",
        "问卷",
        "参与者",
        "定性",
    ],
    "engineering": [
        "sensor",
        "control system",
        "robot",
        "manufacturing",
        "prototype",
        "finite element",
        "simulation",
        "工程",
        "传感器",
        "控制系统",
        "机器人",
        "仿真",
    ],
    "humanities": [
        "archive",
        "textual",
        "historical",
        "literature",
        "philosophy",
        "translation",
        "历史",
        "文学",
        "哲学",
        "档案",
        "文本",
    ],
}

DOMAIN_KEYWORD_WEIGHTS: dict[str, dict[str, float]] = {
    domain: {keyword: 1.0 for keyword in keywords} for domain, keywords in DOMAIN_KEYWORDS.items()
}

DOMAIN_KEYWORD_WEIGHTS["computer_science"].update(
    {
        # These are common tools in cross-disciplinary papers, so they should not
        # dominate the paper's subject area by themselves.
        "neural": 0.35,
        "neural network": 0.35,
        "machine learning": 0.35,
        "deep learning": 0.35,
        "dataset": 0.3,
        "datasets": 0.3,
        "baseline": 0.25,
        "training": 0.3,
        "inference": 0.3,
        "accuracy": 0.25,
        "gpu": 0.25,
        "神经网络": 0.35,
        "数据集": 0.3,
        "训练": 0.3,
        "基线": 0.25,
        # These are closer to CS/NLP/ML as the research object.
        "algorithm": 1.4,
        "algorithms": 1.4,
        "transformer": 2.2,
        "transformers": 2.2,
        "attention": 1.4,
        "self-attention": 2.0,
        "encoder": 1.4,
        "decoder": 1.4,
        "sequence transduction": 2.0,
        "machine translation": 2.0,
        "language model": 2.0,
        "natural language processing": 2.0,
        "computer vision": 1.8,
        "repository": 0.8,
        "代码": 0.8,
        "算法": 1.4,
    }
)

DOMAIN_KEYWORD_WEIGHTS["physics"].update(
    {
        "gravitational wave": 2.4,
        "gravitational waves": 2.4,
        "black hole": 2.0,
        "black holes": 2.0,
        "relativity": 1.8,
        "ligo": 1.8,
        "interferometer": 1.6,
        "cosmology": 1.4,
        "particle": 1.4,
        "quantum": 1.4,
    }
)

DOMAIN_KEYWORD_WEIGHTS["chemistry"].update(
    {
        "chemistry": 2.4,
        "chemical": 2.2,
        "molecular": 2.0,
        "molecule": 1.8,
        "molecules": 1.8,
        "atomistic": 1.8,
        "atomic": 1.4,
        "density functional theory": 2.4,
        "dft": 2.4,
        "force field": 2.4,
        "force fields": 2.4,
        "potential energy": 2.0,
        "quantum chemistry": 2.4,
        "ab initio": 1.8,
        "reaction": 1.6,
        "spectra": 1.4,
        "nmr": 1.6,
        "化学": 2.4,
        "分子": 2.0,
        "反应": 1.6,
    }
)

DOMAIN_KEYWORD_WEIGHTS["biology"].update(
    {
        "biological": 2.0,
        "biophysical": 2.0,
        "gene expression": 2.4,
        "cell": 1.6,
        "cells": 1.6,
        "protein": 1.6,
        "genome": 1.8,
    }
)

DOMAIN_KEYWORD_WEIGHTS["medicine"].update(
    {
        "clinical trial": 2.4,
        "clinical trials": 2.4,
        "patient": 1.8,
        "patients": 1.8,
        "survival data": 2.0,
        "hazard ratio": 1.8,
        "treatment": 1.6,
    }
)

DOMAIN_KEYWORD_WEIGHTS["economics"].update(
    {
        "economic": 2.4,
        "economics": 2.4,
        "economic dynamics": 2.8,
        "optimality": 2.0,
        "market": 1.6,
        "equilibrium": 1.8,
        "welfare": 1.8,
        "policy": 1.5,
        "trade": 1.4,
        "labor": 1.4,
        "elasticity": 1.8,
    }
)

DOMAIN_KEYWORD_WEIGHTS["social_science"].update(
    {
        "social science": 2.8,
        "social sciences": 2.8,
        "computational social science": 3.2,
        "sociology": 2.0,
        "political science": 2.0,
        "survey": 1.8,
        "interview": 1.8,
        "participant": 1.5,
        "questionnaire": 1.8,
        "ethnography": 1.8,
    }
)

DOMAIN_KEYWORD_WEIGHTS["engineering"].update(
    {
        "engineering": 2.4,
        "engineered": 1.6,
        "finite element": 2.6,
        "statistical finite element": 3.0,
        "digital twin": 2.6,
        "digital twinning": 2.8,
        "self-sensing": 2.4,
        "structure": 1.4,
        "structures": 1.4,
        "structural": 1.8,
        "sensor": 1.8,
        "sensors": 1.8,
        "prototype": 1.6,
        "control system": 1.8,
    }
)

DOMAIN_KEYWORD_WEIGHTS["humanities"].update(
    {
        "humanities": 2.4,
        "digital humanities": 3.0,
        "historian": 2.6,
        "historians": 2.6,
        "historical": 2.0,
        "history": 1.8,
        "archive": 1.8,
        "archives": 1.8,
        "archival": 2.0,
        "textual": 1.8,
        "literature": 1.8,
        "translation": 0.4,
    }
)

SELECTABLE_DOMAINS = {
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
}


ACADEMIC_SECTION_RE = re.compile(
    r"\b(abstract|introduction|methods?|methodology|materials and methods|results?|discussion|conclusion|references|bibliography|appendix)\b",
    re.IGNORECASE,
)
CITATION_RE = re.compile(r"(\[[0-9,\s-]{1,20}\]|\([A-Z][A-Za-z-]+ et al\.,? \d{4}\)|doi:|arxiv:)", re.IGNORECASE)
JOKE_RE = re.compile(r"(lorem ipsum|rickroll|just kidding|恶搞|整活|哈哈哈|不是论文|meme|banana)", re.IGNORECASE)


@dataclass
class DocumentClassification:
    document_type: str
    domain: str
    is_academic_paper: bool
    confidence: float
    signals: list[str]
    warnings: list[str]
    guidance: str

    def model_dump(self) -> dict[str, object]:
        return {
            "document_type": self.document_type,
            "domain": self.domain,
            "is_academic_paper": self.is_academic_paper,
            "confidence": self.confidence,
            "signals": self.signals,
            "warnings": self.warnings,
            "guidance": self.guidance,
        }


def classify_document(parsed: ParsedPaper) -> DocumentClassification:
    text = re.sub(r"\s+", " ", parsed.full_text or "").strip()
    lower_text = text.lower()
    signals: list[str] = []
    warnings: list[str] = []

    if len(text) < 300:
        return DocumentClassification(
            document_type="empty_or_unreadable",
            domain="unknown",
            is_academic_paper=False,
            confidence=0.95,
            signals=["PDF text extraction returned very little content."],
            warnings=["无法从 PDF 中提取足够文字，可能是扫描件、图片型 PDF、空白文件或非论文材料。"],
            guidance="请上传可复制文字的论文 PDF，或补充 OCR 后的文本/材料；当前只能给出文件诊断与下一步建议。",
        )

    section_hits = len(ACADEMIC_SECTION_RE.findall(text))
    citation_hits = len(CITATION_RE.findall(text))
    has_abstract = bool(parsed.abstract) or "abstract" in lower_text or "摘要" in text
    has_references = "references" in lower_text or "bibliography" in lower_text or "参考文献" in text
    domain_scores = _score_domains(lower_text, parsed.title, parsed.abstract)
    domain, domain_score = _best_domain(domain_scores)
    joke_hits = len(JOKE_RE.findall(text))

    if has_abstract:
        signals.append("检测到摘要/Abstract。")
    if section_hits:
        signals.append(f"检测到 {section_hits} 个常见学术章节信号。")
    if citation_hits:
        signals.append(f"检测到 {citation_hits} 个引用/DOI/arXiv 信号。")
    if has_references:
        signals.append("检测到参考文献区域。")
    if domain_score:
        signals.append(f"学科关键词更接近 {domain}。")
    if joke_hits:
        signals.append("检测到疑似恶搞或占位文本信号。")

    academic_score = 0
    academic_score += 2 if has_abstract else 0
    academic_score += min(section_hits, 8)
    academic_score += 2 if has_references else 0
    academic_score += min(citation_hits, 6)
    academic_score += 1 if len(text) > 2500 else 0
    academic_score -= min(joke_hits * 3, 6)

    if joke_hits and academic_score < 6:
        warnings.append("文本里有明显恶搞/占位内容信号，不应按真实学术论文解读。")

    if academic_score < 3:
        return DocumentClassification(
            document_type="non_academic",
            domain="non_academic",
            is_academic_paper=False,
            confidence=_bounded_confidence(0.65 + 0.05 * max(0, 3 - academic_score)),
            signals=signals or ["未检测到稳定的论文结构、引用或实验/推导线索。"],
            warnings=warnings + ["该 PDF 不像可复现分析所需的学术论文，疑似非论文材料。"],
            guidance="请确认上传的是论文正文；如果这是讲义、报告、宣传页或玩笑文本，系统会先指出不适配之处，而不是编造实验结论。",
        )

    document_type = _document_type(lower_text, section_hits, has_abstract, has_references)
    confidence = _bounded_confidence(0.52 + math.log1p(max(academic_score, 1)) / 5 + min(domain_score, 8) / 40)
    if domain == "unknown":
        warnings.append("学科关键词不集中，将按通用科研论文处理。")

    return DocumentClassification(
        document_type=document_type,
        domain=domain,
        is_academic_paper=True,
        confidence=confidence,
        signals=signals or ["检测到足够长的论文式正文。"],
        warnings=warnings,
        guidance=_domain_guidance(domain),
    )


def apply_domain_choice(classification: DocumentClassification, analysis_domain: str | None) -> DocumentClassification:
    if not analysis_domain or analysis_domain == "auto" or analysis_domain not in SELECTABLE_DOMAINS:
        return classification
    if not classification.is_academic_paper:
        return classification

    signals = [
        *classification.signals,
        f"用户手动选择分析方向：{analysis_domain}。",
    ]
    warnings = list(classification.warnings)
    if classification.domain not in {"unknown", "general", analysis_domain}:
        warnings.append(f"自动分类倾向 {classification.domain}，但本次分析按用户选择的 {analysis_domain} 执行。")

    return replace(
        classification,
        domain=analysis_domain,
        confidence=0.99,
        signals=signals,
        warnings=warnings,
        guidance=_domain_guidance(analysis_domain),
    )


def _score_domains(lower_text: str, title: str = "", abstract: str = "") -> Counter[str]:
    scores: Counter[str] = Counter()
    body_text = lower_text.lower()
    focus_text = f"{title} {abstract}".lower()
    if not focus_text.strip():
        focus_text = body_text[:2400]

    for domain, keyword_weights in DOMAIN_KEYWORD_WEIGHTS.items():
        for keyword, weight in keyword_weights.items():
            body_hits = _keyword_hits(body_text, keyword, cap=2)
            focus_hits = _keyword_hits(focus_text, keyword, cap=2)
            if not body_hits and not focus_hits:
                continue
            scores[domain] += weight * (body_hits + focus_hits * 2.4)
    return scores


def _best_domain(scores: Counter[str]) -> tuple[str, float]:
    if not scores:
        return "unknown", 0
    domain, score = scores.most_common(1)[0]
    if domain == "computer_science":
        non_cs = [(name, value) for name, value in scores.most_common() if name != "computer_science"]
        if non_cs:
            runner_up, runner_up_score = non_cs[0]
            if runner_up_score >= 4 and score - runner_up_score <= 2.5:
                return runner_up, runner_up_score
    if score < 2:
        return "unknown", score
    return domain, score


def _keyword_hits(text: str, keyword: str, cap: int) -> int:
    lowered = keyword.lower()
    if _has_cjk(lowered):
        return min(text.count(lowered), cap)
    pattern = rf"(?<![a-z0-9]){re.escape(lowered)}(?![a-z0-9])"
    return min(len(re.findall(pattern, text)), cap)


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _document_type(lower_text: str, section_hits: int, has_abstract: bool, has_references: bool) -> str:
    opening = lower_text[:1600]
    if "survey" in opening or "综述" in opening or "review paper" in opening or "systematic review" in opening:
        return "review_paper"
    if "thesis" in lower_text or "dissertation" in lower_text or "学位论文" in lower_text:
        return "thesis_or_report"
    if has_abstract and has_references and section_hits >= 4:
        return "research_paper"
    return "academic_like_document"


def _domain_guidance(domain: str) -> str:
    guidance = {
        "computer_science": "按计算机科学论文处理，但只有论文确实涉及代码、训练或数据集时才讨论这些内容。",
        "physics": "按物理学论文处理，重点关注物理问题、理论模型、关键方程、样品/装置、观测量、单位、误差和不确定度。",
        "mathematics": "按数学论文处理，重点关注定义、定理、引理、证明结构、构造例子和可验证推导，而不是实验复现。",
        "chemistry": "按化学论文处理，重点关注试剂、合成路线、反应条件、表征手段、谱图和可重复实验步骤。",
        "biology": "按生物学论文处理，重点关注样本、实验条件、 assay、对照组、统计方法和材料可获得性。",
        "medicine": "按医学论文处理，重点关注研究设计、病例/队列、纳排标准、干预、终点指标、伦理和统计检验。",
        "economics": "按经济学论文处理，重点关注数据来源、识别策略、回归设定、稳健性检验和可复现实证流程。",
        "social_science": "按社会科学论文处理，重点关注研究问题、样本/访谈/问卷、变量编码、伦理和分析方法。",
        "engineering": "按工程论文处理，重点关注系统结构、材料/设备、参数、仿真或实验设置、测量指标和误差来源。",
        "humanities": "按人文学术文章处理，重点关注材料来源、论证结构、文本/档案证据和可核查引用。",
        "general": "按通用科研论文处理，由用户后续补充材料和正文证据决定分析重点。",
    }
    return guidance.get(domain, "按通用科研论文处理，避免默认套用计算机科学或机器学习复现实验范式。")


def _bounded_confidence(value: float) -> float:
    return round(min(max(value, 0.0), 0.99), 2)
