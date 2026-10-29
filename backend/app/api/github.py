import hashlib
import hmac
from fastapi import APIRouter, Header, HTTPException, Request
from app.core.config import get_settings

router = APIRouter(prefix="/github", tags=["GitHub integration"])


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    settings = get_settings()
    secret = settings.github_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="GitHub webhook is not configured")
    if not x_hub_signature_256 or not x_hub_signature_256.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or invalid GitHub signature")
    body = await request.body()
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")
    # Signature is verified. Processing PR diffs requires GitHub App credentials and is intentionally
    # left as a separate implementation step; this endpoint does not claim to review PRs yet.
    return {"accepted": True, "event": x_github_event or "unknown", "processed": False,
            "message": "Webhook signature verified; PR processing is not configured."}
