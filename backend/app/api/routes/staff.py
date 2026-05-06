"""
Staff / Teacher Management API
"""
import secrets, string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_

from app.db.session import get_db
from app.core.security import require_roles, hash_password
from app.models.models import User
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

    query = select(User).where(
        User.school_id == school_id,
        User.role.in_(["teacher", "principal", "staff"])
    )
    if search:
        query = query.where(or_(
            User.full_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        ))
    if role:
        query = query.where(User.role == role)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page).order_by(User.full_name)
    rows = (await db.execute(query)).scalars().all()

    items = [
        {
            "id": str(u.id),
            "user_id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "designation": None,
            "department": None,
            "qualification": None,
            "subjects": [],
            "joining_date": None,
            "employee_id": f"EMP-{str(u.id)[:6].upper()}",
        }
        for u in rows
    ]

    return PaginatedResponse(
        items=items,
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

    return {
        "id": str(user.id),
        "employee_id": _gen_employee_id(0),
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

    user = (await db.execute(
        select(User).where(User.id == staff_id, User.school_id == school_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Staff not found")

    data = body.model_dump(exclude_unset=True)
    for f in ["full_name", "phone", "is_active", "role"]:
        if f in data:
            setattr(user, f, data[f])

    return {"message": "Staff updated"}


@router.delete("/{staff_id}")
async def deactivate_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin")),
):
    school_id = payload["school_id"]
    user = (await db.execute(
        select(User).where(User.id == staff_id, User.school_id == school_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Staff not found")
    user.is_active = False
    return {"message": "Staff deactivated"}
