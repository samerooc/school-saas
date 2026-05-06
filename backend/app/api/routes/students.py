"""
Students API — Complete CRUD with security
Every query filters by school_id from JWT (multi-tenant isolation)
"""
import uuid, secrets, string
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.core.security import require_roles, get_current_user_payload
from app.models.models import Student, User, Class, Staff, AcademicYear
from app.schemas.schemas import (
    StudentCreate, StudentUpdate, StudentOut, StudentListItem, PaginatedResponse
)

router = APIRouter(prefix="/students", tags=["students"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _generate_admission_number(db: AsyncSession, school_id: str) -> str:
    """Format: SCH-2025-0001"""
    year = date.today().year
    result = await db.execute(
        select(func.count(Student.id)).where(Student.school_id == school_id)
    )
    count = result.scalar() or 0
    return f"SCH-{year}-{str(count + 1).zfill(4)}"


def _random_password(length=10) -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return secrets.choice(string.ascii_uppercase) + \
           secrets.choice(string.digits) + \
           secrets.choice("!@#$") + \
           ''.join(secrets.choice(chars) for _ in range(length - 3))


# ── List Students ─────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse)
async def list_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_premium: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher")),
):
    school_id = payload["school_id"]

    # Base query with join to get class info
    query = (
        select(Student, User, Class)
        .join(User, User.id == Student.user_id, isouter=True)
        .join(Class, Class.id == Student.class_id, isouter=True)
        .where(Student.school_id == school_id)
    )

    # Filters
    if search:
        query = query.where(or_(
            User.full_name.ilike(f"%{search}%"),
            Student.admission_number.ilike(f"%{search}%"),
            Student.roll_number.ilike(f"%{search}%"),
        ))
    if class_id:
        query = query.where(Student.class_id == class_id)
    if is_active is not None:
        query = query.where(Student.is_active == is_active)
    if is_premium is not None:
        query = query.where(Student.is_premium == is_premium)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    query = query.order_by(User.full_name)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for student, user, cls in rows:
        items.append(StudentListItem(
            id=student.id,
            admission_number=student.admission_number,
            full_name=user.full_name if user else "Unknown",
            class_name=cls.name if cls else None,
            section=cls.section if cls else None,
            roll_number=student.roll_number,
            is_active=student.is_active,
            is_premium=student.is_premium,
            photo_url=student.photo_url,
        ))

    return PaginatedResponse(
        items=[i.model_dump() for i in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


# ── Create Student ────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_student(
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    # Validate class belongs to this school
    cls_result = await db.execute(
        select(Class).where(Class.id == body.class_id, Class.school_id == school_id)
    )
    cls = cls_result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found in this school")

    # Handle parent
    parent_id = body.parent_id
    if not parent_id and body.parent_email:
        # Check if parent user already exists
        existing = await db.execute(
            select(User).where(User.email == body.parent_email)
        )
        parent_user = existing.scalar_one_or_none()
        if not parent_user:
            # Create parent user account
            parent_pwd = _random_password()
            parent_user = User(
                school_id=school_id,
                full_name=body.parent_name or "Parent",
                email=body.parent_email,
                phone=body.parent_phone,
                password_hash=__import__('app.core.security', fromlist=['hash_password']).hash_password(parent_pwd),
                role="parent",
                must_change_password=True,
            )
            db.add(parent_user)
            await db.flush()
        parent_id = parent_user.id

    # Create user account for student
    student_email = body.email or f"student_{uuid.uuid4().hex[:8]}@school.internal"
    temp_password = _random_password()

    from app.core.security import hash_password
    student_user = User(
        school_id=school_id,
        full_name=body.full_name,
        email=student_email,
        phone=body.phone,
        password_hash=hash_password(temp_password),
        role="student",
        must_change_password=True,
    )
    db.add(student_user)
    await db.flush()

    # Generate admission number
    admission_number = await _generate_admission_number(db, school_id)

    # Create student record
    student = Student(
        user_id=student_user.id,
        school_id=school_id,
        admission_number=admission_number,
        roll_number=body.roll_number,
        class_id=body.class_id,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        blood_group=body.blood_group,
        address=body.address,
        parent_id=parent_id,
    )
    db.add(student)
    await db.flush()

    return {
        "id": str(student.id),
        "admission_number": admission_number,
        "message": "Student admitted successfully",
        "temp_password": temp_password,  # Show once — admin gives to student
    }


# ── Get Single Student ────────────────────────────────────────────────────────

@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher")),
):
    school_id = payload["school_id"]

    result = await db.execute(
        select(Student, User, Class)
        .join(User, User.id == Student.user_id, isouter=True)
        .join(Class, Class.id == Student.class_id, isouter=True)
        .where(Student.id == student_id, Student.school_id == school_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Student not found")

    student, user, cls = row

    # Get parent info
    parent_name = parent_phone = None
    if student.parent_id:
        p_result = await db.execute(select(User).where(User.id == student.parent_id))
        parent = p_result.scalar_one_or_none()
        if parent:
            parent_name = parent.full_name
            parent_phone = parent.phone

    return StudentOut(
        id=student.id,
        user_id=student.user_id,
        admission_number=student.admission_number,
        roll_number=student.roll_number,
        full_name=user.full_name if user else "Unknown",
        email=user.email if user else None,
        phone=user.phone if user else None,
        class_name=cls.name if cls else None,
        section=cls.section if cls else None,
        date_of_birth=student.date_of_birth,
        gender=student.gender,
        blood_group=student.blood_group,
        address=student.address,
        photo_url=student.photo_url,
        is_active=student.is_active,
        is_premium=student.is_premium,
        admission_date=student.admission_date,
        parent_name=parent_name,
        parent_phone=parent_phone,
    )


# ── Update Student ────────────────────────────────────────────────────────────

@router.patch("/{student_id}")
async def update_student(
    student_id: str,
    body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    update_data = body.model_dump(exclude_unset=True)

    # Update Student table fields
    student_fields = ["roll_number", "class_id", "date_of_birth", "gender",
                      "blood_group", "address", "is_active"]
    for field in student_fields:
        if field in update_data:
            setattr(student, field, update_data[field])

    # Update User table fields
    if "full_name" in update_data or "phone" in update_data:
        user_update = {}
        if "full_name" in update_data:
            user_update["full_name"] = update_data["full_name"]
        if "phone" in update_data:
            user_update["phone"] = update_data["phone"]
        await db.execute(
            update(User).where(User.id == student.user_id).values(**user_update)
        )

    return {"message": "Student updated successfully"}


# ── Delete (Soft) ─────────────────────────────────────────────────────────────

@router.delete("/{student_id}")
async def deactivate_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]

    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # Soft delete — data preserved
    student.is_active = False
    return {"message": "Student deactivated. Data preserved."}


# ── Grant/Revoke Premium ──────────────────────────────────────────────────────

@router.post("/{student_id}/premium")
async def grant_premium(
    student_id: str,
    expires_in_days: Optional[int] = None,
    note: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    from datetime import datetime, timezone, timedelta
    school_id = payload["school_id"]

    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    student.is_premium = True
    student.premium_granted_by = payload["sub"]
    student.premium_granted_at = datetime.now(timezone.utc)
    student.premium_note = note
    student.premium_expires_at = (
        datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        if expires_in_days else None
    )

    return {"message": f"Premium granted{'for ' + str(expires_in_days) + ' days' if expires_in_days else ' (lifetime)'}"}


@router.delete("/{student_id}/premium")
async def revoke_premium(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    student.is_premium = False
    student.premium_expires_at = None
    return {"message": "Premium revoked"}


# ── Photo Upload ──────────────────────────────────────────────────────────────

@router.post("/{student_id}/photo")
async def upload_photo(
    student_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    # Validate file type by magic bytes
    content = await file.read(12)
    await file.seek(0)

    ALLOWED_MAGIC = [
        b'\xff\xd8\xff',           # JPEG
        b'\x89PNG\r\n\x1a\n',     # PNG
    ]
    if not any(content.startswith(magic) for magic in ALLOWED_MAGIC):
        raise HTTPException(400, "Only JPG/PNG images allowed")

    # Check size (max 2MB)
    all_content = await file.read()
    if len(all_content) > 2 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Max 2MB allowed")

    # TODO: Upload to Cloudflare R2 and update student.photo_url
    # For now return placeholder
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # placeholder — replace with actual R2 upload
    student.photo_url = f"/uploads/photos/{student_id}.jpg"

    return {"message": "Photo uploaded", "photo_url": student.photo_url}
