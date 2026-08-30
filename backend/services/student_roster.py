"""Student roster helpers — stable UUID per class+name."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.models import ClassStudent, EduClass
from backend.services.classroom import normalize_student_name


def ensure_roster_student(db: Session, classroom: EduClass, name: str) -> ClassStudent:
    """Find or create roster row; assign persistent student_uuid."""
    clean = normalize_student_name(name)
    key = clean.casefold()
    rows = db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).all()
    for row in rows:
        if normalize_student_name(row.name).casefold() == key:
            if not row.student_uuid:
                row.student_uuid = str(uuid.uuid4())
                db.flush()
            return row
    row = ClassStudent(
        class_id=classroom.id,
        name=clean,
        student_uuid=str(uuid.uuid4()),
    )
    db.add(row)
    db.flush()
    return row


def verify_roster_student(
    db: Session, classroom: EduClass, student_name: str, student_uuid: str
) -> ClassStudent:
    """Verify student_id belongs to roster entry with matching name."""
    clean = normalize_student_name(student_name)
    sid = str(student_uuid or "").strip()
    if len(clean) < 2 or not sid:
        raise ValueError("invalid student identity")
    key = clean.casefold()
    rows = db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).all()
    for row in rows:
        if normalize_student_name(row.name).casefold() != key:
            continue
        if not row.student_uuid:
            row.student_uuid = sid
            db.flush()
            return row
        if row.student_uuid == sid:
            return row
        raise ValueError("student_id mismatch")
    raise ValueError("student not in roster")
