# Business Intelligence Agent
# Copyright (C) 2026  B. Vignesh Kumar (Bravetux) <ic19939@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import markdown as _markdown

from src.models.schemas import AgentOutput
from src.config import JOBS_DIR
from atlassian import Confluence, Jira

logger = logging.getLogger(__name__)


def _md_to_html(text: str) -> str:
    """Convert agent-produced Markdown to HTML that Confluence Cloud accepts
    in its storage format. Confluence's storage representation is XHTML-ish,
    and the python-markdown output is good enough for headings, lists, code
    blocks, bold/italic, tables, and paragraphs."""
    return _markdown.markdown(
        text or "",
        extensions=["extra", "sane_lists", "tables", "fenced_code"],
    )


def _humanise(name: str) -> str:
    return name.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Auth helpers — auto-pick Cloud (basic) vs. Server/DC (bearer) from URL.
# ---------------------------------------------------------------------------

def _is_cloud(url: str) -> bool:
    """Atlassian Cloud hosts are *.atlassian.net (and *.atlassian.com for some
    legacy paths). Anything else is treated as Server / Data Center."""
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return host.endswith("atlassian.net") or host.endswith("atlassian.com")


def _split_email_token(token: str) -> tuple[Optional[str], str]:
    """Allow callers to paste 'email:api_token' in the token field as a
    convenience. Returns (email_or_None, token)."""
    if token and token.count(":") == 1 and "@" in token.split(":", 1)[0]:
        e, t = token.split(":", 1)
        return e.strip(), t.strip()
    return None, token


def _build_confluence(url: str, token: str, email: Optional[str]) -> Confluence:
    inferred_email, clean_token = _split_email_token(token)
    email = email or inferred_email
    if _is_cloud(url):
        if not email:
            raise ValueError(
                "Atlassian Cloud requires an email + API token. Set the "
                "Confluence email field in Settings, or paste 'email:token' "
                "into the token field."
            )
        return Confluence(url=url, username=email, password=clean_token, cloud=True)
    return Confluence(url=url, token=clean_token)


def _build_jira(url: str, token: str, email: Optional[str]) -> Jira:
    inferred_email, clean_token = _split_email_token(token)
    email = email or inferred_email
    if _is_cloud(url):
        if not email:
            raise ValueError(
                "Atlassian Cloud requires an email + API token. Set the Jira "
                "email field in Settings, or paste 'email:token' into the token field."
            )
        return Jira(url=url, username=email, password=clean_token, cloud=True)
    return Jira(url=url, token=clean_token)


def write_local(job_id: str, outputs: Dict[str, AgentOutput],
                base_dir: Path = None) -> List[Path]:
    """Write each artefact as a markdown file under data/jobs/{job_id}/."""
    out_dir = (base_dir or JOBS_DIR) / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, output in outputs.items():
        p = out_dir / f"{name}.md"
        p.write_text(output.content, encoding="utf-8")
        written.append(p)
    return written


def list_confluence_spaces(url: str, token: str,
                           email: Optional[str] = None,
                           limit: int = 200) -> List[Dict[str, str]]:
    """Return [{'key': ..., 'name': ..., 'type': ...}, ...] for every space
    the authenticated user can read. Used by the Settings → Test Connection
    button so users can copy a real space key into the Generate tab."""
    cf = _build_confluence(url, token, email)
    resp = cf.get_all_spaces(start=0, limit=limit)
    spaces = resp.get("results", []) if isinstance(resp, dict) else (resp or [])
    return [
        {"key": s.get("key", ""), "name": s.get("name", ""), "type": s.get("type", "")}
        for s in spaces
    ]


def list_jira_projects(url: str, token: str,
                       email: Optional[str] = None) -> List[Dict[str, str]]:
    """Return [{'key': ..., 'name': ...}, ...] for every Jira project the
    authenticated user can see."""
    jira = _build_jira(url, token, email)
    projects = jira.projects() or []
    return [
        {"key": p.get("key", ""), "name": p.get("name", "")}
        for p in projects
    ]


def push_confluence(outputs: Dict[str, AgentOutput], space_key: str,
                    url: str, token: str,
                    email: Optional[str] = None,
                    target_page: Optional[str] = None) -> List[str]:
    """
    Push artefacts to Confluence. Returns list of error messages (empty = all OK).
    Local files are always written first by the caller — this is best-effort.

    Auth is auto-selected from the URL: *.atlassian.net hosts use basic auth
    (email + API token); other hosts use bearer (Server / Data Center PAT).

    Modes:
      * target_page is None (default): one page per artefact at space root,
        titled by the artefact name. Existing pages are matched by title and
        updated; otherwise a new page is created.
      * target_page is set (numeric ID or page title): all artefacts are
        merged into a single body and posted to that one page. If the page
        doesn't exist, it's created at space root with that title.

    Markdown content is converted to HTML before posting so Confluence Cloud
    renders headings/lists/tables instead of showing raw '##' characters.
    """
    try:
        cf = _build_confluence(url, token, email)
    except Exception as e:
        return [f"Confluence connection failed: {e}"] * (len(outputs) or 1)

    if target_page:
        return _push_combined_page(cf, space_key, target_page, outputs)

    errors: List[str] = []
    for name, output in outputs.items():
        title = _humanise(name)
        body_html = _md_to_html(output.content)
        try:
            existing = cf.get_page_by_title(space=space_key, title=title)
            if existing:
                cf.update_page(page_id=existing["id"], title=title, body=body_html)
            else:
                cf.create_page(space=space_key, title=title, body=body_html)
        except Exception as e:
            msg = f"Confluence push failed for {name}: {e}"
            logger.warning(msg)
            errors.append(msg)
    return errors


def _push_combined_page(cf: Confluence, space_key: str, target: str,
                        outputs: Dict[str, AgentOutput]) -> List[str]:
    """Merge every artefact into a single page identified by *target* (numeric
    Confluence page ID, or page title)."""
    # Resolve target -> (page_id, title)
    page_id: Optional[str] = None
    title: str = target
    try:
        if target.isdigit():
            page = cf.get_page_by_id(target)
            if not page:
                return [f"Confluence: page id {target} not found"]
            page_id = str(page["id"])
            title = page.get("title") or target
        else:
            existing = cf.get_page_by_title(space=space_key, title=target)
            if existing:
                page_id = str(existing["id"])
                title = target
            else:
                # Create the target page so the user can target a desired
                # destination by name even if it doesn't exist yet.
                created = cf.create_page(space=space_key, title=target, body="")
                page_id = str(created["id"])
                title = target
    except Exception as e:
        return [f"Confluence: failed to resolve target page '{target}': {e}"]

    sections: List[str] = []
    for name, output in outputs.items():
        section_html = _md_to_html(output.content)
        sections.append(f"<h1>{_humanise(name)}</h1>\n{section_html}")
    combined_html = "\n\n<hr/>\n\n".join(sections)

    try:
        cf.update_page(page_id=page_id, title=title, body=combined_html)
    except Exception as e:
        return [f"Confluence update of '{title}' failed: {e}"]
    return []


def push_jira(story_output: AgentOutput, project_key: str,
              url: str, token: str,
              email: Optional[str] = None) -> List[str]:
    """
    Parse user story markdown and create Jira issues. Returns list of error messages.
    Best-effort — local files are already written by the caller.

    Auth is auto-selected from the URL (see push_confluence).
    """
    errors = []
    try:
        jira = _build_jira(url, token, email)
    except Exception as e:
        return [f"Jira connection failed: {e}"]

    stories = _parse_stories(story_output.content)
    for story in stories:
        try:
            jira.create_issue(fields={
                "project": {"key": project_key},
                "summary": story["title"][:255],
                "description": story["body"],
                "issuetype": {"name": "Story"},
            })
        except Exception as e:
            msg = f"Jira create failed for '{story['title']}': {e}"
            logger.warning(msg)
            errors.append(msg)
    return errors


def _parse_stories(markdown: str) -> List[Dict]:
    """Extract story title + full body from UserStoryAgent markdown output."""
    stories = []
    blocks = re.split(r"(?m)^## Story:", markdown)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        title = lines[0].strip() if lines else "Untitled Story"
        body = "\n".join(lines[1:]).strip()
        stories.append({"title": title, "body": body})
    return stories
