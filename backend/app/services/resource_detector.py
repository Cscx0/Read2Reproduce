import re

from app.schemas import DetectedResource


URL_RE = re.compile(r"https?://[^\s\]\)\}>\"']+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,;:!?'\""
CODE_HINT_RE = re.compile(
    r"(code|source code|implementation|repository|repo|github|gitlab|available at|released at)",
    re.IGNORECASE,
)
SUPPLEMENT_RE = re.compile(r"(supplementary|supplemental|appendix|artifact|project page)", re.IGNORECASE)


def detect_resources(text: str) -> list[DetectedResource]:
    resources: list[DetectedResource] = []
    seen: set[tuple[str, str]] = set()

    for match in URL_RE.finditer(text):
        url = _clean_url(match.group(0))
        context = text[max(0, match.start() - 180) : min(len(text), match.end() + 180)]
        resource = _classify_url(url, context)
        key = (resource.type, resource.url)
        if key not in seen:
            resources.append(resource)
            seen.add(key)

    for phrase in _detect_textual_hints(text):
        key = (phrase.type, phrase.note or "")
        if key not in seen:
            resources.append(phrase)
            seen.add(key)

    return sorted(resources, key=lambda item: item.confidence, reverse=True)


def has_code_resource(resources: list[DetectedResource]) -> bool:
    decisive_types = {"github", "gitlab", "huggingface", "code_repository"}
    return any(resource.type in decisive_types and resource.confidence >= 0.65 for resource in resources)


def _clean_url(url: str) -> str:
    cleaned = url.strip().rstrip(TRAILING_PUNCTUATION)
    while cleaned.endswith((")", "]")) and cleaned.count("(") < cleaned.count(")"):
        cleaned = cleaned[:-1]
    return cleaned


def _classify_url(url: str, context: str) -> DetectedResource:
    lowered = url.lower()
    context_lower = context.lower()

    if "github.com" in lowered:
        confidence = 0.96 if re.search(r"github\.com/[^/\s]+/[^/\s#?]+", lowered) else 0.82
        return DetectedResource(type="github", url=url, confidence=confidence, note=_snippet(context))

    if "gitlab.com" in lowered:
        confidence = 0.94 if re.search(r"gitlab\.com/[^/\s]+/[^/\s#?]+", lowered) else 0.8
        return DetectedResource(type="gitlab", url=url, confidence=confidence, note=_snippet(context))

    if "huggingface.co" in lowered:
        return DetectedResource(type="huggingface", url=url, confidence=0.88, note=_snippet(context))

    if CODE_HINT_RE.search(context_lower):
        return DetectedResource(type="code_repository", url=url, confidence=0.78, note=_snippet(context))

    if "project" in context_lower or "demo" in context_lower or "homepage" in context_lower:
        return DetectedResource(type="project_page", url=url, confidence=0.7, note=_snippet(context))

    if SUPPLEMENT_RE.search(context_lower):
        return DetectedResource(type="supplementary_material", url=url, confidence=0.68, note=_snippet(context))

    return DetectedResource(type="url", url=url, confidence=0.35, note=_snippet(context))


def _detect_textual_hints(text: str) -> list[DetectedResource]:
    hints: list[DetectedResource] = []
    patterns = [
        ("code_mention", r"(code|implementation|source code)\s+(is|are|will be)\s+(publicly\s+)?available", 0.48),
        ("supplementary_material", r"(supplementary|supplemental)\s+(material|appendix|file|document)", 0.52),
        ("project_page_mention", r"(project|demo)\s+(page|website|homepage)", 0.46),
    ]
    for resource_type, pattern, confidence in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            context = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)]
            hints.append(
                DetectedResource(
                    type=resource_type,
                    url="",
                    confidence=confidence,
                    note=_snippet(context),
                )
            )
    return hints


def _snippet(context: str) -> str:
    return re.sub(r"\s+", " ", context).strip()[:260]

