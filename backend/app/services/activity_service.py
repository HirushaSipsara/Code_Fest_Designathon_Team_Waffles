from sqlalchemy.orm import Session
from app.models.entities import ActivityEvent


def record(db: Session, message: str, category: str = "ok") -> ActivityEvent:
    item = ActivityEvent(message=message, category=category)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def recent(db: Session) -> list[ActivityEvent]:
    return db.query(ActivityEvent).order_by(ActivityEvent.id.desc()).limit(30).all()
