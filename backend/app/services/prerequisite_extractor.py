import re
from collections import Counter
from typing import Any

from app.services.pdf_parser import ParsedPaper


TERM_BANK: dict[str, list[dict[str, str]]] = {
    "general": [
        {
            "term": "研究问题",
            "aliases": "research question,problem statement",
            "category": "论文结构",
            "why_it_matters": "它决定论文到底想解决什么，后面的模型、实验和结论都要围绕它判断。",
            "difficulty": "low",
        },
        {
            "term": "假设",
            "aliases": "assumption,hypothesis",
            "category": "方法基础",
            "why_it_matters": "很多结论只在特定假设下成立，复现或核查时要先确认这些前提。",
            "difficulty": "low",
        },
        {
            "term": "模型",
            "aliases": "model,framework",
            "category": "方法基础",
            "why_it_matters": "模型描述论文如何把输入、材料或现象转化为可验证的结果。",
            "difficulty": "low",
        },
        {
            "term": "基线 / 对照",
            "aliases": "baseline,control group,comparison",
            "category": "证据判断",
            "why_it_matters": "没有基线或对照，就很难判断本文方法、实验或论证是否真的有增量。",
            "difficulty": "medium",
        },
        {
            "term": "评价指标",
            "aliases": "metric,evaluation measure,outcome",
            "category": "证据判断",
            "why_it_matters": "指标定义会影响论文声称的改进、显著性或有效性。",
            "difficulty": "medium",
        },
        {
            "term": "不确定度 / 误差",
            "aliases": "uncertainty,error,confidence interval",
            "category": "证据判断",
            "why_it_matters": "误差和不确定度决定结果是否稳定，尤其影响实验、观测和统计结论。",
            "difficulty": "medium",
        },
        {
            "term": "显著性",
            "aliases": "significance,statistically significant,p-value,p value",
            "category": "统计基础",
            "why_it_matters": "显著性用于判断观察到的差异是否可能只是随机波动。",
            "difficulty": "high",
        },
    ],
    "computer_science": [
        {
            "term": "算法",
            "aliases": "algorithm,algorithms",
            "category": "方法基础",
            "why_it_matters": "算法是论文方法如何执行的核心，复现时需要拆清输入、步骤和输出。",
            "difficulty": "low",
        },
        {
            "term": "数据集",
            "aliases": "dataset,datasets,corpus,benchmark",
            "category": "实验基础",
            "why_it_matters": "数据来源、划分和预处理会直接影响实验结果。",
            "difficulty": "low",
        },
        {
            "term": "神经网络",
            "aliases": "neural network,neural networks,deep learning",
            "category": "模型基础",
            "why_it_matters": "若论文使用深度学习，需要理解网络如何表示和变换数据。",
            "difficulty": "medium",
        },
        {
            "term": "损失函数",
            "aliases": "loss function,objective function,training objective",
            "category": "训练基础",
            "why_it_matters": "损失函数定义模型优化目标，是复现实验时最容易影响结果的细节之一。",
            "difficulty": "medium",
        },
        {
            "term": "注意力机制",
            "aliases": "attention,self-attention,multi-head attention",
            "category": "模型基础",
            "why_it_matters": "许多现代模型靠注意力机制建模不同输入之间的依赖关系。",
            "difficulty": "high",
        },
        {
            "term": "Transformer",
            "aliases": "transformer,transformers",
            "category": "模型基础",
            "why_it_matters": "Transformer 是大量 NLP、视觉和多模态论文的基础架构。",
            "difficulty": "high",
        },
        {
            "term": "消融实验",
            "aliases": "ablation,ablation study",
            "category": "实验判断",
            "why_it_matters": "消融实验用来证明方法中的某个组件是否真的有贡献。",
            "difficulty": "medium",
        },
    ],
    "physics": [
        {
            "term": "哈密顿量",
            "aliases": "hamiltonian",
            "category": "理论基础",
            "why_it_matters": "哈密顿量刻画系统能量和演化规律，是理解许多物理论文公式的入口。",
            "difficulty": "high",
        },
        {
            "term": "量子态",
            "aliases": "quantum state,wave function,wavefunction",
            "category": "理论基础",
            "why_it_matters": "量子态描述系统状态，决定可观测量和测量概率。",
            "difficulty": "medium",
        },
        {
            "term": "散射",
            "aliases": "scattering",
            "category": "实验 / 理论",
            "why_it_matters": "散射实验常用于推断粒子、材料或波的相互作用机制。",
            "difficulty": "medium",
        },
        {
            "term": "光谱",
            "aliases": "spectrum,spectra,spectroscopy",
            "category": "实验基础",
            "why_it_matters": "光谱信息常用于识别能级、材料性质或信号来源。",
            "difficulty": "medium",
        },
        {
            "term": "自旋",
            "aliases": "spin",
            "category": "理论基础",
            "why_it_matters": "自旋影响磁性、量子态和相互作用，是许多凝聚态和粒子物理论文的关键变量。",
            "difficulty": "high",
        },
        {
            "term": "晶格",
            "aliases": "lattice",
            "category": "模型基础",
            "why_it_matters": "晶格结构决定材料或模型中的空间组织方式。",
            "difficulty": "medium",
        },
        {
            "term": "引力波",
            "aliases": "gravitational wave,gravitational waves",
            "category": "物理现象",
            "why_it_matters": "如果论文涉及天体物理观测，引力波概念会影响信号来源和探测方法的理解。",
            "difficulty": "medium",
        },
    ],
    "mathematics": [
        {
            "term": "定理",
            "aliases": "theorem,theorems",
            "category": "证明结构",
            "why_it_matters": "定理是论文要证明的主要结论，需要同时看清前提和结论。",
            "difficulty": "low",
        },
        {
            "term": "引理",
            "aliases": "lemma,lemmas",
            "category": "证明结构",
            "why_it_matters": "引理是主定理的支撑步骤，理解引理之间的依赖能还原证明路线。",
            "difficulty": "medium",
        },
        {
            "term": "流形",
            "aliases": "manifold,manifolds",
            "category": "核心概念",
            "why_it_matters": "流形是几何和拓扑论文中的基本研究对象。",
            "difficulty": "high",
        },
        {
            "term": "曲率",
            "aliases": "curvature,ricci curvature",
            "category": "核心概念",
            "why_it_matters": "曲率描述空间弯曲方式，在几何分析和 Ricci flow 中尤其关键。",
            "difficulty": "high",
        },
        {
            "term": "算子",
            "aliases": "operator,operators",
            "category": "核心概念",
            "why_it_matters": "算子描述对象之间的变换，是很多分析、代数和 PDE 论文的基础语言。",
            "difficulty": "medium",
        },
        {
            "term": "收敛",
            "aliases": "convergence,convergent",
            "category": "证明工具",
            "why_it_matters": "收敛用于判断序列、函数或过程是否趋向目标对象。",
            "difficulty": "medium",
        },
    ],
    "chemistry": [
        {
            "term": "分子",
            "aliases": "molecule,molecular",
            "category": "核心概念",
            "why_it_matters": "分子结构决定反应、性质和表征结果。",
            "difficulty": "low",
        },
        {
            "term": "合成路线",
            "aliases": "synthesis,synthetic route",
            "category": "实验基础",
            "why_it_matters": "合成步骤和条件是化学论文能否复现实验的核心。",
            "difficulty": "medium",
        },
        {
            "term": "催化剂",
            "aliases": "catalyst,catalysis",
            "category": "反应基础",
            "why_it_matters": "催化剂会改变反应速率、选择性和实验条件。",
            "difficulty": "medium",
        },
        {
            "term": "NMR 光谱",
            "aliases": "nmr,nuclear magnetic resonance",
            "category": "表征方法",
            "why_it_matters": "NMR 常用于确认分子结构和反应产物。",
            "difficulty": "high",
        },
        {
            "term": "色谱",
            "aliases": "chromatography,hplc,gc-ms,gc ms",
            "category": "表征方法",
            "why_it_matters": "色谱用于分离和定量物质，影响产率与纯度判断。",
            "difficulty": "medium",
        },
    ],
    "biology": [
        {
            "term": "基因表达",
            "aliases": "gene expression,expression",
            "category": "核心概念",
            "why_it_matters": "基因表达描述遗传信息如何转化为功能分子，是理解生物机制的入口。",
            "difficulty": "medium",
        },
        {
            "term": "蛋白质",
            "aliases": "protein,proteins",
            "category": "核心概念",
            "why_it_matters": "蛋白质承担大量细胞功能，常是生物实验观察的关键对象。",
            "difficulty": "low",
        },
        {
            "term": "基因组",
            "aliases": "genome,genomic",
            "category": "核心概念",
            "why_it_matters": "基因组背景决定样本差异和遗传分析方式。",
            "difficulty": "medium",
        },
        {
            "term": "实验 assay",
            "aliases": "assay,assays",
            "category": "实验方法",
            "why_it_matters": "assay 定义论文如何测量某个生物现象或功能。",
            "difficulty": "medium",
        },
        {
            "term": "突变",
            "aliases": "mutation,mutant",
            "category": "机制判断",
            "why_it_matters": "突变常用于定位基因或蛋白对表型的影响。",
            "difficulty": "medium",
        },
    ],
    "medicine": [
        {
            "term": "临床试验",
            "aliases": "clinical trial,trial",
            "category": "研究设计",
            "why_it_matters": "临床试验设计决定证据强度、偏倚风险和结论适用范围。",
            "difficulty": "low",
        },
        {
            "term": "队列",
            "aliases": "cohort",
            "category": "研究设计",
            "why_it_matters": "队列定义研究对象如何被纳入和跟踪，影响因果解释。",
            "difficulty": "medium",
        },
        {
            "term": "生存分析",
            "aliases": "survival analysis,survival",
            "category": "统计基础",
            "why_it_matters": "生存分析用于处理事件发生时间和删失数据。",
            "difficulty": "high",
        },
        {
            "term": "风险比",
            "aliases": "hazard ratio,relative risk,odds ratio",
            "category": "统计基础",
            "why_it_matters": "风险比类指标用于解释治疗、暴露或干预对结局的影响大小。",
            "difficulty": "high",
        },
        {
            "term": "终点指标",
            "aliases": "endpoint,outcome",
            "category": "证据判断",
            "why_it_matters": "终点指标决定论文真正评估的是疗效、安全性还是其他临床结果。",
            "difficulty": "medium",
        },
    ],
    "economics": [
        {
            "term": "回归",
            "aliases": "regression",
            "category": "统计基础",
            "why_it_matters": "回归是经济学实证论文估计变量关系的常用工具。",
            "difficulty": "medium",
        },
        {
            "term": "识别策略",
            "aliases": "identification strategy,identification",
            "category": "因果推断",
            "why_it_matters": "识别策略说明论文如何把相关关系解释为因果关系。",
            "difficulty": "high",
        },
        {
            "term": "弹性",
            "aliases": "elasticity",
            "category": "经济概念",
            "why_it_matters": "弹性衡量一个变量对另一个变量变化的敏感程度。",
            "difficulty": "medium",
        },
        {
            "term": "市场均衡",
            "aliases": "market equilibrium,equilibrium",
            "category": "经济概念",
            "why_it_matters": "均衡概念用于理解供需、策略互动或动态系统的稳定状态。",
            "difficulty": "medium",
        },
        {
            "term": "工具变量",
            "aliases": "instrumental variable,iv",
            "category": "因果推断",
            "why_it_matters": "工具变量常用于处理内生性，但需要满足严格假设。",
            "difficulty": "high",
        },
    ],
    "social_science": [
        {
            "term": "问卷",
            "aliases": "survey,questionnaire",
            "category": "研究方法",
            "why_it_matters": "问卷设计影响变量测量、样本偏差和结论解释。",
            "difficulty": "low",
        },
        {
            "term": "访谈",
            "aliases": "interview,interviews",
            "category": "研究方法",
            "why_it_matters": "访谈材料通常需要结合抽样、编码和伦理审查来判断可靠性。",
            "difficulty": "low",
        },
        {
            "term": "定性编码",
            "aliases": "qualitative coding,coding",
            "category": "分析方法",
            "why_it_matters": "编码规则决定文本、访谈或观察材料如何变成可分析证据。",
            "difficulty": "medium",
        },
        {
            "term": "抽样",
            "aliases": "sampling,sample,participants",
            "category": "研究设计",
            "why_it_matters": "抽样方式决定研究结论能否推广到更大群体。",
            "difficulty": "medium",
        },
        {
            "term": "伦理审查",
            "aliases": "ethics,irb,informed consent",
            "category": "研究规范",
            "why_it_matters": "涉及参与者的数据需要关注同意、隐私和潜在风险。",
            "difficulty": "medium",
        },
    ],
    "engineering": [
        {
            "term": "传感器",
            "aliases": "sensor,sensors",
            "category": "系统组件",
            "why_it_matters": "传感器决定系统如何获得测量信号和误差来源。",
            "difficulty": "low",
        },
        {
            "term": "控制系统",
            "aliases": "control system,control systems,controller",
            "category": "系统方法",
            "why_it_matters": "控制系统描述输入、反馈和输出如何形成稳定行为。",
            "difficulty": "medium",
        },
        {
            "term": "有限元",
            "aliases": "finite element,fem",
            "category": "仿真方法",
            "why_it_matters": "有限元用于把连续结构离散成可计算模型，是许多工程仿真的核心。",
            "difficulty": "high",
        },
        {
            "term": "标定",
            "aliases": "calibration,calibrated",
            "category": "实验基础",
            "why_it_matters": "标定决定测量值是否可信，直接影响实验复现。",
            "difficulty": "medium",
        },
        {
            "term": "数字孪生",
            "aliases": "digital twin,digital twinning",
            "category": "系统方法",
            "why_it_matters": "数字孪生把真实系统和计算模型连接起来，用于预测、监测或控制。",
            "difficulty": "high",
        },
    ],
    "humanities": [
        {
            "term": "档案",
            "aliases": "archive,archives,archival",
            "category": "材料基础",
            "why_it_matters": "档案来源和保存方式会影响史料或文本证据的解释。",
            "difficulty": "low",
        },
        {
            "term": "语料库",
            "aliases": "corpus,corpora",
            "category": "材料基础",
            "why_it_matters": "语料库定义文本样本的范围、偏差和可重复分析条件。",
            "difficulty": "medium",
        },
        {
            "term": "文本分析",
            "aliases": "textual analysis,text analysis",
            "category": "分析方法",
            "why_it_matters": "文本分析方法决定研究如何从材料中得到解释性结论。",
            "difficulty": "medium",
        },
        {
            "term": "史学方法",
            "aliases": "historiography,historical method",
            "category": "理论背景",
            "why_it_matters": "史学方法影响论文如何使用证据、叙述因果和处理争议。",
            "difficulty": "high",
        },
        {
            "term": "元数据",
            "aliases": "metadata",
            "category": "材料基础",
            "why_it_matters": "元数据帮助追溯材料来源、时间、作者和版本。",
            "difficulty": "medium",
        },
    ],
}

DOMAIN_LABELS = {
    "computer_science": "计算机科学",
    "physics": "物理学",
    "mathematics": "数学",
    "chemistry": "化学",
    "biology": "生物学",
    "medicine": "医学",
    "economics": "经济学",
    "social_science": "社会科学",
    "engineering": "工程学",
    "humanities": "人文学科",
    "general": "通用科研",
}

LEVEL_WEIGHTS = {
    "beginner": {"low": 4, "medium": 2, "high": 1},
    "intermediate": {"low": 2, "medium": 4, "high": 3},
    "advanced": {"low": 1, "medium": 3, "high": 4},
}

STOP_PHRASES = {
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "references",
    "appendix",
    "figure",
    "table",
    "university",
    "department",
    "preprint",
}

STOP_EDGE_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "using",
    "via",
    "with",
}

STOP_START_WORDS = {
    "we",
    "this",
    "that",
    "these",
    "those",
    "our",
}


def extract_prerequisite_terms(
    parsed_paper: ParsedPaper,
    domain: str,
    knowledge_level: str = "intermediate",
    max_terms: int = 12,
) -> list[dict[str, Any]]:
    """Return fast, deterministic prerequisite terms grounded in the uploaded paper text."""
    normalized_domain = domain if domain in TERM_BANK else "general"
    normalized_level = knowledge_level if knowledge_level in LEVEL_WEIGHTS else "intermediate"
    text = _focus_text(parsed_paper)
    lower_text = text.lower()
    candidates: list[tuple[int, dict[str, str]]] = []

    for entry in [*TERM_BANK["general"], *TERM_BANK.get(normalized_domain, [])]:
        count = _count_mentions(lower_text, entry["term"], entry.get("aliases", ""))
        if count <= 0:
            continue
        difficulty = entry["difficulty"]
        level_weight = LEVEL_WEIGHTS[normalized_level].get(difficulty, 1)
        score = count * 5 + level_weight
        candidates.append((score, entry))

    ranked = _dedupe_ranked(candidates)
    if len(ranked) < min(8, max_terms):
        ranked.extend(_fallback_candidates(text, normalized_domain, existing={item["term"].lower() for item in ranked}))

    ranked = ranked[:max_terms]
    if ranked:
        return ranked

    return _default_terms(normalized_domain, normalized_level, max_terms)


def _focus_text(parsed_paper: ParsedPaper) -> str:
    pieces = [parsed_paper.title, parsed_paper.abstract, parsed_paper.full_text[:12000]]
    return "\n".join(piece for piece in pieces if piece).strip()


def _count_mentions(lower_text: str, term: str, aliases: str) -> int:
    mentions = 0
    for alias in [term, *[item.strip() for item in aliases.split(",") if item.strip()]]:
        lowered = alias.lower()
        if _has_cjk(lowered):
            mentions += lower_text.count(lowered)
        else:
            mentions += len(re.findall(rf"(?<![a-z0-9]){re.escape(lowered)}(?![a-z0-9])", lower_text))
    return mentions


def _dedupe_ranked(candidates: list[tuple[int, dict[str, str]]]) -> list[dict[str, Any]]:
    best: dict[str, tuple[int, dict[str, str]]] = {}
    for score, entry in candidates:
        key = entry["term"].lower()
        previous = best.get(key)
        if not previous or score > previous[0]:
            best[key] = (score, entry)

    ordered = sorted(best.values(), key=lambda item: (-item[0], item[1]["term"]))
    return [
        {
            "term": entry["term"],
            "category": entry["category"],
            "why_it_matters": entry["why_it_matters"],
            "difficulty": entry["difficulty"],
        }
        for _, entry in ordered
    ]


def _fallback_candidates(text: str, domain: str, existing: set[str]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    compact = re.sub(r"\s+", " ", text[:10000])
    for match in re.finditer(r"\b[A-Z][A-Za-z0-9]+(?:[- ][A-Za-z0-9]+){0,3}\b", compact):
        phrase = _trim_candidate_phrase(match.group(0).strip(" -"))
        normalized = phrase.lower()
        if _skip_phrase(normalized, phrase):
            continue
        counter[phrase] += 1
    for match in re.finditer(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)?\b", compact):
        phrase = match.group(0).strip()
        normalized = phrase.lower()
        if _skip_phrase(normalized, phrase):
            continue
        counter[phrase] += 2

    domain_label = DOMAIN_LABELS.get(domain, "该领域")
    terms: list[dict[str, Any]] = []
    for phrase, _ in counter.most_common(8):
        if phrase.lower() in existing:
            continue
        terms.append(
            {
                "term": phrase,
                "category": "论文关键词",
                "why_it_matters": f"这个词在论文中反复出现，可能是理解{domain_label}方法、材料或结论的入口。",
                "difficulty": "medium" if len(phrase) < 18 else "high",
            }
        )
    return terms


def _default_terms(domain: str, knowledge_level: str, max_terms: int) -> list[dict[str, Any]]:
    entries = [*TERM_BANK["general"], *TERM_BANK.get(domain, [])]
    weights = LEVEL_WEIGHTS[knowledge_level]
    ordered = sorted(entries, key=lambda item: (-weights.get(item["difficulty"], 1), item["term"]))
    return [
        {
            "term": item["term"],
            "category": item["category"],
            "why_it_matters": item["why_it_matters"],
            "difficulty": item["difficulty"],
        }
        for item in ordered[:max_terms]
    ]


def _skip_phrase(normalized: str, original: str) -> bool:
    if len(original) < 3 or len(original) > 48:
        return True
    if normalized in STOP_PHRASES:
        return True
    if any(part in STOP_PHRASES for part in normalized.split()):
        return True
    if original.isdigit():
        return True
    return False


def _trim_candidate_phrase(phrase: str) -> str:
    parts = phrase.split()
    while parts and parts[0].lower() in STOP_START_WORDS:
        parts.pop(0)
    while parts and parts[-1].lower() in STOP_EDGE_WORDS:
        parts.pop()
    return " ".join(parts)


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)
