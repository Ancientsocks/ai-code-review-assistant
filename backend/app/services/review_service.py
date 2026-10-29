import hashlib
from datetime import datetime, timezone
from app.schemas.review import Finding, ReviewRequest, ReviewResult
from app.services.analyzers import run_bandit, run_ruff
from app.services.ai_service import review_with_ai

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


async def review_code(request: ReviewRequest) -> tuple[ReviewResult, str]:
    findings: list[Finding] = []
    if request.language.lower() in {"python", "py"}:
        findings.extend(run_ruff(request.code))
        findings.extend(run_bandit(request.code))
    ai_summary, ai_findings = await review_with_ai(request.language, request.code)
    findings.extend(ai_findings)
    findings.sort(key=lambda item: (SEVERITY_ORDER.get(item.severity, 9), item.line or 0, item.source))
    summary = f"{len(findings)} finding(s) identified. {ai_summary}"
    if not findings:
        summary = "No findings were reported by the configured analyzers. This does not guarantee the code is bug-free."
    digest = hashlib.sha256(request.code.encode("utf-8")).hexdigest()
    return ReviewResult(summary=summary, findings=findings), digest
