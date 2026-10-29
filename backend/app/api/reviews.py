from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.models import Review, User
from app.db.session import get_db
from app.schemas.review import ReviewRequest, ReviewResponse
from app.services.review_service import review_code

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if len(payload.code) > get_settings().max_code_chars:
        raise HTTPException(status_code=413, detail="Submitted code exceeds configured size limit")
    result, digest = await review_code(payload)
    record = Review(
        user_id=user.id,
        language=payload.language.lower(),
        code_sha256=digest,
        summary=result.summary,
        findings=[item.model_dump() for item in result.findings],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ReviewResponse(
        id=record.id, language=record.language, summary=record.summary,
        findings=result.findings, created_at=record.created_at.isoformat(),
    )


@router.get("", response_model=list[ReviewResponse])
def list_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user), limit: int = 20):
    limit = max(1, min(limit, 100))
    records = db.scalars(
        select(Review).where(Review.user_id == user.id).order_by(Review.created_at.desc()).limit(limit)
    ).all()
    return [
        ReviewResponse(id=r.id, language=r.language, summary=r.summary, findings=r.findings, created_at=r.created_at.isoformat())
        for r in records
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.scalar(select(Review).where(Review.id == review_id, Review.user_id == user.id))
    if record is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(
        id=record.id, language=record.language, summary=record.summary,
        findings=record.findings, created_at=record.created_at.isoformat(),
    )
