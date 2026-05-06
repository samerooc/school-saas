"""
Attendance API — Teacher marks, Admin reports
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.session import get_db
from app.core.security import require_roles
from app.models.models import Attendance, Student, User, Class
from app.schemas.schemas import AttendanceBulkCreate, AttendanceOut

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/bulk", status_code=201)
async def mark_attendance_bulk(
    body: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal")),
):
    """Teacher marks attendance for entire class at once"""
    school_id = payload["school_id"]
    teacher_id = payload["sub"]

    # Validate class in school
    cls = (await db.execute(
        select(Class).where(Class.id == body.class_id, Class.school_id == school_id)
    )).scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    # Check if already marked today (prevent duplicate)
    existing = (await db.execute(
        select(func.count(Attendance.id)).where(
            and_(
                Attendance.class_id == body.class_id,
                Attendance.date == body.date,
                Attendance.school_id == school_id,
            )
        )
    )).scalar() or 0

    if existing > 0:
        raise HTTPException(
            409,
            f"Attendance already marked for this class on {body.date}. "
            "Contact admin to override."
        )

    # Validate all student_ids belong to this class & school
    student_ids = [str(e.student_id) for e in body.entries]
    valid_students = (await db.execute(
        select(Student.id).where(
            Student.id.in_(student_ids),
            Student.class_id == body.class_id,
            Student.school_id == school_id,
            Student.is_active == True,
        )
    )).scalars().all()

    valid_ids = {str(s) for s in valid_students}

    # Create attendance records
    records = []
    for entry in body.entries:
        if str(entry.student_id) not in valid_ids:
            continue  # Skip invalid student IDs silently
        records.append(Attendance(
            school_id=school_id,
            student_id=entry.student_id,
            class_id=body.class_id,
            date=body.date,
            status=entry.status,
            marked_by=teacher_id,
        ))

    db.add_all(records)
    present = sum(1 for e in body.entries if e.status == "present")
    absent = sum(1 for e in body.entries if e.status == "absent")

    return {
        "message": "Attendance marked successfully",
        "date": str(body.date),
        "present": present,
        "absent": absent,
        "total": len(records),
    }


@router.get("/class/{class_id}")
async def get_class_attendance(
    class_id: str,
    date_: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal")),
):
    """Get attendance for a class on a specific date"""
    school_id = payload["school_id"]

    result = await db.execute(
        select(Attendance, Student, User)
        .join(Student, Student.id == Attendance.student_id)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(
            Attendance.class_id == class_id,
            Attendance.date == date_,
            Attendance.school_id == school_id,
        )
        .order_by(User.full_name)
    )
    rows = result.all()

    return [
        {
            "student_id": str(att.student_id),
            "student_name": user.full_name if user else "Unknown",
            "roll_number": student.roll_number,
            "date": str(att.date),
            "status": att.status,
        }
        for att, student, user in rows
    ]


@router.get("/student/{student_id}")
async def get_student_attendance(
    student_id: str,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal", "student", "parent")),
):
    """Get attendance history for a student"""
    school_id = payload["school_id"]

    # Students can only see their own — server enforced
    if payload["role"] == "student":
        # Find student record for this user
        s_result = await db.execute(
            select(Student).where(
                Student.user_id == payload["sub"],
                Student.school_id == school_id,
            )
        )
        own_student = s_result.scalar_one_or_none()
        if not own_student or str(own_student.id) != student_id:
            raise HTTPException(403, "You can only view your own attendance")

    query = select(Attendance).where(
        Attendance.student_id == student_id,
        Attendance.school_id == school_id,
    )
    if month and year:
        query = query.where(
            func.extract("month", Attendance.date) == month,
            func.extract("year", Attendance.date) == year,
        )
    query = query.order_by(Attendance.date.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    late = sum(1 for r in records if r.status == "late")

    return {
        "student_id": student_id,
        "summary": {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": round((present / total * 100), 1) if total > 0 else 0,
        },
        "records": [
            {"date": str(r.date), "status": r.status}
            for r in records
        ],
    }


@router.get("/report/class/{class_id}")
async def class_attendance_report(
    class_id: str,
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    """Admin: Class-wise attendance report for date range"""
    school_id = payload["school_id"]

    if (to_date - from_date).days > 90:
        raise HTTPException(400, "Date range cannot exceed 90 days")

    result = await db.execute(
        select(
            User.full_name,
            Student.roll_number,
            func.count(Attendance.id).label("total"),
            func.sum(
                (Attendance.status == "present").cast(
                    __import__("sqlalchemy", fromlist=["Integer"]).Integer
                )
            ).label("present_count"),
        )
        .join(Student, Student.id == Attendance.student_id)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(
            Attendance.class_id == class_id,
            Attendance.school_id == school_id,
            Attendance.date >= from_date,
            Attendance.date <= to_date,
        )
        .group_by(User.full_name, Student.roll_number)
        .order_by(Student.roll_number)
    )
    rows = result.all()

    return {
        "class_id": class_id,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "students": [
            {
                "name": name,
                "roll_number": roll,
                "total_days": total,
                "present": int(present or 0),
                "absent": int(total or 0) - int(present or 0),
                "percentage": round((int(present or 0) / int(total) * 100), 1) if total else 0,
            }
            for name, roll, total, present in rows
        ],
    }
