import logging
import re
from pathlib import Path
from typing import Dict, List
from src.models.schemas import AgentOutput
from src.config import JOBS_DIR
from atlassian import Confluence, Jira

logger = logging.getLogger(__name__)


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


def push_confluence(outputs: Dict[str, AgentOutput], space_key: str,
                    url: str, token: str) -> List[str]:
    """
    Push each artefact as a Confluence page. Returns list of error messages (empty = all OK).
    Local files are always written first by the caller — this is best-effort.
    """
    errors = []
    try:
        cf = Confluence(url=url, token=token)
    except Exception as e:
        return [f"Confluence connection failed: {e}"] * len(outputs)

    for name, output in outputs.items():
        title = f"P04 — {name.replace('_', ' ').title()}"
        try:
            existing = cf.get_page_by_title(space=space_key, title=title)
            if existing:
                cf.update_page(page_id=existing["id"], title=title, body=output.content)
            else:
                cf.create_page(space=space_key, title=title, body=output.content)
        except Exception as e:
            msg = f"Confluence push failed for {name}: {e}"
            logger.warning(msg)
            errors.append(msg)
    return errors


def push_jira(story_output: AgentOutput, project_key: str,
              url: str, token: str) -> List[str]:
    """
    Parse user story markdown and create Jira issues. Returns list of error messages.
    Best-effort — local files are already written by the caller.
    """
    errors = []
    try:
        jira = Jira(url=url, token=token)
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
