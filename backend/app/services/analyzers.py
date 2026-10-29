import json
import subprocess
import sys
import tempfile
from pathlib import Path

from app.schemas.review import Finding


def _tool_unavailable(tool: str, detail: str = "") -> list[Finding]:
    message = f"{tool} could not run; its findings are unavailable."
    if detail:
        message += f" Detail: {detail[:500]}"
    return [
        Finding(
            source="system",
            severity="info",
            title=f"{tool} unavailable",
            message=message,
            rule_id=f"{tool.upper()}_UNAVAILABLE",
        )
    ]


def run_ruff(code: str) -> list[Finding]:
    """Run Ruff against source supplied on stdin; never execute the submitted source."""
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--output-format",
        "json",
        "--stdin-filename",
        "submitted.py",
        "-",
    ]
    try:
        proc = subprocess.run(
            command,
            input=code,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _tool_unavailable("Ruff", "analysis timed out")
    except OSError as exc:
        return _tool_unavailable("Ruff", str(exc))

    # Ruff uses exit code 1 when findings exist; 2 indicates a tool/configuration error.
    if proc.returncode not in (0, 1):
        return _tool_unavailable("Ruff", proc.stderr.strip() or f"exit code {proc.returncode}")
    try:
        data = json.loads(proc.stdout)
        if not isinstance(data, list):
            raise ValueError("expected JSON list")
    except (json.JSONDecodeError, ValueError):
        return _tool_unavailable("Ruff", "invalid JSON output")

    findings: list[Finding] = []
    for item in data:
        location = item.get("location") or {}
        fix = item.get("fix") or {}
        findings.append(
            Finding(
                source="ruff",
                severity="low",
                title=str(item.get("message") or "Lint finding")[:200],
                message=str(item.get("message") or "Lint finding")[:4000],
                line=location.get("row") if isinstance(location.get("row"), int) else None,
                rule_id=str(item.get("code") or "RUFF")[:100],
                suggestion=str(fix.get("message"))[:4000] if fix.get("message") else None,
            )
        )
    return findings


def run_bandit(code: str) -> list[Finding]:
    """Analyze a temporary source file with Bandit; submitted source is never executed."""
    try:
        with tempfile.TemporaryDirectory(prefix="code-review-bandit-") as temp_dir:
            source_path = Path(temp_dir) / "submitted.py"
            source_path.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "bandit", "-f", "json", str(source_path)],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
                cwd=temp_dir,
            )
    except subprocess.TimeoutExpired:
        return _tool_unavailable("Bandit", "analysis timed out")
    except OSError as exc:
        return _tool_unavailable("Bandit", str(exc))

    # Bandit may exit non-zero when it reports findings; parse its JSON output either way.
    try:
        payload = json.loads(proc.stdout or "")
        if not isinstance(payload, dict) or not isinstance(payload.get("results", []), list):
            raise ValueError("unexpected JSON structure")
    except (json.JSONDecodeError, ValueError):
        return _tool_unavailable("Bandit", proc.stderr.strip() or f"exit code {proc.returncode}")

    severity_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
    findings: list[Finding] = []
    for item in payload.get("results", []):
        findings.append(
            Finding(
                source="bandit",
                severity=severity_map.get(str(item.get("issue_severity", "LOW")).upper(), "low"),
                title=str(item.get("test_name") or "Security finding")[:200],
                message=str(item.get("issue_text") or "Potential security issue")[:4000],
                line=item.get("line_number") if isinstance(item.get("line_number"), int) else None,
                rule_id=str(item.get("test_id") or "BANDIT")[:100],
                suggestion=str(item.get("more_info"))[:4000] if item.get("more_info") else None,
            )
        )
    return findings
