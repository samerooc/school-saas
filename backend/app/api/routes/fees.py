"""
Fee Management API - Module 3
"""
import uuid, hmac, hashlib
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import require_roles, get_current_user_payload
from app.core.config import settings
from app.models.models import FeeStructure, FeePayment, Student, User

router = APIRouter(prefix="/fees", tags=["fees"])


def gen_receipt() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"RCP-{ts}-{uuid.uuid4().hex[:4].upper()}"


@router.post("/structure", status_code=201)
async def create_fee_structure(
    class_id: str, academic_year_id: str, fee_type: str, amount: float,
    due_date: Optional[date] = None, late_fine_per_day: float = 0,
    unlocks_premium: bool = False, premium_duration_days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    fs = FeeStructure(
        school_id=school_id, academic_year_id=academic_year_id,
        class_id=class_id, fee_type=fee_type, amount=Decimal(str(amount)),
        due_date=due_date, late_fine_per_day=Decimal(str(late_fine_per_day)),
        unlocks_premium=unlocks_premium, premium_duration_days=premium_duration_days,
    )
    db.add(fs)
    await db.flush()
    return {"id": str(fs.id), "message": "Fee structure created"}


@router.get("/structure")
async def list_fee_structures(
    class_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher")),
):
    school_id = payload["school_id"]
    query = select(FeeStructure).where(FeeStructure.school_id == school_id)
    if class_id: query = query.where(FeeStructure.class_id == class_id)
    result = await db.execute(query.order_by(FeeStructure.fee_type))
    items = result.scalars().all()
    return [
        {"id": str(f.id), "fee_type": f.fee_type, "amount": float(f.amount),
         "due_date": str(f.due_date) if f.due_date else None,
         "late_fine_per_day": float(f.late_fine_per_day), "unlocks_premium": f.unlocks_premium}
        for f in items
    ]


@router.get("/student/{student_id}/dues")
async def get_student_dues(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    school_id = payload["school_id"]
    role = payload["role"]
    if role == "student":
        own = (await db.execute(
            select(Student).where(Student.user_id == payload["sub"], Student.school_id == school_id)
        )).scalar_one_or_none()
        if not own or str(own.id) != student_id:
            raise HTTPException(403, "You can only view your own fees")
    student = (await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )).scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    structures = (await db.execute(
        select(FeeStructure).where(FeeStructure.school_id == school_id, FeeStructure.class_id == student.class_id)
    )).scalars().all()
    paid = (await db.execute(
        select(FeePayment).where(FeePayment.student_id == student_id, FeePayment.status == "paid")
    )).scalars().all()
    paid_ids = {str(p.fee_structure_id) for p in paid}
    dues = []
    total_due = Decimal("0")
    for fs in structures:
        if str(fs.id) in paid_ids:
            continue
        fine = Decimal("0")
        if fs.due_date and date.today() > fs.due_date and fs.late_fine_per_day > 0:
            fine = fs.late_fine_per_day * (date.today() - fs.due_date).days
        total = fs.amount + fine
        total_due += total
        dues.append({"fee_structure_id": str(fs.id), "fee_type": fs.fee_type,
                     "amount": float(fs.amount), "late_fine": float(fine), "total": float(total),
                     "due_date": str(fs.due_date) if fs.due_date else None})
    return {"student_id": student_id, "dues": dues, "total_due": float(total_due)}


@router.post("/collect/cash")
async def collect_cash(
    student_id: str, fee_structure_id: str, amount_paid: float,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    student = (await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )).scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    fs = (await db.execute(select(FeeStructure).where(FeeStructure.id == fee_structure_id))).scalar_one_or_none()
    if not fs:
        raise HTTPException(404, "Fee structure not found")
    receipt_no = gen_receipt()
    payment = FeePayment(
        school_id=school_id, student_id=student_id, fee_structure_id=fee_structure_id,
        amount_paid=Decimal(str(amount_paid)), payment_method="cash",
        receipt_number=receipt_no, status="paid", collected_by=payload["sub"],
    )
    db.add(payment)
    if fs.unlocks_premium and fs.premium_duration_days:
        student.is_premium = True
        student.premium_granted_by = payload["sub"]
        student.premium_granted_at = datetime.now(timezone.utc)
        student.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=fs.premium_duration_days)
    await db.flush()
    return {"message": "Payment recorded", "receipt_number": receipt_no, "premium_unlocked": fs.unlocks_premium}


@router.post("/razorpay/create-order")
async def create_razorpay_order(
    student_id: str, fee_structure_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    try:
        import razorpay
    except ImportError:
        raise HTTPException(500, "razorpay not installed")
    school_id = payload["school_id"]
    fs = (await db.execute(select(FeeStructure).where(FeeStructure.id == fee_structure_id))).scalar_one_or_none()
    if not fs:
        raise HTTPException(404, "Fee structure not found")
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = client.order.create({
        "amount": int(fs.amount * 100), "currency": "INR",
        "receipt": f"fee_{student_id[:8]}",
        "notes": {"student_id": student_id, "fee_structure_id": fee_structure_id}
    })
    payment = FeePayment(
        school_id=school_id, student_id=student_id, fee_structure_id=fee_structure_id,
        amount_paid=fs.amount, payment_method="online",
        transaction_id=order["id"], receipt_number=gen_receipt(), status="pending",
    )
    db.add(payment)
    await db.flush()
    return {"order_id": order["id"], "amount": int(fs.amount * 100), "currency": "INR", "key_id": settings.RAZORPAY_KEY_ID}


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature", "")
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(400, "Invalid signature")
    import json
    data = json.loads(body)
    if data.get("event") == "payment.captured":
        order_id = data["payload"]["payment"]["entity"].get("order_id")
        result = await db.execute(select(FeePayment).where(FeePayment.transaction_id == order_id, FeePayment.status == "pending"))
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = "paid"
            payment.payment_date = datetime.now(timezone.utc)
            fs = (await db.execute(select(FeeStructure).where(FeeStructure.id == payment.fee_structure_id))).scalar_one_or_none()
            if fs and fs.unlocks_premium and fs.premium_duration_days:
                student = (await db.execute(select(Student).where(Student.id == payment.student_id))).scalar_one_or_none()
                if student:
                    student.is_premium = True
                    student.premium_granted_at = datetime.now(timezone.utc)
                    student.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=fs.premium_duration_days)
    return {"status": "ok"}


@router.get("/report/collection")
async def collection_report(
    from_date: Optional[date] = Query(None), to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    query = (
        select(FeePayment, User)
        .join(Student, Student.id == FeePayment.student_id)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(FeePayment.school_id == school_id, FeePayment.status == "paid")
    )
    if from_date: query = query.where(FeePayment.payment_date >= from_date)
    if to_date:   query = query.where(FeePayment.payment_date <= to_date)
    rows = (await db.execute(query.order_by(FeePayment.payment_date.desc()))).all()
    total = sum(float(p.amount_paid or 0) for p, _ in rows)
    return {
        "total_collected": total, "payment_count": len(rows),
        "payments": [{"receipt_number": p.receipt_number, "student_name": u.full_name if u else "?",
                      "amount": float(p.amount_paid or 0), "method": p.payment_method,
                      "date": p.payment_date.isoformat() if p.payment_date else None}
                     for p, u in rows]
    }
