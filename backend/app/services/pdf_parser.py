import re
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class ParsedPaper:
    title: str
    abstract: str
    sections: list[str]
    pages: list[dict[str, str | int]]
    full_text: str
    page_count: int


SECTION_HEADING_RE = re.compile(
    r"^\s*((\d+(\.\d+)*)\s+)?(abstract|introduction|related work|background|method|methodology|approach|experiments?|results?|discussion|conclusion|limitations?|references)\s*$",
    re.IGNORECASE,
)


def parse_pdf(file_path: str | Path) -> ParsedPaper:
    path = Path(file_path)
    with fitz.open(path) as doc:
        metadata_title = (doc.metadata or {}).get("title") or ""
        pages = []
        full_text_parts = []
        for page_index, page in enumerate(doc):
            text = page.get_text("text")
            pages.append({"page": page_index + 1, "text": text})
            full_text_parts.append(text)

    full_text = "\n".join(full_text_parts)
    first_page_text = pages[0]["text"] if pages else ""
    title = _extract_title(metadata_title, str(first_page_text))
    abstract = _extract_abstract(full_text)
    sections = _extract_sections(full_text)

    return ParsedPaper(
        title=title,
        abstract=abstract,
        sections=sections,
        pages=pages,
        full_text=full_text,
        page_count=len(pages),
    )


def _extract_title(metadata_title: str, first_page_text: str) -> str:
    cleaned_metadata = metadata_title.strip()
    if cleaned_metadata and len(cleaned_metadata) > 5 and not cleaned_metadata.lower().endswith(".pdf"):
        return cleaned_metadata[:240]

    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    candidates = []
    for line in lines[:20]:
        normalized = re.sub(r"\s+", " ", line)
        if 8 <= len(normalized) <= 220 and not re.search(r"@|arxiv|proceedings|university", normalized, re.I):
            candidates.append(normalized)
    return candidates[0] if candidates else "Untitled Paper"


def _extract_abstract(full_text: str) -> str:
    text = re.sub(r"\r", "\n", full_text)
    match = re.search(
        r"\babstract\b\s*[:.\-]?\s*(?P<body>.*?)(?=\n\s*(?:1\s+)?(?:introduction|keywords|index terms|background)\b)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    body = re.sub(r"\s+", " ", match.group("body")).strip()
    return body[:1200]


def _extract_sections(full_text: str) -> list[str]:
    sections: list[str] = []
    seen: set[str] = set()
    for line in full_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or len(line) > 90:
            continue
        is_numbered = bool(re.match(r"^\d+(\.\d+)*\s+[A-Z][A-Za-z0-9 ,:/-]{2,}$", line))
        is_known = bool(SECTION_HEADING_RE.match(line))
        if is_numbered or is_known:
            normalized = line.strip()
            key = normalized.lower()
            if key not in seen:
                sections.append(normalized)
                seen.add(key)
        if len(sections) >= 24:
            break
    return sections


def extract_focus_chunks(parsed: ParsedPaper, max_chars: int = 18000) -> str:
    """Keep high-signal paper regions small enough for one MVP LLM call."""
    candidates = [
        ("Title", parsed.title),
        ("Abstract", parsed.abstract),
    ]
    section_names = [
        "introduction",
        "related work",
        "background",
        "method",
        "methodology",
        "approach",
        "experiment",
        "results",
        "conclusion",
        "limitation",
    ]
    lower_text = parsed.full_text.lower()
    for name in section_names:
        index = lower_text.find(name)
        if index >= 0:
            chunk = parsed.full_text[index : index + 2200]
            candidates.append((name.title(), chunk))

    rendered = "\n\n".join(f"## {label}\n{text.strip()}" for label, text in candidates if text.strip())
    if len(rendered) < 1000:
        rendered = parsed.full_text[:max_chars]
    return rendered[:max_chars]

