import random
import string
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClassRoom, User

router = APIRouter(prefix="/api", tags=["classes"])


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    exam_type: str = Field(..., pattern="^(vpr|oge|ege|school)$")
    grade: Optional[str] = None
    subject: str = Field(..., min_length=2, max_length=80)
    teacher_id: int


class ClassResponse(BaseModel):
    id: int
    name: str
    access_code: str
    exam_type: str
    grade: Optional[str] = None
    subject: str
    teacher_id: int

    class Config:
        from_attributes = True


def _generate_code(db: Session) -> str:
    for _ in range(40):
        code = "EDU-" + "".join(random.choices(string.digits, k=4))
        exists = db.query(ClassRoom).filter(ClassRoom.access_code == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Не удалось сгенерировать код.")


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == payload.teacher_id).first()
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Только учитель может создать класс.")

    classroom = ClassRoom(
        name=payload.name.strip(),
        access_code=_generate_code(db),
        exam_type=payload.exam_type,
        grade=(payload.grade.strip() if payload.grade else None),
        subject=payload.subject.strip(),
        teacher_id=teacher.id,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/classes/by-teacher/{teacher_id}", response_model=List[ClassResponse])
def list_teacher_classes(teacher_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ClassRoom)
        .filter(ClassRoom.teacher_id == teacher_id)
        .order_by(ClassRoom.id.desc())
        .all()
    )


@router.get("/classes/by-code/{code}", response_model=ClassResponse)
def get_class_by_code(code: str, db: Session = Depends(get_db)):
    classroom = db.query(ClassRoom).filter(ClassRoom.access_code == code.upper()).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Класс с таким кодом не найден.")
    return classroom
