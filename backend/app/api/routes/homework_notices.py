"""
Homework + Notices API
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.db.session import get_db
from app.core.security import require_roles
from app.models.models import Homework, Notice, Subject, Class, User, Student
from app.schemas.schemas import HomeworkCreate, HomeworkOut, NoticeCreate, NoticeOut

hw_router = APIRouter(prefix="/homework", tags=["homework"])
notice_router = APIRouter(prefix="/notices", tags=["notices"])


# ── HOMEWORK ──────────────────────────────────────────────────────────────────

@hw_router.post("", status_code=201)
async def create_homework(
    body: HomeworkCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin")),
):
    school_id = payload["school_id"]
    teacher_id = payload["sub"]

    # Validate subject belongs to school
    sub = (await db.execute(
        select(Subject).where(Subject.id == body.subject_id, Subject.school_id == school_id)
    )).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Subject not found")

    hw = Homework(
        subject_id=body.subject_id,
        class_id=body.class_id,
        teacher_id=teacher_id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
    )
    db.add(hw)
    await db.flush()
    return {"id": str(hw.id), "message": "Homework assigned"}


@hw_router.get("/class/{class_id}", response_model=List[HomeworkOut])
async def get_class_homework(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "student", "parent")),
):
    school_id = payload["school_id"]

    # Students: verify they belong to this class (server-side)
    if payload["role"] == "student":
        s = (await db.execute(
            select(Student).where(
                Student.user_id == payload["sub"],
                Student.class_id == class_id,
                Student.school_id == school_id,
            )
        )).scalar_one_or_none()
        if not s:
            raise HTTPException(403, "You are not in this class")

    result = await db.execute(
        select(Homework, Subject, User)
        .join(Subject, Subject.id == Homework.subject_id, isouter=True)
        .join(User, User.id == Homework.teacher_id, isouter=True)
        .where(Homework.class_id == class_id)
        .order_by(Homework.due_date)
    )
    rows = result.all()

    return [
        HomeworkOut(
            id=hw.id,
            title=hw.title,
            description=hw.description,
            due_date=hw.due_date,
            subject_name=sub.name if sub else None,
            teacher_name=user.full_name if user else None,
            attachment_url=hw.attachment_url,
            created_at=hw.created_at,
        )
        for hw, sub, user in rows
    ]


@hw_router.delete("/{hw_id}")
async def delete_homework(
    hw_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin")),
):
    result = await db.execute(select(Homework).where(Homework.id == hw_id))
    hw = result.scalar_one_or_none()
    if not hw:
        raise HTTPException(404, "Homework not found")

    # Teacher can only delete own homework
    if payload["role"] == "teacher" and str(hw.teacher_id) != payload["sub"]:
        raise HTTPException(403, "You can only delete your own homework")

    await db.delete(hw)
    return {"message": "Homework deleted"}


# ── NOTICES ───────────────────────────────────────────────────────────────────

@notice_router.post("", status_code=201)
async def create_notice(
    body: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    notice = Notice(
        school_id=school_id,
        title=body.title,
        content=body.content,
        target_audience=body.target_audience,
        class_id=body.class_id,
        is_published=True,
        published_by=payload["sub"],
        published_at=datetime.now(timezone.utc),
        expires_at=body.expires_at,
    )
    db.add(notice)
    await db.flush()
    return {"id": str(notice.id), "message": "Notice published"}


@notice_router.get("", response_model=List[NoticeOut])
async def list_notices(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student", "parent")),
):
    school_id = payload["school_id"]
    role = payload["role"]

    # Filter notices relevant to this role
    audience_filter = [Notice.target_audience == "all"]
    if role == "student":
        audience_filter.append(Notice.target_audience == "students")
    elif role == "teacher":
        audience_filter.append(Notice.target_audience == "teachers")
    elif role == "parent":
        audience_filter.append(Notice.target_audience == "parents")

    result = await db.execute(
        select(Notice, User)
        .join(User, User.id == Notice.published_by, isouter=True)
        .where(
            Notice.school_id == school_id,
            Notice.is_published == True,
            or_(*audience_filter),
        )
        .order_by(Notice.published_at.desc())
        .limit(50)
    )
    rows = result.all()

    return [
        NoticeOut(
            id=n.id,
            title=n.title,
            content=n.content,
            target_audience=n.target_audience,
            is_published=n.is_published,
            published_at=n.published_at,
            expires_at=n.expires_at,
            published_by_name=user.full_name if user else None,
        )
        for n, user in rows
    ]


@notice_router.delete("/{notice_id}")
async def delete_notice(
    notice_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id, Notice.school_id == school_id)
    )
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(404, "Notice not found")
    await db.delete(notice)
    return {"message": "Notice deleted"}
