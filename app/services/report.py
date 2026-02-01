from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


def to_markdown(output: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Trade Challenges Report")
    lines.append("")
    lines.append(f"Run ID: {output.get('run_id')}")
    lines.append(f"Generated: {datetime.utcnow().isoformat()}Z")
    lines.append("")

    for idx, item in enumerate(output.get("items", []), start=1):
        lines.append(f"## {idx}. {item.get('title')}")
        lines.append("")
        lines.append(item.get("summary", ""))
        lines.append("")
        lines.append(f"- Type: {item.get('challenge_type')}")
        lines.append(f"- Severity: {item.get('severity')}")
        lines.append(f"- Time horizon: {item.get('time_horizon')}")
        lines.append(f"- UK relevance: {item.get('uk_relevance')}")
        lines.append(f"- EU relevance: {item.get('eu_relevance')}")
        lines.append("")
        lines.append("Evidence:")
        for ev in item.get("evidence", []):
            lines.append(
                f"- {ev.get('source_name')}: {ev.get('quote')} ({ev.get('published_at')})"
            )
        lines.append("")
    return "\n".join(lines)
