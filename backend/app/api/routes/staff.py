"""
Staff / Teacher Management API
"""
import uuid, secrets, string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_

from app.db.session import get_db
from app.core.security import require_roles, hash_password
from app.models.models import User, Staff
from app.schemas.schemas import StaffCreate, StaffUpdate, StaffOut, PaginatedResponse

router = APIRouter(prefix="/staff", tags=["staff"])


def _gen_employee_id(count: int) -> str:
    return f"EMP-{str(count + 1).zfill(4)}"


def _random_password(length=10) -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return (secrets.choice(string.ascii_uppercase) +
            secrets.choice(string.digits) +
            secrets.choice("!@#$") +
            ''.join(secrets.choice(chars) for _ in range(length - 3)))


@router.get("", response_model=PaginatedResponse)
async def list_staff(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]

    query = (
        select(Staff, User)
        .join(User, User.id == Staff.user_id)
        .where(Staff.school_id == school_id)
    )
    if search:
        query = query.where(or_(
            User.full_name.ilike(f"%{search}%"),
            Staff.employee_id.ilike(f"%{search}%"),
            Staff.designation.ilike(f"%{search}%"),
        ))
    if role:
        query = query.where(User.role == role)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page).order_by(User.full_name)
    rows = (await db.execute(query)).all()

    items = [
        StaffOut(
            id=staff.id,
            user_id=staff.user_id,
            employee_id=staff.employee_id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            designation=staff.designation,
            department=staff.department,
            qualification=staff.qualification,
            subjects=staff.subjects,
            joining_date=staff.joining_date,
            is_active=user.is_active,
        )
        for staff, user in rows
    ]

    return PaginatedResponse(
        items=[i.model_dump() for i in items],
        total=total, page=page, per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.post("", status_code=201)
async def create_staff(
    body: StaffCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]

    # Check email unique
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Email already registered")

    temp_pwd = _random_password()
    user = User(
        school_id=school_id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(temp_pwd),
        role=body.role,
        must_change_password=True,
    )
    db.add(user)
    await db.flush()

    count_result = await db.execute(select(func.count(Staff.id)).where(Staff.school_id == school_id))
    count = count_result.scalar() or 0

    staff = Staff(
        user_id=user.id,
        school_id=school_id,
        employee_id=_gen_employee_id(count),
        designation=body.designation,
        department=body.department,
        qualification=body.qualification,
        salary=body.salary,
        joining_date=body.joining_date,
        subjects=body.subjects,
    )
    db.add(staff)

    return {
        "id": str(staff.id),
        "employee_id": staff.employee_id,
        "message": "Staff member added",
        "temp_password": temp_pwd,
    }


@router.patch("/{staff_id}")
async def update_staff(
    staff_id: str,
    body: StaffUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.school_id == school_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(404, "Staff not found")

    data = body.model_dump(exclude_unset=True)
    staff_fields = ["designation", "department", "qualification", "salary", "subjects"]
    for f in staff_fields:
        if f in data:
            setattr(staff, f, data[f])

    user_update = {}
    if "full_name" in data:
        user_update["full_name"] = data["full_name"]
    if "phone" in data:
        user_update["phone"] = data["phone"]
    if "is_active" in data:
        user_update["is_active"] = data["is_active"]
    if user_update:
        await db.execute(update(User).where(User.id == staff.user_id).values(**user_update))

    return {"message": "Staff updated"}


@router.delete("/{staff_id}")
async def deactivate_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Staff, User)
        .join(User, User.id == Staff.user_id)
        .where(Staff.id == staff_id, Staff.school_id == school_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Staff not found")
    _, user = row
    user.is_active = False
    return {"message": "Staff deactivated"}
