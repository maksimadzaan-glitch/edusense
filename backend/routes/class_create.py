from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import EduClass, Teacher
from backend.schemas.edu import ClassCreateRequest, ClassCreateResponse, ClassOut, TeacherOut
from backend.services.codes import generate_edu_code

router = APIRouter(prefix="/api/class", tags=["class"])


@router.post("/create", response_model=ClassCreateResponse, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreateRequest, db: Session = Depends(get_db)):
    if not payload.teacher_id and not payload.teacher:
        raise HTTPException(
            status_code=400,
            detail="Передайте teacher_id или объект teacher {name, email}",
        )

    if payload.teacher_id:
        teacher = db.query(Teacher).filter(Teacher.id == payload.teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Учитель не найден")
    else:
        assert payload.teacher is not None
        email = payload.teacher.email.lower().strip()
        teacher = db.query(Teacher).filter(Teacher.email == email).first()
        if teacher:
            teacher.name = payload.teacher.name.strip()
        else:
            teacher = Teacher(name=payload.teacher.name.strip(), email=email)
            db.add(teacher)
            db.flush()

    try:
        code = generate_edu_code(db, EduClass, "code")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    classroom = EduClass(
        teacher_id=teacher.id,
        name=payload.name.strip(),
        code=code,
        subject=payload.subject.strip(),
        target_exam=payload.target_exam,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    db.refresh(teacher)

    return ClassCreateResponse(
        classroom=ClassOut.model_validate(classroom),
        teacher=TeacherOut.model_validate(teacher),
    )
