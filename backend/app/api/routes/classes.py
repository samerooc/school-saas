"""
Classes, Subjects, Academic Year API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.security import require_roles
from app.models.models import Class, Subject, User, Student, AcademicYear
from app.schemas.schemas import (
    ClassCreate, ClassUpdate, ClassOut,
    SubjectCreate, SubjectOut,
    AcademicYearCreate, AcademicYearOut,
)

router = APIRouter(tags=["classes"])


# ── Academic Years ────────────────────────────────────────────────────────────

@router.get("/academic-years", response_model=List[AcademicYearOut])
async def list_academic_years(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(AcademicYear)
        .where(AcademicYear.school_id == school_id)
        .order_by(AcademicYear.start_date.desc())
    )
    return result.scalars().all()


@router.post("/academic-years", response_model=AcademicYearOut, status_code=201)
async def create_academic_year(
    body: AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]

    # If marking as current, unset others
    if body.is_current:
        result = await db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_current == True
            )
        )
        for ay in result.scalars():
            ay.is_current = False

    ay = AcademicYear(
        school_id=school_id,
        year_label=body.year_label,
        start_date=body.start_date,
        end_date=body.end_date,
        is_current=body.is_current,
    )
    db.add(ay)
    await db.flush()
    return ay


# ── Classes ───────────────────────────────────────────────────────────────────

@router.get("/classes", response_model=List[ClassOut])
async def list_classes(
    academic_year_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student", "parent")),
):
    school_id = payload["school_id"]
    query = (
        select(Class, User, func.count(Student.id).label("student_count"))
        .join(User, User.id == Class.class_teacher_id, isouter=True)
        .join(Student, Student.class_id == Class.id, isouter=True)
        .where(Class.school_id == school_id)
        .group_by(Class.id, User.id)
    )
    if academic_year_id:
        query = query.where(Class.academic_year_id == academic_year_id)

    result = await db.execute(query)
    rows = result.all()

    return [
        ClassOut(
            id=cls.id,
            name=cls.name,
            section=cls.section,
            room_number=cls.room_number,
            max_students=cls.max_students,
            class_teacher_name=user.full_name if user else None,
            student_count=count or 0,
        )
        for cls, user, count in rows
    ]


@router.post("/classes", status_code=201)
async def create_class(
    body: ClassCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    # Validate academic year belongs to school
    ay = (await db.execute(
        select(AcademicYear).where(
            AcademicYear.id == body.academic_year_id,
            AcademicYear.school_id == school_id
        )
    )).scalar_one_or_none()
    if not ay:
        raise HTTPException(404, "Academic year not found")

    cls = Class(
        school_id=school_id,
        academic_year_id=body.academic_year_id,
        name=body.name,
        section=body.section,
        class_teacher_id=body.class_teacher_id,
        room_number=body.room_number,
        max_students=body.max_students,
    )
    db.add(cls)
    await db.flush()
    return {"id": str(cls.id), "message": "Class created"}


@router.patch("/classes/{class_id}")
async def update_class(
    class_id: str,
    body: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Class).where(Class.id == class_id, Class.school_id == school_id)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)
    return {"message": "Class updated"}


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]

    # Check no students in this class
    count = (await db.execute(
        select(func.count(Student.id)).where(
            Student.class_id == class_id,
            Student.is_active == True
        )
    )).scalar() or 0

    if count > 0:
        raise HTTPException(400, f"Cannot delete class with {count} active students")

    result = await db.execute(
        select(Class).where(Class.id == class_id, Class.school_id == school_id)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    await db.delete(cls)
    return {"message": "Class deleted"}


# ── Subjects ──────────────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/subjects", response_model=List[SubjectOut])
async def list_subjects(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Subject, User)
        .join(User, User.id == Subject.teacher_id, isouter=True)
        .where(Subject.class_id == class_id, Subject.school_id == school_id)
        .order_by(Subject.name)
    )
    return [
        SubjectOut(
            id=sub.id, name=sub.name, code=sub.code, max_marks=sub.max_marks,
            teacher_name=user.full_name if user else None
        )
        for sub, user in result.all()
    ]


@router.post("/subjects", status_code=201)
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    # Validate class in school
    cls = (await db.execute(
        select(Class).where(Class.id == body.class_id, Class.school_id == school_id)
    )).scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    sub = Subject(
        school_id=school_id,
        name=body.name,
        code=body.code,
        class_id=body.class_id,
        teacher_id=body.teacher_id,
        max_marks=body.max_marks,
    )
    db.add(sub)
    await db.flush()
    return {"id": str(sub.id), "message": "Subject created"}


@router.patch("/subjects/{subject_id}")
async def update_subject(
    subject_id: str,
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.school_id == school_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Subject not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        if hasattr(sub, field):
            setattr(sub, field, value)
    return {"message": "Subject updated"}


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.school_id == school_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Subject not found")
    await db.delete(sub)
    return {"message": "Subject deleted"}
