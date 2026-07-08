import re
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import DetectedResource


GITHUB_RE = re.compile(r"github\.com/(?P<owner>[^/\s#?]+)/(?P<repo>[^/\s#?]+)", re.IGNORECASE)


async def analyze_detected_resources(resources: list[DetectedResource]) -> dict[str, Any]:
    github_urls = [resource.url for resource in resources if resource.type == "github" and resource.url]
    if not github_urls:
        return {"available": False, "message": "未检测到 GitHub 仓库。"}

    repo_url = github_urls[0]
    parsed = _parse_github_repo(repo_url)
    if not parsed:
        return {"available": False, "message": f"无法解析 GitHub 仓库地址：{repo_url}"}

    owner, repo = parsed
    headers = {"Accept": "application/vnd.github+json"}
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
            repo_meta = await _get_repo_meta(client, owner, repo)
            branch = repo_meta.get("default_branch") or "main"
            readme = await _get_readme(client, owner, repo, branch)
            tree = await _get_file_tree(client, owner, repo, branch)
            important_files = _select_important_files(tree)

        return {
            "available": True,
            "repo_url": f"https://github.com/{owner}/{repo}",
            "owner": owner,
            "repo": repo,
            "default_branch": branch,
            "description": repo_meta.get("description") or "",
            "readme": readme[:12000],
            "file_tree": tree[:400],
            "important_files": important_files,
            "dependency_files": _filter_paths(important_files, ["requirements", "environment", "setup.py", "pyproject", "package.json"]),
            "config_files": _filter_paths(important_files, ["config", ".yaml", ".yml", ".json", ".toml"]),
            "message": "已读取 GitHub 仓库公开 README 和文件树。",
        }
    except Exception as exc:
        return {
            "available": False,
            "repo_url": f"https://github.com/{owner}/{repo}",
            "message": f"仓库无法读取，但仍可基于论文分析。原因：{exc.__class__.__name__}",
        }


def _parse_github_repo(url: str) -> tuple[str, str] | None:
    match = GITHUB_RE.search(url)
    if not match:
        return None
    owner = match.group("owner").strip()
    repo = match.group("repo").strip().removesuffix(".git")
    repo = re.split(r"[#?]", repo)[0]
    return owner, repo


async def _get_repo_meta(client: httpx.AsyncClient, owner: str, repo: str) -> dict[str, Any]:
    response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
    response.raise_for_status()
    return response.json()


async def _get_readme(client: httpx.AsyncClient, owner: str, repo: str, branch: str) -> str:
    candidates = ["README.md", "readme.md", "README.rst", "README.txt"]
    for filename in candidates:
        response = await client.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}")
        if response.status_code == 200:
            return response.text
    return ""


async def _get_file_tree(client: httpx.AsyncClient, owner: str, repo: str, branch: str) -> list[str]:
    response = await client.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    response.raise_for_status()
    payload = response.json()
    paths = [item["path"] for item in payload.get("tree", []) if item.get("type") == "blob"]
    return paths


def _select_important_files(paths: list[str]) -> list[str]:
    patterns = [
        "readme",
        "requirements",
        "environment",
        "setup.py",
        "pyproject",
        "package.json",
        "train",
        "eval",
        "test",
        "config",
        "dataset",
        "data",
        "preprocess",
        "main.py",
        "run",
    ]
    selected = [path for path in paths if any(pattern in path.lower() for pattern in patterns)]
    return selected[:80]


def _filter_paths(paths: list[str], keywords: list[str]) -> list[str]:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    return [path for path in paths if any(keyword in path.lower() for keyword in lowered_keywords)]

